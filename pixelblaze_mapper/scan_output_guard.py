"""In-process scan ownership guard. No sockets, persistent objects or auto-resume.

The TD application must also monitor native/third-party writers. This guard only
arbitrates the application's cooperating Python entry points; it is not a claim
of network-wide exclusivity. A worker watchdog independently handles parent loss.
"""
from threading import RLock
from uuid import uuid4

_lock = RLock()
_token = None


def assert_no_scan():
    with _lock:
        if _token is not None:
            raise RuntimeError('Guided Scan owns output; stop the scan before Live or routing changes')


def acquire():
    global _token
    with _lock:
        assert_no_scan()
        _token = str(uuid4())
        return _token


def release(token):
    global _token
    with _lock:
        if not token or token != _token:
            raise RuntimeError('Scan ownership token mismatch')
        _token = None


def active():
    with _lock:
        return _token is not None
