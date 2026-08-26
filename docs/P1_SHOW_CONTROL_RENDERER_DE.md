# P1 Show-Control: Live-Renderer-Vertrag

Stand: 26.08.2026

## Umgesetzt

- Die Show verwendet Schema-Version 2. Jeder Cue speichert Materialname,
  Presetname und den vollständigen Parametersatz: Speed, Scale, Width, Focus
  X/Y, Zoom, Gradient, Farben sowie alle übrigen Shaderparameter. Fehlende oder
  zusätzliche Parameter werden beim Laden abgewiesen.
- Der Live-Mixer verwendet `output_b_mix`. Dadurch ist Slot B auch nach dem
  Wechsel auf Cue 2 bei Transition-Fortschritt 0 tatsächlich der sichtbare
  Ausgangsslot.
- A und B werden getrennt an den kanonischen 3.744 UV-Positionen gesampelt.
  Die Zielmasken werden pro Slot und LED vor der Transition angewendet.
- Zulässige Zielgruppen sind ausschließlich `all`, `middle`, `upper`, `lower`
  und `rear`. Die Bereiche folgen dem freigegebenen Installationsvertrag:
  0–516, 517–785, 786–1183 und 1184–3743.
- Status und Richtung stammen aus `outgoing_slot`/`incoming_slot`. LOOP und
  BLACKOUT zeigen ihren Zustand im Button und im Statustext. BLACKOUT setzt den
  finalen Render-Gain auf null, ohne Transport oder LOOP zu verändern.
- Cue-Zeit statt `absTime` treibt die Materialzeit. PAUSE friert damit auch die
  sichtbare Show-Materialanimation ein.

## Sichere Anwendung

Die Builder aktivieren weder Art-Net noch einen Netzwerk-Ausgang und speichern
kein TouchDesigner-Projekt. Vor der Übernahme in Core 70 müssen zuerst die
Offline-Tests laufen. Anschließend sind Builder und visueller Live-Pfad im
geöffneten Projekt zu prüfen. Ein Test am LED-Aufbau bleibt beaufsichtigt.

## Offline-Abnahme

```text
python -m unittest tests.test_show_sequencer tests.test_show_renderer \
  tests.test_show_control_dialog_regression tests.test_live_show_integration -v
```

Die Suite prüft unter anderem Schema-Roundtrip, vollständige Presets, alle
Panelgrenzen, Maskierung beider Slots vor der Überblendung, wechselnde
A/B-Richtung, BLACKOUT und die netzwerksichere Builderbindung.

## Performance des LED-Mixers

Der Live-Callback ruft nicht mehr für jede der 3.744 LEDs einzeln Validierung,
Maskenaufbau und Mixfunktion auf. Zielmasken werden je Gruppenkombination
vorberechnet; Gewichte und Gains entstehen einmal pro Frame, anschließend wird
jeder RGB-Kanal in einem kompakten Durchlauf berechnet und blockweise in den
Script CHOP geschrieben.

Reproduzierbarer Offline-Benchmark:

```text
python tools/benchmark_show_renderer.py
Show renderer: 3744 LEDs | legacy 21.271 ms | bulk 1.708 ms | 12.45x
```

In zusätzlichen Messungen lagen alle sechs Übergänge zwischen 2,1 und 3,9 ms.
Die tatsächliche TouchDesigner-Cookzeit einschließlich TOP-to-CHOP-Sampling und
Channel-Übernahme bleibt Bestandteil der beaufsichtigten Core-70-Abnahme.
