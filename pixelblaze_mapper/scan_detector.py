"""Sequential LED capture with native image detection and bounded transitions.

Backend acknowledgement means send completion, not optical acknowledgement.
The camera child/supervisor still bound blocking camera or IPC operations.
"""
from math import isfinite
import time

MIN_SEARCH_SECONDS = 0.1


def search_timeout(controller):
    timeout = float(controller.timeout)
    if not isfinite(timeout) or timeout <= 0:
        raise ValueError('LED detection timeout must be finite and positive')
    # Two 20-Hz send intervals of search allowance for a miss. This is NOT a
    # fixed on-time: a valid observation still ends the search immediately.
    return max(MIN_SEARCH_SECONDS, timeout)


def enable_and_find_led(cam, led_backend, led_id, view_id, timeout_controller,
                        threshold, display=False, *, find=None, make_led=None,
                        clock=time.monotonic):
    if find is None:
        from marimapper.detector import find_led
        find = find_led
    if make_led is None:
        from marimapper.led import LED2D
        make_led = LED2D
    timeout = search_timeout(timeout_controller)

    def wait_dark(phase):
        deadline = clock() + 3.0
        while find(cam, threshold, display) is not None:
            if clock() >= deadline:
                raise RuntimeError('LED %s: camera did not become dark %s; '
                                   'scan stopped instead of skipping LEDs' % (led_id, phase))

    # A blocked dark precondition is a capture failure, not an undetected LED.
    wait_dark('before switching on')
    try:
        led_backend.set_led(led_id, True)
        started = clock()  # The full search budget starts AFTER the send ACK.
        deadline = started + timeout
        while True:
            # Always examine a frame for this LED; never skip the camera call
            # because transport waiting consumed the previous timing budget.
            point = find(cam, threshold, display)
            response_time = clock() - started
            if point is not None or clock() >= deadline:
                break
    except BaseException:
        try:
            led_backend.set_led(led_id, False)
        except BaseException:
            pass  # Preserve the original failure; supervisor sends final black.
        raise
    led_backend.set_led(led_id, False)
    # Both success and ordinary detection timeout must finish their OFF phase.
    # A persistent bright frame cannot silently spill into the next LED.
    wait_dark('after switching off')
    if point is None:
        return None
    timeout_controller.add_response_time(response_time)
    return make_led(led_id, view_id, point)
