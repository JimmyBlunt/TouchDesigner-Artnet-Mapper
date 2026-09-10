# Fortschritt pro Scan-Ansicht

Im Guided-Scan-Dialog steht unter START SCAN / NEXT VIEW ein eigener Fortschrittsbereich mit Balken, auch auf den anderen Registern:

- Aktuelle Original-LED-ID und Position in der Scanreihenfolge.
- Gepruefte / gesamte LEDs, erkannt, nicht erkannt und Prozent.
- Nicht erkannt = abgeschlossene Pruefungen minus Erkennungen. Ungepruefte LEDs und abgebrochene Einzelpruefungen zaehlen nicht als Misserfolg.
- Nach 100 Prozent folgen Bewegungskontrolle und Speichern mit eigenem Status. Bei Fehler oder Abbruch bleibt der letzte bestaetigte Stand erhalten.
- Jede neue Ansicht beginnt bei null; eine neue Acquisition entfernt den alten Scanstatus. Die Mehransichten-Abdeckung bleibt separat.

Die Werte stammen aus dem Worker. Die aktuelle Position wird vor dem Detektoraufruf gemeldet; der Supervisor uebersetzt interne Indizes anhand der Auswahlreihenfolge zu Original-IDs. Updates nutzen den bestehenden 0,5-Sekunden-Poll. Kein zusaetzliches Kamera-Lesen und keine Aenderung an Erkennung, Routing oder Ausgabefrequenz. Endzaehler stehen auch in result.json.

73 Offline-Tests bestanden: test_scan_capture_progress, test_scan_capture_progress_worker, test_scan_capture, test_guided_scan_live und test_scan_workflow_ux. Abgedeckt sind fehlende Erkennungen, Abbruch, Fehler, Bewegungskontrolle, unsortierte Original-IDs, Statuspersistenz und Dialogrechtecke. Hardware ist dabei simuliert.

Im laufenden TouchDesigner installiert, ohne den vom Benutzer bereits gestarteten Kameraprozess zu verlieren. Operatorfehler: keine; Live-Sender aus. Anzeige: 0 / 880. Der erste echte Scan mit dieser Anzeige steht noch aus. Checkpoint und SHA-256: progress-save.json. Erneutes Laden wurde nicht getestet.

CAPTURE VIEWS waehlt nur die Aufnahmeseite. Danach CHECK CAMERA, Vorschau pruefen, CLOSE CAMERA, CHECK SCAN PLAN und START SCAN / NEXT VIEW. Panel 3: 880 LEDs, IDs 0-879, Controller 10.0.0.249, U127-U132; vollstaendiger Scan-Frame U120-U132.
