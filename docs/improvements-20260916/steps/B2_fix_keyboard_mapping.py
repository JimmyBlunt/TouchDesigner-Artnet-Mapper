"""B2 - Tastenbelegung des Layout-Editors reparieren.

Befund: /project1/layout_scene_editor/keyboard meldete "Some of your listed
keys are invalid". Die Analyse vermutete zunaechst, dass TouchDesigner
pgup/pgdn/esc erwartet und alle drei Tasten tot seien.

Ein direkter Test am laufenden System (jede Taste einzeln gesetzt, cook
erzwungen, Warnung geprueft) ergab das Gegenteil:

    up down left right   -> gueltig
    pageup pagedown      -> gueltig
    pgup pgdn            -> UNGUELTIG
    z y                  -> gueltig
    esc                  -> gueltig
    escape               -> UNGUELTIG

Kaputt war also nur Escape. PageUp/PageDown - und damit der Nudge auf der
dritten Achse - funktionierten die ganze Zeit.

Zwei Seiten mussten zusammengefuehrt werden: der Knoten liefert 'esc',
der Code in layout_scene_td.key() und layout_fixture_td.key() prueft auf
'escape'. Statt eine Seite umzuschreiben normalisiert jetzt
layout_scene_adapter.canonical_key() beide Schreibweisen, damit kuenftige
Aenderungen an einer Seite die andere nicht wieder still ausser Kraft setzen.
"""

TARGET = '/project1/layout_scene_editor/keyboard'
NEW_KEYS = 'up down left right pageup pagedown z y esc'
OLD_KEYS = 'up down left right pageup pagedown z y escape'


def apply():
    op(TARGET).par.keys = NEW_KEYS
    op(TARGET).cook(force=True)
    return f'{TARGET}.keys = {NEW_KEYS!r} (warnung: {op(TARGET).warnings() or "keine"})'


def revert():
    op(TARGET).par.keys = OLD_KEYS
    op(TARGET).cook(force=True)
    return f'{TARGET}.keys = {OLD_KEYS!r}'
