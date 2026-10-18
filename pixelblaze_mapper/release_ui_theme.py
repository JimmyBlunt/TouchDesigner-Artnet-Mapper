"""Version 1 native presentation tokens; no output or application state changes."""
from __future__ import annotations
import os
from pathlib import Path

THEME = {
    'name': 'Router / Blue Violet', 'font': 'Segoe UI', 'mono': 'Consolas',
    'background': (0.0314, 0.0353, 0.0588), 'surface': (0.0824, 0.0863, 0.1373),
    'border': (0.1608, 0.1647, 0.2510), 'accent': (0.4863, 0.6667, 1.0),
    'violet': (0.7412, 0.5725, 1.0),
    'ink': (0.9333, 0.9333, 0.9725), 'muted': (0.6314, 0.6471, 0.7412),
    'warning': (1.0, 0.796, 0.463), 'danger': (1.0, 0.439, 0.439),
}
STORAGE_KEY = 'release_v1_original_style'
VARIANTS = {
    '01': ('Router / Blue Violet', 'Segoe UI', '#08090f', '#151623', '#292a40', '#7caaff', '#eeeef8', '#a1a5bd'),
    '02': ('Graphite / Lime', 'Bahnschrift', '#171a18', '#232a25', '#354139', '#b3e779', '#f0f5ed', '#adbba8'),
    '03': ('Cyan / Graphite', 'Bahnschrift', '#101820', '#232a25', '#354139', '#55d6e7', '#e1e5e6', '#a9b2b5'),
    '04': ('Obsidian / Amber', 'Consolas', '#191714', '#29241d', '#40382c', '#ffcb76', '#faf0df', '#c6b49a'),
    '05': ('Midnight / Coral', 'Verdana', '#101b25', '#192a36', '#2b4050', '#ffab96', '#eef5fa', '#a7bfce'),
}


def select_theme(key):
    """Select tokens before installation; changes no TD operators itself."""
    values = VARIANTS[str(key).zfill(2)]
    THEME.update(name=values[0], font=values[1])
    for name, value in zip(('background','surface','border','accent','ink','muted'), values[2:]):
        THEME[name] = tuple(int(value[i:i+2],16)/255 for i in (1,3,5))
    THEME['heading'] = THEME['ink']
    THEME['value'] = THEME['accent']
    THEME['button'] = tuple(c/255 for c in (174,183,186)) if str(key).zfill(2)=='03' else THEME['ink']
    fontfile = Path(os.environ.get('WINDIR', 'C:/Windows'))/'Fonts'/'bahnschrift.ttf'
    THEME['fontfile'] = str(fontfile).replace('\\','/') if THEME['font']=='Bahnschrift' and fontfile.is_file() else ''
    return dict(THEME)


def compact_size(size, name=''):
    """Keep small controls readable; reduce oversized headings and labels only."""
    value = float(size or 12)
    if 'title' in name.lower() or value >= 20:
        return min(20, max(16, value - 2))
    return min(13, max(10, value - 1 if value > 12 else value))


def is_neutral(rgb):
    return max(rgb) - min(rgb) < 0.10


def remember_set(node, name, value):
    """Keep a serializable, one-time rollback snapshot before changing style."""
    par = getattr(node.par, name, None)
    if par is None:
        return False
    original = dict(node.fetch(STORAGE_KEY, {}, search=False))
    touched = list(node.fetch('release_v1_touched_style', [], search=False))
    if name not in touched:
        touched.append(name)
        node.store('release_v1_touched_style', touched)
    if name not in original:
        evaluated = par.eval()
        original[name] = {'value': getattr(evaluated,'path',evaluated), 'expr': str(par.expr),
                          'mode': str(par.mode).rsplit('.', 1)[-1]}
        node.store(STORAGE_KEY, original)
    par.val = value
    return True


def _color(node, prefix, rgb):
    for channel, value in zip('rgb', rgb):
        remember_set(node, prefix + channel, value)


def style_button_skin(button):
    """Theme TD's stock skin without replacing captions or semantic fill logic."""
    if not hasattr(button, 'op'):
        return
    text = button.op('text')
    if text is None:
        return
    for channel, value in zip('rgb', THEME['button']):
        par = getattr(text.par, 'fontcolor'+channel, None)
        if par is not None and ('parent().par.value0' in str(par.expr) or text.fetch('release_v1_stock_ink', False, search=False)):
            remember_set(text, 'fontcolor'+channel, value)
            text.store('release_v1_stock_ink', True)
    colors = [getattr(button.par, 'color'+c, None) for c in 'rgb']
    if not all(p is not None for p in colors) or not is_neutral(tuple(float(p.eval()) for p in colors)):
        return
    for channel, value in zip('rgb', THEME['surface']):
        name = 'bgcolor'+channel
        par = getattr(text.par, name, None)
        if par is not None and ('[c/.5 for c in' in str(par.expr) or text.fetch('release_v1_stock_fill', False, search=False)):
            remember_set(text, name, par.eval())
            par.expr = '%s + .045 * parent().panel.rollover + .07 * parent().par.value0' % value
            text.store('release_v1_stock_fill', True)


def style_field_skin(field):
    """The stock FieldCOMP draws through an internal TextTOP/color table."""
    if not hasattr(field, 'op'):
        return
    text = field.op('text')
    if text is None:
        return
    for prefix, color in (('fontcolor',THEME['value']),('bgcolor',THEME['surface'])):
        for channel,value in zip('rgb',color):
            name=prefix+channel
            par=getattr(text.par,name,None)
            if par is not None and ("op('color')" in str(par.expr) or text.fetch('release_v1_field_skin',False,search=False)):
                remember_set(text,name,par.eval())
                par.expr=str(value)+(" + .035 * op('i')['focus']" if prefix=='bgcolor' else '')
    text.store('release_v1_field_skin',True)


def ink_role(node):
    """Separate captions from editable values without changing their content."""
    if node.type=='button': return 'button'
    if node.type=='field': return 'value'
    if hasattr(node,'parent'):
        owner=node.parent()
        if owner.type=='button': return 'button'
        if owner.type=='field': return 'value'
    name=node.name.lower()
    if any(word in name for word in ('title','label','_lbl_','head','caption','hint','note','description')):
        return 'heading'
    par=getattr(node.par,'text',None)
    if par is not None and par.expr: return 'value'
    if name in ('ws','apa','unassigned') or any(word in name for word in ('value','status','count','current','result','summary','route','fps','time','live','_cue_','_info')):
        return 'value'
    return 'heading'


def style_node(node):
    """Only change presentation. In particular no text, geometry or value fields."""
    if str(getattr(node, 'type', '')) not in ('text', 'button', 'field', 'container'):
        return False
    if node.type == 'button':
        style_button_skin(node)
    if node.type == 'field':
        style_field_skin(node)
    remember_set(node, 'font', THEME['font'])
    remember_set(node, 'fontfile', THEME.get('fontfile', ''))
    size = getattr(node.par, 'fontsize', None)
    if size is not None:
        original = node.fetch(STORAGE_KEY, {},search=False).get('fontsize', {}).get('value', size.eval())
        remember_set(node, 'fontsize', compact_size(original, node.name))
    # Status and dynamic colors have meaning. Theme only neutral constant fills.
    pars = [getattr(node.par, 'bgcolor' + c, None) for c in 'rgb']
    if all(p is not None for p in pars):
        constant = all(str(p.mode).lower().endswith('constant') for p in pars)
        if constant and is_neutral(tuple(float(p.eval()) for p in pars)):
            _color(node, 'bgcolor', THEME['background'] if node.type == 'container' else THEME['surface'])
    # Presentation ink uses distinct roles. Preserve red, green,
    # amber and any dynamic expression because those carry runtime status.
    for prefix in ('fontcolor', 'textcolor'):
        ink = [getattr(node.par, prefix+c, None) for c in 'rgb']
        if all(p is not None for p in ink):
            if all(str(p.mode).lower().endswith('constant') for p in ink):
                rgb = tuple(float(p.eval()) for p in ink)
                previous = node.fetch('release_v1_ink_'+prefix, None,search=False)
                selected_before = all(abs(a-b)<.0001 for a,b in zip(rgb,(133/255,228/255,237/255)))
                presentation_blue = rgb[2]>.5 and rgb[1]>.5 and rgb[0]<.6 and rgb[2]>=rgb[1]*.9
                if previous == rgb or selected_before or presentation_blue or (max(rgb)-min(rgb) < .25 and max(rgb) > .35):
                    _color(node, prefix, THEME[ink_role(node)])
                    node.store('release_v1_ink_'+prefix, tuple(getattr(node.par,prefix+c).eval() for c in 'rgb'))
    return True


def restore_node(node):
    saved = node.fetch(STORAGE_KEY, {},search=False)
    touched = node.fetch('release_v1_touched_style', [], search=False)
    for name, state in saved.items():
        if name not in touched:
            continue
        par = getattr(node.par, name, None)
        if par is None:
            continue
        par.val = state['value']
        if state['mode'].lower() == 'expression':
            par.expr = state['expr']
        else:
            mode = getattr(par.mode.__class__, state['mode'].upper(), None)
            if mode is not None:
                par.mode = mode
    return len(saved)


# The user-selected release palette; baked native parameters and CSS persist it.
select_theme('03')
