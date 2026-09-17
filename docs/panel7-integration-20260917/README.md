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
