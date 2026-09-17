"""A visible MATERIAL / SHOW switch in the Material Player panel.

Which of the two reaches the wall is decided by one menu parameter on
``/project1/madmapper_player_controls``. Finding that menu means leaving the
panel and clicking around the network, so the panel gets two buttons instead:
the active one is lit, one click changes sides.

Run inside TouchDesigner in a scope that has the TouchDesigner globals::

    scope = dict(globals()); scope['__name__'] = '__main__'
    exec(compile(open(PATH).read(), PATH, 'exec'), scope, scope)
    scope['build']()
"""

from __future__ import annotations

CONTROLS = "/project1/madmapper_player_controls"
ACTIVE = (0.09, 0.42, 0.34)
IDLE = (0.05, 0.09, 0.13)


def _get_or_create(parent, op_type, name):
    node = parent.op(name)
    if node is not None:
        return node
    node = parent.create(op_type, name)
    node.name = name
    return node


def _set(node, name, value):
    par = getattr(node.par, name, None)
    if par is not None:
        par.val = value


def build():
    controls = op(CONTROLS)
    if controls is None:
        raise RuntimeError("Material Player controls are missing")
    panel = controls.op("ui_panel")
    if panel is None:
        raise RuntimeError("Material Player panel is missing")

    logic = _get_or_create(controls, textDAT, "player_source_switch")
    logic.clear()
    logic.write(SOURCE_SWITCH_RUNTIME)

    # The lit state is an expression on Source, not a repaint callback: it then
    # cannot fall out of step when Source is changed anywhere else.
    is_show = "op('%s').par.Source.eval() == 'show'" % CONTROLS
    for name, label, x, lit_when in (("player_source_material", "MATERIAL", 20, "not " + is_show),
                                     ("player_source_show", "SHOW", 210, is_show)):
        button = _get_or_create(panel, buttonCOMP, name)
        for par, value in (("hmode", "fixed"), ("vmode", "fixed"), ("x", x), ("y", 20),
                           ("w", 180), ("h", 44), ("display", True), ("layer", 60),
                           ("buttontype", "momentary"), ("label", label), ("fontsize", 13),
                           ("fontcolorr", 0.92), ("fontcolorg", 0.95), ("fontcolorb", 0.98),
                           ("fontalpha", 1), ("bgalpha", 1), ("cursor", "pointer")):
            _set(button, par, value)
        for channel, active, idle in (("bgcolorr", ACTIVE[0], IDLE[0]),
                                      ("bgcolorg", ACTIVE[1], IDLE[1]),
                                      ("bgcolorb", ACTIVE[2], IDLE[2])):
            par = getattr(button.par, channel)
            par.expr = "%s if (%s) else %s" % (active, lit_when, idle)
        click = controls.op("click_" + name)
        if click is not None and click.type != "panelexec":
            click.destroy()
            click = None
        click = click or controls.create(panelexecuteDAT, "click_" + name)
        click.name = "click_" + name
        click.par.active = False
        click.par.fromop = button.path
        click.par.panels = button.path
        click.par.panelvalue = "lselect"
        for par, value in (("offtoon", True), ("ontooff", False), ("whileon", False),
                           ("whileoff", False), ("valuechange", False)):
            _set(click, par, value)
        click.clear()
        click.write("def onOffToOn(panelValue):\n    op(%r).module.choose(%r)\n    return\n"
                    % (logic.path, "show" if name.endswith("show") else "material"))
        click.par.active = True

    label = _get_or_create(panel, textCOMP, "player_source_label")
    label_expr = ("'Die Show laeuft auf der Wand.\\nMaterial-Regler wirken erst wieder auf MATERIAL.'"
                  " if (%s) else "
                  "'Das eingestellte Material laeuft auf der Wand.\\nSHOW spielt den Cue-Ablauf.'" % is_show)
    for par, value in (("hmode", "fixed"), ("vmode", "fixed"), ("x", 400), ("y", 20),
                       ("w", 340), ("h", 44), ("display", True), ("layer", 10),
                       ("type", "multiline"), ("font", "Verdana"), ("fontsize", 11),
                       ("fontalpha", 1), ("fontcolorr", 0.55), ("fontcolorg", 0.63),
                       ("fontcolorb", 0.72), ("bgalpha", 1), ("bgcolorr", 0.015),
                       ("bgcolorg", 0.025), ("bgcolorb", 0.038), ("alignx", "left"),
                       ("aligny", "center"), ("textpaddingl", 10), ("clickthrough", True)):
        _set(label, par, value)
    label.par.text.expr = label_expr

    stale = controls.op("player_source_change")
    if stale is not None:
        stale.destroy()
    print({"owner": panel.path, "buttons": 2, "productionTouched": False,
           "outputEnabled": False, "projectSaved": False})
    return panel


SOURCE_SWITCH_RUNTIME = '''# MATERIAL / SHOW switch for the Material Player panel.
CONTROLS = op('/project1/madmapper_player_controls')
PANEL = CONTROLS.op('ui_panel')
ACTIVE = (0.09, 0.42, 0.34)
IDLE = (0.05, 0.09, 0.13)


def material_source():
    """Which of the two material sources the browser last activated.

    Core effects and imported materials are two different Source values, so
    returning to 'material' has to pick the one that matches what is loaded,
    or the switch would show a material the player is not playing.
    """

    key = ''
    runtime = op('/project1/material_state_runtime')
    if runtime is not None:
        try:
            key = str(runtime.module._current_key() or '')
        except Exception:
            key = ''
    if not key:
        store = op('/project1').fetch('p1_material_state_store', None) or {}
        key = str(store.get('active_key') or '')
    return 'materials' if key.startswith('core:') else 'imported'


def choose(target):
    CONTROLS.par.Source = 'show' if target == 'show' else material_source()
    repaint()
    return str(CONTROLS.par.Source.eval())


def repaint():
    current = str(CONTROLS.par.Source.eval())
    showing = current == 'show'
    for name, lit in (('player_source_material', not showing), ('player_source_show', showing)):
        button = PANEL.op(name)
        if button is None:
            continue
        colour = ACTIVE if lit else IDLE
        button.par.bgcolorr, button.par.bgcolorg, button.par.bgcolorb = colour
    label = PANEL.op('player_source_label')
    if label is not None:
        if showing:
            text = 'Die Show laeuft auf der Wand.\\nMaterial-Regler wirken erst wieder auf MATERIAL.'
        else:
            text = 'Das eingestellte Material laeuft auf der Wand.\\nSHOW spielt stattdessen den Cue-Ablauf.'
        if str(label.par.text.eval()) != text:
            label.par.text = text
    return current
'''
