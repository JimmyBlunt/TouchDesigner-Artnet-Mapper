# Bedienung – Pixelblaze Portable Mapper

Der fertige Mapper befindet sich in TouchDesigner unter:

```text
/project1/pixelblaze_mapper
```

Die Oberfläche kann über den Viewer von
`/project1/pixelblaze_mapper/ui` geöffnet werden. Die große Vorschau liegt unter
`/project1/pixelblaze_mapper/preview3d/preview_out`.

## Datei importieren

1. `OPEN PIXELBLAZE` für `.json`, `.map`, `.txt` oder `.js` wählen.
2. `OPEN MARIMAPPER CSV` für `led_map_3d.csv` wählen.
3. Datei im normalen Windows-Dateidialog auswählen.
4. Pixelzahl, Dimension, Bounds, Warnungen und 3D-Vorschau prüfen.
5. Mit `FILL` oder `CONTAIN` ausschließlich die abgeleitete Vorschau ändern.
6. Erst mit `APPLY TO LEDs` in die aktive LED-Kette übernehmen.

Pixelblaze-JavaScript-Generatoren werden in einem separaten, zeitbegrenzten
Node-Prozess materialisiert. Es werden weder `require` noch `process` in den
Generator-Kontext gegeben. Trotzdem sollten nur bewusst ausgewählte Dateien
ausgeführt werden.

## Export

- `EXPORT PIXELBLAZE` schreibt ein reines JSON-Koordinatenarray.
- `EXPORT MARIMAPPER CSV` schreibt `index,x,y,z` und vorhandene Zusatzfelder.
- Exporte verwenden immer Rohkoordinaten, nicht die Fill-/Contain-Ableitung.
- Fehlende Indizes werden als echte `[0,0,0]`-Positionen portabel erhalten.

## Fill und Contain

- `Fill`: Jede Achse wird unabhängig auf `0..1` gestreckt.
- `Contain`: Eine gemeinsame Skalierung erhält die Proportionen und zentriert
  kürzere Achsen.
- Die Rohdaten bleiben bei beiden Modi unverändert.

## Sicherheitsregel

Die aktuelle Produktionskonfiguration besitzt 3.714 RGB-Pixel in 22
Art-Net/DMX-Universen. `APPLY TO LEDs` akzeptiert deshalb nur exakt 3.714
Koordinaten. Eine andere Pixelzahl kann angesehen und exportiert werden, wird
aber nicht still in das Live-Routing übernommen.

Beispiel: Die BallsMatrix3-Datei wird zu 938 Positionen materialisiert. Die
Lücken 894–896 werden mit `[0,0,0]` gefüllt. Apply bleibt erwartungsgemäß
gesperrt.

## Rückkehr zum aktiven Mapping

`REVERT` verwirft den aktuellen Entwurf und stellt die zuletzt aktive
3.714-Pixel-Map wieder her. `RELOAD` liest die ausgewählte Quelldatei erneut.

## Foto-Kalibrierung der Rückwand

Die Foto-Vorschau liegt in TouchDesigner unter
`preview3d/phase2_interaction_background_prototype/prototype_out`.
Sie ändert keine Pixelblaze-Koordinaten und keine Ausgabe-Reihenfolge – sie ist
nur die visuelle Ausrichtung auf das Referenzfoto.

Für die Rückwand gibt es zehn einzeln entzerrte Felder. Jedes Fach besitzt im
Parameter-Tab **Einzelfächer** vier eigene Ecken: oben links, oben rechts,
unten links und unten rechts, jeweils mit X und Y. Eine Änderung betrifft nur
das gewählte Fach; die Nachbarfächer bleiben unverändert.

Zuerst Fach 1 bis Fach 10 grob auf die Foto-Panels setzen und danach bei jedem
Fach die vier Ecken fein nachziehen. Die sichtbaren Zwischenräume im Foto
bleiben dadurch unabhängig einstellbar. In `prototype_out` kontrollieren, ob
jede der zehn LED-Flächen genau auf ihrem Foto-Panel liegt.

Die Seitenwand wird weiterhin getrennt über die vier Werte unter **Photo
Calibration → Side wall corners** ausgerichtet. Der Knopf **Reset both planes**
setzt beide ursprünglichen Vier-Ecken-Flächen zurück und sollte nicht für die
Rückwand-Mesh-Kalibrierung verwendet werden.
