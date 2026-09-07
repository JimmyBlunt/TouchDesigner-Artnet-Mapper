# Speicherfehler – Ursache, Reparatur und tatsächlicher Ladetest

## Ergebnis

**Geprüfte Datei:** `Backup/Implementation/PixelblazeMapper_20260907_STORAGE_VERIFIED.1.toe`.

TouchDesigner meldete beim abschließenden Speichern ausdrücklich `saved successfully`. Genau diese Datei wurde anschließend über `project.load` neu geöffnet. Map, UV, Controller-/Segmenttabellen, Show-Definition und -Zustand, Browser-Seitenzustände, aktive Material-ID, Bedienwerte und kompletter 2D/3D-Arbeitsentwurf stimmen exakt mit dem Stand vor der Reparatur überein. Keine Operator- oder Picklingfehler nach dem Laden. Sender blieb OFF, 0 Pakete.

## Ursache

COMP-Storage enthielt Instanzen von `ShowSequencer`, `LayoutEditor`, `FixtureHistory`, `ImportedMaterialStateStore`, `MaterialStateStore` sowie Shader-Adaptierungsergebnisse. Durch Modul-Neuladen stimmte die Klassenidentität einiger Instanzen nicht mehr mit der exportierten Python-Klasse überein. Der read-only Vorabtest reproduzierte die gemeldeten Fehler für Show, beide Material-Caches und Layout.

Der frühere Test prüfte fälschlich nur `project.save()` und `op.errors()`. Laut [offizieller Project-Dokumentation](https://docs.derivative.ca/Project_Class) bedeutet der Rückgabewert nur, dass eine Datei geschrieben wurde. Er bestätigt nicht deren vollständigen Zustand. Die ursprüngliche CANDIDATE-Datei bleibt als historischer, nicht freigegebener Stand erhalten.

## Reparatur

- Show: Transportzustand als versionierte primitive Werte; Klasseninstanz nur im laufenden DAT-Modul. Beim Laden wird eine laufende Show pausiert, niemals automatisch gestartet.
- Materialien: alle dauerhaften Parameter als primitive Daten; die teuren Shader-Caches bleiben zur Laufzeit erhalten, werden aber nicht in die Datei geschrieben. Materialphase wird beim Laden neu zeitlich verankert, ohne die geschlossene Zeit hinzuzurechnen.
- Layout: Entwurf, ausgewählte Objekte und beide Undo-/Redo-Historien als versionierte Snapshots. Laufende Klassen, Gesten und vorbereitete Apply-Pläne werden beim Öffnen neu erstellt bzw. sicher verworfen. Vorhandene primitive Revert-Snapshots bleiben erhalten.
- Die Trennung flüchtiger Werte verwendet die dokumentierte [TouchDesigner-Storage-Funktion](https://docs.derivative.ca/Storage) `storeStartupValue`. Es wurden keine dauerhaften Zustände pauschal gelöscht.

## Nachweise – nicht nur eine grüne Testsuite

1. `storage-repair/before-repair.json`: Zustand und echte reproduzierte PicklingErrors vor Änderungen.
2. `after-migration.json`: unveränderte Map, Routingtabellen, aktive Material-ID, Bedienwerte und Workspace nach Installation. Kein UI-Neuaufbau notwendig.
3. Beim ersten reparierten Speichern führte die native Meldung weiterhin dieselben drei alten Warnungen. Daher wurde die Datei nicht auf Basis von `True` freigegeben.
4. Eine Kopie wurde mit dem mitgelieferten `toeexpand.exe` entpackt. Ein eingeschränkter Datenleser, der sämtliche Klassenimporte ablehnt, konnte die fünf betroffenen Storage-Bereiche vollständig lesen. Dauerhafte Snapshots vorhanden, flüchtige Klassenwerte tatsächlich `None`. Belege: `file-inspection.json`, `file-storage.json`.
5. Die reparierte Datei wurde neu geladen. Ein nachfolgender Speichervorgang in die neue VERIFIED-Datei meldete keine Speicherwarnungen mehr. Die Ursache des über das erste reparierte Speichern fortgeführten Warntextes wurde nicht als allgemeiner TouchDesigner-Fehler verallgemeinert; entscheidend sind Dateiinhaltsprüfung und Ladetest.
6. VERIFIED-Datei nochmals neu geladen: `after-verified-reopen.json` + `roundtrip-result.json`, alle 15 Prüfungen bestanden. Die API war während des zweiten Ladevorgangs kurz nicht erreichbar; nach abgeschlossenem Start funktionierte sie wieder.
7. Unabhängiger Materialvergleich: alle 8 gespeicherten Materialien mit 137 Werten, 137 Typangaben und 8 Seitenständen identisch. Sämtliche 14 Einstellungen des vorhandenen P1-Materialzustands identisch. Nur der mathematisch erwartete Phasenfortschritt unterscheidet sich. `material-roundtrip-comparison.json` enthält Details und Prüfsummen.
8. Gesamtsuite: **558 Tests bestanden**, 32,464 Sekunden, darunter neue Tests mit echtem Python-Modul-Reload und reproduziertem PicklingError.

Der aktuelle Fixture-Verlauf enthält 1 Undo- und 3 Redo-Schritte nach dem Laden, wie vor dem Speichern. Ein laufender Aufnahmeprozess, Netzwerkoutput oder ein neuer Hardwaretest wurde nicht gestartet.

## Grenzen

Der bestandene Speichertest ist keine Freigabe aller Dialogfunktionen oder der Performance. Niedrige Materialbildrate, weitere Hover-/Seitenwechselabnahmen, native Shortcut-Nebenwirkungen und reale Scan-/Hardwareabnahmen bleiben separat offen. Die ursprüngliche CORE-Datei, fremde Arbeitskopieänderungen und frühere Sicherungen wurden nicht überschrieben.
