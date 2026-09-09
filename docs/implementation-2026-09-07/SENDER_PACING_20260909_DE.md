# Senderate und Ruckeln: Befund und begrenzte Korrektur

## Bestätigter Softwarefehler

Der gemeinsame Art-Net-Sender prüfte bislang, ob seit dem letzten gesendeten
Frame mindestens `1 / höchste Controller-Rate` vergangen war. Nach dem Senden
wurde dieser Zeitpunkt auf die aktuelle Zeit gesetzt. Läuft der TD-Callback
geringfügig schneller als die eingestellte Rate, kann dadurch jeder zweite
Callback übersprungen werden. Außerdem wurden alle Controller gemeinsam mit
der höchsten eingestellten Rate gesendet: eine individuelle Einstellung von
30 FPS wurde neben einem 60-FPS-Controller nicht eingehalten.

`pixelblaze_mapper/sender_pacing.py` verwendet pro Controller fortlaufende
monotone Sollzeitpunkte. Verpasste Zeitfenster werden übersprungen; es gibt
keine Paket-Aufholserie innerhalb eines Callbacks. Ein Controller erhält alle
seine Universen aus demselben aktuellen RGB-Frame. Die RGB-Berechnung, Farben,
Helligkeit, Zuordnung und 510-Byte-Paketgröße werden nicht verändert.

## Nachweis ohne Hardwareausgabe

Deterministische Simulation über ungefähr zehn Sekunden:

| Fall | Altes Verfahren | Neue Zeitplanung |
|---|---:|---:|
| 60 FPS angefordert, Callback 60,1 Hz | 301 Frames | ungefähr 600 Frames |
| Gemeinsamer Callback 60 Hz; Controller 60/30 FPS | beide schnellste Rate | 600 / 300 Frames |

Unit-Tests prüfen zusätzlich Pause ohne Aufholserie, Ratewechsel, Entfernen
und erneutes Hinzufügen, Reset, rückwärts springende Uhr, ungültige Werte und
die fail-closed Installation in den generierten Sendercode.

Ein zusätzlicher Laufzeittest führt den **vollständigen generierten Sendercode**
mit echten Router-Packfunktionen, simulierten TD-Tabellen/CHOP-Kanälen und einem
rein speichernden Fake-Socket aus (`tests/test_generated_sender_runtime.py`).
600 Callbacks ergeben 600 Seiten-Frames und 300 Rückwand-Frames, jeweils mit
zwei Universen: 1800 vollständige ArtDMX-Pakete. Header, Ziel-IP, Universen,
510-Byte-Länge, GRB/RGB, Helligkeit und Schwarzmaske werden geprüft. Im
Kalibrierungsmodus funktioniert die wechselnde Teilmenge fälliger Controller
ebenfalls ohne fehlende Frames oder unnötige Live-Berechnung. Bei 120-Hz-
Callbacks bleiben 60/30 Frames pro Sekunde und genau 60 ausgelassene Ticks.
Zähler für Packen, Senden, Pakete, Cache-Neuaufbau und tatsächliche Senderate
werden gegen diese erwarteten Werte geprüft. Stop verhindert weitere Pakete.
Alle drei Laufzeittests bestanden; es wurde kein echter Socket geöffnet.

## Messung in TouchDesigner

Nur Lesezugriffe und lokale Packberechnung, keine Netzwerkpakete. Acht
Wiederholungen; Median, 3744 RGB-Quellplätze, zwei aktive Konfigurationen:

| Arbeit | Zeit |
|---|---:|
| Konfigurationssignatur lesen | 0,153 ms |
| Drei CHOP-Kanäle als Werte lesen | 0,649 ms |
| Zwei Controller aus Wertelisten packen | 3,910 ms |
| Direkt aus TD-Channel-Objekten packen | 5,594 ms |

Die bestehende Maske für inaktive LED-Plätze erstellt bereits Wertelisten,
wenn Maskenbereiche vorhanden sind. Deshalb wurde hier keine zusätzliche
Snapshot-Optimierung eingebaut. Die Messung enthält **keinen vollständigen
Material-Renderlauf** und erklärt nicht allein die beobachteten 12 FPS.

## Grenzen und Integration

Der Patch kann keine fehlenden TD-Frames ersetzen. Material-Rendering,
GPU-Rücklesen, Vorschau und andere Callback-Arbeiten können weiterhin die
Bildrate begrenzen. Gemessene Sender-FPS sind keine Bestätigung der tatsächlichen
Ausgabe-FPS eines Controllers. 60 FPS werden ausdrücklich nicht garantiert.

Der Builder soll den bestehenden maskierten Sendertext mit
`sender_pacing.install_source(...)` umschließen. Der Installer ist idempotent
und verweigert unbekannten Sendercode. Ein Live-Neuladen des DAT setzt den
Sender zurück; Root muss vorher den laufenden Sender sicher stoppen und erst
nach Prüfung explizit wieder starten. Dieser Untersuchungsdurchlauf selbst
hat weder den Live-DAT geändert noch Ausgänge eingeschaltet.
