"""Read-only live-map comparison; writes diagnostic artifacts, never TD state."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from audit_20260907_capture import td
from PIL import Image, ImageDraw, ImageFont

CODE = '''import json, numpy as np
from pixelblaze_mapper.complete_side_rescan import complete_side_measurements
from pathlib import Path
raw=json.loads(Path('C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper/mappings/sources/complete_new_0_1183_raw_2026-08-24.json').read_text())
repaired, estimated=complete_side_measurements(raw)
p=np.array(repaired[517:786])
center=p.mean(axis=0)
_, singular, basis=np.linalg.svd(p-center, full_matrices=False)
normal=basis[-1]
if normal[2]<0: normal=-normal
h=np.array([1.,0.,0.]); h=h-normal*np.dot(h,normal); h=h/np.linalg.norm(h)
v=np.cross(normal,h)
flat=np.stack(((p-center)@h,(p-center)@v),axis=1)
n=op('/project1/pixelblaze_mapper/map_active')
active=[[float(n[i+1,c]) for c in (1,2,3)] for i in range(517,786)]
result=json.dumps({'active':active,'scan_plane':flat.tolist(),'estimated':[i for i in sorted(estimated) if 517<=i<=785], 'singular_values':singular.tolist()})
'''

def main():
    data = td(CODE)
    if isinstance(data, str):
        data = json.loads(data)
    out = ROOT / 'docs/implementation-2026-09-07/side-alignment'
    out.mkdir(exist_ok=True)
    (out / 'upper-readonly.json').write_text(json.dumps(data, indent=2))
    image = Image.new('RGB', (1440, 780), '#101821')
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 22)
    small = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 17)
    draw.text((30,20), 'OBERES SEITENPANEL | 269 LEDs | Diagnose, keine aktive Änderung', font=font, fill='white')
    panels = [
        ('A: Aktive Map, X nach oben / Y nach rechts', [(p[1],p[0]) for p in data['active']]),
        ('B: Scan-Ebene, längentreu projiziert', [tuple(p) for p in data['scan_plane']]),
        ('C: Gleicher Scan, um 90° gedreht', [(-p[1],p[0]) for p in data['scan_plane']]),
    ]
    for k,(title,points) in enumerate(panels):
        left=20+k*475
        draw.text((left,78), title, font=small, fill='white')
        lo=[min(p[a] for p in points) for a in (0,1)]
        hi=[max(p[a] for p in points) for a in (0,1)]
        scale=min(400/max(hi[0]-lo[0],1e-9),480/max(hi[1]-lo[1],1e-9))
        for i,p in enumerate(points):
            x=left+230+(p[0]-(lo[0]+hi[0])/2)*scale
            y=370-(p[1]-(lo[1]+hi[1])/2)*scale
            color='#ffb94e' if 517+i in data['estimated'] else '#55d9e5'
            draw.ellipse((x-3,y-3,x+3,y+3), fill=color)
            if i in (0,268):
                draw.ellipse((x-7,y-7,x+7,y+7), outline='#ff5b6b' if i==0 else '#fff56c', width=2)
                draw.text((x+9,y-8),str(i),font=small,fill='white')
        draw.text((left,644), 'Breite / Höhe: %.2f' % ((hi[0]-lo[0])/(hi[1]-lo[1])),font=small,fill='white')
    draw.text((30,705),'0 / 268 = lokale LED-IDs; orange = geschätzte Scanpunkte. Jede Ansicht gleichmäßig skaliert.',font=small,fill='white')
    draw.text((30,738),'B/C zeigen mögliche Ansichten, noch keine bestätigte Montageausrichtung. Art-Net und Map unverändert.',font=small,fill='white')
    image.save(out/'upper-comparison.png')
    mirror_image = Image.new('RGB', (1100, 730), '#101821')
    mirror_draw = ImageDraw.Draw(mirror_image)
    mirror_draw.text((24,20), 'Oberes Seitenpanel | gewünschte Blickrichtung prüfen', font=font, fill='white')
    variants = [
        ('C: bisherige Ansicht', [(-p[1],p[0]) for p in data['scan_plane']]),
        ('D: C von oben nach unten geklappt', [(-p[1],-p[0]) for p in data['scan_plane']]),
    ]
    for k,(title,points) in enumerate(variants):
        left=20+k*550
        mirror_draw.text((left,80),title,font=font,fill='white')
        lo=[min(p[a] for p in points) for a in (0,1)]
        hi=[max(p[a] for p in points) for a in (0,1)]
        scale=min(460/(hi[0]-lo[0]),470/(hi[1]-lo[1]))
        for i,p in enumerate(points):
            x=left+250+(p[0]-(lo[0]+hi[0])/2)*scale
            y=365-(p[1]-(lo[1]+hi[1])/2)*scale
            color='#ffb94e' if 517+i in data['estimated'] else '#55d9e5'
            mirror_draw.ellipse((x-3,y-3,x+3,y+3),fill=color)
            if i in (0,268):
                mirror_draw.ellipse((x-7,y-7,x+7,y+7),outline='#ff5b6b' if i==0 else '#fff56c',width=2)
                mirror_draw.text((x+9,y-8),str(i),font=small,fill='white')
    mirror_draw.text((24,650),'Markierungen: lokale LED 0 und 268. Keine Änderung der LED-Reihenfolge.',font=small,fill='white')
    mirror_draw.text((24,683),'Nur Vergleichsansicht: aktive Map, Controller und Ausgabe bleiben unverändert.',font=small,fill='white')
    mirror_image.save(out/'upper-c-top-bottom.png')
    print(out/'upper-comparison.png')
    print('Estimated indices:',data['estimated'])

if __name__ == '__main__':
    main()
