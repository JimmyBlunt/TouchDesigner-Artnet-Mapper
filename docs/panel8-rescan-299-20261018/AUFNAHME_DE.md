# Panel 8: neuer Scan mit 299 LEDs

Vorbereitet am 18. Oktober 2026. Panel 8 ist rechts in der vorletzten Reihe.

- Controller: 10.0.0.251, physischer Ausgang 1, Art-Net U156–157 (ab 0).
- Hardware meldet bereits 299 LEDs. Es war keine Firmwareänderung nötig.
- TouchDesigner-Routing, Port-Editor, LED-Suche und Scan-Plan sind auf 299 eingestellt.
- Aufnahme-IDs: 0–298. Im späteren Gesamtmodell ist der freie Quellbereich 2720–3018 vorgesehen.
- Neuer Aufnahmeordner: `Scans/Panel8_OUT1_299_20261018` im Projektordner.
- Gesichertes Projekt: `PixelblazeMapper_PANEL8_299_SCAN_READY_20261018.1.toe`.
- Sicherung davor: `PixelblazeMapper_BEFORE_PANEL8_299_20261018.1.toe`.

## Aufnehmen

1. Im geöffneten Scan-Fenster prüfen, dass **299 LEDs** und **PANEL8_OUT1_299_20261018** angezeigt werden.
2. Mit **CHECK CAMERA** die Kamera-Vorschau starten und das gesamte Panel ins Bild nehmen. Belichtung und Fokus während einer Ansicht konstant halten. Voreingestellt sind Kamera 0, Belichtung −10, Schwelle 160 und Scan-Helligkeit 9,9 %. Die Kamera wurde in dieser Vorbereitung nicht gestartet; die Eignung dieser Werte muss am realen Bild geprüft werden. Danach die Vorschau mit **CLOSE CAMERA** schließen. Nach Einstellungsänderungen **CHECK SCAN PLAN** drücken.
3. Mit **START SCAN / NEXT VIEW** eine vollständige Scan-Ansicht starten. Kamera und Panel während des Durchlaufs ruhig halten, bis die Ansicht gespeichert ist.
4. Kamera zwischen den Durchläufen versetzen und mehrere überlappende Ansichten aufnehmen, zum Beispiel frontal und schräg von links und rechts. Auch Rand-LEDs müssen sichtbar sein. Ziel sind möglichst mindestens drei Erfassungen pro LED aus unterschiedlichen Blickrichtungen.
5. In derselben neuen Scan-Sitzung bleiben. Keine alten Panel-8-Aufnahmen hinzufügen, weil sich die Anordnung verändert hat.
6. Danach gemeinsam die Abdeckung und fehlende IDs prüfen, 3D rekonstruieren und das bestehende Panel gezielt ersetzen und ausrichten.

## Geprüfter Zustand

Alle 299 Scan-Adressen wurden ohne LED-Ausgabe geprüft, einschließlich des Übergangs 169/170 zwischen U156 und U157. Der Scan sendet vollständige Frames U156–162; die anderen Ausgänge dieses Controllers bleiben dabei schwarz. Vorhandene Ansichten wurden gesichert und aus der neuen Sitzung entfernt. Die Sitzung hat 0 Ansichten und 299 erwartete LEDs. Scan-Plan und Routing-Signatur stimmen überein. Keine TouchDesigner-Operatorfehler oder Warnungen im Scan-/Router-Netz.

Das bisherige Modell mit 256 Positionen bleibt vorläufig als alte Referenz erhalten. Es ist keine gültige Vermessung des umgebauten Panels. Die 43 zusätzlichen Live-Quellslots bleiben bis zum neuen Mapping schwarz; der separate Scan kann sie bereits ansteuern. Alle anderen Positionen und Panel-Routen sind unverändert. LED-Ausgabe und Aufnahme sind aus.

Im Router bestehen Hinweise auf bereits vorhandene freie Quellbereiche und einen überlappenden Bereich einer deaktivierten APA102-Route. Das ist kein Scan-Adresskonflikt. Ausgang 3 desselben Controllers meldet 196 Hardwareplätze, während die bestehende Route nach der früheren Entfernung einer LED 195 nutzt; diese separate Zuordnung wurde nicht verändert.

Technische Nachweise: `prepared.json`, `verification.json`, `scan-plan.json`, `controller-readback.json` und die Sicherungen in diesem Ordner.
