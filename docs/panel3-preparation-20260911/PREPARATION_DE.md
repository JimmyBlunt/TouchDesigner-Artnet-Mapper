# Panel 3: Vorbereitung

Benutzer: 880 LEDs, Controller 249, unter Panel 1, gleiche Groesse 30 x 30 cm. Hinzufuegen, Ausrichten und Entfernen moechte der Benutzer diesmal selbst in den Dialogen versuchen.

GET /api/config bestaetigt Ausgang 3 (id2, GPIO25), 880 LEDs, eingeschaltet, Start U126. Ausgang 2 bleibt bei 738 LEDs und Start U122. Damit ueberlappen beide auf U126 ab Kanal1; betroffen sind die letzten58 LEDs von Panel2 und die ersten58 von Panel3. Keine automatische Hardwareaenderung, keine neue Scan-Sitzung und kein Kamerastart vorgenommen.

Vorgeschlagene Korrektur: nur Ausgang3 auf U127 setzen, Anwenden und dauerhaft speichern. Dann erneut auslesen. Panel3 verwendet U127–132, der komplette Controller-Frame umfasst U120–132 (13 Universen); ausserhalb der gescannten LEDs muss der Scan schwarz senden. Im Scan waeren die lokalen LED-Indizes0–879. Panel2 und seine Scandaten bleiben unveraendert.

## Bestaetigte Korrektur und vorbereitete Sitzung

Der Benutzer hat Ausgang 3 auf U127 geaendert. Erneutes Auslesen bestaetigt U127 und dauerhaft gespeicherte, mit der aktiven Konfiguration uebereinstimmende Einstellungen (controller-corrected.json). Die oben dokumentierte U126-Ueberlappung ist damit behoben. pending-panel3.json bleibt als historischer Ausgangszustand erhalten; ready-panel3.json beschreibt den aktuellen Stand.

Eine eigene Sitzung fuer BACK_PANEL3_880_249 und der Ordner Scans/back_panel3_880_249_20260911_fullscan sind vorbereitet. LED-Indizes 0-879, Panel U127-U132, vollstaendige Scan-Frames U120-U132 mit schwarzen anderen Slots. Helligkeit 9,2 Prozent aus der bestehenden Benutzereinstellung uebernommen. Der Scanplan wurde berechnet, Kamera und Scan wurden nicht gestartet. Aktive Geometrie, Mapping und normale Ausgangsrouten bleiben unveraendert. Kameraausschnitt fuer Panel 3 ist noch vom Benutzer zu pruefen.

Hinzufuegen, Ausrichten und Entfernen von Vorlagen fuer Panel 3 fuehrt der Benutzer spaeter selbst mit Anleitung aus. Die gewuenschte Fortschrittsanzeige mit geprueften/gesamten/erkannten LEDs ist weiterhin offen; sie wurde in dieser Vorbereitung nicht implementiert.

Checkpoint: PixelblazeMapper_PANEL3_SCAN_READY_20260911.1.toe; SHA-256 siehe save.json. Gespeichert mit ausgeschaltetem Sender und ohne Operatorfehler; kein erneutes Laden getestet.
