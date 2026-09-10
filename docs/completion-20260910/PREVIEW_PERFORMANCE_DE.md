# LED-Preview: RGB-Normalisierung als Array-Operation

Die isolierte Optimierung in `pixelblaze_mapper/preview_color_bulk.py` ersetzt ausschließlich die drei Zeilen für Maximalwert, Skalierung und Begrenzung der eingehenden RGB-Werte. Die bestehende Quelle steht in `performance-callbacks-before.json` unter `preview`; ihr SHA-256 ist `bb890e8140ee00735d78b16c080eaa46b777bc11910e660d4a1e35626688accf`.

`source_for_bulk()` prüft den erwarteten Quellenhash und den exakten bisherigen Normalisierungsblock, ersetzt nur diesen Block und kompiliert die resultierende Python-Quelle. Abweichende Quellen werden abgewiesen. `ensure_bulk_source()` erkennt die bereits optimierte Fassung über eine Rücktransformation und denselben Originalhash. Der vorhandene `build_led_preview_contract.build()` verwendet diesen Helfer, damit eine spätere explizite Neuinstallation die Optimierung beibehält.

Die Berechnung liest `r`, `g` und `b` in dieser Reihenfolge jeweils einmal. NumPy berechnet in einem eigenen Float64-Array den globalen Maximalwert und führt Skalierung und Begrenzung aus. Die Grenzen bleiben exakt: bis einschließlich `1.0001` Faktor 1, darüber bis einschließlich `255.0001` Faktor `1/255`, darüber `1/65025`. Anschließend bleibt jeder Wert in `0..1`. Nicht verwendete Samples hinter `n` beeinflussen den Maximalwert nicht.

Die zurückgegebene Struktur bleibt eine Liste von drei Listen. Deshalb bleiben Channel-Zuweisung und anschließende Schwarzmaskierung kompatibel. Eingangslisten und Eingangsarrays werden nicht verändert. Für NaN/Unendlich verwendet der Helfer die bisherige skalare Vergleichsfolge, weil Python `max` mit NaN positionsabhängig reagiert; der schnelle Weg verändert diese seltenen Fälle nicht stillschweigend.

Unverändert bleiben Koordinaten, kanonische LED-Anzahl, Reihenfolge `tx,ty,tz,r,g,b`, vorhandene Missing-Maske, Statusdaten sowie die animierte HSV-Ersatzdarstellung. Effekt-/Simulationscode und `script4` werden nicht bearbeitet.

## Nachweise

`tests/test_preview_color_bulk.py` vergleicht skalare und neue Ergebnisse für normalisierte, 255er- und 65025er-Eingaben, direkt an und neben den beiden Schwellen, für negative Werte, nicht verwendete Endsamples und nichtfinite Werte. Weitere Prüfungen sichern Kanalnamen/-reihenfolge, einmaliges Lesen, keine Eingabemutation und das Ablehnen abweichender Callbackquellen. Der tatsächliche Originalcallback und die transformierte Quelle werden mit isolierten TD-Stubs ausgeführt und hinsichtlich aller sechs Ausgabekanäle, Missing-Maske und Statuszeilen verglichen. Zusammen mit bestehenden Preview-/Installationsprüfungen bestanden 24 Tests.

Der ausdrücklich **außerhalb TouchDesigners** gemessene Python-Mikrobenchmark mit 3.744 RGB-Pixeln, dreimal je 100 Aufrufen, benötigte im Median etwa 4,217 ms für den skalaren Abschnitt und 0,933 ms für den neuen Helfer. Das entspricht in diesem isolierten Test etwa Faktor 4,52. Rohdaten: `preview-color-bulk-benchmark.json`. Daraus wird keine identische FPS- oder Gesamtprojektbeschleunigung abgeleitet. Native Installation und anschließende Profilierung werden separat vom Hauptagenten dokumentiert; dieser Arbeitsschritt hat den laufenden Callback nicht verändert.
