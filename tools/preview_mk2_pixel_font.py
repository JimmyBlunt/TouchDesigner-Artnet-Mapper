"""Reproduce MK2 LCD visual acceptance sheets at native and 2x pixel resolution."""
from copy import deepcopy
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pixelblaze_mapper.maschine_mk2 import dependencies, render
dependencies()
from PIL import Image, ImageDraw, ImageFont


def scenarios():
    labels = ['Speed', 'Scale', 'Width', 'Focus X', 'Focus Y', 'Zoom', 'Intensity', 'Contrast']
    values = [1.25, .75, .5, -.125, .875, 1, .8, 1.1]
    parameters = [dict(id=str(i), abbreviation=n, name=n, value=v, min=-1, max=2)
                  for i, (n, v) in enumerate(zip(labels, values))]
    cards = [dict(label=n) for n in ['Liquid Waves', 'Plasma', 'Grüne Wellen', 'Neon Grid']*4]
    controller = dict(mode='material', screen='home', page=0, bank=0, pad_index=0,
                      material=dict(label='Liquid Waves 012'), cards=cards,
                      parameter_pages=[dict(label='TD', parameters=parameters)])
    home = dict(controller=controller)
    yield 'Material / acht Parameter', home
    browse = deepcopy(home)
    browse['controller'].update(screen='browse', browse_index=2,
        browse_items=[dict(label=n, category='Generativ / Farbe', assignment='A / Pad 03')
                      for n in ['Plasma', 'Neon Grid', 'Grüne Wellen', 'Liquid Waves', 'Particles']])
    yield 'Browse / Namen und Details', browse
    pads = deepcopy(home)
    pads['controller'].update(screen='pad_grid', pad_index=5)
    yield 'Pads / 16 Materialplätze', pads
    show = deepcopy(home)
    show['controller'].update(mode='show', show=dict(playing=True, elapsed=12.5,
        duration=40, progress=.3125, transition='crossfade', transition_duration=2,
        transition_progress=.4, focus='duration', editing=True))
    yield 'Show / Fortschritt und Clip-Einstellungen', show
    focus = deepcopy(show)
    focus['controller']['focused_parameter'] = parameters[3]
    yield 'Show / großer Parameterwert', focus
    confirm = deepcopy(home)
    confirm['controller'].update(screen='confirm_assign', confirm=dict(label='Grüne Wellen',
        options=['Confirm', 'Cancel'], choice=0))
    yield 'Bestätigung / Auswahl', confirm


def main():
    out = ROOT/'docs'/'mk2-v0.2.2'
    out.mkdir(exist_ok=True)
    cases = list(scenarios())
    canvas = Image.new('RGB', (1080, 64+185*len(cases)), '#ededed')
    d = ImageDraw.Draw(canvas)
    try:
        label = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 19)
    except OSError:
        label = ImageFont.load_default(size=19)
    d.text((20, 15), 'MK2 Pixelschrift | 5 x 7 Pixel | Ansichten 2-fach ohne Glättung', font=label, fill='#222222')
    for i, (name, snapshot) in enumerate(cases):
        y = 64+185*i
        d.text((20, y), name, font=label, fill='#222222')
        for side, frame in enumerate(render(snapshot)):
            frame.save(out/('screen-%d-%d.png' % (i, side)))
            canvas.paste(frame.convert('RGB').resize((512, 128), Image.Resampling.NEAREST), (20+528*side, y+30))
    canvas.save(out/'pixelschrift.png')
    print(out/'pixelschrift.png')


if __name__ == '__main__':
    main()
