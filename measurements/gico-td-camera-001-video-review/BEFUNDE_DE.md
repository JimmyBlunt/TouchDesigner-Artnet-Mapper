# LED2.mov: Eingangsprüfung vor optischer Auswertung

Stand: 2026-09-13. Quelle ausschließlich gelesen, keine Videokopie angelegt. Bezug ist `measurements/gico-td-camera-001/run.json` (native TouchDesigner-Ausgabe, fester 30-FPS-Transport; wechselnde 15/25/30-FPS-Bildinhalte). Keine Hardware angesprochen.

## Datei und begrenzte Integritätsprüfung

- Quelle `E:/LED2.mov`, 2.112.502.772 Bytes.
- SHA-256 `8f65f06de4c2fa991e8aed9c2f332006d3e87edaaa1524c7e4aad988cb5d64b3`.
- Kamera laut QuickTime-Metadaten: iPhone 13. Aufnahmezeit `2026-09-12T23:40:19+1000`. Nutzerangabe: Slo-Mo mit 240 FPS.
- 1080 × 1920 Pixel, 44.534 Frames, 30 **Wiedergabe**-FPS, 1.484,4667 s Wiedergabe (24:44).
- Videospur: Zeitskala 2400, alle 44.534 Samples mit Dauer 80 Ticks. Movie-Zeitskala 44100. Video-Edit-List enthält einen einzigen Eintrag mit Medienrate 1.
- Die Dateiatome reichen exakt bis Dateiende. 18 erste Seek-Stichproben einschließlich 0,2 s vor Ende waren decodierbar; zusätzlich 231 grobe Licht-Stichproben und 45 Rand-Stichproben erfolgreich. **Kein vollständiger Decode-/Bitstream-Integritätstest.**
- Keine `AGENTS.md` im Repo oder den geprüften übergeordneten Verzeichnissen gefunden. OpenCV 5.0.0/FFMPEG-Backend verwendet; `ffprobe` war nicht auf PATH.

## Entscheidender Befund: keine globale ×8-Zeitumrechnung

Die Datei besitzt eine konstante 30-FPS-Wiedergabespur. Die Aufnahmegeschwindigkeit kann deshalb nicht aus `CAP_PROP_FPS` allein bestimmt werden. Eventuelle SloMo-Rampen sind in dieser Ausgabe bereits in den Bildern bzw. deren Auswahl umgesetzt; die Edit-List liefert keine rekonstruierbare Rampenkurve.

Visuell überprüfte schwarze Abschnitte:

| Abschnitt | Schwarze Stichproben in Wiedergabesekunden | Benachbarte leuchtende Stichproben |
|---|---:|---:|
| Erste lange Pause | 612 bis 626 | 610 und 628 |
| Zweite lange Pause | 1132 bis 1146 | 1130 und 1148 |
| Letzte kurze Pause | 1474 und 1476 | 1472 und 1478 |

Die ersten beiden Pausen sind jeweils ungefähr 16 Wiedergabesekunden lang; ihr Abstand beträgt 520 s. Das passt zu den zwei geplanten 2-s-Schwarzpausen im Abstand von 65 realen Sekunden bei **achtfach verlangsamter Wiedergabe im mittleren Bereich**. Aus dieser groben Zuordnung ergibt sich dort vorläufig `video_pts ≈ 8 × test_elapsed − 93 s`, mit noch etwa ±1 s Wiedergabeunsicherheit an den Übergängen. Das ist eine Orientierung zum Auffinden der Phasen, **keine fertig kalibrierte Messzeitachse**.

Die letzte Pause liegt nur ungefähr 342 Wiedergabesekunden nach der zweiten, obwohl der Testplan erneut 65 reale Sekunden vorsieht. Damit passt eine unveränderte ×8-Umrechnung nicht bis zum Ende. Zusammen mit dem kurzen Schwarzabschnitt spricht dies für einen wieder normal bzw. schneller abgespielten Endbereich. Eine alternative Unterbrechung/Bearbeitung lässt sich allein mit Stichproben nicht endgültig ausschließen. Auch die Kalibrierung am Anfang passt nicht zur mittleren linearen Zeitachse.

Nach der letzten schwarzen Stichprobe leuchtet das Panel großflächig cyan/weiß (1478 s und später); anschließend bewegt sich die Kamera. Dieses Nachlaufbild gehört nicht zum eigentlichen Gray/CRC-Testmuster und darf nicht als zusätzliche Testframes gewertet werden. Seine Ursache ist aus dem Video allein offen.

## Passende nächste Auswertung

1. Die 21 Einzelleuchten am Anfang neu lokalisieren und zeitlich zuordnen; Kamerageometrie, Marker-Modell und Offset der alten `LED Full.mov` nicht übernehmen.
2. Schwarzgrenzen framegenau bestimmen. Den konstant verlangsamten Mittelteil separat auswerten und Anfang/Ende stückweise kalibrieren. Keine pauschale Multiplikation der Container-FPS mit acht für die gesamte Datei.
3. Vor einer langen Auswertung kurze Ausschnitte aus jeder Phase und dem Übergang am Ende prüfen: direkte CRC-Decodierbarkeit, eindeutige Frame-IDs, Bildduplikate und Zeitrampen. Sender-Zeitdaten nur nach der bildbasierten Decodierung zum Abgleich einsetzen; erwartete Bildnummern dürfen keine unlesbaren LEDs ersetzen.
4. Den zentralen ×8-Bereich kann man voraussichtlich mit der höheren zeitlichen Auflösung nutzen. Für den beschleunigt exportierten Endbereich darf keine lückenlose 240-FPS-Abnahme versprochen werden: beim Rendern könnten Kameraframes entfernt worden sein. Gegebenenfalls reicht eine separate Auswertung des vollständig verlangsamten Teilabschnitts der 30-FPS-Phase; für eine volle 60-s-Abnahme wäre dann die unmodifizierte 240-FPS-Quelle bzw. ein durchgehend verlangsamter Export nötig.
5. Eingereichte TD-Batches können dieselbe optische ID mehrfach enthalten. Neue Lichtbilder anhand eindeutiger IDs zählen, nicht anhand der Anzahl eingereichter Pakete. Die native Testquelle ersetzt das Material/den Effekt; das Ergebnis misst diesen TD-Router/UDP/GICO-Pfad, keine beliebige Effekt-Renderlast.

Bis hier wurde **keine optische FPS-Ergebniszahl** ermittelt. Eine vollständige teure Auswertung wurde ausdrücklich noch nicht gestartet.

## Reproduktion

`inspect_video.py` erzeugt Metadaten, Hash und erste Kontaktübersicht. `inspect_light_timing.py` erzeugt grobe Licht-Stichproben; mit `--boundaries` die engeren Rand-Stichproben und zweite Kontaktübersicht. Die Schwelle zählt blaue Pixel im Panelbereich und dient nur dem Auffinden der später visuell überprüften Schwarzpausen; sie ist kein allgemeiner LED-Detektor (insbesondere weißes Licht kann dabei den Wert null ergeben). Quellvideo und ROI sind für diese konkrete Aufnahme festgelegt.
