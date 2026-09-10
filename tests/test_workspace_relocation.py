"""Read-only relocation validates content/identity before returning a new snapshot."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pixelblaze_mapper.workspace_relocation import prepare_relocation, RelocationError


class WorkspaceRelocationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.old, self.new = Path(self.temp.name) / 'old', Path(self.temp.name) / 'new'
        self.old.mkdir()
        self.new.mkdir()
        self.content = b'index,u,v\n2,0.1,0.2\n5,0.4,0.5\n'
        for root in (self.old, self.new):
            (root / 'Scans' / 'capture-a').mkdir(parents=True)
            (root / 'Scans' / 'capture-a' / 'view.csv').write_bytes(self.content)
        self.source = self.old / 'Scans' / 'capture-a' / 'view.csv'
        self.target = self.new / 'Scans' / 'capture-a' / 'view.csv'

    def migrate(self, value, **kwargs):
        return prepare_relocation(value, self.old, self.new, **kwargs)

    def test_nested_runtime_fields_move_without_mutating_input(self):
        data = {'fields': {'workspace': str(self.old / 'Scans'), 'views': str(self.source)},
                'storage': {'capture_status': {'view_csv': str(self.source)},
                            'numbers': [None, True, 5, .2]}, 'tuple': (str(self.source),)}
        before = deepcopy(data)
        report = self.migrate(data)
        self.assertEqual(data, before)
        self.assertEqual(report['value']['fields']['workspace'], (self.new / 'Scans').as_posix())
        self.assertEqual(report['value']['fields']['views'], self.target.as_posix())
        self.assertEqual(report['value']['tuple'], (self.target.as_posix(),))
        self.assertEqual(len(report['changes']), 4)
        self.assertEqual(len(report['validated']), 2)
        file_report = next(row for row in report['validated'] if row['kind'] == 'file')
        self.assertEqual(file_report['sha256'], sha256(self.content).hexdigest())
        self.assertEqual(file_report['bytes'], len(self.content))

    def test_view_list_preserves_separators_and_supports_backslashes(self):
        value = '  ' + str(self.source).replace('/', '\\') + ' | None | ' + self.source.as_posix() + '  | '
        report = self.migrate(value)
        self.assertEqual(report['value'], '  ' + self.target.as_posix() + ' | None | ' + self.target.as_posix() + '  | ')
        self.assertEqual(len(report['validated']), 1)

    def test_windows_root_matching_is_case_insensitive(self):
        if not self.old.drive:
            self.skipTest('Windows drive-letter behavior')
        report = self.migrate(str(self.source).swapcase())
        self.assertEqual(report['value'].casefold(), self.target.as_posix().casefold())

    def test_missing_root_has_consistent_preflight_error(self):
        with self.assertRaises(RelocationError):
            prepare_relocation({}, self.old, self.new / 'absent')

    def test_boundary_matches_not_siblings_or_arbitrary_prose(self):
        values = [str(self.old) + '-backup/Scans/view.csv',
                  'Error opening ' + str(self.source), 'Status | ' + str(self.source),
                  'https://example.test/' + self.source.as_posix(),
                  json.dumps({'file': str(self.source)})]
        report = self.migrate(values)
        self.assertEqual(report['value'], values)
        self.assertEqual(report['changes'], [])

    def test_default_provenance_is_kept_while_runtime_file_moves(self):
        evidence = str(self.source) + '#sha256=' + sha256(self.content).hexdigest()
        report = self.migrate({'session': {'views': [{'observation_reference': evidence}]},
                               'capture_status': {'view_csv': str(self.source)}})
        self.assertEqual(report['value']['session']['views'][0]['observation_reference'], evidence)
        self.assertEqual(report['preserved'], ['/session/views/0/observation_reference'])
        self.assertEqual(report['value']['capture_status']['view_csv'], self.target.as_posix())

    def test_explicit_provenance_relocation_preserves_and_verifies_hash(self):
        digest = sha256(self.content).hexdigest()
        report = self.migrate({'observation_reference': str(self.source) + '#sha256=' + digest}, preserve_keys=())
        self.assertEqual(report['value']['observation_reference'], self.target.as_posix() + '#sha256=' + digest)
        with self.assertRaisesRegex(RelocationError, 'hash does not match'):
            self.migrate(str(self.source) + '#sha256=' + '0' * 64)

    def test_copied_file_mismatch_rejects_whole_snapshot(self):
        self.target.write_bytes(self.content.replace(b'0.1', b'0.9'))
        data = {'workspace': str(self.old / 'Scans'), 'view': str(self.source)}
        before = deepcopy(data)
        with self.assertRaisesRegex(RelocationError, 'bytes differ'):
            self.migrate(data)
        self.assertEqual(data, before)
        self.assertEqual(self.source.read_bytes(), self.content)

    def test_missing_destination_rejects_instead_of_inventing_path(self):
        self.target.unlink()
        with self.assertRaises(RelocationError):
            self.migrate(str(self.source))
        self.assertFalse(self.target.exists())

    def test_existing_directory_required_and_type_must_match(self):
        (self.old / 'only-old').mkdir()
        with self.assertRaises(RelocationError):
            self.migrate(str(self.old / 'only-old'))
        (self.new / 'only-old').write_text('not a folder')
        with self.assertRaisesRegex(RelocationError, 'type differs'):
            self.migrate(str(self.old / 'only-old'))

    def test_traversal_and_alternate_streams_are_rejected(self):
        for suffix in ('/Scans/../Scans/capture-a/view.csv', '/Scans/capture-a/view.csv:other'):
            with self.subTest(suffix=suffix), self.assertRaisesRegex(RelocationError, 'Ambiguous'):
                self.migrate(self.old.as_posix() + suffix)

    def test_relocation_is_idempotent_and_does_not_rewrite_manifests(self):
        manifest = json.dumps({'workspace': self.old.as_posix(), 'view': self.source.as_posix()}).encode()
        for root in (self.old, self.new):
            (root / 'Scans' / 'capture-a' / 'capture.json').write_bytes(manifest)
        before_files = {path: path.read_bytes() for root in (self.old, self.new) for path in root.rglob('*') if path.is_file()}
        first = self.migrate({'manifest': str(self.source.parent / 'capture.json'), 'views': str(self.source)})
        second = self.migrate(first['value'])
        self.assertEqual(second['changes'], [])
        self.assertEqual(second['value'], first['value'])
        self.assertEqual({path: path.read_bytes() for path in before_files}, before_files)

    def test_non_json_or_nonfinite_values_rejected(self):
        for value in ({'x': float('nan')}, {'x': object()}, {3: 'nonstring key'}):
            with self.subTest(value=value), self.assertRaises(RelocationError):
                self.migrate(value)

    def test_protected_nested_values_are_not_shared(self):
        original = {'quality_reference': {'history': [str(self.source)]}}
        report = self.migrate(original)
        report['value']['quality_reference']['history'].append('new')
        self.assertEqual(original['quality_reference']['history'], [str(self.source)])

    def test_link_outside_destination_root_rejected(self):
        outside = Path(self.temp.name) / 'external.csv'
        outside.write_bytes(self.content)
        link = self.new / 'Scans' / 'outside.csv'
        (self.old / 'Scans' / 'outside.csv').write_bytes(self.content)
        try:
            link.symlink_to(outside)
        except OSError:
            self.skipTest('Symlink creation is unavailable on this Windows host')
        with self.assertRaisesRegex(RelocationError, 'leaves its relocation root'):
            self.migrate(str(self.old / 'Scans' / 'outside.csv'))

    def test_resolved_destination_escape_fails_even_without_symlink_privileges(self):
        outside = Path(self.temp.name) / 'external.csv'
        outside.write_bytes(self.content)
        original = Path.resolve
        def resolve(path, *args, **kwargs):
            return outside if path == self.target else original(path, *args, **kwargs)
        with patch.object(Path, 'resolve', autospec=True, side_effect=resolve):
            with self.assertRaisesRegex(RelocationError, 'leaves its relocation root'):
                self.migrate(str(self.source))


if __name__ == '__main__':
    unittest.main()
