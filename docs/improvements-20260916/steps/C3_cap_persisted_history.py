"""C3 - Dauerhafte Undo-Historie begrenzen.

Befund am laufenden System gemessen:
    current     9.314.988 Zeichen
    undo   30 Eintraege, 141.674.009 Zeichen
    redo    1 Eintrag,     9.314.988 Zeichen
    GESAMT    160.303.985 Zeichen = 152,9 MB in TouchDesigner-Storage

Jeder Undo-Schritt ist eine *vollstaendige* Kopie des Layout-Dokuments,
inklusive aller Scan-Punktwolken. Dieser Block wird bei jedem Projekt-Save
neu kodiert und bei jedem Laden wieder dekodiert - das ist der 82-Sekunden-
Cook von layout_scene_editor/instances und der Grund fuer das langsame
Speichern.

Aenderung in layout_session_storage.py: PERSISTED_HISTORY_DEPTH = 2.
layout_snapshot() und fixture_snapshot() sichern nur noch die zwei Schritte,
die dem aktuellen Stand am naechsten liegen. Die Auswahl erfolgt ueber
_persisted_tail(), das bewusst das *Ende* der Liste nimmt: restore_layout()
baut die Zeitachse als undo + [current] + reversed(redo) und prueft jedes
benachbarte Paar mit SceneHistory.commit. Nur der Schwanz haelt diese Kette
zusammenhaengend.

WICHTIG: Die Historie im laufenden Betrieb bleibt unveraendert vollstaendig.
Begrenzt wird ausschliesslich, wie viele Schritte einen Neustart ueberleben.

Zusaetzlich wurde der bereits gespeicherte Schnappschuss einmalig gekuerzt
(siehe trim_existing_snapshot), sonst haette die Altlast bis zum naechsten
Save weitergewirkt.

Messergebnis:
    Groesse      152,9 MB -> 34,8 MB   (minus 77,2 %)
    Wiederherstellung  82 s -> 2,59 s
    Daten: 11 Objekte, 6241 world points, Auswahl erhalten - unveraendert.

Weitergehend waere die eigentliche Loesung, die Scan-Punktwolken nur einmal
zentral zu halten statt in jedem Schritt erneut; dann waere auch Tiefe 30
billig. Das ist ein Eingriff ins Datenmodell und bewusst nicht Teil dieses
Durchgangs.
"""

EDITOR = '/project1/layout_scene_editor'
KEY = 'layout_session_snapshot'


def trim_existing_snapshot(depth=2):
    """Den bereits gespeicherten Schnappschuss einmalig kuerzen."""
    owner = op(EDITOR)
    snap = owner.fetch(KEY, None)
    if not snap:
        return 'no snapshot stored'
    before = len(snap['current']) + sum(len(x) for x in snap['undo']) + sum(len(x) for x in snap['redo'])
    trimmed = dict(snap)
    trimmed['undo'] = list(snap['undo'])[-depth:] if depth > 0 else []
    trimmed['redo'] = list(snap['redo'])[-depth:] if depth > 0 else []
    after = len(trimmed['current']) + sum(len(x) for x in trimmed['undo']) + sum(len(x) for x in trimmed['redo'])
    owner.store(KEY, trimmed)
    return f'{before:,} -> {after:,} characters'


def verify():
    """Beweist, dass sich der gekuerzte Stand noch wiederherstellen laesst."""
    import time
    from pixelblaze_mapper.layout_session_storage import restore_layout
    snap = op(EDITOR).fetch(KEY, None)
    start = time.perf_counter()
    result = restore_layout(snap)
    elapsed = time.perf_counter() - start
    scene = result.current.scene
    return (f'restored in {elapsed:.2f} s, {len(scene.objects)} objects, '
            f'{len(scene.world_points())} world points, undo depth {len(result._undo)}')


def apply():
    # Die Codeaenderung selbst liegt in pixelblaze_mapper/layout_session_storage.py
    # und ist versioniert; hier wird nur der Altbestand im Storage gekuerzt.
    return trim_existing_snapshot()


def revert():
    """Nicht umkehrbar: die verworfenen Historienschritte existieren nur noch
    in PixelblazeMapper_BASELINE_20260916.toe. Zum Zurueckholen dieses .toe
    laden. Die Codeaenderung selbst per git revert zuruecknehmen."""
    raise RuntimeError('history trim is one-way; restore from the baseline .toe')
