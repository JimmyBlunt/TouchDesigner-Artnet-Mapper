# Leistungsprogramm: aktueller Stand

12.09.2026. Ausführliche Bewertung und Rohbelege: [ERGEBNISSE_DE.md](ERGEBNISSE_DE.md).

| Aufgabe | Stand | Noch offen |
|---|---|---|
| GICO-Kameratest | Erster Lauf mit 15/25/30 FPS abgeschlossen; 5.030 Batches ohne gemeldeten Sendefehler, Schwarz gesendet | Originalvideo des unteren Panels (angegeben: 60 Kamera-FPS) auswerten |
| TouchDesigner | NumPy, Cache, Show-/UI-Optimierung und Worker installiert, getestet und als neues .toe gespeichert; lokal 31,650 FPS, bis zum Teensy 33,770 vollständige Bilder/s | Seltene Producer-/Windows-Pausen; streng gleichmäßige 30-FPS-Abnahme und produktiver Panel-Dauertest |
| ESP | Testnode .151 physisch 256 WS +512 APA; finaler Raw64-Build geflasht, 120 s mit 3.599/3.599 Ausgaben =29,991 FPS, keine Empfangsverluste | Optische Bildprüfung und spätere Produktionsmigration |
| Teensy | FastLED ohne Octo, RX32 auf .253; unabhängiger 120-s-Test 29,983 DMA-FPS, alle 114.268 Pakete empfangen | LEDs/Pegelwandler anschließen, Pinout und Kettenaufteilung prüfen, optischer Dauertest |

Ausgaben nach jedem Test deaktiviert und nachgeprüft. Produktivcontroller .248 und .244 unverändert; TD außerhalb Tests auf ursprüngliche Controllerdaten zurückgesetzt. OneDrive und CPU-Affinität nach den Messungen wiederhergestellt.

Die Agenten arbeiteten parallel an GICO, ESP und Teensy. Nach deren Kontonutzungslimit übernahm der Hauptagent Firmwarekorrekturen, Integration und Abschlussmessungen. Alle eigenen Änderungen werden gezielt versioniert; vorhandene fremde Workspaceänderungen bleiben unberührt. Historische Zwischenstände stehen in STATUS_ZWISCHENSTAENDE.md; Messdateien werden nicht überschrieben.

Aktive Messphase beendet; Statusautomation bis zur nächsten Hardware-/Kameraabnahme pausiert. Die offenen Abnahmen bleiben ausdrücklich offen.
