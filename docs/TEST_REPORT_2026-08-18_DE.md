# Abnahmebericht · 18. August 2026

## Ergebnis

| Ebene | Ergebnis |
|---|---:|
| Portable Unit-/Contract-Tests | 92/92 bestanden |
| TouchDesigner Gesamtbaum | 0 Fehler |
| GLSL-Materialien | 25/25 kompiliert und sichtbar |
| Materialkarten-Mausauswahl | 25/25 korrekte Auswahl |
| Koordinatenmodi | global / panel_local / hybrid unterschiedlich und stabil |
| Show-Übergänge | 6/6 gerendert und visuell verschieden |
| Controller-Packer | WS 4×510, APA 10×510 |
| Sicherer Netzwerktest | beide Ziele mit schwarzen Frames, danach OFF |
| Gespeicherter Endzustand | alle vier DMX-Ausgänge OFF |

## Exakte Abnahmetests

| ID | Eingabe / Aktion | Erwartet | Ergebnis |
|---|---|---|---|
| TC-01 | Effektkarten 0..24 jeweils `click()` | Source=materials, exakter Index | PASS 25/25 |
| TC-02 | Coordinate Mode global/panel/hybrid | drei verschiedene Renderbilder | PASS |
| TC-03 | Show t=17.0 / 18.5 / 20.0 | Progress 0 / 0.5 / Cuewechsel | PASS |
| TC-04 | cut/crossfade/dissolve/wipe/radial/glitch bei 0.5 | sechs nichtleere, unterschiedliche Bilder | PASS |
| TC-05 | WS-Packer | 4 Kanäle × 510 Samples | PASS |
| TC-06 | APA-Packer | 10 Kanäle × 510 Samples | PASS |
| TC-07 | ESP Slots 0..1535 | exakt 0 wegen 512-Pixel-Präfix | PASS |
| TC-08 | Universe 9 Slots 447..509 | exakt 0 Padding | PASS |
| TC-09 | IP `10.0.0.999` | Apply blockiert, gültige Tabelle bleibt | PASS |
| TC-10 | beide Controller Enabled, Brightness 0 | Packermin=max=0; Live ohne Nodefehler | PASS |
| TC-11 | All Outputs Off | beide neue + beide alte Outputs false | PASS |
| TC-12 | Projekt speichern/laden | `.43.toe` + stabiler Alias identisch | PASS |

## Reale Bildschirmbelege

- Ausgangszustand: `screenshots/01-baseline-led-preview.png`
- Materialbrowser: `screenshots/07-material-browser-25-effects.png`
- Controller-Editor: `screenshots/11-controller-editor-validated.png`
- Show-Steuerung: `screenshots/10-show-control-crossfade.png`
- Show-Crossfade: `screenshots/08-show-crossfade-50-percent.png`
- LED-Vorschau während der Show: `screenshots/09-led-preview-show-crossfade.png`

## Netzwerkbeobachtung

- `10.0.0.251` antwortete stabil auf ICMP.
- `10.0.0.244` antwortete mindestens einmal mit ca. 2 ms, zeigte aber im kurzen
  Test Paketverlust. Art-Net ist UDP und liefert keine Zustellbestätigung.
- Beide DMX-Outs wurden mit ausschließlich schwarzen Packerwerten aktiviert;
  ihre Cook-Zähler stiegen auf 10604 und beide Nodes blieben fehlerfrei.
- Danach wurden beide deaktiviert und die gespeicherten Defaults auf
  Helligkeit 0.02 / Enabled 0 zurückgesetzt.

Damit ist die Software- und Senderseite vollständig abgenommen. Die sichtbare
physische Zuordnung des neuen WS2812-Nodes `.244` bleibt beim nächsten Aufbau
per Pixel-Chase/MadMapper zu bestätigen; sie kann aus einem UDP-Test allein
nicht bewiesen werden.
