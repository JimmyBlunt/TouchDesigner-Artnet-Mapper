# Farbreihenfolge-Test (17.09.2026)

## Muster

`/project1/colororder_test` – ein Constant TOP, 64 x 64, als globale
Materialquelle auf `/project1/topto1` gelegt. Da es eine Vollfläche ist, greift
es unabhängig von UV auf **alle** Flächen: Rückwand-Panels 1–8 und die drei
Seitenflächen.

Zyklus, 2 s je Phase, 8 s gesamt, zeitgesteuert per Parameterausdruck
(`absTime.seconds`, keine zusätzliche Execute-DAT):

| Phase | Farbe | Quelle RGB |
|---|---|---|
| 0 | ROT | 1, 0, 0 |
| 1 | GRÜN | 0, 1, 0 |
| 2 | BLAU | 0, 0, 1 |
| 3 | WEISS | 1, 1, 1 |

## Was das Bild aussagt

Alle Flächen bekommen zeitgleich denselben Quellwert. **Jede Fläche, die eine
andere Farbe zeigt als der Rest, hat die falsche Farbreihenfolge.**

| gesehen statt ROT | Diagnose |
|---|---|
| grün | R und G vertauscht (RGB ↔ GRB) |
| blau | R und B vertauscht (RGB ↔ BGR) |
| rot | korrekt |

Die Weiss-Phase prüft zusätzlich, ob alle drei Kanäle überhaupt ankommen:
eine Fläche mit totem Kanal erscheint dort farbig statt weiss.

## Gemessen in der ROT-Phase (Quelle 1,0,0)

| Controller / Universum | Config | gesendete Bytes | Reihenfolge |
|---|---|---|---|
| `PANEL8_251` U0 – Panel 8 | BGR | 0, 0, 179 | R an Position 3 |
| `PANEL8_251` U2 – Panel 7 | RGB | 179, 0, 0 | R an Position 1 |
| `WS2812_NODE` U0 – Seitenflächen | GRB | 0, 179, 0 | R an Position 2 |
| `BACK_PANEL_249` U0 – Panel 1 | RGB | 77, 0, 0 | R an Position 1 |

Die Software sendet also exakt das, was jede Zeile der Config vorgibt.

**Der interessante Fall:** Panel 7 und Panel 8 hängen am selben Controller
10.0.0.251, bekommen aber gegenläufige Reihenfolgen (RGB gegen BGR). Sind beide
Panels baugleich verdrahtet, ist eine der beiden Zeilen falsch – welche, zeigt
nur das Auge.

## Nebenbefund

Panel 4 und Panel 5 laufen mit Gain 3.33 (aus
`tools/set_panel45_gain_20260915.py`). Bei gesättigten Testfarben clippt das;
der Farbton bleibt richtig, die Flächen wirken nur heller.

## Zurückschalten

Ursprüngliche Materialquelle: `/project1/material_gradient_player`
(auch als Kommentar am TOP hinterlegt und in `material-before-colortest.txt`).
