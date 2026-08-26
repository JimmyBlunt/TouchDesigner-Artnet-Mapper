# P0: Kanonischer LED-Vertrag

Stand: 26.08.2026. Dieser Vertrag ist die verbindliche Quelle für Pixel Mapper,
LED Preview und Ausgabebuilder. Das reine Python-Modul
`pixelblaze_mapper/installation_contract.py` hat keine TouchDesigner-, Netzwerk-
oder Hardware-Nebenwirkungen.

## LED-Bereiche

| Bereich | Indizes | Anzahl | Hardware-Port | reservierte UI-Universes |
|---|---:|---:|---:|---:|
| Mitte | 0–516 | 517 | 1 | U1–U4 |
| Oben | 517–785 | 269 | 2 | U5–U8 |
| Unten | 786–1183 | 398 | 3 | U9–U12 |
| Rückwand | 1184–3743 | 2560 | separater Rückwandpfad | – |

Die Bereiche sind lückenlos und enthalten zusammen exakt **3.744 LEDs**. Die
Rückwand besteht aus zehn vollständigen 16×16-Feldern.

Ein Universe enthält 510 Kanäle beziehungsweise 170 RGB-Pixel. Jeder der drei
Side-Ports reserviert vier vollständige Universes. U7, U8 und U12 werden immer
schwarz gepackt; ihre Kapazität darf nicht dem nächsten Panel zugeschlagen
werden. Auf dem nullbasierten Art-Net-Wire sind dies U6, U7 und U11.

## Missing-Policy

- Ein **Draft** darf deklarierte fehlende Koordinaten behalten. Der Index bleibt
  erhalten und die Vorschau stellt die betreffende LED schwarz dar. Ein
  Entfernen der Zeile wäre unzulässig, weil alle nachfolgenden Hardwareindizes
  verschoben würden.
- Eine **aktive Map** darf keine als `missing` markierte LED enthalten. Apply
  wird mit einer verständlichen Fehlermeldung blockiert.
- `(0, 0, 0)` allein gilt nicht als fehlend. Ausschließlich der explizite
  `missing_indices`-/`state=missing`-Zustand ist maßgeblich.
- Falsche Anzahl, ungültige Dimensionen, nichtnumerische und nichtendliche Werte
  werden in Draft und Live abgewiesen.

Die aktuelle kanonische Datei
`mappings/mapping_complete_new_0_1183_full_2026-08-24.json` enthält 3.744
endliche XYZ-Koordinaten und keine `(0,0,0)`-Platzhalter.

## P0-Integration

- Pixel Mapper verwendet `TOTAL_PIXELS` statt einer lokalen 3.740-Konstante.
- Apply validiert zusätzlich die Missing-Policy, bevor die aktive Tabelle oder
  Produktionsverbindung verändert wird.
- LED Preview trimmt Side auf 0–1183 und Rear auf 1184–3743.
- `build_led_preview_contract.py` prüft vor der Änderung 3.744
  Koordinatenzeilen, ergänzt idempotent den Count-Guard und setzt deklarierte
  Missing-Indizes in allen drei Farbkanälen auf Schwarz.
- Photo Calibration erwartet 3.744 Samples und Rear-Start 1184.
- Surface-UV, Rescan und Multi-Controller-Packer beziehen gemeinsame Grenzwerte
  aus dem Contract.

Die Änderungen sind offline testbar. In diesem Arbeitsschritt werden weder eine
`.toe`-Datei gespeichert noch Art-Net aktiviert oder Hardwarepakete gesendet.
