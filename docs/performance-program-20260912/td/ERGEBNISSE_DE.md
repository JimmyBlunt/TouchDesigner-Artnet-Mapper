# TouchDesigner – laufende Leistungsoptimierung, 12.09.2026

Dies ist ein Zwischenstand. Die Abnahme stabiler 30 FPS ist noch offen.

## Umgesetzte Änderungen

- RGB-Snapshot und Routing mit NumPy statt tausender Python-Kanalzugriffe.
  Float64-Multiplikation und Rundung erhalten die skalaren Referenzbytes.
- Streng validierte Maske bleibt unverändert; manuelle Table-DATs verwenden
  nach cook(force=False) totalCooks als Revision. Dynamische, gesperrte und
  unbekannte Tabellen behalten vollständige Textvalidierung.
- Vorschau überträgt Float32-Arrays mit benannten Channel.copyNumpyArray;
  unveränderte angepasste Positionslisten werden nur einmal konvertiert.
- Sender-Telemetrie cached Dateilesen für maximal 100 ms, prüft den Prozess
  weiterhin bei jedem Aufruf; Prozessende und Cleanup lesen finale Werte.
- Lokale UDP-Übergabe prüft Format, Ziel, Eindeutigkeit, leere Batches und
  Größenlimit direkt, ohne redundanten eigenen JSON/Base64-Decode.

## Nachweise und Grenzen

Alle nativen Installationen prüfen Controller-Payloads gegen Scalar-Referenz,
Maskenwerte einschließlich Kanalnamen sowie unveränderte Hashes von Mapping,
Masken-, Segment- und Controllertabellen. Sender und native Ausgaben müssen
vor Installation oder Speichern ausgeschaltet sein. Kein Scan wird verändert.

Baseline unter paralleler Compilerlast: 15,02 FPS, Packen 11,81 ms.
NumPy + Maskencache bei pausierten Compilern: 24,566 FPS über 60 Sekunden,
Packen 1,125 ms, keine Worker-Drops oder Fehler. OneDrive und andere normale
Systemprozesse waren dabei weiterhin aktiv; dies ist keine isolierte CPU-Messung.

Spätere diagnostische Operator-Stichprobe unter erneuter Compilerlast:
TOP-to-CHOP 5,69 ms, Vorschau-Instanzdaten 1,98 ms, Maske 0,57 ms.
Die Render-TOPs der Vorschau und Bibliothek kochten in diesem Fenster nicht:
ihre alten hohen cpuCookTime-Werte waren kein Beleg aktueller Belastung.

Die Datei cook-profile-loopback.json ist KEIN FPS-Abnahmelauf: zusätzliche
Instrumentierung und ein versehentlicher Speicherversuch während des Tests
verursachten einen Bridge-Stall. Die Output-off-Prüfung verweigerte das Speichern
korrekt; der Worker beendete später mit idle_watchdog und Schwarzabschluss.
Temporäre Profiling-Callbacks wurden vollständig wiederhergestellt.

Loopbacktests laufen ausschließlich auf 127.0.0.1:16454. Sie belegen den echten
TD-Produktions-/Pack-/UDP-Pfad, aber keine Controller- oder optische LED-Bildrate.
Firmwarelasttests und GICO-Kameratest liefern dafür getrennte Nachweise.

## Weitere Diagnose und Taktung

Perform-Mode-Vergleich nach Cacheoptimierungen: 28,800 FPS über 45 s.
Mit zusätzlichem Show-Idle-Fastpath, pausierten Compilern und vorübergehend
beendetem OneDrive-Hauptprogramm: 28,908 FPS über 120 s; keine Worker-Drops,
keine Fehler, 3.469 vollständige UDP-Batches. OneDrive.Sync.Service blieb
aktiv. OneDrive-Hauptprogramm wurde anschließend wieder gestartet und geprüft.
Die Ausgabe ist damit weiterhin nicht als stabile 30 FPS abgenommen.

Ein optionaler, separat zu prüfender Modus entkoppelt den Sendetakt:
TD bereitet mit bis zu doppelter Zielrate vor, der Worker hält nur das neueste
vollständige Bild bis zum nächsten phasenfesten Ausgabeslot. Er wiederholt
keine alten Bilder, wenn keine neue Produktion vorliegt. Bewusst ersetzte,
noch nicht gesendete Bilder zählen als stale; das ist keine UDP-Verlustmessung.
Der Modus ist standardmäßig ausgeschaltet, bis seine native Abnahme erfolgt.
