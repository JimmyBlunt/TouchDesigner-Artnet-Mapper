"""Saved show choices, excluding automation and material sidecars."""
import json
from pathlib import Path
from .show_editor import _validated
from . import show_automation


def load_show_bundle(path):
    """Validate all three files before the caller changes any live DAT."""
    path = Path(path)
    document = _validated(json.loads(path.read_text(encoding='utf-8-sig')))
    def sidecar(suffix, default):
        try:
            return json.loads(path.with_suffix(suffix).read_text(encoding='utf-8-sig'))
        except FileNotFoundError:
            return default
    recorded = show_automation.validate(sidecar('.automation.json', show_automation.empty()))
    materials = sidecar('.materials.json', {})
    if not isinstance(materials, dict):
        raise ValueError('Material sidecar must be an object')
    return document, recorded, materials


def saved_shows(folder):
    choices = []
    for path in Path(folder).glob('*.json'):
        if path.name.endswith(('.automation.json', '.materials.json')):
            continue
        try:
            document = _validated(json.loads(path.read_text(encoding='utf-8-sig')))
        except (ValueError, TypeError, KeyError, OSError):
            continue
        choices.append(dict(path=str(path), label=str(document.get('name') or path.stem),
                            filename=path.name, cues=len(document['cues'])))
    return sorted(choices, key=lambda entry: (entry['label'].casefold(), entry['filename'].casefold()))
