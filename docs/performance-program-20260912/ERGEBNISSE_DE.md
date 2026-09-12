# Leistungsprogramm: Ergebnisse und verbleibende Abnahme

Stand: 12. September 2026. Alle Werte stammen aus gespeicherten Messungen; Empfang, Treiberabschluss und sichtbare LED-Bilder sind unterschiedliche Nachweise.

## Ergebnisübersicht

| Bereich | Gemessen / vorbereitet | Grenze der Aussage |
|---|---|---|
| ESP, angeschlossene 256 WS2812 + 512 APA102 | 3.599 vollständige Bilder und je 3.599 Ausgangstransfers in 120,002 s: **29,991 FPS**; alle 21.594 Pakete angekommen | Schwarzer Lasttest, noch keine optische Bildnummernauswertung |
| ESP, virtuelles Profil mit 1.755 Pixeln | 1.800/1.800 Empfangsbilder, 21.600/21.600 Pakete, 1.799 Ausgaben in 60 s: **29,983 FPS** | Physisch bleiben nur ca. 768 LEDs angeschlossen; ein wartendes Bild wurde durch ein neueres ersetzt |
| TouchDesigner, lokaler Empfang | **31,650 FPS** über 60 s bei Ziel 32; mindestens 29 Bilder in einer vollen Sekunde; größter Abstand 136,188 ms | Durchschnitt über 30 erreicht, streng gleichmäßige 30 FPS unter Windows noch nicht abgenommen |
| TouchDesigner → Teensy, echte Animationsdaten | **33,770 vollständige Empfangsbilder/s**, **29,771 DMA-Abschlüsse/s** über 90 s; keine unvollständigen Bilder oder Queue-Drops | Teensy-Ausgabe auf höchstens 30 FPS begrenzt; keine LEDs angeschlossen |
| Teensy, unabhängiger Sender | **29,983 DMA-Abschlüsse/s** über 120 s; 4.081/4.081 vollständige Bilder, 114.268/114.268 Pakete | Ausgabe maximal 30 FPS; keine optische Abnahme |
| GICO | Kameratest mit kodierten Bildnummern, Anleitung und Auswertung bereit; 16 Softwaretests bestanden | Aufnahme durch Benutzer steht aus; keine neue optische GICO-FPS-Messung |

## Was geändert wurde

TouchDesigner packt die Pixel per NumPy. Masken, Vorschaupositionen und unveränderte Statusdaten werden zwischengespeichert; doppelte Pixelabfragen und unnötige Show-Synchronisierung entfallen. Der separate Sender taktet vollständige Bilder, verwirft veraltete wartende Bilder und meldet Sendefehler sichtbar. Nichtblockierende UDP-Ausgabe und selteneres Lesen der Stop-/Statusdateien reduzieren Wartezeiten. 75 gezielte Worker-, Pacing- und UI-Tests sowie 39 Show-Tests bestanden. Payloads wurden gegen die skalare Referenz geprüft; Routing und Scandaten blieben erhalten.

Beim ESP verursachte die kleine SDK-Socket-Mailbox Burstverluste. Die neue Raw-UDP-Annahme kopiert Pakete in eine begrenzte Queue mit 64 Einträgen; Zähler machen Überläufe, fremde Quellen und alte ARM-Generationen sichtbar. WS2812-I2S und APA102-SPI arbeiten parallel und melden den gemeinsamen Abschluss. Vorher lieferte das virtuelle 12-Universen-Profil mit der experimentellen Socket-Version nur 16 von 898 Bildern; nach der Änderung kamen 1.800 von 1.800 an. Hardwaretests für fehlerhafte/übergroße Pakete und den ARM-Wechsel bestanden.

Der Teensy verwendet die moderne FastLED-Channel-API mit parallelem ObjectFLED-DMA, ohne OctoWS2811. Der vorgelagerte Ethernet-Ring wurde im Testbuild SHA-geprüft von 5 auf 32 Empfangsdeskriptoren erweitert. Mit aktiver Ausgabe gingen zuvor 22 von 25.200 Paketen verloren; der Folgeversuch empfing alle 50.344 Pakete. Der große 90-s-Integrationstest empfing danach alle benötigten Universen für 3.040 vollständige Bilder. U138 ist eine reservierte Lücke: dessen 3.040 Pakete wurden erwartungsgemäß ignoriert, nicht verloren.

## PC und Betriebsprofil

Nach dem Schließen von Chrome stieg der freie RAM von etwa 0,5–0,7 GB auf rund 3 GB. Starker Speicherdruck hatte zuvor sogar unabhängige Testsender und Pythonstarts gebremst. Temporäres Beenden der beiden verifizierten OneDrive-Prozesse und Bindung von TouchDesigner an die vier schnellen logischen CPUs verbesserte die Messungen weiter. Erhöhte Prozesspriorität brachte keinen Vorteil und wurde verworfen.

Die reproduzierbaren Wrapper `tools/td_fast_cores_benchmark_20260912.ps1` und `tools/td_sync_quiet_benchmark_20260912.ps1` stellen nach jedem Lauf CPU-Affinität, OneDrive, Perform-Modus, Routing und Controller-Einstellungen wieder her. Das ist ein gemessenes Testprofil, keine unbemerkte permanente Systemänderung. Seltene Windows-/Producer-Pausen bleiben messbar. Eine Durchschnittsrate über 30 ist deshalb keine Garantie für alle einzelnen 33,3-ms-Zeitfenster.

## Aktuell gespeicherter Zustand

- TD-Projekt: `PixelblazeMapper_30FPS_PROGRAM_20260912_worker-clock-ui.1.toe`, SHA256 `1acf5c42671f5ca2068f09c886905b28b8f6ebeb4138aa94eb9f6c038f09e03a`. Optimierungen installiert, Frame-Pacing aktiv, Priorität Normal.
- ESP COM5 / MAC E8-68-E7-0D-38-A4 / 10.0.0.151: **physical768-raw-v2**, WS256 GPIO14 U0–1, APA512 DATA18/CLOCK19 U2–5. Ausgabe deaktiviert. Originalflash zweimal identisch privat gesichert; keine Zugangsdaten im Git-Archiv.
- Teensy COM4 / Seriennummer 7858800 / 10.0.0.253: **unwired RX32 FastLED-Testbuild**, nach Tests STOP/schwarz. USB und Ethernet verbunden, keine LEDs.
- Produktiver ESP 10.0.0.248 und GICO 10.0.0.244 wurden nicht geflasht. Die bisherige produktive 8-FPS-Konfiguration bleibt erhalten; der Testcontroller-Erfolg ist noch keine Freigabe dieser Geräte.

## Noch notwendige Schritte

1. GICO-Kameralauf aus `gico/ANLEITUNG_DE.md` filmen und die Originaldatei auswerten. Der Test ist startbereit; eine Aufnahme kann der Agent nicht ersetzen.
2. Teensy-Ausgänge tatsächlich verdrahten und optisch/elektrisch prüfen. Das vorbereitete Profil nutzt Pins 2–8 und sieben Ketten mit 203/738/880/810/352/680/442 Pixeln. Die bisherige 1.122er-Kette muss dafür physisch bei 680 geteilt werden. Die Pinbelegung ist derzeit ausschließlich für den bestätigten unverdrahteten Test freigegeben.
3. Erst nach dieser Hardwareabnahme die konkrete Produktionskonfiguration migrieren und einen längeren Lauf mit realen Panels abnehmen. Die experimentellen Images enthalten noch kein vollständiges Controller-Webmenü, Art-Net-Discovery oder Mehrsender-Merging.
4. Für eine strenge 30-FPS-Garantie bleiben Producer-/Windows-Jitter und der optische Dauertest offen. Die bisherige Verbesserung ist gemessen; eine Aussage, es gäbe keinerlei weitere Optimierungsmöglichkeiten, wäre nicht belegt.

## Messbelege und Versionierung

- ESP: `esp/physical768-raw64-final120s.json`, `esp/virtual1755-raw64-burst30-60s.json`, `esp/raw64-ingress-hardware-regression.json`.
- TD: `td/fast-cores-32fps-60s.json`, `td/td-teensy-fastcores-34fps-90s.json` sowie zugehörige Affinitäts-/Sync-Wiederherstellungsbelege.
- Teensy: `teensy/RX32_ERGEBNISSE_DE.md`, Build-/Flashmanifeste und einzelne Rohmessungen. Der erste fehlgeschlagene RX32-Flashversuch bleibt dokumentiert; der identitäts- und hashgeprüfte zweite Versuch gelang.
- Bisherige Commits: d8017bd (erste TD-Optimierung/GICO), 319c8e5 (Teensy-Grundlage), a0655b4 (Show-Synchronisierung), d59c1fa (ESP-Grundlage), f0110ac (moderner FastLED-Pfad), 414080c (Worker/UI und nativer TD-Checkpoint). Weitere Abschlussänderungen stehen im Git-Verlauf dieses Berichts.

Die drei parallel beauftragten Agenten bearbeiteten GICO, ESP und Teensy. Nach ihrem Kontonutzungslimit führte der Hauptagent Integration, weitere Firmwarekorrekturen, Messungen und Dokumentation fort.

Abschluss-Commits: `fa74eec` (ESP Raw64 einschließlich beider Hardwareprofile), `385d5ed` (Teensy RX32 einschließlich 120-s-DMA-Test). Firmwarearchive, HEX/ELF und gespeicherter TD-Checkpoint wurden abschließend gegen ihre SHA256-Manifeste geprüft (`final-artifact-verification.json`). `final-hardware-state.json` und `final-td-state.json` bestätigen ausgeschaltete Ausgaben und unverändertes Routing. Die originale Leerzeile im fehlgeschlagenen Teensy-Flashlog bleibt als unveränderter Rohbeleg erhalten.

Die aktive Messphase ist beendet. Die zehnminütige Statusautomation wurde bis zur nächsten Hardware-/Kameraabnahme pausiert; die noch offene strenge Jitter-Abnahme wird dadurch nicht als erfüllt markiert.


## Nachtrag: erste GICO-Originalaufnahme

Die Originaldatei wurde inzwischen vollständig ausgewertet. Im 30-FPS-Fenster wurden 1.785 aufeinanderfolgende Bildnummern ohne Lücke mindestens einmal erkannt, etwa 29,991/s. Darin enthalten ist eine begrenzte CRC-Rekonstruktion unklarer Bits; 593 IDs werden nur durch ein Kamerabild bestätigt. Das spricht deutlich für 30 FPS am gefilmten Panel dieses unabhängigen Sendertests. Eine strenge Zweibild-, elektrische oder TD→GICO-Abnahme folgt daraus noch nicht. Ausführliche Grenzen, Decoderverbesserung und Rohdaten: `measurements/gico-camera-001-original-review/ERGEBNISSE_DE.md` im Projektroot. Die ursprüngliche Tabellenzeile zum damals noch ausstehenden GICO-Video bleibt als zeitlicher Zwischenstand lesbar.
