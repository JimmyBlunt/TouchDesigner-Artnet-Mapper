# Panel 5: angefragte Belegung

Benutzerangabe: unter Panel 3 (dritte Reihe links), 362 LEDs, gleicher
Controller 10.0.0.249, Startuniversum 139.

Bei 170 RGB-Pixeln pro verwendetem 510-Kanal-Universum ergibt das U139 mit
170 LEDs, U140 mit 170 LEDs und U141 mit 22 LEDs. Keine Überschneidung mit
Panel 4 (U133–137); U138 bleibt frei. Die Lücke ist keine notwendige Reserve,
kann aber bestehen bleiben. Der zusammenhängende Scan-Sendebereich wäre
U120–141 (22 Universen einschließlich der Lücke).

Der Controller meldet Ausgang 5 (ID 4, GPIO19) bereits aktiviert ab U139,
aber mit **352 statt der angegebenen 362 LEDs**. Dieser Unterschied muss vor
dem Scan korrigiert werden. Kein Scan und keine Controlleränderung gestartet.
Ausgänge 1–4 entsprechen weiterhin den abgeschlossenen Panels. Die API meldet
21 belegte Universen; dies ist wegen U138 nicht gleich dem zusammenhängenden
Sendebereich von 22 Universen. Beim neuen Scanplan die Lücke schwarz halten
und den Empfang vollständiger Rahmen prüfen.

`controller-before.json` hält den Readback fest, `pending-panel5.json` die
gewünschte Konfiguration und den noch offenen Zählunterschied. Panel 4 bleibt
im abgeschlossenen Projektzustand bestehen.

## Korrektur durch den Benutzer

Die korrekte Anzahl ist **352 LEDs**; die zuvor genannten 362 waren ein
Tippfehler. Die vorhandene Controllerkonfiguration ist damit bestätigt:
Ausgang 5, U139–141, verteilt auf 170 + 170 + 12 LEDs. U138 bleibt frei.
Keine Änderung am Controller erforderlich. Die Scanvorbereitung ist noch
nicht ausgeführt; Panel 4 bleibt im abgeschlossenen Zustand.
