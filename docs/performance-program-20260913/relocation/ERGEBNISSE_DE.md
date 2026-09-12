# Projekt nach Ordnerumzug geprüft

Neuer Ordner: `E:/Daten/Dokumente/ChatGPT/LED-Touchdesigner-Controller/PixelblazeMapper`.
Aktueller gespeicherter Stand: `PixelblazeMapper_30FPS_PROGRAM_20260912_worker-clock-ui.6.toe`.
Der vor dem Umzug gespeicherte Stand `.2.toe` ist bytegleich angekommen.

## Gefundene und behobene Fehler

Beim ersten Start verwiesen eingebettete Python-Skripte auf den nicht mehr
vorhandenen OneDrive-Ordner. Dadurch wurden teilweise ältere Module aus
`C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper` geladen. Das führte zu
fehlenden Imports in Renderer und Sender.

Die projektspezifischen Importe priorisieren jetzt `project.folder`. Exakte
Root-Literale und aktive Datei-Literale darunter werden dynamisch daraus
abgeleitet. Insbesondere funktionieren die Pfade für Controller-Rebuild,
Materialsteuerung, Materialkatalog und Importordner wieder. Die unabhängige
Agentenprüfung fand drei zunächst übersehene Datei-Literale und einen
inkonsistenten Scanbibliothekscache; beides wurde korrigiert.

Aktive Scanpfade wurden auf existierende Ziele umgestellt. Scanplan und
Offline-Manifest wurden invalidiert, damit spätere Hardware-/3D-Aufträge frisch
vorbereitet werden. Die Scanbibliothek wurde neu eingelesen: zwölf vorhandene
Dateien, keine Indexfehler, konsistente Auswahl. Rohscans und historische
Dateimanifeste auf dem Datenträger wurden nicht umgeschrieben.

Zusätzlich trat eine Selbstabhängigkeitswarnung im Vorschau-ScriptCHOP auf.
Der NumPy-Positionscache lag in serialisiertem OP-Storage; beim Laden war zudem
ein ndarray-Vergleichsfehler in `pickleUtils` beobachtet worden. NumPy-Arrays
liegen jetzt in einem begrenzten, transienten Modulcache. Die internen
Koordinatencaches werden direkt gelesen/geschrieben, ohne eigene Cook-
Abhängigkeiten zu erzeugen. Externe Koordinaten- und Maskenabhängigkeiten
bleiben erhalten. Die Warnung verschwand unmittelbar; alle sieben Kanäle
mit jeweils 6.524 Werten waren vor/nach der Änderung exakt gleich.

## Prüfung und Grenzen

- Neuer Prozess lädt das Paket aus dem neuen E:-Ordner.
- Renderer, Quellmaske und Vorschau: jeweils 6.524 Samples.
- Aktives Mapping, Quellmaske, Controller und Routing stimmen per SHA-256
  mit dem geöffneten Umzugsstand überein.
- Scanarbeitsordner und alle vier aktuell eingetragenen View-Dateien existieren.
- Sender und native DMX-Ausgänge sind aus. Kein Hardwaretest durchgeführt.
- 24 Tests bestanden: NumPy-Packing/Maskierung, dynamische Quellgröße,
  Cache-Isolation/-Begrenzung und portable Skriptpfade.
- `after-restart.json` dokumentiert den ersten erfolgreichen Neustart;
  `final-checkpoint.json` den abschließend geprüften Stand.

Die vorhandene lokale MCP-Installation und einige existierende Materialmedien
unter `TouchDesignerLocal` bleiben gültige externe Abhängigkeiten. Sie wurden
nicht ohne Anlass kopiert oder gelöscht. Das gesamte Projekt ist daher noch
kein ausschließlich aus einem einzigen Ordner bestehendes Distributionspaket.

Die erste umfassende Prüfung wertete zu viele Parameter aus und blockierte
zeitweise das Fenster. Der unveränderte gespeicherte Stand wurde neu geöffnet;
die weiteren Prüfungen konzentrierten sich auf relevante Skripte, Pfadfelder
und Vorschauausgaben. Keine Nutzeränderungen wurden verworfen.

## Nachvollziehbarkeit

`before.json.gz` enthält den ursprünglichen Pfadsnapshot; `applied-changes.json`
und `code-path-followup.json` enthalten konkrete Vorher-/Nachher-Texte.
`library-cache-refresh.json` dokumentiert den Bibliothekswechsel.
`preview-cache-source.json` und `preview-cache-check.json` belegen die
Vorschaukorrektur. Die `.2.toe` bleibt als vorheriger Git-Stand erhalten.

Video `E:/LED2.mov` wurde parallel geprüft. Eingangsbericht unter
`measurements/gico-td-camera-001-video-review/BEFUNDE_DE.md`: lesbare
Zeitlupenfassung mit unterschiedlich schnellen Abschnitten. Noch kein
optisches FPS-Ergebnis für diesen neuen TD→GICO-Lauf.
