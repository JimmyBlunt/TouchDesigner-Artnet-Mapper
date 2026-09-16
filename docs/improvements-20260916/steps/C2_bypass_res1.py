"""C2 - Durchleite-Knoten aus der LED-Abtastung nehmen.

Befund: /project1/topto1 bezog sein Bild nicht ueber eine Leitung, sondern
ueber den Parameter 'top' = /project1/res1. res1 steht auf
outputresolution='useinput' und liefert damit exakt sein Eingangsbild
(512x512) unveraendert weiter.

Nachgewiesen, nicht vermutet: numpyArray() beider TOPs im selben Frame
verglichen - Form (512, 512, 4) identisch, maximale Abweichung 0.0 ueber
alle 1.048.576 Werte. res1 ist ein echter Durchleiter.

topto1 zeigt jetzt direkt auf /project1/material_gradient_player.

EHRLICHE EINSCHRAENKUNG: res1 kocht danach weiter (rund 34 Cooks/s), es
zieht ihn also noch etwas anderes - vermutlich ein offener Knoten-Viewer im
Netzwerkeditor. Der erhoffte eingesparte GPU-Blit faellt damit kleiner aus
als angenommen. Der Gewinn ist vor allem struktureller Natur: ein Glied
weniger in der Abtastkette. Wenn sich bestaetigt, dass res1 sonst niemand
braucht, kann er entfallen.
"""

TARGET = '/project1/topto1'
NEW_SOURCE = '/project1/material_gradient_player'
OLD_SOURCE = '/project1/res1'


def apply():
    op(TARGET).par.top = op(NEW_SOURCE)
    return f'{TARGET}.top -> {NEW_SOURCE}'


def revert():
    op(TARGET).par.top = op(OLD_SOURCE)
    return f'{TARGET}.top -> {OLD_SOURCE}'
