"""MariMapper backend contract over an explicitly injected, trusted local IPC.

No socket, camera, route lookup or device acknowledgement lives here. A successful
call means the supervisor acknowledged its command, NOT that a light was observed.
Use partial(pipe_backend, connection, count, timeout) as DetectorProcess factory;
the stock custom CLI's zero-argument Backend() loader is deliberately unsupported.
"""

from math import isfinite
from numbers import Real
from time import monotonic


class BackendError(RuntimeError):
    """Command completion is unconfirmed; the supervisor must abort/blackout."""


def _timeout(value):
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value) or value <= 0:
        raise ValueError("timeout must be finite and positive")
    return float(value)


class PipeTransport:
    """Single caller, dedicated duplex multiprocessing.Connection, trusted peer.

poll bounds waiting for the response. Connection.send/recv themselves cannot be
hard-cancelled here: the supervisor's independent process watchdog remains
mandatory. Never connect this pickle-based channel to an untrusted peer.
"""

    def __init__(self, connection, *, clock=monotonic):
        if not all(callable(getattr(connection, name, None)) for name in ("send", "poll", "recv")):
            raise TypeError("connection needs send, poll and recv")
        self.connection = connection
        self.clock = clock

    def __call__(self, request, timeout):
        deadline = self.clock() + timeout
        self.connection.send(request)
        remaining = deadline - self.clock()
        if remaining <= 0 or not self.connection.poll(remaining):
            raise TimeoutError("supervisor acknowledgement timed out")
        response = self.connection.recv()
        if self.clock() >= deadline:
            raise TimeoutError("supervisor acknowledgement arrived too late")
        return response


class Backend:
    """Native synchronous get_led_count/set_led and black-only set_leds.

transport(request: dict, timeout: float) -> dict must be synchronous and bounded.
Every request carries an increasing request_id echoed by a strict boolean ok
reply. Transport errors, stale/malformed replies and rejection latch failure;
there is no retry because a timed-out command may already have reached hardware.
The supervisor owns selected-ID authorization, route lease and emergency zero.
    count is the frozen selection (including anchors), NOT the source map size;
    worker indices are dense and the supervisor performs the stable-ID mapping.
"""

    def __init__(self, transport, count, timeout=2.0, *, clock=monotonic):
        if not callable(transport):
            raise TypeError("explicit callable IPC transport required")
        if type(count) is not int or count <= 0:
            raise ValueError("count must be a positive selected-worker LED count")
        self._transport = transport
        self._count = count
        self._timeout = _timeout(timeout)
        self._clock = clock
        self._request_id = 0
        self._failed = False
        self._busy = False

    def get_led_count(self):
        return self._count

    def _request(self, action, **payload):
        if self._failed:
            raise BackendError("backend failed; supervisor abort/blackout required")
        if self._busy:
            self._failed = True
            raise BackendError("concurrent/reentrant IPC calls are unsupported")
        self._busy = True
        self._request_id += 1
        request = {"action": action, "request_id": self._request_id, **payload}
        started = self._clock()
        try:
            response = self._transport(request, self._timeout)
            if self._clock() - started >= self._timeout:
                raise TimeoutError("supervisor acknowledgement arrived too late")
            if self._failed:
                raise BackendError("backend failed during IPC command")
            if (type(response) is not dict or type(response.get("request_id")) is not int
                    or response["request_id"] != self._request_id
                    or type(response.get("ok")) is not bool):
                raise BackendError("malformed or stale supervisor acknowledgement")
            if not response["ok"]:
                raise BackendError("supervisor rejected command: " + str(response.get("error", "unspecified error")))
        except Exception as exc:
            self._failed = True
            if isinstance(exc, BackendError):
                raise
            raise BackendError("IPC command completion unconfirmed: " + type(exc).__name__) from exc
        finally:
            self._busy = False

    def set_led(self, led_index, on):
        if type(led_index) is not int or not 0 <= led_index < self._count:
            raise ValueError("LED index must be a dense worker index within selected count")
        if type(on) is not bool:
            raise ValueError("on must be a boolean")
        self._request("set_led", index=led_index, on=on)

    def set_leds(self, buffer):
        """Only exact full-count RGB black buffers are allowed; no fast scan."""
        try:
            if len(buffer) != self._count:
                raise ValueError("black buffer must cover the full selected-worker LED count")
            for row in buffer:
                if len(row) != 3 or any(isinstance(v, bool) or not isinstance(v, Real)
                                        or not isfinite(v) or v != 0 for v in row):
                    raise ValueError("only RGB black is allowed; coloured/fast scan is unsupported")
        except TypeError as exc:
            raise ValueError("expected a full-count RGB black buffer") from exc
        self._request("blackout")


def pipe_backend(connection, count, timeout=2.0):
    """Picklable module-level factory; does not create or own the connection."""
    return Backend(PipeTransport(connection), count, timeout)
