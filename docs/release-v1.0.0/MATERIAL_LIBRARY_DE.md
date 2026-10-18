# Materialbibliothek: Auslieferung und Herkunft

Die v1.0.0-Auslieferung enthält den vorhandenen Katalog, den zugehörigen
Originalquellstand und alle 638 importierten Materialpakete. Zum Öffnen dieser
Bibliothek ist kein erneuter Download erforderlich. Die Laufzeit löst historische
absolute Materialpfade gegen `material_library/` im aktuellen Projekt auf. Die
Originalmetadaten bleiben als Herkunftsnachweis erhalten.

## Enthaltene Dateien

| Bereich | Dateien | Bytes | Zweck |
|---|---:|---:|---|
| `material_library/catalogs/madmapper-official-d7ff211.json` | 1 | 6.463.772 | 638 Einträge, Metadaten und Kompatibilitätsstatus |
| `material_library/sources/madmapper-materials-d7ff211281f1/` | 2.102 | 51.479.825 | Originalshader, Vorschaubilder, Texturen, gemeinsame Libraries und Notices |
| `material_library/imported/` | 3.285 | 70.032.885 | 638 Pakete mit Importmanifesten und vorhandenen abgeleiteten Shadern |
| Gesamt | 5.388 | 127.976.482 | Unkomprimierte lokale Bibliothek zum Prüfzeitpunkt |

Ein separates Verzeichnis `prepared/` ist nicht erforderlich. Die 585 vorhandenen
`prepared.frag` liegen in den jeweiligen importierten Paketen. Die größte Datei
ist der Katalog mit 6.463.772 Bytes; die größte Textur `studio.exr` hat 5.642.917
Bytes. Die Dateigrößen stammen aus dem Abhängigkeitsaudit vor dem finalen Commit;
die endgültige Git-Dateiliste wird im Release geprüft.

## Warum die Quellen mitgeliefert werden

Die Materiallaufzeit liest auch bei vorhandenen vorbereiteten Shadern
Originalparameter, Metadaten, Textureingaben und gemeinsame Libraries. Nur
`prepared.frag` oder nur die acht aktuell in `test1` referenzierten Materialpakete
würden die Bibliothek nicht vollständig bereitstellen. Ein Cache im `.toe`
ersetzt diese Dateien nicht.

Der Katalog enthält **585 adaptable** und **53 unsupported** Einträge. Das sind
Kompatibilitätskategorien und keine Behauptung, dass alle 638 Materialien in
TouchDesigner fehlerfrei rendern. Vorhandene GPU-Prüfungen und Quarantänemarkierungen
bleiben bestehen; die UI zeigt deren Zustand an. Ein Vorschaubild ist kein
Rendernachweis. Exakte Parameteranzeigen für gespeicherte Shows benötigen ebenfalls
die zugehörigen Shaderquellen.

## Herkunft und Bedingungen

`source-snapshot.json` dokumentiert den übernommenen Stand des offiziellen
Repositories `https://github.com/madmappersoftware/MadMapper-Materials`:

- Commit: `d7ff211281f1878feeccd8ead05ce855c0eac5ee`
- Archiv-SHA256: `52adfcd71b631937da1e7b1dfffc7981d3ad158b7e9ff221f5f009bb4d42b7d9`
- Übernommen: `Materials`, `Libraries`, `README.md`, `MaterialsDoc.md`, `LICENSE`
- Nicht Bestandteil dieses Imports: `LaserMaterials`

Die vollständige Apache-2.0-Datei am Wurzelverzeichnis des Snapshots sowie die
Original-READMEs bleiben enthalten. Einzelne Shader enthalten zusätzliche oder
andere Bedingungen. Beispiele im vorhandenen Quellstand sind CC BY-NC-SA 3.0
bei `70s Maelstrom`, `Alien Sunset` und SDF-Demos sowie ein BSD-artiger
Copyright-/Weitergabehinweis bei `Cellular`. Deshalb darf die gesamte Sammlung
nicht pauschal als Apache 2.0 bezeichnet werden. Credits stehen bei 633
Katalogeinträgen im Feld `CREDIT`; 601 enthalten `DESCRIPTION`.

Originalshader, Texturdateien, Paketmetadaten und ihre Hinweise werden vollständig
erhalten. Die Auslieferung ändert diese Bedingungen nicht. Für eine konkrete
Weiterverwendung gelten die Hinweise des betreffenden Materials.

## Betrieb und Aktualisierung

Den gesamten Ordner `material_library/` neben dem `.toe` und `pixelblaze_mapper/`
behalten. Bei fehlendem Material zunächst Katalogpfad, lokalen Quellordner und
Importmanifest prüfen. Für eine neue, bewusst gewählte Bibliotheksversion existiert
`pixelblaze_mapper.sync_madmapper_library`; ein erneuter Import ist kein notwendiger
Installationsschritt und kann den geprüften Metadatenstand verändern. Vor einer
Aktualisierung Quellen, Katalog und Pakete gemeinsam sichern.

Der ursprüngliche Dateiaudit steht in
[qa/material-dependencies.json](qa/material-dependencies.json). Dessen leere
`tracked`-Liste beschreibt ausdrücklich den Zustand **vor** Aufnahme der Assets
in den Release-Commit, nicht die finale Auslieferung.

Die anschließende [Pfadprüfung](qa/material-path-audit.json) bestätigt 638
auflösbare Quellen und Vorschauen, 638 Importmanifeste, 585 vorbereitete Shader
und einen unveränderten Katalog. Die zunächst auffällige Schreibweise eines
Molnár-Pfades betrifft die Zeichenkodierung im historischen `relative_path`;
die tatsächlich vorhandenen Shaderdateien stimmen per SHA256 überein. Die
Laufzeitauflösung verwendet den korrekt geschriebenen lokalen Quellpfad.
