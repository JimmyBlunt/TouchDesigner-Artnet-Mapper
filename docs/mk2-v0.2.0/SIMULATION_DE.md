# MK2 0.2.1 – Simulation aller beschriebenen Bedienabläufe

Stand: 12. Oktober 2026. **308 Tests bestanden**, ohne Fehler, erwartete
Fehlschläge oder übersprungene Tests. Laufzeit: 35,682 Sekunden. Die in der
[Spezifikation](../MK2_CONTROL_SPEC_DE.md) beschriebenen Hauptabläufe sind mit
verbundenen Simulationen und gezielten Regressionstests abgedeckt. Die physische
Geräteabnahme bleibt getrennt davon offen.

## Umfang und Ergebnisse

| Simulation | Ausführung und Nachweis |
|---|---|
| Material Mode | BROWSE, Radwahl und Laden; TD/native Parameterseiten; alle acht Encoder; keine Aktivierung durch reine Auswahl |
| Pad-Bänke | Alle 8 × 16 = 128 Positionen; Zuweisen mit Confirm/Cancel; Select, Edit und Delete; dauerhaftes Speichern und Wiederladen |
| Presetentwurf | Inaktive Bearbeitung; exakte 20-Sekunden-Grenze; Save/Cancel; externe Moduswechsel und konkurrierende Änderungen |
| Show Mode | STEP und externe Source-Wechsel; Fortschritt, Übergänge, sofortige Radbearbeitung, Parametergruppen/-auswahl; gesperrte Encoder außerhalb der Aufnahme |
| Aufnahme | REC für neue Cue; REC+ERASE in beiden Druckreihenfolgen; nur berührte Kurven ersetzen; unberührte Kurven erhalten; Bool, Vektor und Master Speed bis zum Shader-Uniform-Schreiber |
| Aufnahmeende | REC-Stopp, automatisches Ende, leere neue Cue, Abtastfehler, Modul- und Host-Neuaufbau während einer Take |
| Transport | PLAY, vorheriger/nächster Clip und RESTART; Konfliktsperren während Aufnahme |
| USB-Worker | Tatsächlicher Worker-Thread mit simuliertem HID-Gerät; vollständige LCD-/LED-Pakete, Verbindungsverlust, Wiederanschluss, gehaltene Tasten/Pads, Schreib- und Schließfehler |
| Darstellung | 48 Display-Grenzfallkombinationen, fehlende Bilder, leere Bibliothek, Wertebereiche, Fortschritt und Parameteranzeige |
| Dauerbetrieb | 3.750 reproduzierbare gemischte Bedienereignisse über fünf feste Zufallsfolgen; gültige Zustände, Indizes, Werte und persistente Konfiguration nach jedem Schritt |
| Bestehende Funktionen | Gesamte vorhandene Show-/Timeline-Regression einschließlich Speicherung, Interpolation, Schleifenbereich, MIDI, Vorschau und Zugriffsschutz |

Die 308 Testfälle enthalten auch die genannten Parameterkombinationen und
langen Bedienfolgen als Unterprüfungen. Die Zahl wird dadurch nicht künstlich
um jede einzelne simulierte Bewegung erhöht. 35 neue Testfälle ergänzen den
bisherigen Lauf mit 273 Tests.

## Gefundene und behobene Fehler

1. **REC nach USB-Unterbrechung:** Ein alter gedrückter REC-Zustand konnte beim
   späteren Loslassen eine Aufnahme starten. Verbindungsgrenzen verwerfen nun
   alte Eingaben und setzen Tastenzustände vor frischen Eingaben zurück.
2. **Fehler beim Schließen des USB-Geräts:** Ein Fehler nach Abziehen konnte den
   Worker beenden. Er bleibt jetzt im kontrollierten Wiederverbindungsablauf.
3. **Zu früh verschwundene Fehlermeldung:** Das Loslassen eines Pads löschte einen
   gerade entstandenen Ladefehler. Die Meldung bleibt jetzt bis zur nächsten
   bewussten Bedienaktion sichtbar, auch im Controller-Snapshot.
4. **Aufnahme mit offenem Presetdialog:** REC konnte trotz ungesichertem Entwurf
   oder ausstehender Speicherbestätigung starten. Diese Zustände sperren nun
   den Aufnahmebeginn.
5. **Verlorener Overdub-Kontext bei Host-Neuaufbau:** Der Recorder blieb erhalten,
   die ursprünglichen Kurven und berührten Parameter jedoch nicht. Dieser Kontext
   liegt nun im TD-COMP und wird bei passender laufender Take wiederhergestellt.

## Reproduzieren und Einzelergebnisse

```powershell
python tools/check_mk2_acceptance.py --json-report docs/mk2-v0.2.0/acceptance-simulation.json
```

Benötigt Python, die dokumentierten Controller-Abhängigkeiten sowie Node.js für
die JavaScript-Vorschaubildtests. Der Testlauf benötigt kein echtes USB-Gerät.
Der Runner behandelt übersprungene und erwartbar fehlgeschlagene Tests nicht
als vollständige Softwareabnahme.

- [Alle 308 Ergebnisse mit Testnamen und Laufzeiten](acceptance-simulation.json)
- [Workflow-Szenarien und Anforderungsmatrix](SIMULATION_WORKFLOW.md)
- [Aufnahme, Wiedergabe und TouchDesigner-Callbacks](SIMULATION_TD.md)
- [USB-, Display- und Wiederverbindungssimulation](SIMULATION_DEVICE.md)

## Gesicherter Stand und Grenzen

Code und dauerhafte Tests: Commit `fecde59`, Version **0.2.1**. Die getesteten
Korrekturen wurden anschließend in die laufende Anbindung geladen. Show-,
Automations- und importierte Cue-Daten blieben laut SHA-256 unverändert.
Die Simulation selbst verwendete ausschließlich isolierte Testdaten.
Gespeicherte Projektversion:
[PixelblazeMapper_Schrank-MK2-v0.2.1-20261012.toe](../../PixelblazeMapper_Schrank-MK2-v0.2.1-20261012.toe).
Die vor dem Speichern laufende Wiedergabe wurde anschließend fortgesetzt.

Die Tests führen die echten Programmteile bis zu Displaypaketen und numerischen
Shader-Zuweisungen aus. Sie simulieren die Geräte-, TD-Operator- und Zeitgrenzen.
Damit sind weder reale Tastenkontakte und LED-Helligkeit noch GPU-Ausgabe und
die tatsächliche optische Wirkung am Schrank bestätigt. H1/H2 bleiben offen;
es wird keine vollständig bestandene physische Geräteabnahme behauptet.

Eine USB-Unterbrechung verwirft ausstehende Tastenaktionen. Eine bereits laufende
Aufnahme bleibt beim Host und kann dort beziehungsweise nach Wiederanschluss
beendet werden. Die Wiederherstellung des Take-Kontexts ist innerhalb derselben
TD-Sitzung geprüft, nicht als Schutz vor ungespeichertem Rechnerabsturz.
