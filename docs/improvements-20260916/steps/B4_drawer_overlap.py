"""B4 - Ueberlagerung der Parameterschublade im Material Browser aufloesen.

Befund: native_parameter_drawer verankert seine Oberkante bei y=820 und ist
232 px hoch, deckt also das Band y=588..820 ab. Genau dort liegen die
Suchleiste, die fuenf Slider, die Speed-/Gradient-Buttons, Paging und acht
der Vorschaukarten. Keines dieser Elemente wurde beim Oeffnen ausgeblendet -
es lagen zwei anklickbare Ebenen uebereinander.

Am laufenden System gemessen: 33 Bedienelemente liegen im verdeckten Band.

Umsetzung: toggle_native_parameters() blendet sie beim Oeffnen aus und beim
Schliessen wieder ein. Welche Elemente betroffen sind, wird zur Laufzeit aus
der tatsaechlichen Geometrie berechnet statt fest verdrahtet - so bleibt es
richtig, wenn das Layout spaeter verschoben wird.

Geprueft: alle drei Bedienwege (native_params_open_click,
native_params_close_click, native_params_back_top_click) rufen
toggle_native_parameters() auf; es gibt keinen Pfad, der display direkt
setzt. Der Wiederherstellungsweg ist damit garantiert.

Test am laufenden System: oeffnen -> 33 ausgeblendet, schliessen ->
Ausgangszustand vollstaendig wiederhergestellt, keine Abweichung.

KORREKTUR 17.09.2026: Die erste Fassung hat den Wiederherstellungs-Schluessel
bei jedem Oeffnen ueberschrieben. _controls_behind_drawer() ueberspringt
bereits ausgeblendete Elemente, also fand ein zweites Oeffnen nichts mehr und
speicherte eine leere Liste - danach blendete Schliessen nichts mehr ein und
der Browser blieb leer. Am laufenden System waren so 81 Elemente dauerhaft
unsichtbar, darunter Vor/Zurueck, Seitenanzeige, Suchfeld und alle Karten.

Zweiter Faktor: _layout_native_drawer() setzt die Hoehe der Schublade nach der
Anzahl sichtbarer Parameter. Sie war 456 statt der gemessenen 232 px hoch, das
verdeckte Band also 364..820 statt 588..820 - deutlich mehr als die 33
Elemente der urspruenglichen Messung.

Behoben durch Zusammenfuehren statt Ersetzen. Regressionstest am laufenden
System: oeffnen -> 80 gespeichert, erneut oeffnen -> weiterhin 80,
schliessen -> Panel bitgleich wie vorher, Schluessel geloescht.
"""

TARGET = '/project1/material_browser/unified_runtime'

HELPERS = '''DRAWER_SHADOW_KEY = 'native_drawer_hidden'

def _controls_behind_drawer():
    """Panel children sitting in the vertical band the open drawer covers.

    Computed live rather than hardcoded so it stays correct when the layout
    moves. Audit 2026-09-16, step B4: the drawer anchors its top edge at
    y=820 and is ~232 px tall, which is exactly where the search bar, the
    five sliders and the speed/gradient buttons live. Nothing hid them, so
    two clickable layers sat on top of each other.
    """
    drawer = OWNER.op('native_parameter_drawer')
    if drawer is None:
        return []
    bottom = drawer.par.y.eval()
    top = bottom + drawer.par.h.eval()
    found = []
    for child in OWNER.children:
        if child is drawer:
            continue
        if not hasattr(child.par, 'y') or not hasattr(child.par, 'display'):
            continue
        if not bool(child.par.display.eval()):
            continue
        y = child.par.y.eval()
        h = child.par.h.eval() if hasattr(child.par, 'h') else 0
        if y < top and (y + h) > bottom:
            found.append(child)
    return found

def _hide_controls_behind_drawer():
    """Merge into the restore list; never replace it.

    _controls_behind_drawer() skips children that are already hidden, so a
    second open finds nothing and would store an empty list - after which
    closing the drawer restores nothing and the browser stays blank. The
    drawer also grows with the parameter count, so a re-render can cover
    controls the first pass did not, which is why this merges instead of
    only bailing out early.
    """
    hidden = list(OWNER.fetch(DRAWER_SHADOW_KEY, []) or [])
    for child in _controls_behind_drawer():
        child.par.display = False
        if child.name not in hidden:
            hidden.append(child.name)
    OWNER.store(DRAWER_SHADOW_KEY, hidden)
    return hidden

def _restore_controls_behind_drawer():
    for name in OWNER.fetch(DRAWER_SHADOW_KEY, []) or []:
        node = OWNER.op(name)
        if node is not None and hasattr(node.par, 'display'):
            node.par.display = True
    OWNER.unstore(DRAWER_SHADOW_KEY)

'''

ANCHOR = 'def toggle_native_parameters(show=None):'

OLD_BODY = """    drawer.par.display = bool(show)
    if show:
        render_native_parameters()
    return bool(show)"""

NEW_BODY = """    drawer.par.display = bool(show)
    if show:
        render_native_parameters()
        _hide_controls_behind_drawer()
    else:
        _restore_controls_behind_drawer()
    return bool(show)"""


def apply():
    dat = op(TARGET)
    text = dat.text
    if '_hide_controls_behind_drawer' in text:
        return 'already applied'
    if OLD_BODY not in text or ANCHOR not in text:
        raise RuntimeError('anchors not found - unified_runtime has changed')
    text = text.replace(OLD_BODY, NEW_BODY, 1)
    text = text.replace(ANCHOR, HELPERS + ANCHOR, 1)
    dat.text = text
    return f'{TARGET} patched'


def revert():
    dat = op(TARGET)
    text = dat.text
    if '_hide_controls_behind_drawer' not in text:
        return 'nothing to revert'
    # Erst sicherstellen, dass nichts ausgeblendet zurueckbleibt.
    owner = op('/project1/material_browser')
    for name in owner.fetch('native_drawer_hidden', []) or []:
        node = owner.op(name)
        if node is not None and hasattr(node.par, 'display'):
            node.par.display = True
    owner.unstore('native_drawer_hidden')
    text = text.replace(HELPERS, '', 1).replace(NEW_BODY, OLD_BODY, 1)
    dat.text = text
    return f'{TARGET} reverted'
