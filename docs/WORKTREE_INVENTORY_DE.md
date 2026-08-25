# Inventar weiterer lokaler Arbeitsdateien

Stand: 25. August 2026, nach dem Core-67-Snapshot.

Die Dateien in diesem Inventar waren bereits als lokale Änderungen oder neue
Arbeitsdateien vorhanden. Sie sind **nicht** Teil der Core-66-/Core-67-Commits,
damit keine unbestätigten Zwischenstände versehentlich in einen Release-Stand
übernommen werden.

## Bereits geänderte, versionierte Dateien

- `.gitignore`
- `README.md`
- `docs/HOWTO_CURRENT_SYSTEM_DE.md`
- `effects/build_core_effects.py`
- `phase2_preview/build_two_plane_calibration.py`
- `pixelblaze_mapper/build_multi_controller_output.py`
- `pixelblaze_mapper/integrate_live_show.py`
- `pixelblaze_mapper/td_controller.py`
- `tests/test_multi_controller.py`
- `PixelblazeMapper_WORKING_PHASE2_EFFECTS_CORE.toe`

## Neue Arbeitsbereiche

- `docs/` mit Mapping-, Material-Browser-, Shortcut- und Verkabelungsnotizen
- `mappings/` mit Rohdaten, Sicherungen, JSON-/CSV-Exports und Reports
- `pixelblaze_mapper/` mit Spatial-Map-, Material-Library-, Kalibrierungs- und
  Rewire-Werkzeugen
- `tests/` mit zugehörigen Testskripten
- `pixelblaze_patterns/` und `tools/`
- temporäre TouchDesigner-Dateien zu `PixelblazeMapper_WORKING_PHASE2_PHOTO.33`

Vor einem Sammel-Commit sollten diese Zwischenstände einzeln geprüft werden,
insbesondere generierte Bilder, Mapping-Exports und temporäre TouchDesigner-
Verzeichnisse. Der aktuelle, getestete und gespeicherte Projektstand ist davon
unabhängig in `Backup/Projektdatei/...EFFECTS_CORE.67.toe` vorhanden.
