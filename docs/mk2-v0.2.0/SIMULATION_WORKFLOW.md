# Verbundene MK2-Abläufe: Simulation und Abnahme

Stand: 12. Oktober 2026, Workflow-Version **0.2.1**. Bezug: [Bedienungsspezifikation](../MK2_CONTROL_SPEC_DE.md).

Diese zusätzliche Testsuite führt vollständige Bedienfolgen aus. Sie ergänzt die
isolierten Workflow-, Laufzeit-, Geräteprotokoll- und TouchDesigner-Adaptertests.
Sie verwendet keine geöffnete TouchDesigner-Datei und greift nicht auf USB zu.

## Was tatsächlich zusammen geprüft wird

Der Eingang besteht aus synthetischen **rohen HID-Berichten** im MK2-Format.
Produktionscode dekodiert die Berichte mit `ControlEdges` und `PadEdges`. Die
entstehenden Ereignisse laufen durch die echte Warteschlange des `Manager`, die
echte Zustandsmaschine, die Befehlsausführung und die erneute Kontextabfrage.
Der Produktionsrenderer erzeugt beide 256×64-Bilder; der Paketencoder erzeugt
daraus je acht vollständige 265-Byte-Berichte. Bilddaten müssen je nach Bedienung
und Wertänderung tatsächlich verschieden sein.

Dateispeicherung und erneutes Laden des Managers verwenden echte temporäre
JSON-Dateien. Die Uhr für den 20-Sekunden-Test wird gezielt vorgerückt, sodass
Grenzen exakt und ohne Wartezeit wiederholbar sind.

Der USB-Worker ist ein funktionsloses Testobjekt. Der Host bestätigt Zustands-
und Parameteränderungen im Speicher. Dieser Host simuliert **keine** echte
Shaderausführung und **keine** Automationskurven. Aussagen über Aufnahmeinhalte
und Wiedergabe stammen deshalb aus den separaten TouchDesigner-Adaptertests,
nicht aus diesem Hostmodell.

## Dauerhafte Szenarien und Anforderungsbezug

Datei: `tests/test_mk2_scenarios.py`, Klasse `ConnectedScenarios`.

| Szenario / Testname | Durchgehender Ablauf und geprüfte Wirkung | Anforderungen |
| --- | --- | --- |
| `test_material_browse_load_native_pages_and_encoder_images` | Aktive Grundanzeige → native Seite → Encoderänderung → Browser → Markieren ohne Laden → Raddruck lädt → Grundanzeige folgt tatsächlich bestätigtem Material. Parameter- und Materialbilddaten ändern sich. | G01–G03, G05–G06; M01–M04; B3 |
| `test_bank_assignment_confirmation_preset_select_delete_and_restart` | Gruppe D/Pad 6 → leeres Menü → Zuweisung abbrechen → bestätigen → inaktives Preset bearbeiten und speichern → Manager neu starten → Paddruck lädt gespeicherte Werte → Menü-Select → Delete abbrechen → Delete bestätigen → Neustart behält Löschung. Andere Bänke bleiben unverändert. | G07; M05–M08, M10; D1 |
| `test_edit_idle_clean_dirty_cancel_save_and_external_mode` | Unveränderter Entwurf bleibt bei 19,99 s offen und schließt bei 20 s → geänderter Entwurf setzt Frist bei Eingabe zurück → Save/Cancel bei 20 s → Cancel verwirft → neuer Entwurf wird bei externem Moduswechsel erhalten → REC und REC+ERASE bleiben bei offener Bestätigung gesperrt → bestätigtes Save speichert. Kein Live-Parameter wird durch den Entwurf geändert. | M08–M09; G01; Entwurfsschutz |
| `test_show_metadata_transport_focus_activity_and_inert_encoders` | STEP → Clipdauer sofort ändern → Übergangsmodus und Dauer sofort ändern → Gruppe/Pad fokussiert automatisierten Parameter → kleine Encoder bleiben wirkungslos → obere Taste stellt Übersicht wieder her → PLAY/NEXT/PREVIOUS/RESTART → Fortschrittsänderung verändert die Anzeige. | G01; S01–S06, S10; B3 |
| `test_both_recording_workflows_lock_transport_and_restore_encoder_policy` | REC halten und loslassen startet genau eine neue Cue → native Encoder werden wirksam → konkurrierende Modus-/Transportaktionen bleiben gesperrt → REC stoppt → Encoder wieder wirkungslos → REC+ERASE in beiden Druckreihenfolgen startet je genau eine Aufnahme im bestehenden Clip und erzeugt keine neue Cue. | S06–S10; A4; B2 |
| `test_failed_assignment_retry_load_failure_and_pressure_hold` | Speicherfehler behält alte Konfiguration → erneute Bestätigung gelingt → Ladefehler behält aktives Material und bleibt nach Pad-Loslassen sichtbar → nächste gültige Eingabe erholt sich → gehaltenes Pad lädt genau einmal. | G07–G08; M04, M07, M10; Fehlerbehandlung |
| `test_all_eight_banks_and_sixteen_physical_pad_positions_route_correctly` | Alle **128 Kombinationen** aus A–H und Pad 1–16 werden als Druckberichte eingespeist. Jede lädt genau die zugehörige Material-ID und ihre eindeutig unterscheidbaren Presetwerte. Anschließender Neustart behält die vollständige Konfiguration. | G07; M10; B1–B2; D1 |
| `test_all_eight_encoders_native_page_and_idle_noise_route_only_intended_parameter` | Ruheschwankungen lösen keine Befehle aus. Alle acht Encoder auf TD- und nativer Seite ändern jeweils ausschließlich den passenden Parameter. Beide Seiten rendern anschließend vollständig. | G03, G05; M02–M03; B1, B3 |

Alle acht Szenarien enthalten mehrere Zustands- und Wirkungsprüfungen. Ein
Testfall ist jeweils eine zusammenhängende Bedienfolge, kein einzelner Tastendruck.

## Durch die Simulation gefundener und abgesicherter Fehler

Ein fehlgeschlagener Pad-Ladevorgang blieb zunächst intern erfolglos, seine
Fehlermeldung wurde jedoch durch das unmittelbar folgende Loslassen des Pads
wieder gelöscht. Die Laufzeit meldet einen Hostfehler jetzt auch an die
Zustandsmaschine und hält ihn über neutrale Tastenfreigaben hinweg sichtbar.
Eine neue gültige Bedienaktion kann den Fehler zurücksetzen. Der Fehlerpfad,
die erhaltene Materialauswahl und die anschließende Erholung werden gemeinsam
im oben genannten Fehlerszenario geprüft.

Ein weiterer Randfall betraf REC bei offenem Pad-Entwurf: Nach einem externen
Wechsel in Show Mode konnte die Aufnahme beginnen, obwohl noch Save/Cancel
angezeigt wurde. Aufnahmebeginn verwendet jetzt denselben Entwurfsschutz wie
andere konkurrierende Aktionen. Das verbundene Szenario prüft REC und REC+ERASE
bei offener Bestätigung. Der ergänzende dauerhafte Workflow-Test
`test_recording_cannot_start_with_dirty_draft_confirmation_or_pending_save`
prüft zusätzlich das noch nicht bestätigte Dateispeichern und die erfolgreiche
Freigabe der Aufnahme nach dessen Abschluss.

## Wiederholen

Mit Python und Pillow aus der Projekt-Testumgebung:

```text
python -m unittest tests.test_mk2_scenarios -v
```

Ergebnis des gezielten Laufs: **8 Szenarien bestanden**. Für die vollständige
Abnahme zusätzlich die anderen `test_mk2*.py`- und Show-/Timeline-Testdateien
ausführen; die übergreifenden Laufzahlen stehen im Haupt-Abnahmeprotokoll.

## Grenzen und ausdrücklich offene Nachweise

- **H1/H2 bleiben physisch offen:** USB-Geräteverfügbarkeit, Treiber, reale
  Knopffarbe/Helligkeit, elektrische Padempfindlichkeit, fühlbare Encoderbedienung
  und tatsächlich sichtbare LCDs werden durch synthetische Berichte nicht belegt.
- Die konkreten acht TouchDesigner-Parameternamen und Wertebereiche (**G04/C1**)
  stammen aus dem echten Hostadapter und dessen separaten Tests. Diese Szenarien
  verwenden absichtlich einfache, eindeutig unterscheidbare Parameter-IDs.
- Echte Aufnahme-/Ersetzungslogik, Erhalt unberührter Automationskurven,
  Abspielen der aufgezeichneten Werte und Clipende (**C3/S08/S09**) benötigen die
  separaten Adapter-/Hooktests. Der Host in dieser Suite prüft nur die richtige
  Befehlsfolge und bestätigte Aufnahmemodi.
- Reale Vorschaugrafiken, Browser-Netzwerkfehler und Zugriffsprüfung liegen in
  den Vorschau-/Browsertests. Hier werden Bildaufbau, Anzeigewechsel und gültige
  Displaypakete mit Platzhalterbildern geprüft.
- Diese Simulation belegt keine vollständige Erschöpfung aller denkbaren
  Kombinationen. Sie prüft alle beschriebenen Hauptabläufe, sämtliche Bank-/Pad-
  Zuordnungspositionen und beide Encoderseiten; ergänzende Randfalltests bleiben
  Teil der Gesamtabnahme.
