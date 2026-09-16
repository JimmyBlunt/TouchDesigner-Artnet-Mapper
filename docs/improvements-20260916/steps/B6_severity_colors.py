"""B6 - Destruktive Aktionen im Layout-Editor farblich kennzeichnen.

Befund: alle 30 Buttons in /project1/layout_scene_editor/ui_panel trugen
dieselbe Grundfarbe 0.04/0.17/0.24. btn_removeleds sah exakt aus wie
btn_zoom_in. Die Bestaetigungsdialoge existieren bereits - die Optik sollte
die Warnung vorwegnehmen, statt sie dem Dialog allein zu ueberlassen.

Gestaffelt in drei Stufen, Helligkeit bewusst nah an der neutralen Farbe
gehalten, damit die Staffelung informiert statt zu schreien:

    rot   0.32/0.07/0.06  irreversibel oder verwirft Arbeit
    amber 0.30/0.17/0.03  wirkt auf das aktive System / ueberschreibt
    neutral 0.04/0.17/0.24 Navigation, Ansicht, Auswahl (24 Buttons)
"""

PANEL = '/project1/layout_scene_editor/ui_panel'
RED = (0.32, 0.07, 0.06)
AMBER = (0.30, 0.17, 0.03)
NEUTRAL = (0.04, 0.17, 0.24)
DESTRUCTIVE = ('btn_removeleds', 'btn_replace', 'btn_revert')
LIVE = ('btn_apply', 'btn_route', 'btn_exportpb')


def _paint(names, colour):
    for name in names:
        node = op(PANEL).op(name)
        if node:
            node.par.bgcolorr, node.par.bgcolorg, node.par.bgcolorb = colour


def apply():
    _paint(DESTRUCTIVE, RED)
    _paint(LIVE, AMBER)
    return f'{len(DESTRUCTIVE)} destructive + {len(LIVE)} live buttons coloured'


def revert():
    _paint(DESTRUCTIVE + LIVE, NEUTRAL)
    return 'all buttons back to neutral'
