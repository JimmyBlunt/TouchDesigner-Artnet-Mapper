# GICO-6612PRO: Recherche und Messplan

Stand: 12.09.2026. Ergänzung zu den lokalen Messprotokollen. Keine weiteren
Hardwareänderungen oder Lichttests während dieser Recherche.

## Belastbare Erkenntnisse

Unser GICO unter 10.0.0.244 antwortet als GICO-6612PRO 12PORT DMX512&SPI.
Der unabhängige Schwarzbildsender erreichte bei 24 Universen 30,00 FPS,
die tatsächliche TouchDesigner-Pipeline im aktiven Mittel 20,99 FPS.
Das sind Senderaten. Die bisher erhaltenen ArtPoll-Antworten liefern keinen
ausgewerteten Empfangs- oder Ausgabebildzähler. Schwarze Testdaten erlauben
keine optische Kontrolle, ob neue Bilder vollständig ausgegeben werden.

### Herstellerdokumente

Das [GIGACOLOR-Handbuch V1.2, PDF-Seite 11](https://shop.led-studien.de/media/de/95/b8/1764233145/GC-6612pro%20manual_EN.pdf?ts=1764233145)
empfiehlt bei acht Universen pro Port (1360 RGB-Pixeln) etwa 20 Hz Softwareausgabe.
Es dokumentiert auf PDF-Seite 9 einen einstellbaren Speed-Wert, beispielhaft
25 Hz. Dieser ist kein belegter Live-Zähler. Eine Diagnoseanzeige für tatsächlich
ausgegebene FPS wird dort nicht beschrieben. Sechs Universen entsprechen
1020 RGB-Pixeln. Ein kleinerer Wert verändert die Portaufteilung und darf
nicht ohne passende Änderung der Senderzuordnung übernommen werden.

Das [ältere Handbuch V1.1](https://artnet.ro/Download/Manuals/Manual.ArtNet.12.porturi.En.pdf)
beschreibt 72 Universen, V1.2 dagegen 96. Das exakte Geräte-/Firmwaremodell
muss daher vor einer Kapazitäts- oder Menüempfehlung feststehen.

Das [Hersteller-Downloadzentrum](https://www.gigacolor.net/download) listet
ArtnetSettingTools sowie Anleitungen für Resolume und Jinx. Es wurde kein
Programm heruntergeladen oder gestartet. Das Vorhandensein eines solchen
Werkzeugs belegt keinen darin enthaltenen FPS-Zähler.

### Nutzerberichte und Grenzen der Suche

Gezielt gesucht wurden GC-6612Pro, GICO-6612PRO und Gigacolor in Verbindung
mit FPS, frame rate, performance, benchmark und chinesisch 帧率; zusätzlich
Resolume-, TouchDesigner-, MADRIX-, Reddit-, DIYChristmas- und
AusChristmasLighting-Kontexte. Die Forensuche erfolgte parallel durch einen Agenten.

Ein [Ersthandbericht auf AusChristmasLighting, Beitrag 17 vom 05.01.2024](https://auschristmaslighting.com/threads/adding-generic-artnet-device.15918/post-136555)
beschreibt funktionierende Wiedergabe nach Korrektur auf Universe 0 und Nutzung
von DMX-Workshop. Der Aufbau verwendet FPP auf Raspberry Pi 4 und einen
adressierbaren 5-V-Strip. Eine gemessene FPS-Zahl fehlt. Die Aussage eines
anderen Teilnehmers über zwölf Controller betrifft H807SA und ist kein
GICO-Benchmark.

In den öffentlich auffindbaren geprüften Ergebnissen fand sich kein belastbarer
GC-6612Pro-Nutzerbenchmark mit gemessenen Ausgabe-FPS, LED-Zahl, aktiven Ports
und Messmethode. Das bedeutet nicht, dass solche Berichte nirgends existieren.
Werbeformulierungen, Software-Sollwerte und Videos ohne Zeitmessung werden
nicht als Messwerte übernommen.

## Vorgeschlagene Messung

Dieser Abschnitt ist unser Versuchsplan, kein behaupteter Herstellertest.

1. Geräteversion und konfigurierte Universen pro Port festhalten. Den aktuellen
   Aufbau zunächst unverändert lassen. Mehrere unabhängige Art-Net-Sender ausschließen.
2. Mit Wireshark auf Ethernet 3 (10.0.0.125) die Ausgabe an 10.0.0.244 erfassen.
   Für ein einzelnes Universum lautet ein geeigneter Anzeigefilter:

   `ip.dst == 10.0.0.244 && artnet.output.universe == 0`

   Unter Statistics / I/O Graphs bei 1-s-Intervallen die Paketanzahl darstellen.
   Nur bei genau einem Paket je Universum und Bild entspricht sie der Senderate
   dieses Universums. Für unseren 24-Universen-Test ergeben 30 FPS insgesamt
   720 ArtDmx-Pakete/s. Vollständigkeit und Abstände je Universum auswerten;
   Gesamtpakete geteilt durch 24 allein beweisen keine vollständigen Bilder.
   Ein Mitschnitt am PC beweist weder Empfang noch LED-Ausgabe am GICO. Ein
   gespiegelter Switch-Port am GICO zeigt dessen Netzwerkzufuhr besser, aber
   ebenfalls nicht die interne Verarbeitung.
   [Wireshark Art-Net-Felder](https://www.wireshark.org/docs/dfref/a/artnet.html),
   [I/O-Graphen](https://www.wireshark.org/docs/wsug_html_chunked/ChStatIOGraphs.html).
3. Tatsächlich neue LED-Bilder mit einem schwachen räumlichen Testmuster prüfen:
   pro Bild eine fortlaufende Nummer über mehrere LEDs codieren, an mehreren
   Ports und an Universumsgrenzen wiederholen. Eine 120-/240-fps-Aufnahme
   mit kurzer Belichtung kann übersprungene, wiederholte oder gemischte Nummern
   sichtbar machen. Aufnahmezeitstempel verwenden, nicht die verlangsamte
   Abspielzeit. Rolling Shutter und LED-PWM können die Auswertung verfälschen;
   das ist ein praktischer Vorabtest, kein präziser Latenznachweis.
4. Für eine eindeutige technische Messung einen geeigneten Logic Analyzer am
   LED-Datensignal verwenden: Datenblöcke samt Bildnummer decodieren und
   Wiederholungen zählen. Nur Reset-Abstände zu messen genügt nicht, weil
   ein Controller dasselbe Bild wiederholt senden kann. Mehrere Ports erfassen,
   wenn die Synchronität zwischen Panels bewertet werden soll.
5. Bei 15, 25 und 30 FPS jeweils nach Aufwärmphase mindestens 60 Sekunden
   messen, zunächst mit unabhängigem Sender, dann derselbe Versuch aus TD.
   Fehlende Bildnummern, gemischte Bilder, tatsächliche Aktualisierungsrate,
   mittlere und maximale Bildabstände sowie Portbelegung protokollieren.

Das ArtPollReply-Feld RefreshRate bezeichnet laut
[Art-Net-Spezifikation](https://art-net.org.uk/downloads/art-net.pdf) eine
maximal akzeptierte ArtDmx-Rate; selbst wenn ein Gerät es liefert, ist es kein
Live-Ausgabemesswert. ArtPoll-Erreichbarkeit und Ping sind ebenfalls kein FPS-Test.

## Konsequenz für unser weiteres Vorgehen

Zuerst GICO-Ausgabe mit wechselnden Bildnummern nachweisen und parallel die
TD-Bildbereitstellung auf stabile 30 FPS bringen. Danach unter vergleichbarer
Portlast über ESP-Firmware, Ethernet-Nachrüstung oder Teensy 4.1/FastLED entscheiden.
Der vorhandene GICO ist eine geeignete Referenz für diesen Vergleich, seine
30-FPS-Ausgabe ist bisher jedoch nicht nachgewiesen.

Für RGB-LEDs mit nominell 800 kbit/s benötigen 1122 Pixel allein 33,66 ms
Datenzeit, zuzüglich Reset. Diese einzelne Kette muss für 30 FPS verkürzt
oder aufgeteilt werden, unabhängig von CPU- oder Netzwerkgeschwindigkeit.
Das ist eine Rechnung aus dem [NeoPixel-Protokolltiming](https://learn.adafruit.com/adafruit-neopixel-uberguide/advanced-coding),
kein gemessener GICO-Grenzwert. Für den GICO kann außerdem die konfigurierte
Portlänge relevant sein, auch wenn physisch weniger LEDs angeschlossen sind;
das Verhalten ist noch zu messen.
