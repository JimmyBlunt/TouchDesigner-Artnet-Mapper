# P0 Routing – Implementierung und Offlineabnahme

07.09.2026. Nur Quelldateien und Tests geändert; keine Liveinstallation, kein Start, kein UDP-Verkehr, keine `.toe`-Speicherung, kein Commit durch diesen Teilauftrag. Die installierte Sechserkonfiguration und Port4-Zuordnung wurden nicht verändert.

## Red → Green

Zuerst `tests/test_routing_apply_regression.py` angelegt und auf dem alten Stand ausgeführt: **3 Tests fehlgeschlagen**. Reproduziert wurden Teilmutation bei ungültiger APA-IP, Teilmutation bei ungültiger Kalibrierung und doppelte Universekonversion.

Nach Implementierung: **63 Tests bestanden (2,931 s)** über Routing-Apply, multi_controller, GICO-Modell/UI, Kalibrierung und Echtzeitpacker. Zusätzliche Verhaltenstests prüfen erfolgreichen Apply mit 24 reservierten Universen, Rollback nach Builderexception, blockierend zurückkehrenden Builder, Stopfehler, vollständige Routervalidierung, falsche GICO-Flags, Quellüberlauf, UI-Startuniversen 1/2/7, Nicht-WS-Erhaltung und GICO-Draft-Rollback. Die Suite verwendet Mock-DATs und extrahierte echte Runtimequellen; kein TD-/Socketbetrieb.

Abschließender P0-Härtungslauf vor Beginn der Topologieerweiterung: **72 Tests bestanden (2,509 s)** einschließlich OutputSummary. Zusätzlich geprüft: vertauschte Controllerreihenfolge, einmaliger Fehler mitten im Tabellenschreiben, expliziter Recoveryfehler und GICO-Universeüberlauf. Die UI-Initialisierung verwendet jetzt ebenfalls Controlleridentität statt Position; die Wiederherstellung prüft auch eine ohne Exception zurückkehrende blockierte Validierung.

## Umgesetzt

- Gemeinsamer `routing_transaction.py`: vollständiges Routermodell aus getrennten Kandidatentabellen validieren, Stop aller Ausgänge bestätigen, erst dann Tabellen übernehmen und Builder ausführen.
- Ungültiger Kandidat: keine Tabellenmutation und keine Senderzustandsänderung. Ein Safe Apply, der einen gültigen Commit beginnt, lässt bei Erfolg oder Fehler die Ausgabe aus. Automatisches Wiederanlaufen ist ausdrücklich ausgeschlossen.
- Fehler nach Commitbeginn: ursprüngliche Controller-/Segment-/Kalibrier-/Draft-/Validation-/Summarytabellen wiederherstellen, alten abgeleiteten Aufbau erneut herstellen, bei fehlgeschlagener Wiederherstellung deutlich `RECOVERY REQUIRED` melden. Kein falsches `APPLIED SAFELY` nach Routervalidationfehler.
- Router-Felder werden anhand der Controlleridentität WS2812_NODE/APA102_ESP in Kandidaten geändert, nicht mehr anhand von Tabellenzeilenpositionen. Alle übrigen Konfigurationswerte – insbesondere 24 Universen und bestehende Port4-Segmente – bleiben erhalten.
- GICO validiert Quellenende und Art-Net-Blockende; Enabled/Reverse akzeptieren nur 0/1 statt jedes nichtnull Integer.
- GICO konvertiert `FIRST UI UNIVERSE` genau einmal zu zero-based Wireuniversen. Shared Sender verwendet den Routerwert unverändert. Vorhandener Start0 bleibt Start0; keine Migration oder Änderung geladener Tabellen vorgenommen.

## Grenzen und anschließende Abnahme

Die Transaktion macht Tabellenänderungen auf einer einzelnen TD-Ausführung konsistent; sie ist keine Datenbank und kann zerstörte TD-Operatoren bei einem fundamentalen Builderfehler nicht garantieren. Das wird als Recoveryfehler ausgewiesen und die Ausgabe bleibt aus. Vor UIinstallation sind bestehende geladene Runtimequellen und Tabellen zu sichern; danach zuerst ausschließlich Sender-OFF-/Tabellen-/Idempotenztests. Echte Apply-/Start-/Hardwaretests separat beaufsichtigen.

Nicht in diesem P0 enthalten: neue generische Controller-/Portoberfläche, voneinander unabhängige Controllerraten, ArtSync-Unterstützung, Draft-/Live-Konfliktanzeige oder umfassende Status-/Hilfetextüberarbeitung.

## Erweiterung für mehrere Controller und unterschiedliche Portkapazitäten

Ein generischer Entwurf sollte drei Ebenen getrennt führen:

1. Controlleridentität und Netzwerk: Ziel-IP, Interface, Protokoll, Rate, globale Wirebasis.
2. Hardwareprofil/Fähigkeiten: `fixed_equal_blocks` versus `independent_port_blocks`, Anzahl Ports, unterstützte Kanal-/Pixelmodelle, maximale Universen und explizite Basiszählweise.
3. Portentwurf: stabile Port-ID, aktiviert, Label, Universenzahl bzw. daraus abgeleitete Kapazität, Quellsegmente, Reverse/Farbreihenfolge; daraus wird ein validiertes kanonisches Routermodell kompiliert.

Für das aktuell bekannte **GICO-Profil gilt global gleiche Universenzahl pro physischem Port**. Unterschiedliche Universenzahlen dürfen nicht als erfolgreiche GICO-Hardwarekonfiguration angeboten werden. Entweder übernimmt ein gemeinsamer Wert alle Ports oder eine heterogene Eingabe wird mit einer profilbezogenen Erklärung blockiert. Andere Controller dürfen bei belegter Hardwarefähigkeit unabhängige Portblöcke bekommen. Die generische Ebene kann unterschiedliche Kapazitäten darstellen, ohne dem GICO Eigenschaften zu erfinden.

Die nächste Stufe sollte zunächst als reiner Adapter/Compiler mit Tests entstehen: GICO 6/6/6/6 bleibt identisch; generischer Controller 4/2/6 erzeugt kumulative, nicht überlappende Blöcke; GICO 4/2/6 wird zurückgewiesen; neue Controller überschreiben keine fremden Controller-/Segmentzeilen. Erst danach eine gemeinsame nichttechnische Portoberfläche statt weiterer paralleler Editoren.
