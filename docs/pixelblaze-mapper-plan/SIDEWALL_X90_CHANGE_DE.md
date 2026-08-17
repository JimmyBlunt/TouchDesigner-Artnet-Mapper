# Seitenwand-Mapping aufgerichtet und räumlich eingeordnet

Stand: 13. August 2026

## Korrigiertes Ergebnis

Die erste Zwischenlösung (`+90° um X`) wurde durch eine orthografische Prüfung
gegen das Referenzdiagramm als unzureichend erkannt: In der geforderten
Seitenansicht `ZY` erschienen die Motive dabei als diagonale Streifen.

Die aktive Lösung verwendet deshalb die ursprüngliche, gesicherte Map und
ordnet ihre Achsen passend zum Raum neu zu:

```text
neu X = 0.94 + (alt Y - 0.5) * 0.04
neu Y = 1 - alt Z
neu Z = alt X
```

- Indizes `0–1153`: bestehendes Kontur-Mapping auf der rechten Seitenwand.
- `X=0.92…0.96`: schmale Wandebene mit kleiner gemessener Relief-Tiefe.
- `Y=0…1`: aufrechte Raumhöhe.
- `Z=0…1`: Tiefe von vorderer Kontur bis Rückwand.
- Indizes `1154–3713`: zehn Matrix-Panels unverändert auf `Z=1`.

## Gegen das Referenzdiagramm geprüft

- Front `XY`: Panels frontal; Seitenwand rechts kantenförmig.
- Seite/Tiefe `ZY`: drei vollständige, aufrechte Konturmotive.
- Unteres Motiv vorne, mittleres Motiv in der Tiefe, oberes Motiv hinten.
- Alle zehn Panels: zwei Spalten × fünf Reihen.
- Pixel 0 liegt bei jedem Panel unten rechts.
- Pixelanzahl, Indizes, GRB-Reihenfolge und DMX-Routing bleiben unverändert.

Kontrollbild: `sidewall-reference-layout-verified.png`

## Portable Dateien

- Original-Sicherung: `mappings/backups/mapping_before_sidewall_upright_x90.json`
- Korrigierte Map: `mappings/mapping_sidewall_upright_reference_layout.json`
- Korrigierte CSV: `mappings/mapping_sidewall_upright_reference_layout.csv`

Beim Apply muss `Preserve room coordinates` aktiv sein. Dadurch werden die
bereits absoluten Raumkoordinaten nicht erneut durch Fill oder Contain
normalisiert.
