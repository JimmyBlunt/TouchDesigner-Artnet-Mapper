# Panel 4: neue Scanserie nach Masse-Reparatur

Der Benutzer bestätigt nach dem internen Controllertest: Alles läuft
einwandfrei, keine zusätzlichen LEDs blitzen mehr auf. Die zuvor falsch
verbundene Leitung wurde korrigiert. Der Benutzer hat ausdrücklich einer
komplett neuen Scanserie für Panel 4 zugestimmt.

Die TouchDesigner-Verbindung ist wieder erreichbar. Der Controller meldete
den internen Test als beendet. Die Vorbereitung hat keine Kamera und keine
LED-Ausgabe gestartet.

- Neuer Ordner: `Scans/back_panel4_810_249_20260911_repaired`.
- Die vorherige Scanserie unter `Scans/back_panel4_810_249_20260911_fullscan`
  bleibt unverändert als Diagnosebestand erhalten.
- Neue Sitzung mit leerer Ansichtenliste und 0 von 810 erfassten LEDs.
- Lokale LED-Indizes 0–809, Controller 10.0.0.249, Port 4, U133–137.
- Vollständiger Senderahmen U120–137; sonstige Slots schwarz während des Scans.
- Übernommene Kameraeinstellungen: Kamera 0, Belichtung −10, Schwelle 160.
- Scanhelligkeit 9,2 %, Paketabstand 1 ms.

`session-before-restart.json` sichert den vorherigen Sitzungszustand und die
Felder. `prepared.json` enthält den geprüften Plan; `controller-readback.json`
den aktuellen Controllerzustand. Der Plan wurde auf 810 IDs, 18 Universen
pro Rahmen und korrekte Adressierung der ersten/letzten LED geprüft.
Aktive Layoutdaten blieben per Hashvergleich unverändert. Keine Operatorfehler,
keine aktive Anwendungsausgabe nach der Vorbereitung.

Reproduzierbare Vorbereitung: `tools/prepare_panel4_post_repair_20260911.py`.
Der neue Projektcheckpoint und seine SHA-256-Prüfsumme stehen in `save.json`.

Nächster manueller Ablauf: In Capture Views mit Check Camera die aktuelle
Ansicht prüfen, Close Camera, Check Scan Plan, Start Scan / Next View.
Kamera während einer Aufnahme fest lassen; erst nach Abschluss bewegen.
Weitere Ansichten ausschließlich in dieser neuen Sitzung aufnehmen.
