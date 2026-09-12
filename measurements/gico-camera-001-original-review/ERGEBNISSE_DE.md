# GICO: optische Auswertung der Originalaufnahme

## Ergebnis

Die Aufnahme spricht deutlich dafür, dass der GICO in diesem geprüften Aufbau **30 neue Bildzustände pro Sekunde** darstellen kann. Im ausgewerteten 30-FPS-Fenster wurden sämtliche **1.785 aufeinanderfolgenden Bildnummern von 8 bis 1.792** mindestens einmal optisch erkannt: geschätzt **29,991 neue Bildnummern/s**, keine Lücke innerhalb dieser ID-Folge.

Das ist eine optische Beobachtung inklusive begrenzter Prüfsummenrekonstruktion, noch keine elektrische Messung und keine Abnahme aller drei Panels oder einer beliebigen größeren LED-Konfiguration. Nur das gefilmte untere Panel wurde ausgewertet; side_3 bleibt eine vorläufige Zuordnungsbezeichnung. Alle drei Testports wurden gleichzeitig mit dem vorbereiteten 24-Universen-Strom beliefert.

| Gesendet | Einmal oder öfter erkannte IDs | Geschätzte neue IDs/s, mindestens ein Kamerabild | IDs mit mindestens zwei aufeinanderfolgenden Kamerabildern | Entsprechende konservative Beobachtung/s |
|---|---:|---:|---:|---:|
|15 FPS|877|14,730|877|14,730|
|25 FPS|1.488|24,987|1.418|23,837|
|30 FPS|1.785|29,991|1.192|20,209|

Die beiden rechten Spalten zählen ausschließlich mehrfach bestätigte Beobachtungen. **20,209 ist deshalb keine gemessene GICO-Ausgabegrenze.** Bei 30 LED-Bildern/s stehen mit der 60-FPS-Kamera nur etwa zwei Aufnahmen pro Bildzustand zur Verfügung. Sobald eine davon beim Übergang uneindeutig ist, fällt die ID aus der strengen Zweibildzählung, obwohl sie einmal korrekt gelesen wurde. Im 30-FPS-Abschnitt betrifft das 593 IDs. Bei 25 FPS wurden 70 IDs nur einmal beobachtet; eine weitere ID innerhalb der erfassten Folge blieb unbeobachtet.

Im 15-FPS-Abschnitt scheiterte die Bildregistrierung bei Videozeit 91,588–92,588 s für 61 Aufnahmen. Das Kontrollbild bei 92 s zeigt stark veränderte Beleuchtung/Schatten. Dieser Zeitraum wurde verworfen und erklärt die etwa einsekündige Auswertungslücke; daraus folgt kein nachgewiesener Controllerstillstand.

## Aufnahme und Zeitbasis

Original: `E:/LED Full.mov`, 495.727.022 Byte, 1080×1920, 17.349 Kamerabilder, 289,323 s, nominell 59,964 FPS. SHA256: `afb62ceecff3951e239306e075e8a0a1f94f7bdcb5dc2d828c0c935886940460`.

Die Kamera-Zeitstempel der ausgewerteten Abschnitte sind streng steigend, Medianabstand etwa 16,667 ms, maximal 18,333 ms. Zeitmaßstab 1; vorläufiger Offset Videozeit = Senderzeit +58,62 s anhand der zwei Schwarzpausen. Je Messabschnitt werden 0,25 s am Anfang und Ende ausgeschlossen, um Phasengrenzen nicht als Codes auszuwerten. Das Original enthält das schwarze Ende des Tests.

Nach dem unabhängigen Decodieren wurde zusätzlich die zeitliche Plausibilität mit den gespeicherten Einreichungszeiten verglichen. Es gibt keine unerwarteten ID-Sprünge in den rekonstruierten Folgen. Die kleinen positiven/negativen Differenzen sind wegen Kamerabelichtung und Offsetunsicherheit **keine Messung der Netzwerklatenz**. Weder Ziel-FPS noch erwartete Sender-ID werden zum Erzeugen, Korrigieren oder Auswählen einer optischen ID verwendet.

## Verbesserung der Auswertung

Die erste Auswertung verwendete eine kleine feste Helligkeitsprobe pro Marker und verwarf jedes unklare Bit. Helle LED-Gehäuse im Tageslicht, Streulicht und kleine Bildverschiebungen führten so auch im Original zu vielen Ablehnungen. Dies war teilweise eine Grenze unserer Auswertemethode, nicht allein eine Frage der WhatsApp-Komprimierung.

Die neue Auswertung richtet jedes Bild anhand statischer Strukturen auf der Platte aus. Ein lokales RGB-Modell nutzt die bekannte Einzelpunkt-Kalibrierung, um den Beitrag einer leuchtenden LED von Umgebungslicht und benachbarten Markern zu unterscheiden. Trainiert wurde pro Marker ausschließlich auf den bekannten Ein-/Aus-Zuständen der Kalibrierung, nicht auf den später gesendeten Bildnummern.

Eine getrennte Kontrolle in anderen Kalibrierbildern bestätigte alle 21 eingeschalteten Marker (kleinster Score 0,920). Kein ausgeschalteter Marker überschritt die feste Einschaltgrenze 0,75 (größter Off-Score 0,474); einzelne blieben ausdrücklich unklar. Diese Kontrolle prüft Einzelmarker, nicht alle möglichen gleichzeitig leuchtenden Kombinationen. Deshalb bleiben CRC-Prüfung, Ablehnungen und zeitliche Mehrfachbestätigung wichtig.

Der ergänzte Decoder erlaubt höchstens drei unlesbare der 20 codierten Bits, davon höchstens zwei Gray-Code-Bits. Mindestens fünf CRC-Bits bleiben direkt beobachtet. Eine Nummer wird nur rekonstruiert, wenn genau ein Codewort mit allen sicher gelesenen Bits übereinstimmt. Mehrdeutige Fälle werden verworfen. Es wird kein bekanntes Bit umgedreht und kein zeitlich erwarteter Wert eingesetzt. Fehler in sicher eingestuften Bits können zusammen mit Erasures dennoch unentdeckt bleiben; eine gültige CRC ist kein absoluter Beweis gegen Mischbilder.

| Abschnitt | Vollständig gelesene CRC-Kamerabilder | Mit begrenzten Erasures rekonstruierte Kamerabilder | Verworfen | Unterschiedliche IDs mit mindestens einer vollständig gelesenen Aufnahme |
|---|---:|---:|---:|---:|
|15 FPS|1.187|1.900|481|410|
|25 FPS|1.100|2.029|439|638|
|30 FPS|1.099|1.883|586|809|

Damit sind im 30-FPS-Abschnitt 976 der 1.785 IDs ausschließlich über begrenzte Erasure-Rekonstruktion belegt. Diese Unterscheidung bleibt in den Rohdaten erhalten. Die lückenlose, zeitlich plausible Folge stärkt die 30-FPS-Beobachtung, ersetzt aber nicht die strengere Abnahme mit schnellerer Kamera.

## Tests und Reproduktion

Drei neue Softwaretestgruppen bestanden: alle 4.096 unveränderten IDs, 81.920 einzelne sichere Bitfehler, Dreier-Erasure-Kombinationen für acht repräsentative IDs sowie Referenz-/Eingabegrenzen. Die Tests versprechen keine fehlerfreie Rekonstruktion bei beliebigen Mischbildern. Laufzeit 5,117 s, Quellenhashes in `decoder-tests.json`.

- `pixelblaze_mapper/gico_optical_erasure.py`: eigenständiger begrenzter Decoder; bestehender strenger Decoder bleibt verfügbar.
- `tools/gico_local_model_probe_20260912.py`: lokale Kalibrierung und getrennte Kontrollbilder für diese Originalaufnahme; feste Pfade/Parameter dokumentieren diesen konkreten Versuch.
- `tools/gico_original_extract_20260912.py`: vollständige Offline-Auswertung mit eingefrorenem Modell; keine Netzwerk- oder Controllerzugriffe.
- `local-analysis/optical-scores.npz`: Rohscores plus Videozeit, Phase, Registrierungsqualität, direkte/rekonstruierte ID und Zahl unklarer Bits für jedes geprüfte Kamerabild.
- `local-analysis/analysis.json`: strenge und erasuregestützte Zweibildauswertung.
- `comparison-summary.json`: expliziter Vergleich zwischen Einbild- und Zweibildzählung; keine stillschweigende Lockerung der ursprünglichen Abnahme.

Die Farbhalo- und globalen Template-Vorversuche wurden wegen Übersprechen bzw. unzureichend binärer Antworten nicht zur finalen Messung verwendet. Ihre Belege bleiben getrennt erhalten. Das vollständige Originalvideo bleibt auf E:; versioniert werden Code, Modelle, ausgewählte Kontrollbilder und Messwerte, keine Kopie der knapp 496 MB großen Aufnahme.

## Weiteres Vorgehen

Für diesen Aufbau gibt es nun einen starken optischen Hinweis auf 30 FPS. Eine Wiederholung nur wegen fehlender WhatsApp-Qualität ist nicht erforderlich. Für die ursprünglich strenge Abnahme mit mindestens zwei bestätigenden Kamerabildern pro ID bleibt eine Aufnahme mit mindestens 120, vorzugsweise 240 FPS sinnvoll; feste Kamera, gesperrte Belichtung und weniger Überstrahlung verbessern die Trennung. Eine gleichzeitige Aufnahme aller drei Panels prüft zusätzlich deren Synchronität.

Der nächste Integrationstest sollte denselben Bildnummernstrom aus der optimierten TouchDesigner-Pipeline verwenden. Der abgeschlossene Lauf prüfte den unabhängigen Sender; dessen Erfolg ist keine bereits ausgeführte TD→GICO-Abnahme. Es wurde während der Videoauswertung kein neuer Hardwarelauf gestartet und keine Controller-Firmware verändert.
