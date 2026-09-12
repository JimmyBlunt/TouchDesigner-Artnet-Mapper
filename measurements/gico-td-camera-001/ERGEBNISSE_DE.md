# TD → GICO: Kameralauf 001

Der beaufsichtigte Lauf ist vollständig abgeschlossen (220,012 s). Der Benutzer
hat den Kamerastart mit „lauft“ bestätigt; nach Abschluss wurde er zum Stoppen
der Aufnahme aufgefordert. Aufnahme laut Vorbereitung: iPhone 13, Slo-Mo
240 FPS, unteres Panel. Originaldatei, tatsächliche Bildrate und Zeitlupenzeitbasis
sind noch zu prüfen. Es liegt noch kein optisches Ergebnis dieses Laufs vor.

## Messpfad und Sendergebnis

Temporäre optische Testquelle in TouchDesigner → vorhandener Router/Packer →
externer UDP-Worker → GICO 10.0.0.244, Universen 0–23. Der Transport bleibt
auf 30 FPS eingestellt; der kodierte Inhalt wechselt in drei jeweils etwa
60 Sekunden langen Abschnitten mit nominal 15, 25 und 30 FPS. Die Testquelle
ersetzt den Effektinhalt und misst daher keine beliebigen GPU-/Effektkosten.

- 25 native Mustervergleiche vor dem Start bestanden.
- 9.681 eingereichte Batches, 6.541 gesendete Batches / 156.984 Datenpakete.
- 3.139 ältere Batches im Latest-Frame-Worker verworfen; dies sind keine
  nachgewiesenen Netzwerkverluste. Eingereichte Batches können dieselbe
  optische ID enthalten. Ein verbleibender Batch wurde beim Stop nicht gesendet.
- Keine gemeldeten Sendefehler oder abgelehnten Einreichungen.
- Worker-Mittelwert 29,773 gesendete Batches/s über 219,661 aktive Sekunden.
  Das ist keine Messung der tatsächlich angezeigten neuen LED-Bilder.
- Abschließend 48 Schwarzpakete; Worker regulär beendet, keine Cleanupfehler.

Die zeitbasierten IDs und Einreichungszeitpunkte stehen in
`submitted-frames.jsonl`; Phasen, Ausgangskonfiguration und Workerwerte in
`run.json`. Die optische Auswertung muss wiederholte und übersprungene IDs
berücksichtigen und die Zeitbasis aus der neuen Originalaufnahme bestimmen.
Offset und Bildkalibrierung der vorherigen Aufnahme sind nicht übertragbar.

## Wiederherstellung

Laufprüfung bestätigt Ausgabe aus sowie Controller, Quelle, Segmentdaten und
Senderquelltext wiederhergestellt. Eine zusätzliche Live-Prüfung nach dem Lauf
bestätigt: keine aktive Testsitzung, keine temporären Testoperatoren, Quelle
`/project1/math1`, keine Fehler im Ausgabe-Component. Es wurde keine TOE-Datei
für diesen temporären Test gespeichert.

Nächster Schritt: Original-MOV übernehmen, Metadaten und Slo-Mo-Zeitbasis
prüfen, neu kalibrieren und optische Bildwechsel samt Aussetzern auswerten.
