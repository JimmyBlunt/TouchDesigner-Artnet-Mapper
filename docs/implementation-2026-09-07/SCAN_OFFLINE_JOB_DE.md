# Guided Scan: ausführbarer Offline-3D-Auftrag

Stand 2026-09-08. Dieser Schritt ergänzt die bisherige reine Manifest-Erstellung.
Er ersetzt weder die Kameraaufnahme noch die räumliche Registrierung oder die
explizite Layout-Freigabe.

## Bedienung

1. Mindestens zwei geeignete, überlappende MariMapper-2D-Ansichten erfassen oder
   deren CSV-Pfade im Feld `EXISTING 2D VIEW CSV PATHS` mit ` | ` getrennt eintragen.
   Quellindizes und Anker müssen zu den Dateien gehören.
2. `PREPARE 3D OFFLINE JOB` validiert die Ansichten und schreibt ein Manifest.
   Dabei startet noch keine Rekonstruktion.
3. `START 3D` öffnet eine Bestätigung. Erst `Start 3D` darin startet den
   installierten MariMapper-Python in einem separaten, unsichtbaren Prozess.
4. Die zusätzliche Statuszeile zeigt Zustand und vergangene Sekunden, nach
   erfolgreicher Rekonstruktion die Anzahl berechneter LEDs. Dies ist keine
   Prozentanzeige des internen COLMAP-Fortschritts.
5. `STOP 3D` fordert den Abbruch dieses Workers an. Ein separater Timer begrenzt
   die Laufzeit auf fünf Minuten, unabhängig vom TD-Timeline-Polling.
6. `3D RESULT / PATH` öffnet den technischen Ergebnis-DAT mit Kandidatenpfad,
   Logpfad, fehlenden beobachteten IDs und Review-Status. Die ergonomische
   grafische Ergebnisprüfung/Übergabe ist noch ein eigener offener Schritt.

`CANCEL SESSION` stoppt auch den Offline-Worker. Ein Abbruch löscht keine Dateien.
Für einen neuen Versuch ist ein neuer Auftrag mit neuem Ergebnisordner nötig;
vorhandene Ergebnisse werden nicht überschrieben.

## Sicherheit und Datenidentität

- Kein Kamera-/Art-Net-Code im Offline-Worker; kein automatischer Map-Apply.
- Start nur bei ausgeschalteten Ausgängen und ohne laufende Kameraaufnahme.
- Eine unveränderte vorbereitete Sitzung und passende Scope-Felder sind nötig.
- Native MariMapper-/pycolmap-Versionen und Upstream-Commit bleiben im Worker
  geprüft. Es werden keine Pakete installiert.
- Manifest wird für den Prozess als eigener Snapshot geschrieben; die tatsächlich
  gelesenen Quellbytes werden auf ihre vorbereiteten Hashes geprüft.
- Prozess/Timer/Dateihandle bleiben außerhalb des gespeicherten TD-States.
- Exitcode allein ist kein Erfolg: CSV-Format, endliche Werte, eindeutige IDs,
  erlaubter ID-Bereich und Übereinstimmung mit dem Workerbericht werden geprüft.
- Format entspricht MariMapper: `index,x,y,z,xn,yn,zn,error`.
- Fehlende IDs beziehen sich auf beobachtete IDs der Eingabedaten. Nicht einmal
  beobachtete Scope-LEDs sind darin nicht automatisch enthalten.
- Ergebnis bleibt `arbitrary_sfm`, `registration=false`, `layout_applied=false`.
  Kein stilles Normalisieren, Auffüllen oder Umnummerieren.

## Tests und beobachtete Ergebnisse

Der Testauftrag wurde über die TD-Testschnittstelle aus `manifest-3.json`
vorbereitet (sechs Originalansichten aus `hinten/1`, 894 Beobachtungen).
Dies ist kein behaupteter Maustest der Dateieingabe/Prepare-Kette.

`START 3D` und die Bestätigung wurden mit echten Mausklicks betätigt.
Der erste Lauf rekonstruierte erfolgreich, wurde aber von einer zunächst zu
engen CSV-Spaltenprüfung abgelehnt. Die Prüfung und Tests wurden auf das echte
achtspaltige Format korrigiert. Beim erneuten Klicklauf:

- Exitcode 0, nach 2,7 Sekunden `review_required`, 196 LEDs.
- Fehlende beobachtete IDs: 59, 70, 72, 73, 74, 78, 80.
- Ergebnisordner:
  `scan-realdata-20260908/ui-offline-result-3bff44d8-97c0-4ae3-894d-a191422d7b33`.
- Keine TD-Projektfehler, Sender aus, keine aktiven nativen DMX-Ausgänge.
- Aktive Map SHA-256 unverändert:
  `dbcaf4e56561ae3bc68731d89e12e661502a42950274886b1f75645d17f1282f`.
- Vorherige Scan-Sitzung und Eingabefelder nach dem Test wiederhergestellt.

Beim anschließenden Versuch, die Ergebnisanzeige anzuklicken, traf die
Fensterkoordinatensteuerung stattdessen `CANCEL SESSION`. Daher wird dieser
Button ausdrücklich noch nicht als erfolgreich klickgetestet bewertet.
Die Testsitzung wurde anschließend wiederhergestellt. Die Ergebnisdateien
blieben erhalten. Überlagernde Windows-Benachrichtigungen erschwerten die Tests.

Automatische Tests prüfen erfolgreichen/fehlgeschlagenen Worker, ungültige
Kandidaten, Bestätigungspflicht, Abbruch und Timeout mit Prozess-Doubles.
Die zusätzlichen leeren Text-DAT-Fälle sind nun auch im Kamera-/Capture-Bridge
abgesichert, einschließlich des Schreibens der ersten View in ein leeres Feld.

Abschließender gezielter Regressionslauf: **331 Tests bestanden** (einschließlich
geerbter Testfälle). Neue TOE nach Storage-/Pickle-Vorprüfung erfolgreich gespeichert:
`Backup/Implementation/PixelblazeMapper_20260908_OFFLINE_3D_JOB.1.toe`.
Wiederöffnen dieser neuen Datei wurde noch nicht getestet.

Noch offen: vollständiger Prepare→Start→Result-Klickablauf ohne Testschnittstelle,
echter UI-Abbruch während längerer Berechnung, grafische räumliche Ausrichtung,
Qualitätsfreigabe und Ergebnisübernahme; erneuter echter Kamera-/LED-Scan.
