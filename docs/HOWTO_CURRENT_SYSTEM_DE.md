# How-to: TouchDesigner Art-Net Mapper

Stand: 22. August 2026 · Arbeitsstand: `PixelblazeMapper_WORKING_PHASE2_EFFECTS_CORE.53.toe`

## 1. Sicher starten

1. TouchDesigner öffnen.
2. `PixelblazeMapper_WORKING_PHASE2_EFFECTS_CORE.53.toe` laden.
3. Im Network Editor `/project1` öffnen.
4. Prüfen, dass diese vier Ausgänge `Active = Off` zeigen:
   - `/project1/dmxout1`
   - `/project1/esp_artnet_out`
   - `/project1/multi_controller_output/dmxout_ws2812_node`
   - `/project1/multi_controller_output/dmxout_apa102_esp`
5. Für die neue Bedienung `/project1/multi_controller_output/ui_preview` mit Rechtsklick → **View** öffnen.

Der gespeicherte Stand erfüllt diese Bedingungen bereits. Helligkeit `0.02`
bedeutet 2 %, aber beide neuen Empfänger stehen auf `Enabled=0`.

## 2. Systemfluss

```mermaid
flowchart LR
    FX["25 GLSL-Effekte"] --> VS["Visual Source Switch"]
    SHOW["Show-Sequencer A/B"] --> VS
    VS --> PRE["3D-LED-Vorschau"]
    PRE --> RGB["/project1/math1\n3740 RGB-Pixel"]
    RGB --> WS["WS-Packer\n0..511"]
    RGB --> APA["APA-Packer\n512..1678"]
    WS --> N244["10.0.0.244\nU0..U3"]
    APA --> N251["10.0.0.251\nU0..U9"]
```

Jedes Universum enthält 510 Werte = 170 RGB-Pixel. Die Universen dürfen bei
verschiedenen IP-Adressen wieder bei 0 beginnen. Innerhalb derselben IP werden
Überlappungen blockiert.

## 3. UC-01 · Effekt mit der Maus wählen

1. `/project1/material_browser` öffnen.
2. Den Viewer aktivieren (**Viewer Active**).
3. Optional mit `SOURCE`, `GROUP` oder dem Suchfeld filtern.
4. Mit `VIEW: 4 x 2` bzw. `VIEW: 8 x 4` zwischen großen und kompakten Karten wechseln.
5. Eine Core- oder importierte MadMapper-Karte direkt anklicken.
6. Kontrollieren, dass die Statuszeile `ACTIVE CORE MATERIAL` beziehungsweise
   `ACTIVE IMPORTED MATERIAL` anzeigt und die 3D-Vorschau denselben Effekt auf
   Rückwand und Seiten zeigt.

![Gemeinsamer Material-Browser in der 8×4-Ansicht](images/unified_material_browser_8x4.png)

Erwartung: Core-Karten setzen `Source = materials`. Eine automatisch vorbereitete
Importkarte setzt `Source = imported`; der zusätzliche Eingang liegt auf Index 3.
Die bisherigen Indizes Movie 0, Core 1 und Show 2 bleiben unverändert.

Die verbindliche Fotoansicht wird mit `Strg+Umschalt+1` geöffnet. Das Hintergrundbild
läuft unter der Non-Commercial-Lizenz proportional mit 648×1280 Pixeln und ohne
Hardware-Decoding. Dadurch bleibt die 810×1600-Quelldatei sichtbar, ohne das
1280-Pixel-TOP-Limit zu überschreiten.

![LED-Vorschau mit wiederhergestelltem Hintergrundfoto](images/led_preview_background_fixed.png)

## 4. UC-02 · Koordinatenmodus wählen

Im Control COMP `/project1/madmapper_player_controls` den Parameter
`Coordinate Mode` setzen:

| Wert | Verhalten |
|---|---|
| `global` | ein zusammenhängendes Bild über die komplette Installation |
| `panel_local` | Muster wird pro Panel lokal wiederholt |
| `hybrid` | globale Bewegung mit lokal lesbaren Paneldetails |

Erwartung: Die drei Modi erzeugen unterschiedliche Renderbilder, verändern aber
weder Pixelanzahl noch Art-Net-Routing.

### Laufrichtung auf Rückwand und Seitenwand

Die beiden Flächen liegen auf unterschiedlichen räumlichen Ebenen. Deshalb
verwendet die gemeinsame Effekt-Abtastung folgende feste Projektion:

| Fläche | Effekt-U | Effekt-V / vertikale Laufrichtung |
|---|---|---|
| Rückwand | räumliches Z über zwei Spalten | räumliches X über fünf Reihen |
| Seitenwand | ursprüngliches Y = vorne/hinten | ursprüngliches X = Höhe |

Das ursprüngliche Z der Seitenwand beschreibt nur die geringe Tiefe bzw. das
Relief zur Wand. Weil die Seiten-Geometrie vor dem Rendern um −90° gedreht wird,
müssen X und Y für die 2D-Textur vertauscht werden. Werden die ungedrehten Achsen
verwendet, läuft eine fallende Animation nach vorne oder hinten. Die aktive Korrektur liegt in
`/project1/effect_sample_uv`; ihr reproduzierbarer Builder ist
`pixelblaze_mapper/build_effect_surface_uv.py`.

Abnahme mit **Matrix Rain**: Im Material Player und auf der Rückwand fällt das
Muster von oben nach unten. Auf allen drei Seitenpanels muss dieselbe vertikale
Richtung sichtbar sein. Pixelanzahl, Indexreihenfolge, Universen und Art-Net-
Routing dürfen sich beim Umschalten nicht ändern.

## 5. UC-03 · Zwei Art-Net-Empfänger konfigurieren

1. `/project1/multi_controller_output/ui_preview` öffnen.
2. Für jeden Empfänger folgende Felder anklicken und bearbeiten:
   - **IP address**
   - **Start universe**
   - **Brightness 0..1**
   - **Enabled 0/1**
3. **APPLY SAFE DRAFT** anklicken.
4. Die grüne Statuszeile abwarten: `VALIDATED - draft applied; network outputs remain OFF`.

![Validierter Controller-Editor](screenshots/11-controller-editor-validated.png)

Standardwerte:

| Empfänger | IP | Universen | Quellpixel | Zielpixel | Helligkeit | Enabled |
|---|---:|---:|---:|---:|---:|---:|
| WS2812 NODE | 10.0.0.244 | 0–3 | 0–511 | 0–511 | 0.02 | 0 |
| APA102 ESP | 10.0.0.251 | 0–9 | 512–1678 | 512–1678 | 0.02 | 0 |

Ungültige IPs, Helligkeit außerhalb `0..1`, Universe außerhalb `0..32767`,
falsche Farbreihenfolge, unbekannte Controller oder kollidierende Zielbereiche
werden blockiert. Der bisher gültige Tabellenstand bleibt dabei erhalten.

Erweiterte Werte stehen in den DATs `controller_config` und `segment_config`:
lokale Netzwerkkarte, Port, RGB-Reihenfolge, Rate, ArtSync, Quellbereich,
Zielstart, Reverse und Farb-Override. Danach ebenfalls **APPLY SAFE DRAFT**.

## 6. UC-04 · Art-Net kontrolliert starten und stoppen

1. Zunächst **Brightness = 0.02** oder für einen reinen Verbindungstest `0.0` setzen.
2. Nur bei den gewünschten Empfängern **Enabled = 1** setzen.
3. **APPLY SAFE DRAFT** anklicken.
4. Verkabelung und Stromversorgung prüfen.
5. **START ENABLED** anklicken.
6. Status muss `LIVE - ...` anzeigen.
7. Zum sofortigen Stoppen **ALL OUTPUTS OFF** anklicken.

Wichtig: `START ENABLED` validiert erneut und schaltet zuerst alle Ausgänge aus.
Es startet ausschließlich validierte Zeilen mit `Enabled=1`. Der gespeicherte
Projektstand bleibt `Enabled=0` und alle Ausgänge aus.

## 7. UC-05 · Segment-/Pixelrouting ändern

Für neue Stränge oder weitere Empfänger:

1. `controller_config` um eine eindeutige Controllerzeile erweitern.
2. In `segment_config` eine oder mehrere Segmentzeilen anlegen.
3. `source_start` und `count` beziehen sich auf den 3740-Pixel-Quellstrom.
4. `destination_start` ist der logische Pixelindex im Zielgerät.

Aktuell bestätigte GICO-Hardwarezuordnung der drei Seitenpanels (Art-Net-Anzeige
des Controllers, 170 RGB-Pixel je Universe):

| Panel | LED-Anzahl | Universe | `destination_start` |
|---|---:|---:|---:|
| oben, großer Teil | 170 | 3 | 340 |
| oben, kleiner Rest | 102 | 4 | 510 |
| unten | 399 | 6–8 | 850 |
| Mitte | 509 | 9–11 | 1360 |

Die mittlere Leitung liegt physisch/firmwareseitig nicht auf Universe 1–3.
Dies wurde mit echten Rot/Blau-Universe-Tests am Controller `10.0.0.244`
ermittelt. Universe 9 erzeugte ungefähr ein Drittel Rot und Universe 10–11
zwei Drittel Blau auf dem mittleren Panel.

Der obere Aufbau ist ebenfalls physisch geteilt. Universe-Einzeltests ergaben:
Universe 1, 2 und 5 steuern keinen sichtbaren Teil; der große 170-Pixel-Block
liegt auf Universe 3, die übrigen 102 Pixel auf Universe 4.
5. Optional `reverse=1` oder `color_override=GRB` setzen.
6. Builder ausführen:

```python
exec(open(r'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper/pixelblaze_mapper/build_multi_controller_output.py', encoding='utf-8').read())
```

7. `validation` prüfen; bei `error` bleibt alles aus.

Die vorhandene ESP-Regel `destination_start=512` ist absichtlich: der aktuelle
ESP erwartet vor APA102 genau 512 schwarze WS-Pixel.

## 8. UC-06 · Show abspielen

1. `/project1/show_control/control_panel_preview` öffnen.
2. **PLAY** anklicken.
3. Mit **NEXT**, **PREV** oder **GO** die Cuefolge steuern.
4. **PAUSE** friert die exakte Zeitposition ein; **STOP** setzt auf Cue 1 / 0 s.
5. **LOOP** schaltet die Wiederholung um.
6. **BLACKOUT** setzt die Bildhelligkeit auf 0, ohne den Transport zu verlieren.

![Show Control bei 50 Prozent Crossfade](screenshots/10-show-control-crossfade.png)

```mermaid
stateDiagram-v2
    [*] --> Stopped
    Stopped --> Playing: PLAY
    Playing --> Paused: PAUSE
    Paused --> Playing: PLAY
    Playing --> Stopped: STOP / Ende ohne Loop
    Playing --> Transition: Cue-Ende minus Transitiondauer
    Transition --> Playing: nächster Cue
    Playing --> Playing: NEXT / PREV / GO
```

Der Renderer nutzt zwei Shader-Slots A/B. Unterstützte Übergänge: `cut`,
`crossfade`, `dissolve`, `wipe`, `radial`, `glitch`.

![A/B-Crossfade bei 50 Prozent](screenshots/08-show-crossfade-50-percent.png)

## 9. UC-07 · Eine eigene Show anlegen

`shows/demo_show.json` kopieren und Cues bearbeiten. Pflichtfelder pro Cue:

```json
{
  "id": "particles-room",
  "name": "Particles Across Room",
  "effect": "Particles",
  "preset": "Cyan Magenta",
  "parameters": {
    "speed": 1.15, "scale": 4.0, "width": 0.3,
    "focus_x": 0.5, "focus_y": 0.5, "zoom": 1.0,
    "gradient": "neon_cyan_magenta",
    "color_a": [0.91, 0.0, 1.0, 1.0],
    "color_b": [0.0, 0.72, 0.86, 1.0],
    "intensity": 1.0, "contrast": 1.25, "trail": 0.55,
    "direction": 0.125, "rotation_degrees": 0.0, "seed": 11.0,
    "effect_transition": 0.5,
    "panel_columns": 2.0, "panel_rows": 5.0,
    "hybrid_mix": 0.5, "density": 1.25
  },
  "coordinate_mode": "hybrid",
  "duration": 15.0,
  "transition": "dissolve",
  "transition_duration": 2.0,
  "brightness": 0.2,
  "target_groups": ["middle", "upper", "lower", "rear"]
}
```

Regeln: IDs eindeutig; `duration > 0`; Helligkeit `0..1`; animierte
Transitiondauer `> 0` und nicht länger als die Cue-Dauer; Cut-Dauer exakt 0.
`parameters` ist vollständig erforderlich. Zielgruppen sind ausschließlich
`all`, `middle`, `upper`, `lower` und `rear`; `all` wird nicht kombiniert.

Builder und Live-Verknüpfung:

```python
exec(open(r'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper/pixelblaze_mapper/build_show_sequencer.py', encoding='utf-8').read())
exec(open(r'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper/pixelblaze_mapper/integrate_live_show.py', encoding='utf-8').read())
```

Beide Skripte sind idempotent. Das erste baut die Show-Steuerung; das zweite
verbindet ausschließlich die visuelle A/B-Kette. Es aktiviert kein Art-Net.

## 10. UC-08 · Tests ausführen

In PowerShell:

```powershell
Set-Location C:\Users\jbhtz\TouchDesignerLocal\PixelblazeMapper
python -m unittest discover -s tests
```

Erwartung:

```text
Ran 92 tests
OK
```

Live-Prüfung im Projekt:

```python
print(op('/project1').errors(recurse=True))
```

Erwartung: leere Ausgabe. Für einen sicheren Abschluss müssen alle vier DMX
Out CHOPs `Active=False` zeigen.

## 11. Fehlerbehebung

| Symptom | Prüfung | Lösung |
|---|---|---|
| Materialkarte reagiert nicht | Viewer Active? | Browser-Viewer aktivieren und Karte direkt anklicken |
| Seiten zeigen neuen Effekt, Rückwand nicht | Source / Show-Verknüpfung | `integrate_live_show.py` erneut ausführen; `visual_source_switch` muss 3 Eingänge haben |
| Apply meldet BLOCKED | rote Statuszeile / `validation` | markiertes Feld korrigieren; alter gültiger Stand bleibt erhalten |
| Kein Licht | Enabled, Active, IP, lokale NIC | zuerst 2 % testen; Empfänger aktivieren; `10.0.0.178` als lokale NIC prüfen |
| ESP APA-Ausgabe verschoben | Zielstart | APA-Segment muss bei Zielpixel 512 beginnen |
| Universen kollidieren | Ziel-IP + Universebereich | gleiche Universen sind nur auf unterschiedlichen IPs erlaubt |
| Sofort alles aus | Controller-UI | **ALL OUTPUTS OFF** anklicken |
