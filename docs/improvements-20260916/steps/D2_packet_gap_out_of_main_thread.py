"""D2 - Paket-Abstand aus dem Hauptthread nehmen.  NICHT AKTIVIERT.

Befund: in tick() steht

    if offset and gap and not isinstance(_socket, ExternalSocket):
        time.sleep(gap)

Mit live_packet_gap_ms = {'BACK_PANEL_249': 1.5} und 33 Universen sind das
rund 48 ms time.sleep() pro Frame - im Hauptthread von TouchDesigner. Solange
die Ausgabe laeuft, deckelt das die gesamte Anwendung.

WICHTIGE EINSCHRAENKUNG, die im Analysebericht zu kurz kam: Der Abstand ist
nicht ueberfluessig, er wurde absichtlich eingebaut (sender_packet_gap
.install_source). Der GICO-Empfaenger verwirft nachweislich Universen, wenn
Pakete zu dicht aufeinander folgen - im selben Modul steht der Kommentar zur
Sequenznummer-Kompatibilitaet aus einem echten Hardwaretest. Den Sleep
einfach zu streichen kann bedeuten, dass einzelne Panels ausfallen.

Ich kann nicht aus der Ferne beurteilen, wie deine Hardware darauf reagiert.
Deshalb fuehrt dieser Schritt nur einen Schalter ein und aendert das
Verhalten zunaechst NICHT:

    DIRECT_MODE_PACKET_GAP = True   -> wie bisher (Sleep aktiv, ~20 fps)
    DIRECT_MODE_PACKET_GAP = False  -> kein Sleep, volle Bildrate, Risiko
                                       verworfener Universen beim GICO

Der saubere Weg ist ohnehin ein anderer: im externen Sendeprozess greift der
Abstand, ohne TouchDesigner zu blockieren - dort wartet _wait_until() sogar
praeziser als time.sleep(). Der externe Sender ist derzeit deaktiviert
(external_sender_settings enabled=False), vermutlich wegen der 3139
verspaeteten Sendungen auf 9681 uebermittelte Frames in der letzten
Statistik. Diese Ursache zu klaeren ist der eigentliche Auftrag; dieser
Schalter ist nur die Notloesung fuer den Direktbetrieb.

ZUM AKTIVIEREN: apply() aufrufen (aendert noch nichts), dann den Schalter im
DAT auf False setzen und dabei die Wand beobachten.
"""

TARGET = '/project1/multi_controller_output/artnet_510_sender_callbacks'

FLAG = '''# PER_CONTROLLER_PACKET_GAP_SWITCH_V1
# True  = unveraendertes Verhalten: time.sleep(gap) im TouchDesigner-Hauptthread.
# False = kein Sleep im Direktbetrieb. Volle Bildrate, aber der GICO-Empfaenger
#         kann Universen verwerfen, wenn Pakete zu dicht folgen. Beim Umstellen
#         die Wand beobachten.
DIRECT_MODE_PACKET_GAP = True

'''

OLD = """                if offset and gap and not isinstance(_socket, ExternalSocket):
                    time.sleep(gap)"""

NEW = """                if offset and gap and DIRECT_MODE_PACKET_GAP and not isinstance(_socket, ExternalSocket):
                    time.sleep(gap)"""

ANCHOR = 'def stop():'


def apply():
    dat = op(TARGET)
    text = dat.text
    if 'PER_CONTROLLER_PACKET_GAP_SWITCH_V1' in text:
        return 'already applied'
    if OLD not in text or ANCHOR not in text:
        raise RuntimeError('anchor not found - sender source has changed')
    text = text.replace(OLD, NEW, 1).replace(ANCHOR, FLAG + ANCHOR, 1)
    dat.text = text
    return f'{TARGET}: switch added, behaviour unchanged (still True)'


def set_gap(enabled):
    """Den Schalter umlegen, ohne den Text erneut zu patchen."""
    module = op(TARGET).module
    module.DIRECT_MODE_PACKET_GAP = bool(enabled)
    return f'DIRECT_MODE_PACKET_GAP = {bool(enabled)}'


def revert():
    dat = op(TARGET)
    text = dat.text
    if 'PER_CONTROLLER_PACKET_GAP_SWITCH_V1' not in text:
        return 'nothing to revert'
    dat.text = text.replace(FLAG, '', 1).replace(NEW, OLD, 1)
    return f'{TARGET} reverted'
