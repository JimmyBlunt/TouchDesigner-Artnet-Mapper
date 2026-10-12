# MK2 0.2.0 – Implementierung und Abnahme

Nachfolgender Stand: [Simulation aller beschriebenen Abläufe mit Version 0.2.1](SIMULATION_DE.md),
308 erfolgreiche Tests und fünf zusätzliche Fehlerkorrekturen. Dieses Dokument
bewahrt die ursprüngliche 0.2.0-Abnahme.

Stand: 12. Oktober 2026. Die Bedienung ist in TouchDesigner integriert. Die
Softwareprüfungen und USB-Übertragung sind nachgewiesen; die vollständige
Bedienungsabnahme am physischen MK2 ist noch offen.

## Aufgaben und Umsetzung

Die verbindlichen Anforderungen und Testgruppen stehen in
[MK2_CONTROL_SPEC_DE.md](../MK2_CONTROL_SPEC_DE.md).

| Bereich | Zuständig | Ergebnis |
|---|---|---|
| A | Agent mk2_workflow | Material/Show-Zustände, Navigation, acht Pad-Bänke, Presetentwürfe, Bestätigungen und Aufnahmegesten implementiert |
| B | Agent mk2_hardware | HID-Eingaben, monochrome Displays, Vorschaubilder, Parameterbalken und LED-Zustände implementiert |
| C | Agent mk2_touchdesigner | Echte Parameter, laufender Clip, Transport, neue Cue und Overdub im vorhandenen Clip integriert |
| D | Hauptagent | Browser-Bankwahl, Schema-2-Persistenz, Migration, Live-Integration, Testlauf und getrennte Commits |

REC + ERASE ersetzt die Kurven der während der Aufnahme berührten Parameter.
Nicht berührte Kurven bleiben erhalten. REC erzeugt eine neue Cue. Die Gruppen
im Show-Modus wählen Achterblöcke, Pads 1–8 den einzelnen Parameter.

## Dauerhafte Tests

```powershell
python tools/check_mk2_acceptance.py --json-report docs/mk2-v0.2.0/acceptance.json
```

Das maschinenlesbare Ergebnis steht in [acceptance.json](acceptance.json).
Abschließender Lauf: **273 Tests, 0 Fehler, 0 Fehlschläge, 0 übersprungene Tests**.
Der Lauf umfasst MK2-Tests, vorhandene Show-/Timeline-Regressionen und die
Live-Show-Integration mit Test-Doubles. Er steuert keine reale Aufnahme an.
Zusätzliche lokal vorhandene `test_show*.py` werden ebenfalls mit ausgeführt.

## Live-Prüfungen

- Der HID-Worker meldet „MK2 verbunden · Displays übertragen“. Beide Displaybilder
  sind auch im Browser sichtbar. Das bestätigt USB-Schreibvorgänge, ersetzt aber
  keine optische Prüfung des Controllers.
- Browser-Bankwahl A → B → A geprüft. B zeigte 16 leere Plätze, A wieder acht
  bestehende Zuweisungen. Materialvorschauen und 607 Katalogeinträge sind verfügbar.
- Vorhandene Konfiguration wurde in Schema 2 mit acht Gruppen migriert.
- Nach der ersten Integration waren Show-, Automations- und importierte Cue-Daten
  per SHA-256 identisch mit den vor der Integration gesicherten Daten.
- Das beobachtete Leerlaufzittern von Encoder 4 wird durch Quantisierung und
  Hysterese unterdrückt. Eine aufgezeichnete reale Rohwertfolge sowie langsame
  Drehungen und der Zählerumlauf sind Regressionstests.
- Der Nutzertest meldete zunächst keine Reaktion bei BROWSE/STEP. Ursache war
  TouchDesigners Platzhalter `show:default`, der als Material-ID behandelt wurde.
  Die Korrektur trennt Modus und Materialidentität. Der erneute physische Test
  ist noch offen. Die Modusanzeige folgt der Ausgangsquelle, nicht einem im
  Hintergrund laufenden Show-Transport.
- Der erste TD-Parameter ist auf dem kompakten Display als **Speed** beschriftet;
  sein vollständiger Name bleibt **Master speed**.
- Vorschaubilder wiederholen einen fehlgeschlagenen Ladevorgang einmal und zeigen
  bei erneutem Fehler „Kein Bild“. Vier JavaScript-Funktionstests prüfen das Verhalten.
- Gespeicherter Projektstand:
  `PixelblazeMapper_Schrank-MK2-v0.2.0-20261012.toe` (13.796.956 Bytes).
  Nach dem Speichern wurde die zuvor laufende Wiedergabe fortgesetzt. Die Quelle
  blieb `imported`; die drei Dokument-Prüfsummen waren weiterhin unverändert.

## Grenzen der Abnahme

H1/H2 aus der Spezifikation sind noch nicht vollständig bestanden. Insbesondere
echte Tastenbetätigung, Reglerzuordnung, LED-Farben und eine tatsächliche
Aufnahme mit anschließender Wiedergabe benötigen den Gerätetest.

Die LCDs sind monochrom; die oberen Tasten und Transporttasten haben feste
Farben. Helligkeit, Muster und Blinken ersetzen dort die gewünschten RGB-Farben.
Native Compile-Time-Schalter sind nur im Material Mode editierbar, Ereignis-
Parameter sind nicht editierbar. Intensity/Contrast importierter Materialien
wirken während einer Überblendung auf das gemeinsame Mischbild.

## Versionshistorie

| Commit | Inhalt |
|---|---|
| `20c9b3b` | Spezifikation und Abnahmekriterien |
| `2660f05` | Bedienzustände, Presets und Workflowtests |
| `5d38754` | HID-Steuerung, Displays und Hardwaretests |
| `c67b61c` | TouchDesigner-Parameter, Aufnahme und persistente Bänke |
| `66d4b3c` | Browser-Bankwahl, Dokumentation und Testprogramm |
| `a3f51df` | Filter gegen das am Gerät beobachtete Encoderzittern |
| `970a215` | Show-Platzhalter, Rücknahme bei Ladefehlern und Speed-Beschriftung |
| `545a136` | Vorschau-Wiederholung und barrierefreier Fehlerzustand |

Die Commits wurden lokal erstellt. Andere vorhandene Arbeitsänderungen bleiben
außerhalb dieser Commits. Bibliotheken unter `.controller-runtime`, persönliche
Pad-Konfigurationen und binäre TouchDesigner-Projekte liegen weiterhin lokal.
