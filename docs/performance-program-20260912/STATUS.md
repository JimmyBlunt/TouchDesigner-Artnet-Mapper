# Paralleles Leistungsprogramm

Gestartet 12.09.2026 auf ausdrücklichen Benutzerauftrag. System- und
Firmwareänderungen sind erlaubt; Ergebnisse werden getrennt nach Build,
Softwaretest und Hardwaremessung dokumentiert.

| Bereich | Zuständig | Stand |
|---|---|---|
| GICO-Kameratest | gico_camera_test | Aufnahmebereit; 16 Tests bestanden; echte Kameraaufnahme noch offen |
| TouchDesigner | Hauptagent | NumPy/Masken/Preview installiert und referenzgleich; 24,57 FPS im 60-s-Lauf, weitere Optimierung läuft |
| ESP | esp_firmware_30fps | COM5 identifiziert, 2 identische Flashbackups; Testprofil 256 WS + 512 APA im Build |
| Teensy 4.1 | teensy_fastled_30fps | Safe-Firmware geflasht: COM4, Ethernet-Link, IP 10.0.0.253; FastLED-Bench im Build |

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
