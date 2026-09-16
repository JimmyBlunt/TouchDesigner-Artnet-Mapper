"""B8 - Treiber der nie genutzten 3D-Vorschau stilllegen.

Befund: /project1/pixelblaze_mapper/preview3d/animation_driver erzwang alle
4 Frames op('instance_data').cook(force=True) - fuer eine Ansicht, die seit
Projektstart kein einziges Mal gekocht hat (preview_out: totalCooks = 0,
cookFrame = -1). Die verbindliche Vorschau des Projekts ist
/project1/LED_PREVIEW_OUT mit ueber 55.000 Cooks.

Wie bei B1 wird nur der Treiber abgeschaltet, nichts geloescht. Wer die
Arbeit an preview3d wieder aufnimmt, setzt active zurueck auf True.
"""

TARGET = '/project1/pixelblaze_mapper/preview3d/animation_driver'


def apply():
    op(TARGET).par.active = False
    return f'{TARGET}.active = False'


def revert():
    op(TARGET).par.active = True
    return f'{TARGET}.active = True'
