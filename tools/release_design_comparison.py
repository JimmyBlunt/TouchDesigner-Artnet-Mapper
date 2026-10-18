"""Render reproducible native-dialog design studies with installed Windows fonts."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'docs/release-v1.0.0/design'
VARIANTS = [
    ('01', 'Router / Blue Violet', 'Segoe UI', 'segoeui.ttf', '#08090f', '#151623', '#292a40', '#aab7ff', '#eeeef8', '#a1a5bd'),
    ('02', 'Graphite / Lime', 'Bahnschrift', 'bahnschrift.ttf', '#171a18', '#232a25', '#354139', '#b3e779', '#f0f5ed', '#adbba8'),
    ('03', 'Slate / Cyan', 'Calibri', 'calibri.ttf', '#101820', '#18242e', '#263846', '#55d6e7', '#edf6fa', '#a0b4c3'),
    ('04', 'Obsidian / Amber', 'Consolas', 'consola.ttf', '#191714', '#29241d', '#40382c', '#ffcb76', '#faf0df', '#c6b49a'),
    ('05', 'Midnight / Coral', 'Verdana', 'verdana.ttf', '#101b25', '#192a36', '#2b4050', '#ffab96', '#eef5fa', '#a7bfce'),
]

def render(v):
    number, title, family, fontfile, bg, surface, stroke, accent, ink, muted = v
    image = Image.new('RGB', (1120, 700), bg)
    d = ImageDraw.Draw(image)
    def font(size): return ImageFont.truetype('C:/Windows/Fonts/' + fontfile, size)
    def text(x,y,s,size=17,color=ink): d.text((x,y),s,font=font(size),fill=color)
    def box(x,y,w,h,fill=surface): d.rounded_rectangle((x,y,x+w,y+h),radius={'01':10,'02':2,'03':5,'04':0,'05':16}[number],fill=fill,outline=stroke)
    text(32,24,'PIXELBLAZE MAPPER',15,muted)
    text(32,52,'3D Scan',32)
    text(32,96,'Panel 8  /  Neue LED-Positionen aufnehmen',17,muted)
    box(858,42,94,32); text(878,47,'i  Info',15)
    box(962,42,126,32,stroke); text(979,47,'How-to  >',15,accent)
    d.line((32,136,1088,136),fill=stroke,width=1)
    # Same information density for an honest font and palette comparison.
    steps=['01  Vorbereiten','02  Aufnehmen','03  Prüfen','04  Ausrichten']
    for i,s in enumerate(steps):
        x=32+i*267; box(x,155,255,38,stroke if i==0 else surface)
        text(x+12,163,s,16,accent if i==0 else muted)
    box(32,215,468,343)
    text(52,236,'SCAN-EINSTELLUNGEN',14,accent)
    for y,label,value in [(281,'Panel','Panel 8'),(343,'LED-Anzahl','299'),(405,'Aufnahme','Mehrere Blickwinkel')]:
        text(52,y,label,16,muted); box(236,y-7,242,38,bg); text(250,y+1,value,16)
    text(52,474,'LED-ID 0–298  ·  Kamera zwischen den Views bewegen',14,muted)
    box(52,511,188,30,accent); text(66,516,'Kamera prüfen',15,bg)
    box(512,215,576,343)
    text(534,236,'LIVE-VORSCHAU',14,accent)
    for row in range(13):
        for col in range(20):
            if row>8 and col>16-(row-8): continue
            x=636+col*13;y=282+row*15
            d.ellipse((x,y,x+3,y+3),fill=accent)
    text(534,515,'Ausgabe aus  /  Aufnahmestatus bereit',14,muted)
    box(32,578,1056,62)
    text(52,592,'TIPP  LED-Anzahl',14,accent)
    text(242,592,'Anzahl des gewählten Panels. Beispiel: 299 = IDs 0–298.',15)
    text(32,666,number+'  '+title+'   /   '+family,16,accent)
    text(736,666,'Designstudie · kein Live-Screenshot',13,muted)
    if number != '01':
        full = Image.new('RGB',(1280,700),bg)
        full.paste(image,(80,0))
        if number == '02': ImageDraw.Draw(full).rectangle((0,0,12,700),fill=accent)
        if number == '04': ImageDraw.Draw(full).line((12,12,1268,12),fill=accent,width=2)
        return full
    full = Image.new('RGB',(1280,700),bg)
    full.paste(image,(160,0)); rail=ImageDraw.Draw(full)
    rail.line((160,0,160,700),fill=stroke)
    rail.rounded_rectangle((18,26,52,60),radius=9,fill=accent)
    rail.text((28,30),'A',font=font(20),fill=bg)
    rail.text((18,82),'LED CONTROL',font=font(12),fill=ink)
    rail.text((18,108),'DESK / V1.0',font=font(11),fill=muted)
    for i,label in enumerate(['Übersicht','Materialien','Show','3D Scan','Router','Layout']):
        y=186+i*49
        if i==3:
            rail.rounded_rectangle((10,y-8,150,y+29),radius=8,fill=surface,outline=stroke)
            rail.line((11,y-3,11,y+24),fill=accent,width=2)
        rail.text((22,y),label,font=font(14),fill=ink if i==3 else muted)
    rail.text((18,645),'● Ausgabe aus',font=font(12),fill=muted)
    return full

def main():
    DEST.mkdir(parents=True,exist_ok=True)
    images=[]
    for v in VARIANTS:
        im=render(v); im.save(DEST / (v[0]+'-'+v[1].lower().replace(' / ','-')+'.png'))
        images.append(im)
    sheet=Image.new('RGB',(2560,2100),'#08090f')
    for i,im in enumerate(images): sheet.paste(im,((i%2)*1280,(i//2)*700))
    d=ImageDraw.Draw(sheet); f=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',30)
    d.text((1340,1490),'Fünf unterschiedliche Designrichtungen',font=f,fill='#aab7ff')
    d.text((1340,1540),'01 basiert auf deinem Art-Net-Webinterface.',font=f,fill='#eeeef8')
    d.text((1340,1610),'02–05: eigenständige Schrift- und Farbkonzepte.',font=f,fill='#a1a5bd')
    d.text((1340,1680),'Vergleichsstudien · Auswahl noch offen',font=f,fill='#a1a5bd')
    sheet.save(DEST/'five-design-directions.png')
    import html
    cards=[]
    for v in VARIANTS:
        filename=v[0]+'-'+v[1].lower().replace(' / ','-')+'.png'
        cards.append('<section id="design-'+v[0]+'"><h2>'+v[0]+' · '+html.escape(v[1])+'</h2><p>'+html.escape(v[2])+' · '+('Vorbild: vorhandenes Art-Net-Webinterface' if v[0]=='01' else 'Eigenständige Designrichtung')+'</p><a href="'+filename+'"><img src="'+filename+'" alt="'+html.escape(v[1])+' Designstudie"></a></section>')
    page='''<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Version 1.0 · Designvergleich</title><style>:root{color-scheme:dark;font:15px 'Segoe UI',sans-serif;background:#08090f;color:#eeeef8}body{margin:0}header{position:sticky;top:0;padding:16px 28px;background:#10101bf5;border-bottom:1px solid #303044;z-index:1}h1{font-size:21px;margin:0 0 8px}p{color:#a1a5bd}nav{display:flex;gap:8px;flex-wrap:wrap}nav a{padding:8px 14px;background:#202032;color:#c3c6ff;text-decoration:none;border-radius:6px}main{max-width:1280px;margin:auto;padding:20px}section{scroll-margin-top:145px;margin:32px 0 64px}h2{font-size:22px;margin-bottom:5px}img{width:100%;height:auto;border:1px solid #303044;border-radius:10px}a:focus-visible{outline:3px solid #bca0ff}</style><header><h1>Version 1.0 · Fünf Designrichtungen</h1><nav>'''+''.join('<a href="#design-'+v[0]+'">'+v[0]+' · '+html.escape(v[1])+'</a>' for v in VARIANTS)+'''</nav></header><main><p>Visuelle Vergleichsstudien, keine Live-Screenshots. Nur Variante 01 basiert auf dem Art-Net-Webinterface. Die Auswahl ist offen; die bestehende Bedienlogik bleibt erhalten.</p>'''+''.join(cards)+'</main></html>'
    (DEST/'index.html').write_text(page,encoding='utf-8')
    print(DEST/'five-design-directions.png')

if __name__=='__main__': main()
