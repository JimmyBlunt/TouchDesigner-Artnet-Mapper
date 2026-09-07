# MariMapper ArtNet / Router-IPC – Primärquellenreview

Stand 2026-09-07. Installiert ist MariMapper **3.4.2** laut `marimapper-3.4.2.dist-info/METADATA`. Die folgenden Implementierungsbefunde beziehen sich auf diese Installation, nicht ungeprüft auf GitHub `main`.

## Bestehender Vertrag und Grenzen

Die offizielle [Custom-Backend-Anleitung](https://github.com/themariday/marimapper/blob/main/docs/backends/custom.md) verlangt `get_led_count()` und `set_led(led_index, on)`. Der installierte [Prüfer](C:/Users/jbhtz/AppData/Roaming/uv/tools/marimapper/Lib/site-packages/marimapper/backends/custom/custom_backend.py:38) prüft deren gebundene Signaturen. Sein CLI-Loader erzeugt dagegen ausdrücklich `Backend()` ohne Argumente (Zeile 32). Unser Adapter benötigt absichtlich einen injizierten Kanal: Verwendung über `DetectorProcess` und dessen Backend-Factory, **nicht** als unmittelbar startbare Custom-CLI-Datei. Der installierte [DetectorProcess](C:/Users/jbhtz/AppData/Roaming/uv/tools/marimapper/Lib/site-packages/marimapper/detector_process.py:131) erstellt das Backend erst im Kindprozess aus der Factory.

| Thema | Installiertes ArtNet-Backend | Neuer Router-IPC-Adapter |
|---|---|---|
| Besitz der Ausgabe | Eigener UDP-Socket pro Backend; ein Zielserver | Kein Socket; Supervisor besitzt Ausgabe und Lease |
| Adressierung | Fortlaufende Universen ab Basis, feste Kanäle je Fixture | Dichte Worker-IDs; Supervisor übersetzt eingefrorene Auswahl in originale Source-IDs und bestehende Routen |
| LED-Schritt | Nullt eigenen gesamten Kanalpuffer, setzt Fixturekanäle auf 255 | Synchroner `set_led`-Auftrag; Supervisor entscheidet über begrenzte Helligkeit und Framepakete |
| Zeitverhalten | Fünf Sendewiederholungen mit jeweils 50 ms Pause, anschließend ArtSync | Warten auf passende Supervisor-Bestätigung mit Deadline; keine zusätzliche feste Pause |
| Fehler | Socketfehler können propagieren; kein Supervisor-Lease-Vertrag | Timeout/EOF/Ablehnung/ungültige Bestätigung sperrt weitere Aufträge |

Beleg: [installiertes ArtNet-Backend](C:/Users/jbhtz/AppData/Roaming/uv/tools/marimapper/Lib/site-packages/marimapper/backends/artnet/artnet_backend.py:37), Socket Zeile 65, `set_led` Zeile 109, Wiederholungen Zeilen 129–135. Seine Formel `channels // 512 + 1` erzeugt bei exakten 512-Kanal-Vielfachen außerdem ein zusätzliches schwarzes Universum. Die allgemeine fortlaufende Fixture-Annahme ersetzt keine Validierung des vorhandenen Multi-Controller-Routings. Es wird hier kein ArtNet-Code kopiert und kein installiertes Paket verändert.

## Integrationsvertrag

`partial(pipe_backend, connection, count, timeout)` ist die pickelbare Factory aus `pixelblaze_mapper.marimapper_router_backend`. `count` ist die Anzahl ausgewählter LEDs **inklusive Anker**. Beispiel: Auswahl original `[517, 785]` bedeutet Worker `0, 1`, Count `2`; der Supervisor und Ergebnisexport erhalten die stabile Rückabbildung. Der Adapter rät keine Zuordnung.

Der dedizierte lokale Duplexkanal erhält `{'action':'set_led','index':i,'on':bool,'request_id':n}` beziehungsweise `{'action':'blackout','request_id':n}`. Erfolg erfordert `{'ok':True,'request_id':n}`; Ablehnung `{'ok':False,'request_id':n,'error':'...'}`. IDs steigen ab 1. Zusätzliche Antwortfelder sind erlaubt; fehlende/falsche IDs und nichtboolesches `ok` scheitern. Keine automatischen Wiederholungen: Nach einem Timeout könnte der erste Auftrag bereits physisch wirksam sein.

`set_leds` akzeptiert ausschließlich einen vollständigen schwarzen RGB-Puffer der Worker-Anzahl und übersetzt ihn in `blackout`. Nichtschwarze Mehr-LED-Muster sind ausdrücklich unzulässig. Native Fast-Detektion erzeugt solche Muster ([detector_fast.py](C:/Users/jbhtz/AppData/Roaming/uv/tools/marimapper/Lib/site-packages/marimapper/detector_fast.py:69)); ebenso kann die native Statusfarbanzeige dies versuchen ([detector_process.py](C:/Users/jbhtz/AppData/Roaming/uv/tools/marimapper/Lib/site-packages/marimapper/detector_process.py:33)). Beide Modi müssen im aufrufenden Worker ausgeschlossen bleiben. Schwarzsetzung wird bei IPC-Fehlern nicht als erfolgreich behauptet; unabhängiger Supervisor-Abbruch und Notfall-Nullsetzung bleiben erforderlich.

## Sicherheits- und Testgrenze

`PipeTransport` begrenzt die Antwortwartezeit über `poll` und lehnt verspätete Rückkehr ab. `Connection.send/recv` haben selbst keine hart abbrechbare Deadline; ein blockierter/unvollständiger Kanal braucht den unabhängigen Prozess-Watchdog des Supervisors. Der Kanal ist ausschließlich für einen vertrauenswürdigen lokalen Prozess bestimmt (Multiprocessing deserialisiert Pickle). Ein Kanal/Backend bedient genau einen synchronen Aufrufer. Keine Kamera, kein UDP und keine native Backend-Instanziierung erfolgen in diesem Modul.

Offline-Tests mit Fake-Transport/Fake-Pipe prüfen Signaturen, ausgewählte Worker-IDs, Schwarzpuffer, ungültige Argumente, ACK-Zuordnung, Fehlerverriegelung, verspätete Antwort, EOF, Reentranz und pickelbare Factory. **Keine bestandene Ende-zu-Ende-Erfassung oder beobachtete LED-Reaktion behauptet.** Selbst ein gültiges ACK bestätigt nur den Supervisor-Auftrag, nicht einen elektrischen/optischen Hardwarezustand.

## Supervisor-Abschlussprüfung

`scan_capture_worker` verwendet den nativen Einzel-LED-Detektor in einem eigenen kooperativen Kamera-Wrapper, nicht den unveränderten `DetectorProcess`. Vor Sockets prüft der gemeinsame Camera-Probe-Helfer die installierte Version **und** den geprüften Commit. Manifest, Kameraeinstellungen, fest begrenzte Zeiten und eine kanonische neue Capture-Unterdirectory-ID werden validiert. ArtSync-Routen werden derzeit vor Ausgabe ausdrücklich abgelehnt; keine stillschweigend fehlende Synchronisation. Die reguläre Senderkadenz ist höchstens 20 Hz und höchstens die kleinste konfigurierte Controller-Rate. Die erste Notfall-Schwarzsetzung darf zur Sicherheit sofort erfolgen, nachfolgende Wiederholungen halten die Kadenz ein.

Die neuen Supervisor-Tests simulieren alle Geräte/Prozesse. Sie prüfen Abbruch, fehlenden Heartbeat, 40-Sekunden-Fortschrittsgrenze, Start-/Childfehler, vollständig schwarze reservierte Universen, unzulässige Indizes und originale CSV-IDs. Ein Erfolg wird erst nach der Abschluss-Schwarzsetzung und sauberem Child-/Kamera-Aufräumen zurückgegeben; ein später nichtnuller Worker-Exit überschreibt einen zuvor eingegangenen Erfolgsstatus. Die native 30-Sekunden-Grenze wird in kooperativen Reads geprüft, einschließlich `eat`; ein in OpenCV blockierter Read wird weiterhin durch den separaten Supervisor abgebrochen, nicht durch Python im blockierten Kamerathread.
