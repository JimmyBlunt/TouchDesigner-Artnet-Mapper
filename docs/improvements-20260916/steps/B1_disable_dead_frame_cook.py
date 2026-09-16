"""B1 - Toten Frame-Cook abschalten.

Befund der Analyse: /project1/chopexec1 erzwang bei jeder Wertaenderung
op('script4').cook(force=True). script4 ist ein alter, selbstgenuegsamer
Flacker-Effekt (NUM_LEDS = 1152 gegen real 5545 adressierte LEDs), hat
keinen einzigen Ausgang und keine Seiteneffekte ausser auf den eigenen
scriptOp. Zaehlerstand bei Abschaltung: chopexec1 1.133.077 Cooks,
script4 2.102.062 Cooks - vollstaendig ins Leere gerechnet.

Der Knoten selbst bleibt erhalten; nur der erzwungene Cook entfaellt.
"""

TARGET = '/project1/chopexec1'


def apply():
    op(TARGET).par.active = False
    return f'{TARGET}.active = False'


def revert():
    op(TARGET).par.active = True
    return f'{TARGET}.active = True'
