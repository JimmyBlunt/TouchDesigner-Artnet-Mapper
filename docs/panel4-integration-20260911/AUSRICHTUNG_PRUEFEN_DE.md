# Panel 4: Auswertung abgeschlossen, Ausrichtung ausstehend

Der Benutzer hat bestätigt, dass Panel 4 gemeint ist, und die weiteren Schritte
an den Assistenten übergeben. Die endgültige Ausrichtung soll der Benutzer
anhand der Ansicht vorgeben. Panel 5 wird vom Benutzer vorbereitet; dessen
Position, LED-Anzahl und Anschluss sind noch nicht festgelegt.

## Ergebnis

Verwendet wurden ausschließlich die drei Ansichten aus
`Scans/back_panel4_810_249_20260911_repaired`, aufgenommen nach der korrigierten
Masseverkabelung. Die alte Aufnahme mit zusätzlichem Aufblitzen wurde nicht
verwendet. Die drei neuen Ansichten zeigen zusammen alle 810 LEDs, davon 809
in mindestens zwei Ansichten und 767 in allen drei Ansichten.

Die separate Offline-Rekonstruktion lief erfolgreich durch und lieferte 809
3D-Punkte. Der lokale Index 45 (gezählt LED 46) wurde nur einmal beobachtet und
hat keine 3D-Position. Er bleibt als fehlend markiert; keine Position wurde
erfunden und keine nachfolgende LED umnummeriert. Die Punktwolke ist nahezu
planar (Verhältnis der kleinsten zur mittleren SVD-Ausdehnung ca. 0,0093).
Die gespeicherte `error`-Spalte reicht von 0,000798 bis 2,812201; diese Rohwerte
sind kein Nachweis einer metrischen Genauigkeit.

## Layout-Entwurf

- Objekt `Panel 4 | unter Panel 2 | 30 x 30 cm`, ID
  `b5c6ab95-b0c7-462d-89e6-e20ca2f7d511`.
- 809 gemessene Bindungen; 810 reservierte Source-Slots 5362–6171.
- Fehlender lokaler Index 45 entspricht Source-Slot 5407.
- Vorläufige Platzierung unter Panel 2, Mittelpunkt (0,7; 1; 0,4).
- Gleichmäßige Skalierung auf denselben normalisierten 30-cm-Referenzrahmen
  wie die anderen Panels. Keine unabhängige metrische Registrierung.
- Drehung anhand der Kameraansicht vorgewählt, noch nicht vom Benutzer bestätigt.
- Genau die 256 alten Platzhalterbindungen 1696–1951 wurden aus dem Entwurf
  entfernt. Ihre archivierten Scandaten bleiben erhalten.
- Alle vorherigen gemessenen Punkte, IDs und Routen bleiben unverändert.
- Der Entwurf ist reversibel über Layout Undo und gespeicherte Dokumente.

Panel 4 wurde ausgewählt und die Layoutkamera frontal auf das Panel gerichtet.
`panel4-front-review.png` zeigt diese tatsächliche TouchDesigner-Vorschau.
`layout-review.png` zeigt den vorherigen Überblick. Es wurde **noch keine aktive
Map-/Routingübernahme** vorgenommen; diese folgt nach der Ausrichtung.
Die aktive Ausgabe ist aus. Der native Hashvergleich bestätigt unveränderte
aktive Daten; keine Operatorfehler.

## Behobener Statusfehler

Bei der Zustandsaufnahme zeigte die neue Panel-4-Sitzung noch den abgeschlossenen
Offline-Job von Panel 3. Ursache: Der globale abgeschlossene Job blieb vorhanden
und sein Poller schrieb den alten Status nach einem Sitzungswechsel erneut in
die Oberfläche. `scan_offline_job.poll` veröffentlicht Ergebnisse jetzt nur,
wenn die Job-Sitzungs-ID mit der aktuellen Sitzung übereinstimmt. Der laufende
Prozess wird weiterhin gepollt, damit dessen Abschlussbereinigung erfolgt.
Der Fix wurde in der laufenden Anwendung geladen.

45 Tests für Offline-Jobs, die Sitzungszuordnung und partielle Scanübernahme
bestanden. Zusätzlich prüfte die Vorbereitung die realen Scan-Datei-Hashes,
Beobachtungsanzahlen, freie Source-Slots, Punkt-/ID-Erhaltung und die exakte
Platzhalterauswahl. Die native Übernahme prüfte unveränderte aktive Daten.

## Nachvollziehbarkeit und nächster Schritt

`scan-state-before.json` und `reconstruction-and-draft.json` sichern die
Ausgangslage; `offline-start.json` referenziert den Job. `draft-prepared.json`
und `draft-plan.json` enthalten den neuen Entwurf und seine Transformation.
`native-draft-result.json` protokolliert die Anwendung. Der Projektcheckpoint
und seine SHA-256-Prüfsumme stehen in `save.json`.

Nach der Benutzerangabe zur Drehung/Spiegelung: Transformation anpassen,
anschließend aktive Map/UV/Kapazität und den vorhandenen Controllerrahmen auf
U120–137 erweitern. Panel 4 verwendet dabei U133–137, Offset 2210 relativ zu
U120; der physische Controller-Pixeloffset 1821 ist keine Art-Net-Zieladresse.
Der fehlende Slot und die entfernten Platzhalter müssen in der aktiven
Schwarzmaske bleiben. Vorherige Panel-Ausgaben müssen bytegleich erhalten bleiben.
