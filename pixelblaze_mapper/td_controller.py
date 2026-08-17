"""TouchDesigner adapter for the portable Pixelblaze mapper.

The module is imported by a Text DAT inside the project.  All TouchDesigner
objects are passed in by the callback so this file remains importable in normal
Python for review and packaging.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .mapper_io import (
    MappingData,
    PixelblazeGenerator,
    export_marimapper_csv,
    export_pixelblaze_json,
    import_marimapper_csv,
    import_pixelblaze,
    materialize_pixelblaze_generator,
)


EXPECTED_PIXELS = 3740
_states: dict[str, dict[str, object]] = {}


def initialize(ui_owner) -> None:
    """Synchronize UI state with the persistent mapping tables."""

    if getattr(ui_owner.par, "Preservecoordinates", None) is None:
        pages = ui_owner.customPages
        page = pages[0] if pages else ui_owner.appendCustomPage("Mapper UI")
        preserve = page.appendToggle(
            "Preservecoordinates", label="Preserve room coordinates"
        )[0]
        preserve.default = False
        preserve.val = False
    root = ui_owner.parent()
    active = _mapping_from_table(root.op("map_active"), "touchdesigner-active")
    if active.coordinates:
        state = _state(ui_owner)
        state.setdefault("active", active)
        state.setdefault("draft", active)
        _update_ui(ui_owner, active, "READY - current TouchDesigner map", draft=False)
        _set_status(root, "state", "ready")
        _set_status(root, "pixel_count", len(active.coordinates))


def open_with_dialog(ui_owner, chooser, kind: str) -> None:
    file_types = ["csv"] if kind == "marimapper-csv" else ["json", "map", "txt", "js"]
    title = "Open MariMapper led_map_3d.csv" if kind == "marimapper-csv" else "Open Pixelblaze Map"
    path = chooser(load=True, title=title, fileTypes=file_types)
    if path:
        import_file(ui_owner, path, kind)


def import_file(ui_owner, path: str, kind: str | None = None) -> MappingData:
    """Load a real file, validate it, and update draft/preview tables."""

    source_path = Path(path)
    chosen_kind = kind or ("marimapper-csv" if source_path.suffix.lower() == ".csv" else "pixelblaze")
    try:
        imported = (
            import_marimapper_csv(source_path)
            if chosen_kind == "marimapper-csv"
            else import_pixelblaze(source_path)
        )
        if isinstance(imported, PixelblazeGenerator):
            imported = materialize_pixelblaze_generator(imported, EXPECTED_PIXELS)
        _load_draft(ui_owner, imported, str(source_path))
        return imported
    except Exception as exc:
        _set_error(ui_owner, f"IMPORT ERROR - {exc}")
        raise


def reload_source(ui_owner) -> None:
    path = str(ui_owner.par.Sourcepath.eval()).strip()
    if not path:
        _set_error(ui_owner, "RELOAD BLOCKED - no source file selected")
        return
    import_file(ui_owner, path)


def set_fit_mode(ui_owner, mode: str) -> None:
    normalized_mode = mode.lower()
    if normalized_mode not in ("fill", "contain"):
        raise ValueError("fit mode must be fill or contain")
    ui_owner.par.Fitmode = normalized_mode
    state = _state(ui_owner)
    mapping = state.get("draft") or _mapping_from_table(ui_owner.parent().op("map_raw"), "touchdesigner-draft")
    if isinstance(mapping, MappingData) and mapping.coordinates:
        _write_derived(ui_owner.parent(), mapping, normalized_mode)
        _update_ui(ui_owner, mapping, f"PREVIEW - {normalized_mode.title()}", draft=True)
        _set_status(ui_owner.parent(), "fit_mode", normalized_mode)


def revert(ui_owner) -> None:
    root = ui_owner.parent()
    active = _state(ui_owner).get("active") or _mapping_from_table(root.op("map_active"), "touchdesigner-active")
    if not isinstance(active, MappingData) or not active.coordinates:
        _set_error(ui_owner, "REVERT BLOCKED - no active map")
        return
    _state(ui_owner)["draft"] = active
    _write_mapping(root.op("map_raw"), active, include_state=True, raw_axes=True)
    _write_derived(root, active, str(ui_owner.par.Fitmode.eval()))
    ui_owner.par.Sourcepath = ""
    _update_ui(ui_owner, active, "REVERTED - active LED map restored", draft=False)


def export_with_dialog(ui_owner, chooser, kind: str) -> None:
    extension = "csv" if kind == "marimapper-csv" else "json"
    title = "Export MariMapper CSV" if kind == "marimapper-csv" else "Export Pixelblaze JSON"
    path = chooser(load=False, title=title, fileTypes=[extension])
    if path:
        export_file(ui_owner, path, kind)


def export_file(ui_owner, path: str, kind: str) -> str:
    mapping = _state(ui_owner).get("draft") or _mapping_from_table(
        ui_owner.parent().op("map_raw"), "touchdesigner-draft"
    )
    if not isinstance(mapping, MappingData) or not mapping.coordinates:
        raise ValueError("No mapping is loaded")
    output = (
        export_marimapper_csv(mapping)
        if kind == "marimapper-csv"
        else export_pixelblaze_json(mapping, indent=2)
    )
    target = Path(path)
    target.write_text(output, encoding="utf-8", newline="")
    ui_owner.par.Saved = True
    ui_owner.par.Lastaction = f"export:{kind}:{target}"
    ui_owner.par.Status = f"EXPORTED - {target.name}"
    _set_status(ui_owner.parent(), "state", "exported")
    return str(target)


def apply_to_leds(ui_owner) -> bool:
    """Atomically promote the draft to production after a strict count guard."""

    root = ui_owner.parent()
    draft = _state(ui_owner).get("draft") or _mapping_from_table(root.op("map_raw"), "touchdesigner-draft")
    if not isinstance(draft, MappingData):
        _set_error(ui_owner, "APPLY BLOCKED - no draft map")
        return False
    count = len(draft.coordinates)
    if count != EXPECTED_PIXELS:
        _set_error(
            ui_owner,
            f"APPLY BLOCKED - {count} pixels; LED output requires exactly {EXPECTED_PIXELS}",
        )
        ui_owner.par.Applied = False
        _set_status(root, "apply_guard", f"blocked:{count}!={EXPECTED_PIXELS}")
        return False

    preserve_par = getattr(ui_owner.par, "Preservecoordinates", None)
    preserve_coordinates = bool(preserve_par.eval()) if preserve_par is not None else False
    applied_mapping = (
        draft
        if preserve_coordinates
        else draft.normalized(str(ui_owner.par.Fitmode.eval()))
    )
    active_table = root.op("map_active")
    previous = _table_rows(active_table)
    select_dat = root.parent().op("selectDat")
    previous_input = select_dat.inputs[0] if select_dat is not None and select_dat.inputs else None
    try:
        _write_mapping(active_table, applied_mapping, include_state=False)
        if select_dat is None:
            raise RuntimeError("production selectDat was not found")
        # TouchDesigner cannot draw a wire directly across a COMP boundary.
        # ``map_active_out`` exposes map_active as the component's DAT output.
        if not root.outputConnectors:
            raise RuntimeError("mapper component has no map_active_out connector")
        root.outputConnectors[0].connect(select_dat)
        _state(ui_owner)["active"] = draft
        ui_owner.par.Applied = True
        ui_owner.par.Draft = False
        coordinate_mode = "preserved room coordinates" if preserve_coordinates else "normalized"
        ui_owner.par.Status = (
            f"LIVE - {count} pixels applied to LED pipeline | {coordinate_mode}"
        )
        ui_owner.par.Lastaction = "apply:success"
        _set_status(root, "state", "live")
        _set_status(root, "apply_guard", "passed")
        return True
    except Exception as exc:
        _write_rows(active_table, previous)
        if previous_input is not None and select_dat is not None:
            if previous_input.parent() == root and root.outputConnectors:
                root.outputConnectors[0].connect(select_dat)
            else:
                previous_input.outputConnectors[0].connect(select_dat)
        _set_error(ui_owner, f"APPLY ROLLED BACK - {exc}")
        return False


def handle_pulse(ui_owner, chooser, name: str) -> None:
    ui_owner.par.Lastaction = name
    if name == "Openpixelblaze":
        open_with_dialog(ui_owner, chooser, "pixelblaze")
    elif name == "Openmarimapper":
        open_with_dialog(ui_owner, chooser, "marimapper-csv")
    elif name == "Exportpixelblaze":
        export_with_dialog(ui_owner, chooser, "pixelblaze")
    elif name == "Exportmarimapper":
        export_with_dialog(ui_owner, chooser, "marimapper-csv")
    elif name == "Reload":
        reload_source(ui_owner)
    elif name == "Revert":
        revert(ui_owner)
    elif name == "Applytoleds":
        apply_to_leds(ui_owner)


def _load_draft(ui_owner, mapping: MappingData, source_path: str) -> None:
    root = ui_owner.parent()
    _state(ui_owner)["draft"] = mapping
    _write_mapping(root.op("map_raw"), mapping, include_state=True, raw_axes=True)
    _write_derived(root, mapping, str(ui_owner.par.Fitmode.eval()))
    ui_owner.par.Sourcepath = source_path
    ui_owner.par.Saved = True
    ui_owner.par.Applied = False
    warning = f" | {mapping.warnings[0]}" if mapping.warnings else ""
    _update_ui(
        ui_owner,
        mapping,
        f"LOADED - {mapping.source_format}{warning}",
        draft=True,
    )
    ui_owner.par.Lastaction = f"import:{mapping.source_format}"
    _set_status(root, "state", "draft")
    _set_status(root, "source_path", source_path)
    _set_status(root, "warnings", " | ".join(mapping.warnings))


def _write_derived(root, mapping: MappingData, mode: str) -> None:
    normalized = mapping.normalized(mode)
    _write_mapping(root.op("map_normalized"), normalized, include_state=True)
    preview = root.op("preview3d")
    if preview is not None:
        # The preview consumes raw coordinates and owns its Fill/Contain view
        # transform, keeping the export/apply tables independent of rendering.
        preview.par.Coordinatedat = root.op("map_raw")
        preview.par.Fitmode = mode
        preview.op("instance_data").cook(force=True)


def _write_mapping(
    table, mapping: MappingData, *, include_state: bool, raw_axes: bool = False
) -> None:
    if table is None:
        raise RuntimeError("required mapping table is missing")
    table.clear()
    header = ["index", *(('x', 'y', 'z') if raw_axes else ('tx', 'ty', 'tz'))]
    if include_state:
        header.append("state")
    table.appendRow(header)
    missing = set(mapping.missing_indices)
    for index, coordinate in enumerate(mapping.coordinates):
        xyz = (*coordinate, 0.0) if mapping.dimensions == 2 else coordinate
        row = [index, xyz[0], xyz[1], xyz[2]]
        if include_state:
            row.append("missing" if index in missing else "valid")
        table.appendRow(row)


def _mapping_from_table(table, source_format: str) -> MappingData:
    if table is None or table.numRows < 2:
        return MappingData((), 3, source_format)
    coords = []
    missing = []
    for row in range(1, table.numRows):
        coords.append(tuple(float(table[row, col]) for col in range(1, 4)))
        if table.numCols > 4 and str(table[row, 4]) == "missing":
            missing.append(row - 1)
    return MappingData(tuple(coords), 3, source_format, missing_indices=tuple(missing))


def _update_ui(ui_owner, mapping: MappingData, message: str, *, draft: bool) -> None:
    coordinates = [
        point for index, point in enumerate(mapping.coordinates) if index not in set(mapping.missing_indices)
    ] or list(mapping.coordinates)
    bounds = []
    for axis in range(mapping.dimensions):
        values = [point[axis] for point in coordinates]
        bounds.append((min(values), max(values)) if values else (0.0, 0.0))
    while len(bounds) < 3:
        bounds.append((0.0, 0.0))
    ui_owner.par.Pixelcount = len(mapping.coordinates)
    ui_owner.par.Dimensions = f"{mapping.dimensions}D"
    ui_owner.par.Bounds = "  ".join(
        f"{axis}[{lo:.3f}..{hi:.3f}]" for axis, (lo, hi) in zip("xyz", bounds)
    )
    ui_owner.par.Draft = draft
    ui_owner.par.Applied = not draft
    ui_owner.par.Status = message


def _set_error(ui_owner, message: str) -> None:
    ui_owner.par.Status = message
    ui_owner.par.Lastaction = "error"
    _set_status(ui_owner.parent(), "state", "error")
    _set_status(ui_owner.parent(), "error", message)


def _state(ui_owner) -> dict[str, object]:
    return _states.setdefault(ui_owner.path, {})


def _set_status(root, key: str, value) -> None:
    table = root.op("status")
    if table is None:
        return
    for row in range(table.numRows):
        if str(table[row, 0]) == key:
            table[row, 1] = value
            return
    table.appendRow([key, value])


def _table_rows(table) -> list[list[str]]:
    return [[str(table[row, col]) for col in range(table.numCols)] for row in range(table.numRows)]


def _write_rows(table, rows: Iterable[Iterable[object]]) -> None:
    table.clear()
    for row in rows:
        table.appendRow(list(row))
