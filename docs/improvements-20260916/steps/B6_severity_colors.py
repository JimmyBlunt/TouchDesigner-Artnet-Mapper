"""B6 - Destruktive Aktionen im Layout-Editor farblich kennzeichnen.

Befund: alle 30 Buttons in /project1/layout_scene_editor/ui_panel sahen
identisch aus. btn_removeleds war optisch nicht von btn_zoom_in zu
unterscheiden. Die Bestaetigungsdialoge existieren bereits - nur die Optik
warnte nie.

KORREKTUR NACH DEM VISUELLEN REVIEW: Der erste Versuch setzte bgcolor am
Button selbst. Das hatte null sichtbare Wirkung. Jeder Button traegt ein
Kind-Text-COMP, dessen eigener Hintergrund (0.2/0.2/0.2) die Flaeche malt und
die Button-Farbe vollstaendig verdeckt. Erst das geoeffnete Panelfenster hat
das gezeigt - im Netzwerkeditor und in den Parametern sah alles richtig aus.

Dasselbe Muster wie beim zurueckgenommenen B7: was der Benutzer sieht, steht
in den Kind-COMPs, nicht am Button. Die Farbe wird jetzt an beiden Stellen
gesetzt, damit auch Raender nicht widersprechen.

Stufen, in der Helligkeit an die neutrale Flaeche (0.2 Grau) angeglichen,
damit die Staffelung informiert statt zu schreien:

    rot   0.40/0.10/0.09  irreversibel oder verwirft Arbeit
                          REMOVE LEDs, REPLACE REGION, REVERT LAST
    amber 0.36/0.22/0.05  wirkt auf das aktive System / ueberschreibt
                          APPLY (OUTPUT OFF), BIND ROUTE DRAFT,
                          EXPORT PIXELBLAZE 3D
    neutral 0.20/0.20/0.20  die uebrigen 24 Buttons, unveraendert

Am Bildschirm verifiziert.
"""

PANEL = '/project1/layout_scene_editor/ui_panel'
RED = (0.40, 0.10, 0.09)
AMBER = (0.36, 0.22, 0.05)
NEUTRAL_TEXT = (0.20, 0.20, 0.20)
NEUTRAL_BTN = (0.04, 0.17, 0.24)
DESTRUCTIVE = ('btn_removeleds', 'btn_replace', 'btn_revert')
LIVE = ('btn_apply', 'btn_route', 'btn_exportpb')


def _paint(names, button_colour, text_colour):
    painted = []
    for name in names:
        button = op(PANEL).op(name)
        if button is None:
            continue
        label = button.op('text')
        if label is not None:
            label.par.bgcolorr, label.par.bgcolorg, label.par.bgcolorb = text_colour
        button.par.bgcolorr, button.par.bgcolorg, button.par.bgcolorb = button_colour
        painted.append(name)
    return painted


def apply():
    painted = _paint(DESTRUCTIVE, RED, RED) + _paint(LIVE, AMBER, AMBER)
    return f'{len(painted)} buttons graded: {", ".join(painted)}'


def revert():
    _paint(DESTRUCTIVE + LIVE, NEUTRAL_BTN, NEUTRAL_TEXT)
    return 'all buttons back to neutral'
