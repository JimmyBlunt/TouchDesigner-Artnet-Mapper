# Panel 7 – Scan ausgerichtet und in den Layout-Entwurf übernommen (17.09.2026)

## Ausgangslage

Der erste Scan (Session `ff733d6e…`) war unbrauchbar – siehe
`docs/panel7-scan-20260917/SCAN_DIAGNOSE.md`. Der zweite Scan
(Session `capture-e46efe62-37d3-47ae-9bcf-b4cabfbd42bc`, 5 Ansichten,
2701 Beobachtungen) ist sauber:

| Größe | Wert |
|---|---|
| Rekonstruiert | **549 / 549** |
| Reprojektionsfehler | Median 0.507, p90 0.877, max 1.849 |
| Planarität (PC3/PC2) | **0.0121** |
| Hüllrechteck in der Ebene | 2.601 x 2.548 → **1.02 : 1**, also quadratisch |
| Abdeckung | alle 549 LEDs in ≥ 3 Ansichten gesehen |

## Orientierung

Der Betrachter hat die gemessene Form bestätigt, mit dem Hinweis auf eine
Drehung um 180°. Daraus die drei Blöcke des Strips:

| Block | Scan-Index | Lage im Panel |
|---|---|---|
| Streifen | 0 – 240 | volle Breite, **oben** |
| Stufen | 241 – 355 | Mitte, treppenförmig |
| Gefüllter Block | 356 – 548 | **linke untere Ecke** |

`tools/prepare_panel7_20260917.py` erzwingt genau diese Lage über zwei
geometrische Bedingungen (Block unterhalb des Streifens, Block weiter links
als die Stufen) und wählt unter den zulässigen Drehungen die mit der
kleinsten Hüllfläche. Damit ist auch die Spiegelung eindeutig aufgelöst.

## Platzierung

Slot: vierte Reihe links – **unter Panel 5, links neben Panel 8**.

| | Wert |
|---|---|
| Ziel-Mitte | X 0.300 / Y 1.000 / Z 0.600 |
| Bounds | X 0.2173…0.3827, Z 0.5156…0.6844 |
| Envelope | .16875 (dieselbe 30-cm-Referenz wie Panel 2–6, 8) |
| Transform | reine Ähnlichkeit (Skalierung 0.064883, keine Scherung) |
| Source-Offset | 7646 → Quellen 7646…8194 |
| `expected_count` | 7646 → **8195** |
| Zurückgezogene Template-LEDs | 2976 – 3231 (256 Stück aus „Active snapshot") |
| Route | `PANEL8_251`, Port 2 |

Geprüft: alle übrigen Objekte und deren Weltkoordinaten unverändert,
keine überlappenden Source-Slots, keine Netzwerk-Fehler in `/project1`.

## Status

**Nur Entwurf.** Live-Ausgabe und `segment_config` sind unverändert; das
Segment `PORT_PANEL8_251_2` zeigt weiterhin auf die alten Template-Quellen
2976…3524. Der Schritt „active integration" (analog
`tools/integrate_panel6_20260914.py`) steht noch aus.

## Dateien

- `panel7_layout_front.png` – Frontansicht der Rückwand nach der Platzierung
- `panel7-placement.png` – Detail + Übersicht aus dem prepare-Lauf
- `draft-plan.json` – Kennzahlen und Transform
- `draft-prepared.json` – vorbereitetes Dokument
- `panel7-world.csv` – Weltkoordinaten je LED
- `before-document.json` – Zustand vor der Übernahme (für Rollback)

---

# Live-Aktivierung (17.09.2026)

## Ergebnis

| | Wert |
|---|---|
| `source_count` | 7646 → **8195** |
| Gültige Weltpunkte | 6241 → **6534** (+549 gemessen, −256 Template) |
| Inaktive Quellen | 1405 → 1661 |
| Segment | `PORT_PANEL8_251_2 | 7646 | 549 | PANEL8_251 | 340 | RGB` |
| Universen | 158 – 161 (Zielslots 340 – 888) |
| Preview-Kette | alle Knoten auf 8195, Panel 7 mit Alpha > 0, Template-LEDs auf 0 |
| Ausgabe | läuft, Controller `WS2812_NODE`, `BACK_PANEL_249`, `PANEL8_251` |

Offline-Nachweis vor dem Schreiben: eine Testpixel-Packung trifft exakt die
Wireslots 0, 255, 340 und 888; die Frames von `WS2812_NODE`, `APA102_ESP` und
`BACK_PANEL_249` sind Byte für Byte unverändert.

Live gegengeprüft über zwei Zeitpunkte: einmal Panel 8 hell / Panel 7 dunkel,
einmal umgekehrt – das Gradientenmaterial wandert, beide Panels bekommen Daten.
UV-Bereiche: Panel 7 u 0.542–1.000, Panel 8 u 0.002–0.456, v jeweils ≈ 0.21–0.38.

## Zwei Blocker, die dabei aufgefallen sind

### 1. Zweiter, veralteter Checkout (Ursache, nicht Symptom)

`_rebuild_router()` startete den Builder aus
`C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper` (Stand 9.9.), während
`import pixelblaze_mapper` aus `E:\…\PixelblazeMapper` (Stand 12.9.) auflöste –
E: steht in `sys.path` vor C:. Der alte Builder schreibt die Packer-Callbacks
ohne `install_native_source`, also **ohne** `SPARSE_SOURCE_MASK_V1`. Damit
schlug `assert_sparse_contract` fehl und jedes Layout-Apply mit inaktiven
Quellen war blockiert.

Verschärft wurde das durch ein zweites Detail: das live installierte
`ui_callbacks` war eine ältere Generation und setzte in `_rebuild_router()`
kein `scope['__file__']`. Der Builder leitete seinen `LOCAL_ROOT` deshalb aus
dem Operator-Pfad ab und landete bei `E:\project1` – ein Verzeichnis, das es
nicht gibt.

Behoben durch:

1. `pixelblaze_mapper` von E: nach C: gespiegelt (Backup:
   `TouchDesignerLocal/PixelblazeMapper/_backup_pixelblaze_mapper_20260917/`).
   Der C:-Baum war ein echter Teilbaum: 29 Dateien fehlten, 33 waren älter,
   keine einzige war dort neuer oder exklusiv.
2. `scope['__file__'] = BUILDER` in `_rebuild_router()` ergänzt. Die aktuelle
   Builder-Vorlage enthält die Zeile bereits, der Fix trägt sich beim nächsten
   Rebuild also selbst weiter.

Danach führen alle vier Packer den Contract, `assert_sparse_contract` ist grün.

Praktische Auswirkung auf die Wand: **keine**. Die DMX-Out-CHOPs sind
laut Builder-Invariante dauerhaft inaktiv; gesendet wird über den gemeinsamen
Art-Net-Sender, und dessen Callback trug die Maske durchgehend.

### 2. Globale Materialquelle

`apply_plan` verlangt `/project1/topto1.top == /project1/res1`; geladen war
`/project1/material_gradient_player`. `tools/integrate_panel7_20260917.py`
leiht sich `res1` jetzt für die Dauer des Applies und gibt das Material danach
unverändert zurück (auch auf dem Fehlerpfad).

## Rollback

`PixelblazeMapper_PANEL7_DRAFT_20260917.toe` ist der Stand vor der
Aktivierung, `PixelblazeMapper_PANEL7_ACTIVE_20260917.toe` der Stand danach.
Die Tabellen vor dem Eingriff liegen als `before-*.tsv` in diesem Ordner.
