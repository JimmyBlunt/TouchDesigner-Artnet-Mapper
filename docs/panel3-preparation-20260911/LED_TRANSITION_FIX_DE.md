# Lange und ausgelassene LED-Blitze: Ablauf korrigiert

Nutzerbeobachtung: Einzelne LEDs bleiben lange an; danach blinken folgende LEDs sehr kurz oder scheinbar gar nicht. Das Kamerabild ist nach Nutzerangabe insgesamt dunkel. Fremdlicht ist deshalb keine belegte Ursache. Die zweite Ansicht wurde noch mit dem bisherigen Ablauf abgeschlossen: 880 geprueft, 825 erkannt, 55 nicht erkannt.

Vier Fehler im bisher verwendeten nativen Ablauf sind im Quellcode nachgewiesen:

1. Die Suchfrist beginnt vor dem synchronen Einschaltbefehl. Transportwartezeit kann die Frist vor der ersten Kamerapruefung aufbrauchen.
2. Bleibt vor dem Einschalten ein Lichtpunkt sichtbar, kann der native Ablauf nach drei Sekunden None zurueckgeben: Die LED gilt dann als geprueft/nicht erkannt, obwohl sie nie eingeschaltet wurde.
3. Bei erfolgloser Suche fehlt die Dunkelheitspruefung nach dem Ausschalten.
4. Bei dauerhaft sichtbarem Punkt nach einer Erkennung startet die native Dunkelheitsfrist immer wieder neu; bisher begrenzte erst unser uebergeordneter 30-Sekunden-Watchdog diesen Fall.

Diese Befunde passen zu Teilen der Beobachtung, belegen aber nicht abschliessend die Ursache am physischen Panel. Es gibt keinen programmierten Aufholmodus fuer verlorene Zeit.

## Korrigierter Ablauf ab naechstem Scanstart

scan_detector.enable_and_find_led steuert die Schritte im Projekt; die installierte MariMapper-Bibliothek bleibt unveraendert. Ihre Bildverarbeitung, Kameraeinstellungen und der adaptive TimeoutController werden weiterverwendet.

- Positive, endliche Suchfrist pruefen; Mindestbudget 100 ms. Das ist keine feste Leuchtdauer: Eine erfolgreiche Erkennung beendet die Suche sofort.
- Dunkelbild vor Einschalten pruefen. Bei dauerhaft sichtbarem Punkt explizit abbrechen statt LEDs unbemerkt zu ueberspringen.
- LED einschalten und Sendebestaetigung abwarten. Erst dann die monotone Suchuhr starten und mindestens ein Kamerabild pruefen.
- Bei Erfolg, Zeitablauf oder Ausnahme Ausschalten versuchen. Eine zusaetzliche Ausschaltausnahme verdeckt nicht den urspruenglichen Fehler; der Supervisor sendet unabhaengig final Schwarz.
- Nach Erfolg UND erfolgloser Suche auf Dunkelbild warten. Nach drei Sekunden anhaltendem Licht abbrechen, nicht die Frist endlos neu starten.
- Adaptive Suchdauer nur aus der eigentlichen Suche ermitteln, ohne Ein-/Ausschaltwartezeiten. Fuer den Bewegungstest denselben Ablauf verwenden.

Die Phasenmessung bleibt aktiv. search_timeout_used_ms dokumentiert das effektive Budget des gerade geprueften Schritts; search_timeout_ms den danach aktuellen adaptiven Rohwert. Camera.read kann weiterhin blockieren; Kamera-Kindprozess, Abbruchsignal und unabhaengiger Supervisor bleiben deshalb erforderlich. Eine Sendebestaetigung ist kein Nachweis, dass die LED optisch aufgeleuchtet hat.

## Tests und Einfuehrung

99 kombinierte Offline-Tests bestanden. Darunter 11 neue Adaptertests: 200 ms Einschaltwartezeit bei 100 ms Suchbudget und Erkennung 50 ms nach ACK funktioniert; bei 1 ms adaptivem Rohwert bleiben 100 ms Suchbudget; Erkennung beendet frueher; Dunkelheitsfehler, Miss, Ausnahme, KeyboardInterrupt und Ausschaltfehler werden korrekt behandelt. Fortschrittszaehler, Zeitmessung, Sendegrenze, Blackout und Dialoge sind ebenfalls geprueft.

Keine laufende Aufnahme veraendert und keine Hardware gestartet. Keine nativen Operatoraenderungen oder TOE-Neuladung erforderlich: Der existierende Launcher laedt beim naechsten manuellen START SCAN die neuen Python-Dateien. Praxispruefung von Blitzfolge, Geschwindigkeit und Erkennungsquote steht noch aus. Vorhandene Ansichten bleiben unveraendert.
