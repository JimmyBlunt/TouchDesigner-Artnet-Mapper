# MK2-Browse-Korrektur · 18. Oktober 2026

Die zusätzliche Desktop-Materialvorschau ist standardmäßig deaktiviert.
BROWSE verwendet weiterhin die Bilder auf den MK2-Displays, öffnet aber kein
Desktop-Vorschaufenster und lädt dafür keine Bilder oder Shader nach.
Ein zuvor automatisch geöffnetes Vorschaufenster wird geschlossen; der normale
Material Player bleibt erhalten. Die Einstellung ist in
`config/mk2_windows.json` als `desktop_browse_preview: false` gespeichert.

Zusätzlich verwendet der Material-Browse-/Kategorienmodus jetzt ausschließlich
vorhandene Katalogmetadaten. Zuvor wurden beim Drehen auch native Parameter des
angewählten Materials aufbereitet. Dies konnte Shaderadaptierung und wiederholte
Katalogzugriffe im TouchDesigner-Hauptthread auslösen. Aktive Showsteuerung,
Aufnahmen und ausdrückliches Laden/Bearbeiten behalten den vollständigen Kontext.

Die laufende USB-Verbindung wurde einmal sauber geschlossen und neu geöffnet.
Auswahl, Pad-Konfiguration, Show und laufender Sender blieben erhalten. Nach dem
Live-Einbau bestätigte der Benutzer: „Ja, reagiert wieder“.

## Nachweise

- [Desktopvorschau deaktiviert](qa/mk2-desktop-preview-disabled.json): kein
  Vorschauaufruf bei 100 Aktualisierungen. Die dort gemessene Dauer beinhaltet
  auch das Erzeugen vollständiger Controller-Snapshots; sie ist kein isolierter
  Benchmark der Fensterverwaltung.
- [Metadatenpfad live](qa/mk2-metadata-browse-live.json): kein Zugriff auf die
  Shaderparameterfunktion; Auswahl, Konfiguration, Worker, Show und Sender
  unverändert. Keine TouchDesigner-Fehler oder -Warnungen.
- [Gezielte Regressionstests](qa/tests-mk2-metadata-browse.txt): 105 Tests und
  25 Untertests bestanden, einschließlich Laden, Bearbeiten, Show und Aufnahme.
- [Gesamte MK2-Suite](qa/tests-mk2-all.txt): 252 Tests und 3.943 Untertests
  bestanden nach beiden Änderungen.

## Controller 251

Nach seinem Neustart ist `10.0.0.251` wieder erreichbar und empfängt Frames.
Zunächst traten noch einzelne unvollständige Frames/Timeouts auf. Nach Abschalten
der Desktopvorschau zeigten zwei Messfenster 66/66 beziehungsweise 59/59
vollständige Frames ohne neue Timeouts oder unvollständige Frames. Da der MK2
zu diesem Zeitpunkt noch hing, bestätigen diese Fenster keinen erfolgreichen
Bedienungstest unter Last. Die gemessene Bildrate lag bei 2,36–3,30 FPS.

[Wiedererreichbarkeit](qa/controller251-recovery.json) ·
[20-Sekunden-Messung](qa/controller251-preview-off-baseline.json) ·
[25-Sekunden-Messung](qa/controller251-browse-check.json).

Die abschließende Messung nach dem Metadatenfix lieferte keinen gültigen
Endzähler: Statusabfrage und Wiederholung liefen in ein Timeout. Auch Ping blieb
anschließend erfolglos, während `.253` antwortete. Eine zeitlich begrenzte Pause
nur der Pakete an `.251` brachte keine HTTP-Antwort zurück. Der Datenstrom wurde
automatisch wiederhergestellt. Der erneute Controllerausfall ist offen;
eine dauerhafte Stabilisierung der LED-Ausgabe wird ausdrücklich nicht behauptet.
[Abschlussmessung mit Timeout](qa/controller251-metadata-browse-check.json).

Controller-Routing, LED-Anzahlen und Firmware wurden nicht geändert. Der dritte
Hardwareport reserviert weiterhin 196 Plätze, während 195 vorhandene Positionen
zugeordnet sind; der zusätzliche Platz bleibt schwarz. Das sieben Universen
umfassende Frame bleibt dadurch vollständig.
