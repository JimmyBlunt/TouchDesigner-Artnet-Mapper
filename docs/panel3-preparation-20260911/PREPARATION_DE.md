# Panel 3: Vorbereitung

Benutzer: 880 LEDs, Controller 249, unter Panel 1, gleiche Groesse 30 x 30 cm. Hinzufuegen, Ausrichten und Entfernen moechte der Benutzer diesmal selbst in den Dialogen versuchen.

GET /api/config bestaetigt Ausgang 3 (id2, GPIO25), 880 LEDs, eingeschaltet, Start U126. Ausgang 2 bleibt bei 738 LEDs und Start U122. Damit ueberlappen beide auf U126 ab Kanal1; betroffen sind die letzten58 LEDs von Panel2 und die ersten58 von Panel3. Keine automatische Hardwareaenderung, keine neue Scan-Sitzung und kein Kamerastart vorgenommen.

Vorgeschlagene Korrektur: nur Ausgang3 auf U127 setzen, Anwenden und dauerhaft speichern. Dann erneut auslesen. Panel3 verwendet U127–132, der komplette Controller-Frame umfasst U120–132 (13 Universen); ausserhalb der gescannten LEDs muss der Scan schwarz senden. Im Scan waeren die lokalen LED-Indizes0–879. Panel2 und seine Scandaten bleiben unveraendert.
