# Nachprüfung: MK2-Bedienung und Controller-Performance

Die nach dem Release beobachteten Hänger wurden in mehreren Softwarepfaden
untersucht und korrigiert. Ein begrenztes Messfenster am Controller
`10.0.0.253` erreicht nach tatsächlichem Kaltstart zuletzt **28,96 vollständige
Frames pro Sekunde**, also rund 29 FPS,
ohne neue unvollständige Frames oder die unten aufgeführten Paketfehler.
Damit ist eine Verbesserung gegenüber den zuvor beobachteten etwa 3–8 FPS
belegt. Durchgehende 30 FPS, fehlerfreier Langzeitbetrieb und eine vollständige
Hardwareabnahme sind damit nicht nachgewiesen.

## Behobene Arbeit im TouchDesigner-Hauptthread

**UI-Wartung:** Eine Typverwechslung zwischen Text DAT und Text COMP führte
dazu, dass die Wartung alle 20 Bedienpanels im Zwei-Sekunden-Takt erneut
aufbaute. Die Erkennung prüft jetzt `node.isCOMP`. Vorhandene gültige Panels
werden dadurch nicht fortlaufend neu aufgebaut.

**MK2-Materialkatalog:** Beim Durchblättern werden Metadaten verwendet, ohne
Shaderparameter für jedes ausgewählte Material zu laden. Unveränderliche
Katalogdaten werden zwischengespeichert, statt sie bei jedem Aktualisieren
erneut aufzubereiten. Eine warme Live-Aktualisierung lag nach der Korrektur
bei etwa **0,62 ms**, gegenüber etwa **63 ms** im früheren Diagnosepfad.
Das ist die gemessene Softwareaktualisierung; es ist keine Messung der
vollständigen Zeit vom mechanischen Drehregler bis zur sichtbaren Geräteanzeige.

Der getrennte Offline-Vergleich umfasst 635 Metadatensätze und 41
Rad-Auswahlschritte nach einer Aufwärmphase: ungefähr 0,965 Sekunden zuvor
und 0,0243 Sekunden danach. Er schließt TouchDesigner-/Shaderarbeit und
USB-Rendering ausdrücklich aus. [Offline-Messung](qa/mk2-catalog-cache-offline-benchmark.json).

**Show-Datenzugriff:** Zwei wiederholte Lesezugriffe im Show-/Automationspfad
verwenden einen Lesecache. Die Änderung wurde mit den zugehörigen Show-,
Automations- und Übergangstests geprüft; gespeicherte Aufnahmen werden dadurch
nicht inhaltlich umgeschrieben.

**Netzwerkeditor:** Bei 79 Operator-Kacheln im TouchDesigner-Netzwerkeditor
wurde die eingebettete Viewer-Anzeige abgeschaltet. Das vermindert die
Darstellungsarbeit des Editors. Native Bedienfenster und die eigentlichen
Signalverbindungen bleiben davon unberührt.

**Fenstersteuerung:** Beim Schließen von Material Browser, MadMapper Library,
Shortcut-Viewer und MK2-Materialfenster fiel die gemessene Ausgabe zunächst auf
etwa 0,12 FPS. Eine Aktivierung des Hauptfensters lief in einen Timeout, obwohl
die TouchDesigner-API weiterhin antwortete. Die globale Einstellung
`general.stopplayingwhenminimized` wurde nach Sicherung von 1 auf 0 gesetzt;
diese Änderung allein behob den Einbruch nicht (etwa 0,108 FPS).

Danach wurde ein einzelnes Perform-Fenster für
`/project1/shortcut_hub/help_panel` mit 1120 × 912 Pixeln verwendet. Ein erstes
Fenster damit ergab etwa 17,60 FPS; die unten beschriebene anschließende Messung
nach Beruhigungszeit ergab 22,78 FPS. Die Beobachtungen zeigen eine Abhängigkeit
vom Fenster-/Darstellungszustand, aber keinen isolierten Beweis einer einzigen
Ursache. Für den tatsächlichen Öffnungszustand verwendet die Steuerung jetzt
`isOpen`; der Wert des Pulsparameters `winopen` ist dafür ungeeignet.

Ein zusätzlicher MK2-Fensterschutz schließt beim Wechsel zu BROWSE oder Kategorien
das von dieser Steuerung geöffnete Playerfenster, wenn die Desktopvorschau
deaktiviert ist. Dadurch bleibt kein unerwünschtes eigenes Materialfenster
offen. Andere Fenster werden dadurch nicht pauschal geschlossen.

Die große zusätzliche Desktop-Materialvorschau bleibt standardmäßig deaktiviert.
Die Bilder auf den MK2-Displays, Materialauswahl, Laden und Player bleiben
erhalten. Der vorhandene optionale Desktopdialog wird nur bei ausdrücklich
aktivierter Konfiguration verwendet.

## Gemessener Empfänger `.253`

Das letzte dokumentierte Fenster nach dem Kaltstart dauert **15,0208 Sekunden**, nach einer
Beruhigungszeit von zehn Sekunden. Während dieses Messintervalls erfolgen keine
TouchDesigner-API-Aufrufe. Die Rate wird
aus der Differenz des Empfängerzählers und der verstrichenen Zeit berechnet,
nicht aus einer einzelnen kurzzeitig angezeigten FPS-Zahl.

| Messgröße | Zunahme im Fenster |
|---|---:|
| Vollständige Art-Net-Frames | 435 |
| Unvollständige Frames | 0 |
| Veraltete Frames | 0 |
| UDP-Queue-Drops | 0 |
| Abgewiesene Art-Net-Daten | 0 |
| Überschriebene Frames | 0 |
| Eingereichte Ausgabeframes | 435 |

Das ergibt **28,9598 empfangene vollständige Frames/s** und ebenso viele
eingereichte Frames/s. `.251` war in diesem Messfenster isoliert.
[Aktuelle Kaltstart-Messung ohne TouchDesigner-Aufrufe](qa/performance-cold-reopen-no-td-calls.json).
Das vorherige beruhigte Fenster vor dem Kaltstart umfasste 342 vollständige
Frames in 15,0153 Sekunden, entsprechend 22,7768 FPS, ebenfalls ohne neue
Fehler in den genannten Kategorien.
[Vorherige Messung ohne TouchDesigner-Aufrufe](qa/performance-settled-no-td-calls.json).
Das frühere 15,0575-Sekunden-Fenster mit 196 vollständigen Frames ergab 13,0167
FPS und bleibt als vorheriger Diagnosezustand erhalten.
[Frühere Messung](qa/performance-steady-final.json). Dauerhafte 30 FPS wurden
auch durch die neuere Messung nicht nachgewiesen.

## Zustand von `.251` und Grenze der Aussage

Controller `10.0.0.251` wurde zur Eingrenzung aus der Ausgabe genommen und nach
Neustart wieder erreichbar. Frühere Versuche mit Helligkeit 0,7 zeigten noch
keine empfangenen Pakete und zeitweise HTTP-Ausfälle. Das belegt weder, dass
Art-Net den Ausfall auslöste, noch einen Spannungseinbruch. Ein veränderter
Heap-Minimalwert kann auf einen Neustart hinweisen; ohne auslesbaren Resetgrund
ist dessen Ursache nicht gesichert. Die geprüfte Firmwarequelle setzt den
Empfangszähler nur beim Start zurück und sieht 1.200 Plätze pro Pin vor;
ein Überlauf allein durch die 299 Plätze ist daraus nicht ableitbar.

Anschließend wurden kontrollierte Einzelbilder und gedimmte Ausgaben geprüft:

| Versuch | Beobachtung | Bewertung |
|---|---|---|
| Ein schwarzes Bild | 7 empfangene Pakete, 1 vollständiger Frame | Einzelbildempfang bestätigt. |
| Ein stark gedimmtes RGB-Bild | 14 Pakete, 2 vollständige Frames insgesamt | Zweites Einzelbild bestätigt. |
| Konfigurierte Helligkeit 0,02, Zielrate 10 FPS | 225 zusätzliche vollständige Frames in 30,196 Sekunden; keine neuen Timeouts, unvollständigen Frames, Queue-Drops oder erkennbaren Resets | Begrenzter gedimmter Test bestanden; anfangs etwa sieben Sekunden ruhig, danach ungefähr 10 FPS während der letzten 20 Sekunden. |
| Konfigurierte Helligkeit 0,02, Zielrate 30 FPS | Zähler 227 → 596 vollständige Frames; nach 20,1647 Sekunden ein unvollständiger Frame | Automatisch abgebrochen, nicht vollständig bestanden. Keine neuen Timeouts, Queue-Drops, Sequenzfehler oder erkennbaren Resets in diesem Fenster. |

[Gedimmter 10-FPS-Test](qa/controller251-controlled-dim-10fps.json) ·
[Abgebrochener 30-FPS-Test](qa/controller251-controlled-dim-30fps.json).

`.251` wurde anschließend wieder isoliert (`enabled = 0`); der konfigurierte
Helligkeitswert ist auf 0,7 und die Zielrate auf 30 zurückgestellt. Die Ursache
des vollständigen Hängers und der zuverlässige Betrieb bei dieser Helligkeit
bleiben ungeklärt. Es wird weder ein Hardwaredefekt noch eine dauerhafte
Absturzbehebung behauptet.

Frühere lesende Beobachtungsfenster zeigten vollständige Frames ohne neue
unvollständige Frames oder Timeouts. Der Benutzer konnte dabei jedoch nicht
wie vorgesehen am MK2 durchblättern. Diese Beobachtungen sind deshalb kein
bestandener Belastungstest mit gleichzeitiger manueller MK2-Bedienung.

## Regressionen und Nachweise

- MK2-Katalogcache: **257 Tests und 3.943 Untertests bestanden**.
  [Ergebnis](qa/tests-mk2-catalog-cache.txt)
- Show-/Automations-Lesecache: **512 Tests und 4.382 Untertests bestanden**.
  [Ergebnis](qa/tests-show-automation-read-cache.txt)
- MK2-Fensterschutz: **37 Tests und 10 Untertests bestanden**.
  [Ergebnis](qa/tests-mk2-owned-window-browse.txt)
- Abschließende gezielte Prüfung von UI-Wartung, Theme und MK2-Fenstern:
  **25 Tests und 10 Untertests bestanden**.
- Der frühere Metadaten-Livetest bestätigt unveränderte Auswahl, Konfiguration,
  Worker, Show und Sender sowie ausbleibendes Shaderparameterladen; dessen
  63-ms-Wert gehört ausdrücklich zum früheren Stand.
  [Früherer Metadaten-Nachweis](qa/mk2-metadata-browse-live.json)

Die Testmengen überschneiden sich und werden nicht zu einer neuen
Gesamttestzahl addiert. Profileraufzeichnungen liegen in den lokalen
Diagnosesicherungen unter `Backup/`. Dieser Bericht dokumentiert begrenzte
Software- und Empfängermessungen; er ersetzt keine vollständige Release-,
Langzeit-, Lichtausgabe- oder mechanische MK2-Hardwareabnahme.

## Gespeicherter Zustand und Rückweg

Das korrigierte `.toe` wurde mit **allen Ausgaben ausgeschaltet** und `.251`
deaktiviert gespeichert. SHA256 des gespeicherten Release-Abbilds:

`C4B629A00848601ABD08D7055453C62A52B20CD060668888EE11DC28C28F475B`

TouchDesigner meldet dabei keine Fehler oder Warnungen; die Show- und
Automations-JSON-Hashes sind unverändert. Das spätere erneute Einschalten der
anderen Controller ist vom gespeicherten Startzustand zu unterscheiden;
`.251` bleibt isoliert. Dieser Dateinachweis behauptet keinen Commit oder Push
der nachträglichen Performance-Korrekturen.

Die gespeicherte Datei wurde anschließend tatsächlich in einem neuen
TouchDesigner-Prozess (PID 22456) kalt geöffnet. Der Sender war nach dem
Kaltstart ausgeschaltet; Show-, Automations- und Segmenthashes stimmten überein,
und es gab keine Fehler oder Warnungen. Erst nach dem erneuten Start der
freigegebenen Ausgabe entstand das oben dokumentierte rund-29-FPS-Fenster.
[Kaltstartnachweis](qa/performance-cold-reopen.json). Dieser begrenzte Wiederöffnungs-
und Empfängertest bestätigt keinen Langzeitbetrieb oder die gesamte Anlage.

Der unveränderte vorherige Projektstand liegt unter
`Backup/controller251-regression/release-before-performance-fixes.toe`.
`network-viewers-before.json` sichert die ursprünglichen Netzwerk-Viewerwerte,
`minimized-preference.json` die vorherige Minimized-Einstellung. Diese lokalen
Diagnosesicherungen ermöglichen die gezielte Rücknahme der Darstellungsänderungen.
