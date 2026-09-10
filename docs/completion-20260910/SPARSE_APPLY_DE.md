# Sparse Layouts sicher aktivieren

Stand: 10. September 2026. Implementierung in `pixelblaze_mapper/build_layout_apply.py`; Prüfungen in `tests/test_sparse_layout_apply.py` und `tests/test_layout_apply.py`.

## Bisherige Einschränkung und neues Verhalten

Der aktive Layout-Adapter verwendete denselben Export wie eine kompakte Pixelblaze-JSON-Datei. Damit wurden Scans mit freien Source-Adressen, einzelnen fehlenden Punkten oder nicht belegten Restplätzen vollständig abgewiesen. Ein Scan mit Source-IDs 2 und 5 ließ sich nur durch unerwünschtes Umnummerieren in eine dichte Liste einordnen.

Der Adapter erzeugt jetzt eine Tabelle mit exakt der bereits vorhandenen Ausgabekapazität. Jeder Tabellenplatz bleibt seine kanonische Source-Adresse. Bei sieben vorhandenen Slots bleiben die beiden LEDs im Beispiel an 2 und 5; 0, 1, 3, 4 und 6 sind inaktiv. Die Anzahl der Ausgabesamples, Controller, Universen, Segmente und Zieladressen ändern sich beim Apply nicht. Eine Source-Adresse außerhalb der bestehenden Kapazität wird weiterhin vor jedem Schreibzugriff abgewiesen.

## Explizite Schwarzmaske

`/project1/layout_apply/active_source_mask` enthält nach dem Apply die Spalten `index,enabled` und genau eine Zeile pro Source-Slot. Belegte Punkte erhalten `1`, freie Slots und in den Scandaten explizit als fehlend markierte Punkte erhalten `0`. Platzhalterkoordinaten und neu projizierte UVs in freien Slots sind null; beim expliziten Beibehalten der bestehenden Material-UV bleiben auch deren bisherigen Tabellenwerte erhalten. Schwarz wird separat durch die Maske am Ausgang erzwungen. Eine UV von `(0,0)` allein ist ausdrücklich kein Nachweis für schwarze LED-Ausgabe.

Der gemeinsam verwendete Sender, Kalibrierung und native Ausgabepfade müssen den Vertrag `SPARSE_SOURCE_MASK_V1` unterstützen. Die sparse Preflight-Prüfung ruft hierfür `output_slot_mask.assert_sparse_contract(op)` auf. Ein fehlender bzw. nicht unterstützter Ausgabepfad blockiert die Aktivierung. Die Maske ist Teil des geprüften Transaktionszustands. Ausgabelogik und deren Maskenprüfung werden im separaten Router-Arbeitspaket implementiert und getestet.

Die Maske bezeichnet verfügbare Source-Koordinaten, keine automatisch bestätigte Rekonstruktionsqualität. Eine freie Source-Adresse wird nie einem anderen LED zugewiesen. Auch fehlende Punkte behalten ihre ursprüngliche Bindung in der archivierten Workspace-Datei und können später durch einen überprüften Rescan wieder belegt werden.

## Getrennte Regeln für 3D, Fixture-2D und Dateiexport

- 3D-Apply erhält die physische XYZ-Geometrie jedes verfügbaren LED an seiner Source-Adresse; ausschließlich inaktive Slots bekommen Platzhalter. Gewählte UV-Projektionen werden weiterhin ohne automatische Normalisierung oder Begrenzung auf gültige Werte geprüft.
- Fixture-2D-Apply behält die bestehende physische Map und deren nachgeschaltete Geometrie exakt bei. Sampling-UVs und Fixture-Ausgabepositionen werden anhand der Source-Adresse zugeordnet. Jede verfügbare LED muss eine passende Fixture-Bindung besitzen. Fehlende Fixtures oder veraltete Bindungen werden nicht als erlaubte freie Slots interpretiert.
- Der Pixelblaze-Dateiexport bleibt unverändert strikt: Er verlangt weiterhin lückenlose Indizes und lehnt fehlende Scanpunkte ab. Das neue Verhalten gilt für die explizite Aktivierung in der bestehenden TouchDesigner-Ausgabekapazität.

## Physische 3D-Geometrie ohne Änderung der Material-UV

Die reale Installation kann physische Koordinaten außerhalb von `0..1` besitzen. Diese Koordinaten werden durch eine UV-Anforderung weder verkleinert noch verschoben. In der 3D-Oberfläche ist deshalb **3D: KEEP EXISTING MATERIAL UV** die ausdrücklich sichtbare Standardwahl: Apply übernimmt die physischen XYZ-Werte und behält die bisherige Materialabtastung vollständig bei. **3D: PROJECT UV (AXES)** bleibt direkt daneben verfügbar und verlangt weiterhin eine gültige Projektion ohne automatische Normalisierung.

Die API bietet dazu `uv_source='current'` und einen verpflichtenden `active_uv_rows`-Snapshot; bestehende API-Aufrufer behalten als Standard `uv_source='projection'`. Der übergebene Snapshot muss exakt die Spalten `index,panel_id,panel,global_u,global_v,local_u,local_v`, die vorhandene Ausgabekapazität, geordnete Source-IDs sowie endliche globale und lokale UVs in `0..1` besitzen. Bestehende Panel-IDs, Panel-Namen und globale/lokale UV-Werte bleiben unverändert. Der tatsächliche Adapter schreibt die UV-Tabelle bei dieser Option überhaupt nicht.

Die Auswahl wird in Vorbereitung, Bestätigung, aktivem Archiv und UI-Vorbereitungskontext dokumentiert. Wechseln der Wahl macht den vorbereiteten UI-Kontext ungültig. Änderungen an der aktiven UV-Tabelle werden vor dem Schreiben erneut erkannt. Der Transaktions-Snapshot enthält zudem die tatsächlich ausgewerteten Sampling-Koordinaten; diese müssen nach einem Apply mit bestehender UV unverändert sein. Dadurch bleibt auch eine vorhandene Panel- oder Hybridabtastung erhalten, deren lokale UV bewusst von den globalen UV abweichen.

`tests/test_layout_current_uv.py` prüft beliebige physische XYZ bei unveränderter Material-UV, ungültige Snapshots, veraltete UV-Zustände, die tatsächlich unterlassene UV-Schreiboperation und Rollback. Die UI-Grenztests prüfen die explizite Wahl und die notwendige erneute Vorbereitung nach einem Wechsel.

## Transaktion und Rücknahme

Vorbereitung bindet Workspace-Revision, aktive Map, UV-Tabelle, bisherige Maske sowie Ausgabecallbacks und relevante Verbindungen in den Zustands-Hash ein. Änderungen am Workspace, an der Maske, an Callback-Code oder an Verbindungen machen einen vorbereiteten Plan ungültig. Ausgabe muss vor Vorbereitung, vor dem ersten Schreibzugriff und nach dem Schreiben aus sein; ein aktiver Scan-Lock verhindert Apply ebenfalls.

Map/UV, Maske und das aktive Workspace-Archiv werden in derselben bestehenden Transaktion geschrieben und geprüft. Schreibfehler oder fehlgeschlagene Verifikation stellen den vorherigen Zustand wieder her. War die Masken-DAT vorher nicht vorhanden, entfernt die Rücknahme nur die neu angelegte Maske. War sie vorhanden, werden ihre ursprünglichen Inhalte wiederhergestellt. Fremde parallele Änderungen an Routing oder Ausgabecallbacks werden nicht überschrieben; sie erzeugen einen expliziten Wiederherstellungsfehler.

Der Builder erzeugt keine leere Maske vorab, startet keine Hardware und speichert keine TOE-Datei. Revert verwendet den unveränderten letzten Apply-Snapshot; ältere Snapshots ohne den neuen Ausgabevertrag müssen vor einer Migration gesondert bewertet werden.

## Nachweise

Die Offline-Tests prüfen verstreute und nachlaufende freie Slots, fehlende Scanpunkte, unveränderte kanonische IDs, getrenntes 2D/3D-Verhalten, unvollständige Fixture-Abdeckung, Überschreitung der Ausgabekapazität, manipulierte Masken, veraltete Workspace-/Aktivzustände, aktivierte Ausgabe während des Snapshots, Rollback nach Teilschreiben sowie das Entfernen einer neu angelegten Maske. Die tatsächliche Schwarzsetzung von Netzwerk- und nativen Ausgabewegen wird im Router-Testpaket geprüft. In diesem Arbeitspaket wurden weder die laufende TouchDesigner-Instanz noch LED-Ausgabe verändert.
