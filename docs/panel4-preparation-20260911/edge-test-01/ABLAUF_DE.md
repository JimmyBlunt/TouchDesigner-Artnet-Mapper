# Begrenzter Anfang-/Ende-Test

Vom Benutzer ausdrücklich angefordert, um echtes Flackern am Panel einzugrenzen. Der Benutzer berichtet zuvor: derselbe Controller-Ausgang funktioniert an einem anderen Panel ohne das Problem. Ob dasselbe Anschlusskabel verwendet wurde, wurde noch nicht bestätigt.

Ziel: Panel 4, Controller 10.0.0.249, Ausgang 4 laut unveränderter Controller-Konfiguration, 810 LEDs ab U133. Nacheinander lokale IDs **0, 1, 2, 807, 808, 809**, jeweils 2 Sekunden weiß bei 5 % Helligkeit, danach 1 Sekunde schwarz, zwei Durchgänge. Vollständige 18-Universen-Rahmen U120–U137 mit 1 ms Abstand zwischen Paketen; alle übrigen Slots schwarz. Zwei Sekunden Schwarzphase vor Beginn. Beendigung spätestens beim nächsten Sendecheck nach 44 Sekunden; anschließend drei Schwarzrahmenfolgen und Freigabe der Ausgabesperre.

Vor dem Start geprüft: keine laufende Aufnahme oder Kameravorschau, normale TouchDesigner-Ausgabe aus, interner Controller-Test aus und kein dort gehaltener Blackout. Vorab ohne Netzwerk geprüft: je Test-ID exakt eine beleuchtete LED an ihrer korrekten Adresse, alle anderen Slots schwarz, maximal 13/255 pro Kanal. Die interne Ausgabesperre verhindert konkurrierende kooperierende App-Ausgaben während des Tests.

Der Test verwendet keine Kamera und verändert weder Scanansichten noch Layout oder Controller-Einstellungen. `result.json` enthält tatsächlich gesendete Pakete, Phasenzeiten, Abschluss und eventuelle Fehler. Es ist kein optischer Nachweis: ob zusätzliche LEDs aufleuchteten, muss der Benutzer beobachten. Auch null lokale Sendefehler beweisen keinen fehlerfreien Controllerempfang.
