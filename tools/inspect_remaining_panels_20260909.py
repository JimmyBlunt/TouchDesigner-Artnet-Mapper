"""Read-only orientation sheets for middle/lower archived panel scans."""
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from audit_20260907_capture import td

CODE = '''import json, numpy as np
from pathlib import Path
from pixelblaze_mapper.complete_side_rescan import complete_side_measurements
raw=json.loads(Path('C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper/mappings/sources/complete_new_0_1183_raw_2026-08-24.json').read_text())
repaired, estimated=complete_side_measurements(raw)
report={}
for label,start,count in [('middle',0,517),('lower',786,398)]:
 p=np.array(repaired[start:start+count]); center=p.mean(axis=0)
 _, singular, basis=np.linalg.svd(p-center,full_matrices=False)
 normal=basis[-1]
 if normal[2]<0: normal=-normal
 h=np.array([1.,0.,0.]); h-=normal*np.dot(h,normal); h/=np.linalg.norm(h)
 v=np.cross(normal,h)
 flat=np.stack(((p-center)@h,(p-center)@v),axis=1)
 report[label]={'points':flat.tolist(),'start':start,'count':count,'estimated':[i-start for i in sorted(estimated) if start<=i<start+count],'singular_values':singular.tolist()}
result=json.dumps(report)
'''

def main():
    data=td(CODE)
    if isinstance(data,str): data=json.loads(data)
    out=ROOT/'docs/implementation-2026-09-07/side-alignment'
    out.mkdir(exist_ok=True)
    (out/'remaining-readonly.json').write_text(json.dumps(data,indent=2))
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',24)
    small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
    for key,title in [('middle','MITTLERES SEITENPANEL'),('lower','UNTERES SEITENPANEL')]:
        item=data[key]; raw=item['points']
        assert len(raw)==item['count']
        variants=[raw,[(-y,x) for x,y in raw],[(-x,-y) for x,y in raw],[(y,-x) for x,y in raw]]
        canvas=Image.new('RGB',(1400,1050),'#101821'); draw=ImageDraw.Draw(canvas)
        draw.text((25,20),title+' | Scanform ohne Foto-Verzerrung',font=font,fill='white')
        for k,points in enumerate(variants):
            left=25+(k%2)*700; top=80+(k//2)*440
            draw.text((left,top),f'{"ABCD"[k]}: {k*90} Grad',font=font,fill='white')
            low=[min(p[a] for p in points) for a in (0,1)]
            high=[max(p[a] for p in points) for a in (0,1)]
            scale=min(590/(high[0]-low[0]),330/(high[1]-low[1]))
            for i,p in enumerate(points):
                x=left+315+(p[0]-(low[0]+high[0])/2)*scale
                y=top+225-(p[1]-(low[1]+high[1])/2)*scale
                color='#ffb94e' if i in item['estimated'] else '#55d9e5'
                draw.ellipse((x-2.6,y-2.6,x+2.6,y+2.6),fill=color)
                if i in (0,item['count']-1):
                    draw.ellipse((x-7,y-7,x+7,y+7),outline='#ff5b6b' if i==0 else '#fff56c',width=2)
                    draw.text((x+8,y-10),str(i),font=small,fill='white')
        draw.text((25,980),f"{item['count']} LEDs | Endpunkte = lokale IDs | Orange = geschätzte Punkte | Maßstab je Ansicht gleichmäßig",font=small,fill='white')
        draw.text((25,1015),'Nur Diagnose. Keine Änderung von Map, Reihenfolge, Controllern oder LED-Ausgabe.',font=small,fill='white')
        target=out/f'{key}-orientations.png'; canvas.save(target); print(target)
        if key in ('middle', 'lower'):
            canvas=Image.new('RGB',(1200,760),'#101821'); draw=ImageDraw.Draw(canvas)
            draw.text((25,20),title+' | B von oben nach unten geklappt',font=font,fill='white')
            comparisons=[('B: bisherige Ansicht',[(-y,x) for x,y in raw]),
                         ('E: oben/unten vertauscht',[(-y,-x) for x,y in raw])]
            for k,(caption,points) in enumerate(comparisons):
                left=25+k*600
                draw.text((left,80),caption,font=font,fill='white')
                low=[min(p[a] for p in points) for a in (0,1)]
                high=[max(p[a] for p in points) for a in (0,1)]
                scale=min(500/(high[0]-low[0]),490/(high[1]-low[1]))
                for i,p in enumerate(points):
                    x=left+270+(p[0]-(low[0]+high[0])/2)*scale
                    y=385-(p[1]-(low[1]+high[1])/2)*scale
                    color='#ffb94e' if i in item['estimated'] else '#55d9e5'
                    draw.ellipse((x-2.6,y-2.6,x+2.6,y+2.6),fill=color)
                    if i in (0,item['count']-1):
                        draw.ellipse((x-7,y-7,x+7,y+7),outline='#ff5b6b' if i==0 else '#fff56c',width=2)
                        draw.text((x+8,y-10),str(i),font=small,fill='white')
            draw.text((25,692),'Lokale LED-IDs bleiben gleich. Links/rechts unverändert; nur oben/unten vertauscht.',font=small,fill='white')
            draw.text((25,726),'Nur Vergleichsansicht. Aktive Map und LED-Ausgabe unverändert.',font=small,fill='white')
            target=out/f'{key}-b-top-bottom.png'; canvas.save(target); print(target)

if __name__=='__main__': main()
