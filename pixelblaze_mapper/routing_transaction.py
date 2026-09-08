"""Offline-testable safe configuration transaction; never starts any output.

All model universes are zero-based Art-Net wire addresses. Only a hardware UI
adapter may convert a one-based display value before constructing this model.
"""

from pixelblaze_mapper.multi_controller import (
    ControllerConfig, RouterConfig, SegmentConfig, build_router_plan,
)


def table_rows(table):
    return [[str(table[r, c]) for c in range(table.numCols)] for r in range(table.numRows)]


def write_rows(table, rows):
    table.clear()
    for row in rows:
        table.appendRow(row)


def strict_flag(value):
    value = str(value).strip().lower()
    if value not in ('0', '1', 'false', 'true', 'off', 'on', 'no', 'yes'):
        raise ValueError('Boolean value must be 0/1 (or true/false)')
    return value in ('1', 'true', 'on', 'yes')


def records(rows):
    if not rows:
        raise ValueError('Missing configuration table header')
    header = rows[0]
    if not header or any(not isinstance(value, str) or not value.strip() for value in header):
        raise ValueError('Configuration headers must be nonempty text')
    if len(set(header)) != len(header):
        raise ValueError('Duplicate configuration table header')
    if any(len(row) != len(header) for row in rows[1:]):
        raise ValueError('Configuration row width does not match header')
    return [dict(zip(rows[0], row)) for row in rows[1:]]


def router_from_rows(controllers, segments, source_pixels=3744):
    return RouterConfig(
        controllers=tuple(ControllerConfig(
            name=row['name'], enabled=strict_flag(row['enabled']),
            target_address=row['target_ip'], local_interface=row['local_interface'],
            port=int(row['port']), start_universe=int(row['start_universe']),
            color_order=row['color_order'].upper(), brightness=float(row['brightness']),
            rate=int(row['rate']), art_sync=strict_flag(row['art_sync']),
            reserved_universes=int(row.get('reserved_universes', 0)),
        ) for row in records(controllers)),
        segments=tuple(SegmentConfig(
            name=row['name'], controller=row['controller'],
            source_start=int(row['source_start']), count=int(row['count']),
            destination_start=int(row['destination_start']), reverse=strict_flag(row['reverse']),
            color_override=row['color_override'].strip().upper() or None,
        ) for row in records(segments)), source_pixel_count=source_pixels,
    )


def stop_outputs(router):
    """Attempt every stop and refuse a commit unless shutdown is confirmed."""
    errors = []
    sender = router.op('artnet_510_sender_callbacks')
    if sender is not None:
        try:
            try:
                sender.module.set_enabled(False)
            except Exception:
                sender.module.stop()
            if sender.module.status().get('enabled'):
                raise RuntimeError('Shared sender remains enabled')
        except Exception as error:
            errors.append('sender: ' + str(error))
    for node in router.findChildren(depth=1):
        # Helper Constant/Select CHOPs may share the dmxout_ name prefix.
        if node.type != 'dmxout':
            continue
        try:
            node.par.active = False
            if bool(node.par.active):
                raise RuntimeError('native output remains active')
        except Exception as error:
            errors.append('native output: ' + str(error))
    if errors:
        raise RuntimeError('Stop not confirmed: ' + '; '.join(errors))


def _check_validation(router):
    validation = router.op('validation')
    if validation is not None and validation.numRows:
        errors = [row.get('message', '') for row in records(table_rows(validation))
                  if row.get('severity', '').lower() == 'error']
        if errors:
            raise ValueError('; '.join(errors))


def apply_router_transaction(router, controllers, segments, rebuild, *, extra_tables=(), source_pixels=3744):
    """Validate without mutation, stop, commit and rebuild; rollback on failure.

    ``extra_tables`` contains (table, candidate_rows), e.g. calibration or GICO
    draft DATs. Invalid candidates do not even stop the old sender. Once a valid
    commit begins all failure paths leave output OFF, never automatically resume.
    On rollback the previous builder is retried to restore derived operators.
    A failed recovery is explicitly reported and cannot masquerade as success.
    """
    from .scan_output_guard import assert_no_scan
    assert_no_scan()
    build_router_plan(router_from_rows(controllers, segments, source_pixels))
    updates = [(router.op('controller_config'), controllers),
               (router.op('segment_config'), segments), *extra_tables]
    if any(table is None for table, _ in updates):
        raise ValueError('Missing configuration table')
    snapshots = []
    seen = set()
    for table in [table for table, _ in updates] + [router.op('validation'), router.op('controller_summary')]:
        if table is not None and id(table) not in seen:
            snapshots.append((table, table_rows(table)))
            seen.add(id(table))
    stop_outputs(router)
    try:
        for table, rows in updates:
            write_rows(table, rows)
        rebuild()
        _check_validation(router)
        stop_outputs(router)
        return True
    except Exception as error:
        recovery_errors = []
        try:
            stop_outputs(router)
        except Exception as failure:
            recovery_errors.append(str(failure))
        for table, rows in snapshots:
            try:
                write_rows(table, rows)
            except Exception as failure:
                recovery_errors.append('restore: ' + str(failure))
        if not recovery_errors:
            try:
                rebuild()
                _check_validation(router)
            except Exception as failure:
                recovery_errors.append('rebuild: ' + str(failure))
        # A builder may regenerate summaries/drafts. Restore exact table state.
        for table, rows in snapshots:
            try:
                write_rows(table, rows)
            except Exception as failure:
                recovery_errors.append('restore: ' + str(failure))
        try:
            stop_outputs(router)
        except Exception as failure:
            recovery_errors.append(str(failure))
        detail = ('; RECOVERY REQUIRED: ' + '; '.join(recovery_errors)) if recovery_errors else '; previous tables restored; outputs OFF'
        raise RuntimeError(str(error) + detail) from error
