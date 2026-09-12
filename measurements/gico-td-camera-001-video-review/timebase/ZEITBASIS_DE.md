# Zeitbasis der zweiten GICO-Aufnahme

Quelle `E:/LED2.mov`, Offlineanalyse am 2026-09-13. Die Auswertung lokalisiert sichtbare Schwarzgrenzen und unbeschriftete Lichtwechsel. Sie liest keine Gray-/CRC-IDs und setzt keine erwarteten Bildnummern ein. Hardware und TouchDesigner wurden nicht angesprochen.

## Schwarzgrenzen

| Grenze | Letzter Frame davor | Erster Frame danach | Wiedergabe-PTS danach |
|---|---:|---:|---:|
| Beginn Pause nach 15-FPS-Inhalt | 18329 | 18330 | 611,0000 s |
| Ende dieser Pause | 18816 | 18817 | 627,2333 s |
| Beginn Pause nach 25-FPS-Inhalt | 33930 | 33931 | 1131,0333 s |
| Ende dieser Pause | 34409 | 34410 | 1147,0000 s |
| Beginn letzte Pause | 44160 | 44161 | 1472,0333 s |
| Großflächiges Cyan nach dem Test | 44303 | 44304 | 1476,8000 s |

Frames sind nullbasiert. Detektor: im Panelbereich `y=400:1140` jedes dritte Pixel, `B-R > 50`, beleuchtet bei mehr als 100 solchen Pixeln. Nachbarn der Übergänge sind gespeichert. Teilbelichtete Übergangsframes und diese Schwelle bedeuten mindestens eine Videoframe Unsicherheit (33,33 ms Wiedergabe; bei achtfacher Verlangsamung 4,17 ms real). Beginn der ersten Pause ist bei 611,0000 s noch schwach teilbelichtet, bei 611,0333 s vollständig dunkel. Die letzte Cyan-Grenze ist kein Testplananker und darf nicht zum Kalibrieren einer zweisekündigen Pause verwendet werden.

## Mittlerer Bereich: achtfach verlangsamt

Die beiden Schwarzanfänge liegen 520,0333 Wiedergabesekunden auseinander, der Testplan sieht 65 reale Sekunden vor. Das Verhältnis ist 8,000513. Die beiden Wiederanläufe liegen 519,7667 Wiedergabesekunden auseinander. Unterschiedliche Frame-, Sender- und Belichtungslagen erklären kleine Abweichungen; diese Zeiten sind keine Netzwerk-Latenzmessung.

Mit den tatsächlich protokollierten ersten nativen TD-Batches der vier Phasen (`88,0072656`, `90,0207994`, `153,0022784`, `155,0045735` s) ergibt ein linearer Ausgleich:

`video_pts = 7,99978468 × test_elapsed − 92,97700447`.

Größtes Residuum: 0,06333 s Wiedergabe. Bei festem Faktor 8 liegen die vier Offsetwerte zwischen −93,05812 und −92,93306 s; ihr Mittel ist −93,00317 s. Als verständliche Arbeitsachse eignet sich im konstant verlangsamten Bereich `test_elapsed ≈ (video_pts + 93) / 8`. Eine allen Ankern gemeinsame Ausgangs-/Belichtungsverzögerung bleibt unbekannt. Die Zahl 240 beschreibt dort nominal die Kamerasamples je realer Sekunde, nicht 240 unterschiedliche LED-Bilder.

Diese Zuordnung folgt aus Schwarzphasen, nicht aus angenommenen FPS oder geratenen Frame-IDs. Sie ist durch diese Anker besonders gut zwischen 611 und 1147 s abgesichert; Lichtwechsel-Stichproben zeigen den gleichen langsamen Modus auch davor und anschließend bis kurz vor 1446 s. Die gesamte Datei darf nicht mit Faktor 8 umgerechnet werden.

## Endbereich: Export beschleunigt die Bilder wieder

In den Einsekundenfenstern 1438–1445 s gibt es typischerweise 2–6 große Änderungen der blauen Pixelmaske (`XOR > 1000`) je Wiedergabesekunde. Bei 1450–1453 s sind es 23–29. Diese Zählung ist nur ein Indikator für den Exportwechsel: ein LED-Bild kann wegen Teilbelichtung mehrere Maskenänderungen erzeugen; umgekehrt kann eine kleine Änderung unter der Schwelle liegen. Daraus wird keine optische Ergebnis-FPS berechnet.

Die dichte Probe findet noch langsam gehaltene Muster bei 1446,0000–1446,2333 s, zusätzliche Wechsel bei 1446,4000 und 1446,4667 s, und ab 1446,5667 s fast durchgehend neue Muster pro 30-Hz-Videoframe. Für Messungen den Bereich 1445,8–1446,8 s als Übergang ausschließen. Dies ist eine konservative Grenze, keine rekonstruierte Apple-Rampenkurve.

Die Hypothese einer anschließend normalen Wiedergabe ergibt aus dem letzten Schwarzanfang `video_pts ≈ test_elapsed + 1254,0294`. Ihr Schnittpunkt mit dem mittleren Achtfachmodell liegt bei etwa 1446,46 s und passt zur bildbasierten Übergangsstelle. Für eine endgültige 1×-Bestätigung müssen unabhängig decodierte IDs bzw. weitere sichere Zeitanker im Endabschnitt geprüft werden. Ein exakter Export-Verlust an Kameraframes kann aus diesen Schwarz- und Maskendaten allein nicht bewiesen werden. Bei bestätigtem 1×-Export sind dort nur 30 dargestellte Samples pro realer Sekunde vorhanden; Zwischenbilder der 240-FPS-Aufnahme fehlen dann im Export bzw. sind nicht mehr einzeln zugänglich.

## Empfohlene Auswertungsfenster

Für die erste belastbare Auswertung auf der Achtfachachse, jeweils mit Abstand zu Phasenwechseln:

| Testinhalt | Wiedergabefenster | Reale Dauer nach Achtfachmodell |
|---|---:|---:|
| 15 FPS | 133–609 s | 59,5 s |
| 25 FPS | 653–1129 s | 59,5 s |
| 30 FPS | 1173–1444 s | 33,875 s |

Das letzte Fenster belegt nur den konstant verlangsamten Teil der 30-FPS-Phase. Für eine volle 60-s-Auswertung muss der exportierte Endteil separat behandelt werden; aus einem normal abgespielten 30-FPS-Endteil folgt keine lückenlose 240-FPS-Prüfung. Die Anfangskalibrierung wird unabhängig anhand der einzeln leuchtenden Marker zeitlich zugeordnet; der negative mittlere Offset darf dafür nicht blind rückwärts extrapoliert werden.

## Reproduktion

- `inspect_timebase.py`: framegenaue Schwarzgrenzen durch binäres Suchen und Nachbarprüfung; tatsächliche TD-Phasenwechsel. Vorhandene `black-transitions.json` wird wiederverwendet.
- `probe_changes.py`: 17 dreisekündige Stichproben unbeschrifteter Maskenänderungen.
- `probe_tail.py`: alle 481 Frames von 1438 bis 1454 s für die Endbereichsprüfung.

Decoder-Threadzahl in den Skripten auf zwei begrenzt. Die erste Sparse-Probe lief noch mit dem Standarddecoder, das gespeicherte Skript verwendet für Wiederholungen ebenfalls zwei Threads. Keine Quelle verändert oder kopiert.
