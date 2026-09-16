"""D2 - Paket-Abstand abgeschaltet.  AKTIV UND LIVE VERIFIZIERT.

Befund: in tick() stand

    gap = seconds(me.parent().fetch('live_packet_gap_ms', {}), config['name'])
    if offset and gap and not isinstance(_socket, ExternalSocket):
        time.sleep(gap)

Mit live_packet_gap_ms = {'BACK_PANEL_249': 1.5} und 33 Universen sind das
rund 49 ms Schlaf pro Sendezyklus im Hauptthread.

WAS DIE LIVE-MESSUNG KORRIGIERT HAT: Der Bericht nahm an, das deckle die
Bildrate von TouchDesigner. Das stimmt nicht - TouchDesigner lief waehrend
des gesamten Tests mit 54 bis 59 fps. Gedeckelt wurde die AUSGABE: die Wand
wurde nur rund neunmal pro Sekunde aktualisiert, gegen 30 bis 60 Hz laut
Konfiguration.

UMSETZUNG - EINFACHER ALS GEPLANT: Urspruenglich war ein Code-Patch mit einem
Schalter DIRECT_MODE_PACKET_GAP vorbereitet. Der ist nicht noetig und wurde
verworfen. Der Abstand kommt ohnehin aus dem Storage-Wert live_packet_gap_ms;
ihn dort zu leeren schaltet den Sleep ab, ohne eine Zeile Code zu aendern.

Das ist aus einem konkreten Grund der bessere Weg: Ein Patch am Text des
Sender-DATs laedt das Modul neu, waehrend es laeuft - dabei geht der offene
Socket verloren, und zwar ohne Blackout. Genau der Fehlerfall, den D1 gerade
behoben hat. Der Storage-Wert laesst den laufenden Sender unberuehrt.

LIVE-TEST AM 17.09.2026, Anlage in Betrieb, Betreiber vor der Wand:

                        vorher        nachher
    Ausgabe-Frames      7,7-9,2/s     20,3/s        (2,4x)
    Pakete              ~460/s        1187/s
    send_ms pro Zyklus  90,5 ms       34,7 ms
    TouchDesigner       58 fps        59,5 fps      (unveraendert)
    Fehler              0             0
    rate_skips          0             2 in 54 s

    Wand nach 54 s Dauerlauf: unauffaellig, kein Flackern, keine toten
    Bereiche an BACK_PANEL_249 - vom Betreiber bestaetigt.

Die Sorge, der GICO-Empfaenger koenne bei dichteren Paketen Universen
verwerfen, hat sich auf dieser Hardware nicht bestaetigt. Sollte sie spaeter
doch auftreten - einzelne Panels flackern oder fallen aus - genuegt revert().

NOCH OFFEN: 34,7 ms pro Sendezyklus sind jetzt reine Rechen- und Sendezeit.
Sie deckeln bei etwa 30 Ausgabebildern. Fuer die konfigurierten 60 Hz auf dem
WS2812 muesste die Paketierung selbst schneller werden, oder der externe
Sendeprozess die Arbeit uebernehmen.
"""

ROUTER = '/project1/multi_controller_output'
KEY = 'live_packet_gap_ms'
PREVIOUS = {'BACK_PANEL_249': 1.5}


def apply():
    op(ROUTER).store(KEY, {})
    return f'{KEY} = {{}} - packet gap off, sender untouched'


def revert():
    op(ROUTER).store(KEY, dict(PREVIOUS))
    return f'{KEY} = {PREVIOUS} - packet gap restored'


def current():
    return op(ROUTER).fetch(KEY, {})
