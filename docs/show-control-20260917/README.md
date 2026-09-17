# Show Control reaktiviert (17.09.2026)

## Was lief vorher

Die Show Control war vollständig gebaut, aber gestoppt: `transport = stopped`,
`blackout = 1`, geladen war die alte `demo_show.json` mit drei Cues. Die
Ausgabe hing nicht an ihr, weil der Umschalter auf der Live-Materialkette
stand.

## Der Umschalter

`/project1/show_live_sample_switch` (Switch CHOP) entscheidet, was auf die
LEDs geht:

| Eingang | Quelle |
|---|---|
| 0 | `/project1/topto1` – Live-Material (Browser / Player) |
| 1 | `/project1/show_led_renderer_out` – Show Sequencer |

Der Index ist ein Ausdruck:
`int(op('/project1/madmapper_player_controls').par.Source.eval() == 'show')`

Umgeschaltet wird also über **Material Player (Ctrl+Shift+4)**, Parameter
`Source`. Menü: `movie`, `materials`, `show`, `imported`. Vorher stand er auf
`imported`, jetzt auf `show`.

## Neue Show: "Transition Tour"

`shows/transition_tour.json`, 6 Cues, 93 s, Loop an. Sie fährt **alle sechs
Übergangstypen** der Reihe nach durch, damit man sie direkt vergleichen kann:

| # | Cue | Effekt | Gradient | Koordinaten | Dauer | Übergang danach |
|---|---|---|---|---|---|---|
| 1 | Aurora Opening | Aurora | ocean_blue | global | 18 s | crossfade 3.5 s |
| 2 | Plasma Drift | Plasma | acid_lime_blue | global | 16 s | dissolve 2.5 s |
| 3 | Ripple Rings | Ripple Rings | fire_ice | global | 16 s | wipe 3.0 s |
| 4 | Tunnel Pull | Tunnel | neon_cyan_magenta | hybrid | 15 s | radial 3.0 s |
| 5 | Matrix Rain | Matrix Rain | mono_white | panel_local | 14 s | glitch 2.0 s |
| 6 | Comet Tails | Comet Tails | amber_violet | panel_local | 14 s | cut |

`target_groups: all` – jede Cue läuft auf **allen** Flächen: Rückwand-Panels
1–8 und die drei Seitenflächen.

Die drei Koordinatenmodi sind bewusst gemischt: `global` spannt den Effekt über
die ganze Installation, `panel_local` wiederholt ihn pro Panel, `hybrid`
blendet zwischen beidem.

Vor dem Laden offline gegen `pixelblaze_mapper.show_sequencer` validiert
(`Show.from_dict`), nicht erst im laufenden Projekt.

## Live gegengeprüft

- Übergang mitgemessen: `progress 0.781`, `output_b_mix 0.781`, Slot A → B
- Cue-Fortschritt beobachtet: 0 → 2 → 4, Loop aktiv
- Alle Flächen bekommen Daten, gleichmäßig: Panel 7 0.137, Panel 8 0.127,
  Panel 6 0.136, Seite Mitte ≈ 0.13

## Ein Stolperstein

`cue_table` im Show-Control-COMP wird **nur vom Builder** geschrieben, nicht
beim Laden einer Show über `show_json`. Nach dem Laden zeigte sie noch die
Cues der alten Demo, während der Sequencer längst die neue Show fuhr – die
Tabelle ist reine Anzeige, hat mich aber beim Prüfen kurz in die Irre geführt.
Sie ist jetzt aus `show_json` nachgezogen. Wer künftig eine Show lädt, sollte
das mitmachen, sonst widersprechen sich Panel und Realität.

## Bedienung

Show Control: **Ctrl+Shift+8** (`/project1/show_control/control_panel`) –
PLAY, PAUSE, STOP, NEXT, PREVIOUS, GO, LOOP, BLACKOUT.

| Was ändern | Wo |
|---|---|
| Show wechseln | `show_json` DAT im Show-Control-COMP; `cue_table` nachziehen |
| Helligkeit einer Cue | Feld `brightness` je Cue (0…1), aktuell 0.22–0.25 |
| Zurück auf Live-Material | Material Player, `Source` zurück auf `imported` |

Gespeichert als `PixelblazeMapper_SHOW_TRANSITION_TOUR_20260917.toe`.
