# P1 – Show Control: deterministischer Slot-Wechsel und ehrlicher Status

Stand: 2026-09-07. Dieser Teil wurde ausschließlich offline bearbeitet und getestet. Keine API-Schreibzugriffe, Live-Installation, Art-Net-Pakete, Projekt-Speicherung oder Commits durch diesen Agenten.

## Änderungen

- `show_sequencer.py`: Jeder A/B-Slot erhält eine eigene Animationszeit. Der eingehende Slot startet mit Beginn der Überblendung; beim automatischen Cue-Wechsel bleibt seine bereits sichtbare Vorlaufzeit erhalten. Pause friert beide Zeiten ein. Manuelle Sprünge, Stop und Seek beginnen ausdrücklich eine neue Cue-Phase. Die Übergaberichtung B→A und Loop sind mitgetestet.
- `build_show_sequencer.py`: Die Adapter übergeben diese Slot-Zeit an den Renderer. Eine eigene, nur bei Änderungen geschriebene `coordinate_request`-Tabelle trennt UV-Modus/Hybridanteil von laufend veränderter Animationszeit. Der Builder erhält vorhandenes Show-JSON und Transportzustand; bei einer neuen Python-Klasse nach Modul-Reload wird der gespeicherte Zustand einschließlich Slot und Phasenoffset wiederhergestellt. Loop/Blackout sind physisch momentary und semantisch toggelnd, sodass jeder Klick wirkt. Panel-Callbacks werden während der Reparatur deaktiviert.
- `show_renderer.py`: Globale, panel-lokale und hybride Koordinaten werden pro Slot aus demselben kanonischen Lookup ausgewählt. Alle Übergangsmasken ergeben an Mix=0 exakt A und an Mix=1 exakt B; Randpunkte wie u=0 oder der Mittelpunkt einer radialen Blende lecken nicht mehr den anderen Slot.
- `integrate_live_show.py`: A und B haben eigene UV-Script-CHOPs vor ihren Samplern; der globale Material-Player-Modus beeinflusst sie nicht. Die Übergangsmaske verwendet globale kanonische UVs. Auch die TOP-Vorschau hat exakte Endpunkte. Unbekannte Effekte werden mit Cue-/Effektkennung abgewiesen statt als Fluid Noise gerendert. Shader-Parameter und Texte werden nur bei Änderungen geschrieben; Statusfeedback ist auf 4 Hz begrenzt. Der Status liest den tatsächlichen Sender und unterscheidet OUTPUT OFF, LIVE SENDING, OTHER SOURCE SENDING, SENDER ERROR und STATUS UNKNOWN. Bei fehlendem Sender lautet der Zustandswert `unknown`, nicht irreführend 0. Die Installation erhält die gewählte visuelle Quelle und schaltet keinen Sender ein.

## Regressionsevidenz

Vor der Korrektur reproduzierten neue Tests die fehlenden Slot-Uhren und die fehlerhaften Wipe-/Radial-Endpunkte. Nach der Korrektur bestehen 46 gezielte Show-Tests (0,097 s):

```
python -B -m unittest tests.test_show_p1_regression tests.test_show_sequencer tests.test_show_renderer tests.test_show_control_dialog_regression tests.test_live_show_integration -q
```

Enthalten sind ausgeführte generierte Python-Callbacks mit portablen DAT-/Parameter-Mocks, nicht nur Textvergleiche: A/B-UVs, falsche Lookup-Reihenfolge, Runtime-Restore, wiederholte Loop-/Blackout-Befehle, fehlender Effekt sowie tatsächlicher Senderstatus und fehlender Sender. Außerdem automatische Handoffs bei 30/60 fps, B→A/Loop, manuelles GO, Cut, Pause und exakte Masken.

## Live-Abnahme durch den Hauptagenten

1. Sender weiterhin ausgeschaltet lassen; Show-JSON, Source, Transport, Cue, Zeit, Loop und Blackout vorab festhalten.
2. Die Python-Module `pixelblaze_mapper.show_sequencer` und `pixelblaze_mapper.show_renderer` neu laden; anschließend `build_show_sequencer.py` und `integrate_live_show.py` in dieser Reihenfolge ausführen. Dies ist eine Installationsempfehlung, keine hier ausgeführte Aktion.
3. Vorherige visuelle Quelle und Transportzustand müssen erhalten bleiben; Projektfehler müssen leer und Sender/Paketzähler unverändert OFF/0 bleiben.
4. In der Vorschau globalen Cue A gegen panel-lokalen Cue B blenden und den globalen Material-Player-Modus ändern: die Slot-Koordinaten dürfen sich dadurch nicht ändern. Prüfen, dass die UV-CHOPs nach Lookup-/Modusänderungen erneut cooken, nicht unnötig auf jedem Animationsframe.
5. Automatische Übergabe ohne Phasensprung prüfen; Loop und Blackout jeweils viermal klicken und wechselnden Zustand beobachten. Endpunkte der Wipe-/Radial-Blenden prüfen. Keine Hardware-Ausgabe dafür erforderlich.
6. FPS/Cook-Zeiten vor/nach Installation unter derselben sichtbaren Quelle vergleichen. Die Offline-Tests ersetzen keine TD-/GPU-/UI-Performanceprüfung.

## Grenzen / bewusst nicht erweitert

- Der Show-Maskenvertrag bleibt bei den bisherigen 3.744 kanonischen LEDs und vier bekannten Gruppen. Die neue dynamische Scene-Topologie benötigt anschließend einen eigenen Adapter, bevor zusätzliche Fixtures in Show-Masken unterstützt werden; keine stillschweigende Behauptung dynamischer Unterstützung.
- Cue-Helligkeit bleibt das bisherige gemeinsame Gain des ausgehenden Cues. Eine Überblendung zweier unabhängiger Cue-Gains ist hier nicht hinzugefügt.
- Transport verwendet weiterhin den vorhandenen maximalen 1-s-Delta je Render-Frame. Änderungen an Zeitbasis/Überlastpolitik sind nicht Teil dieses Checkpoints.
- Core-Katalog-Effekte werden unterstützt; importierte Materialien werden nicht automatisch als Show-Effekte ausgeführt.
- Keine TD-GPU-Kompilierung, native Klickprüfung oder optische Live-Abnahme durch diese Offline-Tests. Router-Statuscode bleibt während der separaten Performance-Messung des Hauptagenten unverändert.

## Nachprüfung: kurze echte Klicks

Auf Anforderung des Hauptagenten wurden die Button-Bindings in Router, GICO und Show auf den direkten Panel-Wert `lselect` umgestellt. Sie verwendeten bereits Panel Execute, jedoch zuvor `state`; ein CHOP-Sampler war in diesen Dialogen nicht vorhanden. Der Topologie-Editor verwendet denselben GICO-Helper und übernimmt die Korrektur. Nur die steigende Flanke löst aus; Release, While-On/Off und ValueChange werden beim Builder-Rebuild ausdrücklich deaktiviert. Somit stammen Aktionen von der linken Auswahlflanke und nicht von einem später gecookten Momentary-Button-Zustand.

Neue Datei `tests/test_dialog_press_binding.py`: drei Prüfungen für alle vier Binding-Stellen, gemeinsamen Topologie-Helper und die ausgeführte Callback-Dispatchfolge zweier kurzer Press/Release-Paare ohne Render-/CHOP-Sample. Vorher zwei rote Tests, danach 87 gezielte Routing-/Topologie-/Show-Tests grün (0,437 s). Der portable Event-Harness beweist die Konfiguration/Callback-Zuordnung, nicht die native TD-Ereigniszustellung; reale Kurz-Klick-Abnahme erfolgt durch den Hauptagenten. Keine Live-Schreibzugriffe für diese Nachprüfung.
