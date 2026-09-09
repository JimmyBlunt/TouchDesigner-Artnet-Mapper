import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pixelblaze_mapper import router_dynamic_ui as ui


class Field:
    def __init__(self, value): self.value = value
    def __getitem__(self, key): return self.value


class Owner:
    def __init__(self, rows, name):
        self.storage = {'router_card_name': name, 'router_card_drafts': {},
                        'router_card_baselines': {r['name']: dict(r) for r in rows}}
        row = next(r for r in rows if r['name'] == name)
        self.fields = {k: Field(row[k]) for k in ui.FIELDS}
    def fetch(self, key, default=None): return self.storage.get(key, default)
    def store(self, key, value): self.storage[key] = value
    def op(self, path): return self.fields[path.split('/')[1][len('router_'):]]


def controller(name='BACK_PANEL_249', enabled='1'):
    return dict(name=name, target_ip='10.0.0.249', start_universe='120', brightness='0.9',
                enabled=enabled, rate='30', reserved_universes='2')


class RouterDynamicTests(unittest.TestCase):
    def test_panel_type_explicit_bridge_globals(self):
        kind = object()
        self.assertIs(ui._panel_execute_type({'panelexecuteDAT': kind}), kind)

    def test_panel_type_callback_globals_falls_back_to_td(self):
        kind = object()
        with patch.dict('sys.modules', {'td': SimpleNamespace(panelexecuteDAT=kind)}):
            self.assertIs(ui._panel_execute_type({}), kind)

    def test_hide_legacy_prefix_skips_callback_dat_without_display(self):
        callback = SimpleNamespace(name='ws_callbacks', par=SimpleNamespace(active=True))
        ui._set_parameter_if_present(callback, 'display', False)
        self.assertFalse(hasattr(callback.par, 'display'))
        self.assertTrue(callback.par.active)
        component = SimpleNamespace(par=SimpleNamespace(display=True))
        ui._set_parameter_if_present(component, 'display', False)
        self.assertFalse(component.par.display)

    def test_wire_zero_and_decimal_comma(self):
        row = controller(); row.update(start_universe='0', brightness='0,3')
        parsed = ui.validated_fields(row)
        self.assertEqual(parsed['brightness'], '0.3')
        self.assertEqual(parsed['start_universe'], '0')

    def test_invalid_values(self):
        for key, value in [('target_ip', 'broken'), ('start_universe', '-1'),
                           ('start_universe', '32768'), ('brightness', 'nan'),
                           ('enabled', '2'), ('rate', '0'), ('rate', '121')]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                ui.validated_fields(dict(controller(), **{key: value}))

    def test_third_controller_edits_and_preserves_other_rows(self):
        a, b, c = controller('WS'), controller('APA', '0'), controller()
        entries = [a, b, c]; header = list(c)
        rows = [header] + [[r[k] for k in header] for r in entries]
        owner = Owner(entries, c['name']); owner.fields['brightness'].value = '0,2'
        changed = ui.apply_drafts(owner, rows)
        self.assertEqual(changed[:3], rows[:3])
        self.assertEqual(changed[3][header.index('brightness')], '0.2')
        self.assertEqual(rows[3][header.index('brightness')], '0.9')

    def test_external_reconfiguration_rejects_stale_draft(self):
        c = controller(); owner = Owner([c], c['name']); owner.fields['brightness'].value = '0.2'
        header = list(c); updated = dict(c, target_ip='10.0.0.250')
        with self.assertRaisesRegex(ValueError, 'externally'):
            ui.apply_drafts(owner, [header, [updated[k] for k in header]])

    def test_unchanged_draft_does_not_overwrite_external_change(self):
        c = controller(); owner = Owner([c], c['name']); header = list(c)
        updated = dict(c, brightness='0.1')
        rows = [header, [updated[k] for k in header]]
        self.assertEqual(ui.apply_drafts(owner, rows), rows)

    def test_removed_controller_draft_rejected(self):
        c = controller(); owner = Owner([c], c['name']); owner.fields['rate'].value = '40'
        with self.assertRaisesRegex(ValueError, 'externally'):
            ui.apply_drafts(owner, [list(c)])

    def test_mapping_disabled_overlap_and_explicit_black(self):
        rows = [controller('ON'), controller('OFF', '0')]
        segments = [dict(controller='ON', source_start='0', count='4'),
                    dict(controller='OFF', source_start='2', count='4')]
        result = ui.mapping_counts(rows, segments, 10, [(8, 9)])
        self.assertEqual(result, dict(enabled=4, disabled_only=2, unassigned=2, inactive=2))

    def test_unknown_controller_is_unassigned(self):
        segments = [dict(controller='missing', source_start='0', count='2')]
        self.assertEqual(ui.mapping_counts([], segments, 2)['unassigned'], 2)

    def test_drafts_for_multiple_pages_apply_together(self):
        a, b = controller('one'), controller('two'); owner = Owner([a,b], 'two')
        owner.storage['router_card_drafts'] = {'one': {k: a[k] for k in ui.FIELDS}}
        owner.storage['router_card_drafts']['one']['rate'] = '60'
        owner.fields['brightness'].value = '.5'
        header = list(a); rows = [header] + [[r[k] for k in header] for r in (a,b)]
        result = ui.apply_drafts(owner, rows)
        self.assertEqual(result[1][header.index('rate')], '60')
        self.assertEqual(result[2][header.index('brightness')], '0.5')


if __name__ == '__main__': unittest.main()
