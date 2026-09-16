"""C1 - LED-Abtastpunkte vektorisieren.

Befund: /project1/effect_sample_uv_callbacks lief als Python-Schleife ueber
alle 7646 LEDs mit vier table[row, name]-Zugriffen je LED - rund 30.000
Zellenzugriffe pro Cook, gemessen 261 ms. Der Knoten kocht bei jeder
Aenderung von Coordinatemode oder Hybridmix und blockierte dabei den
Hauptthread: auf der Installation ein sichtbarer Aussetzer.

Neu: die vier Spalten werden einmal gelesen und mit NumPy kombiniert.
Gemessen nach der Aenderung: 34 ms, also rund Faktor 7,7.

WICHTIG - scriptOp.copyNumpyArray() ist hier eine Falle. Der erste Versuch
nutzte sie, weil sie der schnellste Weg waere. Sie ersetzt aber die Kanaele
und benennt sie in chan1/chan2/chan3 um. Die Werte waren korrekt, die Namen
nicht - und die gesamte nachgelagerte Kette referenziert tx/ty/tz. Das waere
ein stiller Totalausfall der LED-Abtastung gewesen, sichtbar nur daran, dass
nichts mehr leuchtet. Deshalb Zuweisung ueber chan.vals.

Verifikation am laufenden System:
  - Ausgabe vor und nach der Aenderung ueber SHA-256 aller Kanalwerte
    verglichen: bitgleich (tx, ty, tz).
  - Zusaetzlich alle fuenf Modus-/Blend-Kombinationen (panel, hybrid bei
    0.0/0.37/1.0, global) alte gegen neue Rechnung: maximale Abweichung 0.0.

Der Callback-Text liegt daneben als .txt, damit er diffbar bleibt und nicht
in einem Python-String versteckt ist:
    C1_effect_sample_uv_callbacks.txt           (neu, aktiv)
    C1_effect_sample_uv_callbacks_original.txt  (Original, fuer revert)
"""
import pathlib

TARGET = '/project1/effect_sample_uv_callbacks'
PROBE = '/project1/effect_sample_uv'
HERE = pathlib.Path(__file__).parent


def _load(name):
    return (HERE / name).read_text(encoding='utf-8')


def apply():
    op(TARGET).text = _load('C1_effect_sample_uv_callbacks.txt')
    op(PROBE).cook(force=True)
    return f'{TARGET} vectorised, cookTime now {round(op(PROBE).cookTime, 1)} ms'


def revert():
    op(TARGET).text = _load('C1_effect_sample_uv_callbacks_original.txt')
    op(PROBE).cook(force=True)
    return f'{TARGET} restored, cookTime now {round(op(PROBE).cookTime, 1)} ms'
