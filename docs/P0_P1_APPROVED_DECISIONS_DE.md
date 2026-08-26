# Verbindliche Produktentscheidungen für P0 und P1

Freigegeben am 26.08.2026.

## Mapping und Hardwarevertrag

- Gesamtzahl: 3.744 LEDs, Indizes 0–3743.
- Mitte: 0–516, 517 LEDs.
- Oben: 517–785, 269 LEDs.
- Unten: 786–1183, 398 LEDs.
- Rückwand: 1184–3743, 2.560 LEDs in zehn Feldern zu je 256 LEDs.
- Port 1 reserviert U1–U4.
- Port 2 reserviert U5–U8.
- Port 3 reserviert U9–U12.
- U7, U8 und U12 werden ausdrücklich mit Schwarz belegt.
- Jedes Universe verwendet 510 Kanäle beziehungsweise 170 RGB-Pixel.

## Dialogzuständigkeiten

- Art-Net Router ist die einzige bearbeitbare Ausgabekonfiguration.
- Output Config ist eine schreibgeschützte Live-Zusammenfassung und öffnet bei
  Bedarf den Art-Net Router.
- Material Browser dient Materialwahl und Schnellsteuerung.
- Material Player zeigt die vollständigen Parameter zusammen mit der
  Rohmaterialvorschau.

## Materialzustand

- Speed, Scale, Width, Focus X/Y, Zoom, Gradient, Farben und Koordinatenmodus
  werden pro Material gespeichert.
- Änderungen betreffen standardmäßig nur das aktive Material.
- Ein separater Global Master Speed besitzt den Standardwert 1,0.
- Geschwindigkeitsänderungen dürfen keinen Phasensprung erzeugen.

## Räumliches Verhalten und Show Control

- `Global` verwendet die Raumkoordinaten.
- `Panel Local` verwendet echte lokale UV-Koordinaten für Mitte, Oben, Unten
  und Rückwand, sodass die optische Durchlaufgeschwindigkeit vergleichbar ist.
- Show-Presets speichern Material und Parameter vollständig.
- Zielgruppen sind `all`, `middle`, `upper`, `lower` und `rear` und werden im
  Renderer tatsächlich maskiert.

## Versionierung, Shortcuts und Abnahme

- Core 68 wird nicht überschrieben.
- P0 wird als Core 69 gespeichert und separat committed.
- P1 wird als Core 70 gespeichert und separat committed.
- Shortcuts reagieren nur bei aktivem TouchDesigner.
- Hardwaretests erfolgen nach jeder Phase beaufsichtigt.
- Builder-, Python- und Offline-Tests laufen vor jeder Änderung des geöffneten
  TouchDesigner-Projekts.
