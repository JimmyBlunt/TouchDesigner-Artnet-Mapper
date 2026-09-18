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

> **Beides geht: Core-Effekte und importierte Materialien.** Die 25 Effekte aus
> `effects/effects_manifest.json` (Aurora, Plasma, Fire …) ebenso wie jedes
> importierte MadMapper-Material. Für importierte Materialien gilt eine
> Besonderheit, siehe Abschnitt 6.

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

## 6. Importierte MadMapper-Materialien

Ein Core-Effekt ist eine Nummer in einem gemeinsamen Shader – alle 25 stecken in
derselben Datei. Ein importiertes Material ist dagegen ein **eigener Shader**.
Deshalb hat jeder der beiden Show-Slots einen zweiten Renderer bekommen, der bei
Bedarf den Shader des Materials lädt; ein Umschalter pro Slot entscheidet, wer
gerade spielt. Für dich ändert sich nichts an der Bedienung: Material im Browser
auswählen, **+ AKTUELLES MATERIAL** drücken.

Was dabei intern passiert und warum es dich betrifft:

- Die **Reglerwerte des Materials** werden pro Cue gespeichert, nicht pro
  Material. Du kannst dasselbe Material zweimal in einer Show verwenden und
  unterschiedlich einstellen.
- Die Werte landen beim Speichern in `<name>.materials.json`, analog zu den
  Aufnahmen.
- Beim **Starten** prüft die Show, ob jedes benutzte Material noch in der
  Bibliothek liegt. Fehlt eines, verweigert sie den Start und nennt die Cue –
  besser als ein schwarzes Panel mitten in der Show.
- Der Shader wird nur **neu geladen, wenn sich das Material ändert**, nicht pro
  Bild. Ein Wechsel kostet also einmal Kompilierzeit, danach läuft es normal.
- In der Cue-Liste steht der **Materialname**, nicht die Katalog-ID.

---

## 7. Aufnahmemodus

Eine Cue speichert **einen** Reglerstand. Die Aufnahme ergänzt, was ein Regler
**während** der Cue getan hat. Dafür gibt es zwei Knöpfe.

### AUFNAHME – für eine vorhandene Cue

1. Cue in der Liste auswählen.
2. **AUFNAHME** drücken. Zwei Dinge passieren gleichzeitig: die Show springt an
   den **Anfang dieser Cue** und spielt los, und der Knopf wird rot. **An deinen
   Reglern wird nichts verändert** – die Aufnahme beginnt genau in dem Zustand,
   den du gerade eingestellt hast.
3. Regler bewegen. Was du bewegst, ist **sofort auf der Wand zu sehen** – du
   nimmst nicht blind auf.
4. **AUFNAHME LÄUFT** erneut drücken zum Beenden. Die Meldung nennt, wie viele
   Regler und wie viele Sekunden gesichert wurden.

### AUFNAHME → NEUE CUE – für ein Material ohne vorhandene Cue

Wenn du einfach ein Material im Browser eingestellt hast und eine Bewegung
darauf aufnehmen willst, ohne vorher eine Cue anzulegen:

1. Material im Browser auswählen und einstellen.
2. **AUFNAHME → NEUE CUE** drücken. Es entsteht sofort eine neue Cue am Ende
   der Liste, die dieses Material spielt, und die Aufnahme läuft.
3. Regler bewegen, so lange du willst – bis zu **5 Minuten** am Stück. Solange
   die Aufnahme läuft, steht bei DAUER **AUFNAHME** und in der Liste
   **Aufnahme...** statt einer Zahl: die richtige Länge kennt noch niemand.
4. Denselben Knopf erneut drücken. Die Cue bekommt jetzt genau die **Länge
   deiner Aufnahme**, und die Bewegung hängt daran.

Wird dabei **nichts** bewegt, verschwindet die neue Cue wieder – sie war nur
das Gefäß für die Aufnahme. Früher blieb sie mit der vollen Reservelänge in der
Show stehen.

Danach im Material Player auf **SHOW** umschalten: die Cue spielt die
aufgenommene Bewegung ab.

### Was aufgezeichnet wird

| Cue-Art | Aufgezeichnete Regler |
|---|---|
| Core-Effekt | Die 14 Regler des Material Players: Speed, Scale, Width, Focus X/Y, Zoom, Intensity, Contrast, Trail, Direction, Rotation, Effect-Transition, Hybrid-Mix, Density |
| Importiertes Material | Dessen **eigene** Regler (`mat_zoom`, `mat_speed`, `mat_morph` …) |

Bei einem importierten Material sind es also genau die Regler, die du im
Browser auch tatsächlich anfasst. Core-Regler bleiben bei einer
importierten Cue außen vor: einen `mat_`-Regler anzufassen schiebt über den
Materialzustand auch die Core-Schieber ein Stück, und diese Spuren gehörten
niemandem. Nicht aufgezeichnet werden Farbverläufe,
Seed und mehrteilige Regler wie Farben – eine Automationsspur ist eine Zahl
über die Zeit, und eine Farbe in Komponenten zu zerlegen würde etwas
aufzeichnen, das du als einen Regler siehst.

### Warum die Player-Regler bei importiertem Material nichts aufnehmen

Das ist der häufigste Stolperstein. Bei einer **importierten** Cue rendert die
Show das Material mit dessen **eigenem Shader** – der Material Player liegt
dabei gar nicht im Signalweg:

- **Scale** wirkt nur in der Live-Ansicht (MATERIAL), nicht auf eine importierte Cue.
- **Intensity** ist im Show-Betrieb fest auf 1.0 – der Regler tut dort nichts.
- **Contrast** liegt als **globaler** Effekt hinter der ganzen Show, gehört also
  keiner einzelnen Cue und kann darum auch nicht für eine aufgenommen werden.

Dass sich in der MATERIAL-Ansicht trotzdem sichtbar etwas ändert, macht es so
verwirrend – auf der Wand einer laufenden Show passiert davon nichts.

**Also:** Bei importiertem Material die Regler des Materials selbst nehmen – im
Material Browser unter **NATIVE PARAMS** (`UV / Scale`, `Animation / Speed`,
`Brightness`, `Contrast`, `Saturation` …). Die nimmt die Aufnahme auf, und die
Show fährt sie auch wieder ab. Der Editor sagt das jetzt schon beim Start der
Aufnahme, und wenn eine Aufnahme leer bleibt, weil nur die Player-Regler bewegt
wurden, nennt die Meldung genau diesen Grund.

### Der Startzustand wird mitgenommen

Früher stellte die Aufnahme die Regler erst auf die gespeicherten Werte der Cue
zurück – das setzte das Material zurück, das du gerade eingestellt hattest.
Das tut sie nicht mehr. Stattdessen gilt:

- Die Aufnahme startet **aus dem aktuellen Zustand**. Was du vorher am Material
  gedreht hast, bleibt stehen und ist auf der Wand zu sehen.
- Beim Beenden wird dieser Startzustand **in die Cue geschrieben**. Regler, die
  du gar nicht angefasst hast, stehen bei der Wiedergabe also genau dort, wo sie
  bei der Aufnahme standen – auch ohne eigene Spur.
- Aufgezeichnet wird trotzdem nur, was sich bewegt: der Zustand kommt in die
  Cue, die Bewegung in die Aufnahme.

### Wenn die Aufnahme nicht startet

Die Aufnahme haengt an drei Dingen, und der Editor sagt jetzt jeweils, welches fehlt:

| Meldung | Was zu tun ist |
|---|---|
| Kein spielbares Material aktiv (show) | Der Material Player steht auf **SHOW**. Auf **MATERIAL** schalten, dann ist wieder ein Material aktiv, das man als Cue anlegen oder aufnehmen kann. |
| Cue 09 spielt "Crumpled" - dieses Material erst im Browser aktivieren | Eine importierte Cue wird mit **ihrem eigenen** Material aufgenommen. Es gibt nur einen Satz Regler, also muss im Browser genau dieses Material aktiv sein - sonst landen die Regler des falschen Materials in der Cue. |
| Aufnahme nicht moeglich - Cue 11 "..." hat kein Material | Eine Cue der Show zeigt auf ein Material, das es nicht mehr gibt. Der Transport verweigert dann die **ganze** Show. Diese Cue loeschen (oder das Material importieren), dann laeuft alles wieder. |
| Cue war zu Ende, bevor ein Regler bewegt wurde | Die Cue ist kuerzer als gedacht. **DAUER** hochsetzen oder **AUFNAHME -> NEUE CUE** nehmen, die hat kein Zeitlimit. |

**+ AKTUELLES MATERIAL** legt nur noch eine Cue an, wenn wirklich ein spielbares
Material aktiv ist. Frueher entstand sonst eine Cue ohne Material, die die Show
komplett blockierte. Rechts neben den Knoepfen steht immer, was gerade aktiv ist.

### Was die Farben sagen

| Element | Bedeutung |
|---|---|
| **MATERIAL / SHOW** im Material Player | Die laufende Seite ist **weiß mit dunkler Schrift** und trägt ein `*`, die andere bleibt dunkel. |
| **AUFNAHME** / **AUFNAHME → NEUE CUE** | Leuchtet **rot**, solange aufgenommen wird. |
| Cue-Zeile | Die ausgewählte Cue ist blau hinterlegt. |

(Ein TouchDesigner-Button zeichnet sich nicht aus seiner eigenen Hintergrundfarbe,
sondern aus seinem inneren `text`-Knoten. Deshalb sahen vorher alle Knöpfe gleich
grau aus, obwohl im Code Farben standen.)

### Sonstiges

Die Aufnahme für eine **vorhandene** Cue endet von selbst, wenn die Cue zu Ende ist – die Meldung sagt
dann „(Cue zu Ende)". Eine Aufnahme ist damit immer genau eine Cue lang; was du
danach am Regler machst, gehört schon zur nächsten Cue und wird nicht
mitgeschrieben.

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
- **DUPLIZIEREN** nimmt die Aufnahme mit, **LÖSCHEN** wirft sie weg.
- **AUFNAHME LÖSCHEN** entfernt nur die Aufnahme der ausgewählten Cue.

Warum Aufnahme die Show selbst startet: die Zeitmarken sind **Cue-Zeit**. Steht
der Transport, steht diese Uhr, alle Messpunkte landen auf derselben Sekunde und
die Aufnahme bleibt leer. Genau das sah früher aus wie „kein Regler bewegt".
Bleibt eine Aufnahme leer, sagt die Meldung jetzt, woran es lag:

| Meldung | Bedeutung |
|---|---|
| kein Regler bewegt | Es wurde wirklich nichts angefasst |
| die Show lief nicht, die Cue-Zeit stand still | Der Transport lief nicht mit |
| die Bewegung war zu kurz | Zu wenige Messpunkte für eine Kurve |

---

## 8. Speichern und Laden

**SPEICHERN** legt zwei Dateien unter `shows/` ab, benannt nach dem Showtitel:

| Datei | Inhalt |
|---|---|
| `<name>.json` | Die Show: Cues, Dauern, Übergänge |
| `<name>.automation.json` | Die Aufnahmen, verknüpft über die Cue-ID |
| `<name>.materials.json` | Reglerwerte importierter Materialien, je Cue |

**LADEN** liest die Show, deren Name im Titelfeld steht – Name eintippen, dann
LADEN. Eine fehlende Automations-Datei ist kein Fehler, die Show läuft dann
ohne Aufnahmen.

Die Trennung ist Absicht: das Show-Format ist streng validiert und bleibt
unverändert, damit ältere Shows weiter laufen.

---

## 9. Transport

| Knopf | Wirkung |
|---|---|
| PLAY / PAUSE / STOP | Ablauf steuern |
| PREV / NEXT | Eine Cue zurück oder vor |
| GO | Sofort in den nächsten Übergang |
| LOOP | Am Ende von vorn beginnen |
| BLACKOUT | Ausgabe schwarz, Ablauf läuft weiter |

---

## 10. Fallstricke

**Nach einer Bearbeitung steht der Transport auf PAUSE.** Jede Änderung baut
den Sequencer neu auf, und das Projekt weigert sich bewusst, eine Show danach
von allein weiterlaufen zu lassen. Einmal PLAY drücken.

**Die Show landet nur dann auf der Wand,** wenn im Material Player (Ctrl+Shift+4)
der Knopf **SHOW** leuchtet. Der zweite Knopf, **MATERIAL**, schaltet zurück auf
das einzeln eingestellte Material. Sonst bearbeitest du eine Show, die niemand
sieht.

**Helligkeit ist pro Cue.** Sie multipliziert sich mit der Controller-Helligkeit
und dem Panel-Gain aus `/project1/panel_brightness_config`. Wenn eine Cue zu
dunkel wirkt, kann es an allen dreien liegen.

**Wer `build_show_sequencer.py` neu ausführt,** muss danach auch
`build_show_editor.py` laufen lassen – der Basis-Builder setzt das Panel auf
seine ursprüngliche Höhe zurück.

---

## 11. Wo was liegt

| Sache | Ort |
|---|---|
| Panel | `/project1/show_control/control_panel` |
| Aktuelle Show | `/project1/show_control/show_json` |
| Aufnahmen | `/project1/show_control/automation_json` |
| Werte importierter Materialien | `/project1/show_control/imported_json` |
| Renderer je Slot | `slot_a_player` (Core) / `slot_a_import` (Import) / `slot_a_mux` |
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
