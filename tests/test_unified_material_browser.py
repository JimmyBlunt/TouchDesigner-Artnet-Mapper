"""Contracts for the combined Core + imported MadMapper browser."""

import ast
import importlib.util
import unittest
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


def test_search_group_source_paging_and_both_layouts_exist():
    runtime = module()._runtime_source()
    for name in ("apply_filters", "cycle_source", "toggle_group", "select_group_slot", "toggle_layout", "change_page", "render"):
        assert "def %s(" % name in runtime
    assert "32 if compact else 8" in runtime
    assert "for slot in range(32):" in runtime
    assert '"unified_search"' in source()
    assert '"unified_group_dropdown"' in source()
    assert 'opviewerTOP, "ui_preview"' in source()


def test_selection_preserves_existing_indices_and_appends_imported_source():
    text = source()
    runtime = module()._runtime_source()
    assert "controls.par.Source = 'materials'" in runtime
    assert "controls.par.Source = 'imported'" in runtime
    assert "module.open_live_preview()" in runtime
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


def test_dynamic_native_parameter_drawer_supports_types_groups_and_paging():
    text = source()
    runtime = module()._runtime_source()
    assert "def _native_parameter_controls(browser):" in text
    assert "range(6)" in text
    assert "parameterexecuteDAT" in text
    assert 'node.par.pars = "value0"' in text
    assert "def render_native_parameters():" in runtime
    assert "'point2d': ('X', 'Y')" in runtime
    assert "'floatrange': ('MIN', 'MAX')" in runtime
    assert "'color': ('R', 'G', 'B', 'A')" in runtime
    assert "kind in ('bool', 'event', 'long')" in runtime
    assert "compile_note = ' | RECOMPILE'" in runtime
    assert "toggle_native_parameters(True)" in runtime
    assert "toggle_native_parameters(False)" in runtime
    assert "ZURÜCK ZU MATERIALIEN" in text
    assert "def _clear_native_parameter_rows():" in runtime
    assert "def _native_error(message):" in runtime
    assert "NATIVE PARAMETERS NICHT VERFÜGBAR" in runtime
    assert "if not parameters:" in runtime
    assert "label.unstore('parameter_name')" in runtime


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            suite.addTest(unittest.FunctionTestCase(value, description=name))
    return suite
