# P1 Core 71 – Live-Abnahme

Stand: 26. August 2026

## Umfang

Die P1-Abnahme umfasst den zustandsbehafteten Material-Browser, lokale Panel-UVs,
Show-Control mit A/B-Renderer, MadMapper-/LED-Vorschau sowie die zugehörigen
P0-Ausgabeverträge. Die Hardware-Ausgabe blieb während der Software-Abnahme aus.

## Automatisierte Prüfung

- 277 von 277 Python-Regressionstests bestanden.
- Alle geänderten Python-Quellen und eingebetteten TouchDesigner-Skripte sind
  syntaktisch gültig.
- `git diff --check` meldet keine inhaltlichen Diff-Fehler.
- Show-Renderer für 3744 LEDs: 30,597 ms Referenzpfad gegenüber 2,233 ms
  Bulk-Pfad, entsprechend 13,70-facher Beschleunigung.

## TouchDesigner-Live-Prüfung

- Reale Laufzeit: 9005 Frames in 150,03 Sekunden, entsprechend 60,02 FPS bei
  60 FPS Sollwert.
- Projektfehler: 0.
- Renderer-Ausgabe: 3744 Samples mit drei Farbkanälen.
- Panel-UV-Verteilung: Mitte 517, Oben 269, Unten 398, Rückwand 2560.
- Materialwechsel speichert Speed und weitere Parameter pro Material; erneute
  Auswahl stellt den jeweiligen Materialzustand wieder her.
- Phasenwechsel und Speed-Änderungen verursachen keinen Zeitsprung.
- Show-Befehle Play, Pause, Stop, Previous, Next, Go, Loop und Blackout wurden
  über die echten TouchDesigner-Callbacks geprüft.
- Endzustand vor Speicherung: Show gestoppt, Cue 0, Blackout aus.
- Art-Net-Sender und sichtbarer DMX-Out bleiben aus.
- Kalibrierungs-Reset setzt 88 aktive Werte zurück; die 12 unwirksamen
  Legacy-Parameter sind schreibgeschützt und eindeutig markiert.
- Vorschau verwendet 3744 aktive Mapping-Punkte; Side 0–1183 und Rear
  1184–3743 sind ohne Lücke getrennt.

## Behobene Live-Lücken

- TouchDesigner-`op` wird dem Material-Runtime-Modul explizit bereitgestellt.
- Fehlende Alpha-Parameter werden sicher als 1,0 behandelt.
- Neustart bindet die gespeicherte Phase an die aktuelle Laufzeit an, ohne
  Stillstandszeit nachzuholen.
- Show-Sampler und Renderer werden über gültige Netzwerkgrenzen verbunden.
- TouchDesigner-Kanäle werden über ihre Werte statt als Python-Iterator gelesen.
- Der P0-Art-Net-Builder ersetzt generierte DAT-Inhalte vollständig. Wiederholte
  Builder-Läufe erzeugen damit weiterhin genau einen `onFrameStart`- und einen
  Sender-Callback statt doppelte Sendetakte anzuhängen.

## Noch ausstehend

Die Software-Abnahme ist abgeschlossen. Als separater, beaufsichtigter Schritt
folgt die reale Hardware-Abnahme mit aktiviertem Art-Net: zuerst ein statisches
Testbild, danach Materialwechsel, Geschwindigkeitsprüfung und Show-Übergänge auf
Mitte, Oben, Unten und Rückwand.
