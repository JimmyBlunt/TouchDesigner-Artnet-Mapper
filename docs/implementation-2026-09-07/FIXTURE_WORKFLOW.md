# 2D-Fixtures: getrennte Anordnung und Materialplatzierung

Stand 2026-09-07. Reiner Datenmodell-Checkpoint; keine Änderung aktiver Sampler oder Ausgänge. UI-Integration liegt separat in `build_layout_scene_ui.py`.

## Zwei unabhängige Arbeitsbereiche

| Bereich | Bedeutung | Änderung beeinflusst nicht |
| --- | --- | --- |
| Output-Layout | Relative räumliche Anordnung der 2D-Fixtures auf einer gemeinsamen Arbeitsfläche | Material-UV, lokale Punkte, 3D-Szene, LED-Reihenfolge |
| Material-UV | Welcher Teil eines Materialrechtecks an jeder LED abgetastet wird | Output-Layout, lokale Punkte, 3D-Szene, LED-Reihenfolge |

Beide Bereiche verwenden dieselben unveränderlichen lokalen Fixturepunkte, haben aber jeweils eine eigene `Transform2D`. Transformationen werden **nicht** miteinander verkettet. Pro Bereich: Skalierung um einen Pivot, Rotation gegen den Uhrzeigersinn in Grad, anschließend Translation. Negative Skalierung ist eine explizite Spiegelung; Nullskalierung wird abgelehnt.

Fixturepositionen sind keine neue Ausgabe-Routingtabelle. `source_index` bleibt der globale Abtast-/Ausgabeindex; `led_id` und objektlokaler Index bleiben erhalten. Ein Verschieben der Fixturefläche darf diese Identitäten nie verdichten oder umnummerieren.

## 3D → 2D: explizite, nicht destruktive Projektion

`project_fixture(scene, object_id, projection='YX')` verwendet standardmäßig **Y horizontal, X vertikal**, entsprechend der gewünschten Arbeitsansicht. Weitere explizite Möglichkeiten: XY, XZ, ZX, YZ, ZY. Die nicht dargestellte Achse bleibt im Originalscan erhalten.

Projiziert werden Rohscanpunkte nach `Scan.registration`, also im ursprünglichen lokalen Rahmen des Objekts. Die Welttransformation des 3D-Objekts wird absichtlich nicht übernommen: die relative 2D-Anordnung ist eigenständig. Kein automatisches Zentrieren, Normalisieren, Größenfit oder Umschreiben der 3D-Daten. Eine zukünftige „aus Weltansicht projizieren“-Option müsste als gesonderte bewusste Aktion umgesetzt werden.

Eine Projektion kann Punkte deckungsgleich machen; das ist nicht automatisch ein Fehler, weil verschiedene LEDs dieselbe sichtbare 2D-Position besitzen können. Fehlende Scanpunkte werden hingegen explizit als `missing_ids` übernommen und verhindern einen finalen Samplingexport.

## Modellvertrag für die Oberfläche

Modul: `pixelblaze_mapper/fixture_scene.py`.

- `Transform2D(translation=(0,0), rotation=0, scale=(1,1), pivot=(0,0))`
- `Fixture(fixture_id, object_id, leds, local_points, output_transform, uv_transform, projection='YX', missing_ids=())`
- `Fixture.output_points()` und `.sample_uv()` liefern jeweils `(LedBinding, (x,y))`-Paare; kein verstecktes Indexmapping.
- `FixtureScene(scene_id, scene_revision, fixtures=(), expected_count=None)` bindet den Entwurf an einen konkreten 3D-Szenenstand. Die Oberfläche sollte `expected_count` aus der gesamten Szene setzen, damit ein dichter Teilbereich nicht versehentlich als vollständiges Layout exportiert wird.
- `replace_transform(scene, fixture_id, domain, transform)` verlangt ausdrücklich `domain='output'` oder `'uv'` und liefert einen neuen Entwurf.
- `FixtureHistory` bietet Commit/Undo/Redo. Eine neue Änderung nach Undo entfernt den Redo-Zweig; Commits dürfen bestehende lokale Geometrie und Identitäten nicht umdeuten.
- `export_fixture_json` / `import_fixture_json` erhalten beide Bereiche verlustfrei. Eigenes Schema `pixelblaze-fixture-scene`, Version 1; kein MadMapper-/MariMapper-Dateiformat wird behauptet.
- `validate_source_scene(scene)` lehnt einen geänderten Szenenstand ab. Änderungen an 3D-Scans benötigen ausdrückliches Rebase/Reproject und erneute Kontrolle.

## Materialrechteck und Grenzen

UV-Werte beziehen sich auf ein normiertes Materialrechteck 0..1. Das Modell klemmt Werte niemals still auf den Rand. Außerhalb liegende LED-IDs sind mit `out_of_bounds_ids()` sichtbar; die Oberfläche kann sie markieren. `export_sampling_uv()` lehnt sie standardmäßig ab. Nur die ausdrückliche Option `bounds='preserve'` exportiert sie unverändert; dadurch wird keine bestimmte Sampler-Wiederholungs-/Randregel behauptet.

Der Samplingexport sortiert nach dem unveränderten `source_index`. Lücken, fehlende Messpunkte, leere Fixtures oder eine Abweichung von `expected_count` verhindern den Export. Es werden keine Koordinaten in den Live-Sampler geschrieben. Eine spätere Apply-Funktion muss zusätzlich vollständige Identitätsabdeckung und die Sampler-Randregel prüfen sowie Undo und Ausgangssicherheit berücksichtigen.

Für unkomplizierte Bedienung sollte die Oberfläche getrennte Tabs oder klar markierte Arbeitsflächen anbieten: OUTPUT mit frei gerahmten lokalen Einheiten, MATERIAL mit sichtbarem 0..1-Rechteck. Ein Dropdown für das Transformationsziel verhindert, dass ein Drag unerwartet beide Bereiche verändert. Ein ausdrücklicher „in Materialrechteck einpassen“-Befehl wäre sinnvoll, ist aber keine automatische Eigenschaft des Modells.

## Tests und Grenzen des Nachweises

```powershell
python -m unittest discover -s tests -p 'test_fixture_scene.py' -v
```

**16/16 bestanden**: beide Transformationsrichtungen unabhängig; alle Projektionen; Registrierung vor Projektion; 3D-Welttransform bleibt getrennt; Pivot-/Rotationsreihenfolge; Spiegelung; endliche Zahlen/Nullskalierung; Bounds; Source-Reihenfolge; Lücken/Missing/Anzahl; doppelte Eigentümerschaft; JSON; Szenenrevision; Undo/Redo.

Diese Tests beweisen reine Modelloperationen. Sie beweisen keine Maus-/Touch-Bindings, keine richtige Bildschirmprojektion des neuen Editors und keine tatsächliche Texturabtastung im laufenden TD-Netz. Echte UI- und Sampling-Abnahme muss separat erfolgen. Es wurden durch diesen Teilauftrag keine Kameras, nativen SfM-Bibliotheken oder LED-Ausgänge gestartet.
