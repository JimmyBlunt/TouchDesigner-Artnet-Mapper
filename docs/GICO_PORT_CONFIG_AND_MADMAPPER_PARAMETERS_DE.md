# GICO-Portkonfiguration und dynamische MadMapper-Parameter

## GICO: globale Universenzahl pro Port

Der GICO-Controller verwendet **einen globalen Wert** `Universes per Port` für
alle physischen Ports. Die Portblöcke werden deshalb nicht einzeln frei
vergeben, sondern automatisch berechnet. Bei 510 DMX-Kanälen pro Universe
enthält ein Universe 170 RGB-Pixel.

Bei `Universes per Port = 6` und erstem UI-Universe `1` gilt:

| Port | UI-Universes | Zielstart | Kapazität |
|---|---:|---:|---:|
| 1 | U1–U6 | 0 | 1.020 Pixel |
| 2 | U7–U12 | 1.020 | 1.020 Pixel |
| 3 | U13–U18 | 2.040 | 1.020 Pixel |
| 4 | U19–U24 | 3.060 | 1.020 Pixel |

Die Oberfläche wird im **Art-Net Router** über `GICO PORT CONFIG` oder direkt
mit `Strg+Umschalt+0` geöffnet. Der Shortcut ist reine Navigation: Er verändert
keine Konfiguration und startet keine Ausgabe.
Sie zeigt pro Port Label, Aktivierung, Quellstart, Pixelzahl, Reverse und
Farbreihenfolge. `VALIDATE DRAFT` berechnet die Blöcke. `APPLY SAFE DRAFT`
stoppt zuerst sämtliche Ausgabe, validiert erneut und schreibt nur sichere,
vollständig zugewiesene Portsegmente in den Router.

Port 4 ist mit 896 Pixeln vorbereitet. Solange `Source Start` leer ist, bleibt
er ausdrücklich **nicht geroutet**; die Software erfindet keine Quellindizes.

## Importierte MadMapper-Materialien

MadMapper beschreibt Materialregler in der JSON-Kopfzeile des Shaders unter
`INPUTS`. Beim Import liest der Adapter diese Definitionen und erzeugt daraus
automatisch eine eigene TouchDesigner-Bedienoberfläche. Neue oder nachträglich
ergänzte Inputs erscheinen beim nächsten Refresh/Öffnen automatisch.

Unterstützt werden:

| MadMapper-Typ | Bedienung |
|---|---|
| `float` | Slider |
| `int` | numerischer Slider |
| `bool` | Ein/Aus-Button |
| `event` | Trigger-Button, ein Frame |
| `long` | zyklische Auswahl aus `VALUES` |
| `point2D` | X/Y-Slider |
| `size2D` | Breite/Höhe-Slider |
| `floatRange` | Min/Max-Slider |
| `color` | RGBA-Slider |

Die Shader-Variable `NAME` ist die eindeutige Identität. Dadurch dürfen zwei
Layer beide einen sichtbaren Regler `Speed` besitzen. Die Oberfläche zeigt
beispielsweise `Layer A / Speed [speed_a]` und `Layer B / Speed [speed_b]`.

Der bisherige allgemeine Regler heißt nun `MASTER SPEED`. Er steuert die
gemeinsame Materialzeit. Native Speed-Inputs verändern dagegen gezielt den
jeweiligen Generator oder Layer des importierten Materials.

Jedes Material besitzt einen eigenen gespeicherten Parameterzustand. Bei einer
Shaderänderung bleiben Werte erhalten, wenn `NAME` und Typ gleich bleiben;
neue oder typgeänderte Inputs erhalten ihre neuen Defaults. Parameter mit
`generate_as_define` sind als `RECOMPILE` markiert und werden erst nach
erfolgreicher GLSL-Kompilierung übernommen.

## Sicherheitskorrektur für Hover

Karten-Hover verwendet jetzt `hover_shader` und `hover_preview`. Dieses TOP ist
nicht mit `imported_material_out` verbunden. Nur die explizite Materialauswahl
darf `preview_shader/live_preview` und damit die aktive importierte Ausgabe
ändern.
