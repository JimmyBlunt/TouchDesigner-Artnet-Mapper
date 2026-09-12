# GICO: Kamera-Test für tatsächlich sichtbare neue Bilder

Der Test ist vorbereitet. Er startet **keine Ausgabe beim Import oder beim
Vorbereiten**. Ein echter Durchlauf erfolgt erst mit dem ausdrücklichen
Kommando `run`. Für diesen Stand wurden nur Offline-Tests ausgeführt.

## Was der Test misst

Der unabhängige Sender überträgt unverändert alle 24 Universen U0–U23 an
10.0.0.244 über die vorhandene Schnittstelle 10.0.0.125. Die Zuordnung bleibt:

| Panel | LEDs | Zielpixel ab | Markierte lokale LEDs |
|---|---:|---:|---|
| side_1 | 517 | 0 | Gleichmäßig über 0–516 verteilt |
| side_2 | 269 | 1020 | Gleichmäßig über 0–268 verteilt |
| side_3 | 398 | 2040 | Gleichmäßig über 0–397 verteilt |

Je Panel tragen 20 verteilte LEDs eine Bildnummer: 12 Gray-Code-Bits und eine
CRC8-Prüfsumme. Die 21. LED ist eine konstante Helligkeitsreferenz. Die gleiche
Nummer erscheint an allen drei Ports; auch Marker in späteren Universen werden
erfasst. Alle übrigen Pixel einschließlich reservierter Universen bleiben schwarz.
Die Marker sind weiß mit Kanalwert 16/255, also etwa 6,3 % des digitalen
Wertebereichs. Die tatsächliche Lichtleistung hängt von LED und Controller ab.

Ein Durchlauf dauert etwa 3 Minuten 40 Sekunden:

1. Alle Marker leuchten drei Sekunden, danach eine Sekunde schwarz.
2. 21 Kalibriermarker leuchten nacheinander je eine Sekunde, parallel auf den
   drei Panels. Daraus werden die Positionen im aufgenommenen Video bestimmt.
3. 15, 25 und 30 FPS: jeweils drei Sekunden Aufwärmen, 60 Sekunden Messung und
   zwei Sekunden schwarze Trennung.
4. Der Sender wird geschlossen; der separate Worker sendet Schwarz auf allen
   berührten Universen. Bei Prozessausfall greift dessen vorhandener
   Inaktivitäts-Watchdog. Der letzte Workerstatus wird gespeichert.

Die fortlaufende Bildnummer zählt **vorgelegte Bilder**. Pro Bild werden
24 ArtDmx-Pakete mit **Sequenzbyte 0** erzeugt. Die ArtDmx-Reihenfolgeprüfung
bleibt damit wie im geprüften nativen GICO-Sender ausgeschaltet. Dort hatte eine
pro Bild wiederverwendete, von null verschiedene Sequenznummer beim GICO
Universumsverluste ausgelöst. Die eindeutig sichtbare Bildnummer steht unabhängig
davon im Gray-/CRC-Payload; eine aktivierte Headersequenz ist dafür unnötig.
Die Senderdatei nennt
Einreichungszeit und lokale Annahme; das ist noch kein Empfangsnachweis. Der
Workerstatus enthält tatsächlich versandte, verworfene und fehlerhafte Pakete
beziehungsweise Bildpakete. Bei Rückstau wird nicht versucht, verlorene Zeit
durch schnelleres anschließendes Blinken aufzuholen.

## Aufnahme durch den Nutzer

- Originalvideo mit möglichst 240, mindestens 120 aufgenommenen Bildern/s.
  Alle drei Panels sollten sichtbar und die Marker als einzelne Punkte
  auflösbar sein. Reicht die Auflösung nicht, zunächst ein Panel aufnehmen.
- Kamera fest abstellen und während Kalibrierung und Messung nicht bewegen.
  Fokus und Belichtung fixieren; wenn einstellbar, kurze Belichtung ungefähr
  1/1000 s und HDR ausschalten. Die einzelnen LEDs dürfen nicht zu großen,
  zusammenlaufenden weißen Flächen überbelichten.
- Aufnahme **vor** dem Startkommando beginnen, mindestens bis zum schwarzen
  Ende laufen lassen. Das komplette Original direkt als Datei übertragen;
  keine nachträglichen Schnitte, variablen Zeitlupenrampen oder Bildinterpolation.
- Festhalten, ob es beispielsweise 240-FPS-Aufnahme mit 30-FPS-Zeitlupendatei
  ist. Dann ist der konstante Zeitfaktor 8. Eine Dateiangabe „30 FPS“ allein
  beweist nicht, ob es Echtzeit oder Zeitlupe ist. Unbekannte Zeitbasis wird
  nicht als belastbare physische FPS-Messung interpretiert.

Rolling Shutter oder LED-PWM können einzelne Kameraaufnahmen verfälschen.
Darum werden zweifelhafte Helligkeiten und falsche CRCs verworfen und eine
Bildnummer muss in mindestens zwei unmittelbar aufeinanderfolgenden
Kamerabildern bestätigt werden. Einzelne verworfene Kameraaufnahmen sind
normal und kein Beweis für ein Controllerproblem.

## Startkommandos

PowerShell im Ordner `PixelblazeMapper`; der vorhandene Python-Pfad lautet:

```powershell
$gicoPython = 'C:/Users/jbhtz/AppData/Roaming/uv/tools/marimapper/Scripts/python.exe'
& $gicoPython tools/gico_camera_test.py prepare --output docs/performance-program-20260912/gico/offline-plan
```

`prepare` schreibt ausschließlich einen Plan. Für eine echte Aufnahme ein
**neues** Ausgabeverzeichnis verwenden und Kamera zuerst starten:

```powershell
& $gicoPython tools/gico_camera_test.py run --output measurements/gico-camera-001
```

`run` prüft vor dem Senden über die lokale Bridge, dass TouchDesigner-Ausgaben
ausgeschaltet sind. Schlägt diese Prüfung fehl, beginnt keine Lichtausgabe.
Andere Art-Net-Programme müssen ebenfalls gestoppt sein; eine lokale Prüfung
kann entfernte Sender nicht ausschließen. Es werden keine Controllerparameter,
Scan-Dateien oder Layouts geändert. Abbrechen ist mit Strg+C möglich.

## Auswertung, sobald das Video vorliegt

Die Auswertung benötigt OpenCV und NumPy; beide sind im genannten Python
vorhanden. Sie kann nach der Aufnahme vom Agenten durchgeführt werden.

Zuerst wird die Videozeit festgelegt, die dem Beginn des Senderprotokolls
entspricht. Dafür dienen das erste gemeinsame Aufleuchten und die folgende
Schwarzphase; `run.json` enthält die genauen Phasenzeiten. Der Beispielwert
`2.15` muss durch den aus dem Video bestimmten Wert ersetzt werden.

```powershell
& $gicoPython tools/gico_camera_analyze.py calibrate `
  --video 'C:/Pfad/Originalvideo.mp4' `
  --run measurements/gico-camera-001/run.json `
  --video-zero 2.15 --time-scale 1 --time-basis original_realtime_pts `
  --output measurements/gico-camera-001-calibration
```

Bei konstant achtfach verlangsamter Originaldatei stattdessen
`--time-scale 8 --time-basis constant_slow_motion_verified` verwenden.

Im Kalibrierfenster mit der Maus je ein Rechteck um das erste, zweite und
dritte Panel ziehen. Leertaste bestätigt ein Rechteck, Enter beendet die
Auswahl. Alternativ können bestimmte Panels ohne Fenster über `--regions`
gewählt werden; JSON-Beispiel für ausschließlich Panel 3:

```json
[{"name":"side_3","rect":[100,200,900,700]}]
```

Die Zahlen bezeichnen x, y, Breite und Höhe in **Video-Pixeln**. Die Kamera-
Kalibrierung ist unabhängig von den gespeicherten 3D-Scan-Koordinaten.
`calibration-review.png` zeigt die gefundenen und nummerierten Marker.
Dieses Bild prüfen: jeder Kreis muss genau eine tatsächlich sichtbare LED
treffen. Niedriger Kontrast oder doppelte Markerpositionen brechen die
Kalibrierung mit einer verständlichen Fehlermeldung ab.

```powershell
& $gicoPython tools/gico_camera_analyze.py analyze `
  --video 'C:/Pfad/Originalvideo.mp4' `
  --run measurements/gico-camera-001/run.json `
  --calibration measurements/gico-camera-001-calibration/calibration.json `
  --output measurements/gico-camera-001-analysis
```

Das Ergebnis enthält pro Rate und ausgewähltem Panel:

- geschätzte Rate eindeutig erkannter neuer Bilder und beobachtete Abstände;
- nicht beobachtete Bildnummern, ohne sie voreilig Controllerverlusten zuzuordnen;
- Anteil verworfener Kameraaufnahmen und deren Gründe;
- geprüfte Kamera-Zeitstempel, mediane Aufnahmerate und größte Zeitlücke;
- unterschiedliche gleichzeitig erkannte Nummern zwischen Panels. Auch diese
  können durch Rolling Shutter entstehen und sind zunächst nur Beobachtungen.

`decoded-samples.csv` macht jedes ausgewertete Kamerabild nachvollziehbar.
`analysis.json` enthält die Zusammenfassung. Es wird keine Bildrate aus
Frameindex geteilt durch einen nominalen FPS-Wert erfunden: liefert der Decoder
keine streng steigenden Präsentationszeitstempel, stoppt die Auswertung.

## Interpretation und Grenzen

Die optische Schätzung beruht auf neuen sichtbaren Bildnummern. Sie zählt nicht,
wie oft der Controller elektrisch dieselben Werte erneut ausgibt. Unbeobachtete
IDs können im Sender/Worker, im Controller oder durch Kamera/Decodierung fehlen.
`proven_controller_drops` und `receiver_electrical_fps` bleiben deshalb bewusst
unbestimmt. Geringe Abweichungen sind auch durch zeitliche Kameraabtastung möglich.
Der erste sichtbare Bildzustand wird für die Ratenschätzung ausgelassen, da die
Aufnahme mitten in dessen Haltezeit beginnen kann.

Eine brauchbare 30-FPS-Beobachtung verlangt eine ausreichend schnelle Aufnahme,
guten Marker-Kontrast, fast vollständig erkennbare Nummern und etwa 30 neue
Bildnummern pro realer Sekunde über die volle Minute. Viele CRC-Verwerfungen
erfordern zunächst eine bessere Aufnahme. Bleiben bei guter Aufnahme Lücken,
werden Senderlog und optional Netzwerkmitschnitt verglichen. Für eine eindeutige
elektrische Bestätigung folgt eine Logic-Analyzer-Messung der codierten Daten.

Der vorbereitete Durchlauf prüft den unabhängigen Sender. Dieselbe pure Funktion
`gico_camera_benchmark.encode()` plus `payloads()` kann später in der optimierten
TD-Ausgabe denselben Teststrom liefern. Eine erfolgreiche unabhängige Messung
darf nicht als Messung der TouchDesigner-Pipeline ausgegeben werden.

Quellen und vorherige Hardwaremessungen stehen in
`docs/controller-performance-20260912/GICO_RECHERCHE_UND_MESSPLAN_DE.md`.
Die neue Implementierung selbst ist ein lokales Messverfahren; sie behauptet
keinen bislang unbekannten Diagnosezähler im GICO.
