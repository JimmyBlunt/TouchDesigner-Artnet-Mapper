# Core Effects – Implementierungsstatus

## Schutz der bestehenden Produktion

Die Effektbibliothek erweitert ausschließlich:

- `/project1/madmapper_material_fs`
- `/project1/madmapper_material_player`
- `/project1/madmapper_player_controls`
- `/project1/material_browser`
- `/project1/visual_source_switch`

Unverändert bleiben `LedMap`, die 3.740-Sample-Ausgabe, das DMX-Packing,
Universumsberechnung, Controller-Routing und die physischen Ausgänge.

## Koordinatenmodi

Jeder der 25 Effekte erhält denselben UV-Raum und ist deshalb ohne eigene
Sonderkonfiguration in allen drei Modi verwendbar:

- `Global Canvas`: ein durchgehender Effekt über die komplette 0..1-Map.
- `Panel Local`: Wiederholung im konfigurierten Panelraster.
- `Hybrid`: einstellbare Mischung aus globalem und lokalem Panelraum.

## Effektbibliothek Version 2

Die Indizes 0–12 bleiben gegenüber Version 1 stabil. Neu sind die Indizes
13–24. IDs, Anzeigenamen, Kategorien und Vorschau-Presets liegen zentral in
`effects_manifest.json`; das Installationsskript liest diese Metadaten direkt.

| Index | ID | Material | Kategorie |
|---:|---|---|---|
| 0 | `fill` | Fill | Utility |
| 1 | `gradient` | Gradient | Utility |
| 2 | `diagonals` | Diagonals | Geometry |
| 3 | `fluid_noise` | Fluid Noise | Organic |
| 4 | `cellular` | Cellular | Organic |
| 5 | `blobby` | Blobby | Organic |
| 6 | `spatial_pulse` | Spatial Pulse / Line Anim | Geometry |
| 7 | `comet_tails` | Comet Tails | Particles |
| 8 | `arcs` | Arcs | Geometry |
| 9 | `noisy_barcode` | Noisy Barcode | Glitch |
| 10 | `particles` | Particles | Particles |
| 11 | `bad_tv` | Bad TV | Glitch |
| 12 | `noise_dissolve_transition` | Noise Dissolve Transition | Transition |
| 13 | `plasma` | Plasma | Abstract |
| 14 | `fire` | Fire | Organic |
| 15 | `aurora` | Aurora | Organic |
| 16 | `ocean_waves` | Ocean Waves | Organic |
| 17 | `ripple_rings` | Ripple Rings | Geometry |
| 18 | `kaleidoscope` | Kaleidoscope | Geometry |
| 19 | `tunnel` | Tunnel | Geometry |
| 20 | `matrix_rain` | Matrix Rain | Digital |
| 21 | `twinkle_sparkle` | Twinkle / Sparkle | Particles |
| 22 | `scanner` | Scanner | Geometry |
| 23 | `reaction_diffusion` | Reaction Diffusion | Organic |
| 24 | `geometric_grid_morph` | Geometric Grid Morph | Geometry |

`Reaction Diffusion` ist bewusst als zustandslose, domain-verzerrte Näherung
realisiert. Sie benötigt keinen Feedback-Puffer und bleibt dadurch in einem
MadMapper-/ISF-Wrapper portierbar.

## Automatische Prüfung

`tests/test_effects_library.py` prüft:

- exakt 25 lückenlos indizierte Effekte,
- eindeutige stabile IDs und Anzeigenamen,
- Übereinstimmung von Manifest, Shader-Dispatch und Builder,
- vollständige Presets und gültige Kategorien,
- unveränderte Uniformbelegung,
- die drei Koordinatenmodi `global`, `panel` und `hybrid`,
- explizite Shader-Zweige für alle Indizes 0–24,
- statisch ausgeglichene Klammern und vorhandenen TouchDesigner-Ausgang.

## Bisherige Live-Verifikation

Die 13 Effekte aus Version 1 wurden am 17. August 2026 in TouchDesigner bei
512 × 512, im Browser und in der LED-Vorschau verifiziert. Die zwölf neuen
Effekte sind quellseitig und statisch getestet. Ihre Live-/Screenshot-Abnahme
erfolgt beim nächsten idempotenten Lauf von `build_core_effects.py` in der
laufenden TouchDesigner-Instanz.
