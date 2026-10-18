"""Add a saved-show dropdown to the existing editor, preserving its runtime."""

PICKER_RUNTIME = '''

def _load_show_file(path):
    from pixelblaze_mapper.show_catalog import load_show_bundle
    if _state('recording', '0') == '1':
        raise ValueError('Aufnahme zuerst stoppen, dann Show wechseln.')
    loaded, recorded, materials = load_show_bundle(path)
    # Keep the replaced editor document recoverable for the current session.
    OWNER.store('previous_show_bundle', dict(show=show(), automation=automation_data(), materials=imported_data()))
    OWNER.store('selected_show_path', str(path))
    OWNER.store('selected_show_name', loaded.get('name', ''))
    _write_automation(recorded)
    _write_imported(materials)
    _set_state('selected', 0)
    _set_state('page', 0)
    _message('geladen: ' + str(path))
    write(loaded)


def picker_action(command):
    from pixelblaze_mapper.show_catalog import saved_shows
    from pathlib import Path
    menu = PANEL.op('ed_show_picker_menu')
    if command == 'close':
        menu.par.display = False
        return
    if command == 'open':
        if menu.par.display.eval():
            menu.par.display = False
            return
        entries = saved_shows(Path(project.folder) / 'shows')
        OWNER.store('saved_show_choices', entries)
        OWNER.store('saved_show_page', 0)
        menu.par.display = True
    entries = OWNER.fetch('saved_show_choices', [])
    page = OWNER.fetch('saved_show_page', 0)
    if command in ('previous', 'next'):
        page = max(0, min(max(0, (len(entries)-1)//8), page + (1 if command == 'next' else -1)))
        OWNER.store('saved_show_page', page)
    if command.startswith('choose_'):
        index = page * 8 + int(command.split('_')[1])
        if index < len(entries):
            menu.par.display = False
            try:
                _load_show_file(entries[index]['path'])
            except Exception as error:
                _message('%s: %s' % (type(error).__name__, error))
            repaint()
        return
    for slot in range(8):
        node = menu.op('choice_%d' % slot)
        index = page * 8 + slot
        node.par.display = index < len(entries)
        if index < len(entries):
            entry = entries[index]
            node.par.label = '%s  (%d Cues) [%s]' % (entry['label'], entry['cues'], entry['filename'])
    menu.op('empty').par.display = not bool(entries)
    menu.op('previous').par.display = page > 0
    menu.op('next').par.display = (page + 1) * 8 < len(entries)
'''


def build(scope):
    op = scope['op']
    owner = op('/project1/show_control')
    canvas = owner.op('control_panel')
    callbacks = owner.op('editor_callbacks')

    def setpar(node, name, value):
        par = getattr(node.par, name, None)
        if par is not None:
            par.val = value

    def node(parent, kind, name, x, y, w, h, label=None):
        n = parent.op(name) or parent.create(scope[kind], name)
        n.name = name
        for key, value in dict(hmode='fixed', vmode='fixed', x=x, y=y, w=w, h=h,
                               layer=250, display=True, bgalpha=1).items():
            setpar(n, key, value)
        if label is not None:
            setpar(n, 'label', label)
            setpar(n, 'buttontype', 'momentary')
            setpar(n, 'fontsize', 12)
        return n

    def button(parent, name, command, x, y, w, label):
        b = node(parent, 'buttonCOMP', name, x, y, w, 32, label)
        d = owner.op('picker_click_' + name) or owner.create(scope['panelexecuteDAT'], 'picker_click_' + name)
        d.name = 'picker_click_' + name
        d.par.active = False
        d.par.fromop = b.path
        d.par.panels = b.path
        d.par.panelvalue = 'lselect'
        for key in ('ontooff', 'whileon', 'whileoff', 'valuechange'):
            setpar(d, key, False)
        d.par.offtoon = True
        d.text = 'def onOffToOn(panelValue):\n    op(%r).module.picker_action(%r)\n' % (callbacks.path, command)
        d.par.active = True
        return b

    title = canvas.op('ed_title')
    if title is not None:
        title.par.w = 400
    button(canvas, 'ed_show_picker', 'open', 450, 952, 410, 'SHOW AUSWAEHLEN  v')
    menu = node(canvas, 'containerCOMP', 'ed_show_picker_menu', 450, 612, 530, 336)
    for slot in range(8):
        button(menu, 'choice_%d' % slot, 'choose_%d' % slot, 4, 296-slot*33, 522, '')
    button(menu, 'empty', 'close', 4, 296, 522, 'Keine gespeicherten Shows')
    button(menu, 'previous', 'previous', 4, 4, 125, '< Zurueck')
    button(menu, 'next', 'next', 134, 4, 125, 'Weiter >')
    button(menu, 'close', 'close', 364, 4, 162, 'Schliessen')
    menu.par.display = False
    callbacks.text = replace_picker_runtime(callbacks.text)
    return menu


def replace_picker_runtime(source):
    """Upgrade only picker functions, preserving all other runtime patches."""
    import ast
    lines = source.splitlines(keepends=True)
    spans = [(node.lineno - 1, node.end_lineno) for node in ast.parse(source).body
             if isinstance(node, ast.FunctionDef) and node.name in ('_load_show_file', 'picker_action')]
    for start, end in sorted(spans, reverse=True):
        del lines[start:end]
    return ''.join(lines).rstrip() + '\n' + PICKER_RUNTIME


def install_workflow(scope):
    """Patch file actions and picker widgets without rebuilding the Show graph."""
    import ast
    from pathlib import Path
    callbacks = scope['op']('/project1/show_control/editor_callbacks')
    source_path = Path(__file__).with_name('build_show_editor.py')
    tree = ast.parse(source_path.read_text(encoding='utf-8'))
    embedded = next(ast.literal_eval(node.value) for node in tree.body
                    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'EDITOR_RUNTIME' for t in node.targets))
    replacement = next(node for node in ast.parse(embedded).body if isinstance(node, ast.FunctionDef) and node.name == '_apply')
    function = '\n'.join(embedded.splitlines()[replacement.lineno-1:replacement.end_lineno])
    original = callbacks.text
    current = next(node for node in ast.parse(original).body if isinstance(node, ast.FunctionDef) and node.name == '_apply')
    lines = original.splitlines(keepends=True)
    lines[current.lineno-1:current.end_lineno] = [function + '\n']
    from pixelblaze_mapper.show_timeline import install_editor_source
    callbacks.text = install_editor_source(''.join(lines))
    return build(scope)
