"""Manual LED test controls, separate from acquisition configuration."""
import ipaddress
import json
from math import ceil
from pathlib import Path
from urllib.request import urlopen

OWNER = '/project1/guided_scan'


def field_value(field):
    """Read the current editor value, including an edit not yet committed by Enter."""
    panel = getattr(field, 'panel', None)
    if panel is not None:
        return str(panel.field.val).strip()
    return field.op('string').text.strip()


def port_settings(base, outputs, output_id):
    ports = [p for p in outputs if p.get('enabled')]
    selected = next((p for p in ports if p['id'] == output_id), None)
    if selected is None:
        raise ValueError('Einen aktivierten Ausgang waehlen')
    first = min(p['startUniverse'] for p in ports)
    end = max(p['startUniverse'] + ceil(p['pixelCount']/170) for p in ports)
    settings = {k: base[k] for k in ('target', 'interface', 'rate', 'order')}
    settings.update(name='LED SEARCH OUT %d' % (output_id+1), universe=selected['startUniverse'],
                    count=selected['pixelCount'], frame_start_universe=first,
                    frame_universe_count=end-first)
    from .standalone_scan import routing
    routing(settings)
    return settings


def selected_settings(op):
    owner = op(OWNER)
    panel = owner.op('led_search_panel')
    device = owner.fetch('led_search_device', None)
    if not device:
        raise ValueError('AUSGAENGE LADEN druecken und einen Ausgang waehlen')
    address = field_value(panel.op('controller'))
    if address != device['target']:
        raise ValueError('IP geaendert: AUSGAENGE LADEN druecken')
    from .led_search import legacy_settings_from_ui
    base = dict(owner.fetch('standalone_capture', None) or legacy_settings_from_ui(op))
    base['target'] = address
    return port_settings(base, device['outputs'], owner.fetch('led_search_output', None))


def render(op):
    from .scan_library_ui import style_button
    owner = op(OWNER); panel = owner.op('led_search_panel')
    device = owner.fetch('led_search_device', {}) or {}
    selected = owner.fetch('led_search_output', None)
    outputs = {p['id']: p for p in device.get('outputs', [])}
    for index in range(8):
        button = panel.op('output_'+str(index))
        item = outputs.get(index)
        label = ('OUT %d | %d LEDs' % (index+1, item['pixelCount'])) if item else 'OUT %d' % (index+1)
        button.par.label = label
        style_button(button, 'selected' if index == selected else 'secondary',
                     enabled=bool(item and item.get('enabled')))
    try:
        settings = selected_settings(op)
        panel.op('target').par.text = ('OUT %d | %s | U%d | %d LEDs | lokale Indizes 0-%d' %
            (selected+1, settings['target'], settings['universe'], settings['count'], settings['count']-1))
    except ValueError as error:
        panel.op('target').par.text = str(error)


def action(op, command, output_id=None):
    from . import led_search as search
    owner = op(OWNER); panel = owner.op('led_search_panel')
    try:
        if command == 'load':
            if search._thread and search._thread.is_alive():
                raise ValueError('Leuchttest zuerst mit STOP beenden')
            address = str(ipaddress.IPv4Address(field_value(panel.op('controller'))))
            with urlopen('http://'+address+'/api/config', timeout=2) as response:
                raw = response.read(256*1024+1)
            if len(raw) > 256*1024:
                raise ValueError('Controllerantwort zu gross')
            config = json.loads(raw)
            outputs = config.get('outputs')
            if (not isinstance(outputs, list) or not 1 <= len(outputs) <= 8
                    or any(type(p.get('id')) is not int or not 0 <= p['id'] < 8
                           or type(p.get('pixelCount')) is not int or not 1 <= p['pixelCount'] <= 100000
                           or type(p.get('startUniverse')) is not int or not 0 <= p['startUniverse'] < 32768
                           for p in outputs)
                    or len({p['id'] for p in outputs}) != len(outputs)):
                raise ValueError('Controller liefert keine gueltige Ausgangsliste')
            previous = owner.fetch('led_search_output', None)
            if previous not in [p['id'] for p in outputs if p.get('enabled')]:
                base = owner.fetch('standalone_capture', None) or search.legacy_settings_from_ui(op)
                previous = next((p['id'] for p in outputs if p.get('enabled')
                                 and p['startUniverse'] == base['universe']), None)
            owner.store('led_search_device', {'target': address, 'outputs': outputs})
            owner.store('led_search_output', previous)
        elif command == 'select':
            search.stop()
            owner.store('led_search_output', output_id)
            settings = selected_settings(op)
            # A port change keeps a valid index; larger previous indices reset to zero.
            index = int(field_value(panel.op('index')))
            if not 0 <= index < settings['count']:
                panel.op('index/string').text = '0'
        elif command == 'focus':
            panel.op('index').setKeyboardFocus(selectAll=True)
            return True
        else:
            raise ValueError('Unbekannte Aktion')
        render(op)
        search._message = ('AUSGAENGE GELADEN — OUT waehlen, LED-Index eingeben, SHOW druecken.'
                           if command == 'load' else 'AUSGANG GEWAEHLT — Leuchttest ist aus.')
        return True
    except Exception as error:
        search._message = 'BLOCKED: '+str(error)
        return False


def install(ns):
    import td
    from .scan_library_ui import style_button
    helpers = dict(ns, __name__='led_search_helpers')
    path = Path(__file__).with_name('build_gico_port_config_ui.py')
    exec(compile(path.read_text(encoding='utf-8'), str(path), 'exec'), helpers, helpers)
    node, panel, text, field, button, click = (helpers[k] for k in ('_node','_panel','_text','_field','_button','_click'))
    owner = ns['op'](OWNER)
    fresh = owner.op('new_capture_panel')
    if fresh is not None:
        fresh.op('btn_stage').par.w = 380
        b = button(fresh, 'btn_led_search', 'LED SEARCH / LED-SUCHE', 420, 20, 380)
        style_button(b)
        click(owner, 'click_led_search_open', b,
              "__import__('pixelblaze_mapper.led_search',fromlist=['act']).act(op,'open')")
    p = panel(node(owner, td.containerCOMP, 'led_search_panel'), 0, 0, 960, 560, 10)
    text(p, 'title', 'LED-SUCHE | AUSGANG UND LED AUSWAEHLEN', 20, 510, 920, 38, 19)
    text(p, 'controller_label', 'Controller-IP', 20, 460, 130, 32)
    old = p.op('controller/string')
    from .led_search import legacy_settings_from_ui
    base = owner.fetch('standalone_capture', None) or legacy_settings_from_ui(ns['op'])
    field(p, 'controller', old.text.strip() if old else base['target'], 150, 460, 200)
    p.op('controller').par.fieldmultiline = False
    ui_command = "__import__('pixelblaze_mapper.led_search_ui',fromlist=['action']).action(op,%r%s)"
    b = button(p, 'load_outputs', 'AUSGAENGE LADEN', 370, 460, 250)
    style_button(b)
    click(owner, 'click_led_search_load', b, ui_command % ('load', ''))
    for index in range(8):
        b = button(p, 'output_'+str(index), 'OUT '+str(index+1), 20+(index%4)*235, 405-(index//4)*48, 215)
        style_button(b)
        click(owner, 'click_led_search_output_'+str(index), b, ui_command % ('select', ', '+str(index)))
    text(p, 'target', '', 20, 309, 920, 38)
    text(p, 'legend', 'Weiss: gewaehlte LED | Gruen: davor | Rot: danach. Index beginnt bei 0.', 20, 266, 920, 34)
    text(p, 'input_label', 'LED-Index (ab 0)', 20, 219, 190, 34)
    old = p.op('index/string')
    editor = field(p, 'index', old.text.strip() if old else '0', 220, 220, 150)
    editor.par.fieldmultiline = False
    editor.par.fieldlock = False
    editor.par.fieldprotected = False
    click(owner, 'click_led_search_focus', editor, ui_command % ('focus', ''))
    command = "__import__('pixelblaze_mapper.led_search',fromlist=['act']).act(op,%r,%d)"
    # The shared widget helper treats name+digits as duplicate widgets. Avoid
    # names such as minus1/minus10, which made a rebuild delete the -10 button.
    for name in ('minus10', 'minus1', 'plus1', 'plus10'):
        old_button = p.op(name)
        if old_button is not None:
            old_button.par.display = False
            old_button.par.enable = False
        old_callback = owner.op('click_led_search_'+name)
        if old_callback is not None:
            old_callback.par.active = False
    for name, label, x, y, width, action_name, delta in (
        ('show','SHOW 30s',390,219,210,'show',0), ('stop','STOP / SCHWARZ',620,219,320,'stop',0),
        ('minus_ten','-10',20,169,215,'show',-10), ('minus_one','-1',255,169,215,'show',-1),
        ('plus_one','+1',490,169,215,'show',1), ('plus_ten','+10',725,169,215,'show',10),
        ('chase','LAUFLICHT AB INDEX | 2 SEKUNDEN PRO LED',20,119,920,'chase',0)):
        b = button(p, name, label, x, y, width)
        style_button(b, 'primary' if name == 'show' else 'secondary')
        click(owner, 'click_led_search_'+name, b, command % (action_name, delta))
    label = text(p, 'status', '', 20, 14, 920, 91)
    label.par.text.expr = "__import__('pixelblaze_mapper.led_search',fromlist=['status']).status()"
    callback = node(owner, td.executeDAT, 'led_search_exit')
    callback.text = "def onExit():\n    from pixelblaze_mapper.led_search import stop\n    stop()\n"
    callback.par.exit = True; callback.par.active = True
    render(ns['op'])
    return {'panel': p.path, 'output_started': False}
