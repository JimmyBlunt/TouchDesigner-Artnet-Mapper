"""Static contracts for the isolated TouchDesigner material-library browser."""

import ast
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "pixelblaze_mapper" / "build_material_library_browser.py"


def source():
    return BUILDER.read_text(encoding="utf-8")


def module():
    spec = importlib.util.spec_from_file_location("material_library_browser_builder", BUILDER)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def test_builder_and_embedded_runtime_are_valid_python():
    ast.parse(source())
    runtime = module()._runtime_source()
    compile(runtime, "<material-library-runtime>", "exec")


def test_builder_is_additive_and_has_no_output_or_project_save_path():
    value = module()
    text = source()
    assert value.OWNER == "/project1/madmapper_library"
    assert 'baseCOMP, "madmapper_library"' in text
    assert "project.save(" not in text
    assert "visual_source_switch" not in text
    assert "dmxoutCHOP" not in text
    assert "/project1/math1" not in text
    assert '"outputsActive": False' in text
    assert '"productionTouched": False' in text
    assert '"projectSaved": False' in text


def test_editable_paths_and_browser_state_are_preserved_on_rebuild():
    text = source()
    assert "if parameter is None:" in text
    assert '_ensure_string(owner, page, "Catalogfile"' in text
    assert '_ensure_string(owner, page, "Importroot"' in text
    assert '_ensure_string(owner, page, "Approvedroots"' in text
    assert "if state.numRows < 2:" in text
    assert "if history.numRows == 0:" in text
    assert "_get_or_create" in text


def test_catalog_contract_accepts_core_fields_and_legacy_aliases():
    runtime = module()._runtime_source()
    for field in (
        "id", "name", "label", "source_path", "relative_path", "kind",
        "groups", "category", "tags", "compatibility",
        "compatibility_reasons", "compatibility_reason", "metadata",
        "preview_path", "prepared_shader_path", "touchdesigner_shader_path",
    ):
        assert repr(field) in runtime
    assert "getattr(catalog, 'materials', getattr(catalog, 'items', catalog))" in runtime
    assert "for key in ('materials', 'items', 'entries')" in runtime


def test_search_facets_paging_cards_and_details_are_present():
    text = source()
    runtime = module()._runtime_source()
    assert '"search_field"' in text
    assert 'casefold() in {"", "field"}' in text
    assert '"group_filter"' in text
    assert '"compat_filter"' in text
    assert '"previous_page"' in text
    assert '"next_page"' in text
    assert "for slot in range(32):" in runtime
    assert "def _page_size():" in runtime
    assert "def toggle_layout():" in runtime
    assert "return 32 if _layout_mode() == '8x4' else 8" in runtime
    assert "def apply_filters(" in runtime
    assert "SequenceMatcher" in runtime
    assert "def _query_token_matches(" in runtime
    assert "def toggle_dropdown(" in runtime
    assert "def select_category(" in runtime
    assert "def select_compatibility(" in runtime
    assert '"group_dropdown"' in text
    assert '"compat_dropdown"' in text
    assert '"AUTO-PREPARE"' in text
    assert '"MANUAL / BLOCKED"' in text
    assert '("imported", "IMPORTED")' in text
    assert '"layout_toggle"' in text
    assert "def change_page(" in runtime
    assert "def select_slot(" in runtime
    assert "selected_detail" in text
    assert "catalog_view" in text
    assert "runtime.module.refresh()" in text


def test_preview_and_import_are_explicit_separate_actions():
    text = source()
    runtime = module()._runtime_source()
    assert '"preview_selected", "SHOW STORED PREVIEW"' in text
    assert '"open_live_preview", "OPEN LIVE PREVIEW"' in text
    assert '"import_selected", "IMPORT SELECTED"' in text
    assert "def preview_selected():" in runtime
    assert "def open_live_preview():" in runtime
    assert "def import_selected():" in runtime
    assert "if _state('import_confirm_id') != item['id']:" in runtime
    assert "CONFIRM IMPORT" in runtime
    assert runtime.index("CONFIRM IMPORT") < runtime.index("from pixelblaze_mapper.material_library import import_material")


def test_import_uses_safe_core_then_conservative_td_adapter():
    runtime = module()._runtime_source()
    assert "from pixelblaze_mapper.material_library import import_material, load_catalog" in runtime
    assert "from pixelblaze_mapper.madmapper_td_adapter import adapt_material, write_prepared_shader" in runtime
    assert "result = import_material(catalog, item['id'], import_root)" in runtime
    assert "adapt_material(" in runtime
    assert "write_prepared_shader(adaptation, result.directory / 'prepared.frag')" in runtime
    assert "item['prepared_shader_path'] = str(prepared)" in runtime
    assert "adaptation unavailable" in runtime


def test_every_runtime_file_read_is_approved_and_live_preview_is_isolated():
    text = source()
    runtime = module()._runtime_source()
    assert "resolve(strict=True)" in runtime
    assert "Path is outside Approved Roots" in runtime
    assert "Import Folder is outside Approved Roots" in runtime
    assert "_validated_import_root(_parameter('Importroot'))" in runtime
    assert "_validated_file(item.get('preview_path')" in runtime
    assert "_live_shader_candidate" in runtime
    assert "_state('last_import_id') == item['id']" in runtime
    assert "TDOutputSwizzle" in runtime
    assert "material is not marked TouchDesigner-ready" in runtime
    assert 'glslTOP, "live_preview"' in text
    assert 'live_preview.par.const0name = "uTDTime"' in text
    assert "material_state_runtime').module.phase()" in text
    assert 'live_preview.par.const0value.expr = (' in text
    assert '"op(\'/project1/material_state_runtime\').module.phase() if "' in text
    assert '"absTime.seconds % max(1.0, parent().par.Hoverloopseconds)"' in text
    assert 'live_preview.par.vec0name = "uTDCoordinate"' in text
    assert '"Coordinatemode", "Coordinate Mode"' in text
    assert 'infoDAT, "live_preview_info"' in text
    assert 'textTOP, "compile_error_preview"' in text
    assert 'outTOP, "imported_material_out"' in text
    assert "preview.cook(force=True)" in runtime
    assert "preview.errors()" in runtime
    assert "LIVE PREVIEW FAILED" in runtime


def test_persisted_managed_import_restores_prepared_shader_after_runtime_restart():
    runtime = module()._runtime_source()

    class Parameter:
        def __init__(self, value):
            self.value = value

        def eval(self):
            return self.value

    class Parameters:
        pass

    class Owner:
        def __init__(self, approved_root, import_root):
            self.par = Parameters()
            self.par.Approvedroots = Parameter(str(approved_root))
            self.par.Importroot = Parameter(str(import_root))
            self.par.Catalogfile = Parameter(str(approved_root / "catalog.json"))

    with tempfile.TemporaryDirectory() as temp:
        approved_root = Path(temp).resolve()
        import_root = approved_root / "imported"
        material_id = "mat_0123456789abcdefabcd"
        package = import_root / material_id
        package.mkdir(parents=True)
        (package / "material-import.json").write_text(
            json.dumps({"material_id": material_id}), encoding="utf-8"
        )
        prepared = package / "prepared.frag"
        prepared.write_text("void main() {}", encoding="utf-8")
        catalog_path = approved_root / "catalog.json"
        catalog_path.write_text("{}", encoding="utf-8")

        def load_in_fresh_runtime():
            owner = Owner(approved_root, import_root)
            namespace = {"op": lambda _path: owner}
            exec(compile(runtime, "<material-library-runtime>", "exec"), namespace)
            return namespace

        catalog_record = {
            "id": material_id,
            "prepared_shader_path": str(approved_root / "stale-catalog-alias.frag"),
        }
        first = load_in_fresh_runtime()["_normalize"](catalog_record, catalog_path)
        restarted = load_in_fresh_runtime()["_normalize"](catalog_record, catalog_path)

        assert first["imported"] is True
        assert restarted["imported"] is True
        assert Path(restarted["prepared_shader_path"]) == prepared.resolve()


def test_persisted_import_manifest_must_match_the_catalog_material():
    runtime = module()._runtime_source()
    assert "manifest_data.get('material_id') != material_id" in runtime
    assert "package.parent != import_root" in runtime


def test_hover_preview_is_bounded_isolated_and_restores_the_card_image():
    text = source()
    runtime = module()._runtime_source()
    assert '"Hoverloopseconds", "Hover Loop Seconds", 6.0, 1.0, 15.0' in text
    assert "def _hover_execute(" in text
    assert 'node.par.panelvalue = "rollover"' in text
    assert "node.par.ontooff = True" in text
    assert "def hover_slot(slot, entered):" in runtime
    assert "def _shader_for_hover(item):" in runtime
    assert "adapt_material(" in runtime
    assert "viewer.store('stored_preview'" in runtime
    assert "viewer.fetch('stored_preview'" in runtime
    assert "HOVER READY - stored preview restored" in runtime
    assert "production source unchanged" in runtime
    assert "def _card_hit_area(" in text
    assert 'containerCOMP, name' in text
    assert '("clickthrough", False)' in text
    assert '"material_hit_%d" % slot' in text
    assert 'material_hit_click_%d' in text
    assert 'panel_value="lselect"' in text
    assert "hit.par.display = True" in runtime
    assert "hit.par.display = False" in runtime


def test_ui_actions_have_panel_execute_callbacks_and_local_preview_surface():
    text = source()
    assert "panelexecuteDAT" in text
    assert 'existing.type != "panelexec"' in text
    assert 'def _execute(parent, name, source, callback, panel_value="state"):' in text
    assert "node.par.panelvalue = panel_value" in text
    assert "node.par.offtoon = True" in text
    assert "node.par.valuechange = False" in text
    assert "material_card_click_%d" in text
    assert 'opviewerCOMP, "browser_ui"' in text
    assert 'opviewerTOP, "ui_preview"' in text
    assert '_set_if_present(ui_preview, "allowpanel", False)' in text
    assert '"resolutionw", 1280' in text
    assert '"resolutionh", 800' in text


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            suite.addTest(unittest.FunctionTestCase(value, description=name))
    return suite
