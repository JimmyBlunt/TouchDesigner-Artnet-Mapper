"""B7 - ZURUECKGENOMMEN. Die Buttons waren nie leer.

Ursprungsannahme (aus der Analyse): die 14 open_*-Buttons in
/project1/shortcut_hub/help_panel haetten ein leeres label und erschienen als
unbeschriftete Kaestchen.

Das war falsch, und der Fehler ist lehrreich. Der Parameter `label` ist
tatsaechlich leer - aber jeder Button traegt ein Kind-Text-COMP `scan_label`
mit dem Text 'OPEN'. Die Analyse stuetzte sich auf Aufnahmen ueber
opviewer-TOPs, und die rendern genau diese Kind-Beschriftungen nicht mit. Im
Bild sah man Flaechen ohne Text und schloss auf fehlende Beschriftung.

Das Setzen von `label` hat den Zustand verschlechtert: 'OEFFNEN' und 'OPEN'
lagen uebereinander, im Panel als "OeOPENN" lesbar. Sichtbar wurde das erst
im visuellen Review am echten Fenster.

Daher: label wieder geleert, sichtbar bleibt das originale 'OPEN'.

Lehre fuer kuenftige Analysen: opviewer-Aufnahmen taugen nicht zur
Beurteilung von Beschriftungen. Nur ein echtes geoeffnetes Panelfenster
zeigt, was der Benutzer sieht.
"""

PANEL = '/project1/shortcut_hub/help_panel'


def _buttons():
    return [c for c in op(PANEL).children if c.name.startswith('open_')]


def apply():
    """Zustand herstellen, wie er sein soll: label leer, scan_label sichtbar."""
    for b in _buttons():
        b.par.label = ''
    return f'{len(_buttons())} button labels cleared (scan_label shows OPEN)'


def revert():
    raise RuntimeError('this step is itself a revert; setting label again re-creates the overlap')
