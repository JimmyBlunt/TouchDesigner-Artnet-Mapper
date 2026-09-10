# Scan-Tempo: Anzeige und Diagnose

Benutzervergleich: frueher 3-4 LEDs/s in der MariMapper-Konsole. Kurze passive Beobachtung dieser Aufnahme: 12 gepruefte LEDs in 8,14 Sekunden, also 1,47 LEDs/s; davon 11 erkannt. Das ist kein Durchschnitt ueber die gesamte Aufnahme.

Die native Konsole nutzt tqdm mit smoothing=0 und zaehlt sowohl DETECT als auch SKIP. Sie zeigt somit kumulativ bearbeitete LEDs/s. Der neue Dialogzusatz zeigt dagegen die aktuelle Rate ueber ein gleitendes Zeitfenster von bis zu zehn Sekunden; nach zwei Sekunden beginnt die Anzeige. Nur bestaetigt gepruefte LEDs zaehlen. Bei Stillstand sinkt die aktuelle Rate; bei Abschluss bleibt die letzte Rate stehen. Neue Aufnahmen setzen die Messung zurueck. Spaetes Aktivieren erfindet keinen Durchschnitt fuer die bereits vergangene Aufnahme.

Die Anzeige beobachtet ausschliesslich bereits gespeicherte Statuszaehler und verwendet eine monotone Uhr. Keine Aenderung an Kamera, Worker, Netzwerk oder Scan-Timing. 25 Tests fuer Fortschritt/Rate und Dialogverhalten bestanden. Native Anzeige ohne Operatorfehler geladen; beim Laden war die erste Aufnahme bereits abgeschlossen: 880 geprueft, 833 erkannt, 47 nicht erkannt. Echte laufende Rate ist bei der naechsten Aufnahme zu beobachten.

## Architektur und offene Zeitmessung

TouchDesigner startet separate Supervisor- und Kameraprozesse. Das 0,5-Sekunden-UI-Polling uebertraegt Status und Heartbeats; es gibt nicht jede LED frei. Gemeinsame CPU-/GPU-Last ist dadurch nicht ausgeschlossen und wurde hier nicht vermessen.

Read-only Review des Supervisorloops zeigt einen zusaetzlichen Warteweg: last_send wird aus now vor parent.poll/blockierendem send uebernommen. Ein periodischer Refresh kann dadurch zu frueh faellig erscheinen, in die Sendepause gehen und ein inzwischen eingegangenes LED-Kommando zusaetzlich um etwa einen 50-ms-Takt verzoegern. Kandidat fuer die Korrektur: tatsaechlichen last_transmit verwenden und die Faelligkeit nach dem Poll mit frischer monotoner Zeit pruefen. Diese Aenderung wurde hier nicht vorgenommen und ihr Anteil an der beobachteten Verlangsamung ist nicht gemessen.

Weitere zu trennende Zeiten: Kamera.read, Ein-/Ausschaltbestaetigung im Bild, Darstellung und adaptive Suchfrist. Keine pauschale Schuldzuweisung an TouchDesigner oder die Kamera. Die vom Benutzer berichteten frueheren Einstellungen/Backend/Version sind fuer einen direkten Vergleich noch nicht belegt.
