# Controller 248: Firmware- und Ausgabetiming-Audit

Stand: 12. September 2026. Unabhängiger Agent, ausschließlich lesende Analyse;
keine Geräteabfragen, Konfigurationsänderungen, Paketsendungen oder Flash-Vorgänge
durch diesen Agenten. Hardwaretests erfolgen ausschließlich durch den Hauptagenten.

## Ergebnis und Grenzen

Der tatsächliche Firmwarequellcode wurde lokal nicht gefunden. Gesucht wurden
`platformio.ini`, `.ino`, `.cpp`, `.h` und `AGENTS.md` im gesamten Projekt,
`TouchDesignerLocal`, Documents, OneDrive und Downloads. Im Projekt liegt kein
anwendbares `AGENTS.md`; die zusätzlich gefundene Datei
`C:/Users/jbhtz/.codex/AGENTS.md` ist leer. Das gespeicherte ChatGPT-Projekt
„SkyGlow Controller“ betrifft einen separaten Raspberry-Pi-Gestencontroller
mit Skywriter/PiGlow und enthält laut „Projektstatus zusammenfassen“ nur Fotos.

Damit sind Aussagen über konkrete RMT-Treiber, Task-Affinität, DMA-Verwendung,
Socketpuffer oder die genaue Bedeutung der Empfangszähler **nicht durch
Firmwarecode belegt**. Insbesondere ist „alle Ausgänge werden seriell gesendet“
keine gesicherte Diagnose. Es wäre falsch, eine vorhandene lokale Firmwaredatei
oder einen bereits implementierten Firmwarefix zu behaupten.

Die Hardwaregrenze pro LED-Kette und die vorhandenen Messprotokolle erlauben
trotzdem konkrete Schlussfolgerungen. 4105 Pixel insgesamt sind allein noch
kein Beweis für eine Überlastung; die längste Kette, tatsächliche Parallelität,
Empfang während der Ausgabe und Paketpuffer sind entscheidend.

## Nachprüfbare lokale Quellen

Alle folgenden Pfade sind relativ zum Repository
`C:/Users/jbhtz/OneDrive/Desktop/Pictures/Documents/ChatGPT/LED-Touchdesigner-Controller/PixelblazeMapper`:

- `docs/controller-replacement-248-20260911/controller-config-before.json`:
  Profil `esp32-wroom-flex-8ws-2apa`, sechs WS2812B-Ausgänge, 4105 Pixel,
  28 tatsächlich belegte Universen, Ziel 30 FPS.
- `docs/controller-replacement-248-20260911/final-live-verification.json`:
  Ausgabezeit 55.517 ms; lokaler Sender durchschnittlich 66.971 ms pro Batch,
  `actual_send_fps` 3.290 trotz Sollwert 5. Der kurze API-Momentanwert `fps: 5`
  ist deshalb kein Nachweis dauerhaft erreichter 5 vollständiger Bilder/s.
- `docs/controller-replacement-248-20260911/gap-1ms-probe.json`:
  Paketabstand verbessert vollständige Sammlungen von null auf 22 im Fenster,
  gleichzeitig weiterhin 15 zusätzliche unvollständige Sammlungen.
- `docs/controller-performance-20260912/controller-index.html:445`:
  Die geladene Geräteoberfläche nennt `framesComplete` ausdrücklich
  „Vollständige Sammlungen“, `outputFrames` separat „LED-Ausgaben“ und
  `outputTimeUs` „Ausgabetiming“. Nur UI-Code, nicht der Empfängerquellcode.
- `pixelblaze_mapper/build_multi_controller_output.py:592`: tatsächliche
  ArtDMX-Serialisierung mit Sequenz 0. Der Kommentar dokumentiert eine frühere
  Empfängerinkompatibilität bei wiederverwendeten Sequenznummern pro Frame.
- `pixelblaze_mapper/sender_packet_gap.py:24`: der bisherige Paketabstand
  wartet mit `time.sleep(gap)` zwischen UDP-Paketen im TD-Aufruf.
- `pixelblaze_mapper/sender_pacing.py`: individuelle monotone Friststeuerung;
  verpasste Termine erzeugen keine nachträglichen Aufholbursts.

## Physikalisches Zeitbudget

Berechnung unter der konfigurierten WS2812B-Annahme: 24 Bits bei 800 kbit/s
ergeben 30 µs pro Pixel, zuzüglich Reset/Latch und Treiberaufwand.
Herstellerreferenz: [Worldsemi, 800-kHz-/24-Bit-Datenschnittstelle](https://www.world-semi.com/).
Die konkrete LED-Revision und tatsächlich erzeugte Bitrate sind nicht gemessen.

| Ausgang | Pixel | Reine Datenzeit | Konsequenz |
|---|---:|---:|---|
| Panel 1 | 203 | 6,09 ms | unter 33,33-ms-Budget |
| Panel 2 | 738 | 22,14 ms | unter Budget |
| Panel 3 | 880 | 26,40 ms | längste eingemessene Kette |
| Panel 4 | 810 | 24,30 ms | unter Budget |
| Panel 5 | 352 | 10,56 ms | unter Budget |
| Ausgang 6, noch ohne Scan | 1122 | 33,66 ms | bereits ohne Latch länger als ein 30-FPS-Frame |

Für fünf eingemessene Panels sind echte 30 FPS aus der reinen Bitzeit heraus
bei paralleler Ausgabe prinzipiell möglich. Mit der zusätzlichen 1122er-Kette
liegt die ideale Obergrenze schon ohne Latch nur bei etwa 29,71 FPS.
Ein zweiter Controller verkürzt diese einzelne 1122er-Kette nicht; dafür müsste
sie auf zwei physische Datenleitungen aufgeteilt werden. Dagegen können mehrere
Controller die gesamte Zahl der Pakete und parallel zu bedienenden LED-Ausgänge
je Empfänger verringern.

Bei vollständig serieller Ausgabe aller sechs Ketten wären 123,15 ms nötig,
bei ideal vollständig paralleler Ausgabe mindestens 33,66 ms. Gemessene
`outputTimeUs` um 55,5 ms beweisen keine konkrete Treiberarchitektur und dürfen
**nicht als direktes Bitzeit-/Framelimit von 18 FPS interpretiert werden**.
Die späteren kontrollierten Einzelporttests unten zeigen Ausgabezeiten weit
unter der physikalischen Übertragungsdauer. Das Feld misst offensichtlich
nicht durchgehend die vollständige Zeit am Draht. Eine asynchrone Übergabe
mit phasenabhängigen Wartezeiten ist eine plausible, unbestätigte Erklärung.

## Empfang und Sender getrennt bewerten

28 belegte Universen mit jeweils 510 RGB-Bytes benötigen bei 30 FPS
428400 Byte/s Nutzdaten (3,43 Mbit/s); mit den 18-Byte-ArtDMX-Headern
443520 Byte/s. IP-, UDP-, Ethernet-/WLAN-Overhead kommt hinzu.
Diese mittlere Nutzdatenrate erklärt allein keine Grenze von 5 FPS.
840 einzelne UDP-Pakete/s und kurze Bursts können jedoch kleine Empfängerqueues
überfordern, besonders wenn die Ausgabe den Empfang zeitweise blockiert.

Der bisher zusammenhängende Sendebereich enthält zusätzlich das unbelegte U138
und erzeugt 29 Pakete statt 28. Weglassen dieses einen Lochs spart etwa 3,45 %
Pakete und darf die absolute Universumsnummerierung nicht verschieben.
Es ist keine hinreichende Erklärung für den großen Leistungseinbruch.

1 ms Abstand bei 29 Paketen kostet theoretisch schon 28 ms pro Batch.
Die aufgezeichneten rund 67 ms zeigen zusätzlich erheblichen tatsächlichen
Warte-/Hostaufwand. Diese Wartezeiten dürfen nicht als dauerhafte
30-FPS-Lösung im TouchDesigner-Hauptthread bleiben.

`droppedPackets == 0` beweist keine verlustfreie Übertragung: Pakete können
bereits unterhalb des Firmwarezählers verloren gehen. Für jeden Test sind
gesendete Pakete, gezählte Pakete, vollständige Sammlungen und LED-Ausgaben
über dasselbe ausreichend lange Zeitfenster zu vergleichen. Semantik von
`timeouts`, `framesIncomplete` und Sequenzfehlern ist ohne Quellcode offen;
aus zwei Zählern darf daher nicht ungeprüft eine Fehlerwahrscheinlichkeit
einzelner Frames abgeleitet werden.

## Konkrete Prüf- und Optimierungsreihenfolge

1. Bisherige sechs Ausgänge mit identischen Schwarzframes durch einen externen,
   monoton getakteten Prozess testen. So werden Materialberechnung,
   TouchDesigner-Takt und Sender-GIL aus der Empfangsmessung herausgenommen.
2. Paketabstand und Sollrate getrennt variieren. Keine HTTP-Abfragen innerhalb
   des Messfensters; danach eine kurze Auslaufphase und Zählervergleich.
3. Den unbenutzten Ausgang 6 nach Schwarzbild vorübergehend deaktivieren,
   genau dessen sieben Universen aus dem erwarteten Datensatz entfernen und
   dieselben Messungen für die fünf tatsächlich zu animierenden Panels machen.
   Vorherige Gerätekonfiguration sichern und später bewusst wiederherstellen
   oder die deaktivierte Reserve als Setupänderung dokumentieren.
4. Mit einzelnen langen Ports und sinnvollen Portgruppen das Ausgabetiming
   vergleichen. Damit lässt sich erkennen, ob ein Kanal-/Batchlimit erst bei
   mehreren aktiven Ausgängen entsteht. Solche Tests verändern keine Scan-IDs,
   Koordinaten oder endgültige Zuordnung.
5. Erst bei erfolgreicher externer Übertragung den TD-Sender testen, samt
   Batchdauer, Packdauer, effektiver TD-Bildrate und Empfängerzählern. Gewinne
   durch schnelleren Packer dürfen nicht mit Empfangsgewinnen verwechselt werden.
6. Für einen stabilen Kandidaten mindestens 60 Sekunden messen, danach mit
   gedimmter bewegter Ausgabe optisch prüfen. Ein Schwarztest beweist Transport
   und Zählerverhalten, aber keine sichtbare Animationsqualität.

## Firmwarearbeiten, sobald der passende Quellstand vorliegt

- Empfangsschleife und GPIO-Ausgabe entkoppeln, vollständige Bildpuffer atomar
  tauschen und keine halben Bilder veröffentlichen; begrenzte Queue mit
  bevorzugtem neuesten vollständigen Frame statt wachsendem Rückstau.
- Tatsächliche Universumsmenge je aktiviertem Ausgang erwarten, keine
  unbelegten Zwischenuniversen. Frames nicht auf die erste Universe eines
  nachfolgenden Batches vermischen. Sequenz-0- und Sequenz-Modus separat testen.
- UDP-Queue-Tiefe, Auslastung, fehlende Universumsnummern, max. Empfangspause,
  tatsächliche Port-Ausgabezeiten und Firmware-Version über Diagnostik ausgeben.
- Treiber auf echte gleichzeitige Ausgabe prüfen; keine pauschale Annahme,
  dass acht konfigurierbare GPIOs acht parallel sendende Hardwarekanäle bedeuten.
- Bei bestätigtem RMT-/WLAN-Konflikt Interruptkern, Pufferspeicher und
  DMA-Alternative prüfen. Espressif dokumentiert diesen Problemtyp für lange
  WS2812-Ketten: [offizielle RMT-FAQ](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/peripherals/rmt.html).
  Die FAQ nennt insbesondere einen anderen CPU-Kern für RMT-Interrupts oder
  SPI-DMA als Alternativen. Das ist eine begründete Prüfrichtung, keine Diagnose
  des hier unbekannten Firmwaretreibers.

Firmware-Neubau oder Controllerkauf sollten auf diesen Befunden basieren.
Mehr Controller können helfen, garantieren aber ohne passende Ausgabe- und
Empfangsarchitektur keine 30 FPS. Für Ausgang 6 bleibt die Kettenlänge eine
separate Grenze, auch bei zusätzlichem Controller.

## Kontrollierte Hardwaremessungen vom 12. September

Die folgenden Daten wurden vom Hauptagenten mit
`tools/controller_black_benchmark_20260912.py` erhoben und hier offline
ausgewertet. Der Sender läuft als externer Prozess und sendet ausschließlich
Schwarzwerte für die tatsächlich aktivierten Universen. Jede Tabellenzeile
ist ein einzelnes ungefähr sechssekündiges Messfenster mit 250 ms Auslaufphase.
Das sind diagnostische Kurztests, keine Dauerbetriebsabnahme. Die Protokolle
sichern vollständige Konfigurationen, Vorher-/Nachherzähler und Senderstatistik.

`Ausgaben/s` wird hier ausdrücklich als `delta(outputFrames) / seconds`
berechnet. `Sammlungen/s` meint dagegen `delta(framesComplete) / seconds`.
Beide sind Firmwarezähler und noch keine optische Messung.

| Aktive Pixel je Port | Geräte-Ziel-FPS | Soll-Sender-FPS | Abstand ms | Sender tatsächlich | Sammlungen/s | Ausgaben/s | letztes outputTimeUs |
|---|---:|---:|---:|---:|---:|---:|---:|
| 203,738,880,810,352,1122 | 30 | 30 | 0 | 30,00 | 0,00 | 0,00 | 55422 |
| 203,738,880,810,352,1122 | 30 | 30 | 1 | 26,63 | 8,49 | 8,49 | 55369 |
| 203,738,880,810,352,1122 | 30 | 8 | 2 | 8,00 | 7,33 | 7,33 | 55386 |
| 203,738,880,810,352 | 30 | 30 | 1 | 29,83 | 10,33 | 10,33 | 54102 |
| 203 allein | 30 | 30 | 0 | 30,00 | 30,00 | 27,50 | 300 |
| 880 allein | 30 | 30 | 0 | 29,68 | 27,36 | 27,03 | 1148 |
| 203,738,880 | 30 | 30 | 1 | 30,00 | 15,00 | 15,00 | 52687 |
| 810,352 | 30 | 30 | 0,5 | 30,00 | 20,83 | 20,83 | 1443 |
| 810,352 | 30 | 30 | 1 | 30,00 | 19,83 | 19,83 | 51952 |
| 880 allein | 60 | 30 | 0 | 30,00 | 29,83 | 29,83 | 1084 |
| 203,738,880,810,352 | 60 | 30 | 1 | 29,61 | 10,31 | 10,31 | 54073 |

Quellen: `external-six-outputs.json`, `external-six-conservative.json`,
`external-five-outputs.json`, `external-one-203.json`, `external-one-880.json`,
`external-three-a.json`, `external-two-b.json`, `external-one-880-cap60.json`
und `external-five-cap60.json`, jeweils in diesem Ordner. Vollständige weitere
Paketabstandskombinationen bleiben in den JSON-Dateien erhalten.

### Was die Messungen belegen

1. **Der PC kann den Transportversuch mit ungefähr 30 FPS ausführen.** Bei sechs
   Ports und Abstand null wurden 5040 Pakete gesendet, aber nur 2182 im
   Firmwarezähler erfasst; vollständige Sammlungen und Ausgaben blieben null.
   Das Problem tritt damit auch ohne TouchDesigner und ohne Materialberechnung
   auf. Ob die Verluste im Netzwerk, Netzwerkstack, Socketpuffer oder Empfänger
   entstehen, ist noch nicht getrennt. `droppedPackets: 0` schließt sie nicht aus.
2. **Paketabstand hilft, löst den Mehrportengpass aber nicht.** Sechs Ausgänge
   erreichen im Kurztest etwa 8,49 Ausgaben/s. Fünf erreichen etwa 10,33.
   Das Entfernen der 1122er-Reserve verbessert die Lage, bringt allein jedoch
   keine Nähe zu 30 FPS. Weniger sendeseitige Wartezeit ist nicht automatisch
   besser: Bursts führen hier bis zum vollständigen Ausfall der Sammlung.
3. **Eine zusätzliche Ausgabedrossel ist von Paketverlust zu unterscheiden.**
   Bei nur 203 LEDs kamen alle 360 Pakete an und alle 180 Bilder wurden
   vollständig gesammelt, aber nur 165 LED-Ausgaben gezählt. Das ist im
   Messfenster eine Differenz von 15 Bildern nach erfolgreichem Empfang.
   Ein Takt-/Freigabefilter, Rundung oder andere Outputplanung ist plausibel;
   eine bestimmte fehlerhafte Codezeile ist mangels Firmwarequelle unbelegt.
4. **Ein einzelner langer Port kann nahe 30 FPS erreichen.** Bei 880 LEDs,
   Geräte-Ziel 60 und Sendetakt weiterhin 30 wurden 179 von 180 Bildern
   gesammelt und ausgegeben: etwa 29,83 Ausgaben/s. Die Geräte-Zahl 60 ist
   dabei ein experimenteller Freigabewert und keine Behauptung, dass 880
   WS2812B-Pixel physikalisch 60 FPS schaffen. Der Kontrolltest spricht dafür,
   dass die bisherige 30er-Gerätefreigabe zumindest am Einzelport eine zusätzliche
   Begrenzung verursacht. Eine Kausalbehauptung über Rundung wäre vorzeitig.
5. **Die Geräte-Zielrate hochzusetzen behebt den Mehrportengpass nicht.** Bei
   fünf Ports bleiben es mit Ziel 60 etwa 10,31 statt 10,33 Ausgaben/s im
   vergleichbaren 1-ms-Test. Das ist innerhalb dieser Kurztests kein relevanter
   Gewinn. Eine permanente Änderung auf 60 ist daraus nicht gerechtfertigt.
6. **Die gemeldete Ausgabezeit ist kein durchgehendes physikalisches Zeitmaß.**
   203 LEDs benötigen schon rund 6090 µs reine Bitzeit, während das Feld 300 µs
   meldet. Bei 880 LEDs sind es rund 26400 µs, gemeldet wurden etwa 1100 µs.
   Die gleiche Zweiergruppe meldet je nach Versuch 1443 oder 51952 µs. Daher
   sind 55 ms weder eine bewiesene serielle Übertragungsdauer noch ein belastbares
   universelles FPS-Limit. Das Feld sollte später mit klarer Messgrenze ergänzt
   werden: Übergabe, eventuelles Warten, tatsächlicher Start und tatsächliches Ende.

### Konsequenz für mehrere Controller

Die Gruppenmessungen sprechen für einen Engpass, der mit der Anzahl aktiver
Ports/Universen wächst. Die Dreiergruppe erreicht etwa 15, die Zweiergruppe
etwa 21 und ein Einzelport knapp 30 Ausgaben/s. Damit ist Entlastung durch
weitere Controller als Ansatz empirisch plausibel. Es ist aber nicht bewiesen,
dass eine Verteilung auf genau zwei Controller bereits 30 FPS erreicht: Die
hier getesteten Zweier-/Dreiergruppen bleiben darunter. Gemeinsame WLAN-Last
und die tatsächliche Gerätefirmware müssten zusätzlich gemessen werden.

Eine endgültige Empfehlung lautet deshalb nicht „zu viele Pixel, kaufe zwei
Controller“, sondern: Empfang/Outputplanung in der passenden Firmware prüfen,
Transport optimieren, konkrete Aufteilung testen und erst daraus die notwendige
Hardwarezahl bestimmen. Der Einzelporttest zeigt, dass die vorhandene
880er-Kette für sich kein Hindernis für das 30-FPS-Ziel ist.
