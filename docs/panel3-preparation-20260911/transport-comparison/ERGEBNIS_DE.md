# Panel 3: Netzwerkabstand und Scanvergleich, 11.09.2026

Der kontrollierte Vergleich verbessert die Erkennung und die Geschwindigkeit deutlich. Für den nächsten Vollscan ist **PACKET GAP = 1 ms** eingestellt. Ein kompletter Scan aller 880 LEDs mit dieser Einstellung steht noch aus.

| Test | Angeforderter Paketabstand | Erkannt | Mittlere Zeit je LED | LEDs/s |
| --- | ---: | ---: | ---: | ---: |
| A | 0 ms | 18/20 | 866,4 ms | 1,15 |
| B | 1 ms | 20/20 | 327,3 ms | 3,06 |
| B2, Wiederholung | 1 ms | 20/20 | 338,25 ms | 2,96 |

Die Geschwindigkeit ist 1000 geteilt durch die mittlere abgeschlossene LED-Zykluszeit. Kameraanlauf und abschließendes Aufräumen sind darin nicht enthalten. Die Kamera wurde vor diesem Vergleich gegenüber dem vorherigen Vollscan bewegt und blieb während A, B und B2 an derselben Position. Helligkeit 9,2 %, Kamera 0, Belichtung −10 und Schwellwert 160 blieben gleich. Getestet wurden die lokalen IDs 1–15, 17–19, 21 und 22.

## Ursache und Änderung

Der Controller 10.0.0.249 erhält pro Ausgabe 13 Universen (120–132). Ohne Abstand kamen im Messfenster 4045 von 5356 lokal erfolgreich gesendeten Paketen am Controllerzähler an, etwa 75,5 %. Mit 1 ms Abstand waren es bei B 2041 von 2067, etwa 98,7 %. Gleichzeitig stieg die Zahl vollständiger Sammlungen von 80 bei A auf 152 bei B; unvollständige Sammlungen sanken von 331 auf 7. Die Messfenster schließen Kameraanlauf und Abschluss ein und sind unterschiedlich lang.

Das ist starke Evidenz für Empfangsprobleme bei unmittelbar aufeinanderfolgenden Paketen. Die genaue Verluststelle innerhalb Netzwerk/Controller ist damit nicht bewiesen. Lokaler Sendeerfolg allein bestätigt keinen Empfang. Die mittlere Zeit in Kamera-Leseaufrufen sank von 729,6 auf 192,95 ms pro LED. Damit erklärt sich auch, warum die bisherige Phasenanzeige viel Kamerazeit auswies, obwohl der Transport die Erkennung beeinflusste.

Der Worker wartet jetzt optional zwischen den Paketen eines Universenpaketsatzes. Es gibt keine zusätzliche Wartezeit vor dem ersten oder nach dem letzten Paket. Die bestehende Begrenzung auf höchstens 20 Paketsätze pro Sekunde bleibt bestehen. Windows kann einen angeforderten Abstand von 1 ms etwas verlängern; der Wert ist keine Präzisionsgarantie. Abbruch/Heartbeat werden vor dem nächsten beleuchteten Paket erneut geprüft. Der abschließende Not-Blackout verwendet keinen zusätzlichen Paketabstand.

Die Einstellung wird im Scanplan gespeichert, beim Erzeugen des konkreten Scanverzeichnisses übernommen und zusammen mit Sendezählern im Ergebnis protokolliert. Zulässig sind 0–2 ms. Bestehende Pläne ohne das optionale Feld behalten 0 ms. Änderungen an diesem Feld machen einen vorher geprüften Plan ungültig.

## Bedienung und wiederhergestellter Zustand

1. In **SETTINGS → PACKET GAP (ms, 0-2)** steht für diesen Aufbau **1**.
2. Nach einer Änderung **CHECK SCAN PLAN** drücken. Die Zusammenfassung zeigt den Paketabstand an.
3. **CAPTURE VIEWS → START SCAN / NEXT VIEW** startet die nächste Aufnahme. Die Kamera während der Aufnahme stehen lassen.

Der vorbereitete Vollscan umfasst wieder **0–879**, Panel 3 auf **U127–U132**. Gesendet werden **U120–U132**, wobei die anderen Panelbereiche schwarz bleiben. Die drei bisherigen vollständigen Ansichten sind erhalten. Die drei kurzen Diagnoseaufnahmen liegen separat unter `Scans/panel3_transport_diagnostic_20260911` und wurden nicht zur produktiven Rekonstruktion hinzugefügt. Es wurde kein weiterer Vollscan automatisch gestartet.

## Prüfung und Nachweise

- Acht gezielte Tests prüfen Planvalidierung, Paketabstand, Sendezähler, Fehler und Abbruchverhalten; zusätzlich wurden die betroffenen Capture-Tests ausgeführt.
- 44 Tests für Paketabstand, Guided-Scan-Brücke und Workflow bestanden nach Ergänzung des Settings-Felds.
- Die native Installation prüft 880 IDs, unveränderte Ansichten/Arbeitsordner, gültige Plansignatur, keine Operatorfehler und ausgeschaltete Ausgabe. Ergebnis: `native-gap-ready.json`.
- A/B/B2-Rohmessungen stehen in den jeweiligen `*-start.json`, `*-observations.jsonl` und `*-result.json`. Zu jeder Diagnoseaufnahme bleiben Plan, Ergebnis und CSV erhalten.
- `native-original.json` und `native-restored.json` dokumentieren Sicherung und Rückkehr zum Vollscan.
- `save.json` enthält den tatsächlich gespeicherten TOE-Dateinamen und SHA-256. Der Checkpoint wurde gespeichert, nicht erneut geöffnet.

Die kurze Stichprobe belegt die Verbesserung unter diesen Bedingungen. Geschwindigkeit und Erkennungsquote über alle 880 LEDs werden erst im nächsten Vollscan bestätigt.

## Nachtrag: erster vollständiger Scan mit 1 ms

Aufnahme `capture-4837c418-23bc-4190-8aea-29d84cb6a854` ist vollständig abgeschlossen: **880 verarbeitet, 864 erkannt (98,18 %)**. Mittlere LED-Zykluszeit **334,073 ms**, entsprechend **2,99 LEDs/s**; das gesamte Transportmessfenster einschließlich Anlauf/Abschluss dauerte **300,328 s** (rund fünf Minuten). Keine lokalen Sendefehler, keine Fehler beim Kameraabschluss und keine Fehler am Guided-Scan-Operator. Damit bestätigt der Vollscan die Geschwindigkeit aus dem Kurztest. Die Erkennungsquoten verschiedener Kamerapositionen sind kein isolierter Vergleich der Transportänderung.

Die vier produktiven CSV-Ansichten enthalten zusammen alle **880 LEDs mindestens einmal**, **875 mindestens zweimal**, **855 mindestens dreimal**. Fünf LEDs sind erst einmal beobachtet. Diese Zählung belegt Beobachtungsabdeckung, noch keine erfolgreich rekonstruierte 3D-Position. Die vierte Ansicht ist im nativen Dialog zur vorhandenen Liste hinzugefügt. Als nächster Schritt können die Ansichten unter BUILD 3D / SAVED SCANS rekonstruiert und die räumlichen Lücken visuell geprüft werden.

## Nachtrag: fünfte Ansicht abgeschlossen

Aufnahme `capture-aca36f5f-4643-45fb-b372-b5a8502a0dc7`: **880 verarbeitet, 877 erkannt (99,66 %)**, mittlere LED-Zykluszeit **326,523 ms = 3,06 LEDs/s**. Das Transportmessfenster einschließlich Anlauf/Abschluss dauerte **295,703 s** (rund 4 Minuten 56 Sekunden). Paketabstand weiterhin 1 ms; keine gemeldeten Sende-, Kameraabschluss- oder Guided-Scan-Operatorfehler. Die Aufnahme ist als fünfte produktive Ansicht im Dialog eingetragen.

CSV-Abdeckung über die fünf eingetragenen Ansichten: **880 mindestens zweimal**, **875 mindestens dreimal**, **855 mindestens viermal**, **697 in allen fünf Ansichten**. Keine LED ist vollständig unbeobachtet oder nur einmal beobachtet. Das ist eine gute Grundlage für die folgende Rekonstruktion; geometrische Qualität und mögliche Ausreißer bleiben anschließend visuell zu prüfen. Die 3D-Berechnung wurde bei dieser Ergebnisprüfung nicht gestartet.

## Nachtrag: 3D-Berechnung durch den Benutzer abgeschlossen

Der Benutzer hat PREPARE 3D, START 3D und REVIEW RESULT ausgeführt. Ergebnis `result-c4187aae-1d17-49e7-a4d6-9745c471d466`: **880 rekonstruierte Positionen**, lokale IDs **0–879**, keine fehlenden beobachteten IDs. Laufzeit 5,3 Sekunden, Exitcode 0. Keine Interpolation; Koordinaten weiterhin in beliebigen SfM-Einheiten, Registrierung und Layout-Anwendung noch nicht erfolgt. Keine Operatorfehler im Guided Scan.

Der Review-Dialog schlägt den globalen Source-Offset **4482** vor. Damit erhalten die 880 Punkte die internen IDs **4482–5361**. Dieser Offset ist keine Universumsnummer; die spätere Hardware-Zuordnung bleibt ein eigener Schritt. Name derzeit `Raw scan`, Translation/Rotation jeweils 0 und Skalierung jeweils 1. Nächster manueller Schritt: verständlichen Namen vergeben, als neues Draft-Objekt hinzufügen und anschließend im Layout die Geometrie prüfen, auf 30 × 30 cm bringen und unter Panel 1 ausrichten. Der Benutzer übernimmt diese Bedienung selbst.
