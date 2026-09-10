# Rückwandpanel 2: Anschlussprüfung und Kurztest

Aktuelle Konfiguration direkt von 10.0.0.249 gelesen, 10.09.2026:

| Panel | Ausgang (UI) | GPIO | LEDs | Art-Net-Universen |
|---|---:|---:|---:|---|
| 1 | 1 | 26 | 203 | 120–121 |
| 2 | 2 | 27 | 738 | 122–126 |

Beide Ausgänge: WS2812B, GRB in der Firmware, 30 FPS. Dritter Ausgang deaktiviert. Der Controller verwendet 941 physische LEDs und sieben Universen. Während der Vorbereitung änderte der Benutzer die Zuordnung von einem einzigen 738-LED-Ausgang ab U120 auf die obige Kombination. Die Prüfung vor dem ersten Start verhinderte die Verwendung der veralteten Zuordnung. Controller-Einstellungen wurden durch Codex nicht geschrieben.

## Test und Befund

Eigene Scansitzung mit 738 lokalen LED-Identitäten. Geprüft: 0, 170, 340, 510, 737 (nullbasiert). Kamera 0, Belichtung −10, Schwelle 160, Scanhelligkeit 6,2 %.

1. Nur Panel-2-Universen U122–126 gesendet: keine der fünf LEDs erkannt, keine Ansicht übernommen. Controller danach: 1.035 Pakete, 0 vollständige und 207 unvollständige Frames.
2. Erneuter Test mit vollständigem Controllerbereich U120–126; Panel 1 ausschließlich schwarz. **Drei von fünf LEDs erkannt:** IDs 0, 170 und 510. IDs 340 und 737 fehlen. Bewegungsprüfung bestanden, neue 2D-Testansicht gespeichert. Controller danach: 2.009 Pakete, 98 vollständige und 255 unvollständige Frames (kumulative Zähler; somit weiterhin 48 zusätzliche unvollständige Frames, nicht als fehlerfreier Transport bewertet). Keine gemeldeten Paket-Drops oder Sequenzfehler.

Der Vergleich stützt die Vermutung, dass vollständige Controllerframes bei mehreren aktiven Ausgängen notwendig sind. Er beweist keine vollständige optische oder langfristige Netzwerkabnahme. Die genaue Ursache der zwei fehlenden LEDs ist noch nicht festgestellt. Ein Vollscan der 738 LEDs wurde nicht ausgeführt.

Die zweite Testkonfiguration nutzt im Art-Net-Packer die virtuelle Zielposition 340: zwei Universen mit je 170 Plätzen vor Panel 2. Der Firmwarewert startPixel=203 beschreibt dagegen den gepackten physischen LED-Puffer; er darf hier nicht als Art-Net-Zielposition eingesetzt werden. Weiße Scanpunkte werden im Sender als RGB übertragen; die Firmware übernimmt ihre konfigurierte GRB-Ausgabe.

## Erhaltene Daten und Abschlusszustand

Keine automatische Layoutübernahme oder Registrierung. Vorige Scansitzung einschließlich Eingabefeldern liegt in previous-session.json; alte Scandateien wurden nicht verändert. Mapping, Material-UVs, Routertabellen und Entwurf sind hashgleich. Worker beendet, Kamera freigegeben, Scan-Lease gelöst, alle TD-Ausgänge aus. Blackout-Pakete gesendet; optische Dunkelheit nicht bestätigt.

Die JSON-/CSV-Rohdaten sind im artifact-manifest.json mit SHA-256 aufgeführt. prepared.json zeigt den ersten Plan, prepared-complete-frames.json den korrigierten expliziten Controllerbereich. Die Python-Dateien dokumentieren die tatsächlich ausgeführte TD-Vorbereitung; sie starten für sich keinen Scan.

## Wiederverwendung dieses Diagnoseplans

Die unabhängige Codeprüfung bestätigt local0→U122/slot0, local169→U122/slot507, local170→U123/slot0 und local737→U126/slot171. U120/121 bleiben bei allen ausgewählten Testpunkten schwarz. Die aktuelle eigenständige Scan-UI kann begleitende Schwarzuniversen noch nicht in ihren Einstellungen ausdrücken: CHECK SCAN PLAN würde zum unvollständigen Fünf-Universen-Bereich zurückkehren. Die Bibliotheks-Wiederaufnahme dieses speziellen Diagnosecaptures wird wegen des abweichenden Einstellungsdigests korrekt abgewiesen; sie startet keine falsch zugeordneten LEDs.

Deshalb wurden vorbereiteter Captureplan und Startsignatur nach dem Test explizit entwertet und die Oberfläche als Diagnosezustand beschriftet. Die Ansicht und stabilen Identitäten bleiben erhalten. Vor einem weiteren Vollscan ist der vollständige Controllerbereich U120–126 wieder explizit zu berücksichtigen; eine dauerhafte UI-Unterstützung für begleitende Schwarzuniversen ist noch erforderlich. Dieser Kurztest wird nicht als fertig vorbereiteter Vollscan ausgegeben.
