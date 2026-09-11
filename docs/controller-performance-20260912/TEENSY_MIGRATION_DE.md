# Teensy 4.1 mit FastLED: Migrationsbewertung

Stand 12. September 2026. Recherche und Planung, keine Bestellung, kein
Firmwarebau, kein Flashen und keine Änderung an laufender Hardware.
Benutzerentscheidung: **FastLED verwenden; keine Octo-Adapterplatine und keine
OctoWS2811-Konfiguration als Umsetzung vorschlagen.**

## Eignung für unser Setup

Ein Teensy 4.1 mit echtem kabelgebundenem Ethernet und FastLEDs parallelem
ObjectFLED-Treiber ist ein sinnvoller Kandidat, um den nachgewiesenen
Mehrportengpass des jetzigen ESP32 zu umgehen. Das ist eine technisch
begründete Erwartung und noch kein gemessenes Ergebnis dieses Aufbaus.
Der Teensy bringt einen 600-MHz-Cortex-M7 und 10/100-Mbit-Ethernet mit;
die Ethernet-Variante enthält den PHY, benötigt aber zusätzlich die
RJ45-Magnetics-/Steckerplatine. [PJRC Teensy 4.1](https://www.pjrc.com/store/teensy41.html)

FastLED dokumentiert für Teensy 4.x den ObjectFLED-Treiber als Standard für
WS2812. Mehrere Datenpins werden parallel ausgegeben; das offizielle Beispiel
zeigt mehrere `FastLED.addLeds(...)`-Registrierungen und einen gemeinsamen
`FastLED.show()`-Aufruf. Für uns sind zunächst fünf, später sieben physische
Ausgänge relevant, nicht die beworbenen maximalen Kanalzahlen.
[FastLED README](https://github.com/FastLED/FastLED/blob/master/README.md),
[TeensyMassiveParallel-Beispiel](https://github.com/FastLED/FastLED/blob/master/examples/TeensyMassiveParallel/TeensyMassiveParallel.ino)

Die Aussage „FastLED ist schneller“ muss sich auf die konkret ausgewählte
Teensy-Ausgabe beziehen. Ein Bibliotheksname allein garantiert weder
Parallelität noch durchgehend freien Empfang während `show()`. Die
Bibliotheksversion und der tatsächlich verwendete Treiber werden daher im
Build festgeschrieben und mitgemessen. Das vorhandene Material-/Mapping-
Rendering bleibt in TouchDesigner und muss weiterhin 30 neue Bilder/s liefern.

## Grenzen durch die Datenketten

Bei nominal 800 kbit/s und 24 RGB-Bits braucht jede LED 30 µs reine Datenzeit.
Das ist eine eigene Zeitbudgetrechnung; die Zusatzzeit für Reset und Treiber
kommt hinzu. Parallelität sorgt dafür, dass die längste Kette maßgeblich ist.

| Bereich | LEDs | Reine Datenzeit | Einordnung für 30 FPS |
|---|---:|---:|---|
| Panel 1 | 203 | 6,09 ms | ausreichend Reserve |
| Panel 2 | 738 | 22,14 ms | grundsätzlich passend |
| Panel 3 | 880 | 26,40 ms | längste eingemessene Kette, grundsätzlich passend |
| Panel 4 | 810 | 24,30 ms | grundsätzlich passend |
| Panel 5 | 352 | 10,56 ms | ausreichend Reserve |
| bisherige Reserve an Port 6 | 1122 | 33,66 ms | überschreitet 33,33 ms schon vor Reset |

Für die fünf eingemessenen Panels ist ein Teensy deshalb ein plausibler
Ein-Controller-Ansatz für 30 FPS. Der 1122er-Strang bleibt auch am Teensy
ein Sonderfall. Eine robust planbare Lösung ist eine physische Aufteilung
in 680 und 442 LEDs. Keine Verkürzung der LED-Bitzeiten oder LED-Übertaktung
als Voraussetzung für das Ziel einplanen.

## Bestehende Scans und Universen erhalten

Die neue Firmware empfängt die vorhandenen absoluten Art-Net-Universen,
510 Datenkanäle/170 RGB-Pixel pro Universe, ArtDMX auf UDP 6454 und zunächst
Sequenz 0 entsprechend dem bestehenden Sender. RGB aus dem Netzwerk wird
an den WS2812B-Ausgängen in die bisherige GRB-Reihenfolge umgesetzt. Das
ist ein Kompatibilitätsvertrag für die neue Firmware, kein automatisches
Merkmal eines beliebigen Teensy-Beispielsketches.

| Logischer Bereich | Neuer physischer Ausgang | Universe-Bereich | lokale LEDs |
|---|---:|---|---|
| Panel 1 | 1 | U120–121 | 0–202 |
| Panel 2 | 2 | U122–126 | 0–737 |
| Panel 3 | 3 | U127–132 | 0–879 |
| Panel 4 | 4 | U133–137 | 0–809 |
| Panel 5 | 5 | U139–141 | 0–351 |
| bisheriger Strang 6, erster Teil | 6 | U142–145 | bisherige IDs 0–679 |
| bisheriger Strang 6, zweiter Teil | 7 | U146–148 | bisherige IDs 680–1121 |

U138 bleibt unbelegt. Die Trennung bei 680 ist bewusst auf einer
Universe-Grenze gewählt: 4 × 170 Pixel. Am zweiten physischen Ausgang
beginnt der Teilstrang bei seiner Hardware-LED 0, logisch bleibt dies
Pixel 680 des bisherigen Strangs. Dafür muss die Datenleitung tatsächlich
nach der 680. LED getrennt und der zweite Teil separat angesteuert werden.
Das ist eine geplante spätere Verkabelungsänderung, jetzt nicht ausgeführt.

Panelgeometrie, Orientierung, globale Source-IDs, UVs, Fehlstellenmasken
und gesicherte Kameraansichten können unverändert bleiben. Für Panel 1–5
ist kein erneutes Scannen erforderlich, wenn die Firmware genau diesen
Adressierungsvertrag erfüllt. Die tatsächliche Ziel-IP wird bei der
Migration bewusst festgelegt; zwei aktive Geräte erhalten nicht dieselbe IP.

## Empfangsarchitektur

QNEthernet ist eine passende Bibliothek für den nativen Ethernetanschluss.
Die dokumentierte Standard-UDP-Warteschlange fasst nur **ein** Paket.
Der Konstruktor erlaubt größere Kapazität; die Bibliothek bietet außerdem
Queuebelegung und verworfene Empfangspakete als Diagnosewerte.
[QNEthernet, UDP receive buffering](https://github.com/ssilverman/QNEthernet#udp-receive-buffering)

Unser Startentwurf sieht eine ausdrücklich konfigurierte Kapazität von
64 Paketen vor; diese Zahl ist eine zu prüfende Entwurfsentscheidung,
keine Herstellerempfehlung. Empfang fortlaufend abarbeiten, während ein
separater Bildpuffer das zuletzt vollständig empfangene Bild enthält.
Erwartet werden nur Universen tatsächlich aktivierter Ausgänge. Der Sender
darf keine vollständigen Bilder durch ein wartendes `show()` verlieren.
Bei Rückstau die neueste vollständige Darstellung bevorzugen und veraltete
Bilder gezielt zählen, anstatt unbegrenzt Latenz aufzubauen.

Erforderliche Diagnosen: eingegangene Pakete, fehlende Universen,
vollständige Bilder, wirklich gestartete Ausgaben, Queue-Maximum,
Empfangsverluste, `show()`-Aufrufdauer, DMA-/Reset-Busyzeit und maximale
Zeit ohne Bearbeitung des Empfangs. Ein alleiniger `fps`-Wert reicht nicht.

## FastLED-Version und asynchrone Ausgabe ausdrücklich prüfen

Die FastLED-Releasehistorie beschreibt den eingeführten ObjectFLED-Pfad als
asynchronen DMA-Treiber. [FastLED Release Notes](https://github.com/FastLED/FastLED/blob/master/release_notes.md)
Beim aktuellen Quellstand sind die Aussagen in den unterschiedlichen
Abstraktionsebenen jedoch nicht vollständig konsistent: Die Channel-Engine
kommentiert `show()` als synchron und gibt bei `poll()` sofort READY zurück,
während das darunterliegende Interface aktive DMA-/Latch-Busyzeit beschreibt.
Das ist ein Grund, **den gewählten API-Pfad auf echter Hardware zu messen**,
statt Nichtblockierung pauschal zu versprechen.
[Channel-Engine-Quellcode](https://github.com/FastLED/FastLED/blob/master/src/platforms/arm/teensy/teensy4_common/drivers/objectfled/channel_engine_objectfled.cpp.hpp),
[ObjectFLED-Interface](https://github.com/FastLED/FastLED/blob/master/src/platforms/arm/teensy/teensy4_common/drivers/objectfled/iobjectfled_peripheral.h)

Vorgabe für den späteren Build: konkrete FastLED-/Teensy-Core-/QNEthernet-
Versionen pinnen, Treiberauswahl im Build protokollieren und identische
WS2812B-Timings für alle betroffenen Ports verwenden, damit sie in einer
parallelen Timinggruppe landen. Einen stillen Rückfall auf einen anderen
Ausgabetreiber erkennen. Kein blindes Aktualisieren auf wechselndes `master`.

## Benötigte Hardware und Preisorientierung

- Teensy 4.1 **mit Ethernet-PHY**, nicht die als „without Ethernet“/`NE`
  angebotene Variante. PJRC listet beide ausdrücklich getrennt.
- Passender Ethernet-MagJack-/RJ45-Kit am dedizierten Ethernetheader.
- Geeignete 3,3→5-V-Datenpuffer, beispielsweise eine geprüfte
  74AHCT125-/74AHCT245-Lösung, mit getrennt zu prüfender Pinbelegung und
  gemeinsamer Masse. Die genaue Ausgangsplatinenauswahl ist noch offen.
  Die genannten AHCT-Bausteine haben TTL-kompatible Eingänge und werden
  mit 4,5–5,5 V versorgt: [TI SN74AHCT125](https://www.ti.com/product/SN74AHCT125),
  [TI SN74AHCT245](https://www.ti.com/product/SN74AHCT245).
- Passende Header, Anschlüsse und Verdrahtung für fünf bzw. sieben Datenpins.

Preisbeispiel eines australischen Händlers, am 12. September 2026 geprüft:
Teensy 4.1 **A$52,95 inkl. GST**, Ethernet-Kit **A$16,10 inkl. GST**,
zusammen **A$69,05** vor Versand, Ausgangspuffern und Anschlussmaterial.
Das ist kein vollständiger Aufbaupreis und keine Bestellung.
[Core Electronics Teensy 4.1](https://core-electronics.com.au/teensy-4-1.html),
[Core Electronics Ethernet-Kit](https://core-electronics.com.au/ethernet-kit-for-teensy-4-1.html)

Die vorhandene ESP32-Firmware läuft nicht unverändert auf dem Teensy.
Art-Net-Empfang, Portkonfiguration, Diagnose-API, Blackout und Speicherung
müssen implementiert bzw. portiert und geprüft werden. Eine Weboberfläche
ist ein zusätzlicher Softwareteil, kein Bestandteil des bloßen Boardtausches.

## Abnahme vor der Umschaltung

1. Firmwarekompilierung und Offline-Pakettests für alle unveränderten
   Universe-Grenzen, 510-Byte-Daten, Farben und Fehlstellen.
2. Je Ausgang erster/letzter Pixel und Übergänge bei 169/170 prüfen.
3. Einen 880er-Port und anschließend alle fünf Panels mit externer
   Testquelle 30 FPS betreiben; Paket- und Ausgaberaten getrennt messen.
4. Mindestens zehn Minuten mit allen fünf Ports prüfen, zunächst geringe
   Helligkeit, danach bewegte Animationsdaten. Jede neue Darstellung muss
   als solche erkennbar sein; wiederholte Frames zählen nicht als neue 30 FPS.
5. Erst danach den identischen Versuch aus TouchDesigner durchführen.
   Der Controllerwechsel ersetzt die noch laufende PC-Optimierung nicht.

Fazit für die Entscheidung: **Teensy 4.1 + FastLED + natives Ethernet ist
ein gut begründeter nächster Hardwareansatz.** Für Panel 1–5 ist 30 FPS
realistisch planbar, aber erst der konkrete Firmware-/Hardwaretest liefert
den Nachweis. Die 1122er-Kette benötigt für strikte 30 FPS eine separate
Längenlösung; sieben parallele Ausgänge nach dem vorgeschlagenen Split
würden die längste Kette wieder auf 880 LEDs begrenzen.
