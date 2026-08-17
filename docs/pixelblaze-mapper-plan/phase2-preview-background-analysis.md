# Phase 2: Interaktive 3D-Vorschau und Foto-Hintergrund

Stand: 13.08.2026

## Ziel

Die bestehende Vorschau unter `/project1/pixelblaze_mapper/preview3d` soll zwei neue Arbeitsweisen ermoeglichen:

1. Freie Pruefung der LED-Punktwolke per Maus: Orbit/Tumble, Pan und Zoom/Dolly.
2. Vergleich des Mappings mit einem Foto oder Referenzbild der realen Wand.

Beide Funktionen gehoeren nur in die Vorschau. Sie duerfen weder Mappingdaten noch DMX-Ausgabe veraendern.

## Aktueller Stand der Vorschau

Die integrierte Vorschau hat bereits eine gute Trennung zwischen Daten und Rendering:

- `instance_data` erzeugt `tx ty tz r g b`.
- `led_points_geo` instanziert die LED-Punkte.
- `preview_camera` ist momentan eine feste orthografische Kamera.
- `preview_render` rendert die Punktwolke.
- `preview_out` ist ein statischer TOP-Ausgang fuer die UI.

Wichtig: Ein TOP zeigt nur das Bild. Die bisherige Einbindung von `preview_out` kann deshalb nicht automatisch die Mausnavigation einer Camera COMP erhalten. Fuer interaktive Navigation muss die UI einen aktiven Panel-COMP der Kamera anzeigen beziehungsweise die Mausereignisse explizit an diesen Panel-COMP leiten.

## Orbit, Pan und Zoom

### Empfohlene Loesung: offizielles `cameraViewport`

TouchDesigner liefert in der Palette bereits die Camera COMP `cameraViewport`. Sie besitzt dieselben grundlegenden 3D-Interaktionen wie die internen 3D-Viewer und kann auf einen beliebigen Render TOP zeigen. Die dokumentierten Standardaktionen sind Ziehen mit linker, rechter oder mittlerer Maustaste sowie das Mausrad; `f` rahmt die Szene, `h`/`n` setzt Home/Front. [Offizielle Dokumentation: cameraViewport](https://docs.derivative.ca/Palette%3AcameraViewport)

Die lokale TouchDesigner-Installation enthaelt die Vorlage unter:

`/sys/TDTox/cameraViewport`

Die untersuchte Version ist `1.2.5` und bietet unter anderem:

- frei zuweisbare Tasten fuer Tumble, Pan und Dolly;
- Geschwindigkeitsmultiplikatoren;
- Home/Frame und manuelle oder automatische Bounds;
- Achsen- und Pivotanzeige;
- perspektivische oder orthografische Projektion;
- Presets und optionale Callbacks.

Empfohlene Bedienung fuer den Mapper:

| Aktion | Eingabe |
| --- | --- |
| Orbit/Tumble | linke Maustaste ziehen |
| Pan | rechte Maustaste ziehen |
| Dolly | mittlere Maustaste ziehen |
| Zoom | Mausrad |
| Szene rahmen | `F` |
| Home/Front | `H` beziehungsweise `N` |

Die UI muss den `renderView`-Panel des `cameraViewport` anzeigen und Viewer Active aktivieren. Ein blosses Bild des Render TOP reicht fuer die Interaktion nicht.

### Alternative: eigener Mouse-In-/Panel-Execute-Controller

Ein eigener Controller koennte Mouse In CHOP oder Panel Execute DAT verwenden. Mouse In liefert Positionen, Maustasten und Mausrad und kann auf ein fokussiertes Panel beschraenkt werden. Panel Execute kann auf Panel-Wertaenderungen reagieren. [Mouse In CHOP](https://docs.derivative.ca/Mouse_In_CHOP), [Panel Execute DAT](https://docs.derivative.ca/Panel_Execute_DAT)

Diese Variante ist hier nicht empfohlen. Sie muesste Pivot, Welt-/Kameraraum, Zoomgrenzen, Tastaturfokus, Framing und unterschiedliche Projektionen erneut implementieren. `cameraViewport` loest diese Randfaelle bereits und entspricht der vertrauten TouchDesigner-Navigation.

## Hintergrundbild: empfohlene einfache Pipeline

Ein stilles Bild kann direkt mit Movie File In TOP geladen werden; dieser Operator unterstuetzt neben Videos auch Einzelbilder und Bildsequenzen. [Movie File In TOP](https://docs.derivative.ca/Movie_File_In_TOP)

Vorgeschlagene TOP-Kette:

```text
Background File
    -> Movie File In TOP
    -> Fit TOP (Contain / Cover / Stretch)
    -> optional Corner Pin TOP
    -> Level TOP (Background Opacity)
    -> Under/Over Composite <- transparenter LED Render
    -> preview_with_background_out
```

Der LED-Render braucht dabei Hintergrund-Alpha `0`. Der Hintergrund liegt als unterste Ebene, die LED-Punkte werden mit ihrem Alpha daruebergelegt.

Der Fit TOP unterscheidet die benoetigten Modi direkt:

- **Contain** = `Fit Best`: ganzes Bild sichtbar, Seiten koennen frei bleiben.
- **Cover** = `Fit Outside`: ganze Ausgabeflaeche gefuellt, Bildteile koennen abgeschnitten werden.
- **Stretch** = `Fill`: volle Flaeche, aber moegliche Verzerrung.

Diese Bedeutung entspricht der offiziellen [Fit TOP-Dokumentation](https://docs.derivative.ca/Fit_TOP).

### Datei-Dialog

Der Pulse `Open Background...` kann folgenden offiziellen Python-Aufruf verwenden:

```python
path = ui.chooseFile(
    load=True,
    fileTypes=tdu.fileTypes['image'],
    title='Select wall/reference image'
)
```

`ui.chooseFile()` liefert den ausgewaehlten Pfad oder `None` nach Abbruch. [Offizielle UI-Class-Dokumentation](https://docs.derivative.ca/UI_Class)

Fuer portable Projekte sollte es zusaetzlich die Option `Copy into project` geben. Sie kopiert das Bild nach `assets/backgrounds/` und speichert einen relativ zu `project.folder` aufgeloesten Pfad. Ohne diese Option ist der absolute Pfad nur auf demselben Rechner gueltig.

### Sinnvolle Parameter

| Parameter | Zweck |
| --- | --- |
| Background Enabled | Foto ein-/ausblenden |
| Background File | sichtbarer Dateipfad |
| Open Background | Datei-Dialog |
| Clear Background | Bildreferenz entfernen |
| Opacity | Vergleich mit LED-Layer, Bereich 0..1 |
| Fit | Contain, Cover oder Stretch |
| Alignment | Simple oder Perspective Corner Pin |
| LED Opacity | LED-Layer separat dimmen |

## Vergleich der Ausrichtungsverfahren

### A. Einfache 2D-Ueberlagerung

Das Foto bleibt bildschirmfest und die LED-Punktwolke wird darueber gerendert.

Vorteile:

- sehr einfach, schnell und GPU-guenstig;
- ideal zum optischen Vergleichen aus einer gespeicherten Front-/Seitenansicht;
- Contain/Cover und Opacity sind unmittelbar verstaendlich.

Grenzen:

- beim freien Orbit bleibt das Foto stehen und passt nicht mehr zur 3D-Geometrie;
- Perspektive und Objektivverzeichnung werden nicht korrigiert;
- keine metrische Kalibrierung.

Empfehlung: Standardmodus fuer schnelle Referenzkontrolle. Sobald ein Foto sichtbar ist, sollte die UI deutlich `Reference photo: screen-space` anzeigen.

### B. Projective 2D-Ausrichtung mit Corner Pin

Der Corner Pin TOP kann vier Bildecken verschieben und unterstuetzt bilineare oder perspektivische Abbildung. [Offizielle Corner Pin TOP-Dokumentation](https://docs.derivative.ca/Corner_Pin_TOP)

Vorteile:

- schnell fuer eine einzelne ebene Wand;
- vier gut sichtbare Wand- oder Panel-Ecken genuegen fuer eine optische Anpassung;
- keine OpenCV-Kalibrierung notwendig.

Grenzen:

- nur eine Ebene kann exakt ausgerichtet werden;
- Seitenwand und Rueckwand lassen sich aus einem einzigen Corner Pin nicht gleichzeitig korrekt abbilden;
- die Ausrichtung gilt nur fuer eine feste Kameraansicht.

Empfehlung: als optionaler `Perspective Corner Pin`-Modus fuer die Rueckwand anbieten. Die vier Pins sollten spaeter direkt im Preview gezogen und zusaetzlich numerisch gespeichert werden koennen.

### C. Kalibrierte 3D-Kamera

Fuer eine echte Uebereinstimmung zwischen Foto und 3D-Koordinaten muessen die virtuelle Kamera und die reale Aufnahmekamera dieselben Intrinsics/Extrinsics abbilden. TouchDesigners Palette-Komponente `camSchnappr` berechnet aus sechs oder mehr 2D-/3D-Korrespondenzpunkten Position, Rotation, Skalierung und Blickwinkel einer Camera COMP und zeigt einen OpenCV-Kalibrierungsfehler an. [Offizielle camSchnappr-Dokumentation](https://docs.derivative.ca/Palette%3AcamSchnappr)

Wenn das reale Objektiv sichtbar verzeichnet, muss ausserdem die Fotoebene beziehungsweise der Render passend entzerrt/verzerrt werden; dafuer existiert der [Lens Distort TOP](https://docs.derivative.ca/Lens_Distort_TOP).

Vorteile:

- bestmoegliche geometrische Uebereinstimmung mit einem realen Kamerabild;
- Rueckwand und Seitenwand koennen gemeinsam geprueft werden;
- Kalibrierungsfehler ist messbar.

Grenzen:

- mindestens sechs verlaessliche Punkte mit bekannten 3D-Koordinaten und sichtbaren 2D-Bildpositionen noetig;
- Kamera, Zoom und Foto duerfen nach der Kalibrierung nicht mehr veraendert werden;
- deutlich komplexerer Workflow.

Empfehlung: als spaeteren **Calibration Mode** getrennt vom freien **Explore Mode** entwickeln. In Calibration Mode wird die kalibrierte Kamera gesperrt; Orbit/Pan/Zoom wirken nur in Explore Mode. Ein Button `Return to calibrated view` stellt die gespeicherte Matrix wieder her.

### D. Foto als echte 3D-Wandtextur

Bei einer einzelnen ebenen Wand kann das Foto als Textur auf ein Rechteck im 3D-Raum gelegt werden. Dann bleibt die Wand beim Orbit geometrisch an ihrem Platz. Ein einzelnes Foto enthaelt aber keine korrekte Tiefeninformation fuer den ganzen Raum. Fuer Rueckwand, Seitenwand und Moebel waeren getrennte Flaechen, Masken und eine vermessene Raumgeometrie erforderlich.

Empfehlung: nur dann einsetzen, wenn eine vermessene 3D-Raumvorschau explizit gewuenscht wird. Fuer den Mapper ist die Kombination aus einfachem Fotovergleich und optionaler kalibrierter Ansicht effizienter.

## Vorgeschlagener Endzustand

```text
Explore Mode
  cameraViewport panel
  LMB orbit / RMB pan / MMB+wheel dolly
  neutraler Hintergrund oder Foto nur als unverbindliche Referenz

Photo Align Mode
  feste Front-/Seitenkamera
  Foto: Contain/Cover/Stretch
  Opacity + optionaler Perspective Corner Pin

Calibration Mode (spaetere Ausbaustufe)
  camSchnappr / >= 6 Korrespondenzen
  Kamera gesperrt
  gespeicherte Kalibrierungsmatrix + Reprojection Error
```

## Abnahmekriterien fuer die Implementierung

- Orbit, Pan, Dolly und Mausrad funktionieren nur, wenn der Preview-Panel Fokus hat.
- Andere UI-Elemente und Textfelder verlieren keine Maus- oder Tastatureingaben.
- `F` rahmt alle Punkte; `H` stellt die definierte Home-Ansicht her.
- Bildauswahl akzeptiert die von TouchDesigner unterstuetzten Bildformate und behandelt Abbruch ohne Fehler.
- Contain zeigt das ganze Bild ohne Verzerrung.
- Cover fuellt die Vorschau ohne Verzerrung und darf beschneiden.
- Stretch wird deutlich als verzerrend bezeichnet.
- Opacity 0 blendet den Hintergrund vollstaendig aus; 1 zeigt ihn unveraendert.
- LED-Farben und Alpha bleiben beim Compositing korrekt.
- Corner-Pin-Werte werden mit dem Projekt beziehungsweise Mapper-Preset gespeichert.
- Calibration Mode zeigt mindestens Punktzahl und Reprojection Error.
- Kein Preview-Parameter veraendert Mapping- oder DMX-Daten.

## Prototypstatus

Vorgesehener isolierter Pfad:

`/project1/pixelblaze_mapper/preview3d/phase2_interaction_background_prototype`

Vorgesehener separater Ausgang:

`prototype_out`

Der Prototyp soll eine lokale Kopie von `/sys/TDTox/cameraViewport`, einen separaten Render TOP und eine getrennte Hintergrund-Compositing-Kette verwenden. `preview_out`, die bestehende Kamera und alle Produktionsnodes bleiben dabei unveraendert.

### Live-Blocker am 13.08.2026

Die Analyse des bestehenden Preview-COMPs und der lokalen `cameraViewport`-Vorlage war erfolgreich. Anschliessend wurden nach einem Save-As die API-Routen des TouchDesigner-MCP-Webservers nicht wieder registriert:

- TouchDesigner-Prozess laeuft weiterhin.
- TCP-Port `9981` lauscht weiterhin.
- alle Aufrufe unter `/api/td/server/*` antworten jedoch mit `NOT_FOUND`.

Der erste Erstellungsversuch wurde wegen eines Python-Syntaxfehlers bereits vor Ausfuehrung verworfen. Der korrigierte Erstellungsversuch erreichte TouchDesigner wegen der fehlenden Route nicht. Daher wurde **kein** Phase-2-Prototyp angelegt und es gibt keine teilweise erzeugte Prototype-Struktur.

Zur sicheren Fortsetzung muss `/project1/mcp_webserver_base` beziehungsweise dessen API-/Route-Registrierung einmal neu gestartet werden. Danach kann der oben spezifizierte Unter-COMP in einem Schritt erzeugt und mit Node-Error-, Maus- und Screenshot-Tests abgenommen werden.

Die Projektdatei wird in dieser Forschungsphase nicht gespeichert.
