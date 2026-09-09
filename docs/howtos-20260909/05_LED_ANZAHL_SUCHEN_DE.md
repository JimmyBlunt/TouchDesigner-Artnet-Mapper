# Die letzte LED finden

1. Guided Scan → **NEW CAPTURE (NO LAYOUT)** öffnen.
2. IP, lokales Netzwerkinterface, Startuniversum und vorläufige LED-Anzahl für den betreffenden Anschluss eintragen. Die Hardware muss denselben Universumsstart verwenden. Es wird keine Controllerkonfiguration übertragen.
3. **LED SEARCH / FIND LAST LED** neben CREATE ACQUISITION öffnen. Dafür muss noch keine neue Scan-Sitzung erstellt werden.
4. Zieladresse und Universumsbereich oben prüfen. Die Helligkeit kommt aus dem Guided-Scan-Regler (1–10 %).
5. Unter Selected LED eine **lokale, nullbasierte** Zahl eingeben. SHOW 30s startet den Test: vorherige LED grün, gewählte LED weiß, nächste LED rot. Alles andere innerhalb des angezeigten Testbereichs ist schwarz.
6. Mit −10/+10 grob, −1/+1 fein suchen. Jeder Schritt startet einen neuen 30-Sekunden-Test. STOP / BLACK beendet ihn. Keine automatische Animation danach.
7. Beispiel: 201 grün, 202 weiß, 203 rot angefordert, aber nur grün/weiß sichtbar → 202 ist ein Kandidat für die letzte LED, also **203 LEDs insgesamt**. Noch einen Schritt prüfen: bei 203 nur 202 grün sichtbar. Defekte LEDs, Unterbrechungen oder eine zu kleine Hardware-Pixelanzahl können dasselbe Bild verursachen; physische Kontrolle bleibt nötig.
8. Ermittelte Anzahl anschließend selbst in der Controller-Hardware und in NEW CAPTURE eintragen. Erst dann CREATE ACQUISITION und CHECK SCAN PLAN. Der Test ändert weder Scananzahl noch Layout selbständig.

Die vorläufige Anzahl wird für diesen Test auf ganze 170-Pixel-Universen aufgerundet. Bei 450 ab U122 ist der Bereich U122–124, lokale IDs 0–509. Ein Nachbar außerhalb dieses Bereichs wird nicht gesendet und im Status entsprechend bezeichnet. Nur nach Prüfung der tatsächlichen Portreserve den Bereich durch eine größere vorläufige Anzahl erweitern: sonst könnte der nächste Port betroffen sein. Die UI kann unbekannte Hardwaregrenzen nicht erkennen.

Live-/Kalibrierungsausgabe vorher ausschalten. Während der Suche blockiert die gemeinsame Ausgabesperre einen Scan bzw. den kooperierenden Live-Sender. Fremde Programme werden dadurch nicht gesperrt. Die Kamera wird nicht benutzt. Fenster schließen alleine beendet den Test nicht sofort: STOP benutzen oder maximal 30 Sekunden abwarten. Bei Netzwerkverlust ist die Zustellung des abschließenden Schwarzbildes nicht garantiert.
