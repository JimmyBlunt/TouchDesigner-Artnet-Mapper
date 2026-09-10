# Scan-Workflows: Umsetzung und Abnahme, 10.09.2026

## Ergebnis und tatsächliche Grenze

Die bearbeitbaren Softwarepunkte sind umgesetzt und im laufenden TouchDesigner-Projekt geprüft. Der gespeicherte Einstieg ist `PixelblazeMapper_SCAN_COMPLETE_20260910.1.toe`. Der vorherige Meilenstein `PixelblazeMapper_SCAN_UX_20260910.1.toe` bleibt bestehen.

Eine vollständige optische Hardwareabnahme ist **nicht abgeschlossen**: Die Kamera funktioniert, erkennt im aktuellen Aufbau beim gezielten LED-Test jedoch keine LEDs. Es wurden keine Messwerte erfunden und keine fehlgeschlagene Aufnahme übernommen. Weitere Kameraperspektiven, verifizierte Referenzpunkte und Montageabstände erfordern den tatsächlichen Aufbau.

## Erledigte Punkte

| Bereich | Umsetzung | Prüfung |
|---|---|---|
| Scan-Bibliothek | Suche, 2D/3D-Filter, Seiten, Mehrfachauswahl, Punktvorschau und Orbit; kurze lesbare Dateinamen mit vollständigem Herkunftspfad im Detail | Native Beschriftung tatsächlich mit der Maus angeklickt; Auswahl und Vorschau ändern sich korrekt |
| Wiederverwenden von Aufnahmen | Originale LED-Identitäten und Aufnahmeparameter wiederherstellen; umgezogene Dateien ohne Veränderung ihrer Ursprungsmetadaten nutzen | Identitäts-, Mischungs-, Pfad- und Wiederaufnahmetests |
| Fehlende/schwache LEDs | Expliziter neuer Teilumfang aus geprüften Ansichten; vorhandene Ansichten bleiben erhalten | Auswahltests, keine automatische Umnummerierung |
| Registrierung/Teilersatz | Bekannte LED-Paare, mindestens drei geeignete Fit-Anker und ein unabhängiger Prüfanker; nur ausdrücklich angenommene LEDs ersetzen; Undo und archivierter Beleg | Rotation, Maßstab, Verschiebung, Degeneration, falsche/stale Identitäten, Dateimanipulation, Abbruch und Undo |
| Freie Quellenplätze | Volle Ausgabegröße bleibt erhalten; gemeinsame Schwarzmaske für freie/fehlende Plätze in Live-, Kalibrierungs- und nativen Ausgaben | 3.744 Plätze, 53 freie Stellen 1643–1695; reale Übernahme und Rücknahme im Projekt |
| 3D und Material-UV | Explizit KEEP EXISTING MATERIAL UV oder PROJECT UV; beliebige physische XYZ bei unveränderter vorhandener UV-Zuordnung | Native Übernahme mit unveränderten UVs; vollständige Rücknahme bestätigt |
| Router-Regressionen | Veraltete Test-Doppel auf tatsächliche Controllerkarten-Entwürfe und Baselines umgestellt; Stopp-/Rollback-Tests erreichen wieder die reale Transaktion | Zuvor sieben Fehler beseitigt; keine ausgeblendeten Tests |
| Projektpfade | Aktive Scanpfade auf dieses Repository umgestellt; kopierte Dateien vorab byteweise geprüft; alte vorbereitete Pläne verworfen | Erneute 3D-Rekonstruktion ausschließlich mit Dateien im neuen Workspace |
| Bedienbarkeit | Lesbare helle Klickbeschriftungen, cyan Auswahl, grüne Hauptaktionen, amber Teilersatz, rote Stopps; kompakte ID-Bereiche | Native Screenshots `library.jpg`, `registration.jpg`, `scan-workflow.jpg` |

Details: [Bibliothek](LIBRARY_DE.md), [Registrierung](REGISTRATION_DE.md), [Sparse Apply](SPARSE_APPLY_DE.md), [Pfadmigration](PATHS_DE.md).

## Performance und zusätzliche Fehlerbehebungen

Der Ausgangsprofiler zeigte laufende Arbeit des alten ESP-Art-Net-Packers trotz ausgeschalteter Ausgabe. Nachfrageabhängige native Ausgabegates führen in diesem Zustand konstante Schwarzkanäle zu. Für aktive Packer erfolgt die Übertragung kanalweise statt Sample für Sample. Die alte ESP-Verarbeitung wurde mit unveränderter Rundung, Kanalreihenfolge, Begrenzung und 510-Byte-Universen vektorisiert.

Die unabhängige Prüfung fand eine falsche Großschreibung der ESP-RGB-Kanäle und einen Kalibrierungscache, der Änderungen der Quellenmaske nicht berücksichtigte. Beide Fehler sind behoben. Masken werden streng geprüft; ungültige Masken stoppen den Sender vor weiteren Paketen. Der Installer prüft vorab und stellt bei Fehlern Callbacktexte, Leitungen und vorhandene Gate-Einstellungen wieder her. Änderungen an alten Routing-Parametern oder DAT-Quellen machen vorbereitete Layoutpläne ungültig.

Die LED-Vorschau liest jede RGB-Spalte nur einmal und normalisiert in Float64 über NumPy. Koordinaten, Maskierung, animierte Ersatzdarstellung und Effekt-Simulation bleiben unverändert. Die Abdeckungsanzeige cached unveränderte Beobachtungsdateien, statt sie bei jedem neuen Capture-Status erneut einzulesen; geänderte Dateien werden erneut validiert. Datei- und Zeilengrenzen verhindern unbegrenztes Einlesen.

Native cProfile-Messung, jeweils acht Sekunden mit laufendem Effekt, sichtbarer Scan-UI und ausgeschalteter Ausgabe:

| Messgröße | Vorher | Nachher |
|---|---:|---:|
| Alter ESP-Packer im ausgeschalteten Zustand | 172 Aufrufe / 3,629 s | 0 Aufrufe |
| Vollständiger Preview-Callback pro Aufruf | 16,448 ms | 4,219 ms |
| Erfasste Python-Eigenzeit im Messfenster | 5,791 s | 2,757 s |

Der Profiler beeinflusst die Laufzeit; diese Werte sind keine garantierte Netzwerk-FPS oder Langzeitlast-Abnahme. Rohdaten stehen in `profile-before.json`, `profile-final.json` und `performance-comparison.json`. Ein ergänzender isolierter Normalisierungsbenchmark und die Paritätsprüfungen sind in [PREVIEW_PERFORMANCE_DE.md](PREVIEW_PERFORMANCE_DE.md) beschrieben.

## Native Funktions- und Hardwareprüfung

- Kamera 0: 640×480, angeforderte/tatsächliche Belichtung −10, 93 Frames bis zum kontrollierten Beenden, Bereinigung bestätigt.
- Controller 10.0.0.249: Konfiguration 203 LEDs, aktiver Ausgang ab Wire-Universum 120; drei Quellen-IDs 0,101,202 mit maximal 7 % geprüft (Plan verwendet den bestehenden Wert).
- Controllerzähler nach dem Test: 336 Pakete, 168 vollständige Frames, keine unvollständigen Frames, keine gemeldeten Drops, Sequenzfehler oder Timeouts.
- Kameraergebnis: 0/3 erkannt. Die Aufnahme endet als Fehler ohne akzeptierte Ansicht. Blackout-Pakete wurden gesendet; optische Dunkelheit wurde nicht bestätigt. Worker beendet, Scan-Lease freigegeben, alle Projektausgänge aus. Die vorherige Sitzung wurde wiederhergestellt.
- 10.0.0.244 und 10.0.0.251 antworteten beim begrenzten HTTP-Test nicht. Daraus allein folgt keine vollständige Diagnose ihrer Stromversorgung oder Firmware. Es wurden keine Controllerparameter verändert.
- Die zehn vorhandenen Ansichten wurden danach erneut offline rekonstruiert: 203/203 LEDs, keine fehlenden IDs, 4,8 s, Exitcode 0, weiterhin Roh-SfM-Koordinaten ohne behauptete Registrierung. Das Ergebnis liegt unter `Scans/back_test_249_20260909_001708/result-ffcb4375-f65b-4988-b8e2-47ee03da9ea4`.
- Native Sparse-Übernahme und Rücknahme: Mapping, UVs, Controller-/Segmenttabellen und Entwurf anschließend hashgleich. Während der 3D-Übernahme blieben die Material-UVs gleich. Keine Ausgabe aktiviert.
- Speichern/erneutes Öffnen: Mapping-, UV-, Router-, Show-, Material-, Browser- und Undo-Zustände stimmen überein; keine Operator- oder Picklefehler; Sender aus und nach Wiederöffnung null gesendete Pakete. Nachweis `roundtrip.json`.

## Versionskontrolle und Reproduktion

Arbeitszweig: `codex/scan-completion-performance-20260910`, Ausgangspunkt `3fc90cf`. Die drei Agenten bearbeiteten Bibliothek/UX, Registrierung sowie Sparse Apply/Pfade; anschließend erfolgten unabhängige Ausgabeprüfung und Integration. Commits und Dateihashes in `artifact-manifest.json` verbinden Code, Daten und TOE.

Die bereits vorhandenen Änderungen an `.gitignore`, `README.md` und `PixelblazeMapper_WORKING_PHASE2_EFFECTS_CORE.toe` wurden nicht überschrieben oder in diesen Änderungsstand aufgenommen. Der schon unversioniert vorhandene Native-DMX-Gate-Helfer samt Tests wird als geprüfte Abhängigkeit mit aufgenommen; seine ältere Gate-Integration im Router wird erhalten. Die überschaubaren vorhandenen Scan-JSON/CSV-Daten werden zur Nachvollziehbarkeit ebenfalls versioniert; historische Manifeste bleiben bytegleich, ihre ursprünglichen Pfade dienen weiter als Herkunftsbeleg.

Installationswerkzeuge: `python -m tools.install_completion_output`, `python -m tools.install_scan_completion`. Die einmalige aktive Pfadumstellung ist in `tools.relocate_completion_workspace` nachvollziehbar. Alle Installer verlangen ruhende Ausgaben; sie starten keine Hardware. Historische Profil-/Scanberichte sind Belege, keine Steuerbefehle.

Verifikation mit der vorhandenen MariMapper-Python-Umgebung:

```powershell
& 'C:/Users/jbhtz/AppData/Roaming/uv/tools/marimapper/Scripts/python.exe' -m unittest discover -s tests -q
```

Finaler Workspace-Lauf: **995 Tests, 994 bestanden, ein OS-abhängiger Symlink-Test übersprungen; keine Fehler.** `full-tests-first.txt` und `full-tests-second.txt` dokumentieren die zwischenzeitlich gefundenen Probleme; entscheidend ist `full-tests-final.txt`. Zusätzliche Git-Snapshot-Prüfung wird separat dokumentiert.

## Verbleibend am physischen Aufbau

Kamerasicht, Fokus/Belichtung am tatsächlich leuchtenden Aufbau, geeignete zusätzliche Perspektiven, verifizierte räumliche Referenzen/Montagepositionen sowie ein optischer Gesamtscan und längerer Hardwarelasttest sind noch erforderlich. Der fehlende optische Nachweis wurde nicht als Softwareerfolg ausgegeben. Der neue Teilersatzdialog verweigert beim vorhandenen Rohscan ohne passende Referenzanker zu Recht eine behauptete geprüfte Ausrichtung.

## Git-Export: zusätzlich gefundene Abhängigkeiten

Der erste reine Git-Export von `c52591e` scheiterte an bisher unversionierten Alt-Abhängigkeiten (963 Tests, sieben Fehler und ein fehlgeschlagener Test). Die Scan- und TOE-Dateihashes stimmten bereits vollständig. Der unveränderte Fehlerbeleg bleibt in `git-snapshot-first-tests.txt` und `git-snapshot-first-check.json`.

Gezielt aufgenommen wurden die vollständige Seitenrekonstruktion samt unterem Seitenhelfer, räumlicher Lookup-Builder, vier erforderliche Mapping-/Messdateien sowie passende Tests. Für die Reproduktion wurden außerdem die frühere Mapping-Sicherung, Vorbereitungs-/Exportwerkzeuge und die historische Lookup-Dokumentation aufgenommen. Die dortigen Hardware-Abnahmehinweise beschreiben den älteren Lookup-Meilenstein; die heutige Software- und Hardwareabnahme ist oben getrennt dokumentiert. Der Lookup-Builder bestimmt seinen Datenpfad nun relativ zum Repository. JSON-Belege behalten ihre Originalbytes. `adopted-dependencies.json` dokumentiert Umfang und Hashes.

Die unabhängige Rekonstruktion aus Sicherung und Rohmessung ergibt exakt alle 3.744 kanonischen Koordinaten; 21 fehlende und drei verworfene Messungen ergeben 24 geschätzte Positionen. Übrige unversionierte Altdateien bleiben außerhalb dieses Änderungsstands.
