# Core Effects – Implementierungsstatus

## Schutz der bestehenden Produktion

Die Effektbibliothek erweitert ausschließlich:

- `/project1/madmapper_material_fs`
- `/project1/madmapper_material_player`
- `/project1/madmapper_player_controls`
- `/project1/material_browser`
- `/project1/visual_source_switch`

Unverändert bleiben `LedMap`, die 3.740-Sample-Ausgabe, GRB-Packing,
Universumsberechnung, Routingtabelle und `dmxout1`.

## Koordinatenmodi

- `Global Canvas`: ein durchgehender Effekt über die komplette 0..1-Map.
- `Panel Local`: Wiederholung in der vorhandenen Rückwandstruktur 2 × 5.
- `Hybrid`: Mischung aus globaler Bewegung und lokaler Panelstruktur.

## Enthaltene Materialien

Fill, Gradient und Diagonals bleiben erhalten. Ergänzt werden Fluid Noise,
Cellular, Blobby, Spatial Pulse / Line Anim, Comet Tails, Arcs, Noisy Barcode,
Particles, Bad TV und Noise Dissolve Transition.

## Live-Verifikation am 17. August 2026

- Alle 13 Materialien wurden bei 512 × 512 einzeln gekocht.
- Alle Materialien liefern ein nicht-konstantes Bild und melden keine
  Shaderfehler oder Warnungen.
- Alle 13 Browser-Vorschauen kompilieren und rendern fehlerfrei.
- Global-, Panel- und Hybridmodus liefern unterschiedliche Bildräume.
- Der Effekt ist im bestehenden `LED_PREVIEW_OUT` auf Rückwand und Seitenwand
  sichtbar.
- Produktionsinvarianten nach dem Einbau: `LedMap`, `null4` und `null5` haben
  weiterhin jeweils 3.740 Samples; `DMX_Universes` und Routingtabelle weiterhin
  jeweils 23 Zeilen inklusive Header.
- `dmxout1` bleibt an `/project1/merge1` angeschlossen; `selectDat` bleibt an
  `/project1/pixelblaze_mapper/map_active_out` angeschlossen.
