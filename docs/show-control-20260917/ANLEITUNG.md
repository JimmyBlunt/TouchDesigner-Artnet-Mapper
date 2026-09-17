# Show Control – Anleitung

Stand 17.09.2026. Panel öffnen mit **Ctrl+Shift+8**.

---

## 1. Was das Panel zeigt

Ein Fenster, von oben nach unten:

```
┌─ SHOW EDITOR ─────────────────────────────────────────────┐
│ [Showname        ] LOOP  NEUE SHOW  SPEICHERN  LADEN  6 Cues│
│  #  NAME          EFFEKT      DAUER      ÜBERGANG   …      │  ← Kopfzeile
│ 01  Aurora Opening Aurora     18 s+3.5 s crossfade  …      │  ← Cue-Liste,
│ 02  Plasma Drift   Plasma     16 s+2.5 s dissolve   …      │    10 Zeilen
│ …                                                          │
│ <   Seite 1 / 1   >        Cue 01 von 6                    │
│ [+ AKTUELLES MATERIAL] [DUPLIZIEREN] [LÖSCHEN] [▲] [▼]     │
│ NAME          DAUER s   ÜBERGANG s  HELLIGKEIT             │
│ [___________] [____]    [____]      [____]   [ÜBERNEHMEN]  │
│ ÜBERGANG            KOORDINATEN      FARBVERLAUF           │
│ < crossfade      >  < global     >   < fire_ice        >   │
│ [AUFNAHME] [AUFNAHME LÖSCHEN]  Aufnahme: 2 Regler, 8.4 s   │
├─ TRANSPORT (war schon da) ─────────────────────────────────┤
│ PREV PLAY PAUSE STOP NEXT GO LOOP BLACKOUT                 │
└────────────────────────────────────────────────────────────┘
```

Die **hell hinterlegte Zeile** in der Liste ist die ausgewählte Cue. Alle Felder
und Menüs darunter beziehen sich immer auf genau diese eine Cue.

---

## 2. In fünf Schritten zur eigenen Show

1. **NEUE SHOW** – legt eine leere Show an.
2. Im **Material Browser (Ctrl+Shift+2)** ein Material aussuchen und die Regler
   so einstellen, wie es dir gefällt.
3. Zurück im Show-Panel: **+ AKTUELLES MATERIAL**. Das hängt genau diesen
   Zustand als neue Cue an – Effekt, Farbverlauf, Speed, alle Slider.
   Rechts neben den Knöpfen steht mit *„Aktuell: …"* immer, was gerade
   übernommen würde – ein Blick dorthin vor dem Klick spart Korrekturen.
4. Schritte 2 und 3 wiederholen, bis alle Bilder drin sind.
5. Pro Cue Dauer und Übergang setzen (siehe unten), dann **SPEICHERN** und
   **PLAY**.

Damit die Show auf die Wand kommt, muss im **Material Player (Ctrl+Shift+4)**
der Parameter `Source` auf **`show`** stehen. Auf `imported` läuft stattdessen
das einzelne Live-Material.

> **Eine Show spielt nur Core-Effekte.** Die 25 Effekte aus
> `effects/effects_manifest.json` (Aurora, Plasma, Fire, Matrix Rain …) lassen
> sich übernehmen, ein importiertes MadMapper-Material nicht. Der Knopf weist
> das ab und sagt es – täte er es nicht, entstünde eine Cue, die erst beim
> Abspielen scheitert. Importierte Materialien laufen weiterhin live über den
> Material Player, nur eben nicht im Show-Ablauf.

---

## 3. Cues bearbeiten

| Knopf | Wirkung |
|---|---|
| **+ AKTUELLES MATERIAL** | Hängt den aktuellen Zustand des Material Browsers als neue Cue an und wählt sie aus |
| **DUPLIZIEREN** | Kopie direkt hinter der Auswahl; nimmt eine vorhandene Aufnahme mit |
| **LÖSCHEN** | Entfernt die Cue samt ihrer Aufnahme (die letzte Cue lässt sich nicht löschen) |
| **NACH OBEN / NACH UNTEN** | Verschiebt die Cue im Ablauf |

**Felder** (Name, Dauer, Übergangsdauer, Helligkeit) werden erst mit
**ÜBERNEHMEN** wirksam – du kannst also alle vier ändern und einmal drücken.

**Menüs** (Übergang, Koordinaten, Farbverlauf) wirken sofort beim Klick auf
`<` oder `>`.

Zwei Kopplungen nimmt dir der Editor ab, weil sie sonst ungültige Shows
erzeugen:

- Wählst du `cut`, wird die Übergangsdauer auf 0 gesetzt. Wechselst du wieder
  weg, bekommt sie automatisch einen brauchbaren Wert.
- Machst du eine Cue kürzer als ihren Übergang, wird der Übergang mitgekürzt.
- Beim Wechsel des Farbverlaufs werden **beide** Farben mitgezogen.

Eine ungültige Eingabe wird abgewiesen und als Text neben der Cue-Nummer
angezeigt – die Show bleibt dabei unverändert.

---

## 4. Die 15 Übergänge

Der Übergang einer Cue beschreibt, wie sie in die **nächste** übergeht.

### Blenden – die ganze Fläche ändert sich gleichzeitig

| Name | Wirkung |
|---|---|
| `cut` | Harter Schnitt, keine Übergangsdauer |
| `crossfade` | Lineare Überblendung |
| `fade_black` | Blendet über Schwarz – alte Cue aus, neue auf |
| `burn` | Weiche, gefaserte Auflösung mit unscharfem Rand |

### Reveals – die neue Cue wandert über die Fläche

| Name | Wirkung |
|---|---|
| `dissolve` | Zufällige LEDs zuerst |
| `glitch` | Blockweise, mit Versatz |
| `wipe` | Wisch nach rechts |
| `wipe_left` | Wisch nach links |
| `wipe_up` | Wisch nach oben |
| `wipe_down` | Wisch nach unten |
| `radial` | Von der Mitte nach außen |
| `iris` | Von außen zur Mitte |
| `bars` | Senkrechte Lamellen |
| `checker` | Schachbrettfelder |
| `spiral` | Winkel-Sweep um die Mitte |

Die Reveals richten sich nach den **Weltkoordinaten der LEDs**, nicht nach dem
Bild – ein `wipe` läuft also wirklich über die Wand und nicht über eine Textur.

---

## 5. Koordinatenmodus

| Modus | Bedeutung |
|---|---|
| `global` | Der Effekt spannt sich über die ganze Installation |
| `panel_local` | Jedes Panel zeigt den Effekt für sich, alle gleich |
| `hybrid` | Mischung aus beidem |

Faustregel: große, ruhige Effekte wirken in `global`, kleinteilige Muster in
`panel_local`.

---

## 6. Aufnahmemodus

Eine Cue speichert **einen** Reglerstand. Die Aufnahme ergänzt, was ein Regler
**während** der Cue getan hat.

1. Cue in der Liste auswählen.
2. **AUFNAHME** drücken – der Knopf wird rot und zeigt „AUFNAHME LÄUFT".
3. Im Material Browser Regler bewegen, während die Show läuft.
4. **AUFNAHME LÄUFT** erneut drücken zum Beenden.

Danach steht rechts, wie viele Regler aufgezeichnet wurden und wie lang die
Aufnahme ist. Bei der Wiedergabe fährt die Cue diese Bewegung nach, zwischen
den Messpunkten linear interpoliert.

Details, die im Betrieb zählen:

- Aufgezeichnet wird **nur, was sich bewegt.** Ein nicht angefasster Regler
  kostet nichts.
- Die Zeitbasis ist die Cue-Zeit, nicht die Uhr. Eine Bewegung bei Sekunde 4
  passiert bei der Wiedergabe wieder bei Sekunde 4 der Cue.
- Vor der ersten und nach der letzten Messung wird der Wert **gehalten**, nicht
  extrapoliert.
- Aufnehmbar sind: Speed, Scale, Width, Focus X/Y, Zoom, Intensity, Contrast,
  Trail, Direction, Rotation, Effect-Transition, Hybrid-Mix, Density.
  Farbverlauf und Seed sind bewusst **nicht** dabei – die springen, statt zu
  fahren.
- **DUPLIZIEREN** nimmt die Aufnahme mit, **LÖSCHEN** wirft sie weg.
- **AUFNAHME LÖSCHEN** entfernt nur die Aufnahme der ausgewählten Cue.

---

## 7. Speichern und Laden

**SPEICHERN** legt zwei Dateien unter `shows/` ab, benannt nach dem Showtitel:

| Datei | Inhalt |
|---|---|
| `<name>.json` | Die Show: Cues, Dauern, Übergänge |
| `<name>.automation.json` | Die Aufnahmen, verknüpft über die Cue-ID |

**LADEN** liest die Show, deren Name im Titelfeld steht – Name eintippen, dann
LADEN. Eine fehlende Automations-Datei ist kein Fehler, die Show läuft dann
ohne Aufnahmen.

Die Trennung ist Absicht: das Show-Format ist streng validiert und bleibt
unverändert, damit ältere Shows weiter laufen.

---

## 8. Transport

| Knopf | Wirkung |
|---|---|
| PLAY / PAUSE / STOP | Ablauf steuern |
| PREV / NEXT | Eine Cue zurück oder vor |
| GO | Sofort in den nächsten Übergang |
| LOOP | Am Ende von vorn beginnen |
| BLACKOUT | Ausgabe schwarz, Ablauf läuft weiter |

---

## 9. Fallstricke

**Nach einer Bearbeitung steht der Transport auf PAUSE.** Jede Änderung baut
den Sequencer neu auf, und das Projekt weigert sich bewusst, eine Show danach
von allein weiterlaufen zu lassen. Einmal PLAY drücken.

**Die Show landet nur dann auf der Wand,** wenn der Material Player auf
`Source = show` steht. Sonst bearbeitest du eine Show, die niemand sieht.

**Helligkeit ist pro Cue.** Sie multipliziert sich mit der Controller-Helligkeit
und dem Panel-Gain aus `/project1/panel_brightness_config`. Wenn eine Cue zu
dunkel wirkt, kann es an allen dreien liegen.

**Wer `build_show_sequencer.py` neu ausführt,** muss danach auch
`build_show_editor.py` laufen lassen – der Basis-Builder setzt das Panel auf
seine ursprüngliche Höhe zurück.

---

## 10. Wo was liegt

| Sache | Ort |
|---|---|
| Panel | `/project1/show_control/control_panel` |
| Aktuelle Show | `/project1/show_control/show_json` |
| Aufnahmen | `/project1/show_control/automation_json` |
| Auswahl, Seite, Aufnahmestatus | `/project1/show_control/editor_state` |
| Editor-Logik | `/project1/show_control/editor_callbacks` |
| Transport-Logik | `/project1/show_control/callbacks` |
| Show-Dateien | `shows/` |

Quellcode: `pixelblaze_mapper/show_editor.py` (Bearbeitung),
`show_automation.py` (Aufnahmen), `show_sequencer.py` (Ablauf),
`show_renderer.py` (Übergänge auf den LEDs),
`build_show_editor.py` (Oberfläche).

Tests: `tests/test_show_editor.py`, `tests/test_show_automation.py`,
`tests/test_show_transitions.py` – zusammen 48 Stück.
