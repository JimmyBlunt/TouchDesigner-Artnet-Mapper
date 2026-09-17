# Panel 7 – Scan-Diagnose (17.09.2026)

Session `ff733d6e-9241-41a0-90c3-95bb4fa4d0fb`, Ordner `Scans/Pannel7`.

## Ergebnis in einem Satz

Die **2D-Erfassung ist einwandfrei** (549/549 LEDs in zwei von vier Ansichten),
die **3D-Rekonstruktion ist entartet** und darf nicht ins Layout uebernommen werden.

## Belege

| Groesse | Wert |
|---|---|
| Beobachtungen gesamt | 2177 |
| 3D rekonstruiert | 520 von 549 (nach Ausreisser-Trim) |
| Hauptachsen (Std) | PC1 2.129 / PC2 0.182 / PC3 0.0049 |
| PC2 / PC1 | **0.086** → praktisch eindimensional |
| Ausdehnung PC1 / PC2 | 6.681 / 0.771 (8.7 : 1) |
| Korrelation LED-Index ↔ Lage auf PC1 | **r = −0.976** |
| Reprojektionsfehler | Median 0.413, p90 0.959, max 2.119 |

Die Punktwolke ist keine Flaeche, sondern eine **Gerade**, auf der die LEDs
exakt in Index-Reihenfolge aufgefaedelt sind. Genau das passiert, wenn die
Triangulation unterbestimmt ist: jede LED landet irgendwo auf ihrem Sehstrahl.

`tools/place_panel*.py` bricht an dieser Stelle bewusst ab
(`assert singular[2]/singular[1] < .1, 'Review non-planar scan before fitting'`);
der Kandidat wuerde als diagonale LED-Schnur im Layout landen.

## Ursache

Die vier ausgewerteten Ansichten zeigen praktisch dieselbe Silhouette, nur
verschoben – die Kamera hat geschwenkt statt die Position zu wechseln.
Ohne Parallaxe (Basislinie) ist keine Triangulation moeglich.

| Ansicht | erkannte LEDs | u-Bereich | v-Bereich |
|---|---|---|---|
| capture-666bbcbe | 549 | 0.221–0.705 | 0.218–0.636 |
| capture-db6cbee4 | 549 | 0.388–0.746 | 0.180–0.542 |
| capture-95fc5b9f | 541 | 0.298–0.637 | 0.353–0.688 |
| capture-210a45df | 538 | 0.234–0.751 | 0.159–0.640 |

## Sichtbare Panel-Geometrie (aus den 2D-Ansichten, konsistent in allen vier)

LED-Strip serpentinenfoermig in **Spalten**, Spaltenabstand ≈ doppelter
LED-Abstand. Drei Bloecke als absteigende Treppe:

| Block | LED-Index | Spalten | LEDs/Spalte | Lage im Bild |
|---|---|---|---|---|
| A | 0 – ca. 270 | 7 | ca. 40 | links, volle Hoehe |
| B | ca. 271 – 355 | 7 | 19 → 5 (Keil) | Mitte, **oben** |
| C | ca. 356 – 548 | 10 | ca. 21 | rechts, **unten**, ca. quadratisch |

## Naechste Schritte

1. **Neu scannen mit echter Basislinie** – 5–6 Ansichten, zwischen den
   Aufnahmen jeweils 1–2 m seitlich versetzt (nicht nur schwenken/zoomen),
   Panel immer vollstaendig im Bild. Danach Offline-Solve wiederholen.
2. **Alternativ planar aus einer Ansicht** – das Panel ist flach und in
   `capture-666bbcbe` sind alle 549 LEDs sichtbar. Mit den bekannten realen
   Aussenmassen laesst sich die Ansicht per Homographie entzerren und direkt
   als Layout verwenden; SfM entfaellt. Dafuer werden die realen Kantenmasse
   von Panel 7 benoetigt.

Bis dahin: **keine Aenderung am Layout-Entwurf.** Panel 7 ist weiterhin nicht
in der Szene (11 Objekte, Panel 7 nicht darunter).

Bild: `Scans/Pannel7/panel7_scan_diagnose.png`
