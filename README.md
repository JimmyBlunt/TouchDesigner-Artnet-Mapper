# TouchDesigner Art-Net Mapper

TouchDesigner project for mapping GPU-driven effects to a mixed WS2812B/APA102 LED installation over Art-Net.

## Verified project

Open `PixelblazeMapper_WORKING_PHASE2_EFFECTS_CORE.41.toe` in TouchDesigner. The file `PixelblazeMapper_WORKING_PHASE2_EFFECTS_CORE.toe` is the matching stable alias.

The current live configuration was verified on physical LEDs:

- Art-Net unicast target: `10.0.0.251:6454`
- Universes: `0` through `9`
- Pixels: `1679`, RGB
- Universe payload: `510` channels / `170` pixels
- Universe 9: pixels `1530` through `1678`; unused channels remain black
- Pixels `0` through `511`: WS2812B on ESP GPIO 23
- Pixels `512` through `1678`: APA102 on ESP GPIO 18 (data) and GPIO 19 (clock)
- Initial live safety brightness: `0.02`

## Live TouchDesigner path

`/project1/math1` feeds `/project1/esp_artnet_live_pack`, which produces ten 510-channel universe streams. `/project1/esp_artnet_out` sends those streams as unicast ArtDMX. The former `/project1/dmxout1` output is disabled to prevent duplicate traffic.

The retained `/project1/esp_artnet_test_pattern` branch can be reconnected for hardware diagnostics.

## Project contents

- `effects/`: effect metadata and verification reports
- `mappings/`: LED coordinate mappings
- `pixelblaze_mapper/`: portable mapping code
- `tests/`: mapping and integration tests
- `docs/`: implementation notes, user guide, and visual evidence
- `assets/`: installation reference images
- `touchdesigner-mcp-td/`: embedded TouchDesigner MCP bridge used to inspect and update the live project (API version `1.5.0`)

Backups, temporary files, and obsolete `.toe` versions are intentionally excluded from Git. The embedded MCP bridge is included so the repository contains the complete runnable integration state.
