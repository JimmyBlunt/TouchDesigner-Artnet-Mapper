# Paralleles Leistungsprogramm

Gestartet 12.09.2026 auf ausdrücklichen Benutzerauftrag. System- und
Firmwareänderungen sind erlaubt; Ergebnisse werden getrennt nach Build,
Softwaretest und Hardwaremessung dokumentiert.

| Bereich | Zuständig | Stand |
|---|---|---|
| GICO-Kameratest | gico_camera_test | Aufnahmebereit; 16 Tests bestanden; echte Kameraaufnahme noch offen |
| TouchDesigner | Hauptagent | Neuer Worker und Router-UI installiert/gespeichert; bester Lauf 29,82 FPS/60 s; stabile 30-FPS-Abnahme offen |
| ESP | Hauptagent nach Agentenlimit | COM5 / .151: Physical768 mit 900/900 vollständigen Empfangs-/Ausgabebildern in 30 s; Virtual1755 jetzt geflasht, disarmed bestätigt, Test folgt |
| Teensy 4.1 | Hauptagent nach Agentenlimit | COM4 / .253: moderne FastLED-API läuft; Empfang ohne Ausgabe 600/600, mit DMA 898/900; RX-Puffererweiterung im Build |

USB-Anschluss vom Benutzer bestätigt. Windows erkannte zunächst CP2102 ohne
COM (Treiberfehler) und Teensy VID16C0/PID0478 im HID-Bootloader. COM3 ist Intel
AMT und kein Testcontroller. Agenten dürfen nach Identifikation die jeweiligen
Testgeräte programmieren; produktiver ESP .248 und GICO .244 werden nicht geflasht.

Die laufenden Compiler-/Installationsprozesse beeinflussen aktuelle TD-Zeiten.
Abschlussmessungen müssen ohne diese zusätzliche Last erfolgen.

Abnahme: GICO aufnahmebereit mit auswertbarer Bildnummer; TD mindestens 30 FPS
über einen längeren dokumentierten Lauf mit Paket- und Jitterkontrolle; Firmware
gebaut, Recovery dokumentiert und auf verfügbarer Hardware gemessen. Ohne
Kameraaufnahme bzw. angeschlossene LED-/Ethernet-Testhardware keine erfundene
optische oder elektrische Bestätigung. Einzelstände in gico/, esp/, teensy/, td/.

Statusautomation: controller-optimierung-status-alle-10-minuten, alle zehn Minuten.

Aktueller Stand nach dem Schließen von Chrome (12.09., ca. 14:13 AEST):
- Vorher nur 0,5–0,7 GB freier RAM bei 16 GB und 1.200–1.900 nachgeladenen
  Speicherseiten/s. Das betraf auch unabhängige Firmware-Sender und Workerstarts;
  zehn Prozessintegrationstests scheiterten am 5-s-Starttimeout, nicht an einer
  Paketassertion. Ergebnisse unter dieser Last sind keine Controllergrenze.
- Benutzer hat Chrome geschlossen: rund 3 GB RAM frei; nach kurzer Beruhigung
  413 nachgeladene Seiten/s. Weitere Messungen werden nacheinander ausgeführt.
- Teensy: 93 vollständige Frames und 93 DMA-Abschlüsse im ersten modernen
  Smoke-Test, ungefähr 2,19 ms show()-CPU-Zeit und 28,66 ms kompletter Transfer.
  STOP bestätigt, danach 94 DMA-Abschlüsse einschließlich Schwarzbild.
  Keine LEDs angeschlossen: noch keine optische Bestätigung.
- ESP: neue Firmware bei 768 physischen Pixeln bestätigt beide Ausgangstransfers.
  Der neue Hostlauf lieferte selbst nur 23,03 statt 30 FPS; daher keine Aussage,
  dass die neue Firmware langsamer als die vorherige 29,77-FPS-Baseline sei.
  Ursprüngliche USB-Adresse war .251; experimentelle Firmware jetzt .151.
- Worker: Nonblocking-Socket mit 1-MB-Sendepuffer, sichtbarer Fehlerabbruch,
  begrenzter Timeout für abschließendes Schwarz und reduzierte Stop-Dateizugriffe.
  Neue Fehlertests bestanden; erneute Prozessintegration und native Messung offen.
- Invalidierte Bildraten werden im neuen generierten Sender vor der Ausgabe
  abgefangen und stoppen den Sender. Die endgültige native Installation steht an.
- Temporär erhöhte Prozesspriorität brachte keinen Vorteil: 29,299 FPS/120 s.
  Prioritäten sind wieder Normal; diese Einstellung wird nicht standardmäßig aktiviert.
- Alle TD-Hardwareausgänge bleiben außerhalb ausdrücklich gestarteter Tests aus.

Weiterer Zwischenstand ca. 14:40 AEST:
- Alle 75 gezielten Worker-/Pacing-/UI-Tests bestanden nach Speicherentlastung.
  Der V2-Fehlerabbruch und die Router-Statusoptimierung sind nativ installiert.
- TD-Checkpoint `PixelblazeMapper_30FPS_PROGRAM_20260912_worker-clock-ui.1.toe`,
  SHA256 `1acf5c42671f5ca2068f09c886905b28b8f6ebeb4138aa94eb9f6c038f09e03a`.
  Frame-Pacing aktiviert, normale Priorität; Controller-Raten und Routing bleiben
  unverändert, Ausgabe aus. Produktivcontroller .248 deshalb weiter mit bisheriger
  8-FPS-Konfiguration; noch keine behauptete 30-FPS-Freigabe dieser Hardware.
- Vollständiges temporäres Schließen beider OneDrive-Prozesse verbesserte den
  TD-Lauf auf29,816 FPS, mindestens28 in einer vollen Sekunde, maximal116,161 ms
  Abstand. Beide OneDrive-Komponenten wurden anschließend nachweislich gestartet.
- ESP Physical768: 900 gesendete/empfangene/ausgegebene Frames,5400/5400 Pakete,
  keine Teilbilder; beide Treiber900 bestätigte Transfers in30s. Beleg:
  `esp/physical768-memory-free-30fps.json`. Kein optischer FPS-Nachweis.
- Teensy: reine Empfangsabnahme600/600 Frames; mit aktiver DMA898/900 und22
  fehlende UDP-Pakete. Ringpuffer-Hypothese wird durch einen SHA-geprüften
  5→32-RX-Deskriptor-Patch im Testbuild untersucht. Noch keine Freigabe dieses
  neuen Builds. Testcontroller blieb nach beiden Läufen gestoppt/schwarz.
- Alle drei Agenten wurden anschließend vom Kontonutzungslimit beendet.
  Hauptagent führt die verbleibenden Arbeiten ohne zusätzliche Agenten weiter.

Aktualisierung während der laufenden Arbeit:
- Teensy kurz vom Benutzer getrennt; Hardwareaktionen pausiert und nach erneuter
  Anschlussbestätigung fortgesetzt. Safe-Image initialisiert keine LED-Ausgänge.
- ESP: tatsächliche angeschlossene Längen laut Benutzer ungefähr 256 WS2812
  (GPIO14) und 512 APA102 (DATA18/CLOCK19). Alte NVS-Werte 731/1024 sind keine
  Bestätigung physischer Längen. Testprofil beseitigt die alte U4-Überlappung:
  WS U0–1, APA U2–5. Privates Vollbackup liegt außerhalb Git.
- TD: Masken und Routingtabellen unverändert, alle erzeugten Controller-Payloads
  gegen skalare Referenz geprüft. Statusdatei-Cache und Positionsarray-Cache
  reduzieren zusätzliche Arbeit. 30 FPS noch nicht abgenommen.
- Benchmark „numpy-quiet-60s“: 1.474 vollständige Batches/60 s = 24,566 FPS,
  keine Worker-Drops/Fehler; gepackte Pixel im Mittel 1,125 ms. Firmwarecompiler
  waren pausiert; sonstige Systemlast (insbesondere OneDrive) blieb bestehen.

Versionierte Zwischenstände:
- d8017bd: erste native NumPy-/Senderoptimierungen, gespeicherter TD-Checkpoint,
  reproduzierbare Messungen und aufnahmebereiter GICO-Kameratest.
- 319c8e5: Teensy-Quellen, Hosttests, funktionsfähige Safe-Ethernet-Firmware und
  erstes experimentelles FastLED-Bench-Image. Letzteres startet noch nicht bis
  zur Statusschleife; eine mögliche FastLED-ObjectFLED-Ursache wird untersucht.
  Dieser Commit ist ausdrücklich KEINE erfolgreiche DMA-Ausgabeabnahme.
- Show-Idle-Synchronisierung anschließend im TD-Projekt installiert; Plan und
  sechs State-/Request-DATs blieben unverändert. 39 gezielte Show-Tests bestanden.
