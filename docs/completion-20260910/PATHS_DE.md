# Aktive Projektpfade portabel vorbereiten

`pixelblaze_mapper/workspace_relocation.py` bietet eine ausschließlich lesende Vorprüfung für bereits kopierte Projektdateien. Das Modul verschiebt und überschreibt keine Dateien und verändert weder TouchDesigner noch Hardware.

```python
from pixelblaze_mapper.workspace_relocation import prepare_relocation

report = prepare_relocation(
    {"scan_storage": storage_snapshot, "fields": field_snapshot},
    old_root="C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper",
    new_root="C:/Users/jbhtz/OneDrive/Desktop/Pictures/Documents/ChatGPT/LED-Touchdesigner-Controller/PixelblazeMapper",
)
# report["value"] ist eine unabhängige, vorbereitete Kopie.
# Der Runtime-Installer übernimmt sie in seiner eigenen Transaktion.
```

## Welche Referenzen aktualisiert werden

Ein vollständiger absoluter Pfad unterhalb der alten Projektwurzel wird seinem gleichnamigen Ziel unterhalb der neuen Wurzel zugeordnet. Verzeichnisse müssen dort bereits existieren. Dateien müssen an beiden Orten vorhanden und bytegleich sein. Der Bericht dokumentiert SHA-256, Dateigröße, alte/neue Pfade sowie die betroffenen JSON-Pfade. Wiederholt referenzierte Dateien werden innerhalb einer Vorbereitung nur einmal vollständig verglichen.

Die Rekursion unterstützt verschachtelte JSON-kompatible Dictionaries, Listen, Tupel und skalare Werte. Windows-Laufwerkspfade akzeptieren Groß-/Kleinschreibung und beide Schrägstrichformen; Zielwerte verwenden `/`. Die mit `|` getrennte Ansichtenliste bleibt einschließlich ihrer Trenner und Rand-Leerzeichen erhalten. Leere Einträge und der frühere Platzhalter `None` werden nicht als Dateipfad interpretiert.

Ein Pfadpräfix trifft nur an der tatsächlichen Wurzelgrenze: `PixelblazeMapper-backup` ist kein Unterordner von `PixelblazeMapper`. Freitext mit eingebetteten Pfaden, Statusmeldungen, URLs und als Text gespeicherte JSON-Dokumente werden nicht durch globale Zeichenersetzung verändert. Dictionary-Schlüssel bleiben ebenfalls unverändert. Pfadtraversierung, Alternate-Data-Stream-Syntax und symbolische Verknüpfungen außerhalb der jeweiligen Projektwurzel werden abgewiesen.

## Aktive Referenzen und historische Belege

Aktive Felder wie `workspace`, `views`, `manifest`, `capture_status.view_csv`, `offline_status.candidate`, `offline_status.output` und `result_review.path` können dadurch auf die kopierten Dateien zeigen. Historische Felder namens `observation_reference`, `registration_reference` und `quality_reference` bleiben standardmäßig unverändert. Das ist nachvollziehbare Herkunft und kein aktiver Dateipfadfehler. Bei ausdrücklich aktiven Strukturen kann der Aufrufer `preserve_keys=()` übergeben. Ein vorhandener `#sha256=…`-Beleg wird dann unverändert mitgeführt und gegen den tatsächlichen Dateiinhalt geprüft.

Unveränderliche Erfassungsdateien wie `capture.json`, Rekonstruktionsmanifeste und Qualitätsberichte behalten ihre ursprünglichen Bytes und historischen Wurzelangaben. Das Modul ändert lediglich die ausgewählten Verweise im zurückgegebenen Runtime-Snapshot. Die Wiederaufnahme einer kopierten Erfassung muss ihren aktuellen Erfassungsordner als Arbeitsordner verwenden und weiterhin die ursprünglichen LED-IDs und die Konfigurationsrevision prüfen; sie darf die ursprüngliche Manifestdatei nicht nachträglich umschreiben.

## Anwendung durch den Runtime-Installer

Der Installer muss zuerst laufende Aufnahme-/3D-Prozesse ausschließen, den aktuellen Snapshot erfassen und die vollständige Vorprüfung erfolgreich abschließen. Erst danach darf er alle ausgewählten Runtime-Felder und Speicherwerte gemeinsam übernehmen. Bei Fehlern ist der unveränderte ursprüngliche Snapshot wiederherzustellen.

Bereits vorbereitete Aufnahme- und Offline-Jobs müssen nach dem Ortswechsel verworfen und im neuen Arbeitsordner erneut vorbereitet werden. Insbesondere serialisierte Signaturen oder alte Worker-Manifeste werden nicht durch die Pfadprüfung zu neu autorisierten Jobs. Die gespeicherten Resultate lassen sich über ihre geprüften neuen Pfade wieder öffnen, ohne erneut zu erfassen. Historische Quelldateien und der alte Projektbaum bleiben unberührt.

Der Vorprüfbericht bestätigt Dateiinhalte zum Prüfzeitpunkt; er ersetzt weder diese Anwendungstransaktion noch die erneute Validierung bei einem späteren Scanstart. `tests/test_workspace_relocation.py` prüft Kopiengleichheit, fehlende Ziele, Typkonflikte, Pfadgrenzen, Ansichtenlisten, Herkunftsbelege, Unveränderlichkeit der Originaldaten und Manifestdateien sowie Wiederholbarkeit.
