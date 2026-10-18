"""Archive verified unreferenced legacy DATs; run inside TouchDesigner.

Restore: exec this file, then restore(op('/project1')). The full before-release
TOE also retains the exact original operator parameters and network layout.
"""
import json
from pathlib import Path

NAMES = ('effect_sample_uv_callbacks1', 'legacy_source_mask_callbacks1',
         'esp_artnet_live_pack_callbacks1', 'esp_artnet_test_pattern_callbacks1',
         'DMX_Universes_backup_pre_panels', 'dmxout1_routingtable_backup_pre_panels')


def archive_path():
    return Path(project.folder) / 'docs/release-v1.0.0/qa/legacy-dats-backup.json'


def restore(parent):
    restored = []
    for item in json.loads(archive_path().read_text(encoding='utf8')):
        if parent.op(item['name']) is not None:
            raise ValueError('Restore would overwrite ' + item['name'])
        node = parent.create(textDAT if item['type'] == 'text' else tableDAT, item['name'])
        if item['type'] == 'text':
            node.text = item['text']
        else:
            node.clear()
            for row in item['rows']:
                node.appendRow(row)
        node.nodeX, node.nodeY = item['position']
        assert node.text == item['text']
        restored.append(node.path)
    return restored


def clean():
    from pixelblaze_mapper.guided_scan_live import assert_outputs_off
    assert_outputs_off(op)
    root = op('/project1')
    evidence = json.loads((archive_path().parent / 'legacy-candidates.json').read_text(encoding='utf8'))
    assert {item['path'].split('/')[-1] for item in evidence} == set(NAMES)
    assert all(not item['references'] and not item['inputs'] and not item['outputs'] for item in evidence)
    data = []
    for name in NAMES:
        node = root.op(name)
        assert node is not None and node.type in ('text', 'table')
        assert not node.inputs and not node.outputs
        data.append(dict(name=name, type=node.type, text=node.text,
                         rows=[[str(cell) for cell in row] for row in node.rows()] if node.type == 'table' else [],
                         position=[node.nodeX, node.nodeY]))
    if archive_path().exists():
        assert json.loads(archive_path().read_text(encoding='utf8')) == data, 'Archive differs from current nodes'
    else:
        archive_path().write_text(json.dumps(data, indent=2), encoding='utf8')
    # Prove that the archive can reconstruct every DAT before removing originals.
    assert root.op('release_restore_check') is None
    scratch = root.create(baseCOMP, 'release_restore_check')
    try:
        restored = restore(scratch)
        assert len(restored) == len(NAMES)
    finally:
        scratch.destroy()
    for name in NAMES:
        root.op(name).destroy()
    assert_outputs_off(op)
    assert not root.errors(recurse=True), root.errors(recurse=True)
    return dict(removed=list(NAMES), restore_verified=True,
                backup=str(archive_path()), errors=root.errors(recurse=True))
