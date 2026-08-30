# P1: Materialzustand und echte Panel-UVs

Stand: 26. August 2026. Grundlage sind die freigegebenen Entscheidungen in
`P0_P1_APPROVED_DECISIONS_DE.md`.

## Materialphase und Zustand

`pixelblaze_mapper/material_state.py` enthält die offline testbare Logik. Die
Phase wird aus der seit dem letzten Tick vergangenen Zeit integriert:

`neue Phase = alte Phase + Delta-Zeit × Material-Speed × Global Master Speed`

Eine Speed-Änderung schreibt deshalb nur die künftige Steigung um und verändert
nicht rückwirkend die bereits erreichte Phase. Der Global Master Speed startet
mit `1,0` und folgt derselben Kontinuitätsregel.

Für jeden Materialschlüssel (`core:<id>` bzw. `madmapper:<id>`) werden getrennt
gespeichert:

- Speed, Scale und Width
- Focus X/Y und Frame Zoom
- Gradient-Preset sowie Color A/B
- Koordinatenmodus (`global`, `panel`, `hybrid`)
- aktuelle, beim Verlassen pausierte Materialphase

Der idempotente TouchDesigner-Adapter ist
`pixelblaze_mapper/build_p1_material_state.py`. Er erzeugt
`/project1/material_state_runtime`, `/project1/material_state_table` und den
Parameter-/Frame-Callback. Der Builder speichert keine `.toe`-Datei und ändert
keine Netzwerkausgabe.

Importierte MadMapper-Materialien erhalten die integrierte Phase über
`uTDMaterial0.x`. Derselbe Vektor transportiert Scale, Width und Frame Zoom;
`uTDMaterial1.xy` transportiert Focus X/Y. Die Vektorbindung ersetzt die frühere
einzelne `uTDTime`-Konstante, die in TouchDesigner nicht zuverlässig aktualisiert
wurde und importierte Animationen dadurch stehen lassen konnte. Alte
`prepared.frag`-Dateien werden anhand ihrer Adapter-Versionsmarke erkannt und
vor der Verwendung automatisch aus dem Originalshader aktualisiert.

Der aktive `MaterialStateStore` liegt zusätzlich im Laufzeitspeicher von
`/project1`. Das ist erforderlich, weil TouchDesigner ein Text-DAT-Modul beim
erneuten Zugriff neu ausführen kann. Ohne diesen Speicher würde das Modul seine
Zeitbasis bei jedem Zugriff neu setzen und die Phase bliebe praktisch bei null.
Die Tabelle bleibt die serialisierbare Projektkopie. Das Execute DAT überträgt
die fortlaufende Phase pro Frame als Konstantwert und erzwingt nur bei einer
aktiven importierten Quelle deren GPU-Cook; Art-Net/DMX wird dabei nicht
verändert.

## Echte lokale UVs und Panel-IDs

`pixelblaze_mapper/effect_surface_uv.py` leitet aus der bestehenden geprüften
globalen UV-Projektion pro physischem Panel eigene 0–1-Koordinaten ab. Die
Grenzen stammen ausschließlich aus dem kanonischen LED-Vertrag:

| Panel-ID | Name | LED-Indizes |
|---:|---|---:|
| 0 | middle | 0–516 |
| 1 | upper | 517–785 |
| 2 | lower | 786–1183 |
| 3 | rear | 1184–3743 |

`pixelblaze_mapper/build_effect_surface_uv.py` schreibt diese Daten in
`/project1/pixelblaze_mapper/effect_panel_uv`. Der Live-Sampler wählt daraus:

- `global`: geprüfte Raum-UV
- `panel`: echte, innerhalb des jeweiligen Panels normalisierte UV
- `hybrid`: Blend zwischen beiden über `Hybrid Mix`

Das frühere künstliche 2×5-Raster wurde aus den Core- und adaptierten
MadMapper-Shadern entfernt. Nur der per-LED-Sampler kennt die reale Panel-ID;
der 512×512-Rohmaterialshader kann sie nicht zuverlässig erraten.

## Sichere Integrationsreihenfolge

1. Offline-Tests ausführen.
2. `pixelblaze_mapper/build_p1_material_state.py` in der geprüften Core-70-
   Arbeitskopie ausführen.
3. `pixelblaze_mapper/build_effect_surface_uv.py` ausführen.
4. Materialwechsel, Speedänderung und alle drei Koordinatenmodi in der Vorschau
   prüfen.
5. Hardwareausgabe erst anschließend und beaufsichtigt abnehmen.
