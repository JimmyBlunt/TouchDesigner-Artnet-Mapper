# Scanbibliothek, Vorschau und gezielte Nachaufnahme

Implementierungsstand 10. September 2026. Zuständige Dateien: `pixelblaze_mapper/scan_library.py`, `scan_library_ui.py`, Einbindung in `build_scan_session_ui.py`, Hilfetext in `scan_workflow_ux.py`. Die Bibliothek verändert keine gespeicherten CSVs, Capture-Manifeste oder Live-Ausgänge. Die Installation und Sichtprüfung der aktuellen TouchDesigner-Oberfläche dokumentiert der übergeordnete Abschlussbericht.

## Bedienung

1. In Guided Scan → **Build 3D** → **Open scan library** öffnen.
2. Ordner wählen und **Refresh files** drücken. Der Index findet 2D-Ansichten und 3D-CSV-Dateien im Ordner sowie zwei Unterordnerebenen. **Search** filtert Namen und Pfade; **All / 2D views / 3D results** filtert den Typ. Vor/Zurück blättert durch jeweils acht Einträge.
3. Auf eine Zeile klicken: `[x]` markiert die Datei für die nächste Aktion, ein weiterer Klick entfernt die Markierung. Die zuletzt angeklickte Datei erscheint rechts als Punktvorschau. Ausgewählte Dateien bleiben beim Suchen und Blättern markiert; die Gesamtanzahl bleibt sichtbar. **Clear selection** hebt alle Markierungen auf.
4. **Add selected views** fügt ausschließlich die markierten 2D-Dateien zur aktuellen 3D-Auswahl hinzu. LED-Identitäten, Aufnahmeumfang und Szenenrevision müssen übereinstimmen. Gleiche numerische LED-Indizes reichen nicht. Auch bereits eingetragene Ansichten werden bei diesem Übergang geprüft.
5. **Review 3D** öffnet genau ein ausgewähltes Ergebnis im bestehenden Review-Dialog. Dazu werden `candidate_3d.csv` und die zugehörige `quality_pending.json` benötigt. Andere 3D-CSVs können angezeigt und über den Layout-Import verwendet werden.

Die 2D-Vorschau zeigt U/V-Bildmessungen. Die 3D-Vorschau projiziert die unveränderten XYZ-Messungen; **Orbit − / +** ändert ausschließlich die Betrachtungsrichtung. Punktfarben zeigen Tiefe, keine Registrierungsqualität. Bei mehr als 8.000 Punkten wird nur die Darstellung ausgedünnt; Anzahl, ID-Liste und Bounds beziehen sich auf alle gelesenen Messpunkte. Ein Punkt `(0, 0, 0)` bleibt eine gültige Messung. Fehlende numerische IDs werden nicht erzeugt.

Nach visueller Rückmeldung wurden Bibliothek und Registrierungsdialog mit kontrastreichen Beschriftungen und konsistenten Aktionsfarben nachgebessert: ausgewählte Zeilen/Filter cyan, primäre Aktionen teal, Teilersatz amber und Nebenaktionen dunkel. Die native Prüfung zeigte, dass ButtonCOMP `colorr/g/b` die sichtbare Button-Gestaltung einfärbt und keine unabhängigen Fontparameter bereitstellt. Deshalb erzeugt die Implementierung für jede Schaltfläche eine transparente TextCOMP-Beschriftung mit heller Schrift und `clickthrough=True`; die vorhandenen Klick-Callbacks bleiben am unveränderten Button. Bei dynamischen Zeilen wird diese Beschriftung mitgeführt. Grundlage für die Parameter: [Derivative Button COMP](https://derivative.ca/UserGuide/Button_COMP). Die endgültige Bildschirmwirkung und Klickweiterleitung werden zusätzlich nativ geprüft.

Bei eindeutig fehlender Auswahl oder falschem Dateityp werden die betreffenden Bibliotheksaktionen deaktiviert; vorherige/nächste Seite sind nur bei vorhandener Seite verfügbar. Der tatsächliche Vorgang validiert die Daten weiterhin erneut. Listen zeigen einen lesbaren Aufnahme-/Ordnernamen mit kurzem Capture-ID-Suffix. Die Detailanzeige behält den vollständigen ursprünglichen Dateipfad und damit die vollständige Identität bei.

## Vorhandene eigenständige Aufnahme fortsetzen

Genau eine ursprüngliche 2D-Ansicht markieren und **Resume original** wählen. Die Bibliothek liest `capture.json` und `result.json`, validiert das eingefrorene Routing, die ursprünglichen Einstellungen samt Revision und die darin gespeicherten LED-Identitäten. Sie stellt die ursprüngliche `capture-…`-Identität wieder her. Dadurch können passende Ansichten derselben Aufnahme ergänzt werden, ohne an einer neu generierten UUID zu scheitern.

Anschließend weitere passende Dateien markieren und **Add selected views** wählen. Die wiederhergestellte Aufnahme darf auch erneut erfasst werden; davor Kamera und Scanplan kontrollieren. Pläne und vorbereitete 3D-Jobs der zuvor aktiven Sitzung werden ungültig gemacht. Die Wiederherstellung startet weder Kamera noch Hardware.

Bei umgezogenen Projektordnern wird der aktuelle Elternordner des gewählten Capture-Verzeichnisses als Arbeitsordner verwendet. Der historische `workspace`-Eintrag in `capture.json` wird nicht verändert; die Originaldatei bleibt bytegleich. Die Einstellungen und Identitäten werden weiterhin streng geprüft. Alte Dateien ohne belastbare Identitätsdaten werden nicht als beliebige fremde Sitzung übernommen. Layout-Scans werden über das ursprüngliche Layout-Objekt vorbereitet.

## Fehlende oder schwach beobachtete LEDs nacherfassen

Passende 2D-Ansichten markieren. **New scope: missing** wählt LEDs aus, die in keiner der ausgewählten Ansichten vorkommen. **New scope: weak** wählt LEDs mit weniger als drei Beobachtungen, einschließlich fehlender LEDs.

Die Aktion erstellt einen neuen geplanten Teilumfang innerhalb der bestehenden LED-Identität. Stabile Vergleichsanker bleiben erhalten. Die aktive Ansichtsliste wird geleert, damit alte Vollaufnahmen nicht mit dem neuen Teilumfang vermischt werden. Alle bisherigen Dateien bleiben auf der Platte und in der Bibliothek auffindbar. Danach Scanplan erneut prüfen und neue Ansichten aufnehmen. Wenn keine LEDs dem Filter entsprechen, bleibt der bisherige Umfang unverändert.

Die Filter verwenden die markierten Ansichten, nicht ungeprüft alle gefundenen Dateien. Beobachtungsanzahl ist keine bestätigte 3D- oder Registrierungsqualität. Der getrennte Registrierungsdialog übernimmt die anschließende Prüfung und den kontrollierten Teilersatz im Entwurf.

## Begrenzte Arbeit und Cache

- Der Index liest nur CSV-Kopfzeilen. Er untersucht höchstens 1.000 Verzeichniseinträge und nimmt höchstens 250 Dateien auf; verlinkte Pfade außerhalb des gewählten Stammordners werden ausgelassen.
- Dateiinhalt wird bei expliziter Auswahl oder einer expliziten Analyse gelesen. Pro Datei gilt eine Grenze von 16 MB, pro gemeinsam geprüfter Auswahl 64 Ansichten und 32 MB einschließlich Metadaten.
- Eine Vorschau validiert höchstens 100.000 Messpunkte und zeigt höchstens 8.000. Acht Vorschauen werden nach Dateipfad, Änderungszeit und Dateigröße zwischengespeichert.
- Suche, Filter, Blättern und Zeilenanzeige arbeiten auf dem Index im Speicher. Die ScriptTOP-Projektion verwendet gespeicherte Punkte und einen Bildcache; sie liest keine Dateien pro Frame.
- Neue Dateien erscheinen über **Refresh files**. Die Bibliothek behauptet keine automatische Hintergrundüberwachung.

## Verifikation

`tests/test_scan_library_workflow.py` prüft Indexgrenzen, Dateitypen und Suche, fehlerhafte CSVs, sparse IDs und Nullkoordinaten, ursprüngliche Aufnahmeidentität, Fremdidentität, verschobene Ordner ohne Metadatenänderung, schwache/fehlende Teilumfänge, echte UI-Aktionen mit isolierten TD-Stubs und unveränderte Dateien. Die Vorschau wird auf endliche Pixel und veränderte 3D-Ansicht bei Orbit geprüft. `test_scan_workflow_ux.py` prüft den Bibliothekseinstieg ohne automatische Auswahl sowie die weiterhin korrekte Übergabe eines bearbeiteten Umfangs an den Offline-Job.

Die gezielte Prüfung aus Bibliothek, Workflow, Staging und Standalone-Scan bestand zunächst mit 83 Tests. Nach Ergänzung des Umzugsfalls bestanden Bibliothek und Workflow zusammen mit 33 Tests. Das sind automatisierte Funktionsprüfungen außerhalb der nativen Oberfläche, keine abgeschlossene Nutzerstudie. Ein zusätzlicher rein lesender Test fand 11 bestehende Scan-Dateien und konnte die ursprüngliche eigenständige Aufnahme eines vorhandenen 256-LED-Captures wiederherstellen; dabei wurde keine aktive TD-Sitzung geändert.

Die spätere Kontrast-/Auswahlüberarbeitung wurde einschließlich Registrierungsprüfungen mit 48 Tests geprüft. Neue Prüfungen decken die tatsächlich vorhandenen ButtonCOMP-Farbparameter, auswählbare Aktionen, lesbare Dateibezeichnungen ohne Veränderung der Originalquelle und die dynamische, klickdurchlässige Textbeschriftung ab.

Der Hauptagent bestätigte die native Darstellung anschließend mit `library.jpg`. Ein echter Mausklick auf die Beschriftung einer zweiten Zeile führte zur zweiten Auswahl, aktualisierte die cyanfarbene Markierung und die Vorschau. Die Textüberlagerung verhinderte das Klickereignis nicht.
