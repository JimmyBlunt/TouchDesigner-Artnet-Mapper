# Phase 2 – verifizierter Implementierungsstand

Stand: 13. August 2026

## Ergebnis

Die Phase-2-Funktionen wurden lokal und isoliert aufgebaut. Die laufende
Produktionskette wurde nicht umverdrahtet.

### DMX-Kern

- Kanonische Berechnung in `pixelblaze_mapper/dmx_config.py`.
- RGB-Eingang wird in bestehender GRB-Reihenfolge gepackt.
- 170 Pixel beziehungsweise 510 aktive DMX-Slots pro vollem Universum.
- Indexlücken bleiben physische, schwarz ausgegebene Slots.
- Auto-Allokation, Startuniversum/-kanal, Art-Net-Adressierung,
  Routingtabellen, Padding, Validierung und Diff-Klassifikation.
- Baseline 3.714 Pixel: 11.142 Kanäle, 22 Universen, letztes Universum
  144 Pixel/432 aktive Slots/78 Null-Padding.
- `allocate_dmx()` stellt den stabilen Adapter für die TouchDesigner-UI bereit.

### OUTPUT (DMX)-Entwurf

- COMP: `/project1/pixelblaze_mapper/output_config`
- Ansicht: `/project1/pixelblaze_mapper/output_config/ui_preview`
- Zeigt Pixel-/Kanal-/Universumsbedarf, GRB, Netzwerkdaten und kompakte
  Universumsübersicht.
- `LIVE` und `DRAFT` sind sichtbar getrennt.
- `Review & Apply` bleibt absichtlich gesperrt, bis Hardware-Entscheidungen
  und atomarer Apply/Rollback bestätigt sind.

Screenshot: `phase2-output-ui.png`

### Interaktive 3D-Vorschau und Hintergrund

- COMP:
  `/project1/pixelblaze_mapper/preview3d/phase2_interaction_background_prototype`
- Interaktives Panel:
  `.../interactive_camera/renderView`
- Ausgabe: `.../prototype_out` mit 960 × 960 Pixeln.
- Offizielles TouchDesigner-`cameraViewport`: LMB Orbit, RMB Pan,
  MMB/Mausrad Dolly/Zoom, `F` Frame, `H` Home.
- Hintergrund: Open/Clear, Opacity, Contain/Cover/Stretch und optionaler
  perspektivischer Corner Pin.
- Standbilder bleiben fest auf Frame 0; ein beim Test entdeckter schwarzer
  Bildzustand durch Timeline-Indexierung wurde behoben.
- LED-Render besitzt transparenten Hintergrund und wird über das Referenzbild
  gelegt.

Screenshot: `phase2-background-preview.png`

## Verifikation

- Lokale Python-Suite: 33/33 Tests bestanden.
- DMX-Kern: 19/19 Tests bestanden.
- Phase-2-Preview-Selbsttest: bestanden, keine Probleme.
- `/project1/pixelblaze_mapper/output_config`: 0 Node-Fehler.
- Phase-2-Preview-Prototyp: 0 Node-Fehler.
- Produktionsbaseline unverändert:
  - `selectDat` liest weiter `pixelblaze_mapper/map_active_out`;
  - 3.714 Samples an `null4` und `null5`;
  - 23 Zeilen in `DMX_Universes` inklusive Header;
  - 23 Zeilen in `dmxout1_routingtable` inklusive Header;
  - `dmxout1` aktiv und die geprüften Produktionsnodes ohne Fehler.

## Noch gesperrt

Der Live-DMX-Apply ist noch nicht freigegeben. Vor seiner Implementierung und
Hardware-Abnahme müssen die Entscheidungen aus `PHASE2_ROADMAP_DE.md` geklärt
werden: Verhalten bei kleineren Maps, Controller-Limit, globale oder
segmentweise Farbreihenfolge, ArtSync und optionaler Blackout vor Routingwechsel.

