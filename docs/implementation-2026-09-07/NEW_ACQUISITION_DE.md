# Erstaufnahme ohne vorhandenes Layout

8. September 2026. Neuer Einstieg für ein physisches Rückwand-Panel, dessen Daten zunächst separat erfasst werden. Keine zusätzliche Geometrie im bestehenden Layout; Zuordnung und Zusammenbau der zehn Panels erfolgen später.

## Scan vorbereiten

1. **Ctrl+Shift+G** → **NEW CAPTURE (NO LAYOUT)**.
2. Aufnahmename z. B. `TEST_249`; Controller `10.0.0.249`; lokale Schnittstelle `10.0.0.125`.
3. **START UNIVERSE (WIRE, ZERO-BASED): 120**, LED-Anzahl **256**, FPS-Limit **30**.
4. Netzwerk-Farbreihenfolge **RGB**: Das gelesene Controller-Webinterface beschreibt empfangene RGB-Pixel und übernimmt die GRB-Anordnung am WS2812-Ausgang. Nicht beide Seiten ungeprüft vertauschen; den späteren Farbtest getrennt durchführen. Der weiße Scan ist hiervon unabhängig.
5. **CREATE ACQUISITION (OUTPUT OFF)** erzeugt eine separate Sitzung. Lokale LED-Nummern sind 0–255; eindeutige Aufnahme-IDs verhindern die Verwechslung mit Source-IDs im Schrank-Layout. Vorhandene Scan-Dateien werden nicht gelöscht.
6. Im Hauptdialog Kamera/Belichtung/Schwelle und existierenden Arbeitsordner prüfen; **CHECK SCAN PLAN** startet noch nichts.
7. Erst ausdrücklich **START SCAN / NEXT VIEW** bestätigen. Dabei wird ausschließlich der neue Zielcontroller auf wire 120–121 bedient, nicht der bisherige Schrankcontroller. Nach der Aufnahme Kamera versetzen für weitere Ansichten. USB während des Tests nicht trennen.

Die CSVs enthalten lokale Indizes. Sie dürfen nicht als Ersatz für bestehende globale LEDs interpretiert werden. Rekonstruktion und spätere Zuordnung bleiben getrennt; ein automatischer Ersetzungs-Handoff für diese Sitzung wird abgelehnt. Die bestehenden Grenzen der [Scan-Anleitung](GUIDED_SCAN_ARTNET_DE.md) gelten weiter, einschließlich noch fehlender Interpolation und ausstehender physischer Scan-Abnahme.

## Controller für später als Entwurf anlegen

**Ctrl+Shift+C** → CONTROLLER ID `TEST_249` → **NEW DRAFT**. Bestehende Controller nicht überschreiben.

| Feld | Wert |
|---|---|
| PROFILE | independent |
| TARGET IPv4 | 10.0.0.249 |
| LOCAL INTERFACE | 10.0.0.125 |
| UDP PORT | 6454 |
| FIRST UI U | **121** (UI zählt ab 1; entspricht wire 120) |
| RATE FPS | 30 |
| BRIGHTNESS | 0.05 für spätere erste Ausgabetests |
| ENABLED | 0 |
| DEFAULT COLOR ORDER | RGB, später mit Farbtest prüfen |
| Erste Portzeile PIXELS / RESERVE U | 256 / 2 |
| Erste Portzeile SOURCE | leer: noch keine Animationszuordnung |
| Erste Portzeile ON | 0 |
| Erste Portzeile TARGET | leer = automatische Ausgangsposition |

**VALIDATE DRAFT** prüft den Entwurf. **SAFE APPLY** ist die getrennte Übernahme in die Live-Router-Konfiguration und wurde hier nicht ausgeführt. Für den isolierten Guided Scan ist diese Übernahme nicht erforderlich. Der im Webinterface mit Output 0 bezeichnete erste Ausgang entspricht hier organisatorisch der ersten Portzeile; die physische GPIO-Konfiguration wird dadurch nicht geändert.

## Prüfung dieser Erweiterung

- Reale TouchDesigner-Callbacks zum Anlegen und Vorbereiten ausgeführt; keine Kamera und keine LED-Ausgabe gestartet. Keine Behauptung vollständiger Mausklicktests für das neue Dialogfenster.
- Vor/nach identische SHA-256-Werte für aktive Map, UV-Tabelle, Controller- und Segmenttabellen.
- Ausgabeplan: lokale LED 0 → wire 120/Kanal 1; LED 169 → wire 120/Kanal 508; LED 170 → wire 121/Kanal 1; LED 255 → wire 121/Kanal 256. Jeweils RGB-Dreiergruppen, exakt 510 Kanäle pro Paket.
- Tests prüfen ungültige Konfiguration, unverändertes Live-Routing, getrennte Identitäten, veränderte Scan-Einstellungen und den weiterhin funktionierenden vorhandenen Layout-Scan.
- Das reale LED-Aufleuchten und die optische Erkennung stehen weiterhin aus.
