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
