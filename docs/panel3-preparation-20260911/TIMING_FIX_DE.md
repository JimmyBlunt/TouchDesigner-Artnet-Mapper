# Sendetiming korrigiert, Messung fuer naechste Aufnahme

Ausloeser: Nutzer beobachtet auch in der zweiten Panel-3-Ansicht etwa 1,5 LEDs/s. Die laufende Aufnahme wurde nicht gestoppt, neu geladen oder umkonfiguriert. Beim Beginn der Diagnose waren 207 LEDs geprueft, 195 erkannt; Supervisor-Launcher PID 18496. Aenderungen betreffen den Code, den erst der naechste Scanstart in neuen Prozessen laedt.

## Behobener Fehler

Der periodische Art-Net-Refresh verwendete einen Zeitpunkt von vor dem eventuell blockierenden Senden. Dadurch konnte eine Wiederholung zu frueh als faellig gelten und den naechsten Schaltbefehl um einen weiteren 50-ms-Takt verzoegern. Die Schleife prueft jetzt mit frischer monotoner Zeit gegen den Zeitpunkt der tatsaechlich abgeschlossenen Uebertragung.

Deterministische Regression: ON angefragt bei 1 ms, gesendet/bestaetigt bei 50 ms; OFF angefragt bei 65 ms. Vorher wurde OFF erst bei 150 ms bestaetigt, mit Fix bei 100 ms. Das ist eine belegte Verbesserung fuer diesen Ablauf, keine gemessene Beschleunigung des gesamten realen Scans.

Unveraendert: 20-Hz-Ausgabeobergrenze, Controller-/Universenbelegung, volle Blackout-Frames, ACK erst nach Sendung, Heartbeat und Abbruch vor einer weiteren Lichtausgabe. Kameraeinstellungen, Helligkeit und adaptive Erkennungsfristen wurden nicht veraendert.

## Passive Zeitmessung

Ein Wrapper misst die unveraenderten nativen Detektor- und Backendaufrufe. Jeder abgeschlossene LED-Schritt liefert unter capture_status.timing:

- dark_before_ms: Warten auf Dunkelbild vor Einschalten.
- send_on_ms: Einschaltbefehl einschliesslich IPC und Sendepause.
- detect_ms: Bilder lesen, Erkennung und Darstellung bis Ausschalten.
- send_off_ms: Ausschaltbefehl einschliesslich IPC und Sendepause.
- dark_after_ms: Warten auf Dunkelbild nach Ausschalten.
- cycle_ms: gesamte Einzelpruefung.
- camera_read_ms und camera_frames: darin enthaltene Zeit/Anzahl der Kamera-Leseaufrufe. Diese Zeit ist eine Teilmenge der obigen Phasen und darf nicht nochmals zur Gesamtzeit addiert werden.

Es gibt last, mean ueber abgeschlossene Pruefungen und recent_mean ueber die letzten 20. Warmup und Bewegungskontrolle zaehlen nicht mit. Eine abgebrochene Einzelpruefung erscheint als last_completed=false, ohne den Mittelwert abgeschlossener Pruefungen zu veraendern. search_timeout_ms zeigt die adaptive Suchfrist nach dem letzten Schritt, also den Stand fuer die weitere Erkennung. Die letzte Messzusammenfassung wird auch in result.json gespeichert.

Keine zusaetzlichen Kamerabilder, keine Bildkopien oder Netzwerkaufrufe. Die Messung wird erst ab der naechsten Aufnahme verfuegbar; der genaue Engpass der laufenden Aufnahme bleibt noch ungemessen.

## Validierung

86 Tests fuer Timing, Worker, Fortschritt und Dialoge bestanden; danach zwei zusaetzliche Pipeline-Tests ergaenzt und alle sieben Tests von test_scan_capture_timing erneut erfolgreich ausgefuehrt (88 verschiedene Tests insgesamt). Neue Regressionen testen Sendezeit, 20-Hz-Begrenzung, Blackout, Stop waehrend einer Sendepause, Phasensummen, Fehlerweitergabe, begrenzten Messspeicher und Persistenz im Supervisor-Ergebnis. Alle Hardwarezugriffe in Tests simuliert.

Kein TOE-Speichern/Neuladen waehrend des laufenden Scans. Es wurden keine nativen Operatoren veraendert; der bestehende Launcher startet beim naechsten Aufruf die versionierten Python-Dateien. Physische Geschwindigkeit und Erkennungsquote mit dem Fix muessen noch an der naechsten Aufnahme verglichen werden.
