# Integrationsvertrag – Pixelblaze/MariMapper Mapper

Stand: 2026-08-13

## Produktionsgrenze

Die bestehende Kette wird erst in der Integrationsphase umgeschaltet:

```text
/project1/pixelblaze_mapper/map_active
  -> /project1/selectDat
  -> /project1/evaluate1
  -> /project1/LedMap
  -> Preview / DMX
```

`map_active` besitzt exakt die bestehenden Spalten:

```text
index  tx  ty  tz
```

Jede Datenzeile entspricht genau einem LED-Index. Indexlücken werden nicht komprimiert, sondern mit einer Position `[0,0,0]` belegt.

## Interne Tabellen

### `map_raw`

```text
index  x  y  z  state
```

- unveränderte Rohkoordinaten für portable Exporte;
- `state` ist `ok`, `missing` oder `warning`;
- bei echten 2D-Maps bleibt die Dimension separat `2`, intern kann Z für die Vorschau abgeleitet werden.

### `map_normalized`

```text
index  tx  ty  tz  state
```

- abgeleitete Fill-/Contain-Koordinaten;
- wird für Vorschau und nach Apply für `map_active` verwendet;
- Rohwerte werden niemals überschrieben.

### `status`

Zweispaltige Key/Value-Tabelle mit mindestens:

```text
valid
message
source_path
source_kind
pixel_count
dimensions
fit_mode
missing_count
warning_count
dirty
saved
applied
source_sha256
```

## UI-Parameter

```text
Sourcepath       String
Fitmode          Menu: Fill / Contain
Pixelcount       Int, read-only
Dimensions       Int, read-only
Status           String, read-only
Openpixelblaze   Pulse
Openmarimapper   Pulse
Reload           Pulse
Revert           Pulse
Exportpixelblaze Pulse
Exportmarimapper Pulse
Saveprojectcopy  Pulse
Applytoleds      Pulse
```

## Sichere Apply-Regel

Ein Apply ist nur erlaubt, wenn:

- Parserstatus gültig ist;
- alle Koordinaten endlich sind;
- Dimensionen einheitlich sind;
- Pixelzahl für die Produktionskonfiguration ausdrücklich akzeptiert wurde;
- DMX-Routing bei abweichender Pixelzahl nicht stillschweigend verändert wird.

Die aktuelle Produktionsbaseline ist 3.714 Pixel und 22 RGB-Universen.

## Testfixture `BallsMatrix3`

- 935 vorhandene CSV-Datenzeilen;
- Indizes 0 bis 937;
- fehlend: 894, 895, 896;
- erwartete interne/Pixelblaze-Länge: 938;
- erwartete Platzhalter an den drei Lücken: `[0,0,0]`;
- Export benutzt Rohkoordinaten, nicht die abgeleitete Normalisierung.

