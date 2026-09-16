"""B5 - Statusanzeige des Routers drosseln.

Befund der Analyse: /project1/multi_controller_output/router_status_execute
rief refresh_status() bei jedem Frame auf. Die Funktion ist intern auf 4 Hz
gedrosselt, kostet aber pro tatsaechlichem Durchlauf rund 87 ms am Stueck -
also viermal pro Sekunde ein sichtbarer Haenger, fuer eine reine Anzeige.

Neu: einmal pro Sekunde. Fuer ein Status-Readout voellig ausreichend,
spart rund 260 ms Blockade pro Sekunde.
"""

TARGET = '/project1/multi_controller_output/router_status_execute'

NEW_TEXT = '''# Status display only. refresh_status() costs ~87 ms per call; at frame rate it
# fired four times a second (internal 4 Hz throttle) and produced a visible hitch
# each time. Once per second is ample for a status readout.
# Audit 2026-09-16, step B5. Revert: restore the unconditional call.

def onFrameStart(frame):
    if frame % 60 == 0:
        op('ui_callbacks').module.refresh_status()
    return
'''

OLD_TEXT = '''def onFrameStart(frame):
    op('ui_callbacks').module.refresh_status()
    return
'''


def apply():
    op(TARGET).text = NEW_TEXT
    return f'{TARGET} throttled to 1 Hz'


def revert():
    op(TARGET).text = OLD_TEXT
    return f'{TARGET} restored to every frame'
