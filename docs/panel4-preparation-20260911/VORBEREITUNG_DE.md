# Panel 4: Scanvorbereitung

Benutzerangaben: unter Panel 2, gleiche Panelgröße 30 × 30 cm, **810 LEDs**, Controller **10.0.0.249**, physischer **Ausgang 4**, **Startuniversum 133**.

Die aktive Controller-Konfiguration wurde per HTTP nur gelesen: Ausgang-ID 3, GPIO 14, 810 LEDs, U133, aktiviert. Vorherige Ausgänge bleiben 203/U120, 738/U122 und 880/U127. Gesamt 2631 physische LEDs, 18 Universen. Es wurde keine Controller-Konfiguration geschrieben.

Guided Scan enthält eine neue separate Aufnahme `BACK_PANEL4_810_249` mit lokalen IDs **0–809**. Eigener Arbeitsordner: `Scans/back_panel4_810_249_20260911_fullscan`. Der Scan umfasst **U133–U137**, sendet vollständige Controllerrahmen **U120–U137** und hält die übrigen Slots schwarz. Kamera 0, Belichtung −10, Schwellwert 160, Helligkeit 9,2 %, Paketabstand **1 ms**. Die Endpunkte wurden ohne Netzwerkausgabe gepackt: LED 0 auf U133/RGB-Slot 0, LED 809 auf U137/RGB-Slot 129.

Die fünf Ansichten und das 3D-Ergebnis von Panel 3 bleiben auf Disk und im abgeschlossenen Panel-3-Projekt erhalten. `panel3-session-before.json` sichert zusätzlich den vorherigen Dialogzustand. Der neue Dialog zeigt null gespeicherte Ansichten und 810 erwartete LEDs; frühere Ergebnis-/Registrierungsdaten wurden aus dem neuen Aufnahmezustand entfernt. Aktive Map, UVs und Routing wurden anhand des aktiven Hashs als unverändert bestätigt. Keine Operatorfehler; Kamera und LED-Ausgabe wurden nicht gestartet.

`prepared.json` hält Plan und Einstellungen fest, `controller-readback.json` die Controller-Konfiguration. Während der Vorbereitung hat der Benutzer bereits die Kameravorschau gestartet. Der zusätzliche TOE-Speicherversuch wurde deshalb vor jeder Änderung durch die Idle-Prüfung abgewiesen; die Vorschau blieb unbeeinträchtigt. Ein eigener Panel-4-TOE-Checkpoint steht noch aus. Der abgeschlossene Panel-3-Checkpoint bleibt vorhanden; Vorbereitung und Plan werden separat in Git gesichert.

Nächster manueller Schritt: **CHECK CAMERA**, Panel vollständig ins Bild nehmen, **CLOSE CAMERA**, anschließend **START SCAN / NEXT VIEW**. Werden Einstellungen verändert, vorher erneut **CHECK SCAN PLAN** drücken. Der Paketabstand bleibt 1 ms; eine Geschwindigkeit für den vergrößerten 18-Universen-Rahmen ist erst nach dem ersten Vollscan gemessen.

Nachtrag: Die erste Aufnahme wurde inzwischen mit 804/810 Erkennungen und ca. 2,06 LEDs/s abgeschlossen. Danach wurde bei gestoppter Kamera und Ausgabe der Checkpoint `PixelblazeMapper_PANEL4_VIEW1_SAVED_20260911.1.toe` gespeichert; `view1-save.json` enthält SHA-256 und Speichernachweis. Das vom Benutzer gemeldete Flackern wird in `video-analysis/BEOBACHTUNG_DE.md` getrennt beurteilt.
