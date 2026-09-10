# Vom Nutzer für später vorgemerkt

Screenshot user-reported-coverage-context.png: In der Mitte steht weiterhin der alte Testumfang 3/5 und die Empfehlung für weitere Ansichten, während das bearbeitete Feld LEDS TO SCAN bereits 0–737 enthält. Der Nutzer möchte dies später verbessern, nicht während der aktuellen manuellen Aufnahme.

Die Werte stammen aus der letzten erfassten/übernommenen Sitzung. Künftig klar zwischen letztem Testergebnis und neu eingegebenem, noch nicht geprüftem Scanumfang unterscheiden; Herkunft/Umfang der Anzeige explizit anzeigen und Hinweis nach Scopeänderung passend aktualisieren. Keine Änderung an der Coverage-Logik in diesem Schritt.

## Offen: Fortschrittsanzeige während der Aufnahme

Vom Nutzer während der manuellen Panel-2-Aufnahme ausdrücklich für später gewünscht: In Guided Scan eine gut sichtbare, laufend aktualisierte Anzeige entsprechend der MariMapper-Konsole einbauen.

- Bereits bearbeitete LEDs / insgesamt zu scannende LEDs.
- Davon erfolgreich erkannte LEDs.
- Beispiel: „Bearbeitet 420 / 738 · Erfolgreich erkannt 398“ (nur Beispielwerte).
- Werte auf die aktuell laufende Ansicht beziehen; vergangene Ansichten und Abdeckungsstatistik separat kennzeichnen.
- Die Zähler aus dem tatsächlichen Workerstatus übernehmen (processed, detected, total), nicht aus verstrichener Zeit schätzen. Bei Abschluss oder Abbruch den letzten Stand und den Endstatus zeigen.

Status: vorgemerkt, noch nicht umgesetzt. Während der laufenden manuellen Aufnahme keine UI- oder Workeränderungen vornehmen.
