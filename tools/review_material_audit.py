"""Build reviewable contact sheets and a searchable gallery from the audit journal.

Rendering success is not visual equivalence. Stored thumbnails can represent
other parameter values; this gallery supports explicit visual review.
"""
import argparse
import html
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
LABELS = {'passed':'Bildtest bestanden', 'review':'Bild nachprüfen',
          'compile_error':'Shaderfehler', 'unsupported':'Eingaben oder Funktionen fehlen',
          'quarantined':'GPU-Test ausgesetzt', 'probe_error':'Prüfung fehlgeschlagen'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, default=ROOT/'docs/material-audit-20261013/results.json')
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding='utf-8'))
    out = args.report.parent
    (out/'reference').mkdir(exist_ok=True)
    (out/'contact-sheets').mkdir(exist_ok=True)
    try:
        font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 13)
    except OSError:
        font = ImageFont.load_default(size=13)
    cards, rendered = [], []
    for item in report['results']:
        key, name, status = item['id'], item['name'], item['status']
        ref = None
        if item.get('preview_path'):
            try:
                with Image.open(item['preview_path']) as original:
                    ref = ImageOps.contain(original.convert('RGB'), (96,96))
                ref.save(out/'reference'/(key+'.png'))
            except (OSError, ValueError):
                pass
        thumb_path = Path(item['thumbnail']) if item.get('thumbnail') else None
        strip = None
        if thumb_path and thumb_path.is_file():
            with Image.open(thumb_path) as image:
                strip = image.convert('RGB')
            rendered.append((item, ref, strip))
        reasons = item.get('reasons') or item.get('adaptation',{}).get('reasons') or []
        detail = html.escape('; '.join(str(r) for r in reasons))
        if item.get('import',{}).get('error'):
            detail += ' '+html.escape(item['import']['error'])
        preview = ('<img alt="Katalog-Vorschaubild" class="ref" src="reference/'+key+'.png">') if ref else '<span class="missing">Keine Referenz</span>'
        gpu = ('<img alt="GPU-Bilder bei drei Zeitpunkten" class="gpu" src="'+html.escape(thumb_path.relative_to(out).as_posix())+'">') if strip else '<span class="missing">Kein GPU-Ergebnis</span>'
        cards.append('<article data-status="'+status+'" data-name="'+html.escape(name.lower(),quote=True)+'"><h2>'+html.escape(name)+'</h2><p class="badge">'+LABELS.get(status,status)+'</p><div class="images">'+preview+gpu+'</div><p>'+detail+'</p><details><summary>Messwerte / Import</summary><pre>'+html.escape(json.dumps({k:item.get(k) for k in ('id','import','adaptation','probe')},ensure_ascii=False,indent=2))+'</pre></details></article>')
    for start in range(0, len(rendered), 36):
        page = Image.new('RGB', (1440, 60+120*9), '#e7e9ec')
        draw = ImageDraw.Draw(page)
        draw.text((16,12),'Materialprüfung: links Katalogreferenz, rechts GPU bei t=0 / 1 / 2. Abweichende Defaults möglich.',font=font,fill='#222')
        for i,(item,ref,strip) in enumerate(rendered[start:start+36]):
            x,y=(i%4)*360, 52+(i//4)*120
            name=item['name']
            while draw.textlength(name,font=font)>345:
                name=name[:-2]+'…'
            draw.text((x+5,y),name,font=font,fill='#111')
            draw.text((x+5,y+18),item['status'],font=font,fill='#922' if item['status']!='passed' else '#154')
            if ref:
                page.paste(ImageOps.contain(ref,(60,64)),(x+5,y+39))
            page.paste(strip.resize((288,64),Image.Resampling.NEAREST),(x+68,y+39))
        page.save(out/'contact-sheets'/('page-%02d.png'%(start//36+1)))
    counts=html.escape(' · '.join(str(count)+' '+LABELS.get(status,status) for status,count in report['counts'].items()))
    document='''<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Materialbibliothek – Einzelprüfung</title>
<style>body{margin:24px;background:#eceff2;color:#20262a;font:15px system-ui}h1{margin-bottom:8px}header{position:sticky;top:0;background:#eceff2;padding:8px 0;z-index:1}input,select{font:inherit;padding:8px;margin-right:8px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(400px,1fr));gap:16px}article{background:white;border:1px solid #ccd2d8;border-radius:8px;padding:16px;overflow:hidden}h2{font-size:18px;margin:0}.badge{font-family:monospace}.images{display:flex;align-items:center;gap:12px;background:#16191d;padding:8px}.ref{width:64px;max-height:96px;object-fit:contain}.gpu{width:288px;height:64px;image-rendering:pixelated}.missing{color:#bec7d3}pre{white-space:pre-wrap;font-size:11px;overflow-wrap:anywhere}article[hidden]{display:none}</style>
<h1>Materialbibliothek: Einzelprüfung</h1><p>Links das gespeicherte Katalogbild, rechts drei tatsächlich gerenderte GPU-Bilder. Kompilierung und Messwerte beweisen keine identische Darstellung in jeder Parameterkombination. Einfarbige oder schwarze Ausgaben sind zur Nachkontrolle markiert.</p><p>'''+counts+'''</p><header><input id="search" type="search" placeholder="Material suchen" aria-label="Material suchen"><select id="status" aria-label="Prüfstatus"><option value="">Alle Ergebnisse</option><option>passed</option><option>review</option><option>compile_error</option><option>unsupported</option><option>quarantined</option><option>import_conflict</option><option>import_error</option><option>probe_error</option></select><span id="count"></span></header><main>'''+''.join(cards)+'''</main><script>function filter(){let n=0;for(const c of document.querySelectorAll('article')){c.hidden=!(c.dataset.name.includes(search.value.toLowerCase())&&(!statusSelect.value||c.dataset.status===statusSelect.value));if(!c.hidden)n++}document.querySelector('#count').textContent=n+' Materialien'}const search=document.querySelector('#search'),statusSelect=document.querySelector('#status');search.oninput=filter;statusSelect.onchange=filter;filter();</script></html>'''
    document = document.replace('</style>', '@media(max-width:500px){body{margin:12px}main{grid-template-columns:minmax(0,1fr)}.images{flex-wrap:wrap}.gpu{max-width:100%;height:auto}input,select{max-width:100%;box-sizing:border-box;margin-bottom:6px}}</style>')
    for status,label in LABELS.items():
        document = document.replace('<option>'+status+'</option>', '<option value="'+status+'">'+label+'</option>')
    invalid = sum(any(not s.get('finite',False) for s in item.get('probe',{}).get('samples',[])) for item in report['results'])
    if invalid:
        document = document.replace('</h1>', '</h1><p><strong>'+str(invalid)+' Material mit ungültigen Pixelwerten ist in den Nachkontrollen enthalten und bleibt gesperrt.</strong></p>',1)
    (out/'galerie.html').write_text(document,encoding='utf-8')
    print(json.dumps(dict(materials=len(cards),rendered=len(rendered),sheets=(len(rendered)+35)//36)))


if __name__=='__main__':
    main()
