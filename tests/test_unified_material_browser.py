"""Contracts for the combined Core + imported MadMapper browser."""

import ast
import importlib.util
import json
import unittest
from types import SimpleNamespace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "pixelblaze_mapper" / "build_unified_material_browser.py"


def source():
    return BUILDER.read_text(encoding="utf-8")


def module():
    spec = importlib.util.spec_from_file_location("unified_material_browser", BUILDER)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def test_builder_and_runtime_compile():
    ast.parse(source())
    compile(module()._runtime_source(), "<unified-runtime>", "exec")


def test_combines_core_manifest_with_confirmed_import_manifests():
    runtime = module()._runtime_source()
    assert "data['effectDefinitions']" in runtime
    assert "material-import.json" in runtime
    assert "_core_items() + _imported_items()" in runtime
    assert "'imported', 'madmapper'" in runtime


def test_browser_reads_the_same_configured_folder_as_import_dialog(tmp_path=None):
    if tmp_path is None:
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as directory:
            return test_browser_reads_the_same_configured_folder_as_import_dialog(Path(directory))
    catalog = tmp_path / 'catalog.json'
    imports = tmp_path / 'actual-imports'
    imports.mkdir()
    records = []
    for material_id, name in (('glow', 'Glow Boundary'), ('kirby', 'Kirby')):
        directory = imports / material_id
        directory.mkdir()
        (directory / 'material-import.json').write_text('{}')
        (directory / 'prepared.frag').write_text('// prepared')
        records.append({'id': material_id, 'name': name})
    catalog.write_text(json.dumps({'materials': records}))
    values = {'Catalogfile': str(catalog), 'Importroot': str(imports)}
    parameters = {key: SimpleNamespace(eval=lambda key=key: values[key]) for key in values}
    runtime = ast.parse(module()._runtime_source())
    functions = ast.Module(body=[n for n in runtime.body if isinstance(n, ast.FunctionDef)
        and n.name in ('_library_paths', '_catalog_signature', '_imported_items')], type_ignores=[])
    scope = {'Path': Path, 'json': json, 'CATALOG': tmp_path/'obsolete-catalog.json',
        'IMPORT_ROOT': tmp_path/'obsolete-imports', 'MANIFEST': catalog,
        'op': lambda path: SimpleNamespace(par=parameters)}
    exec(compile(functions, '<configured-imports>', 'exec'), scope)
    items = scope['_imported_items']()
    assert {i['label'] for i in items} == {'Glow Boundary', 'Kirby'}
    assert all(Path(i['prepared_path']).is_relative_to(imports) for i in items)
    before = scope['_catalog_signature']()
    values['Importroot'] = str(tmp_path/'new-empty-folder')
    assert scope['_catalog_signature']() != before
    assert scope['_imported_items']() == []


def test_search_group_source_paging_and_both_layouts_exist():
    runtime = module()._runtime_source()
    for name in ("apply_filters", "cycle_source", "toggle_group", "select_group_slot", "toggle_layout", "change_page", "render"):
        assert "def %s(" % name in runtime
    assert "32 if compact else 8" in runtime
    assert "for slot in range(32):" in runtime
    assert '"unified_search"' in source()
    assert '"unified_group_dropdown"' in source()
    assert 'opviewerTOP, "ui_preview"' in source()


def test_runtime_reload_preserves_the_visible_page_before_card_selection():
    runtime = module()._runtime_source()
    assert "def refresh(reset_page=True):" in runtime
    assert "def apply_filters(reset_page=True):" in runtime
    assert "apply_filters(reset_page=reset_page)" in runtime
    assert "if reset_page:\n        _set_state('page', 0)" in runtime
    assert runtime.rstrip().endswith("refresh(reset_page=False)")
    assert "index = int(_state('page', 0)) * size + int(slot)" in runtime


def test_selection_preserves_existing_indices_and_appends_imported_source():
    text = source()
    runtime = module()._runtime_source()
    assert "controls.par.Source = 'materials'" in runtime
    assert "controls.par.Source = 'imported'" in runtime
    assert "module.activate_selected()" in runtime
    assert 'if "imported" not in names:' in text
    assert 'names.append("imported")' in text
    assert "imported_source.outputConnectors[0].connect(switch)" in text
    assert "switch.inputConnectors[duplicate_index].disconnect()" in text


def test_selection_activates_the_matching_per_material_state():
    runtime = module()._runtime_source()
    assert "state_runtime = op('/project1/material_state_runtime')" in runtime
    assert "state_runtime.module.activate(item['key'], item.get('preset', {}))" in runtime
    assert "'preset': dict(definition.get('preset', {}))" in runtime


def test_builder_never_enables_network_or_saves_project():
    text = source()
    assert "dmxoutCHOP" not in text
    assert "project.save(" not in text
    assert '"networkOutputEnabled": False' in text
    assert '"projectSaved": False' in text


def test_generated_duplicate_detection_keeps_canonical_controls_only():
    value = module()
    for duplicate in (
        "mb_control_speed1", "mb_control_speed1_change",
        "mb_control_focusx_change2", "unified_apply3", "unified_next_click4",
    ):
        assert value._is_generated_duplicate_name(duplicate)
    for canonical in (
        "mb_control_speed", "mb_control_speed_change", "mb_control_speed_0",
        "unified_apply", "material_card_0", "card_top_0",
    ):
        assert not value._is_generated_duplicate_name(canonical)


def test_material_handlers_are_canonical_and_builder_cleans_before_layout():
    text = source()
    assert "_remove_generated_duplicates(browser)" in text
    assert "def _momentary_execute(" in text
    assert "node.type != \"panelexec\"" in text
    assert text.index("_remove_generated_duplicates(browser)") < text.index("_material_controls(browser)", text.index("def build():"))


def test_material_sliders_watch_the_real_value0_parameter():
    text = source()
    assert "parent.create(parameterexecuteDAT, name)" in text
    assert 'node.par.pars = "value0"' in text
    assert "float(par.eval())" in text
    assert 'node.par.panelvalue = "value"' not in text


def test_material_player_shortcut_surface_has_preview_and_live_controls():
    text = source()
    assert "def _material_player_surface(controls):" in text
    assert "MATERIAL PLAYER | FINAL MATERIAL + LIVE CONTROLS" in text
    assert "controls, containerCOMP, 'ui_panel'" in text
    assert "panel.viewer = True" in text
    assert "'player_preview'" in text
    assert "op('/project1/material_gradient_player')" in text
    surface = text.index("def _material_player_surface")
    assert text.index("op('/project1/material_gradient_player')", surface) < text.index("op('/project1/visual_source_switch')", surface)
    assert text.index("op('/project1/visual_source_switch')", surface) < text.index("controls.op('material_preview')", surface)
    for parameter in ("Speed", "Scale", "Width", "Focusx", "Focusy", "Framezoom", "Intensity", "Contrast"):
        assert "'%s'" % parameter in text
    assert "ART-NET ACTUAL" in text
    assert "actual_send_fps" in text
    assert "project.cookRate" in text
    assert "if int(frame) % 15:" in text
    assert "OPEN MATERIAL BROWSER" in text
    assert "RESET VIEW" in text


def test_dynamic_native_parameter_drawer_supports_types_groups_and_overflow_paging():
    text = source()
    runtime = module()._runtime_source()
    assert "def _native_parameter_controls(browser):" in text
    assert "NATIVE_PARAMETER_SLOT_COUNT = 16" in text
    assert "range(NATIVE_PARAMETER_SLOT_COUNT)" in text
    assert "parameterexecuteDAT" in text
    assert 'node.par.pars = "value0"' in text
    assert "def render_native_parameters():" in runtime
    assert "'point2d': ('X', 'Y')" in runtime
    assert "'floatrange': ('MIN', 'MAX')" in runtime
    assert "'color': ('R', 'G', 'B', 'A')" in runtime
    assert "kind in ('bool', 'event', 'long', 'enum')" in runtime
    assert "compile_note = ' *'" in runtime
    assert "toggle_native_parameters(True)" in runtime


def test_native_parameter_drawer_uses_compact_touchdesigner_style_rows():
    text = source()
    runtime = module()._runtime_source()
    assert "20, 364, 1240, 456, 120" in text
    assert "NATIVE_PARAMETER_COLUMN_COUNT = 2" in text
    assert "NATIVE_PARAMETER_ROWS_PER_COLUMN = 8" in text
    assert "NATIVE_PARAMETER_COLUMN_COUNT = 2" in runtime
    assert "NATIVE_PARAMETER_ROWS_PER_COLUMN = 8" in runtime
    assert "column = slot % NATIVE_PARAMETER_COLUMN_COUNT" in text
    assert "row = slot // NATIVE_PARAMETER_COLUMN_COUNT" in text
    assert "cell_x = 16 + column * 604" in text
    assert "y = 374 - row * 32" in text
    assert "drawer, 'native_param_row_%d' % slot" in text
    assert "cell_x, y, 588, 26" in text
    assert "module.native_select(%d)" in text
    assert "toggle_native_parameters(False)" in runtime
    assert "ZURÜCK ZU MATERIALIEN" in text
    assert "def _clear_native_parameter_rows():" in runtime
    assert "def _native_error(message):" in runtime
    assert "NATIVE PARAMETERS NICHT VERFÜGBAR" in runtime
    assert "if not parameters:" in runtime
    assert "row.unstore('parameter_name')" in runtime


def test_native_materials_use_dense_adaptive_pages():
    runtime = module()._runtime_source()
    assert "NATIVE_PARAMETER_SLOT_COUNT = 16" in runtime
    assert "page_count = max(1, (len(parameters) + NATIVE_PARAMETER_SLOT_COUNT - 1) // NATIVE_PARAMETER_SLOT_COUNT)" in runtime
    assert "NATIVE_PAGE * NATIVE_PARAMETER_SLOT_COUNT:" in runtime
    assert "_native_control('native_params_previous').par.display = overflow" in runtime
    assert "_native_control('native_params_next').par.display = overflow" in runtime
    assert "set_parameter_page" not in runtime
    assert "NATIVE_PAGE = 0" in runtime
    assert "NATIVE_SELECTED_SLOT = 0" in runtime
    assert "def _layout_native_drawer(visible_count):" in runtime
    assert "height = 200 + row_count * 32" in runtime
    assert "drawer.par.y = 820 - height" in runtime
    assert "_layout_native_drawer(len(visible))" in runtime
    assert "'< PREVIOUS 16'" in source()
    assert "'NEXT 16 >'" in source()


def test_native_rows_share_one_lightweight_typed_editor():
    text = source()
    runtime = module()._runtime_source()
    assert "_remove_native_parameter_children(drawer)" in text
    assert "def _remove_native_parameter_children(drawer):" in text
    assert "'native_param_editor_%d' % component" in text
    assert "native_editor_value_changed(%d, float(par.eval()))" in text
    assert "native_param_editor_action" in text
    assert "def native_select(slot):" in runtime
    assert "def _render_native_editor(parameter):" in runtime
    assert "def native_editor_value_changed(component, value):" in runtime
    assert "def native_editor_action():" in runtime
    assert "component_width = int((900 - max(0, component_count - 1) * 6) / component_count)" in runtime
    assert "slider.par.w = component_width" in runtime
    assert "elif kind in ('long', 'enum'):" in runtime
    assert "component_value = values[component] if component < len(values) else 0.0" in runtime
    assert "native_param_%d_%d_change" not in text


def test_native_master_rows_show_current_values_and_selection():
    runtime = module()._runtime_source()
    assert "def _native_value_text(parameter):" in runtime
    assert "def _native_row_text(parameter):" in runtime
    assert "row.par.label = _native_row_text(parameter)" in runtime
    assert "NATIVE_PAGE_STORE_KEY = 'native_parameter_page'" in runtime
    assert "NATIVE_SLOT_STORE_KEY = 'native_parameter_selected_slot'" in runtime
    assert "OWNER.fetch(NATIVE_SLOT_STORE_KEY, NATIVE_SELECTED_SLOT)" in runtime
    assert "OWNER.store(NATIVE_SLOT_STORE_KEY, NATIVE_SELECTED_SLOT)" in runtime
    assert "target_component = -1 if int(parameter.get('components') or 1) <= 1 else int(component)" in runtime
    assert "library.set_material_parameter(name, target_component, float(value))" in runtime
    assert "row.par.bgcolorg = 0.28 if selected else 0.095" in runtime
    assert "row.par.label = _native_row_text(parameter)" in runtime


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            suite.addTest(unittest.FunctionTestCase(value, description=name))
    return suite
