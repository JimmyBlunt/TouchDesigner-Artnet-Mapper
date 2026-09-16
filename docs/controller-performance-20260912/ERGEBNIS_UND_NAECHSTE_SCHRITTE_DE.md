# Controller 248: Messungen und Optimierung vom 12.09.2026

Ziel sind 30 vollstÃ¤ndige Bilder pro Sekunde auf der vorhandenen Installation.
Dieses Ziel ist auf dem derzeitigen ESP32 mit mehreren aktiven AusgÃ¤ngen **noch
nicht erreicht**. Drei Agenten untersuchten Sender, Controllergrenzen und
Hardwarealternativen; sÃ¤mtliche physischen Tests fÃ¼hrte ein einziger Sender aus.
Die Tests sendeten ausschlieÃŸlich schwarze RGB-Daten. Keine Firmware wurde
geflasht, keine Verdrahtung geÃ¤ndert und keine Hardware bestellt.

## Direkte Ãœbertragung ohne TouchDesigner

39 zeitlich begrenzte MesslÃ¤ufe verglichen PaketabstÃ¤nde, Senderaten, einzelne
AusgÃ¤nge und Ausgangsgruppen. `measurement-summary.json` enthÃ¤lt jede Messung;
`external-*.json` enthalten Ausgangskonfiguration, ZÃ¤hlerstÃ¤nde und Sendezeiten.
`framesComplete` und `outputFrames` werden getrennt ausgewertet. Die Ausgabe-
zahlen sind **SoftwarezÃ¤hler des Controllers**, keine optische Messung oder
Logikanalysator-Aufzeichnung. Gemessen wurden Ã¼berwiegend 6, bei den letzten
Paarvergleichen 8 Sekunden je Fall. Das sind Vergleichstests, kein Dauerlauf-
Nachweis fÃ¼r eine komplette Installation.

| Last / Testkonfiguration | Controller-Ausgaben pro Sekunde |
|---|---:|
| Alle sechs AusgÃ¤nge, 4105 LEDs, 30 angefordert, 1 ms Paketabstand | 8,49 |
| Erste fÃ¼nf Panels, 2983 LEDs, 30 angefordert, 1 ms | 10,33 |
| Nur 880er-Ausgang, GerÃ¤tefreigabe 30, Sender 30 | etwa 27 |
| Nur 880er-Ausgang, GerÃ¤tefreigabe 60, Sender 30, ohne Abstand | 29,83 |
| Zwei AusgÃ¤nge 810 + 352, GerÃ¤tefreigabe 60, Sender 30 | bis 21,83 |
| Drei AusgÃ¤nge 203 + 738 + 880, Sender 30 | bis 15,00 |

Die GerÃ¤tefreigabe 60 im Einzeltest bedeutet nicht, dass 60 Bilder gesendet
wurden. Sie trennt die interne Ausgabedrossel vom 30-FPS-Datenstrom. Bei fÃ¼nf
AusgÃ¤ngen brachte dieselbe Freigabe keine wesentliche Verbesserung.

Ungebremste PaketblÃ¶cke fÃ¼r alle sechs AusgÃ¤nge lieferten trotz 30 gesendeter
Bildserien pro Sekunde **kein einziges vollstÃ¤ndiges Bild**. Damit ist
TouchDesigner als alleinige Ursache widerlegt. Empfang, Pufferung und
Ausgangsverarbeitung sind getrennt zu optimieren. Dass ein einzelner Ausgang
fast 30 FPS schafft, belegt keine entsprechende Leistung mit sechs AusgÃ¤ngen.

`outputTimeUs` darf nicht als komplette elektrische Ãœbertragungszeit gelesen
werden: Der Einzelport mit 203 LEDs meldet beispielsweise 300 Âµs, obwohl seine
Datenleitung allein mindestens 6,09 ms benÃ¶tigt. Eine feste 18-FPS-Grenze aus
den frÃ¼her gemeldeten 55 ms abzuleiten wÃ¤re deshalb falsch.

Alle fÃ¼r Vergleichstests verÃ¤nderten GerÃ¤tekonfigurationen wurden im `finally`-
Pfad exakt wiederhergestellt und zurÃ¼ckgelesen. Es wurde nie `/api/config/save`
aufgerufen. Die Belege stehen in `profile-restoration*.json`.

## Umgesetzte SoftwareÃ¤nderungen

- Der reine RGB-Packer benÃ¶tigt im gepaarten Offline-Vergleich etwa 48â€“51 %
  weniger Zeit bei identischen Bytes (ca. 3,5â€“3,6 auf 1,7â€“1,9 ms). Das ist keine
  Behauptung einer Verdopplung der gesamten Bildrate.
- Ein optionaler separater Python-Prozess Ã¼bernimmt die Paketpausen und UDP-
  Ausgabe. TouchDesigner berechnet weiter Mapping, Maskierung und Farben und
  Ã¼bergibt vollstÃ¤ndige Bildserien ohne auf die physische Sendeschleife zu warten.
- Der Prozess verwirft Ã¼berholte lokale Bildserien zugunsten des neuesten Bildes,
  statt nach einer VerzÃ¶gerung alte Bilder nachzuholen. Seine Statistik wird von
  TouchDesigners Ãœbergaberate getrennt angezeigt. Beide sind keine EmpfangsbestÃ¤tigung.
- Stop und AusfallÃ¼berwachung senden Schwarz fÃ¼r zuvor berÃ¼hrte Universen.
  Eine begrenzte Startfrist erlaubt TouchDesigner, das erste Bild bereitzustellen;
  danach beendet sich der Prozess bei ausbleibenden Bildern automatisch.
- Ein Review korrigierte den Verlust des 129. Datagramms beim begrenzten Leeren
  der lokalen Warteschlange und prÃ¼fte Fehlerpfade beim Beenden.

Der externe Modus unterstÃ¼tzt zunÃ¤chst **genau einen aktivierten Controller**.
Bei mehreren aktiven Controllern schlÃ¤gt der Start mit einer ErklÃ¤rung fehl;
es gibt keinen stillen Wechsel auf eine andere Zieladresse. FÃ¼r das bisherige
direkte Mehrcontroller-Verfahren kann `external_sender_settings.enabled` auf
false gesetzt werden. Die vorhandenen Scan-, Maskierungs- und RoutingprÃ¼fungen
bleiben erhalten. Ã„nderungen des Paketabstands erfordern Stop und Neustart.

Die ersten beiden nativen Prozessversuche scheiterten vor dem ersten Paket an
der zu kurzen Startfrist. Diese FehlschlÃ¤ge bleiben als Messbelege erhalten;
nachfolgende Dateien mit `fixed` beziehungsweise `precision` dokumentieren
die korrigierte Implementierung. Die native PrÃ¼fung berechnet die reale
Animationspipeline, ersetzt ihre Ã¼bertragenen Farben jedoch durch Schwarz.

## Controllerzahl, Ethernet und Teensy

4105 LEDs insgesamt sind allein kein Ausschlussgrund fÃ¼r einen Controller.
Die lÃ¤ngste **einzelne** WS2812B-Kette bestimmt aber eine feste Untergrenze:
1122 Ã— 30 Âµs = 33,66 ms, zuzÃ¼glich Resetzeit. Echte 30 FPS benÃ¶tigen weniger
als 33,33 ms pro Bild. Diese Kette muss dafÃ¼r geteilt werden, unabhÃ¤ngig davon,
ob ein ESP32, Teensy oder Ethernet verwendet wird. Ein Split 680 + 442 erhÃ¤lt
die vorhandenen Universumsgrenzen U142â€“145 und U146â€“148.

Mehr ESP32 verteilen die beobachtete Last; die Paar- und Dreiermessungen erlauben
aber keine Zusage, dass zwei GerÃ¤te genÃ¼gen. Ethernet entfernt die Funkstrecke
und kann Verluste und Schwankungen reduzieren. Es ersetzt keine passende
Ausgabetreiber- und Empfangsarchitektur. Der PC sendet bereits Ã¼ber Ethernet
(10.0.0.125); eine UmrÃ¼stung betrifft die Controllerseite.

Der Benutzer bevorzugt inzwischen als Alternative **Teensy 4.1 mit FastLED,
ohne Octo**. Eine konkrete Planung muss deshalb FastLEDs passenden parallelen
Teensy-Treiber, Ethernetempfang und nicht blockierende Ausgabe zusammen prÃ¼fen.
Die Behauptung, jede FastLED-Konfiguration sei automatisch schneller, wird
nicht vorausgesetzt. Ein ESP32-Binary lÃ¤uft nicht unverÃ¤ndert auf einem Teensy.
Mapping und Scanpunkte kÃ¶nnen erhalten bleiben, wenn die neue Firmware den
bestehenden Art-Net-Vertrag mit 510 Nutzbytes und den aktuellen Universen erfÃ¼llt.

FÃ¼r eine gezielte Reparatur der aktuellen ESP32-Firmware fehlt noch ihr
Quellcode. Die Suchorte, PrimÃ¤rquellen und Empfehlungen sind in
`FIRMWARE_AUDIT.md`, `CAPACITY_RESEARCH_DE.md`, `NATIVE_HOTSPOTS.md` und den
Hardwarevergleichsberichten dokumentiert. Der Firmwarepfad wurde beim Benutzer
angefragt; es wurde kein Treiber aufgrund einer Vermutung ersetzt.


## Vergleich mit dem anderen Controller (GICO 10.0.0.244)

Ping antwortete mit 1 ms. Die HTTP-Ports antworteten nicht; daraus folgt
keine Nichterreichbarkeit des Controllers. ArtPoll identifizierte das Gerät
als **GICO-6612PRO 12PORT DMX512&SPI**, einschließlich mehrerer Bind-Antworten.
`controller244-artpoll.json` sichert die Rohantworten. Das ist ein anderer
Controller als der ESP32 mit `/api/status`; dessen Messmethode lässt sich nicht
ungeprüft auf den GICO übertragen.

Vier externe Schwarztests mit 24 Universen U0–23 dauerten jeweils 10 Sekunden:
15,00 / 30,00 / 59,89 gesendete FPS ohne Paketpausen und 29,86 FPS bei
0,5 ms Abstand. Bei 30 FPS ohne Abstand benötigte die komplette Paketserie im
Mittel 0,574 ms. Die maximale gemessene Bildabstandszeit war 35,06 ms.
Der GICO blieb über ArtPoll erreichbar. Seine Antworten enthielten jedoch
keinen auswertbaren Frame-Zähler; `receiver_fps` bleibt ausdrücklich null.
Diese Senderaten dürfen nicht als gemessene LED-Ausgaberaten ausgegeben werden.

Der anschließende Test durch die tatsächliche TouchDesigner-Animationspipeline
lieferte etwa **20,99 FPS im aktiven Mittel des separaten Senders**, obwohl
30 FPS angefordert waren. TouchDesigners Vorbereitung/Übergabe brauchte dabei
im Mittel 16,58 ms, davon 6,62 ms Packing. Der unabhängige Testgenerator war
schneller: neben dem ESP32 gibt es somit eine eigenständige Begrenzung im
TD-Projekt. Die Stichprobe der aktiven Operatoren ist in `NATIVE_HOTSPOTS.md`
dokumentiert. `topto1` verwendet bereits `downloadtype=nextframe`; ein bloßer
Wechsel auf den verzögerten GPU-Download wäre keine neue Optimierung.

Belege: `gico244-black-comparison.json` und `gico244-native-comparison.json`.
Alle GICO-Routeränderungen wurden nach dem Test zurückgesetzt; Schwarzbilder
wurden vor dem Schließen gesendet. Eine optische Empfangsbestätigung liegt
nicht vor. Eine vorhandene FPS-Anzeige am Gerät wurde beim Benutzer angefragt.

## Gespeicherter Zwischenstand und Grenzen

Für den Rückwandcontroller ist der externe Modus mit **8 angeforderten FPS
und 1,5 ms Paketabstand** vorbereitet. Im nativen Präzisionstest kamen im
10-Sekunden-Messfenster 61 vollständige Bilder an; die Ausfälle bleiben ein
Problem, und dieser Stand ist kein Erfolgskriterium für 30 FPS. Die Hauptthread-
Vorbereitung lag dabei im Mittel bei 18,56 ms statt früher rund 60–67 ms
inklusive der dort ausgeführten Paketpausen. Der Vergleich hängt auch von
Projektlast und Testbedingungen ab; der isolierte Packervergleich ist die
saubere Messung der reinen Codebeschleunigung.

Der 30-FPS-Stresstest zeigte zusätzlich eine Pause des TD-Produzenten, auf die
der Worker bestimmungsgemäß mit Schwarz und Beenden reagierte. Der Statuspfad
wurde danach korrigiert, damit er einen beendeten Worker nicht weiter als
aktiv meldet. Dieser Fall besitzt einen eigenen Verhaltenstest.

Der neue `.toe`-Checkpoint wird mit Ausgabe AUS gespeichert (`save.json`,
SHA-256 enthalten). Keine Scanpunkte, Ausrichtungen oder Quellkapazitäten wurden
verändert; die Quelle enthält weiterhin 6524 Slots. Die Benutzerhelligkeit
von 70 % wurde erhalten. Die sechs Controllerausgänge und ihre gespeicherte
Konfiguration entsprechen wieder der Anfangskonfiguration.

Offen bleiben: ESP32-Firmwarequelle für konkrete Treiber-/Empfängeränderungen,
weitere Optimierung des TD-Bildpfads, echter GICO-Ausgabe-/Empfangsnachweis,
und bei einem Hardwarewechsel die Umsetzung und Messung von Ethernet sowie
FastLED auf Teensy. Hardwareplanung und Preisbeispiele stehen in
`ETHERNET_OPTIONS_DE.md` und `TEENSY_MIGRATION_DE.md`.

## Abschliessende Softwarepruefung

53 Tests fuer externen Sender, native Integration, Packing, Paketabstand, Pacing und Routing bestanden. Der Checkpoint wurde mit Ausgabe AUS gespeichert. Die 30-FPS-Zielmarke ist weiterhin nicht erreicht.
