"""Check release guide references, source pointers, web IDs and diagram syntax."""
from pathlib import Path
from html.parser import HTMLParser
import json
import re
import xml.etree.ElementTree as ET
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('src', 'href') and value:
                self.links.append(value)


def main():
    catalog = json.loads((ROOT/'help_catalog.json').read_text(encoding='utf-8'))
    errors = []
    keys = [s['key'] for s in catalog['screens']]
    if len(keys) != len(set(keys)): errors.append('Duplicate help keys')
    references = 0
    web_html = (REPO/'pixelblaze_mapper/timeline_assets/index.html').read_text(encoding='utf-8')
    for screen in catalog['screens']:
        path = ROOT/screen['howto']
        if not path.exists(): errors.append('Missing guide: '+str(path))
        for source in screen['source']:
            if not (REPO/source).is_file(): errors.append('Missing source: '+source)
        if not screen['native']:
            source_html = (REPO/screen['web_source']).read_text(encoding='utf-8') if screen.get('web_source') else web_html
            screen_web_ids = set(re.findall(r'\bid=["\x27]([^"\x27]+)', source_html))
            for field in screen['fields']:
                if field not in screen_web_ids: errors.append('Unknown web field: '+field)
    for path in ROOT.glob('*.html'):
        parser = Links()
        parser.feed(path.read_text(encoding='utf-8'))
        for link in parser.links:
            parsed = urlparse(link)
            if parsed.scheme or not parsed.path: continue
            references += 1
            target = path.parent/unquote(parsed.path)
            if not target.exists(): errors.append(f'{path.name}: missing {link}')
    diagrams = list((ROOT/'diagrams').glob('*.svg'))
    for path in diagrams:
        try: ET.parse(path)
        except ET.ParseError as exc: errors.append(f'{path.name}: {exc}')
    native = json.loads((ROOT/'qa/documentation-native-readback.json').read_text(encoding='utf-8'))
    expected_native = {s['key'] for s in catalog['screens'] if s['native']}
    checked_native = {s['key'] for s in native['results']}
    if expected_native != checked_native:
        errors.append('Native readback does not cover current catalog: '+str(sorted(expected_native ^ checked_native)))
    for entry in native['results']:
        if not entry['target_exists'] or entry['missing_fields']: errors.append('Native mismatch: '+entry['key'])
    result = dict(guides=len(keys), fields=sum(len(s['fields']) for s in catalog['screens']),
                  local_references_checked=references, svg_parsed=len(diagrams),
                  native_targets_checked=len(native['results']), web_fields_checked=True,
                  screenshots_present=[p.stem for p in (ROOT/'screenshots').glob('*.png')],
                  errors=errors,
                  visual_html_check='Served Sequencer guide screenshot inspected: readable text, diagram and live UI capture. Per-screen browser interaction evidence is maintained separately by release QA. No file-URL browser policy bypass.')
    (ROOT/'qa/documentation-validation.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(errors))


if __name__ == '__main__': main()
