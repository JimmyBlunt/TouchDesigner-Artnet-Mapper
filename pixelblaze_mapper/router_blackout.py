"""Explicit all-off packets; stopping a socket alone leaves latched LEDs lit."""
import socket
import time

from .multi_controller import build_router_plan
from .routing_transaction import router_from_rows, table_rows, stop_outputs


def send_blackout(config, *, socket_factory=socket.socket, sleep=time.sleep):
    plan = build_router_plan(config)
    groups = {}
    for controller in plan.controllers:
        if not controller.config.enabled:
            continue
        c = controller.config
        packets = groups.setdefault(c.local_interface, {})
        for route in controller.routes:
            universe = route.linear_universe
            packet = (b'Art-Net\0\x00\x50\x00\x0e\x00\x00' +
                      universe.to_bytes(2, 'little') + b'\x01\xfe' + bytes(510))
            packets[(c.target_address, c.port, universe)] = packet
    sent = 0
    errors = []
    for interface, packets in groups.items():
        sock = None
        try:
            sock = socket_factory(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(.2)
            sock.bind((interface, 0))
            # Repeat complete frames, including reserved black-only universes.
            for _ in range(3):
                for (address, port, universe), packet in packets.items():
                    sock.sendto(packet, (address, port))
                    sent += 1
                    sleep(.001)
        except Exception as error:
            errors.append(interface + ': ' + str(error))
        finally:
            if sock is not None:
                sock.close()
    if errors:
        raise RuntimeError('Outputs stopped; blackout send failed: ' + '; '.join(errors))
    return {'packets_sent': sent, 'universes': sum(map(len, groups.values())),
            'delivery_confirmed': False}


def all_off(router):
    stop_outputs(router)
    from .scan_output_guard import assert_no_scan
    assert_no_scan()
    source = router.op('source_select')
    config = router_from_rows(table_rows(router.op('controller_config')),
                              table_rows(router.op('segment_config')), int(source.numSamples))
    report = send_blackout(config)
    router.store('last_blackout_report', report)
    return report
