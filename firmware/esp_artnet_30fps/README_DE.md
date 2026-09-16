# Experimentelle ESP32 Art-Net / FastLED-Firmware

Diese neue Testfirmware ersetzt nicht automatisch sämtliche Funktionen der vorhandenen Firmware. Sie ist ausschließlich für einen identifizierten klassischen ESP32-Testcontroller vorgesehen. S3, C3, Web-Konfigurationseditor, OTA, ArtPoll, ArtSync, Quellen-Merge und beliebige dynamische Pinbelegung sind nicht implementiert.

## Reproduzierbarer Build (PowerShell)

Im Verzeichnis dieser README:

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install platformio==6.1.18 ziglang==0.13.0
$env:PLATFORMIO_CORE_DIR = 'C:/Users/jbhtz/AppData/Local/CodexESP30/pio'
$env:PLATFORMIO_BUILD_DIR = 'C:/Users/jbhtz/AppData/Local/CodexESP30/build'
./.venv/Scripts/python.exe -m platformio run -j 1 -e esp32_testnode_mixed
New-Item -ItemType Directory -Force build | Out-Null
./.venv/Lib/site-packages/ziglang/zig.exe c++ -std=c++17 -nostdlib++ -O2 -Iinclude test/test_frame_assembler.cpp -o build/test_frame_assembler.exe
./build/test_frame_assembler.exe
```

Für einen Vergleichsbuild im selben Cache kann ausschließlich der Projektcode
übersteuert werden, beispielsweise mit
`$env:PLATFORMIO_BUILD_SRC_FLAGS = '-DEXPERIMENTAL_PROFILE_OVERRIDE=1755'`.
Danach dieselbe Mixed-Umgebung bauen. Vor einem normalen768-Build diese Variable
entfernen. Kein kombiniertes `-U/-D PANEL_PROFILE` verwenden: SCons ordnet diese
Schalter um. Das Snapshotwerkzeug prüft die tatsächliche Größe des `leds`-Symbols
im ELF unabhängig vom Umgebungsnamen.

Die Rückwandprofile nutzen GPIOs 26,27,25,14,19,17 (GRB / WS2812B). Die Mixed-Profile verwenden WS an GPIO14 und APA102 DATA18/CLOCK19 mit Hardware-SPI4MHz; beide Treiber laufen gleichzeitig und synchronisieren vor dem nächsten Frame:

| Profil | Pixel pro Port | Startuniversen |
|---|---|---|
| esp32_testnode_mixed (physischer Testaufbau) | WS256, APA512 | 0,2 |
| esp32_virtual_mixed1755 (virtueller Lasttest) | WS731, APA1024 | 0,5 |
| esp32_single | 203 | 120 |
| esp32_five | 203,738,880,810,352 | 120,122,127,133,139 |
| esp32_six | 203,738,880,810,352,1122 | 120,122,127,133,139,142 |

Der letzte 1122-Pixel-Port kann mit nominellem WS2812-Timing keine echten 30 vollständigen Lichtbilder pro Sekunde darstellen. Das Sechsportprofil ist ein Vergleichs-/Grenztest, kein 30-FPS-Versprechen. Pixeladressierung verwendet 170 RGB-Pixel pro Universum; bei 512 DMX-Slots werden die letzten zwei Slots ignoriert. Kürzere Pakete sind nur erlaubt, wenn sie alle tatsächlich benötigten RGB-Kanäle des betreffenden Universums enthalten.

## USB und Netzwerk

115200 Baud, zeilenbasierte Befehle:

- `status`: JSON-Telemetrie.
- `wifi SSID<TAB>PASSWORT`: Netzwerkzugang, Tabulator als Trenner; Zugangsdaten bleiben in eigenem NVS-Namespace und werden nicht ausgegeben. DHCP, gewünschte `.151` bei Bedarf als Routerreservierung. Bestehende NVS-Namespaces werden nicht gelöscht.
- `ip ADDRESS MASK GATEWAY`: statische IPv4-Konfiguration speichern/anwenden, beispielsweise `ip 10.0.0.151 255.0.0.0 10.0.0.1`.
- `arm`: Ausgabe freigeben; verwirft davor empfangene Mailboxdaten und unvollständige Assemblerkandidaten. Erst hierbei werden LED-GPIOs initialisiert.
- `stop`: Ausgabe deaktivieren; letzter aktiver Output wird schwarz gesetzt.

HTTP: `GET /api/status`, `GET /api/config`, `POST /api/arm?enabled=true` bzw. `false`. Das Testinterface ist unverschlüsselt und ohne Login im lokalen Testnetz. Keine WLAN-Zugangsdaten in Git/Logs aufnehmen.

Nach Start und bei jedem neuen Arm müssen frische vollständige Frames eintreffen. Ohne vollständiges Frame wird nach einer Sekunde schwarz gesetzt. Feste Helligkeitsobergrenze16/255 (~6.3%), Zielsendetakt30FPS und Ausgabeobergrenze60FPS gegen Phasenaliasing. Höhere theoretische Ausgangsrate ist kein Ersatz für Messung. Der Host sendet als fest zugelassener einzelner Sender10.0.0.125 ArtDmx an UDP6454; für eindeutige Messung pro Bild eine gemeinsame Nichtnull-Sequenz 1..255 verwenden. Sender mit unabhängigen Sequenzen pro Universum benötigen eine andere Assemblierungsstrategie.

## Empfangsoptimierung V2

Die aktuelle Version bindet UDP6454 über die lwIP-Raw-API auf deren TCP/IP-Thread.
Ein Callback kopiert maximal531Bytes in eine begrenzte64-Paket-FreeRTOS-Queue
und gibt den Netzwerkpuffer sofort frei. Damit entfällt die SDK-Socketmailbox
mit nur sechs Datagrammen. `rawUdpQueueDrops`, `rawUdpQueuePeak`, Oversize- und
Epoch-Zähler machen die zusätzliche Schicht beobachtbar. Veraltete Queuepakete
werden bei ARM/STOP durch eine Generation verworfen. Quelle bleibt10.0.0.125.
Die historischen Socketfelder bleiben zur Kompatibilität vorhanden, messen
aber nicht die Größe der neuen Queue. WLAN-interne Verluste sind weiterhin
nur durch Sender-/Empfangsvergleich vollständig erkennbar.

Am virtuellen1755-Profil: zuvor16/898 vollständige Bilder in30s, danach
1800/1800 Bilder und21600/21600Pakete in60s. Beide Ausgänge bestätigten1799
Transfers; ein neueres Bild ersetzte nach Hostjitter das vorherige. Gemessen
29,983Ausgaben/s, keine Raw-Queue-Drops. Hardwaretests für malformed/oversize,
ARM mit altem Teilbild, frisches vollständiges Bild und STOP bestanden.

## Messprotokoll

Vor und nach jedem 20-s-Lauf `/api/status` lesen. Getrennt berichten: gesendete Bilder und Datagramme, vollständige Empfangsbilder, `outputFrames`-Delta, unvollständige Frames, Mailboxüberschreibungen, RSSI und Transferdauer. `outputFrames` steigt erst nach abgeschlossener WS- und gegebenenfalls APA-Übertragung. Die getrennten Transferzähler enthalten zusätzlich Schwarzübertragungen. Kamera oder Logic-Analyzer ergänzt den noch fehlenden optischen Nachweis.

```powershell
./.venv/Scripts/python.exe benchmark.py --run --seconds 20 --rates 5 15 30 --above-normal --output ../../docs/performance-program-20260912/esp/MEASUREMENT.json
```

Der Berichtspfad muss neu sein. `--above-normal` erhöht ausschließlich die Priorität dieses Windows-Senderprozesses bis zu dessen Ende. `--gap-ms 1` ist ein optionaler Kontrolltest für Burstverträglichkeit. Standardmäßig werden nur schwarze Bilder gesendet. `--pattern moving-dot` sendet einen roten Punkt am WS- und einen blauen Punkt am APA-Ausgang, Hostwert255 mit einmaliger Firmwarebegrenzung16/255. Keine doppelte Helligkeitsskalierung verwenden. Jeder Lauf deaktiviert die Ausgabe in einem `finally`-Block.

Die erste neue Physical768-Messung war durch PC-Speicherdruck begrenzt. Nach dem Schließen von Chrome erreichte der Aufbau900/900 bestätigte Ausgaben in30s und5400/5400 empfangenePakete ohne Teilbilder. Die abschließende Raw-V2-Messung über 120,002 s bestätigte alle 3.599 Bilder auf beiden Ausgängen und alle 21.594 Pakete: 29,991 FPS, keine Teilbilder, Queue-Drops oder Mailboxüberschreibungen. Das physische 768er-Profil ist wieder installiert und disarmed. Die Originalfirmware erreichte am kleinen Aufbau bereits29,77 Ausgabe-FPS; beim virtuellen12-Universen-Bursttest dagegen nur0,55–0,60. Artefakte und aktueller Status liegen unter `docs/performance-program-20260912/esp/`.

## Sicherung und reproduzierbare Artefakte

Zwei bytegleiche vollständige Originalflash-Backups liegen privat außerhalb Git. `snapshot_build.py` archiviert die nichtgeheimen Buildabschnitte mit Quellen und SHA256. `flash_verified.py` prüft beide privaten Originalbackups, die Artefakthashes und die USB-MAC, bevor es ausschließlich COM5 / E8-68-E7-0D-38-A4 schreibt. Der Flash ist kein Teststart: Boot bleibt deaktiviert und die tatsächliche `/api/config` muss zum angeschlossenen Aufbau passen. Die Produktionscontroller werden damit nicht verändert.
