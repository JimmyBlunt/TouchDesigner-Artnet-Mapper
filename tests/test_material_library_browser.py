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


def test_pagination_uses_repeatable_button_output_edges():
    text = source()
    runtime = module()._runtime_source()
    assert 'navigation, "layer", 120' in text
    assert "def _button_chop_execute(" in text
    assert "return _execute(parent, name, source, callback, panel_value='lselect')" in text
    assert 'node.par.offtoon = True' in text
    assert '_button_chop_execute(owner, "previous_page_click", previous, "change_page(-1)")' in text
    assert '_button_chop_execute(owner, "next_page_click", next_button, "change_page(1)")' in text
    assert "_RUNTIME_PAGE_KEY = 'material_browser_runtime_page'" in runtime
    assert "runtime_page = OWNER.fetch(_RUNTIME_PAGE_KEY, None)" in runtime
    assert "OWNER.store(_RUNTIME_PAGE_KEY, int(value))" in runtime
    assert "def refresh(reset_page=True):" in runtime
    assert "if reset_page:\n            _set_state('page', 0)" in runtime
    assert "refresh(reset_page=False)" in runtime
    assert "from pixelblaze_mapper.material_library_paging import clamped_page, page_count" in runtime
    assert "previous.par.enable = page > 0" in runtime
    assert "next_button.par.enable = page < count - 1" in runtime
    assert "previous.par.opacity = 1.0 if page > 0 else 0.35" in runtime
    assert "next_button.par.opacity = 1.0 if page < count - 1 else 0.35" in runtime


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
    assert 'glslmultiTOP, "live_preview"' in text


def test_hover_preview_cannot_replace_the_published_imported_material():
    text = source()
    runtime = module()._runtime_source()
    assert "shader = OWNER.op('hover_shader')" in runtime
    assert "shader.text = source" in runtime
    assert "preview = OWNER.op('hover_preview')" in runtime
    assert "info = OWNER.op('hover_preview_info')" in runtime
    assert "OWNER.op('preview_shader').text = source" not in runtime.split("def _compile_hover_item(item):", 1)[1].split("def hover_slot", 1)[0]
    assert '_get_or_create(owner, glslmultiTOP, "hover_preview")' in text
    assert 'hover_preview.outputConnectors[0].connect(imported_output)' not in text
    assert "_configure_parameter_uniforms(preview, adaptation, values, publish_schema=False)" in runtime
    assert "OWNER.store('hover_compiled_id', material_id)" in runtime


def test_native_material_state_and_uniform_contract_is_persistent_and_dynamic():
    text = source()
    runtime = module()._runtime_source()
    assert '"material_parameter_state"' in text
    assert '"material_parameter_schema"' in text
    assert "def parameter_snapshot():" in runtime
    assert "def set_material_parameter(name, component, value):" in runtime
    assert "def pulse_material_parameter(name):" in runtime
    assert "preview.par.vec.sequence.numBlocks = 3 + len(adaptation.schema)" in runtime
    assert "getattr(preview.par, 'vec%dname' % block).val" in runtime
    assert "if parameter.compile_time" in runtime
    assert "write_prepared_shader(adaptation" in runtime
    assert 'live_preview.par.const.sequence.numBlocks = 1' in text
    assert 'live_preview.par.const0name.val = ""' in text
    assert 'live_preview.par.vec.sequence.numBlocks = 3' in text
    assert "material_state_runtime').module.phase()" in text
    assert 'live_preview.par.vec0name.val = "uTDMaterial0"' in text
    assert 'live_preview.par.vec0valuex.expr = (' in text
    assert '"op(\'/project1/material_state_runtime\').module.phase() if "' in text
    assert 'live_preview.par.vec0valuey.expr = "op(\'/project1/madmapper_player_controls\').par.Scale"' in text
    assert 'live_preview.par.vec0valuez.expr = "op(\'/project1/madmapper_player_controls\').par.Width"' in text
    assert 'live_preview.par.vec0valuew.expr = "op(\'/project1/madmapper_player_controls\').par.Framezoom"' in text
    assert 'live_preview.par.vec1name.val = "uTDMaterial1"' in text
    assert 'live_preview.par.vec2name.val = "uTDCoordinate"' in text
    assert 'live_preview.par.vec1name = "uTDMaterial1"' not in text
    assert '"Coordinatemode", "Coordinate Mode"' in text
    assert 'infoDAT, "live_preview_info"' in text
    assert 'textTOP, "compile_error_preview"' in text
    assert 'outTOP, "imported_material_out"' in text
    assert "preview.cook(force=True)" in runtime
    assert "preview.errors()" in runtime
    assert "LIVE PREVIEW FAILED" in runtime
    assert "prepared_shader_is_current(source)" in runtime
    assert "write_prepared_shader(adaptation, package / 'prepared.frag')" in runtime
    assert "_restore_parameter_store()" in runtime
    assert "if not _restore_catalog_cache():\n        refresh(reset_page=False)" in runtime
    assert runtime.rstrip().endswith("_restore_active_label()")


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
            self.storage = {}

        def fetch(self, key, default=None):
            return self.storage.get(key, default)

        def store(self, key, value):
            self.storage[key] = value

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


def test_hover_is_animated_bound_cached_and_restores_both_viewers():
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
    hover_body = runtime.split("def hover_slot(slot, entered):", 1)[1].split("def open_live_preview():", 1)[0]
    compile_body = runtime.split("def _compile_hover_item(item):", 1)[1].split("def _restore_active_hover():", 1)[0]
    assert "_compile_hover_item(item)" in hover_body
    assert "_restore_active_hover()" in hover_body
    assert "viewer.par.opviewer = preview.path" in hover_body
    assert "detail.par.opviewer = preview.path" in hover_body
    assert hover_body.index("preview = _compile_hover_item(item)") < hover_body.index("viewer.par.opviewer = preview.path")
    assert "_parameter_context(item)" in compile_body
    assert "_hover_context_cache" in compile_body
    assert "material_id in PARAMETER_STORE.material_ids" in compile_body
    assert "source_stat.st_mtime_ns" in compile_body
    assert "cached[2] == source_stamp" in compile_body
    assert "publish_schema=False" in compile_body
    assert "OWNER.store('hover_compiled_id', material_id)" in compile_body
    assert "def _restore_active_hover():" in runtime
    assert "card.par.opviewer = stored" in runtime
    assert "detail.par.opviewer = target.path" in runtime
    assert "project was saved mid-hover" in runtime
    assert '"hover_detail_restore"' in text
    assert "parent().fetch('hover_started_at', absTime.seconds)" in text
    assert "parent().par.Hoverloopseconds" in text
    stored_body = runtime.split("def preview_selected():", 1)[1].split("def _result_path", 1)[0]
    live_body = runtime.split("def open_live_preview():", 1)[1].split("def import_selected", 1)[0]
    assert "viewer.par.opviewer = image.path" in stored_body
    assert "viewer.par.opviewer = preview.path" in live_body
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
