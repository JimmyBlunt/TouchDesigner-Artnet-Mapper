"""B7 - Shortcut-Buttons beschriften.

Befund: die 14 open_*-Buttons rechts in /project1/shortcut_hub/help_panel
hatten ein leeres label. Im Panel standen 14 identische leere Kaestchen,
deren Funktion man raten musste - ausgerechnet in der Uebersicht, die als
Navigationsebene des Projekts dient.
"""

PANEL = '/project1/shortcut_hub/help_panel'
LABEL = 'ÖFFNEN'


def _buttons():
    return [c for c in op(PANEL).children if c.name.startswith('open_')]


def apply():
    for b in _buttons():
        b.par.label = LABEL
    return f'{len(_buttons())} buttons labelled {LABEL!r}'


def revert():
    for b in _buttons():
        b.par.label = ''
    return 'labels cleared'
