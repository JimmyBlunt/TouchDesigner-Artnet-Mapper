# Ersatzcontroller 248 und Animation auf Panel 1–5

Der Benutzer meldete den Controllerwechsel von 10.0.0.249 auf 10.0.0.248
und bat anschließend um eine Animation auf den bereits vorhandenen Panels.

## Geprüfte Konfiguration

Der Ersatzcontroller ist erreichbar. Die ersten fünf Ausgänge entsprechen
den abgeschlossenen Panels: 203/U120, 738/U122, 880/U127, 810/U133 und
352/U139. Zusätzlich ist Ausgang 6 mit 1122 LEDs ab U142 konfiguriert.
Dieser Ausgang hat noch keine eingemessene Zuordnung und wird schwarz gehalten.
Der interne Controllertest war bei der Vorbereitung inaktiv.

Das aktive Netzwerkziel wurde auf 10.0.0.248 umgestellt. Der interne Schlüssel
`BACK_PANEL_249` bleibt als stabile Referenz der bestehenden Segment- und
Objektzuordnungen erhalten; er bezeichnet nicht mehr die tatsächliche IP.
Die Router- und Controllerdialog-Zielfelder wurden auf 248 aktualisiert und
alte zwischengespeicherte Routerentwürfe zurückgesetzt.

Der vollständige Sendebereich ist U120–U148, 29 Universen einschließlich
U138. Die API meldet 28 belegte Universen; die freie Lücke U138 erklärt den
Unterschied zum zusammenhängenden Bereich. U138 und U142–U148 bleiben schwarz.
Die Zielbytes des noch nicht eingemessenen Ausgangs 6 wurden offline geprüft.

Alte Aufnahme-Dateien und abgeschlossene Sitzungsidentitäten bleiben
unverändert. Das aktuelle Scan-Netzwerkziel und die neuen Aufnahmefelder
wurden auf 248 / 29 Universen umgestellt; der alte Startplan wurde verworfen.
Die neue Routingrevision verhindert ein versehentliches Fortsetzen des alten
Plans. Vor weiteren Scans muss eine neue Aufnahme angelegt werden. Die alten
Ansichten bleiben mit ihrer tatsächlichen damaligen Adresse archiviert.

## Animation

Vorbereitet ist das bestehende Material `ocean_waves`, Cyan–Magenta-Verlauf,
Geschwindigkeit 0,35, globale Koordinaten, Skalierung 2. Controllerhelligkeit
20 %. Zunächst wurden 15 FPS angefordert. Der Controller meldete rund 55 ms
Ausgabedauer; diese Dauer allein war keine ausreichende Grundlage für die
Sendebildrate: Empfang, Paketabstände und TouchDesigner benötigen zusätzlich Zeit.
Für diese Vorschau ist nur der Rückwandcontroller aktiviert. Die anderen
Controller wurden in der Sendekonfiguration deaktiviert; ihre vorherigen
Einstellungen stehen in `transaction-before.json`.

Alle fünf eingemessenen Rückwand-Panels werden über die vorhandene Zuordnung
angesprochen. Fehlende LEDs und alte Platzhalter bleiben maskiert. Geometrie,
UVs, Schwarzmaske und Layoutdokument sind per Hashvergleich unverändert.
Keine neuen Scanpunkte oder Panel-6-Zuordnungen angelegt.

`tools/replace_controller_248_animation_20260911.py` enthält die Vorbereitung.
`native-before.json`, `animation-before.json` und `transaction-before.json`
sichern die Ausgangslage; die `controller-*-before.json`-Dateien den
Controller-Readback. `prepared.json` dokumentiert die geprüfte Konfiguration.
Der Projektcheckpoint wird vor dem Live-Start mit ausgeschalteter Ausgabe
gespeichert; `save.json` enthält den Namen und die SHA-256-Prüfsumme.
Empfang und laufender Sender werden nach dem Start gesondert protokolliert.

## Übertragung korrigiert

Der erste Live-Versuch sendete alle 29 Universen ohne Abstand. Der Sender meldete
rund 14,7 FPS, der Empfänger dagegen **kein vollständiges Bild** bei 658
unvollständigen Bildern. Lokale Sendestatistik beweist deshalb keine LED-Ausgabe.

`sender_packet_gap.py` ergänzt einen optionalen Abstand pro Controller. Die
Router-Storage `live_packet_gap_ms` enthält für `BACK_PANEL_249` den Wert `1.0`
(Millisekunden); andere Controller behalten standardmäßig Abstand null. Der
Builder installiert dieselbe Erweiterung bei einem Neuaufbau. Die Schleife
wartet zwischen Paketen, ohne zusätzliche Pakete oder Aufholbursts zu erzeugen.
Es läuft kein zeitkritischer Hintergrundthread in TouchDesigner.

Nach Vergleich von 0,5–1,5 ms und 5–15 angeforderten FPS wurde für diese
Vorschau **5 FPS mit 1 ms Paketabstand** gewählt. Das ist eine vorsichtige
Vorschaukonfiguration, keine Behauptung einer flüssigen Hochleistungs-Ausgabe.
Bei 7 FPS / 1 ms wurden in einem kurzen Vergleich 23 vollständige und drei
unvollständige Bilder empfangen, bei 5 FPS / 1 ms 16 vollständige und ein
unvollständiges Bild. Die Messfenster und Senderdaten liegen in `gap-*.json`;
HTTP-Abfragen und Fenstergrenzen beeinflussen kurze Vergleichsmessungen.
Die Wartezeiten laufen im Hauptthread und begrenzen dessen mögliche Bildrate.

`steady-live-verification.json` prüft anschließend längeren Empfang, veränderte
Animationsdaten, schwarze Daten für Ausgang 6 / U138 und native Fehler.
26 Tests zu Paketabstand, Sendetaktung und Routing bestanden. Insbesondere
bleiben Universumsnummern, Nutzdaten und Paketanzahl durch den Abstand erhalten;
Abstände gelten nur für den konfigurierten Controller und ungültige Werte
werden verworfen. Der korrigierte Projektstand wird mit Ausgabe AUS gespeichert,
danach wird die ausdrücklich gewünschte Vorschau wieder gestartet.

Bedienung: Im Router stoppt **ALL OUTPUTS OFF** die Anwendungsausgabe. Im Material-
Dialog lassen sich Geschwindigkeit und Farben der Animation ändern.

Der längere abschließende Vorabtest erfasste 38 vollständige und drei
unvollständige Bilder bei angeforderten 5 FPS. Animations-Hashes wechselten,
Ausgang 6 und U138 waren in den gesendeten Daten schwarz, native Fehler leer.
Die verbleibenden Empfangsausfälle sind ein offener Leistungsaspekt; es wird
keine fehlerfreie oder optisch bereits bestätigte Übertragung behauptet.
Der endgültige Speicherbeleg liegt in `save-verified.json`, der Neustart und
Empfang nach dem Speichern in `final-live-verification.json`.
