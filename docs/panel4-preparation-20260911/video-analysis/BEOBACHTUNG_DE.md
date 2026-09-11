# Video 11:39:36: Zusatzpunkt und Flackern

Das unveränderte Benutzervideo enthält 1307 Bilder, 464 × 832 Pixel, ca. 59,963 Bilder/s, Dauer 21,80 Sekunden. Quelle und SHA-256 stehen in `source.json`. Die Übersicht zeigt 16 gleichmäßig verteilte Bilder; die PNGs sind unveränderte Einzelbilder an den angegebenen Frame-Indizes. Es wurden keine Bildverbesserungen oder synthetischen Inhalte verwendet.

## Sichtbare Beobachtung

Neben der hellen Scan-LED erscheint zeitgleich ein deutlich kleinerer grün/türkiser Punkt. Beispiele: Frame 87 (1,45 s), 435 (7,25 s), 783 (13,06 s), 1306 (21,78 s). Der kleine Punkt liegt nicht konstant auf derselben physischen LED. Im letzten Einzelbild liegt er auf dem Rahmen unterhalb der gescannten LED-Fläche. Seine Lage relativ zum Hauptlicht verändert sich mit dessen Position und dem Handy-Bildausschnitt.

Das ist starke Evidenz für ein optisches Geisterbild/Objektivreflex im Handyvideo. Es beweist keinen Verdrahtungsfehler und erklärt nicht automatisch jedes vom Benutzer mit bloßem Auge beobachtete Flackern. Der Benutzer wurde gefragt, ob er genau diesen kleinen Punkt meint und ob zusätzliche LEDs auch ohne Handy sichtbar blitzen. Diese Antwort steht bei Erstellung der Notiz noch aus.

Zur Unterscheidung: bei einer ruhig leuchtenden Test-LED nur den Handywinkel leicht verändern; ein Reflex wandert relativ zum Panel. Eine tatsächlich zusätzlich leuchtende LED bleibt an ihrer physischen Position. Die Scan-Kamera muss für eine laufende Aufnahme unverändert bleiben. Es wurde für die Videoanalyse kein zusätzlicher Hardwaretest gestartet und keine Verdrahtung/Controller-Konfiguration geändert.

Wenn tatsächlich mehrere nachfolgende LEDs auch mit bloßem Auge aufblitzen, bleiben Signalqualität/GND-Verbindung, Steck-/Lötstellen und Datenpegel sowie Controller-Ausgabetiming als Kandidaten offen. Aus diesem Handyvideo lässt sich keine bestimmte defekte LED oder Leitung identifizieren. Ein lokaler Sendezähler ohne Fehler beweist keinen fehlerfreien Controllerempfang.

Quellen zur Einordnung: [Nikon: starke Lichtquellen können Ghosting/Flare verursachen](https://www.nikonusa.com/learn-and-explore/c/products-and-innovation/nikkor-z-lenses-pursuing-precision); [Adafruit: gemeinsame Masse und Pegelanpassung](https://learn.adafruit.com/neopixel-levelshifter/shifting-levels). Diese Quellen erklären mögliche Mechanismen; die Zuordnung des Zusatzpunkts ist eine Schlussfolgerung aus dem vorliegenden Video.

## Begleitender Scanstatus

Die erste Panel-4-Aufnahme `capture-5a17f6c1-1aff-4d5f-856a-4e99b5595cde` lief während der Prüfung unverändert weiter und endete vollständig: **810 verarbeitet, 804 erkannt**, keine gemeldeten Sendefehler oder Abschlussfehler. Mittlere LED-Zykluszeit 485,822 ms, ca. **2,06 LEDs/s**; Transportmessfenster inklusive Anlauf/Abschluss 401,594 s. Die Quote allein bestätigt noch keine korrekten 3D-Positionen und schließt kurzzeitige Fehlblitze nicht aus.
