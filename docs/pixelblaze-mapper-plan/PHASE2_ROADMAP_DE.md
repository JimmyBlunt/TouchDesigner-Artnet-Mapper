# Phase 2 – DMX, interaktive Vorschau und realer Hintergrund

Stand: 13. August 2026

## Zielbild

Phase 2 erweitert den fertigen portablen Mapper in vier klar getrennten
Arbeitspaketen:

```text
importierte LED-Map
       |
       +--> Mapping-/Indexprüfung
       |
       +--> DMX-Bedarf als Entwurf berechnen
       |       |
       |       +--> Review --> atomarer Apply oder vollständiger Rollback
       |
       +--> interaktive 3D-Vorschau
               |
               +--> freies Orbit/Pan/Zoom
               +--> Fotovergleich
               +--> optional kalibrierte Kameraansicht
```

## 1. Einfluss einer Map auf DMX

Die elektrische Reihenfolge ist vollständig indexabhängig:

```text
Map-Slot i = RGB-Sample i = physische LED i
```

Deshalb gilt:

- Positionsänderungen und Fill/Contain ändern DMX nicht.
- 2D oder 3D ändert DMX nicht.
- Eine andere Pixelzahl ändert Kanäle, Universen und Routing.
- Indexlücken bleiben echte Slots und erhalten `[0,0,0]`.
- Anhängen am Ende ist der sichere Erweiterungsfall.
- Einfügen oder Löschen in der Mitte verschiebt die folgenden physischen LEDs
  und benötigt eine deutliche Expertenwarnung.

Die aktuelle Anlage verwendet **GRB**, drei Kanäle pro Pixel, 170 Pixel je
Universum und 22 Universen für 3.714 LEDs. Der aktuelle flache Stream besitzt
11.142 Werte. Die bisherige `lookup1`-Obergrenze `11141` ist hart an diese
Pixelzahl gekoppelt und muss bei einem variablen Setup automatisch erzeugt
werden.

## 2. DMX-Konfiguration

Empfohlen wird ein eigener Bereich `OUTPUT (DMX)` mit zwei Zuständen:

- `LIVE`: tatsächlich laufende Konfiguration;
- `DRAFT`: aus der geladenen Map berechneter Vorschlag.

Immer sichtbar:

- Output an/aus;
- Pixelzahl und Format;
- Farbreihenfolge, standardmäßig bestehendes **GRB**;
- Startuniversum und Startkanal;
- benötigte Universen und letzte Belegung;
- Zieladresse, lokaler Netzwerkadapter und Rate;
- kompakte Universentabelle mit Pixelbereich und Art-Net-Adresse.

Der Standard ist automatische, fortlaufende Allokation ohne Aufteilen eines
Pixels über eine Universumsgrenze. Ein Apply mit geänderter Pixelzahl baut Map,
`DMX_Universes`, Lookup-Indizes, Universumskanäle und Routingtabelle als eine
Transaktion. Scheitert eine Prüfung, bleibt beziehungsweise wird die vorherige
Konfiguration vollständig wiederhergestellt.

Die DMX-Ausgabe erwartet in TouchDesigner Packet-per-Channel: ein CHOP-Kanal
entspricht einem Universum. Der DMX Out CHOP akzeptiert Werte 0–255 und kann
Net/Subnet/Universe über eine Routing-Table pro Kanal festlegen. Das entspricht
der offiziellen [DMX Out CHOP-Dokumentation](https://docs.derivative.ca/DMX_Out_CHOP).
Art-Net bündelt 512 DMX-Kanäle pro Universum; Net/Sub-Net/Universe bilden die
Port-Adresse. Siehe [offizielle Art-Net-Terminologie](https://art-net.org.uk/art-net-glossary/).

## 3. Maussteuerung

Für Orbit, Pan und Zoom soll keine zweite, unvollständige Kamerasteuerung gebaut
werden. TouchDesigners offizielles `cameraViewport` besitzt die benötigte
Navigation bereits. Empfohlen:

- linke Maustaste: Orbit;
- rechte oder mittlere Maustaste: Pan/Dolly;
- Mausrad: Zoom;
- `F`: alle LEDs rahmen;
- Home/Front und Front/Side/Top/ISO als sichtbare Buttons;
- Kamera-Lock für Installation und Abnahme.

Die Mapper-UI muss dafür den interaktiven Panel-Viewer des `cameraViewport`
einbetten, nicht nur ein statisches TOP-Bild. Referenz:
[cameraViewport](https://docs.derivative.ca/Palette%3AcameraViewport).

## 4. Foto oder reales Hintergrundbild

Die Umsetzung erfolgt in drei Stufen:

### Stufe A – einfache Backplate

```text
Movie File In -> Fit -> Level/Opacity -> Composite unter LED-Render
```

Das ist der empfohlene erste Implementierungsschritt: leicht verständlich,
schnell und ausreichend für einen Vergleich aus einer festen Front- oder
Seitenansicht. `Contain`, `Cover` und `Stretch` beziehen sich nur auf das Foto.
Eine Composite- bzw. Layer-Mix-Pipeline kann ein separates Hintergrundbild und
den transparenten LED-Render verbinden. Siehe
[Composite TOP](https://docs.derivative.ca/Composite_TOP) und
[Layer Mix TOP](https://docs.derivative.ca/Layer_Mix_TOP).

### Stufe B – perspektivischer Corner Pin

Für eine ebene Wand kann das Foto anhand von vier Ecken optisch angepasst
werden. Das ist einfach, gilt aber nur für eine feste Ansicht und eine Ebene.
Referenz: [Corner Pin TOP](https://docs.derivative.ca/Corner_Pin_TOP).

### Stufe C – echte Kamerakalibrierung

Wenn Rück- und Seitenwand gleichzeitig exakt mit einem Foto übereinstimmen
sollen, wird eine kalibrierte Kamera benötigt. TouchDesigners `camSchnappr`
berechnet Kamera-/Projektionsparameter aus mindestens sechs 2D-/3D-
Korrespondenzen. Explore Mode und Calibration Mode müssen getrennt bleiben;
die kalibrierte Kamera wird gesperrt. Referenz:
[camSchnappr](https://docs.derivative.ca/Palette%3AcamSchnappr).

## Empfohlene Umsetzungsreihenfolge

1. MCP-Routen im lokal gespeicherten Projekt wieder starten.
2. Reinen DMX-Allokationsrechner mit Unit-Tests implementieren.
3. `OUTPUT (DMX)` zunächst nur als Draft/Preview bauen.
4. D01–D09 ohne aktive Netzwerkänderung testen.
5. `cameraViewport` lokal einbetten und Maus-/Fokustests ausführen.
6. Foto-Backplate mit Open/Clear, Opacity und Contain/Cover/Stretch bauen.
7. Optionalen Corner-Pin-Modus ergänzen.
8. Erst danach atomaren DMX-Apply/Rollback mit deaktiviertem Output testen.
9. Reale Hardware-Abnahme durchführen.
10. Stabilen Stand als neue, versionsnummerierte OneDrive-Sicherung kopieren.

## Noch zu klärende Entscheidungen vor dem DMX-Live-Apply

- Soll eine kleinere Map unbenutzte bisherige Universen sofort entfernen oder
  zunächst als nullgesetzte Reserve behalten?
- Welche maximale Pixel-/Universumszahl unterstützt der Controller
  `10.0.0.244` tatsächlich?
- Soll die Farbreihenfolge global GRB bleiben oder pro Segment/Controller
  konfigurierbar werden?
- Soll ArtSync auf der realen Hardware aktiv bleiben?
- Soll vor einem Routingwechsel ein bestätigter Blackout-Frame gesendet werden?

Diese Entscheidungen blockieren nicht UI, Maussteuerung oder Foto-Backplate;
sie müssen aber vor dem ersten veränderlichen Hardware-Apply beantwortet sein.

