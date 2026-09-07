# Kumulativer 3D-Layoutentwurf: Datenvertrag

Stand 07.09.2026. Implementiert in `pixelblaze_mapper/layout_scene.py`; keine TouchDesigner-/Hardwareaufrufe und keine Dateischreibaktionen. Dies ist das unabhängig getestete Modell für den späteren Editor, noch keine neue Live-Bedienoberfläche und kein Kamerascanner.

## Identität und Originaldaten

- `Scene.scene_id`: dauerhaftes Dokument; optionale `expected_count` für die abschließende Ausgabeprüfung (z. B. 3744). Kleinere Zwischenentwürfe sind erlaubt.
- `Scan.scan_id`: unveränderlicher Originalscan mit Rohpunkten, Missing-Indizes, CSV-Metadaten und optionalem ursprünglichem Generatorquelltext. Frühere Scans bleiben auch nach vollständigem Ersetzen archiviert.
- `SceneObject.object_id`: stabiles Layoutobjekt, eigener Name und eigener Transform.
- `LedBinding.led_id`: stabile LED-Identität; `local_index` benennt die LED im Objekt; `source_index` ist der globale Index im vollständigen LED-Ausgang. `scan_id/scan_index` benennt die derzeit verwendete Messung. Nur diese Messungsreferenz wechselt bei einem Teilrescan.

Keine automatische Neunummerierung, kein Nearest-Neighbor-Matching und keine Annahme, dass gleichliegende Koordinaten dieselbe LED sind. Doppelte globale Indizes, Objekt-/Scan-/LED-IDs und lokale Doppelindizes werden abgewiesen. Räumlich deckungsgleiche unterschiedliche LEDs sind erlaubt; physische Mindestabstände werden nicht behauptet.

## Transformation und Registrierung

Originalpunkte werden nie überschrieben. Transformation: Skalierung um Pivot → rechtshändige Eulerrotation X, Y, Z in Grad → Pivot zurück → Translation. Nicht endliche Werte, Überläufe und Skalierung null werden abgewiesen; negative Skalierung ist ein ausdrücklich gewähltes Spiegeln.

`Scan.registration` bildet Scanraum auf den ursprünglichen Objektraum ab. Danach wirkt `SceneObject.transform` auf den Raum des Layouts. Damit kann ein registrierter Teilrescan seine unveränderten Rohpunkte behalten. Die Identitätsregistrierung ist die ausdrückliche Behauptung des Aufrufers, dass beide Räume bereits übereinstimmen; das Modell ermittelt oder bestätigt dies nicht. MariMapper-3D-Punkte dürfen nicht ohne fachlichen Nachweis als Millimeterkoordinaten behandelt werden. Anker-/Registrierungsqualität muss vor einer Übernahme separat geprüft werden.

## Import: tatsächlich unterstützte Formate

| Formatargument | Datenvertrag |
|---|---|
| `pixelblaze` / `pixelblaze-json` | Koordinatenarray, vorhandener sicherer Parser; 2D erhält ausdrücklich z=0 |
| `pixelblaze-generator` | erkannter Generator; standardmäßig NICHT ausgeführt. Ausführung nur mit explizitem `generator_materializer` und positiver `generator_count` |
| `marimapper-csv` | vorhandener Parser für `index,x,y,z`, auch `tx,ty,tz`; Zusatzfelder erhalten; Lücken bleiben markiert |
| `marimapper-json` | geprüftes schlichtes `[[x,y,z], ...]`-Array wie die tatsächlich gefundene `Exported/AllExported.json`; keine erfundenen JSON-Wrapper |
| Scene JSON | eigener Versionsvertrag `pixelblaze-layout-scene`, Version1; `import_scene_json()` |

MariMapper-2D-CSV `index,u,v` wird hier nicht als ungeprüfte 3D-Geometrie interpretiert. Unbekannte JSON-Objekte, falsche Versionen/Felder und Generatoren im MariMapper-JSON-Pfad ergeben sichtbare Fehler. Stringargumente sind Inhalt; Dateipfade ausdrücklich als `pathlib.Path` übergeben. Der bestehende Generatoradapter kann bewusst als Materializer übergeben werden, wird von diesem Modul nie automatisch gewählt.

## Append und Teilersatz

`append_scan(scene, scan, source_start=..., object_id=...)` fügt ein Objekt hinzu. Alternativ ist `source_indices=(...)` möglich. Eines von beiden ist zwingend; es wird kein freier Bereich geraten. `scan_indices=(...)` wählt optional eine explizite Teilmenge des Originalscans.

Wichtig bei absoluten CSV-Indizes: Ein Scan mit Zeilen517…785 besitzt im Parser Missing-Slots0…516. Mit `scan_indices=tuple(range(517,786))` und `source_indices=tuple(range(517,786))` wird bewusst nur der gemessene Bereich gebunden. Das erzeugt keine Phantom-LEDs und verschiebt keine anderen Quellen. Ob eine konkrete Datei absolute oder lokale Indizes meint, muss der Importdialog klären.

`replace_region(scene, object_id, local_indices, new_scan, scan_indices=...)` paart die ausgewählten lokalen Indizes in exakt angegebener Reihenfolge mit Messungsslots. Anzahl muss übereinstimmen. Anker können ausdrücklich ausgeschlossen werden. Die Objekttransformation und sämtliche LED-, Objekt-, lokalen und globalen Identitäten bleiben bestehen; nicht ausgewählte Messungsreferenzen bleiben unverändert. Vergrößern/Verkleinern eines vorhandenen Verdrahtungsbereichs ist keine implizite Teilrescanoperation.

## Undo/Redo und Export

Alle Editfunktionen liefern einen neuen unveränderlichen Scene-Wert. `SceneHistory.commit(new_scene)` speichert genau einen Draftschritt; `undo()`/`redo()` stellen vollständige Zustände wieder her. Ein neuer echter Edit löscht Redo, ein No-op nicht. Commit verbietet nachträgliche Änderung/Entfernung archivierter Originalscans und Umwidmung existierender LED-Identitäten. Nichts davon verändert die aktive LED-Map.

`export_scene_json()` erhält IDs, archivierte Rohscans, Metadaten, Registrierungen und Objekttransformationen. Die Undo-/Redo-Stapel selbst sind sitzungslokal. Import ist strikt; doppelte JSON-Felder werden abgewiesen.

`export_pixelblaze_3d()` liefert ausschließlich transformierte XYZ-Punkte, sortiert nach ihren bereits existierenden globalen Quellindizes. Es verlangt lückenlose Indizes0…N−1, keine Missing-Messungen und ggf. exakt `expected_count`. Bei Lücken scheitert es, statt zu komprimieren, umzunummerieren oder erfundene Null-LEDs anzulegen. Ein Pixelblaze-Array kann keine IDs tragen: zusätzlich Scene JSON aufbewahren. Beide Exportfunktionen geben Text zurück, sie schreiben keine Datei und wenden nichts live an.

## Verifikation

`python -m unittest discover -s tests -p test_layout_scene.py`

Die Verhaltenstests prüfen Transformreihenfolge, Originalunveränderlichkeit, IDs, kumulative Importe, echte Parserpfade, CSV-Lücken/absolute Indizes, explizite Generatorfreigabe mit Testadapter, strikte Schemas, Teilersatz mit ausgeschlossenen Ankern, Registrierung, Undo/Redo und einen 3744-LED-Entwurf mit Teilrescan. Das sind Datenmodelltests, keine GPU-, UI-, Kamera- oder Hardwareabnahme.
