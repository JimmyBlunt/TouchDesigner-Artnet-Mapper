# MariMapper – echter nativer Offline-Smoke-Test

Datum: 2026-09-07. Ergebnis: **Native Abhängigkeiten und echte SfM-Rekonstruktion erfolgreich**, aber **keine geometrische Freigabe, Kameraaufnahme oder Layout-Übernahme**.

## Geprüfte vorhandene Umgebung

Interpreter: `C:\Users\jbhtz\AppData\Roaming\uv\tools\marimapper\Scripts\python.exe`.

Die nativen Imports von NumPy 2.5.1, OpenCV 5.0.0.93, Open3D 0.19.0 und pycolmap 3.11.1 waren erfolgreich. MariMapper 3.4.2 ist laut installiertem `direct_url.json` exakt Commit `7dc5f799a1b7c180573c2632f6d12a3be0cbf4fa`. Zusätzlich wurden `LED2D`, `Point2D`, `sfm` und der 3D-CSV-Writer erfolgreich importiert. Keine Pakete installiert oder aktualisiert; keine Kamera-/Backend-Klasse instanziiert.

## Reale Eingaben und expliziter Umfang

Nur vorhandene Dateien aus `C:\Users\jbhtz\OneDrive\Desktop\Pictures\Documents\~Projects~\Marrimapper-LED-Schrank\oben_neu` wurden gelesen:

- `led_map_2d_20260827-220052.csv`
- `led_map_2d_20260827-220245.csv`
- `led_map_2d_20260827-220541.csv`

Jeweils 269 Beobachtungen, zusammen 807 Beobachtungen für 269 IDs (517–785). Die Manifest-Sitzung heißt ausdrücklich `offline-evidence-not-live-scene`: bestehende importierte Ansichten, keine gestartete Aufnahme und kein Nachweis einer aktuellen TD-Szenenzuordnung. Alle IDs wurden explizit übernommen, keine Ansicht gefiltert oder umnummeriert. Der Standard-Dry-Run des vorhandenen Workers bestätigte 807 Beobachtungen und deaktivierte Kamera-/Hardware-/Layout-Fähigkeiten.

## Gefundener und behobener Workerfehler

Der erste echte Aufruf rekonstruierte Punkte und schrieb `native-sfm-smoke-oben-neu/candidate_3d.csv`, endete aber nach 1,640 s mit Exit 1: `numpy.int64`-LED-IDs konnten nicht in `quality_pending.json` serialisiert werden. Dieser erste Ergebnisordner bleibt als **unvollständiger Fehlversuch** erhalten und wurde nicht überschrieben.

Begrenzte Korrektur in `pixelblaze_mapper/scan_worker.py`: IDs im Bericht explizit in Python-`int` umwandeln. Keine Rekonstruktionsparameter, Datenwerte, ID-Zuordnungen oder Gates geändert. Neuer Offline-Test `test_native_integer_ids_are_serializable_in_success_report` reproduzierte den Fehler zunächst und besteht nach der Korrektur; er modelliert einen nativen Integer ohne native Abhängigkeit im gewöhnlichen Test-Python. **29 Scan-Session-/Worker-Tests bestanden** (0,230 s).

## Erfolgreicher zweiter Lauf

Vorhandener Worker, separates neues Ziel und ein 120-s-Prozesslimit:

```
python.exe -B -m pixelblaze_mapper.scan_worker docs/implementation-2026-09-07/native-smoke-manifest-verified.json --confirm-offline-reconstruction
```

Interpreter wie oben; Arbeitsverzeichnis Repository. **Exit 0 in 1,469 s.** Das Limit wurde nicht erreicht. `native-smoke-manifest-verified.json` hält Eingangspfade, SHA-256, IDs und Ausgabeziel fest. Existierende Ergebnisse werden weiterhin ausdrücklich abgewiesen; für einen neuen Lauf ist ein weiterer neuer Ergebnis-Unterordner erforderlich.

Ergebnisse unter `native-sfm-smoke-oben-neu-verified/`:

- `candidate_3d.csv`: **258 von 269 IDs** rekonstruiert, keine außerhalb des erlaubten Bereichs.
- `quality_pending.json`: nativer Workerbericht, Review weiterhin erforderlich.
- `comparison.json`: zusätzlicher numerischer Diagnosevergleich mit vorhandener `led_map_3d.csv`.

Fehlende IDs bleiben fehlend: **619, 653, 705, 724, 751, 766, 767, 771, 772, 773, 777**. Keine Interpolation, Normalenschätzung, Skalennormalisierung, Registrierung oder Live-Anwendung. Alle drei Eingabedateien stimmen nach dem Lauf weiter mit ihren Manifest-SHA-256 überein.

## Vergleich – ausdrücklich kein Qualitätszertifikat

Vorhandene Referenz: 269 Punkte. Vergleich: alle 258 gemeinsamen IDs; orientierungserhaltender Least-Squares-Similarity-Fit mit freier Skalierung, Rotation und Translation, ausschließlich für diese Diagnose. Keine Transformation wurde in Candidate/Referenz oder Layout gespeichert.

| Kennzahl | Wert |
| --- | ---: |
| Fit-Skala Candidate → Referenz | 1,610441 |
| RMSE in Referenzeinheiten | 0,382978 |
| Median des Punktabstands | 0,271829 |
| Maximaler Punktabstand | 2,119745 |
| Referenz-Bounding-Box-Diagonale der gemeinsamen Punkte | 25,749661 |
| RMSE / diese Diagonale | 1,4873 % |

Dieser Fit verwendet sämtliche gemeinsamen Punkte und besitzt **keine unabhängigen Prüfpunkte**. Die Referenzdatei allein belegt weder Kalibrierung noch Provenienz eventuell früher ergänzter Punkte. Daher keine Aussage „geometrisch korrekt“ oder „zur Übernahme freigegeben“. Es bleiben elf fehlende Punkte und messbare Abweichungen; eine qualifizierte Registrierung, Reprojektions-/Ankerprüfung und explizite Nutzerabnahme fehlen.

## Sicherheits- und Aussagegrenzen

Keine Aufnahmesession, kein TouchDesigner-Zugriff, keine Kameranutzung, keine Sender-/Backend-Ausführung, keine Paketinstallation und keine Änderung der Originalmessung. MariMapper verwendet intern einen temporären SfM-Arbeitsordner; bleibende neue Resultate und Manifeste liegen nur im dokumentierten Audit-Ergebnisbereich. Der Worker ist keine OS-Sandbox. Erfolg gilt für diese vorhandene native Umgebung und diesen Datensatz, nicht für beliebige Kameras, Live-Scan-Automation, Mehrcontroller-Capture oder eine geprüfte Layout-Registrierung.
