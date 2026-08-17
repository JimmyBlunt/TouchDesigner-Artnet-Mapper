# TouchDesigner Art-Net Mapper

Complete TouchDesigner project for mapping GPU effects to a mixed
WS2812B/APA102 LED installation and distributing the pixels to multiple Art-Net
receivers.

## Verified project

Open `PixelblazeMapper_WORKING_PHASE2_EFFECTS_CORE.43.toe` in TouchDesigner.
`PixelblazeMapper_WORKING_PHASE2_EFFECTS_CORE.toe` is the matching stable alias.
Both files contain the same tested state.

Safe startup state:

- all four legacy/new DMX Out CHOPs are inactive;
- controller brightness defaults to `0.02`, but `Enabled=0` for both receivers;
- show transport is stopped at cue 1 with blackout off;
- the full TouchDesigner `/project1` tree reports zero errors.

## Current signal path

```text
25 GLSL materials / show A-B mixer
              |
              v
existing visual source switch -> existing 3D LED preview -> /project1/math1 (3 x 3740)
                                                         |
                          +------------------------------+------------------+
                          |                                                 |
                          v                                                 v
                WS2812_NODE packer                                APA102_ESP packer
                source 0..511                                     source 512..1678
                target 0..511                                     target 512..1678
                4 x 510 DMX slots                                 10 x 510 DMX slots
                10.0.0.244:6454                                   10.0.0.251:6454
```

The ESP branch deliberately leaves target pixels `0..511` black because the
current ESP firmware places the APA102 chain after its 512-pixel WS2812 prefix.
Source pixels `1679..3739` remain available for the later full-installation 3D
mapping.

## TouchDesigner controls

- `/project1/madmapper_material_browser`: clickable 5 x 5 library with 25
  GPU effects; legacy indices `0..12` remain stable.
- `/project1/multi_controller_output/ui_preview`: editable receiver IP,
  start universe, brightness and enable fields plus validated safe apply,
  deliberate start and immediate all-off controls.
- `/project1/show_control/control_panel_preview`: play, pause, stop, previous,
  next, go, loop and blackout for the deterministic A/B show sequencer.
- `/project1/pixelblaze_mapper/preview3d/preview_out`: existing full LED preview,
  now also showing show transitions on rear and side panels.

## Effect and show library

The manifest contains 25 effects, including Fluid Noise, Cellular, Blobby,
Spatial Pulse / Line Anim, Comet Tails, Arcs, Noisy Barcode, Particles, Bad TV,
Noise Dissolve, Plasma, Fire, Aurora, Ocean Waves, Ripple Rings, Kaleidoscope,
Tunnel, Matrix Rain, Twinkle, Scanner, Reaction Diffusion and Grid Morph.

Shows are JSON files under `shows/`. `shows/demo_show.json` demonstrates three
cues and the sequencer supports `cut`, `crossfade`, `dissolve`, `wipe`,
`radial` and `glitch` transitions.

## Verification

Run the portable test suite from the repository root:

```powershell
python -m unittest discover -s tests
```

The checked-in state passes 92 tests. Live TouchDesigner acceptance additionally
verified all 25 material clicks, all coordinate modes, exact cue boundaries,
all six transition renders, both controller packers, invalid-field blocking,
safe black Art-Net traffic to both configured receivers and final all-off state.

Detailed instructions and evidence are in `docs/HOWTO_CURRENT_SYSTEM_DE.md` and
`docs/TEST_REPORT_2026-08-18_DE.md`.

## Repository contents

- `effects/`: GLSL shader, manifest, builder and implementation status
- `shows/`: validated show definitions
- `pixelblaze_mapper/`: mapping, multi-controller and show-control cores/builders
- `mappings/`: coordinate mappings
- `tests/`: portable unit and contract tests
- `docs/screenshots/`: real TouchDesigner screenshots used by the guide
- `touchdesigner-mcp-td/`: embedded TouchDesigner bridge for a reproducible full state

Backups, autosaves and obsolete `.toe` versions are intentionally excluded.
