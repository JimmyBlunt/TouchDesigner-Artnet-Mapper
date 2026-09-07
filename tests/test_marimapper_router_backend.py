import inspect
import pickle
import unittest

from pixelblaze_mapper.marimapper_router_backend import Backend, BackendError, PipeTransport, pipe_backend


class Transport:
    def __init__(self):
        self.requests = []
        self.response = None

    def __call__(self, request, timeout):
        self.requests.append((request.copy(), timeout))
        if isinstance(self.response, Exception):
            raise self.response
        return self.response if self.response is not None else {"ok": True, "request_id": request["request_id"]}


class BackendTests(unittest.TestCase):
    def test_selected_count_is_not_inferred_from_original_ids(self):
        transport = Transport()
        backend = Backend(transport, 2)
        backend.set_led(1, True)  # Supervisor may map worker 1 to original 785.
        self.assertEqual(backend.get_led_count(), 2)
        self.assertEqual(transport.requests[0][0]["index"], 1)
        with self.assertRaises(ValueError):
            backend.set_led(785, True)

    def test_native_contract_and_unchanged_worker_index(self):
        transport = Transport()
        backend = Backend(transport, 3744)
        self.assertEqual(len(inspect.signature(backend.get_led_count).parameters), 0)
        self.assertEqual(len(inspect.signature(backend.set_led).parameters), 2)
        self.assertEqual(backend.get_led_count(), 3744)
        self.assertFalse(transport.requests)
        self.assertIsNone(backend.set_led(3001, True))
        backend.set_led(3001, False)
        self.assertEqual(transport.requests[0][0], {"action": "set_led", "index": 3001, "on": True, "request_id": 1})
        self.assertEqual(transport.requests[1][0]["request_id"], 2)

    def test_black_only(self):
        transport = Transport()
        backend = Backend(transport, 2)
        backend.set_leds([[0, 0, 0], [0.0, 0, 0]])
        self.assertEqual(transport.requests[0][0], {"action": "blackout", "request_id": 1})
        for buffer in ([], [[0, 0, 0]], [[1, 0, 0], [0, 0, 0]], [[0, 0], [0, 0]],
                       [[float("nan"), 0, 0], [0, 0, 0]], [[False, 0, 0], [0, 0, 0]], None):
            with self.subTest(buffer=buffer), self.assertRaises(ValueError):
                backend.set_leds(buffer)
        self.assertEqual(len(transport.requests), 1)

    def test_invalid_arguments_do_not_send(self):
        transport = Transport()
        for count in (True, 0, -1, 2.0):
            with self.assertRaises(ValueError):
                Backend(transport, count)
        for timeout in (True, 0, -1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                Backend(transport, 2, timeout)
        backend = Backend(transport, 2)
        for index, on in ((-1, True), (2, True), (True, True), (1.0, True), (0, 1)):
            with self.assertRaises(ValueError):
                backend.set_led(index, on)
        self.assertFalse(transport.requests)

    def test_unconfirmed_commands_latch_failure_without_retry(self):
        for response in ({}, {"ok": 1, "request_id": 1}, {"ok": True, "request_id": True},
                         {"ok": True, "request_id": 0}, {"ok": False, "request_id": 1, "error": "lease expired"},
                         [], TimeoutError(), EOFError(), BrokenPipeError()):
            with self.subTest(response=response):
                transport = Transport()
                transport.response = response
                backend = Backend(transport, 2)
                with self.assertRaises(BackendError):
                    backend.set_led(0, True)
                with self.assertRaises(BackendError):
                    backend.set_leds([[0, 0, 0]] * 2)
                self.assertEqual(len(transport.requests), 1)

    def test_late_success_is_not_success(self):
        clock = iter([0, 2]).__next__
        with self.assertRaises(BackendError):
            Backend(Transport(), 1, timeout=2, clock=clock).set_led(0, True)

    def test_reentrant_transport_fails_outer_command_too(self):
        def transport(request, timeout):
            with self.assertRaises(BackendError):
                backend.set_led(0, False)
            return {"ok": True, "request_id": request["request_id"]}
        backend = Backend(transport, 1)
        with self.assertRaises(BackendError):
            backend.set_led(0, True)

    def test_factory_pickles_without_native_or_socket_imports(self):
        self.assertIs(pickle.loads(pickle.dumps(pipe_backend)), pipe_backend)


class Connection:
    def __init__(self, ready=True):
        self.ready = ready
        self.sent = []
        self.polls = []
        self.received = 0

    def send(self, value):
        self.sent.append(value)

    def poll(self, timeout):
        self.polls.append(timeout)
        return self.ready

    def recv(self):
        self.received += 1
        return {"ok": True, "request_id": self.sent[-1]["request_id"]}


class PipeTests(unittest.TestCase):
    def test_sync_round_trip_with_bounded_poll(self):
        connection = Connection()
        transport = PipeTransport(connection, clock=iter([0, 0.25, 0.5]).__next__)
        self.assertEqual(transport({"request_id": 7}, 2), {"ok": True, "request_id": 7})
        self.assertEqual(connection.polls, [1.75])
        self.assertEqual(connection.received, 1)

    def test_no_reply_never_reads_or_succeeds(self):
        connection = Connection(False)
        with self.assertRaises(BackendError):
            pipe_backend(connection, 1).set_led(0, True)
        self.assertEqual(connection.received, 0)

    def test_delayed_send_does_not_wait_more(self):
        connection = Connection()
        with self.assertRaises(TimeoutError):
            PipeTransport(connection, clock=iter([0, 3]).__next__)({}, 2)
        self.assertFalse(connection.polls)

    def test_delayed_receive_rejected(self):
        connection = Connection()
        with self.assertRaises(TimeoutError):
            PipeTransport(connection, clock=iter([0, 0, 3]).__next__)({"request_id": 1}, 2)


if __name__ == "__main__":
    unittest.main()
