# Controller 248: Pixelzahl, Ausgabezeit und 30 FPS

Stand: 12.09.2026. Recherche ausschließlich in Primärquellen; keine Änderung am
Controller durch diese Teiluntersuchung. Die folgenden Leistungsgrenzen sind
Berechnungen, keine Behauptung bereits erreichter Bildraten. Die tatsächlichen
Versuche dieser Untersuchung werden separat protokolliert.

## Ergebnis für die vorhandene Rückwand

**Die Summe von 4105 konfigurierten LEDs beweist keine Überlastung eines
Controllers. Entscheidend sind die längste serielle LED-Kette, tatsächlich
parallel arbeitende Ausgänge und der Empfang während der Ausgabe.** Die ersten
fünf Panels enthalten zusammen 2983 LED-Adressen. Bei echter paralleler Ausgabe
ist ihr längster Ausgang mit 880 LEDs der maßgebliche Zeitbedarf. Das lässt bei
800 kbit/s grundsätzlich Platz für 30 vollständige Bilder pro Sekunde.

Der zusätzlich konfigurierte sechste Ausgang hat 1122 LEDs. Eine vollständige
Aktualisierung dieser Kette dauert bei nominal 800 kbit/s bereits **33,66 ms ohne
Resetpause**. Damit sind 30 vollständige Aktualisierungen pro Sekunde an diesem
einzelnen Ausgang unter diesem Timing nicht erreichbar. Ein zusätzlicher
Controller allein verkürzt diese Kette nicht. Eine Aufteilung auf zwei
unabhängige Datenausgänge dagegen schon.

Die früher gemessenen rund 55,5 ms `outputTimeUs` sind größer als diese reine
Leitungszeit. Sie sprechen für zusätzlichen Aufwand oder eine teilweise
Serialisierung; sie identifizieren deren Ursache noch nicht. Insbesondere darf
aus dem Profilnamen `esp32-wroom-flex-8ws-2apa` nicht geschlossen werden, dass
acht Ausgänge gleichzeitig übertragen werden.

## Nachvollziehbare Rechnung

Adafruit beschreibt für RGB-NeoPixel 24 Bit pro LED bei 800 kbit/s, entsprechend
30 µs pro LED. Die tatsächliche Bildrate liegt wegen Verarbeitung und Latchzeit
unter der reinen Übertragungsgrenze. Die konkrete LED-Revision ist hier nicht
identifiziert. Für die Vergleichsrechnung verwenden wir **300 µs Resetreserve**,
wie im Abschnitt „Writing Your Own Library“ der Quelle; diese Reserve ist keine
Messung unseres Controllers. [Adafruit: Advanced Coding](https://learn.adafruit.com/adafruit-neopixel-uberguide/advanced-coding)

```text
T_Bildziel = 1 / 30 s = 33,333 ms
T_Daten(N) = N × 24 / 800000 s = N × 0,030 ms
T_Leitung(N) = T_Daten(N) + 0,300 ms
F_max_Leitung(N) = 1000 / T_Leitung(N)

Echte Parallelität: T_Leitung_gesamt ≈ max(T_Leitung je Ausgang)
Vollständig seriell: T_Leitung_gesamt ≈ Summe(T_Leitung je Ausgang)
```

Eigene Berechnung aus `config-before.json`:

| Ausgang | LEDs | Art-Net-Universen | Datenzeit | Mit 0,30 ms Reset | Rechnerische Obergrenze |
| --- | ---: | --- | ---: | ---: | ---: |
| Panel 1 | 203 | 120–121 | 6,09 ms | 6,39 ms | 156,49 FPS |
| Panel 2 | 738 | 122–126 | 22,14 ms | 22,44 ms | 44,56 FPS |
| Panel 3 | 880 | 127–132 | 26,40 ms | 26,70 ms | 37,45 FPS |
| Panel 4 | 810 | 133–137 | 24,30 ms | 24,60 ms | 40,65 FPS |
| Panel 5 | 352 | 139–141 | 10,56 ms | 10,86 ms | 92,08 FPS |
| Ausgang 6, noch ohne Scan-Zuordnung | 1122 | 142–148 | 33,66 ms | 33,96 ms | 29,45 FPS |

Mit parallelen ersten fünf Ausgängen bleiben rechnerisch **6,63 ms** des
30-FPS-Zeitfensters zusätzlich zur längsten Leitung. Empfang und Ausgabe müssen
sinnvoll überlappen, wenn die sonstigen Arbeiten länger dauern. Alle sechs
vollständig seriell benötigen dagegen ungefähr 124,95 ms, entsprechend nur
8,00 FPS. Dieser Vergleich erklärt, weshalb die Gesamtpixelzahl ohne Kenntnis
des Ausgabetreibers wenig aussagt.

Selbst Schwarz benötigt bei einer regulären vollständigen Ausgabe dieselbe
Leitungszeit wie Farbe. Ausgang 6 nur mit Schwarz zu beschicken beseitigt seinen
Zeitbedarf daher nicht. Nur wenn die Firmware einen unveränderten oder
deaktivierten Ausgang wirklich von der Ausgabe ausnimmt, fällt dessen Last weg.
Das muss ein Vergleich mit gesichertem und anschließend wiederhergestelltem
Ausgangsprofil zeigen.

## Netzwerkbudget und vollständige Bilder

Art-Net transportiert ArtDmx über UDP; das Paket enthält unter anderem eine
Universumsadresse und Sequenzinformation. ArtSync kann mehrere zuvor
übertragene Universen gemeinsam zur Ausgabe freigeben, sofern der Empfänger
diesen Modus unterstützt. Es repariert keine verlorenen Pakete. Die
Spezifikation kennt zudem eine vom Empfänger angekündigte maximale ArtDmx-Rate.
30 FPS ist keine Überschreitung einer allgemeinen 5-FPS-Protokollgrenze.
[Artistic Licence: Art-Net 4, ArtDmx/ArtSync und ArtPollReply](https://art-net.org.uk/downloads/art-net.pdf)

Eigene Budgetrechnung für unsere 510 DMX-Nutzbytes plus 18 ArtDmx-Headerbytes:

| Sendemenge | Universen/Bild | Pakete/s bei 30 FPS | ArtDmx-Datenrate ohne IP/UDP |
| --- | ---: | ---: | ---: |
| Bisheriger zusammenhängender Bereich U120–148 | 29 | 870 | 3,675 Mbit/s |
| Nur die sechs belegten Ausgangsbereiche | 28 | 840 | 3,548 Mbit/s |
| Nur die fünf eingemessenen Panels | 21 | 630 | 2,661 Mbit/s |

Für 29 Universen ergeben sich mit IPv4/UDP ungefähr 3,870 Mbit/s; eine
Ethernet-Rechnung einschließlich Präambel, Frameheader, Prüfsumme und
Zwischenraum liegt bei etwa 4,134 Mbit/s, ohne VLAN. **Dies ist keine
WLAN-Airtime-Rechnung.** WLAN-Antworten, Wiederholungen, Konkurrenz um den Kanal
und Energiesparverhalten können die verfügbare Zeit deutlich verändern.

Die Datenmenge allein rechtfertigt deshalb keine Neuanschaffung. Ein kleiner
Empfangspuffer oder eine blockierende LED-Ausgabe kann trotz geringer mittlerer
Datenrate Bursts verlieren. Nur belegte Universen zu senden kann Last sparen;
dafür muss die Empfänger-Erwartungsmenge dazu passen. Das bloße Weglassen der
sieben Universen eines weiterhin als aktiv erwarteten Ausgangs kann komplette
Bilder verhindern.

Bei 29 Paketen verursachen 1 ms Zwischenabstand bereits 28 ms Wartezeit pro Bild,
bei 0,5 ms 14 ms. Im TouchDesigner-Hauptthread kommen Packen, Kopieren und
Senden dazu. Allein diese addierten Wartezeiten können das 33,33-ms-Budget
aufbrauchen. Ein eigener zeitgesteuerter Senderprozess kann den Hauptthread
entlasten; er erhöht aber nicht die physische LED-Leitungsrate.

## Welche Firmware-Ansätze helfen?

| Ansatz | Möglicher Nutzen | Voraussetzung oder Grenze |
| --- | --- | --- |
| Alle LED-Ausgänge starten, erst anschließend gemeinsam auf Fertigstellung warten | Verhindert Serialisierung durch einzelnes Starten und Warten | Die Treiber müssen unabhängige Kanäle tatsächlich parallel betreiben |
| Getrennte Empfangs- und Ausgabepuffer, Übergabe nur vollständiger Frames | UDP kann während der Ausgabe weiter empfangen; keine halb aktualisierten Puffer | Besitzwechsel und Sequenzen müssen korrekt sein; alte Frames begrenzt verwerfen |
| RMT auf einem von WLAN getrennten CPU-Kern, angemessene Speicherblöcke | Weniger Konflikte bei interruptbasierter Übertragung | Auf dem klassischen ESP32 keine RMT-DMA verfügbar |
| Paralleles I2S mit DMA für gleichartige WS2812-Ausgänge | Weniger CPU-Arbeit und echte gleichzeitige Leitungen | Passender Treiber, GPIOs, Speicherbudget und Bibliotheksversion erforderlich |
| DMA-fähiger Ausgabetreiber auf passender Hardware | Reduziert Interruptlast | DMA-Unterstützung konkret prüfen; der Name ESP32 allein reicht nicht |
| Begrenzte Senderwarteschlange, neuester vollständiger Frame gewinnt | Keine veralteten Animationsframes oder Aufholbursts | Empfänger muss mit der gewählten Sequenzbehandlung harmonieren |

Espressif dokumentiert ausdrücklich mögliche RMT-Störungen durch konkurrierende
WLAN-Interrupts sowie die Trennung auf CPU-Kerne und SPI-DMA als Alternativen.
Der klassische ESP32 hat diese RMT-DMA-Unterstützung nicht; die FAQ empfiehlt
für diesen Fall passende andere Hardware. Dies ist eine bekannte
Implementierungsgefahr, **kein Nachweis**, dass sie unseren aktuellen
Paketverlust verursacht. [Espressif: RMT FAQ](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/peripherals/rmt.html)

Die Dokumentation des Espressif-LED-Treibers erläutert Speicher- und
Interruptkosten von RMT, verfügbare DMA-Unterstützung auf geeigneten Chips und
den SPI-Ansatz. Ein SPI-Ausgang belegt dabei einen ganzen Bus; dies ersetzt nicht
automatisch sechs unabhängige Ausgänge.
[Espressif led_strip 3.0.1](https://components.espressif.com/components/espressif/led_strip/versions/3.0.1/readme)

FastLED dokumentiert einen I2S-Treiber für **clockless** LEDs mit parallelen
Kanälen und DMA-Puffern auch für den klassischen ESP32. Gemeinsames LED-Timing
ist Voraussetzung. Die separat beschriebene Mehrkanal-SPI-API für APA102 darf
nicht mit diesem WS2812-Treiber verwechselt werden. Eine Umstellung muss gegen
die tatsächlich verwendete Firmwareversion gebaut und getestet werden.
[FastLED: ESP32-Ausgabetreiber](https://github.com/FastLED/FastLED/blob/master/src/platforms/esp/32/README.md)

## Konkrete Aufteilungen

**Option A — vorhandene fünf Panels auf einem Controller optimieren.**
2983 LEDs, fünf Ports, längster Port 880. Zuerst diese Konfiguration isoliert
messen und die Ausgabe parallelisieren beziehungsweise vorhandene Parallelität
nachweisen. Der aktuell ungemappte sechste Ausgang wird für einen solchen
Vergleich explizit deaktiviert, nicht bloß im Sender vergessen. Bei erfolgreichem
30-FPS-Dauertest ist für diese fünf Panels kein zweiter Controller erforderlich.

**Option B — alle 4105 LEDs auf einem Controller mit einem zusätzlichen Port.**
Die 1122er Kette an einer zugänglichen Stelle nach LED 680 auftrennen und die
verbleibenden 442 LEDs von einem eigenen Datenausgang versorgen. Das entspricht
vier Universen U142–145 plus drei U146–148. Die bestehende Reihenfolge der
Art-Net-Nutzdaten kann dadurch erhalten bleiben; ein neuer Port beginnt genau
an einer bisherigen Universumsgrenze. Der längste Ausgang bleibt Panel 3 mit
880 LEDs. Das Hardwareprofil nennt acht WS-Ausgänge, aber ein tatsächlich freier
geeigneter GPIO und seine Nutzung durch die Firmware sind vorher zu prüfen.
Dies ist eine Planung, keine bereits ausgeführte Verdrahtungsänderung.

**Option C — zwei Controller für nur die fünf vorhandenen Panels.**
Links Panel 1+3+5: 1435 LEDs, elf belegte Universen; rechts Panel 2+4: 1548 LEDs,
zehn belegte Universen. Das verteilt Empfang und Treiberlast ungefähr gleich
und folgt der räumlichen Anordnung. Beide Geräte müssen weiterhin ihre eigenen
Ports parallel betreiben. Bei vollständig serieller Ausgabe wären 43,95 ms
links und 47,04 ms rechts weiterhin zu lang für 30 FPS.

**Option D — zwei Controller für alle 4105 LEDs, 1122er Kette geteilt.**
Controller A: 203+738+680+442 = 2063 LEDs, 14 belegte Universen.
Controller B: 880+810+352 = 2042 LEDs, ebenfalls 14 belegte Universen. Die
Universumsnummern können erhalten bleiben, wenn Sender und Empfänger genau die
zugewiesenen Bereiche unterstützen; Lücken sollen nicht je Controller wieder
als vollständiger U120–148-Block übertragen werden. Der Aufwand sind eine
zusätzliche Controlleranbindung, passende Datenverdrahtung und überprüfte
Bildsynchronisation. Zwei Geräte im selben WLAN halbieren die gemeinsame
Funklast nicht, sondern verteilen primär die lokale Empfangs- und Ausgabelast.

## Entscheidende Messungen vor einer Hardwareentscheidung

1. Den gleichen vorberechneten Frame aus einem unabhängigen Senderprozess und
   aus TouchDesigner senden. Gleiches Ziel, gleiche Universen, gleiche Daten,
   gleiche Messdauer; keine gleichzeitigen Sender.
2. 5/10/15/20/25/30 FPS mit geeigneten Paketabständen vergleichen. Tatsächliche
   Sendezeit, Empfang vollständiger Bilder und physische Ausgabe getrennt
   bewerten. Ein Zähler „Pakete gesendet“ oder ein konfiguriertes `targetFps:30`
   ist kein 30-FPS-Erfolg.
3. Sechs aktive Ausgänge gegen fünf aktive Ausgänge vergleichen. Danach einzelne
   Ports beziehungsweise Portkombinationen testen: wächst `outputTimeUs` wie
   das Maximum oder eher wie die Summe der Kettenlängen?
4. Bei gleicher LED-Ausgabe gezielt die Empfangslast variieren. Steigt der
   Verlust mit der Paketrate, obwohl die Ausgabedauer konstant bleibt, spricht
   das eher für Empfang/Puffer/Scheduling als für das reine LED-Timing.
5. Kandidaten mit längerem Lauf bestätigen: beispielsweise 60 Sekunden mit
   erwarteten 1800 eindeutigen vollständigen Bildern bei 30 FPS, getrenntem
   Auslaufzeitraum und ohne Start-/Stop-Schwarzbilder in der Nutzmessung.
   Vollständigkeitsquote, Frameabstände und längste Lücke auswerten, nicht nur
   den Mittelwert. Optisch auf Ruckler und über Panelgrenzen versetzte Bilder
   prüfen.

Die Empfehlung ist deshalb zunächst **Software und konkrete Ausgangskonfiguration
messen**, dann bei nachgewiesener lokaler Controllerüberlastung aufteilen. Für
den späteren echten 30-FPS-Betrieb aller sechs Ausgänge bleibt die 1122er Kette
bei nominalem WS2812-Timing ein eigener, unabhängig vom Netzwerk zu lösender
Punkt.
