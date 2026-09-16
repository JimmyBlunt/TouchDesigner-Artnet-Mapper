"""D1 - Echte Schwarzschaltung beim Stoppen.  AKTIV UND LIVE VERIFIZIERT.

Der schwerwiegendste Befund der Analyse. Heute macht stop() im Sender genau
drei Dinge: _enabled auf False, Namensliste leeren, Socket schliessen. Es
wird kein einziges Paket mehr gesendet.

Art-Net ist zustandslos. Ein Empfaenger haelt sein zuletzt empfangenes Bild,
unbegrenzt. Das heisst: Klick auf ALL OUTPUTS OFF, Ausnahme im Sendetakt,
Netzwerkausfall oder Absturz von TouchDesigner - in allen vier Faellen
bleibt die Wand stehen wie sie war. Bei einem hellen Standbild also volle
Leistung, unbeaufsichtigt, ohne laufende Steuerung.

Der externe Worker macht es bereits richtig (external_packet_sender, finally-
Block): er sendet jedes beruehrte Universum zweimal schwarz, bevor er den
Socket schliesst. Dieser Schritt gibt dem prozessinternen Sender dieselbe
Zusage.

Umsetzung:
  - _sent_universes merkt sich je Controller (Ziel, Basis-Universum, Anzahl),
    eine Eintragung pro Controller und Tick statt pro Paket.
  - _blackout_sent_universes() sendet genau diese Universen zweimal mit
    510 Nullbytes, mit begrenztem Socket-Timeout und Fehlern, die den Stopp
    nicht verhindern duerfen.
  - stop() ruft das auf, bevor der Socket geschlossen wird.

Nebenwirkung, bewusst in Kauf genommen: wird der Sender neu konfiguriert
(set_enabled ruft intern stop()), blitzt die Wand kurz schwarz. Das ist der
richtige Preis fuer die Garantie, dass ein Stopp auch wirklich aus bedeutet.

LIVE-TEST AM 17.09.2026, mit eingeschalteter Anlage und Sicht auf die Wand:

    vor dem Stopp adressiert   59 Universen auf 3 Controllern
        10.0.0.244:6454        Universen 0..23    (WS2812_NODE)
        10.0.0.253:6454        Universen 120..152 (BACK_PANEL_249)
        10.0.0.251:6454        Universen 156..157 (PANEL8_251)
    Blackout-Pakete gesendet   118   (59 Universen x 2, wie vorgesehen)
    stop()                     sauber, kein Fehler, _sent_universes geleert
    Wand                       dunkel - vom Betreiber bestaetigt

Damit ist der schwerwiegendste Befund der Analyse behoben: ein Stopp bedeutet
jetzt tatsaechlich aus, nicht eingefroren.
"""

TARGET = '/project1/multi_controller_output/artnet_510_sender_callbacks'

HELPER = '''# BLACKOUT_ON_STOP_V1
_sent_universes = {}

def _blackout_sent_universes(repeats=2):
    """Switch every universe this session addressed to zero before closing.

    Art-Net is stateless: a receiver holds its last frame indefinitely, so
    closing the socket freezes the installation instead of turning it off.
    The external worker already does exactly this in its finally block; this
    gives the in-process sender the same guarantee.
    """
    if _socket is None or not _sent_universes:
        return 0
    blank = bytes(510)
    sent = 0
    try:
        _socket.settimeout(.2)
    except Exception:
        pass
    for repeat in range(max(1, repeats)):
        for (target, base), count in list(_sent_universes.items()):
            for offset in range(count):
                try:
                    _socket.sendto(_packet(base + offset, blank), target)
                    sent += 1
                except Exception:
                    pass
        try:
            if isinstance(_socket, ExternalSocket):
                _socket.flush()
        except Exception:
            pass
        if repeat == 0:
            time.sleep(.05)
    return sent

'''

OLD_STOP = """def stop():
    global _socket, _enabled, _active_names
    _enabled = False
    _active_names = []
    if _socket is not None:
        try:
            _socket.close()
        except Exception:
            pass
    _socket = None"""

NEW_STOP = """def stop():
    global _socket, _enabled, _active_names
    _enabled = False
    _active_names = []
    if _socket is not None:
        # BLACKOUT_ON_STOP_V1: switch off before closing, never just walk away.
        try:
            _blackout_sent_universes()
        except Exception:
            pass
        try:
            _socket.close()
        except Exception:
            pass
    _socket = None
    _sent_universes.clear()"""

OLD_TICK = """                _socket.sendto(_packet(config['universe'] + offset, payload), target)
                sent_packets += 1
        if isinstance(_socket, ExternalSocket):"""

NEW_TICK = """                _socket.sendto(_packet(config['universe'] + offset, payload), target)
                sent_packets += 1
            # BLACKOUT_ON_STOP_V1: remember what was actually addressed, one entry
            # per controller per tick, so stop() can switch exactly these off.
            _sent_universes[(target, config['universe'])] = len(frames)
        if isinstance(_socket, ExternalSocket):"""


def apply():
    dat = op(TARGET)
    text = dat.text
    if 'BLACKOUT_ON_STOP_V1' in text:
        return 'already applied'
    for anchor in (OLD_STOP, OLD_TICK):
        if anchor not in text:
            raise RuntimeError('anchor not found - sender source has changed')
    text = text.replace(OLD_TICK, NEW_TICK, 1)
    text = text.replace(OLD_STOP, HELPER + NEW_STOP, 1)
    dat.text = text
    return f'{TARGET} patched - blackout on stop is now ACTIVE'


def revert():
    dat = op(TARGET)
    text = dat.text
    if 'BLACKOUT_ON_STOP_V1' not in text:
        return 'nothing to revert'
    text = text.replace(HELPER + NEW_STOP, OLD_STOP, 1).replace(NEW_TICK, OLD_TICK, 1)
    dat.text = text
    return f'{TARGET} reverted'
