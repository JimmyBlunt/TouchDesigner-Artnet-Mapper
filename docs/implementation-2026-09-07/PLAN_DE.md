# Umsetzung nach dem Audit – Arbeits- und Abnahmeplan

Freigabe: Nutzerauftrag vom 07.09.2026. Ausgangspunkt: Audit `c006d18`, Formatkorrektur `3129216`. Dieser Plan ersetzt keine Testergebnisse.

## Reihenfolge und Arbeitsverteilung

1. **P0: sichere Konfiguration.** Gesamten Entwurf validieren, erst dann atomar übernehmen; Fehlerrollback und genau eine Umrechnung zwischen UI-Universe und Art-Net-Adresse. Routing-Agent implementiert und prüft; Hauptagent integriert und prüft die Bedienung.
2. **P1: verlässliche Materialien.** Auswahl/Vorschau/aktiv trennen; Native-Rollback und Befüllungsschutz; gleichwertige Intensitäts-/Kontrastwirkung; Original-/Gradientmodus mit Bestandsschutz; Library-Klicks und eindeutige Zustandsanzeigen.
3. **Mapping, Show, Oberfläche und Leistung.** Aktive Map vom Entwurf trennen, Show-Zeit/UV korrigieren, reproduzierbare Dialoge, Hilfe und messbare Laufzeitdiagnose. Anschließend Rebuild-/Bedienregression.

Parallel zu P0 werden die Datenmodelle der freigegebenen Erweiterungen vorbereitet. Sie werden erst nach der Sicherheitsgrundlage an den aktiven Ausgabeweg angeschlossen. Nur der Hauptagent bedient den gemeinsamen Desktop.

## Zusätzliche freigegebene Funktionen

| Erweiterung | Verbindliches Verhalten | Abnahme |
|---|---|---|
| Controller-/Port-/Universe-Editor | Controller und Ports als eigene Einträge; per-Port-Start und Kapazität; Hardwarefähigkeiten ausdrücklich unterscheiden; Entwurf/Validieren/Übernehmen | Mehrere Controller, ungleiche Portkapazitäten bei unterstützter Hardware, Konflikt-/Grenztests, keine Änderung bei ungültigem Entwurf |
| Kumulatives 3D-Layout | Verifizierte MariMapper-CSV und Pixelblaze-Koordinaten/JSON importieren; stabile LED-IDs; einzelne farbige Scanobjekte; Transformieren/Auswählen; undo/redo; Zuordnung zur Ausgabe getrennt von Raumposition | Import/Export-Roundtrip; append und gezieltes Ersetzen; keine stille Neunummerierung; Maus-/Tastaturbedienung; aktive Map bleibt bis Apply unverändert |
| Unabhängige 2D-Fixtures | Eigene Fläche für Fixture-Anordnung und eigene Fläche für Platzierung auf dem Material; pro Bereich getrennte Verschiebung, Drehung und Skalierung; ursprüngliche 3D-Daten bleiben erhalten | 2D-Layoutänderung verändert weder Materialausschnitt noch XYZ; UV-Änderung verändert weder Fixture-Anordnung noch XYZ; Bereichsauswahl, Speichern/Laden, Übernehmen/Rücknahme getrennt testen |
| Geführte vollständige/partielle Scans | MariMapper-Anbindung mit expliziter Geräte-/Bereichsauswahl, Scanplan, Prüfstatus und bestätigter Übernahme | Keine Kamera-/LED-Aktion beim Importieren eines Python-Moduls; bestehende Teilbereiche bleiben bei Teilscan erhalten; echte Aufnahme und Rekonstruktion getrennt von simulierten Ablauftests ausweisen |

Ein MariMapper-eigenes JSON-Sessionformat wird nicht erfunden: reine Koordinatenarrays sind als Pixelblaze-kompatible Daten zu behandeln. Skriptexporte werden beim Import nicht ungefragt ausgeführt.

## Festgelegte Schutzregeln

- Aktueller Hardware-Ausgangspunkt bleibt unverändert: GICO sechs Universen pro Port, vier verwendete Portblöcke. Die alte Diskussion über 517/524 ist kein Anlass für neue Indexverschiebungen.
- GICO-Geräte, die nur eine gemeinsame Portkapazität unterstützen, dürfen in der Oberfläche nicht als unabhängig programmierbar dargestellt werden. Nutzungsgröße und physische Reserve sind unterschiedliche Werte.
- Bestehende Dateien und fremde uncommittete Änderungen bleiben erhalten. Neue Arbeiten werden gezielt versioniert; keine pauschalen Git-Aufnahmen.
- Offline-Tests, Live-Parameterprüfung, echte Maustests und physische Hardwareabnahme werden getrennt protokolliert.
- Der Sender bleibt in dieser Entwicklungsphase aus. Physische Scan-/Ausgabetests benötigen einen ausdrücklich abgestimmten Testschritt.
- Neue Materialien: Originalfarben als Standard; bewusste Gradientwahl mit Stärke. Vorhandene Materialzustände behalten ihren bisherigen Look durch explizite Migration.
- Aktive Materialauswahl nur durch eine erkennbare Übernahmeaktion. Hover und Vorschau dürfen keine laufende Ausgabe ersetzen.

## Fortschritt und Abschluss

Alle zehn Minuten erfolgt ein belegtes Statusupdate. Jeder Arbeitsschritt dokumentiert geänderte Dateien, ausgeführte Tests, noch offene Live-/Hardwareabnahmen und bekannte Grenzen. Ein vorhandenes Datenmodell ist noch keine fertige Oberfläche; ein simulierter Scan ist keine erfolgreiche Rekonstruktion.

Abschlussbericht: Ergebnisse pro Dialog, verbesserte Bewertung, verbleibende Risiken und genaue Bedienwege. Kein pauschales Versprechen einer hundertprozentigen Fehlerfreiheit.
