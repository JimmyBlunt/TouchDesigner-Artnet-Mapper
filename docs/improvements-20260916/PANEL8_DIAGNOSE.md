# Panel 8 gab nichts aus - Diagnose vom 17.09.2026

## Symptom

Nach dem Anschliessen und Einschalten blieb Panel 8 dunkel, obwohl es in
TouchDesigner korrekt konfiguriert war und der Controller erreichbar ist.

## Falsche Faehrten unterwegs

Zwei Messungen fuehrten zunaechst in die Irre und sind hier festgehalten,
damit man sie beim naechsten Mal schneller abhakt:

1. Eine erste Stichprobe an `source_select` zeigte fuer den Bereich
   2720..2975 exakt `min = max = 0` auf allen drei Kanaelen. Das sah nach
   "es kommen gar keine Daten an" aus. Eine zweite Messung Sekunden spaeter
   zeigte normale Werte - der erste Blick fiel in einen Moment, in dem das
   Material an dieser Stelle schwarz war. **Einzelmessungen an animierten
   Ketten taugen nicht als Beweis.**

2. Die aktive Maske stand im Verdacht. Sie ist fuer Panel 8 aber vollstaendig
   aktiv (256 von 256). Auch die Kette bis `math1` fuehrt Farbe.

Nebenbefund, noch offen: die UV-Koordinaten von Panel 8 liegen in einem sehr
dunklen Bereich des Materials (Mittelwert 0,036 / 0,038 / 0,092 gegen
0,30 / 0,44 / 0,25 an der Rueckwand). Panel 8 bekommt Daten, aber wenig
Licht. Das ist eine Mapping-Frage, kein Ausgabefehler.

## Die tatsaechliche Ursache

Der Controller sagt es selbst. `GET http://10.0.0.251/api/config`:

    pixelCount      816
    universeCount     6
    outputs[0]  APA102  256 px  ab Pixel   0  ab Universum 156   (= Panel 8)
    outputs[1]  APA102  560 px  ab Pixel 256  ab Universum 158

`GET http://10.0.0.251/api/status` vor der Korrektur:

    packets           19.944     er empfaengt uns, 42 Pakete/s
    framesComplete         0     aber kein einziges vollstaendiges Bild
    framesIncomplete   9.614
    fps                    0     also gibt er nichts aus
    droppedPackets         0

TouchDesigner hatte fuer PANEL8_251 `reserved_universes = 2` und sendete nur
die Universen 156 und 157. Der Controller wartet auf alle sechs Universen
seiner Konfiguration, bevor er ein Bild ausgibt. Die Universen 158 bis 161
kamen nie an, also blieb jedes Bild unvollstaendig - und damit blieb auch
Panel 8 dunkel, obwohl fuer Panel 8 selbst alles stimmte.

Es ist alles oder nichts: ein korrekt versorgter Ausgang nuetzt nichts,
solange ein anderer Ausgang desselben Controllers hungert.

## Korrektur

`reserved_universes` fuer PANEL8_251 von 2 auf 6. Sofortige Wirkung:

    framesComplete   0 -> 443
    fps              0 -> 16, spaeter 22
    droppedPackets   0, sequenceErrors 0

## Zustand nach der Sitzung

Beide Ausgaenge am Controller sind aktiv (Ausgang 1 wurde zwischenzeitlich
testweise deaktiviert und auf Wunsch wieder eingeschaltet, weil dort
Panel 7 angeschlossen werden soll). TouchDesigner sendet U156..161.

Die Originalkonfiguration des Controllers liegt als
`controller_10.0.0.251_config_backup_20260917.json` daneben.

## Was fuer Panel 7 noch fehlt

Ausgang 1 erwartet 560 Pixel ab Universum 158. Damit dort etwas ankommt -
und damit der gefuehrte Scan Panel 7 ueberhaupt ansteuern kann - braucht es
eine Zeile in `segment_config`:

    name              PANEL7_...
    source_start      freier Bereich, z.B. 2976  (2976..3743 sind laut
                      Validierung unbelegt, 768 Pixel - reicht fuer 560)
    count             560
    controller        PANEL8_251
    destination_start 256
    color_override    nach Hardware pruefen

Solange diese Zeile fehlt, gehen an die Universen 158..161 nur Nullen.

Das ist genau der Befund aus der Analyse: ein neues Panel muss an mehreren
Stellen eingetragen werden, und keine davon prueft die anderen. Hier war es
die Universen-Reserve, die niemand mitgezogen hat.

---

## Nachtrag 17.09.2026: Panel 7 auf Ausgang 1 eingetragen

Angaben des Betreibers: 549 LEDs, Farbreihenfolge RGB.

Neue Zeile in `segment_config`:

    name               PANEL7_OUT1_251
    source_start       2976
    count              549
    controller         PANEL8_251
    destination_start  256
    reverse            0
    color_override     RGB

Der Quellbereich 2976..3524 lag frei; auf Kollision mit allen zwoelf
bestehenden Segmenten geprueft, keine.

Nach dem Eintrag traegt der Frame fuer PANEL8_251 alle sechs Universen:

    U156  Summe 23617   Panel 8
    U157  Summe 25701   Panel 8 + Anfang Panel 7
    U158  Summe     0   Panel 7, Quellpixel dort ohne Licht
    U159  Summe 27053   Panel 7
    U160  Summe 15842   Panel 7
    U161  Summe     0   Rest

    Controller: framesComplete 1692 | fps 23 | droppedPackets 0

Dass U158 und U161 schwarz sind, ist kein Fehler: Panel 7 ist noch nicht
vermessen und greift daher auf Quellpixel ohne sinnvolle UV-Zuordnung zu.
Was dort leuchtet, ist bedeutungslos, bis der gefuehrte Scan gelaufen ist.
Fuer den Scan selbst spielt es keine Rolle, weil dieser die LEDs direkt
ansteuert.

### Offene Unstimmigkeit

Der Controller ist fuer Ausgang 1 auf **560** Pixel konfiguriert, physisch
haengen dort **549**. Am Universum-Bedarf aendert das nichts (beides
erfordert vier Universen), aber die beiden Wahrheiten sollten angeglichen
werden - entweder `pixelCount` am Controller auf 549, oder bewusst als
Reserve stehen lassen und hier vermerken.

### Unstimmigkeit geschlossen

Der Betreiber hat `pixelCount` fuer Ausgang 1 am Controller auf 549
korrigiert. Damit stimmen alle drei Wahrheiten ueberein:

    Controller  Ausgang 0  256 px ab U156   Ausgang 1  549 px ab U158
                pixelCount 805   universeCount 6
    TouchDesigner  PANEL8_251 reserved_universes 6, sendet U156..161
    segment_config  PANEL8_UNTER_PANEL6 256 px -> Ziel 0
                    PANEL7_OUT1_251     549 px -> Ziel 256

Messung danach:

    framesComplete    1438 und steigend
    framesIncomplete     0     (vorher liefen Reste mit)
    fps                 20
    timeouts             0
    droppedPackets       0
    TD send_ms        23,4 ms  (vorher 34,7 - der Frame ist jetzt passend
                                dimensioniert statt mit Blind-Pixeln gefuellt)

Hinweis zu den Farbreihenfolgen: der Controller meldet fuer beide Ausgaenge
RGB, waehrend `segment_config` fuer Panel 8 `color_override = BGR` traegt und
fuer Panel 7 RGB. Das war vor dieser Sitzung schon so und hat fuer Panel 8
offenbar gestimmt - beim ersten Blick auf Panel 7 also darauf achten, ob die
Farben stimmen oder vertauscht sind.

Die aktuelle Controller-Konfiguration liegt als
`controller_10.0.0.251_config_20260917_final.json` daneben; das aeltere
`..._backup_20260917.json` ist der Stand *vor* den Korrekturen und sollte
nicht mehr zum Zurueckschreiben verwendet werden.

---

## Korrektur: destination_start war falsch gerechnet

Beim Anlegen des Panel-7-Segments hatte ich `destination_start = 256`
eingetragen, weil der Controller fuer Ausgang 1 `startPixel: 256` meldet.
Das ist die falsche Groesse.

`destination_start` ist ein Pixel-Index **innerhalb des Controller-Frames**,
und der Frame beginnt beim ersten reservierten Universum. Die Universums-
nummer ergibt sich daraus als `destination_start // 170` - nachzulesen in
`build_port_topology_ui.py` Zeile 166:

    tail = controller.reserved_universes - (last.destination_start // 170)

Und der Scan-Code rechnet es selbst genauso vor (`standalone_scan.py`):

    destination_start = (port['universe'] - first) * 170

Fuer Panel 7 auf Universum 158 bei Frame-Start 156 heisst das:

    (158 - 156) * 170 = 340

Mit 256 landete das Segment auf Universum 157 - also 84 Pixel zu frueh.
Der Controller beginnt Ausgang 1 aber exakt an der Universumsgrenze 158.
Folge waere ein um 84 LEDs verschobenes Bild gewesen, bei dem die letzten
84 LEDs leer bleiben. Korrigiert auf 340, damit belegt das Segment die
Ziel-Pixel 340..888, also genau die Universen 158..161.

Merksatz: `startPixel` in der Controller-Konfiguration und
`destination_start` in `segment_config` sind **nicht dasselbe**, sobald ein
Ausgang nicht an einer Universumsgrenze endet. Panel 8 endet bei Pixel 255
mitten in Universum 157; der Controller richtet Ausgang 1 trotzdem auf die
naechste ganze Universumsgrenze aus.

Nachmessung nach der Korrektur, Quelldaten je Universum:

    U158  Panel7 lokal   0..169   alles 0      Quellpixel ohne Licht
    U159  Panel7 lokal 170..339   Mittel 0,24  Daten
    U160  Panel7 lokal 340..509   Mittel 0,34  Daten
    U161  Panel7 lokal 510..548   alles 0      Quellpixel ohne Licht

Die schwarzen Universen sind kein Packfehler: die Quellpixel 2976..3145 und
3486..3524 tragen derzeit schlicht kein Licht, weil Panel 7 noch keine
echte UV-Zuordnung hat. Das loest der Scan.

## Hinweis zum Scan-Dialog

`NEW ACQUISITION` blockiert mit "Controller frame range must contain every
panel universe", wenn `CONTROLLER UNIVERSE COUNT` zu klein ist. Die Pruefung
in `standalone_scan.py` verlangt:

    letztes Panel-Universum  <=  frame_start + frame_count

549 LEDs = ceil(549/170) = 4 Universen, belegt also 158..161 (exklusives
Ende 162). Bei Frame-Start 156 muss der Count daher mindestens 6 sein.
Mit 3 reichte der Rahmen nur bis 159 - blockiert.

Richtige Werte fuer Panel 7:

    PANEL START UNIVERSE        158
    LED COUNT                   549
    CONTROLLER FRAME START      156
    CONTROLLER UNIVERSE COUNT     6
    NETWORK COLOR ORDER         RGB
