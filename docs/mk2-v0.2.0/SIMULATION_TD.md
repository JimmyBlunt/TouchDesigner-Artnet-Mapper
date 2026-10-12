# Verbundsimulation: Material Player, Show und Aufnahme

Stand: 12. Oktober 2026. Bezug: `docs/MK2_CONTROL_SPEC_DE.md`.

## Ausführung und Umfang

```powershell
python -m unittest tests.test_mk2_recording_scenarios tests.test_mk2_td -v
```

Ergebnis dieses Laufs: **33 Tests erfolgreich**, davon **12 durchgehende
Bedienabläufe** in `tests/test_mk2_recording_scenarios.py`. Keine erwarteten
Fehlschläge oder übersprungenen Tests. Der bestehende Adaptertest enthält
zusätzlich 21 gezielte Funktions- und Regressionstests.

Die Verbundsimulation führt diese Kette aus:

`Controller-Ereignis → Workflow → Host → erzeugte TD-Callbacks → Recorder →
Automationsdaten → erzeugter Uniform-Schreiber`.

Es laufen die tatsächlichen Implementierungen von `start_recording`,
`_apply('add_material')`, `_arm`, `_take`, `stop_recording`, `_trim_new_cue`,
`_remove_cue`, den MK2-Hooks und der Wiedergabe. Simuliert werden ausschließlich
die TD-Operatoren/COMP-Speicherung, Transportanbindung, externe Zeit und
Shader-Aktivierung. Die Show-, Parameter- und Automationsvalidierung bleibt aktiv.
Die Bedienung gelangt über dieselben normalisierten Tasten-/Encoder-Ereignisse
wie die USB-Anbindung in die echte Zustandsmaschine.

## Abgedeckte Abläufe

| Bezug | Durchgehend geprüfter Ablauf | Ergebnis |
|---|---|---|
| G01, G02, M03 | STEP → Show → gesperrter Material-Browser → STEP zurück → BROWSE → Radwahl → Radklick lädt → externer Source-Wechsel; aktive Browserauswahl und laufende Show-Cue bleiben getrennt | bestanden |
| S06, S07, S09, G04, G05 | Encoder im normalen Showbetrieb ohne Wirkung; REC-Druck allein erzeugt keine Cue; Loslassen startet neue Cue; Master Speed, Scale, native Farbe und Bool ändern; REC beendet und kürzt Cue; gespeicherte Werte erreichen die echten Shader-Uniforms | bestanden |
| S08 | REC+ERASE und ERASE+REC starten jeweils Aufnahme im vorhandenen Clip; neue Kurve ersetzt nur den gedrehten Parameter; unberührte Kurven und deren Bearbeitungsebenen bleiben erhalten | bestanden |
| S09 | Clipwechsel während einer laufenden Take beendet die Aufnahme; die Kurven gehören weiter zum ursprünglichen Clip; keine Werte gelangen in den nächsten Clip | bestanden |
| S07 | Neue Cue ohne Reglerbewegung wird entfernt; vorhandene Show-Automation bleibt unverändert | bestanden |
| S04 | Radbearbeitung ändert Clipdauer, Übergangsart und Übergangsdauer sofort, bevor der Bearbeitungsmodus verlassen wird | bestanden |
| S10 | PLAY, vorheriger/nächster Clip und RESTART funktionieren; während Aufnahme werden diese Aktionen sowie STEP, BROWSE und SCENE blockiert; nach REC-Stopp wieder verfügbar | bestanden |
| S09, Fehlerbehandlung | Fehler bei der Aufnahmeabtastung beendet die Aufnahme mit Meldung und erhält unberührte Automationskurven | bestanden |
| G08, Fehlerbehandlung | Teilweise angewendetes Preset schlägt fehl: Material, Werte, Auswahl, Identitätscache und Show-Source werden wiederhergestellt | bestanden |
| Zusatzrobustheit | Erneutes Ausführen des Editor-DAT während Aufnahme erhält den COMP-gespeicherten Recorder und setzt dieselbe Kurve fort | bestanden |
| Zusatzrobustheit | Vollständige Neuerzeugung des MK2-Host während Overdub erhält Take-Art, Live-Werte, berührte Parameter und ursprüngliche Kurven; Stopp ersetzt weiterhin nur berührte Kurven | bestanden |
| Zusatzrobustheit | Vollständige Neuerzeugung des MK2-Host während neuer Cue erhält native Vektoraufnahme und spätere Cue-Kürzung; Speicherung wird nach Abschluss entfernt | bestanden |

## Durch die Simulation gefundener und behobener Fehler

Der Recorder lag bereits dauerhaft im COMP, der ergänzende MK2-Aufnahmekontext
jedoch nur in der Python-Host-Instanz. Eine vollständige Neuerzeugung dieses
Host während REC+ERASE verlor damit die Liste berührter Parameter und die
Sicherung der vorherigen Kurven. Ein anschließender Stopp hätte unberührte
Automation entfernen können.

`mk2_td.Host` speichert diesen Kontext jetzt zusätzlich unter
`mk2_recording_context_v1` im gleichen COMP: Take-Art, Cue-ID, Ausgangsautomation,
Startwerte, berührte Parameter, aktuelle Live-Werte und Material-ID. Die Daten
enthalten ausschließlich primitive Werte. Ein neuer Host stellt sie nur bei
passender laufender Aufnahme/Cue wieder her. Nach erfolgreichem Abschluss wird
der Eintrag entfernt. Zwei getrennte Verbundtests prüfen Overdub und neue Cue.

## Kompatibilitätsprüfung am laufenden Projekt

Es erfolgte ausschließlich eine lesende Abfrage des Editor-DAT. Beide Hooks
waren genau einmal vorhanden (`MK2_EDITOR_V020`, `MK2_SOURCE_IDENTITY_V021`);
Start, Abtastung, Stopp, Uniform-Schreiber und Materialidentität waren vorhanden.
Zum Zeitpunkt dieser Abfrage lief keine Aufnahme. SHA-256 des gelesenen DAT:
`ce208dfa1c9ef70e3ac51729339116668da8e1ef18019e175c5a4dfad650b001`.

Die Simulation änderte weder Live-Materialien noch Source, Show, Aufnahme,
Projektdatei oder Hardware. Der neue Persistenzcode wurde hier nicht im
laufenden TouchDesigner neu geladen.

## Grenzen dieser Teilabnahme

- Die physische MK2, tatsächliche Tastenerkennung, USB-Verbindung, Displays und
  LED-Farben sind Gegenstand der separaten Hardwareprüfung.
- GPU-Kompilierung realer Materialpakete und sichtbare LED-Ausgabe werden hier
  nicht simuliert. Der Test prüft den Weg bis zu den tatsächlichen numerischen
  Shader-Uniform-Zuweisungen.
- Compile-Time-Defines und Event-Parameter sind weiter nicht aufnehmbar; native
  skalare Werte, Bool und Vektorkomponenten sind geprüft.
- Die vorhandene Show-Editor-Regel für neue Cues bleibt unverändert:
  `max(1, round(Aufnahmespanne + 0.5, 1))`. Beispiel: 2,25 Sekunden Take ergeben
  2,8 Sekunden Cue; die Simulation behauptet keine samplegenaue Kürzung.
- Importierte Intensität/Kontrast verwenden die vorhandene gemeinsame
  Nachbearbeitung; während Überblendungen betrifft sie das Mischbild.
- Die Tests prüfen Wiederherstellung beim Neuaufbau des Host/Editor-Moduls in
  derselben TD-Sitzung. Ein Absturz vor Speichern des Projekts oder ein echter
  Neustart des Rechners wird damit nicht als verlustfrei bestätigt.
