"""Rebuild source-grounded SVG diagrams. No application or hardware actions."""
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parent/'diagrams'
ROOT.mkdir(exist_ok=True)


def start(width, height, title):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">',
            f'<rect width="{width}" height="{height}" rx="24" fill="#101820"/>',
            '<style>text{font-family:Bahnschrift,Segoe UI,Arial,sans-serif;fill:#e1e5e6}.h{font-size:25px;font-weight:600}.t{font-size:18px}.s{font-size:16px;fill:#a9b2b5}</style>']


def text(parts, x, y, label, style='t'):
    parts.append(f'<text class="{style}" x="{x}" y="{y}">{escape(label)}</text>')


def box(parts, x, y, w, h, title, lines):
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="#232a25" stroke="#354139"/>')
    text(parts, x+22, y+37, title, 'h')
    for i, line in enumerate(lines): text(parts, x+22, y+72+28*i, line, 's')


p = start(1200, 940, 'MK2: Tasten, Displays und Aufnahmegesten; schematische Belegung')
text(p, 40, 55, 'MASCHINE MK2 · Belegung im Projekt', 'h')
text(p, 40, 87, 'Der aktuelle Modus bestimmt die Aktion. Schematisch, kein Hardwarefoto.', 's')
box(p, 40, 115, 540, 135, 'Obere Tasten 1–8', ['Hauptbild: TD-/MM-Parameterseite wählen', 'Browser: 1 ALL · 2 FAV · 3 CAT · 8 Favorit'])
box(p, 610, 115, 550, 135, 'Drehregler 1–8', ['Parameter der sichtbaren Seite bearbeiten', 'Show: Werteänderung nur während Aufnahme'])
box(p, 40, 275, 540, 180, 'Linkes Display', ['Materialbild / Name / Modus', 'Show: Status, vergangene und übrige Zeit', 'Fortschritt, Übergang; unten Cuewerte'])
box(p, 610, 275, 550, 180, 'Rechtes Display', ['Parameter / Werte / ausgewähltes Detail', 'Browser: Auswahl und Zuweisungen', 'Padansicht oder Bestätigung je nach Kontext'])
box(p, 40, 480, 540, 310, 'Navigation & Transport', [])
rows = [('STEP', 'Material ↔ Show'), ('BROWSE', 'Materialliste; Rad wählt / bestätigt'), ('SCENE', 'Pad-Raster und Preset-Menü'), ('SELECT', 'Browsermaterial → Bank → Pad'), ('A–H', 'Pad-Bank / Show-Parameterblock'), ('PLAY / ◀ / ▶', 'Start / vorherige / nächste Cue'), ('RESTART', 'Showanfang + Wiedergabe')]
for i, (label, value) in enumerate(rows):
    text(p, 60, 556+32*i, label)
    text(p, 205, 556+32*i, value, 's')
text(p, 640, 510, 'Pads · Hardwarezählung', 'h')
for row in range(4):
    for column in range(4):
        x, y = 640+130*column, 535+64*row
        n = (3-row)*4+column+1
        p.append(f'<rect x="{x}" y="{y}" width="110" height="52" rx="8" fill="#253943" stroke="#55d6e7"/>')
        text(p, x+43, y+34, str(n))
box(p, 40, 820, 1120, 90, 'REC loslassen → neue Cue · REC + ERASE → Automation im Clip', ['REC erneut beendet die Aufnahme. ERASE allein löscht nichts. Danach Show speichern.'])
(ROOT/'mk2-controls.svg').write_text(''.join(p)+'</svg>', encoding='utf-8')

p = start(1200, 690, 'PixelblazeMapper: Material, Mapping, Scan und vier konfigurierte Controller')
text(p, 40, 55, 'PixelblazeMapper · 1.0.0', 'h')
text(p, 40, 87, 'Von Material und Kameramessung zur Show auf der Installation', 's')
box(p, 40, 125, 325, 150, 'Material / Show', ['Core + importierte Materialien', 'Timeline · Automation · MK2'])
box(p, 437, 125, 325, 150, 'LED-Mapping', ['10.330 Quellplätze', 'Original-IDs und Lücken erhalten'])
box(p, 835, 125, 325, 150, 'LED-Vorschau', ['Schrankansicht / Orientierung', 'Softwarebild vor Hardwareausgabe'])
text(p, 387, 208, '→', 'h'); text(p, 785, 208, '→', 'h')
box(p, 40, 330, 325, 155, 'Scan → Layout', ['Ansichten → 3D → Entwurf', 'Panel 8: 296 / 299 gemessen'])
text(p, 388, 414, '↗', 'h'); text(p, 585, 310, '↓', 'h')
box(p, 437, 330, 723, 280, 'Art-Net Router', ['WS2812_NODE → 10.0.0.244 · U0–23 · GRB', 'PANEL8_251 → 10.0.0.251 · U156–162 · BGR', 'BACK_PANEL_249 → 10.0.0.253 · U120–156 · RGB', 'APA102_ESP → 10.0.0.251 · deaktivierte historische Route', '', 'Validieren → sicher übernehmen → bewusst starten'])
text(p, 40, 654, 'Abgelesener Stand 18.10.2026 · Paketadressen ab 0 · Softwareprüfung ersetzt keine physische Abnahme.', 's')
(ROOT/'system-overview.svg').write_text(''.join(p)+'</svg>', encoding='utf-8')
print('Generated MK2 and system overview SVGs.')
