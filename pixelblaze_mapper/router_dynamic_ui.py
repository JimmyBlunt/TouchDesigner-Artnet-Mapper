"""Configuration-driven Router card. UI installation never restarts output."""
import ipaddress

from pixelblaze_mapper.router_extra_brightness_ui import parse_brightness
from pixelblaze_mapper.routing_transaction import records, table_rows, strict_flag

FIELDS = ('target_ip', 'start_universe', 'brightness', 'enabled', 'rate')


def _set_parameter_if_present(node, name, value):
    """Prefix matches include generated callback DATs, not only panel COMPs."""
    parameter = getattr(node.par, name, None)
    if parameter is not None:
        setattr(node.par, name, value)


def _panel_execute_type(helpers):
    """TD DAT modules resolve OP types as builtins, absent from globals()."""
    if 'panelexecuteDAT' in helpers:
        return helpers['panelexecuteDAT']
    import td
    return td.panelexecuteDAT


def validated_fields(values):
    address = str(ipaddress.IPv4Address(values['target_ip']))
    universe, enabled, rate = (int(values[k]) for k in ('start_universe', 'enabled', 'rate'))
    if not 0 <= universe <= 32767:
        raise ValueError('WIRE universe must be 0..32767')
    if enabled not in (0, 1):
        raise ValueError('Enabled must be 0 or 1')
    if not 1 <= rate <= 120:
        raise ValueError('Requested rate must be 1..120 FPS')
    return dict(target_ip=address, start_universe=str(universe),
                brightness=str(parse_brightness(values['brightness'])),
                enabled=str(enabled), rate=str(rate))


def mapping_counts(controllers, segments, count, inactive=()):
    """Disabled destinations are mapped, but not currently eligible for output."""
    configured = {r['name']: strict_flag(r['enabled']) for r in controllers}
    all_mapped, enabled_mapped = set(), set()
    for row in segments:
        if row['controller'] not in configured:
            continue
        indices = range(max(0, int(row['source_start'])),
                        min(count, int(row['source_start']) + int(row['count'])))
        all_mapped.update(indices)
        if configured[row['controller']]:
            enabled_mapped.update(indices)
    masked = set()
    for first, last in inactive:
        masked.update(range(max(0, int(first)), min(count, int(last) + 1)))
    return {'unassigned': len(set(range(count)) - all_mapped - masked),
            'disabled_only': len(all_mapped - enabled_mapped - masked),
            'inactive': len(masked), 'enabled': len(enabled_mapped - masked)}


def _entries(owner):
    return records(table_rows(owner.op('controller_config')))


def _current_values(owner):
    return {key: str(owner.op('ui_panel/router_' + key + '/string')[0, 0]).strip()
            for key in FIELDS}


def _remember(owner):
    name = owner.fetch('router_card_name', None)
    if name:
        drafts = dict(owner.fetch('router_card_drafts', {}))
        drafts[name] = _current_values(owner)
        owner.store('router_card_drafts', drafts)


def select(owner, step=0, reload=False):
    entries = _entries(owner)
    if not reload:
        _remember(owner)
    old = owner.fetch('router_card_name', None)
    if not entries:
        owner.store('router_card_name', None)
        owner.op('ui_panel/router_title').par.text = 'No controllers configured'
        return
    pos = next((i for i, r in enumerate(entries) if r['name'] == old), 0)
    row = entries[(pos + step) % len(entries)]
    name = row['name']
    drafts = dict(owner.fetch('router_card_drafts', {}))
    baselines = dict(owner.fetch('router_card_baselines', {}))
    if reload or name not in baselines or name not in drafts:
        baselines[name] = row
        drafts[name] = {key: row[key] for key in FIELDS}
    owner.store('router_card_name', name)
    owner.store('router_card_baselines', baselines)
    owner.store('router_card_drafts', drafts)
    for key, value in drafts[name].items():
        owner.op('ui_panel/router_' + key + '/string').text = value
    owner.op('ui_callbacks').module.refresh_status(force=True)


def select_name(owner, name):
    """Pick a current controller by identity; retain unsaved drafts on both cards."""
    names = [row['name'] for row in _entries(owner)]
    if name not in names:
        owner.op('ui_callbacks').module._set_status('Controller no longer available; reopen selection')
        return False
    current = owner.fetch('router_card_name', None)
    previous = names.index(current) if current in names else 0
    select(owner, names.index(name) - previous)
    menu = owner.op('ui_panel/router_controller_menu')
    if menu is not None:
        menu.par.display = False
    return True


def install_picker(owner):
    """Small hot-install independent of full card installation or output state."""
    import td
    canvas = owner.op('ui_panel')
    def node(parent, kind, name, x, y, w, h):
        result = parent.op(name) or parent.create(kind, name)
        result.name = name
        for key, value in dict(x=x,y=y,w=w,h=h,hmode='fixed',vmode='fixed',layer=230,display=True).items():
            _set_parameter_if_present(result, key, value)
        return result
    def button(parent, name, label, x, y, width, action):
        result = node(parent, td.buttonCOMP, name, x,y,width,30)
        for key,value in dict(label=label,buttontype='momentary',fontsize=11).items():
            _set_parameter_if_present(result,key,value)
        callback_name='router_picker_click_'+name
        callback=owner.op(callback_name) or owner.create(td.panelexecuteDAT,callback_name)
        callback.name=callback_name
        callback.par.active=False
        callback.par.fromop=result.path
        callback.par.panels=result.path
        callback.par.panelvalue='lselect'
        callback.par.offtoon=True
        for key in ('ontooff','whileon','whileoff','valuechange'):
            _set_parameter_if_present(callback,key,False)
        callback.text='def onOffToOn(panelValue):\n    from pixelblaze_mapper import router_dynamic_ui as ui\n    ui.'+action+'\n'
        callback.par.active=True
        return result
    title=canvas.op('router_title')
    if title is not None: title.par.w=590
    button(canvas,'router_btn_choose','CONTROLLER  v',630,560,216,'toggle_picker(parent())')
    rows=_entries(owner)
    height=min(380,max(38,38*len(rows)))
    menu=node(canvas,td.containerCOMP,'router_controller_menu',630,554-height,524,height)
    _set_parameter_if_present(menu,'bgalpha',1)
    _set_parameter_if_present(menu,'vscrollbar','on')
    for child in menu.children: child.par.display=False
    for index,row in enumerate(rows):
        button(menu,'controller_'+str(index),row['name']+' | '+row['target_ip'],4,height-38*(index+1)+4,516,
               'select_name(parent(), %r)' % row['name'])
    menu.par.display=False
    return menu


def toggle_picker(owner):
    menu=owner.op('ui_panel/router_controller_menu')
    if menu is not None and bool(menu.par.display):
        menu.par.display=False
    else:
        install_picker(owner).par.display=True


def apply_drafts(owner, rows):
    """Return modified row copy; leave actual write/stop/rollback to transaction."""
    _remember(owner)
    drafts = owner.fetch('router_card_drafts', {})
    baselines = owner.fetch('router_card_baselines', {})
    result = [list(r) for r in rows]
    current = {r['name']: r for r in records(rows)}
    for name, values in drafts.items():
        base = baselines.get(name)
        if base is None or all(str(values[k]) == str(base[k]) for k in FIELDS):
            continue
        if current.get(name) != base:
            raise ValueError(name + ': config changed externally; select and RELOAD before applying')
        parsed = validated_fields(values)
        target = next(r for r in result[1:] if r[result[0].index('name')] == name)
        for key, value in parsed.items():
            target[result[0].index(key)] = value
    return result


def brightness_live(owner):
    """Explicit single-cell live edit, never applies other draft fields."""
    try:
        name = owner.fetch('router_card_name', None)
        row = next((r for r in _entries(owner) if r['name'] == name), None)
        baseline = owner.fetch('router_card_baselines', {}).get(name)
        if row is None or row != baseline:
            raise ValueError('Controller changed externally; RELOAD first')
        value = parse_brightness(_current_values(owner)['brightness'])
        table = owner.op('controller_config')
        index = next(i for i in range(1, table.numRows) if str(table[i, 'name']) == name)
        previous = str(table[index, 'brightness'])
        try:
            table[index, 'brightness'] = str(value)
            assert float(table[index, 'brightness']) == value
        except Exception:
            table[index, 'brightness'] = previous
            raise
        baseline = dict(row, brightness=str(value))
        baselines = dict(owner.fetch('router_card_baselines', {}))
        baselines[name] = baseline
        owner.store('router_card_baselines', baselines)
        owner.op('ui_panel/router_brightness/string').text = str(value)
        _remember(owner)
        owner.op('ui_callbacks').module._set_status(name + ': brightness %.1f%% live; sender unchanged' % (value * 100))
        owner.op('ui_callbacks').module.refresh_status(force=True)
        return True
    except Exception as error:
        owner.op('ui_callbacks').module._set_status('BLOCKED - ' + str(error), (0.98, 0.38, 0.32))
        return False


def route_summary(routes, item):
    """Two bounded lines; full segment ranges remain in Controller Ports."""
    header = '%d routes | %d reserved universes | NIC %s | UDP %d' % (
        len(routes), item.universe_count, item.local_interface, item.port)
    detail = ('%d LED assignments | Full source/target ranges: Controller Ports (Ctrl+Shift+C)' %
              sum(int(row['count']) for row in routes)) if routes else 'No pixel routes assigned'
    return header + '\n' + detail


def refresh(owner, summary):
    c = owner.op('ui_panel')
    if c.op('router_title') is None:
        return
    entries = _entries(owner)
    selected = owner.fetch('router_card_name', None)
    names = [r['name'] for r in entries]
    if selected not in names:
        if names:
            select(owner, reload=True)
        else:
            c.op('router_title').par.text = 'No controllers configured'
        return
    item = next(r for r in summary.controllers if r.name == selected)
    c.op('router_title').par.text = '%s | %s | %d / %d controllers' % (selected, item.state, names.index(selected) + 1, len(names))
    c.op('router_live').par.text = 'LIVE CONFIG: %s | WIRE %s | %.1f%% | requested %d FPS | %s' % (
        item.target, item.universe_label, item.brightness * 100, item.rate, item.color_order)
    segments = records(table_rows(owner.op('segment_config')))
    routes = [r for r in segments if r['controller'] == selected]
    c.op('router_route').par.text = route_summary(routes, item)
    from pixelblaze_mapper.router_status_source import mapping_counts_cached
    counts = mapping_counts_cached(owner, entries, segments, summary.source_pixels or 0,
                                   owner.fetch('inactive_source_ranges', []))
    c.op('unassigned').par.text = 'SOURCE PIXELS: enabled routes %(enabled)d | disabled-only %(disabled_only)d | unassigned %(unassigned)d | explicit black slots %(inactive)d' % counts


def install(owner, helpers):
    """UI-only hot install: caller replaces ui_callbacks separately, never build()."""
    label, field, button = (helpers[k] for k in ('_label', '_field', '_button'))
    get, settext = helpers['_get_or_create'], helpers['_replace_dat_text']
    panel_execute_type = _panel_execute_type(helpers)
    c = owner.op('ui_panel')
    for node in c.children:
        if node.name.startswith(('ws_', 'apa_', 'extra_')) or node.name in ('firmware_note', 'advanced'):
            _set_parameter_if_present(node, 'display', False)
    for node in owner.children:
        if node.name.startswith('extra_brightness_click_'):
            _set_parameter_if_present(node, 'active', False)
    label(c, 'router_title', 'Controller', 24, 560, 820, 30, size=14)
    for name, title, x, width, action in (
            ('prev', '<', 858, 44, 'select(parent(), -1)'),
            ('next', '>', 910, 44, 'select(parent(), 1)'),
            ('reload', 'RELOAD', 964, 190, 'select(parent(), reload=True)'),
            ('brightness_live', 'BRIGHTNESS LIVE', 864, 402, 'brightness_live(parent())')):
        # Last action sits beside the brightness field, other actions navigate.
        y, width = (408, 290) if name == 'brightness_live' else (560, width)
        b = button(c, 'router_btn_' + name, title, x, y, width, (.10, .38, .42))
        b.par.h = 30
        cb = get(owner, panel_execute_type, 'router_card_click_' + name)
        cb.par.active = False
        cb.par.fromop = b.path; cb.par.panels = b.path
        cb.par.panelvalue = 'lselect'; cb.par.offtoon = True
        cb.par.ontooff = False; cb.par.whileon = False; cb.par.whileoff = False; cb.par.valuechange = False
        settext(cb, 'def onOffToOn(panelValue):\n    from pixelblaze_mapper import router_dynamic_ui as ui\n    ui.' + action + '\n    return\n')
        cb.par.active = True
    label(c, 'router_live', '', 24, 530, 1132, 26, size=12)
    specs = (('IP address (draft)', 'target_ip', 24, 260, 492, 292),
             ('First WIRE universe (0-based)', 'start_universe', 594, 884, 492, 270),
             ('Enabled 0/1 (draft)', 'enabled', 24, 260, 450, 292),
             ('Requested rate FPS (draft)', 'rate', 594, 884, 450, 270),
             ('Brightness 0..1 (0,3 = 30%)', 'brightness', 24, 260, 408, 292))
    for text, key, lx, fx, y, width in specs:
        label(c, 'router_' + key + '_label', text, lx, y, fx-lx-8, 32, size=12)
        field(c, 'router_' + key, '', fx, y, width, 32)
    label(c, 'router_route', '', 24, 356, 1132, 44, size=11)
    label(c, 'router_draft_note', 'Fields = drafts; APPLY stops output. Brightness Live changes only brightness. < > retain drafts; RELOAD discards this card draft.', 24, 332, 1132, 22, size=10)
    owner.store('router_card_drafts', {})
    owner.store('router_card_baselines', {})
    select(owner, reload=True)
    install_picker(owner)
