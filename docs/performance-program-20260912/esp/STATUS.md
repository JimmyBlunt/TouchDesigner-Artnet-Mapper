# ESP Art-Net: Arbeitsstand und Testgrenzen

Stand: 2026-09-12. Neue experimentelle Firmware, keine belegte Funktionsgleichheit mit der vorhandenen Controller-Firmware.

## Aktueller Hardwarestand

Die experimentelle Mixed-Firmware ist auf dem verifizierten Testboard installiert. Esptool bestätigte die Prüfsummen aller vier geschriebenen Bereiche. Ein unverändertes, doppelt gelesenes vollständiges Originalbackup ist vorhanden.

- **COM5 / MAC E8-68-E7-0D-38-A4 / IP10.0.0.151**.
- Laufzeit und HTTP-Konfiguration geprüft: Profil768, WS256 an GPIO14/U0–1 und APA512 an DATA18/CLOCK19/U2–5.
- Ausgabe nach allen Tests deaktiviert. LED-GPIOs werden erst nach ARM initialisiert.
- WLAN-Zugang ohne erneute Eingabe übernommen; RSSI−38 bis−40dBm, rund228kB freier Heap vor Treiberinitialisierung.
- Binärdatei und genaue Quellen im Paket `esp-firmware-physical768-socket-v1.zip`; Build- und Flashmanifeste enthalten SHA256 und Identitätsnachweise. Firmware-SHA256: `3c93a10dc2c5796f60aec11b8a441bfb9b2ad18f2d345df81fdd671b016e5a40`.
- Physical768-Schwarz- und Punkttests abgeschlossen; Ergebnisse unten. Virtual1755 wird anschließend mit einem Compilerjob inkrementell gebaut und gemessen.

### Neue Firmware: bisherige Hardwaremessung

| Test | angefordert | Host-FPS | abgeschlossene Ausgabe/s | vollständige / gesendete Frames |
|---|---:|---:|---:|---:|
| Physisch768, schwarz | 5 | 4.934 | 4.884 | 98/99 |
| Physisch768, schwarz | 15 | 13.089 | 12.940 | 259/262 |
| Physisch768, schwarz | 30 | 23.032 | 22.882 | 458/461 |
| Physisch768, sichtbarer Punkt,8 s | 30 | 14.694 | 14.323 | 116/119 |

Der erste30-FPS-Lauf erlitt65 Hostoverruns und bis243 ms Abstand zwischen Frames; der sichtbare Lauf57 Overruns. Das ist keine isolierte ESP-Leistungsgrenze. In allen vier Fällen entsprachen die getrennten WS-/APA-Transferdeltas exakt den ausgegebenen vollständigen Bildern; keine Mailboxüberschreibungen. Rot am WS-Ausgang und Blau am APA-Ausgang wurden mit Hostwert255 und einmaliger Firmwarebegrenzung16/255 gesendet. Eine optische Bestätigung liegt nicht vor.

Rohdaten: `experimental-physical768-socket-v1.json`, `experimental-physical768-visible-socket-v1.json`. Der Sender bietet jetzt optional AboveNormal nur für seinen eigenen Prozess. Ein belastbarer Nachweis stabiler30-FPS-Ausgabe der neuen Firmware steht noch aus.

Die Originalfirmware-Baseline unter `.251` wurde vor dem Flash abgeschlossen und ihre Konfiguration exakt restauriert. `.248` und `.244` bleiben unverändert. `version-control-whitelist.json` nennt die zur Versionierung vorgesehenen Dateien; private Flashbackups mit möglichen WLAN-Zugangsdaten sind ausdrücklich ausgeschlossen.

## Aktuelle Messergebnisse vor dem Firmwarewechsel

Der USB-Testcontroller war mit der Originalfirmware tatsächlich unter **10.0.0.251** erreichbar. Die Zuordnung wurde über Bootprotokoll, identische gespeicherte Konfiguration und ARP-MAC `E8-68-E7-0D-38-A4` auf Ethernet 3 bestätigt. Die neue Testfirmware ist inzwischen unter `.151` eingerichtet und erneut per ARP-MAC bestätigt.

Alle folgenden Läufe sendeten ausschließlich Schwarz. Die Originalkonfiguration wurde anschließend jeweils exakt zurückgesetzt und nochmals schwarz ausgegeben. `.248` und `.244` wurden nicht verändert.

| Profil | Universen | Paketabstand | Host-FPS | gemeldete Ausgabe-FPS | vollständige / unvollständige Frames |
|---|---:|---:|---:|---:|---:|
| Physisch ca.256 WS +512 APA, Ausgabelimit30 | 6 | 0ms | 29.816 | 29.766 | 597 /0 |
| Physisch ca.256 WS +512 APA, Ausgabelimit60 | 6 | 0ms | 29.126 | 29.126 | 583 /0 |
| Virtuell731 WS +1024 APA, Ausgabelimit30 | 12 | 0ms | 29.697 | 0.550 | 11 /583 |
| Virtuell731 WS +1024 APA, Ausgabelimit60 | 12 | 0ms | 28.709 | 0.599 | 12 /563 |
| Virtuell731 WS +1024 APA, Ausgabelimit60 | 12 | 1ms | 27.592 | 13.996 | 280 /257 |

Beim virtuellen Test blieben physisch dieselben Panels angeschlossen; lediglich längere Datenketten wurden schwarz übertragen. Das ist kein optischer Nachweis für1755 vorhandene LEDs. Die unterschiedliche gemessene Hostrate berücksichtigt Compilerlast und Paketabstände; sie darf nicht der Firmware zugeschrieben werden. Rohdaten: `original-baseline*.json`.

Der kleine Aufbau erreicht somit bereits mit der Originalfirmware nahezu die Senderate. Bei zwölf Universen bricht dagegen die Paketannahme bzw. Zusammensetzung vollständiger Bilder ein. Ein Millisekundenabstand verbessert dies deutlich. Das ist kein Nachweis einer allgemeinen WLAN-Bandbreitengrenze.

Im SDK der experimentellen Firmware wurde eine UDP-Empfangsmailbox mit sechs Datagrammen gefunden (`CONFIG_LWIP_UDP_RECVMBOX_SIZE=6`); `SO_RCVBUF` vergrößert diese Slotanzahl nicht. Der neue dedizierte Socket-Empfänger wird gemessen; eine Raw-UDP-Anwendungsqueue ist eine gezielte weitere Option, falls auch dort Burstverluste auftreten. Die konkrete Originalfirmwarequelle bleibt unbekannt.

## Erledigt / in Prüfung

- Vorhandene ESP-Quellen erneut im Projektparent gesucht; keine `.ino`/`platformio.ini`/Firmwarequelle gefunden. Vorheriger Audit hatte zusätzliche Benutzerordner ohne Treffer durchsucht.
- Testnode `10.0.0.151`: `/api/status` und `/api/config` antworteten beim ersten Versuch nicht.
- USB-Treiberproblem behoben: offizieller, gültig signierter Silicon-Labs-Treiber 11.6.0.420 via Windows-UAC installiert. `USB\\VID_10C4&PID_EA60\\0001` ist jetzt **COM5**, PnP Status OK.
- esptool 4.8.1 identifiziert ESP32-D0WD Revision 1.0, Dual Core 240 MHz, 4 MB Flash, MAC `e8:68:e7:0d:38:a4`. Zwei vollständige 4-MB-Lesungen bei 230400 Baud sind bytegenau identisch: SHA256 `213b16a2e37df6435a4262552063cb8921fe1ea9b04ea194562d83cc8fb4da1d`. Backups privat außerhalb Git; Manifest `backup-verification.json`. Ein erster Versuch bei 460800 unter Compilerlast wurde wegen beschädigtem Datenpaket verworfen. Kein Flash verändert.
- Aktive NVS-Konfiguration gesichert: WS2812B 731 Pixel an GPIO14, GRB, U0; APA102 1024 Pixel DATA18/CLOCK19, BGR, 4 MHz, U4. U4 überschneidet sich; diese Konfiguration wird nicht als valide parallele Topologie übernommen.
- **Nutzerkorrektur:** tatsächlich ca. 256 WS2812 + 512 APA102 an beiden genannten Ausgängen angeschlossen. Physisches Testprofil `esp32_testnode_mixed`: WS256 GPIO14 U0–1, APA512 DATA18/CLOCK19 U2–5, insgesamt768 Pixel, keine Überlappung. Die gespeicherten1755 Pixel sind kein Nachweis der physischen Kettenlänge. Separates virtuelles1755-Lastprofil vorhanden.
- Gemischte Ausgabe vorbereitet: WS2812 per FastLED-I2S und APA102 per Hardware-SPI4MHz laufen gleichzeitig, mit Completionbarriere vor dem nächsten Frame. Feste Helligkeitsobergrenze16/255 (~6.3%). Senderziel30FPS, interne Ausgabeobergrenze60FPS als Spielraum gegen Phasenaliasing zweier unabhängiger30Hz-Takte; echte Rate wird gemessen.
- GPIO-Schutz: FastLED-Pininitialisierung vollständig bis zum ausdrücklichen ARM verschoben. Disarmed Boot/Flash nutzt keine LED-GPIOs.
- Peer-Review: Assemblerkandidat/Sequenzzustand werden bei ARM/STOP zurückgesetzt, sodass ein vor ARM begonnenes Teilbild nicht vervollständigt wird. UDP-Quelle ist auf 10.0.0.125 gepinnt. Ausgabe-FPS-Status nutzt konsistenten Snapshot.
- Isolierte PlatformIO-6.1.18-Installation. Wegen Windows-Pfadlängen liegen Toolchain/Buildcache unter `C:/Users/jbhtz/AppData/Local/CodexESP30/`; Quellcode bleibt im Repository.
- Firmwarecode: FastLED 3.9.15, klassischer ESP32-I2S-Paralleltreiber, separate Empfangs-/Ausgabetasks, Datagramm-Burstdrain, vollständige Frames, Mailbox mit neuestem vollständigem Frame, Einsekunden-Blackout, Boot mit deaktivierter Ausgabe.
- **12 C++-Hosttestgruppen bestanden**: RGB510/512-Routing, kurze/malformed Pakete, fehlende/duplizierte/späte Universen, Sequenzwechsel255→1, Timeout/Zeitzählerüberlauf, ARM-Kandidatreset, Konfigurationsgrenzen, APA102-BGR-Framing/Helligkeit/Endtakte,10000 vollständige28-Universen-Frames. `host-tests.json` enthält Quellenhashes. Zig ist beendet.
- Erster Single-WS-Crossbuild erfolgreich (786793Byte Flash,48024Byte RAM); Mixed768 erfolgreich (792753Byte Flash,55328Byte RAM) und verifiziert geflasht. Weitere Builds laufen mit **einem** Job; Abhängigkeiten und Buildcache liegen außerhalb OneDrive. Quellcode bleibt im Repository. Kein eigener Compilerprozess ist noch angehalten.

## Messbarkeit

`/api/status` trennt Datagramme, akzeptierte Universen, vollständige/unvollständige Frames, überschriebene Mailboxframes und `FastLED.show()`-Aufrufe. `showCallUs` misst die Dauer des Treiberaufrufs, keine gesicherte Draht-/Lichtdauer. Netzwerkverluste können nur mit Senderzähler plus Empfangszähler bestimmt werden; ein eigenständiger lwIP-Dropzähler ist nicht verfügbar.

Nichtnull-ArtDmx-Sequenzen werden als gemeinsame Bildkennung über alle Universen verlangt. Sequenz null bleibt mit bestehenden Sendern kompatibel, erlaubt nach Paketverlust aber keinen sicheren Nachweis gegen das Vermischen von Bildern. Für Messungen sind fortlaufende gemeinsame Bildsequenzen erforderlich. Das ist eine begrenzte ArtDmx-Empfangsimplementierung für einen einzelnen Sender, kein vollständiger Art-Net-Knoten mit Discovery, Merge oder ArtSync.

## Durchgeführter Schutz vor dem ersten Flash

1. Offiziellen Silicon-Labs-CP210x-Treiber installieren und COM-Port erkennen.
2. Chiptyp, MAC und Flashgröße mit esptool lesen; vollständiges Flashbackup lokal sichern und per zweitem Lesen/Hash prüfen. Backups können WLAN-Zugangsdaten enthalten und werden nicht eingecheckt.
3. Tatsächliche Pinbelegung und LED-Anschluss des Testboards klären. Verwendet wird das bestätigte Mixed768-Profil; es bleibt nach Boot deaktiviert.
4. Erst dann ausschließlich das identifizierte Testboard flashen. Keine Eingriffe in `.248` oder `.244`.
5. WLAN-Provisionierung über USB; anschließend kontrollierte 5/15/30-FPS-Tests erst nach zentraler Freigabe des LED-Testfensters.

## Quellen

- [FastLED 3.9.15: klassischer ESP32-I2S-Treiber](https://github.com/FastLED/FastLED/blob/3.9.15/src/platforms/esp/32/clockless_i2s_esp32.h)
- [Espressif Arduino Network API](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/network.html)
- [Art-Net-Protokoll](https://art-net.org.uk/downloads/art-net.pdf)
- [Silicon Labs offizieller CP210x-Treiber](https://www.silabs.com/software-and-tools/usb-to-uart-bridge-vcp-drivers?tab=downloads)
