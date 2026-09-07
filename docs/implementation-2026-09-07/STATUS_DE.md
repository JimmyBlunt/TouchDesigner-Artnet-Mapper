# Umsetzungsstand und Abnahmen

Stand: 07.09.2026, laufender Implementierungsschritt. **Kein vollständiger Abschlussbericht.** Die historischen Auditberichte beschreiben den Ausgangsstand, nicht diese Änderungen.

**Aktueller geprüfter Stand:** `Backup/Implementation/PixelblazeMapper_20260907_PERFORMANCE_VERIFIED.1.toe`, erfolgreich gespeichert und tatsächlich neu geladen. Material-/Routingzustand und vollständige Layout-/Fixture-Historien erhalten; keine Speicher-/Operatorfehler. 583 Tests, OK (ein NumPy-Test übersprungen, separat im nativen Interpreter geprüft). Neue echte Maus-/Undo-Tests und byteidentischer optimierter Packer. Die letzte kurze Live-Messung liegt bei etwa 12,5 Bildern/s: **60 FPS sind nicht abgenommen**. Details und nächste Schritte: `PERFORMANCE_CHECKPOINT_DE.md` und `performance/roundtrip.json`.

**Speicher-Historie:** Die erste `P0P1_2D_CANDIDATE.1.toe` meldete echte PicklingErrors und ist keine freigegebene Sicherung. Der reparierte Rückfallstand `Backup/Implementation/PixelblazeMapper_20260907_STORAGE_VERIFIED.1.toe` bleibt erhalten. Details zur ursprünglichen Reparatur: `SAVE_REPAIR_DE.md` und `storage-repair/roundtrip-result.json`. Die übrigen Funktions-/Performanceabnahmen bleiben offen.

## Übersicht

| Bereich | Implementiert | Nachgewiesen | Noch offen |
|---|---|---|---|
| Routing / Controller-Ports | Vollständige Entwurfsprüfung, sichere Übernahme/Rollback, individuelle Portmodelle mit Hardwaregrenzen | Offline-Regression; Live-Build ohne gemeldete Fehler und ohne Senderstart | Neue Topologie-UI mit echten Eingaben durchprüfen; physische Controllerabnahme |
| Materialbibliothek | Direkte Klickereignisse, gecachte Katalogdaten, getrennte Detail-/Hover-/Produktionsshader | Echte kurze NEXT-Klicks bis Seite 6 und PREVIOUS zurück auf 5 | Weitere Filter-/Grenz-/Hover- und Importkombinationen |
| Materialbrowser | Auswahl und Übernahme getrennt; Material-ID statt Seitenposition; Native-Hydrierungsschutz; materialbezogene Intensität/Kontrast/Farbmodus | Echte Auswahl von Fractal Oil auf Seite 2, anschließendes Apply, aktive ID geprüft, Rückkehr aus Native Params ohne Seitenverlust | Vollständige Einzelparameter-Matrix aller importierten Shader |
| Materialausgabe | Expliziter Original-/Gradientmodus, Intensität 0 auch nach Einfärbung schwarz, getrennte Materialzustände | GPU-Auslesen des aktiven importierten Materials: Intensität 0 ergibt Max/Mean RGB 0; Kontrollwerte und Look anschließend wiederhergestellt | Langzeit-FPS bei gleicher Fenster-/Materiallast, Hardwareausgabe |
| Show | Korrigierte Slot-Zeitübergabe, getrennte A/B-UV, Endpunktmasken und tatsächlicher Senderstatus | Offline-Regression, Live-Build ohne gemeldete Fehler | Echte Show-Transport-/Übergangsabnahme |
| 3D / 2D | Unveränderliche Scans, Layoutentwurf, kumulativer Import/Export, unabhängige Fixture-Ausgabe und Material-UV, explizite Apply-/Revert-Grenze | Echte Mausverschiebung beider 2D-Flächen, Pfeiltaste und Undo mit unabhängigen Werten; tatsächliches 2D-Apply/Revert aller 3.744 LEDs und identische Wiederherstellungsprüfsumme | Weitere Rotations-/Skalierungs-/Import-Klickfälle; Controllerzuordnung zusammen mit Layoutänderung |
| Geführter Scan | Bereich-/Anker-/Sitzungsmodell, Planungsoberfläche, separater Offline-Worker | Nativer MariMapper-Offline-Lauf: 258 von 269 Punkten rekonstruiert, 11 fehlende IDs ausdrücklich gemeldet; Eingabedaten unverändert | Exklusive Kamera-/LED-Aufnahme, Registrierung/Qualitätsreview, überwachte Jobs und physischer Teilscan |

## Reproduzierbare Belege

- Gesamtsuite nach Speicherreparatur: `python -m unittest discover -s tests` → **558 Tests, OK**, 32,464 Sekunden. Zuvor 540 Tests; diese hatten die Klassenidentitätsfehler beim Speichern nicht abgedeckt.
- `install-p0.json`, `install-materials.json`, `install-show.json`, `install-layout.json`, `install-shortcuts.json`: Ergebnis der gezielten Live-Builds. Die Ausgabe war ausgeschaltet; diese Dateien sind kein Hardwaretest.
- `gpu-material-probe.json`: tatsächliche Pixelwerte aus `res1`, 512 × 512 RGBA. Intensität 0: maximale und mittlere RGB-Komponente exakt 0. Der erste Versuch lief wegen eines offenen Windows-Systemmenüs in einen Antwort-Timeout; nach Schließen wurde der wiederhergestellte Zustand geprüft und der Test erfolgreich wiederholt.
- `material-page2-click-test.json`: ausgewählte und aktive Material-ID sowie Wiederherstellung von Bubble Rings nach dem Test.
- `screenshots/library-page6.png`: echte Materialbibliothek auf Seite 6 von 20.
- `screenshots/native-fractal-oil.png`: Native-Ansicht des korrekt übernommenen Seite-2-Materials mit 33 Parametern, 16 Zeilenplätzen pro Seite.
- `live-layout-apply-probe.json`: tatsächliche 2D-Übernahme mit veränderten UV, unveränderten physischen Koordinaten und exakt geprüfter Wiederherstellung.
- `ui-layout-*.json` und `LIVE_2D_WORKFLOW_DE.md`: echte Maus-/Pfeiltasten-/Undo-Schritte und voneinander unabhängige Transformationen.
- `MARIMAPPER_NATIVE_SMOKE.md`: nativer Offline-Test mit tatsächlichen CSV-Aufnahmen; keine Kamera- oder LED-Ausgabe.
- `preview-freeze-live-evidence.json`: auf Materialseite 2 über 5,168 Sekunden keine Neuberechnung der 25 Core-Vorschauen + 25 Karten-TOPs und inaktiver Hover-/Detail-TOPs. Produktion weiterhin frei: 59 Neuberechnungen, circa 11,42/s. Das ist **keine** bestandene 60-FPS-Abnahme; Fensterlast und weitere Renderverbraucher bleiben zu untersuchen.

Die Klicktests unterscheiden gültige Klicks von Eingaben außerhalb des Buttons. Teilweise lagen Dialogfenster außerhalb des sichtbaren Desktops; sie wurden maximiert. Ein API-Parameterwechsel zählt nicht als Maustest. Bei erkannten parallelen Benutzereingaben wird neu beobachtet und nicht blind weitergeklickt.

## Neue Bedienwege

TouchDesigner muss den Tastaturfokus haben. Die neuen Buchstaben-Shortcuts L/C/G wurden mit echten Tastatureingaben geöffnet. Beim C-Test erschien zusätzlich TouchDesigners Meldung „1 node copied“: Das native Kopierverhalten wird offenbar nicht unterdrückt; dieser Fokus-/Shortcut-Konflikt bleibt offen. Die Ziffern wurden in diesem Schritt nicht vollständig neu getestet.

| Tasten | Ziel |
|---|---|
| Strg + Umschalt + L | 3D Layout + 2D Fixtures |
| Strg + Umschalt + C | Controller / Ports |
| Strg + Umschalt + G | Geführte Scanplanung |
| Strg + Umschalt + 9 | Übersicht mit OPEN-Buttons |

Die vorhandenen Ziffern-Shortcuts wurden nicht umbelegt. Der Materialbrowser übernimmt die markierte Karte erst mit **APPLY SELECTED**. **Zurück zu Materialien** schließt die Native-Ansicht.

## Was ausdrücklich nicht als fertig gilt

1. „ARM CAPTURE“ ist gesperrt, solange kein geprüfter exklusiver Kamera-/Routeradapter vorhanden ist. Die Oberfläche ist derzeit Scanplanung plus Offline-Rekonstruktionspfad, kein fertiger Live-Scanner.
2. Layout-Routingfelder sind Entwurfszuordnungen. Die aktive Layoutübernahme verlangt ausdrücklich das Beibehalten bestehender Routen. Neue LED-Anzahlen und neue Routen werden noch nicht in einer gemeinsamen Transaktion übernommen.
3. Ein grüner Offline-Test beweist weder sichtbare Hardwarewirkung noch stabile 60 FPS. Die Bildrate des TouchDesigner-Zeitgebers ist nicht die gemessene Material- oder Senderbildrate.
4. Die bisherigen Kamerapositionen, Panelindizes und Hardwarezuordnungen werden nicht anhand alter Chat-Aussagen neu geschätzt.
5. Keine pauschale Zusage von 100 % Fehlerfreiheit. Jede noch fehlende Abnahme bleibt sichtbar.

## Weiterführende Dokumentation

- `CONTROLLER_PORTS_DE.md`, `P0_ROUTING.md`
- `P1_SHOW_DE.md`, `MATERIAL_CACHE_PERFORMANCE.md`
- `../LAYOUT_SCENE_EDITOR_DE.md`, `../LAYOUT_SCENE_MODEL_DE.md`
- `FIXTURE_WORKFLOW.md`, `LAYOUT_ACTIVE_APPLY.md`
- `MARIMAPPER_INTEGRATION.md`

Der Ausgangszustand wurde vor der Installation separat als TOE-Checkpoint gesichert. Die ursprüngliche, bereits zuvor geänderte CORE-Projektdatei wird nicht ungeprüft überschrieben oder zusammen mit fremden Änderungen committed.

## Gesicherter Testkandidat und nächste Reihenfolge

Historische Datei: `Backup/Implementation/PixelblazeMapper_20260907_P0P1_2D_CANDIDATE.1.toe`. `saved-candidate.json` erfasste nur den Rückgabewert der Speicherfunktion und Operatorfehler, NICHT die nativen Speicherwarnungen. Die frühere Erfolgsaussage war deshalb falsch. Dieser Beleg bleibt zur Nachvollziehbarkeit unverändert archiviert.

Aktuell gespeichert und erneut geöffnet: `Backup/Implementation/PixelblazeMapper_20260907_STORAGE_VERIFIED.1.toe`. 15 Zustands-/Sicherheitsprüfungen im Roundtrip bestanden, alle 8 gespeicherten importierten Materialien mit 137 Parameterwerten erhalten, Sender OFF und keine Pakete gesendet. Keine allgemeine Produktionsfreigabe; ältere Dateien bleiben erhalten.

1. Performance unter kontrollierter Fensterlast weiter messen; Rückkehr auf Core-Seite und echtes Hover-Ein/Aus nach Preview-Freeze separat abnehmen. Native Shortcut-Nebenwirkung bei C klären.
2. Verbleibende Controller-/Show-/Layout-Eingabematrix durchgehen; kombinierte neue LED-Anzahl und Routenumstellung als gemeinsame Transaktion ergänzen, nicht still über die Entwurfsfelder ausgeben.
3. Kamera- und exklusiven LED-Aufnahmeadapter anbinden, reale Teilscans mit unabhängigen Prüfpunkten abnehmen. Der erfolgreiche Offline-Lauf alleine gibt keine Scanregistrierung frei.

Quelländerungen sind in getrennten Git-Commits für Routing/Show, Materialien und 2D/3D/Scanplanung gegliedert; Nachweise und der gespeicherte Testkandidat folgen separat. Bestehende fremde Arbeitskopieänderungen werden nicht mit aufgenommen.
