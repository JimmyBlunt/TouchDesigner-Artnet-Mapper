"""Read-only release help asset allowlist for the local timeline HTTP bridge."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1] / 'docs/release-v1.0.0'
MIME = {'.html':'text/html; charset=utf-8', '.css':'text/css; charset=utf-8',
        '.svg':'image/svg+xml', '.png':'image/png', '.jpg':'image/jpeg', '.gif':'image/gif',
        '.json':'application/json; charset=utf-8'}


def approved_help_asset(path, root=ROOT):
    if not path.startswith('/release-help/'):
        return None
    relative = path[len('/release-help/'):]
    if relative == 'catalog.json': relative = 'help_catalog.json'
    # Deny traversal and URL-encoded surprises instead of attempting normalization.
    if any(part in relative for part in ('..', '%', '\\', ':')):
        return None
    candidate = (root/relative).resolve()
    if not candidate.is_relative_to(root.resolve()) or not candidate.is_file():
        return None
    if candidate.suffix.lower() not in MIME:
        return None
    # JSON is deliberately limited to the public help catalog, never runtime data.
    if candidate.suffix == '.json' and relative != 'help_catalog.json':
        return None
    return candidate, MIME[candidate.suffix.lower()]


def apply_web_theme(key):
    """Write selected tokens into the release-only CSS asset, preserving base CSS."""
    from .release_ui_theme import select_theme
    theme = select_theme(key)
    css = Path(__file__).with_name('timeline_assets')/'release.css'
    source = css.read_text(encoding='utf-8')
    start = source.index(':root{'); end = source.index('}', start)+1
    def hexcolor(rgb): return '#' + ''.join(f'{round(c*255):02x}' for c in rgb)
    tokens = {'bg':'background','panel':'surface','line':'border','ink':'ink','heading':'heading','value':'value','button-ink':'button','muted':'muted','accent':'accent'}
    block = ':root{' + ''.join('--'+k+':'+hexcolor(theme[v])+';' for k,v in tokens.items())
    block += "font-family:'"+theme['font']+"',sans-serif;font-size:12px}"
    css.write_text(source[:start]+block+source[end:],encoding='utf-8')
    return str(css)
