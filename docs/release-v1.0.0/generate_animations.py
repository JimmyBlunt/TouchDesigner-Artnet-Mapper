"""Create explanatory animations from primitives, not simulated screen recordings.

Requires Pillow (included in the Codex bundled artifact Python runtime).
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent/'diagrams'
FONT = 'C:/Windows/Fonts/bahnschrift.ttf'
BG, PANEL, CYAN, MUTED = '#17191c', '#272c32', '#78dced', '#b3c0cc'


def font(size): return ImageFont.truetype(FONT, size)


def frame(title, subtitle):
    im = Image.new('RGB', (1080, 520), BG)
    d = ImageDraw.Draw(im)
    d.text((32, 25), title, fill=CYAN, font=font(32))
    d.text((32, 72), subtitle, fill=MUTED, font=font(20))
    d.text((32, 485), 'SCHEMATISCHE ABLAUFGRAFIK · keine Bildschirmaufnahme', fill=MUTED, font=font(16))
    return im, d


def save(frames, path, duration):
    palette = [f.quantize(colors=128) for f in frames]
    palette[0].save(path, save_all=True, append_images=palette[1:], duration=duration,
                    loop=0, optimize=False, disposal=2)


steps = [('1 · Wählen', 'SHOW AUSWAEHLEN / LADEN: gespeicherte Show wählen.'),
         ('2 · Bearbeiten', 'Cue wählen, Material ergänzen, Name und Dauer eintragen.'),
         ('3 · Übernehmen', 'UEBERNEHMEN setzt die Cue-Felder; Übergang wählen.'),
         ('4 · Prüfen', 'Quelle SHOW, Vorschau und Übergänge mit PLAY kontrollieren.'),
         ('5 · Speichern', 'SPEICHERN: Show plus Automation und Materialzustände.'),
         ('6 · Wieder laden', 'Gespeicherte Show auswählen und Werte erneut kontrollieren.')]
frames = []
for active, (_, description) in enumerate(steps):
    im, d = frame('Show bearbeiten · sechs Schritte', 'Speichern und erneutes Laden gehören zum vollständigen Ablauf.')
    for i, (label, _) in enumerate(steps):
        x, y = 32+(i%3)*344, 127+(i//3)*102
        d.rounded_rectangle((x, y, x+320, y+78), radius=12, fill='#23454e' if i == active else PANEL,
                            outline=CYAN if i == active else '#41505d', width=3 if i == active else 1)
        d.text((x+18, y+25), label, font=font(24), fill=CYAN if i == active else MUTED)
    d.text((32, 365), description, fill=CYAN, font=font(23))
    d.text((32, 410), 'Neu/Laden während Aufnahme: zuerst REC beenden.', fill=MUTED, font=font(20))
    frames.append(im)
save(frames, ROOT/'show-workflow.gif', 2100)

frames = []
for tick in range(37):
    t = tick/2
    im, d = frame('Echte Überlappung · zwei Clips', 'Beispiel: A = 12 s, B = 8 s, Crossfade = 2 s ergibt 18 s Showzeit')
    x0, scale = 85, 50
    for sec in range(0, 19, 2):
        x = x0+sec*scale
        d.line((x, 143, x, 325), fill='#38414b', width=1)
        d.text((x-10, 114), str(sec), fill=MUTED, font=font(18))
    d.rounded_rectangle((x0, 165, x0+12*scale, 225), radius=8, fill='#265b69', outline=CYAN, width=2)
    d.rounded_rectangle((x0+10*scale, 255, x0+18*scale, 315), radius=8, fill='#59522a', outline='#dfce7b', width=2)
    d.text((x0+16, 181), 'Clip A · 0–12 s', fill=CYAN, font=font(22))
    d.text((x0+10*scale+16, 271), 'Clip B · 10–18 s', fill='#f0dda0', font=font(22))
    playhead = x0+t*scale
    d.line((playhead, 140, playhead, 330), fill='#f1f6fb', width=3)
    a = 1 if t < 10 else max(0, 1-(t-10)/2)
    b = 0 if t < 10 else min(1, (t-10)/2)
    d.text((32, 355), f'Zeit {t:04.1f} s     Anteil A {a:3.0%}     Anteil B {b:3.0%}', font=font(25), fill=CYAN)
    caption = 'Nur A spielt.' if t < 10 else 'A und B laufen gleichzeitig; die Mischung wechselt.' if t < 12 else 'Nur B spielt weiter.' if t < 18 else 'Ende der 18-Sekunden-Show.'
    d.text((32, 402), caption, fill=MUTED, font=font(22))
    d.text((32, 442), 'Eigene Clip-Fades sind eine zusätzliche, unabhängige Einstellung.', fill=MUTED, font=font(18))
    frames.append(im)
save(frames, ROOT/'sequencer-overlap.gif', 250)
print('Generated show-workflow.gif (6 frames) and sequencer-overlap.gif (37 frames).')
