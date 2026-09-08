# Guided Scan – Prüfung mit vorhandenen MariMapper-Daten

Stand: 8. September 2026. Ergebnis: Die geprüfte Datenübernahme erhält IDs und
Koordinaten. Die Rekonstruktion kann unvollständige Ergebnisse liefern; ein
vollautomatischer, qualitativ geprüfter Scan-bis-Live-Layout-Ablauf ist damit
ausdrücklich **nicht** nachgewiesen.

## Umfang und Schutz

Quelle: `C:\Users\jbhtz\OneDrive\Desktop\Pictures\Documents\~Projects~\Marrimapper-LED-Schrank`.
104 Dateien: 81 zweidimensionale Aufnahme-CSV, 23 3D-/Pixelblaze-Importdateien.
14 Aufnahmegruppen, insgesamt 38.444 Beobachtungen. Alle Quelldateien wurden
vor und nach dem ersten Audit per SHA-256 verglichen: unverändert.
Keine Kamera geöffnet, keine Art-Net-Ausgabe gestartet, keine Live-Szene ersetzt.
Ergebnisse liegen ausschließlich im Projektunterordner `scan-realdata-20260908`.

## Bestandene Prüfungen

- Sämtliche 23 Importdateien: Import, Szene-JSON-Roundtrip, Teilersatz der ersten
  bis zu sieben vorhandenen Messpunkte, stabile LED-/Objektzuordnung, Undo/Redo.
- Für CSV wird jede originale ID mit ihrem originalen XYZ-Tupel verglichen:
  keine Achsenvertauschung, Spiegelung, Skalierung oder Umnummerierung beim Import.
- Jede der 38.444 UV-Beobachtungen wurde nach Manifestprüfung exakt mit
  Quelldatei, Ansichtsindex und ursprünglicher LED-ID abgeglichen.
- Lücken und führende ID-Offsets bleiben explizit markiert. Der abschließende
  Pixelblaze-Export verweigert lückenhafte globale Adressen, statt sie zu verdichten.
- Zusammenhängende vollständige Arrays werden koordinatengenau exportiert.
- 202 vorhandene Regressionstests bestanden: Scan-Lebenszyklus, Scope,
  Manifest/Hash-Manipulation, doppelte/ungültige IDs, nichtendliche Werte,
  Bestätigungs-/Qualitätssperren, Capture-/Routing-Verträge, Layout/Teilersatz.
- Vier neu rekonstruierte Kandidaten wurden zusätzlich **im laufenden
  TouchDesigner-Python** in isolierte Szenen importiert und verlustfrei
  serialisiert. Controller-/Segmenttabellen unverändert, Sender weiterhin aus.

Der Audit zählt 49.750 Einzelvergleiche/Prüfschritte. Das sind überwiegend
Koordinaten-/Beobachtungsvergleiche, **nicht** ebenso viele unabhängige Tests.

## Echte Offline-Rekonstruktion

Nicht gemockt: installierter MariMapper 3.4.2 / geprüfter Commit, pycolmap 3.11.1,
Kameramodell `camera_model_opencv`, keine Interpolation. Bestehende UV-Aufnahmen
wurden durch denselben Offline-Worker verarbeitet, den Guided Scan vorbereitet.

| Gruppe | In Aufnahmen beobachtete IDs | Rekonstruierte IDs | Nicht rekonstruiert |
|---|---:|---:|---:|
| hinten/1 | 203 | 196 | 7 |
| mitte_neu | 513 | 506 | 7 |
| oben_neu | 269 | 251 | 18 |
| unten_neu | 382 | 368 | 14 |

Alle ausgegebenen Kandidaten-IDs sind Teil des angeforderten Bereichs. Alle
ausgegebenen XYZ-Werte werden beim anschließenden Import exakt erhalten.
Fehlende Punkte entstehen hier vor dem Import in der Rekonstruktion. Eine
Abweichung gegenüber alten Ergebnissen belegt allein keinen Importfehler:
Kameramodell, Rekonstruktionsentscheidung und damalige Interpolation sind nicht
als identischer historischer Lauf dokumentiert. SfM-Ergebnisse besitzen zudem
einen freien Maßstab und eine freie räumliche Ausrichtung.

## Konkrete Datenauffälligkeiten

- `oben_neu/led_map_3d.csv`: 269 vorhandene Punkte mit IDs 517–785.
  Der indexbasierte Import hat 786 Slots, davon sind die ersten 517 nur
  fehlende Vorgänger-IDs, **keine zusätzlich gescannten LEDs**. Beim Anhängen
  sind vorhandene Scan-Indizes ausdrücklich auszuwählen.
- `mitte_neu/led_map_3d.csv`: 509 Messpunkte im Bereich 0–516, acht Lücken.
  Das ist nicht automatisch ein vollständiges Abbild der später diskutierten
  524 Hardware-LEDs. Die erwartete Anzahl muss separat vorgegeben werden.
- `unten_neu/led_map_3d.csv`: 367 vorhandene Messpunkte; die Aufnahmen reichen
  bis ID 1185 und passen daher nicht ungeprüft zu einer alten 0–1183-Zuordnung.
- `hinten/1/led_map_3d.csv`: 200 Messpunkte bei IDs 0–202, Lücken 72–74.
  Dieses historische Beispiel ist **nicht** der neue vollständige 256-LED-Test.
- `complete_new.txt` enthält 1183 Koordinatentupel. Eine reine Array-Datei
  enthält keine separaten physischen IDs und keine zuverlässige Fehlpunktmarkierung.

## Offene Funktions-/Bedienungspunkte

1. Nach jedem Scan Soll-Anzahl, beobachtete IDs, rekonstruierte IDs und fehlende
   IDs getrennt zeigen. Führende Index-Offsets nicht als echte LED-Anzahl anzeigen.
2. Vor Übernahme räumliche Registrierung/Ausrichtung und Qualität prüfen.
   Koordinatentreuer Import allein beweist nicht, dass die Punkte räumlich
   schon korrekt zum bestehenden Schrank passen.
3. Die vorhandenen Methoden `stage_registered_candidate` und `request_handoff`
   sind Übergabeschnittstellen. Die separate Erfassung verweist weiterhin auf
   expliziten Import/Zuordnung im Layout; sie übernimmt nicht automatisch ins Live-Layout.
4. Interpolation ist im aktuellen Offline-Worker bewusst deaktiviert. Die vom
   Benutzer genannten MariMapper-Interpolationsoptionen sind dort noch nicht umgesetzt.
5. Der echte Kamera-/LED-Scan, visuelle Klicktests des gesamten Übergabeablaufs
   sowie eine geometrische Qualitätsabnahme gegen vermessene Referenzen bleiben offen.

## Reproduzierbarkeit

`tools/audit_scan_realdata_20260908.py --source <Quellordner> --output <neuer Ergebnisordner>`
erstellt Dateiinventar, Prüfergebnis und 14 Manifeste ohne native Hardwarezugriffe.
`tools/audit_scan_native_20260908.py <Ergebnisordner>` rekonstruiert vier Gruppen
mit getrenntem MariMapper-Python und 120 Sekunden Timeout je Prozess.
Vorhandene Resultatordner werden nicht überschrieben; für einen vollständig neuen
Lauf einen neuen Ergebnisordner verwenden.

Belege: `scan-realdata-20260908/report.json`, `native-report.json`,
die 14 Manifeste und vier `native-*/candidate_3d.csv` / `quality_pending.json`.
Produktionscode wurde in diesem Analyseauftrag nicht geändert.
