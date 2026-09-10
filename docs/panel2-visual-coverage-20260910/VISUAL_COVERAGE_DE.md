# Sichtbare fehlende Bereiche in Guided Scan

Neuer Button FEHLENDE BEREICHE ANZEIGEN in Guided Scan und FEHLENDE BEREICHE im Result Review. Das Fenster zeigt die gespeicherten gemessenen LED-Punkte aus jeder Kameraansicht und bietet Vorherige/Naechste Ansicht, Meiste Hinweise, Refresh und Zurueck zum Scan. Es werden keine Fotos vorausgesetzt und keine Kamera-/LED-Ausgaben gestartet.

Farben: Tuerkis = rekonstruiert mit mindestens drei Beobachtungen; Gelb = rekonstruiert mit weniger als drei; Orange = beobachtet, aber nicht rekonstruiert. Ohne vorhandenes 3D-Ergebnis bezeichnen Tuerkis/Gelb ausschliesslich Beobachtungshaeufigkeit. Violette Ringe und gestrichelte Linien verbinden ausschliesslich gemessene direkte Nachbarstellen von nie erkannten LED-Luecken. Sie sind kein Beweis fuer deren Position und erzeugen keine fehlenden Messpunkte.

Nachbarhinweise nur fuer zusammenhaengende Luecken bis acht LEDs, bei zwei unmittelbaren beobachteten Nachbarn in derselben Ansicht und maximal0,15 normalisiertem Abstand. Kettenfaltungen bleiben moeglich; UI kennzeichnet Hinweise ausdruecklich. Nicht eingrenzbare LEDs werden separat gezaehlt.

Aktueller Panel-2-Stand: neun Ansichten,680/738 rekonstruierte LEDs,35 beobachtet ohne3D und23nie gesehen. Fuer12der23 gibt es begrenzte Nachbarhinweise,11 bleiben unlokalisiert. Ansicht1 zeigt neun orange Punkte und Nachbarhinweise fuer acht LEDs. Besonders rechts mittig liegen398/406/414/422 sowie Nachbarn der Luecken404–405,412–413,420–421,428–429. Ansicht7 zeigt neun weitere orange Punkte vor allem im oberen Drittel. Die Empfehlungen beziehen sich auf die jeweilige gespeicherte Blickrichtung, nicht auf behauptete absolute Montagepositionen.

Die Daten stammen aus den originalen CSVs und dem geprueften Kandidaten. Pfade/Dateigroessen/Zeilenzahlen und Zahlenwerte sind begrenzt und validiert; Sitzungsidentitaet und Ergebnisreport muessen passen. Jede Anzeige kann explizit aktualisiert werden; Blaettern und Bild-Cook lesen keine Dateien. Bilder werden pro Datenrevision/Ansicht zwischengespeichert.

Orientierung: MariMapper normalisiert U auf die Sensorbreite und V auf ein quadratisches Bildfeld mit Hoehenausgleich. Deshalb quadratische Darstellung; V=0 oben. Der ScriptTOP dreht die NumPy-Zeilen fuer die TOP-Konvention um. Native Screenshots bestaetigen die Darstellung; ein echter Mausklick wechselte von Ansicht1zu2, danach Rueckkehr zur empfohlenen Ansicht1.

51 Tests aus Visual-Coverage, Workflow und Bibliothek bestanden. Native Installation ohne Operatorfehler; Mapping, UVs, Routing, Entwurf, Aufnahmeauswahl, Scanordner und bestehende Ansichten unveraendert. Kein Scan oder Kamerastart. Neuer TOE-Checkpoint gespeichert, waehrend der Nutzeranleitung nicht erneut geladen. Originale Aufnahme-/Ergebnis-JSON/CSV-Dateien und SHA-256-Belege sind mit versioniert.

Die zuvor vorgemerkten allgemeinen Coverage-Status- und Fortschrittsanzeigen bleiben separate spaetere UI-Punkte.
