# Ethernet für die ESP-LED-Controller

Recherche vom 12.09.2026, Preise pro Stück. Keine Bestellung und keine
Hardwareänderung ausgeführt. Preise sind die beim Abruf angezeigten Angebote;
Versand ist in allen folgenden Beträgen ausgeschlossen.

## Empfehlung für den bestehenden Aufbau

**Für einen ersten Vergleich ist ein W5500-SPI-Ethernet-Modul am vorhandenen
ESP32 der günstigste Ansatz: ungefähr A$10–15 für das Modul pro Controller.**
Das vermeidet einen vollständigen Boardwechsel und prüft gezielt, welchen
Anteil die Funkverbindung an den Verlusten hat. Vor dem Anschluss müssen jedoch
freie GPIOs und die Firmwareanbindung geprüft werden. Das Modul ist kein
Adapter, der ohne Firmwareänderung an einen beliebigen ESP angeschlossen wird.

Der PC ist bereits per Ethernet unter 10.0.0.125 angeschlossen. Der sinnvolle
Aufbau ist daher PC → vorhandener Router/Switch → je ein Netzwerkkabel zum
ESP-Ethernet-Modul. Ein weiterer PC-Netzwerkadapter ist bei ausreichend freien
Switchports nicht erforderlich. Benötigt werden zusätzlich Kabel und eventuell
ein Switch; deren Anzahl und Länge sind noch offen und nicht in den Modulpreisen
enthalten.

Ein ESP32-S3-Board mit Ethernet ist eine mögliche spätere Plattform, aber nicht
automatisch ein fertiger Ersatz für unseren Controller mit sechs LED-Ausgängen.
GPIO-Verfügbarkeit, Ausgangstreiber und elektrische LED-Anschlüsse müssen auch
hier passen.

## Konkrete Preisbeispiele

| Produkt / Händler | Angezeigter Stückpreis | Steuer / Verfügbarkeit / Einordnung |
| --- | ---: | --- |
| W5500 Ethernet-Modul, Zaitronics Z0246 | **A$9,90** | Inkl. GST; A$9,00 ex GST. Seite nennt 5–10 Tage bis Versand, zeigt gleichzeitig „Unavailable“; Lieferbarkeit vor Bestellung klären. [Angebot](https://zaitronics.com.au/products/ethernet-w5500-wiznet-network-module) |
| W5500 SPI-Ethernet-Modul, AUSCOM | **A$13,20** | Inkl. GST; beim Abruf 10 Stück auf Lager. Lokales Preisbeispiel für eine einfache Nachrüstung. [Angebot](https://www.auscomtech.com.au/product/w5500-ethernet-network-module-spi-tcp-ip-lan-for-arduino-esp32-stm32/) |
| Waveshare ESP32-S3-ETH, Hersteller-AUD-Katalog | **A$24,50–37,47** | Angezeigte Spanne für Varianten des Boards/der Kits; GST im ausgewerteten Katalog nicht ausgewiesen. Basis, Pinheader, Kamera und PoE-Varianten unterscheiden sich. Kein australischer Endpreis inklusive Import/Versand. [AUD-Katalog](https://www.waveshare.com/product/index.htm?dir=desc&limit=20&mode=grid&order=name&p=55) |
| Waveshare ESP32-S3-ETH, Hersteller-Produktseite | **US$16,99–25,99** | Vergleich der Herstellerpreise in USD, ausdrücklich **nicht AUD**. Nicht zusätzlich zum obigen Boardpreis addieren; gleiche Produktfamilie. [Produktseite](https://www.waveshare.com/product/iot-communication/wired-comm-converter/esp32-s3-eth.htm) |
| SparkFun MicroMod W5500 Function Board, Core Electronics COM-18708 | **A$65,25** | Inkl. GST, ausverkauft. Benötigt passende MicroMod-Träger-/Prozessorhardware und ist für unsere einfache ESP-Nachrüstung unpassend teuer. [Angebot](https://core-electronics.com.au/sparkfun-micromod-ethernet-function-board-w5500.html) |

Damit beträgt der reine Nachrüst-Modulpreis für drei Controller anhand der
beiden lokalen Beispiele A$29,70 bis A$39,60 inklusive GST. Arbeitszeit,
Firmwareanpassung, Gehäuse, Versorgung, Steckverbinder und Netzwerkkabel sind
nicht eingerechnet. **Für einen Pilotversuch genügt zunächst ein Modul.** Die
Waveshare-AUD-Anzeige ist ein Preisanker, keine zugesicherte australische
Endsumme. Einen einfachen nackten W5500-Nachrüstbaustein bei Core Electronics
konnte diese Recherche nicht mit günstigerem belastbarem Angebot belegen.

## W5500 statt LAN8720 an den vorhandenen Pins

Die aktuelle Controllerkonfiguration belegt LED-Datenpins 26, 27, 25, 14, 19
und 17. Die feste RMII-Belegung des klassischen ESP32 kollidiert mit mehreren
dieser Ausgänge:

| GPIO | Derzeit LED-Ausgang | RMII-Funktion |
| --- | --- | --- |
| 26 | Panel 1 | RXD1 |
| 27 | Panel 2 | CRS_DV |
| 25 | Panel 3 | RXD0 |
| 19 | Panel 5 | TXD0 |

Ein LAN8720-PHY an RMII wäre daher **kein einfacher Zusatz bei unveränderter
LED-Verdrahtung**. Diese Datenpins lassen sich beim klassischen ESP32 nicht
beliebig per GPIO-Matrix verschieben. GPIO17 kann außerdem je nach gewählter
RMII-Takterzeugung zusätzlich betroffen sein.
[Espressif: Ethernet-Kit, RMII-Pinbelegung](https://docs.espressif.com/projects/esp-idf/en/v4.2.3/esp32/hw-reference/esp32/get-started-ethernet-kit.html)

Der W5500 verwendet stattdessen SPI: Takt, MOSI, MISO und Chip Select, dazu je
nach Treiber Reset und Interrupt. SPI kann über die GPIO-Matrix auf geeignete
andere Pins gelegt werden. Die übliche ESP32-VSPI-Belegung verwendet allerdings
GPIO19 als MISO und würde ebenfalls mit Panel 5 kollidieren. Deshalb muss die
Belegung bewusst gewählt werden; vorhandene APA102-Ports, Flash/PSRAM,
Boot-Pins, herausgeführte Anschlüsse und nur als Eingang nutzbare Pins sind
mitzuprüfen. Hier wird noch kein Verdrahtungsplan als freigegeben erklärt.
[Espressif: SPI Master und GPIO-Matrix](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/spi_master.html)

Espressifs Ethernet-Treiber unterstützt externe SPI-Ethernet-Controller. Die
Firmware muss den W5500 initialisieren, Link und IP-Konfiguration behandeln und
unseren Art-Net-Empfang sowie das Webmenü an die Ethernet-Schnittstelle anbinden.
Erst dann wird aus dem Zusatzmodul eine nutzbare kabelgebundene Verbindung.
[Espressif: Ethernet-Treiber](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/network/esp_eth.html)

## Was Ethernet verbessern kann

Für die bisher gesendeten 29 Universen bei 30 FPS fallen ungefähr 870
ArtDmx-Pakete/s beziehungsweise 3,87 Mbit/s einschließlich IPv4/UDP an; die
Berechnung steht in `CAPACITY_RESEARCH_DE.md`. Ein 100-Mbit-Ethernet-Link hat für
diese mittlere Datenrate reichlich nominelle Reserve. Der W5500 und das
Waveshare-S3-ETH-Board bieten 10/100-Mbit-Ethernet; beim S3-Board sitzt der W5500
bereits auf der Platine und ist über SPI angeschlossen.
[Waveshare: ESP32-S3-ETH](https://www.waveshare.com/product/iot-communication/wired-comm-converter/esp32-s3-eth.htm)

Die erwartete Verbesserung ist vor allem gleichmäßigerer Empfang ohne
Funkkanalkonkurrenz, WLAN-Neuverbindungen und WLAN-Energiesparpausen. Wird WLAN
im Controller während des Ethernet-Betriebs deaktiviert, entfällt zudem dessen
Interruptlast. Das ist für ESP-Ausgabetreiber relevant: Espressif beschreibt
Konflikte zwischen RMT-Verarbeitung und WLAN-Interrupts.
[Espressif: RMT-FAQ](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/peripherals/rmt.html)

Das ist eine begründete Erwartung, **kein bereits gemessener Ethernet-Gewinn
unseres Systems**. Auch mit Kabel können unzureichende Empfangspuffer,
blockierende Firmware, SPI-Transferkosten und unvollständige Frame-Zusammenführung
Pakete verlieren. Der W5500 macht eine ineffiziente LED-Ausgabe nicht automatisch
parallel. Die 1122 LEDs auf einem einzelnen WS2812-Port benötigen bei nominal
800 kbit/s weiterhin 33,66 ms reine Datenzeit; Ethernet verkürzt diese nicht.

## ESP32-S3-Ethernet als neue Plattform

Das Waveshare-Board kombiniert ESP32-S3R8, 8 MB PSRAM, 16 MB Flash und W5500.
SD-Karte, Kameraanschluss und weitere Peripherie teilen sich GPIO-Ressourcen.
Die Header allein sind deshalb kein Nachweis, dass sechs oder sieben für unsere
LEDs geeignete freie Anschlüsse vorhanden und gleichzeitig nutzbar sind.
[Waveshare: Boarddetails](https://www.waveshare.com/product/iot-communication/wired-comm-converter/esp32-s3-eth.htm)

Der S3 unterstützt RMT mit DMA, was CPU-Arbeit reduzieren kann. Er besitzt aber
**vier RMT-TX-Kanäle und vier RX-Kanäle**, nicht acht unabhängige TX-Kanäle.
Deshalb darf „S3 mit DMA“ nicht pauschal als Lösung für sechs parallele
LED-Datenausgänge verkauft werden. Dafür braucht es einen geeigneten anderen
Parallel-Ausgabetreiber, eine überprüfte zeitliche Kanalaufteilung oder mehrere
Controller. Auch die konkrete DMA-Ressourcenzuteilung muss zum Treiber passen.
[Espressif: Variantenvergleich, RMT-Kanäle](https://docs.espressif.com/projects/esp-idf/en/v5.0.3/esp32s3/esp-idf-en-v5.0.3-esp32s3.pdf),
[Espressif: S3-RMT-DMA](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/rmt.html)

Für uns ist die Reihenfolge daher: **ein W5500-Modul und eine passende
Firmwareanbindung als Vergleich prüfen**, danach Empfang und tatsächliche
LED-Ausgabe gegen die WLAN-Messungen vergleichen. Erst der gemessene Restengpass
entscheidet, ob weitere Nachrüstmodule genügen oder ein neues Controllerdesign
mit geprüften parallelen Ausgängen sinnvoller ist.
