# Panel 4: korrigierter Anfang-/Endetest, 11.09.2026

## Korrektur zu Durchlauf 01 und 02

Der Benutzer hat bei beiden vorherigen Versuchen keine leuchtenden LEDs gesehen.
Die lokalen Sendeberichte allein belegen keine Ausgabe am Panel. Der Controller
empfing über beide Versuche zusammen 3618 weitere Pakete (81320 → 84938),
aber der Zähler vollständiger Datenrahmen blieb bei 4277. Unvollständige Rahmen
stiegen von 340 auf 889, Timeouts von 24 auf 573. Beide Versuche sind deshalb
als elektrischer/optischer Paneltest **nicht aussagekräftig**.

Der Sender lief dort in einem TouchDesigner-Python-Hintergrundthread. Die
18 Pakete eines Rahmens wurden trotz angeforderter 1-ms-Pausen so langsam
übertragen, dass der Controller sie nicht zu vollständigen Rahmen verband.

## Änderung

`tools/panel4_edge_probe_20260911.py` startet die zeitkritische Ausgabe jetzt
mit dem vorhandenen MariMapper-Python als separaten, unsichtbaren Prozess.
TouchDesigner überwacht lediglich diesen Prozess und hält währenddessen die
Ausgabesperre gegen konkurrierende Anwendungssender. Scan, Kamera und Layout
bleiben unverändert. Ein Stoppsignal wird über eine Datei an den Prozess
weitergegeben. Laufzeitbegrenzung und abschließende Schwarzrahmen bleiben aktiv.

## Umfang und Nachweis

- Controller 10.0.0.249, Port 4, Panel 4 mit 810 LEDs, U133–137.
- Vollständiger Controllerrahmen U120–137; alle anderen Slots schwarz.
- Lokale Indizes 0, 1, 2, 807, 808, 809 (gezählt: LED 1–3 und 808–810).
- Je zwei Sekunden einzeln an, eine Sekunde schwarz; zwei Runden, 5 %.
- Offline geprüft: 18 Universen pro Rahmen, genau eine ausgewählte LED,
  maximaler Kanalwert 13/255.
- Vor Start: Kamera-/Scanprozesse und Anwendungsausgaben aus, interner
  Controllertest inaktiv, keine bereits gehaltene Ausgabesperre.

`controller-before.json`, `controller-during.json`, `controller-after.json`
halten den Empfang fest. `result.json` beschreibt den lokalen Sendeablauf;
`supervisor.json` den Prozessabschluss. Empfangs- und Ausgabezähler belegen
keine optisch korrekte Funktion. Die Beobachtung des Benutzers ist weiterhin
erforderlich, um das ursprüngliche Flackern zu beurteilen.

## Ergebnis des korrigierten Durchlaufs

Prozess regulär beendet (Exitcode 0), 38,266 Sekunden, 5688 lokal gesendete
Pakete, keine lokalen Sendefehler, abschließende Schwarzrahmen gesendet.
Danach ist die Anwendungsausgabe aus und die Ausgabesperre freigegeben.
Der Controller registrierte 5560 zusätzliche Pakete, 283 vollständige Rahmen
und 283 Ausgaben. Zusätzlich traten 39 unvollständige Rahmen und 34 Timeouts
auf. Die Übertragung ist somit noch nicht verlustfrei; 128 lokal gesendete
Pakete erscheinen nicht im Empfangszähler. Die Ursache dieser verbleibenden
Differenz ist nicht geklärt. Der entscheidende Unterschied zu 01/02 ist,
dass nun vollständige Rahmen verarbeitet und ausgegeben wurden.

## Optische Rückmeldung des Benutzers

Nach dem korrigierten Durchlauf: „erste led hat nicht geflackert aber alle
dnach bi au die allerletzte wider“. Bezogen auf die sechs getesteten LEDs
waren die Testphasen für die erste und letzte LED unauffällig; bei den
dazwischen getesteten LEDs trat wieder zusätzliches Aufblitzen auf.
Es wurden nicht alle 810 LEDs getestet.

Anschließende ausdrückliche Klarstellung: „es flakert nie die eigentluche LED
sondern immer andere“. Die jeweils angesteuerte LED selbst bleibt also
stabil; andere, laut Testdaten schwarze LEDs blitzen ungewollt auf.
Die frühere Formulierung darf nicht als Flackern der Ziel-LED gelesen werden.
Ob diese anderen LEDs in der elektrischen Reihenfolge ausschließlich hinter
der Ziel-LED liegen, ist noch nicht bestätigt.

Dies bestätigt ein optisches Problem auch beim gezielten externen Test,
identifiziert aber noch kein defektes Bauteil. Das zuvor beobachtete Flackern
beim internen Controllertest besteht unabhängig von Art-Net und TouchDesigner.
Der vom Benutzer berichtete Gegenversuch mit einem anderen Panel am selben
Controllerausgang war unauffällig. Damit stehen Panel 4 und seine Zuleitung
im Vordergrund; ob dabei exakt dieselbe Zuleitung verwendet wurde, ist noch
nicht bestätigt. Die erste LED ist anhand dieses Musters allein nicht als
defekt identifiziert. Keine weitere Ausgabe ohne angekündigten Test gestartet.

Nächster sinnvoller Vergleich: gleiche Controllerbuchse und exakt dieselbe
Zuleitung mit dem unauffälligen Panel verwenden, sofern dies nicht bereits
der vorherige Gegenversuch war. Steckverbindungen nur spannungsfrei wechseln.
Bei weiter nur an Panel 4 auftretendem Fehler dessen Eingangsstecker,
Daten-/Masseverbindungen und Versorgung untersuchen. Dies sind Prüfschritte,
keine bestätigte Bauteildiagnose. Sichere Kontakte, gemeinsame Masse und kurze
Datenleitungen werden auch in den Herstellerhinweisen beschrieben:
https://learn.adafruit.com/adafruit-neopixel-uberguide/best-practices
