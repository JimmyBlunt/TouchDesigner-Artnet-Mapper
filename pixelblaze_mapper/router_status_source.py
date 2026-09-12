"""Reversible Router status refresh patch; no TD or output access on import."""

MARKER = '# ROUTER_STATUS_SOURCE_ONCE_V1'
_OLD = '''        summary = build_output_summary(records(table_rows(op('controller_config'))),
            records(table_rows(op('segment_config'))), state, source_pixels=_source_pixels(),
            validation_rows=records(table_rows(op('validation'))))
        from pixelblaze_mapper.sender_external_source import rate_label
        op('ui_panel/safety').par.text = '%s | sender %s | %s | %d RGB source pixels' % (
            summary.state, 'ON' if summary.sender_enabled else 'OFF', rate_label(state), _source_pixels())
'''
_NEW = ('        ' + MARKER + '\n        source_pixels = _source_pixels()\n' +
        _OLD.replace('source_pixels=_source_pixels()', 'source_pixels=source_pixels')
            .replace('rate_label(state), _source_pixels())', 'rate_label(state), source_pixels)'))


def install_source(source):
    if MARKER in source:
        if source.count(_NEW) != 1 or _OLD in source:
            raise ValueError('Changed Router status source-count patch')
        return source
    if source.count(_OLD) != 1:
        raise ValueError('Expected reviewed Router refresh_status source')
    return source.replace(_OLD, _NEW, 1)


def restore_source(source):
    if MARKER not in source:
        if source.count(_OLD) != 1:
            raise ValueError('Expected reviewed Router refresh_status source')
        return source
    if source.count(_NEW) != 1:
        raise ValueError('Changed Router status source-count patch')
    return source.replace(_NEW, _OLD, 1)


def _freeze(value):
    """Exact content/type key; unsupported objects use the uncached path."""
    kind = type(value)
    if kind in (str, int, float, bool, type(None)):
        return kind.__name__, value
    if kind in (list, tuple):
        return kind.__name__, tuple(_freeze(item) for item in value)
    if kind is dict:
        return 'dict', tuple((_freeze(key), _freeze(item)) for key, item in value.items())
    raise TypeError('Unsupported mapping-count cache input')


def mapping_counts_cached(owner, controllers, segments, count, inactive=()):
    from pixelblaze_mapper.router_dynamic_ui import mapping_counts
    try:
        signature = _freeze((controllers, segments, count, inactive))
    except TypeError:
        return mapping_counts(controllers, segments, count, inactive)
    key = 'router_mapping_counts_cache_v1'
    cached = owner.fetch(key, None)
    if cached is not None and cached[0] == signature:
        return dict(cached[1])
    # Only successful validation/computation replaces a previously valid entry.
    result = mapping_counts(controllers, segments, count, inactive)
    owner.store(key, (signature, tuple(result.items())))
    return dict(result)
