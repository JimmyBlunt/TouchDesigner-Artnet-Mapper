# Phase 2 Preview staging

This directory contains the isolated TouchDesigner Phase 2 preview builder and validation logic.

Files:

- `build_phase2_preview.py`: idempotently creates only
  `/project1/pixelblaze_mapper/preview3d/phase2_interaction_background_prototype`.
- `test_phase2_preview.py`: validates paths, public controls and output, then
  writes a screenshot into this local directory.

Safety guarantees:

- No production mapping or DMX node is modified.
- Existing `preview_out`, `preview_render` and `preview_camera` are not rewired.
- The scripts never call `project.save()`.
- Rebuilding deletes only the named isolated prototype child.

Planned interaction:

- Left drag: orbit/tumble.
- Right drag: pan.
- Middle drag or wheel: dolly/zoom.
- `F`: frame all LEDs.
- `H`: home camera.

The builder uses the official local `/sys/TDTox/cameraViewport` template and
creates a separate photo backplate chain with Contain, Cover, Stretch,
Perspective Corner Pin, background opacity and LED opacity.
