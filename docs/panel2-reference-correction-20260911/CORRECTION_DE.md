# Ausrichtung anhand des Benutzer-Referenzbildes korrigiert

Der Benutzer korrigierte die bisherige Orientierung mit einem Screenshot und praezisierte: erneut drehen und spiegeln, wobei das kleine Quadrat oben rechts bleiben muss. Die bisherige Position des Quadrats allein war kein eindeutiger Orientierungsnachweis.

Verglichen wurden alle acht rechtwinkligen Dreh-/Spiegelvarianten der 680 Messpunkte mit den orangefarbenen Punkten des Screenshots. Die Achsenvertauschung in Frontkoordinaten (rechts, oben) war eindeutig die beste der acht Varianten. Der Vergleich nutzt normalisierte Punktabstaende und dient nur der Orientierung, nicht der metrischen Registrierung. 681 erkannte Bildkomponenten sind keine neue LED-Zaehhlung. Ergebnisse: `reference-analysis.json`.

Umgesetzt wurde relativ zum vorherigen Entwurf eine weitere Drehung um 90 Grad im Uhrzeigersinn, danach eine Oben-unten-Spiegelung. Dies vertauscht rechts/oben und laesst die obere rechte Ecke an gleicher Stelle. Sichtpruefung der erzeugten Vorschau: grosse Flaeche oben links, kleines Quadrat oben rechts, kleineres Feld unten links, langer Bereich rechts unten, passend zum Benutzerbild.

Die Transformation erfolgt um (0.9, 1.0, 0.4). Mittelpunkt, Tiefe und einheitlicher Massstab bleiben erhalten; 680 Bindungen, originale Rohmessungen und 58 Fehlmarkierungen sowie andere Objekte und Routen sind unveraendert. Punktweise Matrixpruefung, Undo/Redo und JSON-Roundtrip bestanden. Native Uebernahme als ein Layout-Commit, aktive Tabellen unveraendert, Sender aus, keine Operatorfehler.

Neuer gespeicherter Stand: `PixelblazeMapper_PANEL2_REFERENCE_MATCHED_20260911.1.toe`, Hash im Speicherbericht. Kein Neuladen in diesem Schritt. Die vorherigen Ausrichtungsstaende bleiben als nachvollziehbare Zwischenstaende erhalten. Noch keine aktive Controller-/Mapping-Uebernahme oder verifizierte physische Registrierung.
