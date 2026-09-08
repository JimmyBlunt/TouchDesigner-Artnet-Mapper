# Guided Scan: echter Klicktest am 08.09.2026

## Umfang und Sicherheit

Test mit Zustimmung zum Überschreiben von Daten; vorhandene Sicherung:
`Backup/Implementation/PixelblazeMapper_20260908_UNIVERSE_ZERO.1.toe`.
Bedienung über echte Maus- und Tastatureingaben, einschließlich Dateiauswahl und Bestätigungsdialogen. Ergänzend wurden Koordinaten in der laufenden TouchDesigner-Instanz lesend geprüft. Kamera und LED-Ausgabe wurden nicht gestartet. Keine funktionalen Codeänderungen, keine Speicherung des Testzustands in die TOE.

## Ergebnisse

| Schritt | Eingabe / Aktion | Beobachtetes Ergebnis |
| --- | --- | --- |
| Offline-Auftrag | Zwei CSV-Ansichten aus `hinten/1`: `led_map_2d_20260904-115932.csv` und `led_map_2d_20260904-120233.csv`; PREPARE 3D OFFLINE JOB | Manifest gespeichert; Meldung ausdrücklich „nothing launched“. Kein automatischer Rekonstruktionsstart. |
| Navigation | BACK TO LAYOUT | Layout-Dialog geöffnet. |
| Teilersatz | Format `marimapper-csv`; Originalindizes `517-785`; lokale Zielindizes `517-785`; REPLACE REGION; Datei `oben_neu/led_map_3d.csv` | Nach Bestätigung im Entwurf ersetzt. Alle 269 XYZ-Tupel exakt gleich der Quelldatei. Gesamtzahl weiterhin 3.744. |
| 3D-Anzeige | 3D LAYOUT | Import sichtbar; rohe Scan-Koordinaten besitzen einen deutlich anderen Maßstab als das bestehende Layout. Dies ist keine bestätigte räumliche Registrierung. |
| Übernahme vorbereiten | Keep live routes `YES`; VALIDATE / PREPARE; Modus 3D, Projektion YX; Bestätigung | BLOCKED: `Projected 3D UV outside 0..1; use explicit fixture UV placement instead of silent normalization/clamping`. Keine Aktivierung. |
| Rückweg | UNDO → REDO | Ersatz rückgängig gemacht und wiederhergestellt; nach REDO erneut alle 269 XYZ exakt bestätigt. |
| Wiederherstellung | Abschließend UNDO und FRAME / RESET VIEW | Originalentwurf wieder sichtbar. Alle 3.744 Entwurfskoordinaten exakt gleich der aktiven Map. |

Quellwurzel:
`C:\Users\jbhtz\OneDrive\Desktop\Pictures\Documents\~Projects~\Marrimapper-LED-Schrank`.

Der Offline-Testauftrag wurde in
`docs/implementation-2026-09-07/scan-realdata-20260908`
angelegt. Die bestehende Sitzung umfasste 256 Indizes (0–255); die historischen Ansichten decken nur einen Teil davon ab. Der Klicktest behauptet deshalb keine vollständige Rekonstruktion dieses 256-LED-Bereichs.

## Integritätsprüfung nach Wiederherstellung

- Aktive Map: 3.744 LEDs; Entwurf: 3.744 LEDs.
- Sämtliche XYZ-Koordinaten des wiederhergestellten Entwurfs stimmen exakt mit `map_active` überein.
- SHA-256 von `map_active.text` vor und nach dem Test unverändert:
  `dbcaf4e56561ae3bc68731d89e12e661502a42950274886b1f75645d17f1282f`.
- APPLY wurde nicht ausgeführt; die vorbereitende Prüfung blockierte bereits.
- Testpfade, Format-/Bereichsfelder und Keep-live-routes-Eingabe verbleiben als nicht gespeicherter UI-Testzustand. Geometrie wurde zurückgesetzt.

## Offene Punkte und nächster sinnvoller Schritt

1. Offline-Auftrag ist bislang nur Vorbereitung. Für einen durchgehenden Dialogablauf fehlen Start, Fortschritt und Ergebnisübergabe der Rekonstruktion.
2. Rohe Scan-Koordinaten lassen sich korrekt im Entwurf ersetzen, sind aber nicht automatisch zum Bestandslayout registriert. Registrierung und Material-UV-Zuordnung müssen explizit erfolgen; keine stille Normalisierung oder Umgehung der Sperre.
3. Erst nach dieser Ausrichtung einen vollständigen PREPARE/APPLY/Rücknahme-Test durchführen. Eine erfolgreiche aktive Übernahme oder Hardwareprüfung wurde hier ausdrücklich nicht nachgewiesen.

Dies ist ein gezielter Klicktest des beschriebenen Ablaufs, keine Vollabdeckung aller Dialogbuttons. Die Bildschirmbelege sind in den Computer-Use-Ausgaben dieser Unterhaltung sichtbar; separate Screenshotdateien wurden für diesen Test nicht archiviert.

## Fortsetzung: aktive Übernahme, Scanplanung und 2D-Roundtrip

Weitere echte Klicktests nach ausdrücklicher Aufforderung zum Fortsetzen:

| Test | Ergebnis / Messung |
| --- | --- |
| Gültige 3D-Transformation | Translate Z = `0.01`, SET TRANSFORM: alle 3.744 Entwurfspunkte genau um 0,01 in Z verschoben, X/Y unverändert. |
| PREPARE → APPLY, Modus 3D/YX, Keep live routes YES | Erfolgreich. Aktive Map entspricht dem Entwurf für alle 3.744 Punkte. Größte Abweichung der nachgelagerten Float-Geometrie in LedMap/null4: `2.97878630650672e-08`. Routingtabellen unverändert, Sender aus. |
| REVERT LAST → UNDO | Aktive Übernahme und danach Entwurfstransformation zurückgenommen. Vollständiger vom Apply-Adapter erfasster Zustand entspricht wieder seinem Ausgangshash. |
| Layout → GUIDED SCAN | **Fehler:** `BLOCKED — Cell does not exist.` Die Scan-Sitzung und Quellauswahl wurden vorher bereits verändert. Kein atomarer Abbruch. |
| CHECK SCAN PLAN nach dieser Übergabe | Korrekte Sperre `unrouted source: 1184`; der gesamte ungruppierte Layout-Snapshot ist nicht vollständig im aktuellen Router zugeordnet. Dies ist von dem Navigationsfehler zu unterscheiden. |
| NEW CAPTURE → CREATE ACQUISITION | Erfolgreich mit TEST_249, Ziel 10.0.0.249, Interface 10.0.0.125, Startuniversum 120, 256 LEDs, 30 FPS, RGB. Keine Kamera und keine Ausgabe gestartet. |
| CHECK SCAN PLAN für separate Erfassung | Erfolgreich: U120–U121, 510 Kanäle, maximal 5 %. Alle 256 abgeleiteten Kanaladressen geprüft. |
| PREPARE 3D OFFLINE JOB ohne Ansichten | Korrekt abgewiesen: mindestens zwei unterschiedliche CSV-Ansichten erforderlich. |
| START SCAN / NEXT VIEW → Cancel | Bestätigungsdialog nennt den richtigen Controller und U120–121; Abbruch startet keinen Capture-Prozess. Keine Bestätigung von Start Scan. |
| 2D: linke Fläche um 15 Bildpunkte nach rechts ziehen | Nur output_transform.translation.x geändert: von -0.09805013927576611 auf -0.05208913649025081. UV unverändert. Strg+Z stellt Ausgangszustand wieder her. |
| 2D: rechte Materialfläche um 14 Bildpunkte nach rechts ziehen | Nur uv_transform.translation.x geändert: von 0 auf 0.03899721448467969. Ausgabe-Transformation und aktive 3D-Map unverändert. Anzeige meldet 2.573 außerhalb 0–1 liegende Samples. Strg+Z stellt Ausgangszustand wieder her. |
| EXPORT WORKSPACE → OPEN SCENE | Echte Dateidialoge verwendet. Export und Wiederimport stimmen strukturell exakt mit LayoutDocument und FixtureScene überein, einschließlich LED-Identitäten und Transformationen. |

Testexport (nur lokales Testartefakt, nicht produktive Map):
`scan-realdata-20260908/click-workspace-roundtrip.json` (3.571.974 Bytes).
SHA-256: `5e1a78ff5161d44093e61f349637db17043c57504b94ce3cd7f361ff2b6c7de3`.

### Universengrenzen der separaten Erfassung

| Lokale LED, ab 0 | Art-Net-Universum, ab 0 | Erstes RGB-Kanalbyte, ab 0 |
| --- | --- | --- |
| 0 | 120 | 0 |
| 169 | 120 | 507 |
| 170 | 121 | 0 |
| 255 | 121 | 255 |

Für alle LEDs gilt: Universum = `120 + index // 170`, Byteposition = `3 * (index % 170)`. Es wurden ausschließlich die geplanten Adressen geprüft, keine Pakete an Hardware gesendet.

### Eingrenzung des neuen Navigationsfehlers

`build_scan_session_ui.py::_show_scope` schreibt mittels `node[0,0] = ...` in das Ankerfeld. Die laufende leere Text-DAT dieses Feldes besitzt 0 Zeilen und 0 Spalten. `stage_scene` setzt zuvor bereits Sitzung und Auswahl zurück. Das erklärt den beobachteten Teilzustand und ist ein zu behebender Integrationsfehler; im Testlauf wurde er nicht durch direktes Befüllen oder Umgehen kaschiert.

### Automatische Regression in dieser Fortsetzung

- 202 Tests: scan_worker, scan_session, scan_routing, scan_capture, layout_scene, layout_scene_adapter, layout_apply, guided_scan_live, standalone_scan.
- Weitere 83 Tests: mapper_io, fixture_scene, layout_fixture_td, layout_active_snapshot, layout_session_storage.
- Insgesamt **285 bestanden**. Diese automatischen Tests decken den realen leeren Text-DAT-Integrationsfehler offensichtlich nicht ab. Erfolgreiche Unit-Tests sind deshalb keine vollständige UI-Freigabe.

### Abschließende Integrität und verbleibende Testgrenzen

Alle 3.744 Entwurfskoordinaten entsprechen wieder der aktiven Map. Vollständiger Apply-Adapter-Ausgangshash vor Übernahme und nach Rücknahme:
`1732f23a71fbae2f36ae39c6c8aa916e12d02073f2719c29aa3e39c438ce9245`.
Der oben dokumentierte map_active-Hash ist ebenfalls unverändert. Sender deaktiviert, kein Capture-Prozess, keine aktiven nativen DMX-Ausgänge. Die aktive Testübernahme wurde nicht in eine TOE gespeichert.

Die UI verbleibt im wieder geöffneten Testworkspace (identische Daten), Ansicht 2D, Fenster maximiert. Die separate 256-LED-Erfassung ist vorbereitet, aber nicht gestartet; Ansichten sind dort leer. Vorherige CSV-Dateien und Manifestdateien bleiben auf Datenträger erhalten.

Nicht als abgeschlossen/bestanden beansprucht: echter Kamera-/LED-Scan, Hardwareempfang, räumliche Registrierung eines Rohscans, vollständiger Scan→Rekonstruktion→Review→Merge-Ablauf, aktive 2D-Übernahme und sämtliche übrigen Feld-/Buttonkombinationen. Der durchgehende Scanablauf ist wegen der dokumentierten Implementierungslücken nicht freigabefähig. Weitere Testwiederholungen allein beheben diese Lücken nicht; zunächst Fehlerkorrektur und danach gezielter Nachtest nötig.

## Korrektur und echter Nachtest: Layout → Guided Scan

Nach Freigabe wurden die Eingabefelder auf Text-DAT-Textzugriff umgestellt.
Leere Text-DATs müssen keine Zelle `[0,0]` mehr besitzen. Der UI-Aufbau und
die separate Erfassung benutzen ebenfalls den leeren-sicheren Leser.
Beide Scope-Felder werden vorab geprüft; fehlende Felder verändern die Sitzung
nicht. Ein fehlgeschlagener Feldschreibvorgang nimmt die Feldänderungen zurück.
Ein laufender Capture-Prozess blockiert die Neuauswahl. Beim erfolgreichen
Staging werden vorherige Capture-Freigabe, Worker-Plan und Dry-run verworfen.

- **290 automatische Tests bestanden**, einschließlich fünf neuer Tests in
  `tests/test_scan_ui_staging.py`. Diese führen den tatsächlich generierten
  Runtime-Code mit Text-DAT-Doubles aus, deren Zellzugriff immer fehlschlägt.
- Nur die Guided-Scan-Runtime wurde in der laufenden Anwendung neu geladen;
  kein Router-/Ausgabe-Neuaufbau.
- **Echter Mausklick** auf `GUIDED SCAN` im Layoutfenster öffnete den Dialog.
  Anzeige: `STAGED: 3744 LEDs + 0 anchors`. Das Ankerfeld hatte vor dem Klick
  tatsächlich null Zeilen. Kein `Cell does not exist` mehr.
- Nachprüfung per Leseschnittstelle: Anker leer, `capture_plan = null`,
  Worker-Plan leer, Sender aus, kein aktiver nativer DMX-Ausgang.
- Aktive Map weiterhin SHA-256
  `dbcaf4e56561ae3bc68731d89e12e661502a42950274886b1f75645d17f1282f`.

Speicherung nach Plain-Storage-/Pickle-Vorprüfung erfolgreich:
`Backup/Implementation/PixelblazeMapper_20260908_SCAN_STAGING_FIXED.1.toe`.
TouchDesigner meldete ausdrücklich `saved successfully`; keine Projektfehler
bei der Vorprüfung. Wiederöffnen dieser neuen TOE ist hier noch nicht getestet.
Die Scanansicht enthält nun die Layoutauswahl, nicht mehr die separate
256-LED-Erfassung; deren bisherige Dateien bleiben unverändert erhalten.

Dieser Fix schließt den Navigationsfehler, nicht die oben dokumentierten
Rekonstruktions-/Registrierungs-/Review-Lücken. Für diese bleibt ein eigener
Implementierungs- und Abnahmeschritt erforderlich; Schutzprüfungen wurden
nicht umgangen und keine Kamera-/LED-Aufnahme gestartet.
