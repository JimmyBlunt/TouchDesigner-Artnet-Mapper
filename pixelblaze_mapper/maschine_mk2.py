"""MASCHINE MK2 HID surface. Worker owns USB; callbacks only enqueue pad edges.

Protocol reference: Ardour libs/surfaces/maschine2/m2_dev_mk2.cc.
No firmware, driver or Native Instruments template changes are made.
"""
from collections import deque
from functools import lru_cache
from io import BytesIO
from pathlib import Path
import sys
import math
import threading
import time

__version__ = '0.2.0'

# Report offsets include the report ID. Top and transport buttons have fixed
# colour LEDs; only the groups and pads support RGB. Protocol facts verified
# against Ardour m2_dev_mk2.{h,cc}; encoder positions are absolute, not deltas.
BUTTONS = {(1, i): ('top', i) for i in range(8)}
BUTTONS.update({(4, i): ('group', i) for i in range(8)})
BUTTONS.update({(2, 1): ('step', None), (2, 2): ('browse', None),
                (3, 7): ('wheel', None), (6, 0): ('scene', None),
                (5, 0): ('restart', None), (5, 1): ('previous', None),
                (5, 2): ('next', None), (5, 4): ('play', None),
                (5, 5): ('rec', None), (5, 6): ('erase', None)})


class ControlEdges:
    """Decode absolute counters and button edges; reconnect establishes baseline."""
    def __init__(self, encoder_quantum=10, encoder_hysteresis=5):
        # The small knobs report 1000 absolute counts per turn, not detents.
        # Actual idle MK2 reports oscillate 705/710/715 on a stationary knob.
        # Ten counts = one UI step; a five-count Schmitt margin rejects this
        # noise. Retain residual travel so arbitrarily slow movement accumulates
        # instead of discarding small deltas. The 16-detent wheel is unaffected.
        self.encoder_quantum = max(1, int(encoder_quantum))
        self.encoder_hysteresis = max(0, int(encoder_hysteresis))
        self.encoder_residual = [0]*8
        self.previous = None

    def read(self, report):
        if len(report) < 25 or report[0] != 1:
            return []
        current = bytes(report[:25])
        old, self.previous = self.previous, current
        if old is None:
            return []
        events = []
        for (offset, bit), (name, index) in BUTTONS.items():
            pressed = bool(current[offset] & (1 << bit))
            if pressed == bool(old[offset] & (1 << bit)):
                continue
            if name == 'wheel':
                if pressed:
                    events.append(dict(type='wheel_press'))
                continue
            event = dict(type='button', name=name, down=pressed)
            if index is not None:
                event['index'] = index
            events.append(event)
        # Wheel: modulo 16. Eight encoders: little-endian modulo 1000.
        for index, offset, modulus in [(-1, 8, 16)]+[(i, 9+2*i, 1000) for i in range(8)]:
            value = current[offset] if index < 0 else int.from_bytes(current[offset:offset+2], 'little')
            previous = old[offset] if index < 0 else int.from_bytes(old[offset:offset+2], 'little')
            if value >= modulus or previous >= modulus:
                continue
            delta = (value-previous+modulus//2) % modulus-modulus//2
            if index >= 0:
                self.encoder_residual[index] += delta
                residual = self.encoder_residual[index]
                steps = max(0, (abs(residual)-self.encoder_hysteresis)//self.encoder_quantum)
                delta = steps if residual > 0 else -steps
                self.encoder_residual[index] -= delta*self.encoder_quantum
            if delta:
                event = dict(type='wheel' if index < 0 else 'encoder', delta=delta)
                if index >= 0:
                    event['index'] = index
                events.append(event)
        return events


def dependencies():
    root = Path(__file__).resolve().parents[1]/'.controller-runtime'
    if sys.version_info[:2] == (3, 11):
        root /= 'td311'
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def physical_pad(usb_index):
    return (3-usb_index//4)*4+usb_index%4


def display_packets(display, pixels):
    if display not in (0, 1) or len(pixels) != 2048:
        raise ValueError('MK2 display requires 256 × 64 monochrome pixels')
    for band in range(8):
        yield bytes([0xe0 | display, 0, 0, band*8, 0, 32, 0, 8, 0])+pixels[band*256:(band+1)*256]


def pad_lights(snapshot, now=None):
    controller = snapshot.get('controller') or {}
    cards = controller.get('cards', snapshot.get('cards', []))
    selected = controller.get('pad_index', snapshot.get('selected', 0))
    flashes = controller.get('pad_flash', [False]*16)
    flash_until = snapshot.get('_pad_flash_until', {})
    now = time.monotonic() if now is None else now
    packet = bytearray([0x80])
    for usb_index in range(16):
        index = physical_pad(usb_index)
        assigned = index < len(cards) and cards[index].get('available', False)
        colour = (75, 75, 75) if index == selected else (0, 35, 55) if assigned else (0, 0, 0)
        if controller.get('mode') == 'show' and not controller.get('recording'):
            parameters = [p for page in controller.get('parameter_pages', []) for p in page.get('parameters', [])]
            parameter = controller.get('parameter_group', 0)*8+index
            changed = parameter < len(parameters) and (parameters[parameter].get('automated') or parameters[parameter].get('modified'))
            colour = (85, 75, 0) if index < 8 and parameter < len(parameters) and parameter == controller.get('parameter_index', 0) else (0, 20, 35) if index < 8 and changed else (0, 0, 0)
        if (index < len(flashes) and flashes[index]) or flash_until.get(index, 0) > now:
            colour = (100, 0, 0)
        packet.extend(colour)
    return bytes(packet)


def button_lights(snapshot, now=None):
    """0x81: duplicated group RGB + transport; 0x82: fixed-colour brightness."""
    c = snapshot.get('controller') or {}
    now = time.monotonic() if now is None else now
    blink = 100 if int(now*4) % 2 == 0 else 0
    groups, buttons = bytearray(57), bytearray(32)
    groups[0], buttons[0] = 0x81, 0x82
    content = c.get('group_activity', [False]*8) if c.get('mode') == 'show' and not c.get('recording') else c.get('group_has_content', [False]*8)
    active = c.get('parameter_group', 0) if c.get('mode') == 'show' and not c.get('recording') else c.get('bank', 0)
    for i in range(8):
        rgb = (85, 75, 0) if i == active else (0, 15, 30) if i < len(content) and content[i] else (0, 0, 0)
        groups[1+6*i:7+6*i] = bytes(rgb)*2
    groups[49:52] = bytes([20, 20, 20])
    groups[53] = 90 if c.get('show', {}).get('playing') else 20
    recording = c.get('recording')
    groups[54] = blink if recording else 15
    groups[55] = blink if recording == 'automation' else 10
    buttons[1] = 80 if c.get('mode', 'material') == 'material' else 15
    buttons[2] = 100 if c.get('mode') == 'show' else 0
    buttons[3] = 100 if c.get('screen') == 'browse' else 15
    for i in range(min(8, len(c.get('parameter_pages', [])))):
        buttons[9+i] = 100 if i == c.get('page', 0) % 8 else 20
    buttons[17] = 100 if c.get('screen', '').startswith('pad_') else 15
    return bytes(groups), bytes(buttons)


class PadEdges:
    """Median filtering and hysteresis; one action per press, never pressure repeats."""
    def __init__(self):
        self.samples = [deque(maxlen=3) for _ in range(16)]
        self.down = [False]*16
        self.initialized = [False]*16

    def read(self, report):
        if len(report) < 33 or report[0] != 0x20:
            return []
        pressed = []
        for i in range(16):
            pressure = report[1+i*2] | ((report[2+i*2]&15)<<8)
            samples = self.samples[i]
            samples.append(pressure)
            if len(samples) < 3:
                continue
            value = sorted(samples)[1]
            if not self.initialized[i]:
                # A pad held while connecting is a baseline, never a new hit.
                # Require a filtered release before it can fire for the first time.
                self.initialized[i] = True
                self.down[i] = value >= 16
                continue
            if value >= 48 and not self.down[i]:
                self.down[i] = True
                pressed.append(physical_pad(i))
            elif value < 16:
                self.down[i] = False
        return pressed


def _legacy_render(snapshot):
    from PIL import Image, ImageDraw, ImageOps, ImageFont
    images = [Image.new('1', (256, 64)) for _ in range(2)]
    draw = [ImageDraw.Draw(img) for img in images]
    font = ImageFont.load_default(size=10)
    selected = snapshot['selected']
    cards = snapshot['cards']

    def thumbnail(card, size):
        path = snapshot['images'].get(card.get('image'))
        if not path:
            return None
        try:
            with Image.open(path) as original:
                return ImageOps.fit(original.convert('L'), size).convert('1')
        except (OSError, ValueError):
            return None

    card = cards[selected]
    thumb = thumbnail(card, (62, 62))
    if thumb:
        images[0].paste(thumb, (1, 1))
    else:
        draw[0].rectangle((1, 1, 62, 62), outline=1)
        draw[0].text((7, 24), 'Kein Bild', font=font, fill=1)
    draw[0].text((70, 1), 'PAD %02d  /  %s' % (selected+1, 'CLIP' if card['kind']=='cue' else 'MATERIAL'), font=font, fill=1)
    # Pixel-width wrapping handles names with and without spaces.
    lines, line = [], ''
    for char in card['label']:
        if draw[0].textlength(line+char, font=font) > 180:
            lines.append(line)
            line = ''
        line += char
    lines.append(line)
    for row, line in enumerate(lines[:3]):
        draw[0].text((70, 18+row*12), line, font=font, fill=1)
    for usb_index in range(16):
        index = physical_pad(usb_index)
        x, y = usb_index%4*64, usb_index//4*16
        thumb = thumbnail(cards[index], (42, 14))
        if thumb:
            images[1].paste(thumb, (x+20, y+1))
        draw[1].text((x+3, y+2), '%02d'%(index+1), font=font, fill=1)
        if index == selected:
            draw[1].rectangle((x, y, x+63, y+15), outline=1)
    return images


@lru_cache(maxsize=128)
def _thumbnail(path, size):
    """Approved catalog paths only. Cache resized pixels, never reopen per tick."""
    from PIL import Image, ImageOps
    try:
        with Image.open(path) as original:
            return ImageOps.fit(original.convert('L'), size).convert('1')
    except (OSError, ValueError):
        return None


def _number(value):
    if isinstance(value, bool):
        return 'On' if value else 'Off'
    if isinstance(value, (float, int)):
        return ('%.3f' % value).rstrip('0').rstrip('.') if isinstance(value, float) else str(value)
    return str(value)


@lru_cache(maxsize=32)
def _transition_mask(kind):
    """Small original pictograms for every transition supported by the player."""
    from PIL import Image, ImageDraw
    mask = Image.new('1', (32, 12))
    d = ImageDraw.Draw(mask)
    if kind == 'cut':
        d.line((10, 1, 10, 10), fill=1); d.line((21, 1, 21, 10), fill=1)
    elif kind == 'crossfade':
        d.line((2, 1, 29, 10), fill=1); d.line((2, 10, 29, 1), fill=1)
    elif kind == 'fade_black':
        d.line([(2, 1), (15, 10), (29, 1)], fill=1)
    elif kind == 'burn':
        d.line([(3, 10), (7, 6), (10, 9), (15, 1), (17, 7), (22, 4), (28, 10)], fill=1)
    elif kind == 'dissolve':
        for x in range(2, 30):
            for y in range(1, 11):
                if (x*7+y*11) % 13 < 3:
                    d.point((x, y), fill=1)
    elif kind == 'glitch':
        for line in ((2,2,18,2), (13,4,28,4), (5,7,20,7), (18,9,30,9)):
            d.line(line, fill=1)
    elif kind in ('wipe', 'wipe_left', 'wipe_up', 'wipe_down'):
        points = {'wipe': [(3,6),(28,6),(22,1),(28,6),(22,10)],
                  'wipe_left': [(28,6),(3,6),(9,1),(3,6),(9,10)],
                  'wipe_up': [(16,10),(16,1),(10,5),(16,1),(22,5)],
                  'wipe_down': [(16,1),(16,10),(10,6),(16,10),(22,6)]}[kind]
        d.line(points, fill=1)
    elif kind == 'radial':
        d.ellipse((11,1,21,11), outline=1)
        d.line((16,6,29,1), fill=1); d.line((16,6,27,10), fill=1)
    elif kind == 'iris':
        d.ellipse((4,1,27,10), outline=1); d.ellipse((11,3,20,8), outline=1)
    elif kind == 'bars':
        for x in range(3, 30, 6):
            d.rectangle((x,1,x+2,10), fill=1)
    elif kind == 'checker':
        for x in range(2,30,4):
            for y in range(1,10,3):
                if (x//4+y//3) % 2:
                    d.rectangle((x,y,x+2,y+1), fill=1)
    elif kind == 'spiral':
        points = [(16+int((i/10)*math.cos(i*.3)), 6+int((i/28)*math.sin(i*.3))) for i in range(100)]
        d.line(points, fill=1)
    else:
        d.line((3,10,28,1), fill=1)
    return mask


def transition_tile(kind, progress):
    from PIL import Image, ImageDraw, ImageChops
    background = Image.new('1', (32,12))
    end = int(32*max(0, min(1, float(progress))))
    if end:
        ImageDraw.Draw(background).rectangle((0,0,end-1,11), fill=1)
    return ImageChops.logical_xor(background, _transition_mask(kind))


def render(snapshot):
    """Render immutable workflow state; no TouchDesigner calls or state mutation."""
    if not snapshot.get('controller'):
        return _legacy_render(snapshot)
    from PIL import Image, ImageDraw, ImageFont
    c = snapshot['controller']
    images = [Image.new('1', (256, 64)) for _ in range(2)]
    draws = [ImageDraw.Draw(img) for img in images]
    font = ImageFont.load_default(size=9)
    small = ImageFont.load_default(size=8)
    big = ImageFont.load_default(size=15)

    def text(side, x, y, value, width=256, selected=False, f=font):
        d = draws[side]
        value = str(value)
        while value and d.textlength(value, font=f) > width:
            value = value[:-1]
        if selected:
            d.rectangle((x, y, min(255, x+width), y+10), fill=1)
        d.text((x, y-1), value, fill=0 if selected else 1, font=f)

    def picture(side, material, xy, size):
        image = material.get('image') or material.get('id')
        path = snapshot.get('images', {}).get(image)
        thumb = _thumbnail(str(path), size) if path else None
        x, y = xy
        if thumb is not None:
            images[side].paste(thumb, xy)
        else:
            draws[side].rectangle((x, y, x+size[0]-1, y+size[1]-1), outline=1)
            text(side, x+3, y+size[1]//2-4, 'Kein Bild', size[0]-5, f=small)

    def bar(side, box, fraction, marker=False):
        d = draws[side]
        x, y, right, bottom = box
        try:
            fraction = max(0, min(1, float(fraction)))
        except (TypeError, ValueError):
            fraction = 0
        d.rectangle(box, outline=1)
        end = x+1+int((right-x-2)*fraction)
        if end > x+1:
            d.rectangle((x+1, y+1, end, bottom-1), fill=1)
        if marker:
            d.line((end, y-2, end, bottom+2), fill=1)

    pages = c.get('parameter_pages', [])
    page_index = max(0, min(c.get('page', 0), len(pages)-1))
    page = pages[page_index] if pages else {}
    screen = c.get('screen', 'home')
    material = c.get('material') or {}

    def tabs():
        base = page_index//8*8
        for i, p in enumerate(pages[base:base+8]):
            side, x = i//4, i%4*64
            draws[side].rectangle((x, 0, x+62, 9), outline=1, fill=1 if base+i == page_index else 0)
            label = str(p.get('label', 'MM'))
            if base+i == len(pages)-1 and c.get('parameter_overflow', 0):
                label += ' +%d' % c['parameter_overflow']
            draws[side].text((x+3, -1), label[:12], font=small, fill=0 if base+i == page_index else 1)

    def parameters():
        params = page.get('parameters', [])[:8]
        focused = c.get('focused_parameter')
        if c.get('mode') == 'show' and not c.get('recording') and focused is not None:
            if isinstance(focused, dict):
                param = focused
            elif isinstance(focused, int):
                param = params[focused] if 0 <= focused < len(params) else None
            else:
                param = next((p for p in params if p.get('id') == focused), None)
            if param:
                text(1, 3, 13, param.get('name') or param.get('label', ''), 249)
                text(1, 3, 27, _number(param.get('value', 0)), 249, f=big)
                lo, hi, value = param.get('min', 0), param.get('max', 1), param.get('value', 0)
                try:
                    ratio = (value-lo)/(hi-lo) if hi != lo else 0
                except TypeError:
                    ratio = 0
                bar(1, (4, 50, 249, 59), ratio, marker=True)
                return
        for i, p in enumerate(params):
            x, y = (i//4)*128+3, 12+(i%4)*13
            name = p.get('abbreviation') or p.get('label') or p.get('name', '')
            supported = p.get('editable', True)
            text(1, x, y, name if supported else '! '+name, 68, f=small)
            text(1, x+70, y, _number(p.get('value', 0)) if supported else 'N/A', 51, f=small)
            lo, hi, value = p.get('min', 0), p.get('max', 1), p.get('value', 0)
            try:
                ratio = (value-lo)/(hi-lo) if hi != lo and supported else 0
            except TypeError:
                ratio = 0
            bar(1, (x, y+8, x+120, y+11), ratio)
        if not params:
            text(1, 5, 27, 'Keine Parameter', 245)

    if screen == 'browse':
        items = c.get('browse_items', [])
        index = max(0, min(c.get('browse_index', 0), len(items)-1))
        text(0, 2, 0, 'Materialien', 180)
        text(0, 198, 0, '%d/%d' % (index+1 if items else 0, len(items)), 57)
        start = max(0, min(index-2, len(items)-5))
        for row, item in enumerate(items[start:start+5]):
            text(0, 2, 12+row*10, '%03d %s' % (start+row+1, item.get('label', '')), 250, start+row == index)
        if items:
            item = items[index]
            picture(1, item, (0, 12), (50, 50))
            text(1, 0, 0, 'BROWSE  %03d' % (index+1), 250)
            text(1, 57, 13, item.get('label', ''), 198)
            text(1, 57, 25, item.get('category') or 'Material', 198)
            assignment = item.get('assignment') or item.get('pad_label')
            if not assignment and item.get('assignments'):
                assignment = ', '.join('%s/%02d' % (chr(65+a['group']), a['pad']+1) for a in item['assignments'])
            if not assignment and item.get('bank') is not None:
                assignment = '%s / Pad %02d' % (chr(65+item['bank']), item.get('pad_index', 0)+1)
            text(1, 57, 37, assignment or 'Keinem Pad zugeteilt', 198, f=small)
            text(1, 57, 51, 'Druecken: auswaehlen', 198, f=small)
    elif screen == 'pad_grid':
        cards = c.get('cards', snapshot.get('cards', []))
        for i in range(16):
            # Physical 4x4 pad ordering; each display holds two columns.
            index = physical_pad(i)
            side, x, y = (i%4)//2, (i%2)*128, (i//4)*16
            card = cards[index] if index < len(cards) else {}
            selected = index == c.get('pad_index', 0)
            draws[side].rectangle((x, y, x+126, y+14), outline=1, fill=1 if selected else 0)
            label = '%s%02d %s' % (chr(65+c.get('bank', 0)), index+1, card.get('label') or 'Leer')
            text(side, x+3, y+3, label, 121, selected, f=small)
    elif screen in ('pad_menu', 'confirm_assign', 'confirm_delete', 'confirm_edit'):
        confirm = c.get('confirm') or {}
        cards = c.get('cards', snapshot.get('cards', []))
        selected = c.get('pad_index', 0)
        selected_card = cards[selected] if selected < len(cards) else {}
        text(0, 3, 2, 'PAD %s%02d' % (chr(65+c.get('bank', 0)), c.get('pad_index', 0)+1), 249)
        text(0, 3, 19, confirm.get('label') or selected_card.get('label') or 'Pad bearbeiten', 249)
        text(0, 3, 48, 'Drehen: waehlen / Druecken: OK', 249, f=small)
        options = confirm.get('options') or c.get('options') or c.get('menu') or []
        choice = confirm.get('choice', c.get('choice', 0))
        for i, option in enumerate(options[:5]):
            text(1, 5, 4+i*12, option.get('label', '') if isinstance(option, dict) else option, 244, choice == i)
    else:
        tabs()
        parameters()
        if c.get('mode') == 'show' and screen != 'pad_edit':
            show = c.get('show') or {}
            text(0, 2, 11, material.get('label') or 'Kein Material', 151)
            text(0, 195, 11, 'Show Mode', 60, f=small)
            elapsed, duration = show.get('elapsed', 0), show.get('duration', 0)
            status = 'Playing' if show.get('playing') else 'Paused' if show.get('state', show.get('status')) == 'paused' else 'Stopped'
            text(0, 2, 22, '%s  %ss / %ss' % (status, _number(round(elapsed, 1)), _number(round(max(0, duration-elapsed), 1))), 211, f=small)
            # Dynamic transition tile: icon remains legible as its background fills.
            d = draws[0]
            d.rectangle((218, 22, 253, 36), outline=1)
            icon = str(show.get('transition', 'fade')).lower()
            images[0].paste(transition_tile(icon, show.get('transition_progress', 0)), (220, 24))
            bar(0, (2, 38, 253, 43), show.get('progress', 0))
            # LCD is monochrome: entry vertical ticks, exit diagonal ticks.
            total = max(.001, float(duration))
            inlet = min(248, int(248*float(show.get('transition_in', show.get('transition_duration', 0)))/total))
            outlet = min(248, int(248*float(show.get('transition_out', show.get('transition_duration', 0)))/total))
            for x in range(4, 4+inlet, 4):
                d.line((x, 38, x, 43), fill=0)
                d.point((x, 37), fill=1)
            for x in range(252-outlet, 252, 4):
                d.line((x, 43, x+3, 39), fill=0)
                d.point((x, 44), fill=1)
            fields = [('duration', 'Len '+_number(round(duration, 1))+'s', 2, 70),
                      ('transition', str(show.get('transition', 'fade')), 76, 101),
                      ('transition_duration', _number(show.get('transition_duration', 0))+'s', 183, 70)]
            for field, label, x, width in fields:
                text(0, x, 51, label, width, show.get('focus') == field and bool(show.get('editing')), f=small)
                if show.get('focus') == field:
                    d.line((x, 62, x+width-2, 62), fill=1)
        else:
            picture(0, material, (1, 12), (50, 50))
            text(0, 176, 12, 'PAD EDIT' if screen == 'pad_edit' else 'Material Mode', 79, f=small)
            text(0, 56, 26, material.get('label') or 'Kein aktives Material', 195)
            sets = page.get('label', 'TD')+' / '+str(len(pages))+' Sets'
            if c.get('parameter_overflow', 0):
                sets += ' +%d weitere' % c['parameter_overflow']
            text(0, 56, 43, sets, 195, f=small)
            if screen == 'pad_edit':
                text(0, 56, 54, 'Entwurf - nicht live', 195, f=small)
    if c.get('error'):
        draws[0].rectangle((0, 53, 255, 63), fill=0)
        text(0, 2, 54, c['error'], 251, f=small)
    return images


class Surface:
    def __init__(self, post, event_callback=None):
        self.post = post
        self.event_callback = event_callback
        self.snapshot = None
        self.status = 'MK2 wird verbunden …'
        self.frames = ()
        self.frame_version = 0
        self.writes = 0
        self.presses = 0
        self.halt = threading.Event()
        self.thread = threading.Thread(target=self.run, name='MaschineMK2', daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self.halt.set()

    def run(self):
        dependencies()
        try:
            import hid
            from PIL import Image
        except ImportError as error:
            self.status = 'MK2-Bibliothek fehlt: '+str(error)
            return
        while not self.halt.is_set():
            device = None
            try:
                devices = [d for d in hid.enumerate(0x17cc, 0x1140) if d['interface_number']==2]
                if not devices:
                    raise OSError('MASCHINE MK2 nicht gefunden')
                device = hid.device()
                device.open_path(devices[0]['path'])
                device.set_nonblocking(True)
                edges, controls, sent, next_render = PadEdges(), ControlEdges(), {}, 0
                flashes = {}
                while not self.halt.is_set():
                    snapshot = self.snapshot
                    for _ in range(64):
                        report = device.read(256)
                        if not report:
                            break
                        for index in edges.read(report):
                            if snapshot:
                                self.post(index, snapshot['version'])
                                self.presses += 1
                                flashes[index] = time.monotonic()+.22
                        if self.event_callback and snapshot:
                            for event in controls.read(report):
                                self.event_callback(event, snapshot['version'])
                    # Repaint time-varying progress, values and blink at 8 Hz.
                    # Identical USB bands and LEDs are still suppressed below.
                    if snapshot and time.monotonic() >= next_render:
                        frames = render(snapshot)
                        packets = [p for side, frame in enumerate(frames) for p in display_packets(side, frame.tobytes())]
                        packets.append(pad_lights(dict(snapshot, _pad_flash_until=flashes)))
                        if snapshot.get('controller'):
                            packets.extend(button_lights(snapshot))
                        for packet in packets:
                            address = (packet[0], packet[3] if packet[0] >= 0xe0 else 0)
                            if sent.get(address) != packet:
                                # Windows HID pads shorter reports to the maximum
                                # output size (265), including the 49-byte RGB report.
                                if device.write(packet) < len(packet):
                                    raise OSError('Unvollständige USB-Übertragung')
                                sent[address] = packet
                                self.writes += 1
                        pngs = []
                        for frame in frames:
                            data = BytesIO()
                            frame.save(data, format='PNG')
                            pngs.append(data.getvalue())
                        if self.frames != tuple(pngs):
                            self.frames = tuple(pngs)
                            self.frame_version += 1
                        next_render = time.monotonic()+.125
                        self.status = 'MK2 verbunden · Displays übertragen'
                    self.halt.wait(.01)
            except Exception as error:
                self.status = 'MK2: '+str(error)
            finally:
                if device:
                    device.close()
            self.halt.wait(1)
        self.status = 'Direkte MK2-Anbindung aus'
