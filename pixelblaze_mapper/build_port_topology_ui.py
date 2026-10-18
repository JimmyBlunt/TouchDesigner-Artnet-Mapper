"""Bounded controller/port draft editor; builds UI only, never starts output."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = '/project1/multi_controller_output/gico_port_config/controller_ports'


def _runtime_source():
    return r'''import json
import re
import sys
from dataclasses import asdict, replace
from math import ceil
from pathlib import Path

ROOT = Path(project.folder) if 'project' in globals() else Path(__import__('pixelblaze_mapper').__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from pixelblaze_mapper.multi_controller import ControllerConfig, controller_rows, segment_rows
from pixelblaze_mapper.installation_contract import TOTAL_PIXELS
from pixelblaze_mapper.port_topology import ControllerDraft, PortDraft, build_topology, merge_controller, remove_controller, add_port, remove_port, ui_to_wire, wire_to_ui
from pixelblaze_mapper.routing_transaction import table_rows, router_from_rows, apply_router_transaction

OWNER = op('/project1/multi_controller_output/gico_port_config/controller_ports')
ROUTER = op('/project1/multi_controller_output')
PAGE_SIZE = 6

def _source_pixels():
    source = op('/project1/math1')
    return int(source.numSamples) if source is not None else TOTAL_PIXELS

def _router():
    return router_from_rows(table_rows(ROUTER.op('controller_config')),
                            table_rows(ROUTER.op('segment_config')), _source_pixels())

def _signature():
    return json.dumps([table_rows(ROUTER.op('controller_config')), table_rows(ROUTER.op('segment_config'))])

def _field(name):
    value = OWNER.op('ui_panel/' + name + '/string')[0, 0]
    return '' if value is None else str(value).strip()

def interface_label():
    address = _field('interface')
    rows = OWNER.fetch('local_interfaces', [])
    name = next((row['name'] for row in rows if row['address'] == address), 'nicht erkannt')
    if address == '0.0.0.0': name = 'Automatische Schnittstelle'
    return address + ' | ' + name + '  v'

def choose_controller(name):
    if name not in {item.name for item in _router().controllers}:
        _status('Controller nicht mehr vorhanden; Auswahl erneut oeffnen.')
        return False
    # A menu choice loads a draft only. Live configuration and output stay intact.
    OWNER.op('ui_panel/load_id/string').text = name
    return act('load')

def toggle_controllers():
    menu = OWNER.op('ui_panel/controller_menu')
    if bool(menu.par.display):
        menu.par.display = False
        return
    scope = dict(globals(), __name__='controller_menu_refresh', __file__=str(ROOT/'pixelblaze_mapper/build_port_topology_ui.py'))
    path = ROOT/'pixelblaze_mapper/build_port_topology_ui.py'
    exec(compile(path.read_text(encoding='utf-8'),str(path),'exec'),scope,scope)
    scope['build_controller_menu'](OWNER)
    menu.par.display = True

def choose_interface(address):
    allowed = {'0.0.0.0'} | {row['address'] for row in OWNER.fetch('local_interfaces', [])}
    if address not in allowed:
        raise ValueError('Interface is no longer in the available list; refresh')
    OWNER.op('ui_panel/interface/string').text = address
    OWNER.op('ui_panel/btn_interface').par.label = interface_label()
    OWNER.op('ui_panel/interface_menu').par.display = False
    _status('Schnittstelle im Entwurf: ' + address + ' | Ausgabe unverändert')

def toggle_interfaces():
    from pixelblaze_mapper import local_interfaces
    menu = OWNER.op('ui_panel/interface_menu')
    menu.par.display = not bool(menu.par.display)
    if bool(menu.par.display): local_interfaces.refresh()

def poll_interfaces():
    from pixelblaze_mapper import local_interfaces
    value = local_interfaces.take_result()
    if value is None: return
    if value['error']:
        _status('Schnittstellen konnten nicht aktualisiert werden: ' + value['error'])
        return
    OWNER.store('local_interfaces', value['interfaces'])
    scope = dict(globals(), __name__='interface_menu_refresh')
    path = ROOT/'pixelblaze_mapper/build_port_topology_ui.py'
    scope['__file__'] = str(path)
    exec(compile(path.read_text(encoding='utf-8'),str(path),'exec'),scope,scope)
    scope['build_interface_menu'](OWNER)
    OWNER.op('ui_panel/btn_interface').par.label = interface_label()

def _flag(name):
    value = _field(name)
    if value not in ('0', '1'):
        raise ValueError(name + ' must be 0 or 1')
    return value == '1'

def _optional(value):
    return None if value.strip() == '' else int(value)

def _decode(data):
    return ControllerDraft(ControllerConfig(**data['controller']), data['profile'],
                           tuple(PortDraft(**port) for port in data['ports']))

def _saved():
    return _decode(OWNER.fetch('draft'))

def _save(draft):
    OWNER.store('draft', asdict(draft))

def _status(message):
    OWNER.store('message', message)
    node = OWNER.op('ui_panel/status')
    if node is not None:
        node.par.text = message

def _repaint():
    scope = dict(globals())
    scope['__name__'] = 'embedded_port_topology'
    path = ROOT / 'pixelblaze_mapper' / 'build_port_topology_ui.py'
    scope['__file__'] = str(path)
    exec(compile(path.read_text(encoding='utf-8'), str(path), 'exec'), scope, scope)
    scope['build']()

def _rebuild_router():
    scope = dict(globals())
    scope['__name__'] = '__main__'
    path = ROOT / 'pixelblaze_mapper' / 'build_multi_controller_output.py'
    scope['__file__'] = str(path)
    exec(compile(path.read_text(encoding='utf-8'), str(path), 'exec'), scope, scope)

def _gico_tables(draft):
    if draft.controller.name != 'WS2812_NODE' or draft.profile != 'gico_equal':
        return ()
    gico = ROUTER.op('gico_port_config')
    if len(draft.ports) != 4 or {item.number for item in draft.ports} != {1, 2, 3, 4}:
        raise ValueError('Current GICO adapter has four physical ports; disable unused ports instead of removing hardware slots')
    settings = [('key', 'value'), ('universes_per_port', draft.ports[0].reserved_universes),
                ('first_universe', wire_to_ui(draft.controller.start_universe))]
    ports = [('port', 'label', 'enabled', 'source_start', 'pixel_count', 'reverse', 'color_order')]
    for item in sorted(draft.ports, key=lambda port: port.number):
        ports.append((item.number, item.label, int(item.enabled), '' if item.source_start is None else item.source_start,
                      item.pixel_count, int(item.reverse), item.color_order))
    return ((gico.op('settings'), settings), (gico.op('ports'), ports))

def _import_controller(name):
    config = _router()
    controller = next((item for item in config.controllers if item.name == name), None)
    if controller is None:
        raise ValueError('Unknown controller; use NEW DRAFT to create this ID')
    routes = [item for item in config.segments if item.controller == name]
    ports = []
    profile = 'gico_equal' if name == 'WS2812_NODE' else 'independent'
    if profile == 'gico_equal':
        gico = ROUTER.op('gico_port_config')
        settings = {str(row[0]): str(row[1]) for row in table_rows(gico.op('settings'))[1:]}
        reserve = int(settings['universes_per_port'])
        # Infer assignments from the live router, never overwrite with stale draft sources.
        count = max(1, ceil(controller.reserved_universes / reserve))
        for number in range(1, count + 1):
            destination = (number - 1) * reserve * 170
            matches = [route for route in routes if route.destination_start == destination]
            if len(matches) > 1:
                raise ValueError('Multiple segments in a GICO port require explicit consolidation')
            route = matches[0] if matches else None
            ports.append(PortDraft(number, route.name if route else 'Port %d' % number,
                route is not None, route.source_start if route else None,
                route.count if route else 0, reserve, route.reverse if route else False,
                (route.color_override or controller.color_order) if route else controller.color_order))
        if any(route.destination_start not in {item.number * reserve * 170 - reserve * 170 for item in ports} for route in routes):
            raise ValueError('GICO routes do not match its fixed hardware blocks; inspect original tables')
    else:
        identities = [re.fullmatch(r'PORT_' + re.escape(name) + r'_([1-9][0-9]*)', route.name) for route in routes]
        named_numbers = {route.name: int(match.group(1)) for route, match in zip(routes, identities) if match}
        preserve_numbers = len(named_numbers) == len(routes) and len(set(named_numbers.values())) == len(routes)
        for number, route in enumerate(sorted(routes, key=lambda item: item.destination_start), 1):
            if preserve_numbers:
                number = named_numbers[route.name]
            reserve = ceil((route.destination_start % 170 + route.count) / 170)
            ports.append(PortDraft(number, route.name, True, route.source_start, route.count,
                reserve, route.reverse, route.color_override or controller.color_order, route.destination_start))
        if ports:
            # Preserve trailing reserved capacity in the last imported port.
            last = ports[-1]
            tail = controller.reserved_universes - (last.destination_start // 170)
            ports[-1] = replace(last, reserved_universes=max(last.reserved_universes, tail))
        ports.sort(key=lambda item: item.number)
    draft = ControllerDraft(controller, profile, tuple(ports))
    build_topology(draft, source_pixels=_source_pixels())
    return draft

def ensure_draft():
    if OWNER.fetch('draft', None) is None:
        config = _router()
        name = next((item.name for item in config.controllers if item.name == 'WS2812_NODE'),
                    config.controllers[0].name if config.controllers else None)
        import_error = ''
        if name:
            try:
                _save(_import_controller(name))
            except Exception as error:
                import_error = ' | Existing topology needs review: ' + str(error)
                _save(ControllerDraft(ControllerConfig('NEW_CONTROLLER', '127.0.0.1', '0.0.0.0'), 'independent', ()))
        else:
            _save(ControllerDraft(ControllerConfig('NEW_CONTROLLER', '127.0.0.1', '0.0.0.0'), 'independent', ()))
        OWNER.store('baseline', _signature())
        OWNER.store('page', 0)
        OWNER.store('delete', False)
        OWNER.store('message', 'DRAFT ONLY | router unchanged; read all fields before SAFE APPLY' + import_error)
    return OWNER.fetch('draft')

def _draft():
    previous = _saved()
    controller = replace(previous.controller, target_address=_field('target'),
        local_interface=_field('interface'), port=int(_field('udp_port')),
        start_universe=int(_field('first_ui')),
        brightness=float(_field('brightness')), rate=int(_field('rate')),
        enabled=_flag('enabled'), color_order=_field('order').upper())
    ports = list(previous.ports)
    start = int(OWNER.fetch('page', 0)) * PAGE_SIZE
    for slot, old in enumerate(ports[start:start + PAGE_SIZE]):
        prefix = 'row%d_' % slot
        ports[start + slot] = replace(old, label=_field(prefix + 'label'), enabled=_flag(prefix + 'enabled'),
            source_start=_optional(_field(prefix + 'source')), pixel_count=int(_field(prefix + 'pixels')),
            reserved_universes=int(_field(prefix + 'reserve')), reverse=_flag(prefix + 'reverse'),
            color_order=_field(prefix + 'order').upper(), destination_start=_optional(_field(prefix + 'target')))
    return ControllerDraft(controller, _field('profile'), tuple(ports))

def act(command):
    try:
        if command == 'load':
            _save(_import_controller(_field('load_id')))
            OWNER.store('baseline', _signature())
            OWNER.store('page', 0)
            OWNER.store('delete', False)
            _status('LOADED live controller; draft only')
        elif command == 'new':
            name = _field('load_id')
            if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', name):
                raise ValueError('New ID: letter followed by letters, digits, underscore or hyphen')
            if name in {item.name for item in _router().controllers}:
                raise ValueError('ID already exists; LOAD it to edit')
            _save(ControllerDraft(ControllerConfig(name, '127.0.0.1', '0.0.0.0'), 'independent',
                                  (PortDraft(1, 'Port 1', False, reserved_universes=1),)))
            OWNER.store('baseline', _signature())
            OWNER.store('page', 0)
            OWNER.store('delete', False)
            _status('NEW DRAFT | set device IP/interface; controller disabled by default')
        elif command == 'delete':
            OWNER.store('delete', True)
            _status('DELETE STAGED: ' + _saved().controller.name + ' | SAFE APPLY removes this controller and its routes; LOAD cancels')
        else:
            draft = _draft()
            if command == 'add':
                draft = add_port(draft)
                OWNER.store('page', (len(draft.ports) - 1) // PAGE_SIZE)
                _status('PORT ADDED TO DRAFT | disabled/unassigned; router unchanged')
            elif command == 'remove':
                if not draft.ports:
                    raise ValueError('No port to remove')
                draft = remove_port(draft, int(_field('remove_number')))
                OWNER.store('page', min(int(OWNER.fetch('page', 0)), max(0, (len(draft.ports) - 1) // PAGE_SIZE)))
                _status('PORT REMOVED FROM DRAFT | router unchanged until SAFE APPLY')
            elif command in ('prev', 'next'):
                pages = max(1, ceil(len(draft.ports) / PAGE_SIZE))
                OWNER.store('page', max(0, min(pages - 1, int(OWNER.fetch('page', 0)) + (-1 if command == 'prev' else 1))))
            elif command in ('validate', 'apply'):
                delete = OWNER.fetch('delete', False)
                candidate = remove_controller(_router(), draft.controller.name) if delete else merge_controller(_router(), draft)
                extras = () if delete else _gico_tables(draft)
                if command == 'apply':
                    if OWNER.fetch('baseline') != _signature():
                        raise ValueError('Router changed since LOAD; reload before applying to avoid stale overwrite')
                    # Save editable draft before builder recreates controls; this is not live config.
                    _save(draft)
                    apply_router_transaction(ROUTER, controller_rows(candidate), segment_rows(candidate),
                        _rebuild_router, source_pixels=_source_pixels(), extra_tables=extras)
                    OWNER.store('baseline', _signature())
                    OWNER.store('delete', False)
                    _status('APPLIED SAFELY | controller %s | outputs OFF' % ('removed' if delete else 'updated'))
                else:
                    _status('VALID DRAFT | %s | outputs unchanged' % ('DELETE STAGED' if delete else 'hardware capability and full router checked'))
            _save(draft)
        _repaint()
        return True
    except Exception as error:
        _status('BLOCKED | ' + str(error))
        return False

def back():
    ROUTER.op('gico_port_config/ui_panel').openViewer()
'''


def build_interface_menu(owner):
    scope = dict(globals(), __name__='interface_widgets')
    path = ROOT/'pixelblaze_mapper/build_gico_port_config_ui.py'
    exec(compile(path.read_text(encoding='utf-8'),str(path),'exec'),scope,scope)
    canvas = owner.op('ui_panel')
    menu = scope['_node'](canvas,containerCOMP,'interface_menu')
    visible = bool(menu.par.display)
    rows = [{'address':'0.0.0.0','name':'Automatische Schnittstelle'}] + owner.fetch('local_interfaces',[])
    # Scrollable list retains every interface, including VPN/virtual adapters.
    height = min(360,38*len(rows))
    scope['_panel'](menu,516,645-height,600,height,200)
    scope['_set'](menu,'vscrollbar','on')
    for child in menu.children:
        child.par.display = False
    for index,row in enumerate(rows):
        button = scope['_button'](menu,'option_'+str(index),row['address']+' | '+row['name'],0,height-38*(index+1),600)
        scope['_click'](owner,'interface_option_'+str(index),button,"op('runtime').module.choose_interface(%r)" % row['address'])
    menu.par.display = visible


def build_controller_menu(owner):
    scope = dict(globals(), __name__='controller_widgets')
    path = ROOT/'pixelblaze_mapper/build_gico_port_config_ui.py'
    scope['__file__'] = str(path)
    exec(compile(path.read_text(encoding='utf-8'), str(path), 'exec'), scope, scope)
    canvas = owner.op('ui_panel')
    menu = scope['_node'](canvas, containerCOMP, 'controller_menu')
    rows = owner.op('runtime').module._router().controllers
    height = min(380, max(38, 38 * len(rows)))
    scope['_panel'](menu, 185, 717-height, 600, height, 220)
    scope['_set'](menu, 'vscrollbar', 'on')
    scope['_set'](menu, 'bgalpha', 1)
    for child in menu.children:
        child.par.display = False
    for index, controller in enumerate(rows):
        label = controller.name + ' | ' + controller.target_address
        button = scope['_button'](menu, 'option_'+str(index), label, 0, height-38*(index+1), 600)
        scope['_click'](owner, 'controller_option_'+str(index), button,
                        "op('runtime').module.choose_controller(%r)" % controller.name)
    if not rows:
        scope['_text'](menu, 'empty', 'Keine Controller vorhanden. Neue ID eingeben und NEW DRAFT.', 0, 0, 600, 38, 11)
    menu.par.display = False


def install_controller_picker(scope):
    """Update only the controller selection row and callback DAT, preserving drafts."""
    globals().update({key: value for key, value in scope.items() if key in
                      ('op', 'containerCOMP', 'buttonCOMP', 'textCOMP', 'fieldCOMP', 'panelexecuteDAT', 'tableDAT', 'textDAT', 'baseCOMP')})
    owner = op(OWNER)
    if owner is None:
        raise RuntimeError('Controller Ports must exist before picker installation')
    helpers = dict(globals(), __name__='controller_picker_widgets')
    path = ROOT/'pixelblaze_mapper/build_gico_port_config_ui.py'
    helpers['__file__'] = str(path)
    exec(compile(path.read_text(encoding='utf-8'), str(path), 'exec'), helpers, helpers)
    # Retain every field and OWNER storage entry; replacing code does not load or apply.
    owner.op('runtime').text = _runtime_source()
    canvas = owner.op('ui_panel')
    current = owner.op('runtime').module._saved().controller.name
    picker = helpers['_button'](canvas, 'btn_controller', current+'  v', 185, 721, 245)
    helpers['_click'](owner, 'controller_menu_click', picker, "op('runtime').module.toggle_controllers()")
    field = canvas.op('load_id')
    helpers['_panel'](field, 600, 721, 170, 32, 50)
    helpers['_text'](canvas, 'new_id_label', 'Neue Controller-ID:', 600, 753, 170, 22, 10)
    for name, x, width in (('load',440,150), ('new',780,140), ('delete',930,140), ('back',1080,170)):
        button = canvas.op('btn_'+name)
        if button is not None:
            button.par.x, button.par.w = x, width
    build_controller_menu(owner)
    return owner


def build():
    scope = dict(globals())
    scope['__name__'] = 'port_topology_helpers'
    path = ROOT / 'pixelblaze_mapper' / 'build_gico_port_config_ui.py'
    exec(compile(path.read_text(encoding='utf-8'), str(path), 'exec'), scope, scope)
    node, panel, text, field, button, click = (scope[name] for name in ('_node', '_panel', '_text', '_field', '_button', '_click'))
    gico = op('/project1/multi_controller_output/gico_port_config')
    owner = node(gico, baseCOMP, 'controller_ports')
    for child in owner.children:
        if child.type == 'panelexec':
            child.par.active = False
    runtime = node(owner, textDAT, 'runtime')
    runtime.text = _runtime_source()
    data = runtime.module.ensure_draft()
    draft = runtime.module._saved()
    page = int(owner.fetch('page', 0))
    canvas = panel(node(owner, containerCOMP, 'ui_panel'), 0, 0, 1280, 900, 10)
    canvas.viewer = True
    text(canvas, 'title', 'CONTROLLERS & PORTS | SAFE DRAFT', 20, 850, 1240, 36, 23)
    text(canvas, 'notice', 'GICO: equal reserved universes per physical port. Independent: use only when supported by the device. Needed universes are not hardware reserve.', 20, 800, 1240, 44, 12)
    config = runtime.module._router()
    text(canvas, 'known', 'LIVE CONTROLLERS: ' + ', '.join(item.name for item in config.controllers), 20, 763, 1240, 30, 12)
    text(canvas, 'load_label', 'CONTROLLER ID', 20, 721, 160, 32)
    picker = button(canvas, 'btn_controller', draft.controller.name + '  v', 185, 721, 245)
    click(owner, 'controller_menu_click', picker, "op('runtime').module.toggle_controllers()")
    # Free text is only needed when creating a new controller ID.
    field(canvas, 'load_id', draft.controller.name, 600, 721, 170)
    text(canvas, 'new_id_label', 'Neue Controller-ID:', 600, 753, 170, 22, 10)
    build_controller_menu(owner)
    controls = [('load', 'LOAD / REVERT', 440, 721, 150), ('new', 'NEW DRAFT', 780, 721, 140),
                ('delete', 'STAGE DELETE', 930, 721, 140), ('back', 'BACK TO GICO', 1080, 721, 170)]
    values = [('profile', draft.profile, 'PROFILE: gico_equal / independent'), ('target', draft.controller.target_address, 'TARGET IPv4'),
              ('interface', draft.controller.local_interface, 'LOCAL INTERFACE'), ('udp_port', draft.controller.port, 'UDP PORT'),
              ('first_ui', draft.controller.start_universe, 'START-UNIVERSE (ART-NET, AB 0)'),
              ('rate', draft.controller.rate, 'RATE FPS'), ('brightness', draft.controller.brightness, 'BRIGHTNESS 0..1'),
              ('enabled', int(draft.controller.enabled), 'ENABLED 0/1'), ('order', draft.controller.color_order, 'DEFAULT COLOR ORDER')]
    for index, (name, value, label) in enumerate(values):
        x = 20 + (index % 5) * 248
        y = 645 - (index // 5) * 78
        text(canvas, name + '_label', label, x, y + 31, 240, 28, 10)
        field(canvas, name, value, x, y, 232)
    canvas.op('interface').par.display = False
    picker = button(canvas,'btn_interface',runtime.module.interface_label(),516,645,232)
    click(owner,'interface_menu_click',picker,"op('runtime').module.toggle_interfaces()")
    build_interface_menu(owner)
    canvas.op('interface_menu').par.display = False
    poller = node(owner,executeDAT,'interface_poll')
    poller.text = "def onFrameStart(frame):\n    op('runtime').module.poll_interfaces()\n"
    poller.par.active = True
    poller.par.framestart = True
    # The obsolete opaque strip otherwise covers the top half of column labels.
    text(canvas, 'port_header', '', 20, 520, 1240, 30, 10).par.display = False
    columns = [('number','Port',20,45),('label','Bezeichnung',65,145),
               ('enabled','Aktiv\n0/1',215,50),('source','Erste Quell-LED\nleer = unzugeordnet',270,90),
               ('pixels','LED-Anzahl',365,80),('reserve','Reservierte\nUniversen',450,85),
               ('reverse','Umkehr\n0/1',540,50),('order','Farbfolge',595,75),
               ('target','Zielpixel-Offset\nleer = automatisch',675,100),
               ('derived','Benötigte / reservierte Universen | Paketadressen | Zuordnung',785,475)]
    for name,label,x,width in columns:
        heading = text(canvas,'column_'+name,label,x,497,width,54,10)
        scope['_set'](heading,'alignx','left')
        scope['_set'](heading,'textpaddingl',2)
    try:
        plan = runtime.module.build_topology(draft, source_pixels=runtime.module._source_pixels())
        by_number = {item.port.number: item for item in plan.ports}
    except Exception:
        by_number = {}
    for slot in range(6):
        index = page * 6 + slot
        row = draft.ports[index] if index < len(draft.ports) else None
        y = 457 - slot * 54
        prefix = 'row%d_' % slot
        widgets = [text(canvas, prefix + 'number', str(row.number) if row else '', 20, y, 45, 34, 13)]
        for name, value, x, width in (
            ('label', row.label if row else '', 65, 145), ('enabled', int(row.enabled) if row else 0, 215, 50),
            ('source', '' if row is None or row.source_start is None else row.source_start, 270, 90),
            ('pixels', row.pixel_count if row else 0, 365, 80), ('reserve', row.reserved_universes if row else 1, 450, 85),
            ('reverse', int(row.reverse) if row else 0, 540, 50), ('order', row.color_order if row else 'GRB', 595, 75),
            ('target', '' if row is None or row.destination_start is None else row.destination_start, 675, 100)):
            widgets.append(field(canvas, prefix + name, value, x, y, width))
        item = by_number.get(row.number) if row else None
        derived = ('%d / %d U | wire U%d-U%d | %s' % (item.used_universes, row.reserved_universes,
            item.first_wire_universe, item.last_wire_universe, 'routed' if item.routable else 'NOT ROUTED')) if item else 'Not validated'
        widgets.append(text(canvas, prefix + 'derived', derived, 785, y, 475, 36, 11))
        for widget in widgets:
            scope['_set'](widget, 'display', row is not None)
    controls += [('prev', 'PREV PAGE', 20, 138, 145), ('next', 'NEXT PAGE', 175, 138, 145),
                 ('add', 'ADD PORT', 330, 138, 145), ('remove', 'REMOVE PORT #', 585, 138, 185),
                 ('validate', 'VALIDATE DRAFT', 20, 82, 220), ('apply', 'SAFE APPLY (OUTPUT OFF)', 250, 82, 330)]
    field(canvas, 'remove_number', draft.ports[-1].number if draft.ports else '', 485, 138, 90)
    text(canvas, 'page', 'Page %d | %d ports | changes are drafts until SAFE APPLY' % (page + 1, len(draft.ports)), 780, 138, 480, 36, 12)
    for name, label, x, y, width in controls:
        control = button(canvas, 'btn_' + name, label, x, y, width)
        action = "op('runtime').module.back()" if name == 'back' else "op('runtime').module.act(%r)" % name
        click(owner, 'click_' + name, control, action)
    text(canvas, 'status', owner.fetch('message', 'DRAFT ONLY'), 20, 20, 1240, 50, 12)
    return owner


if globals().get('__name__') == '__main__' and 'op' in globals():
    build()
