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
