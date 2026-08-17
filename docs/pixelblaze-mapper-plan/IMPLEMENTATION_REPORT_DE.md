# Abschlussbericht – Pixelblaze Portable Mapper

Stand: 13. August 2026

## Ergebnis

Die portable Mapping-Kette ist umgesetzt und live in das TouchDesigner-Projekt
integriert:

```text
Pixelblaze JSON / JS ─┐
                     ├─> map_raw -> Fill/Contain -> map_normalized
MariMapper CSV ──────┘                         ├─> animierte 3D-Vorschau
                                              └─> Guard -> map_active -> LED/DMX
```

TouchDesigner-Komponente:

```text
/project1/pixelblaze_mapper
```

Produktionspfad nach erfolgreichem Apply:

```text
/project1/pixelblaze_mapper/map_active_out
  -> /project1/selectDat
  -> /project1/evaluate1
  -> /project1/LedMap
  -> Vorschau / 22 Art-Net-Universen
```

## Umgesetzte Funktionen

- Windows-Open-File-Dialoge für Pixelblaze und MariMapper.
- Pixelblaze-JSON inklusive Kommentaren und trailing commas.
- Pixelblaze-JavaScript-Generatoren über opt-in Node-Adapter mit 500-ms-VM-Limit,
  deaktivierter dynamischer Codegenerierung und 2-s-Prozesslimit.
- MariMapper-CSV mit indexbasierter Sortierung, Lücken, Zusatzfeldern und
  `x,y,z` sowie TouchDesigner-Kompatibilität `tx,ty,tz`.
- Pixelblaze-JSON- und MariMapper-CSV-Export aus unveränderten Rohkoordinaten.
- Fill und Contain als nicht-destruktive Ableitungen.
- 3D-Punktvorschau mit isometrischer, Front-, Seiten- und Draufsicht.
- Live-RGB-Anbindung an `/project1/null5`; unterstützt Wertebereiche `0..1`,
  `0..255` und den vorhandenen Projektbereich `0..65025`.
- Animierte Ersatzfarben, falls kein RGB-CHOP angeschlossen ist.
- Strikter 3.714-Pixel-Apply-Guard mit Rollback.
- Eingebettete Vorschau direkt in der Mapper-Oberfläche.

## Verifizierte Testfälle

### 1. BallsMatrix3 mit Indexlücken

- 935 vorhandene CSV-Zeilen erkannt.
- Ausgabegröße 938.
- Indizes 894, 895 und 896 als `[0,0,0]` eingesetzt.
- CSV- und Pixelblaze-JSON-Export erneut eingelesen.
- Apply wegen `938 != 3714` blockiert.
- `/project1/selectDat` blieb während dieses Tests an der bisherigen
  Produktionsquelle.

Belege:

- [Guard in der UI](07-ballsmatrix-guard-ui.png)
- [3D-Vorschau der BallsMatrix](08-ballsmatrix-preview.png)

### 2. Pixelblaze-JavaScript-Generator

- Generatorfunktion mit `pixelCount=3714` materialisiert.
- 3.714 konsistente 3D-Koordinaten erzeugt.
- Erste Position `(0.0, 0.5, 0.5)`.
- Letzte X-Position `0.9997307485`.
- Anschließend ohne Produktionsänderung auf das aktive Mapping zurückgesetzt.

### 3. Live-Integration

- Aktive Mappinggröße: 3.714.
- `/project1/null4`: 3.714 Samples.
- `/project1/null5`: 3.714 RGB-Samples.
- Maximale Koordinatenabweichung gegenüber der vorherigen aktiven Quelle: `0.0`.
- Mapper-Komponente: 0 Node-Fehler.
- Produktionsquelle: `/project1/pixelblaze_mapper/map_active_out`.

Belege:

- [Fertige Live-Oberfläche](09-final-live-ui.png)
- [Fertige Live-3D-Vorschau](10-final-live-preview.png)

### 4. Automatisierte Python-Tests

`python -m unittest discover -s tests -v`

Ergebnis: **14/14 Tests erfolgreich**.

Abgedeckt sind Parsing, ungültige Werte, gemischte Dimensionen, Kommentare,
trailing commas, Indexlücken, Metadaten, Roundtrips, Fill/Contain,
2D-zu-CSV und sichere JS-Materialisierung.

## Bekannte Altfehler außerhalb des Mappers

Der neue Mapper selbst meldet 0 Fehler. In `/project1` existieren weiterhin 18
bereits vor der Implementierung vorhandene Meldungen, darunter fehlende
`websockets`- und `scipy`-Module sowie zwei Script-CHOPs ohne `onCook`. Diese
gehören nicht zur Mapper-Komponente und wurden nicht verändert.

## Sicherung

Vor Beginn wurde eine unveränderte Projektkopie angelegt:

```text
backups/3D-Mapper-DMX-Artnet_GRB-Pixelblaze.LEDAnimation.Python.20_pre_pixelblaze_mapper_2026-08-13.toe
```

SHA-256:

```text
38AF862634A718178B5508E062C2A6DF20E591C16138CCE730AAA5D547F66EE8
```

