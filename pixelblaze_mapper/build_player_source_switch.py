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
# The running side is white, the other one stays dark: at a glance across the
# room the lit button is the only bright thing on the panel. A dark teal on
# near-black read as "both grey" and told the operator nothing.
ACTIVE_BG = (0.94, 0.96, 0.98)
ACTIVE_FG = (0.03, 0.05, 0.07)
IDLE_BG = (0.07, 0.10, 0.14)
IDLE_FG = (0.48, 0.56, 0.64)


def _get_or_create(parent, op_type, name):
    node = parent.op(name)
    if node is not None:
        return node
    node = parent.create(op_type, name)
    node.name = name
    return node


def _paint(button, lit_when):
    """Colour a button by writing the text COMP that actually draws it.

    A buttonCOMP does not paint itself from its own Bgcolor: its inner `text`
    child carries the whole look, and its stock expressions derive both fill
    and label from the parent's Color, multiplied down to 40%. Setting Bgcolor
    from outside therefore changed nothing at all, which is why both sides of
    the switch stayed the same grey. So the inner text is what gets the
    expressions - with the rollover brightening kept, because losing the hover
    feedback would be a step back.
    """

    text = button.op("text")
    if text is None:
        return button
    rollover = "%s.panel.rollover" % _literal(button.path)
    for channel, active, idle in (("bgcolorr", ACTIVE_BG[0], IDLE_BG[0]),
                                  ("bgcolorg", ACTIVE_BG[1], IDLE_BG[1]),
                                  ("bgcolorb", ACTIVE_BG[2], IDLE_BG[2])):
        _expression(getattr(text.par, channel),
                    "(%s if (%s) else %s) + 0.07 * %s" % (active, lit_when, idle, rollover))
    for channel, active, idle in (("fontcolorr", ACTIVE_FG[0], IDLE_FG[0]),
                                  ("fontcolorg", ACTIVE_FG[1], IDLE_FG[1]),
                                  ("fontcolorb", ACTIVE_FG[2], IDLE_FG[2])):
        _expression(getattr(text.par, channel), "%s if (%s) else %s" % (active, lit_when, idle))
    return button


def _literal(path):
    return "op('%s')" % path


def _expression(par, expression):
    """Bind a parameter to an expression and make sure it stays bound.

    Assigning par.val anywhere later drops the parameter back to CONSTANT and
    freezes whatever it happened to hold - which is exactly how the lit button
    ended up marking the side that was NOT running.
    """

    par.expr = expression
    # ParMode is a TouchDesigner global that is not always in the exec scope a
    # builder is run from; the enum on the parameter itself always is.
    par.mode = par.mode.__class__.EXPRESSION
    return par


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
                           ("buttontype", "momentary"), ("fontsize", 13),
                           ("fontalpha", 1), ("bgalpha", 1), ("cursor", "pointer")):
            _set(button, par, value)
        _paint(button, lit_when)
        # The running side also says so in words, for anyone who cannot rely on
        # the colour alone.
        _expression(button.par.label,
                    "'%s  *' if (%s) else '%s'" % (label, lit_when, label))
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
    _expression(label.par.text, label_expr)

    stale = controls.op("player_source_change")
    if stale is not None:
        stale.destroy()
    print({"owner": panel.path, "buttons": 2, "productionTouched": False,
           "outputEnabled": False, "projectSaved": False})
    return panel


SOURCE_SWITCH_RUNTIME = '''# MATERIAL / SHOW switch for the Material Player panel.
CONTROLS = op('/project1/madmapper_player_controls')
PANEL = CONTROLS.op('ui_panel')


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
    """Flip the player. The buttons repaint themselves.

    Their colours and labels hang off expressions on Source, so writing them
    here would only turn those expressions back into frozen constants - and
    then the panel would light whichever side happened to be lit at the time,
    forever.
    """

    CONTROLS.par.Source = 'show' if target == 'show' else material_source()
    return str(CONTROLS.par.Source.eval())


def repaint():
    """Kept for callers; the switch is expression-driven and needs no repaint."""

    return str(CONTROLS.par.Source.eval())
'''
