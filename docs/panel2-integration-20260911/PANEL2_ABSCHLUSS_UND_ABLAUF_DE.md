# Panel 2: Abschluss und Ablauf zum Nachmachen

Panel 2 liegt oben rechts, ist 30 x 30 cm gross und nach dem bestaetigten Referenzbild ausgerichtet. 680 LEDs besitzen gueltige 3D-Koordinaten. 58 bleiben fehlend und werden in der Ausgabe schwarz geschaltet. Ob eine fehlende LED verdeckt war, bleibt unbekannt.

## Warum lagen die weissen Punkte dahinter?

`Add to Draft` fuegt einen Scan als neues Objekt hinzu. Es ersetzt keine alten LEDs. Die 256 regelmaessigen Punkte oben rechts waren eine alte 16-x-16-Vorlage im Sammelobjekt `Active snapshot (ungrouped)`. Sie wurden zuerst bewusst erhalten, waehrend wir den neuen Scan ausrichteten. Der Austausch war deshalb noch nicht abgeschlossen.

Jetzt wurden ausschliesslich die alten Quellen 1184–1439 dieser Vorlage entfernt. Die uebrigen Vorlagen fuer spaetere Panels bleiben stehen. Panel 2, Panel 1 und die Seitenpanels wurden bei diesem Entfernen nicht bewegt oder umnummeriert. Rohscans bleiben archiviert.

## Die Arbeitsschritte im Projekt

1. **Guided Scan:** eine eigene Sitzung mit richtiger LED-Anzahl, Controller und Startuniversum anlegen. Kamera pruefen, Vorschau schliessen, `Check Scan Plan` lesen. Erst dann selbst den Scan starten.
2. **Weitere Ansichten:** Kamera nur zwischen den Aufnahmen bewegen. Anschliessend 3D berechnen und `Fehlende Bereiche` ansehen.
3. **Add to Draft:** die gueltigen Messpunkte in den Layout-Entwurf aufnehmen. Luecken behalten ihre urspruenglichen LED-Adressen.
4. **Layout 3D:** das richtige Objekt auswaehlen und seine Position, Drehung und Skalierung einstellen. Eine Spiegelung veraendert die Orientierung; die urspruenglichen Messwerte bleiben erhalten. Die Bildansicht entscheidet, was rechts/links und im Uhrzeigersinn bedeutet. Eine Weltachsen-Drehung entspricht bei einem schon gedrehten Scan nicht automatisch dem Addieren von 90 zu einem einzelnen lokalen Eulerfeld.
5. **Alte Vorlage ersetzen:** nur den eindeutig zugehoerigen Vorlagenbereich entfernen. Dafuer gibt es derzeit keinen geeigneten Bereich-entfernen-Dialogknopf; dieser Schritt erfolgte mit dem geprueften Skript `tools/retire_panel2_template_20260911.py`. Den ganzen Sammelbereich zu loeschen waere falsch. Die Entwurfs-Aenderung ist ueber Layout-Undo rueckgaengig.
6. **Ausgabe vorbereiten:** Controller/Port-Zuordnung und die gesamte Adresskapazitaet pruefen. Die Entwurfs-Zuordnung allein aendert noch keine aktiven Routen. In diesem Schritt musste deshalb auch die interne Kapazitaet erweitert werden.
7. **Aktive Daten uebernehmen:** bereinigte XYZ-Daten und Maske ueber den geprueften Prepare/Apply-Ablauf uebernehmen. Die bestehenden Effekt-UVs bleiben erhalten; neue Panel-2-UVs folgen derselben Rueckwand-Projektion wie Panel 1. Erst ein gesonderter Start der LED-Ausgabe sendet Netzwerkdaten.

## Konkrete Zuordnung

| Eigenschaft | Wert |
|---|---|
| Controller | BACK_PANEL_249 / 10.0.0.249 |
| Physischer Ausgang | 2 |
| Panel-LED-Indizes | 0–737 |
| Interne Quellen | 3744–4481 |
| Zielstart im Controller | 340 Pixel, also nach zwei Universen |
| Panel-Universen | 122–126, Art-Net-Wire-Adressen |
| Vollstaendiger Controller-Frame | 120–126, insgesamt sieben Universen |
| Panel 1 | unveraendert auf 120–121 |

Die 738 Adressplaetze duerfen nicht auf 680 zusammengeschoben werden: sonst verschieben sich nachfolgende LEDs. Die gesamte interne Kapazitaet betraegt jetzt 4482. Davon sind 367 Plaetze inaktiv: 256 entfernte Vorlagenplaetze, 53 alte Panel-1-Luecken und 58 Panel-2-Luecken. Die uebrigen alten Vorlagen gehoeren zu noch nicht ersetzten Panels; diese Zahl bedeutet nicht, dass bereits alle Panels physisch gescannt wurden.

## Nachweise und Grenzen

Die reine Paketberechnung bestaetigt, dass alle 58 fehlenden Panel-2-LEDs und die unbenutzten Zielkanaele schwarz sind. Panel-1-Pakete und Seitenpanel-Pakete bleiben identisch. Die native 3D-Vorschau zeigt keine alte Vorlage mehr hinter Panel 2. Der aktive XYZ-/UV-/Maskenpfad und Show-Renderer haben die erweiterte Kapazitaet; fehlende Punkte sind auch in der Vorschau unsichtbar. Netzwerk-Ausgabe bleibt aus; kein optischer Hardwaretest in diesem Schritt, da der Benutzer Panel 3 anschliesst.

Ein Fehler im Router-Neuaufbau wurde behoben: der ausgefuehrte Builder erhaelt jetzt seinen echten `__file__`-Pfad statt des TouchDesigner-DAT-Pfads. Ein fehlgeschlagener erster Versuch und die Wiederherstellung der alten Konfiguration sind dokumentiert. Der Neuaufbau erhaelt jetzt auch den Guided-Scan-Ausgabeschutz. Der zweite Uebernahmeversuch war erfolgreich.

Die unabhaengige 2D-Fixture-Anordnung wurde nicht neu projiziert; aktive Uebernahme erfolgte explizit im 3D-Modus mit Erhalt der bisherigen Effekt-UVs. Alte Kalibrierungs-/Kapazitaetsannahmen wurden im zugehoerigen Code und den Regressionstests angepasst. Die Testmuster lesen jetzt die aktive UV-Tabelle; `rear` und der Chase-Bereich bis 4481 sind verfuegbar. Rows/columns sind ausdruecklich 24 UV-Teststreifen, kein Nachweis physischer Reihen. Die erzeugten Show-Callbacks und die Preview verwenden den aktuellen Repository-Pfad, damit kein alter Code aus TouchDesignerLocal geladen wird.

139 gezielte Regressionstests bestanden (`tests-final.txt`). Native Datenpruefung: 4482 Samples in Show und Vorschau, sieben Controller-Frames, alle 58 Panel-2-Fehlstellen auch im Kalibrierungsmuster schwarz, keine Operatorfehler, null gesendete Pakete. Das Laden der Callback-Quellen wurde in der laufenden Anwendung geprueft; der gespeicherte TOE-Stand wurde in diesem Schritt nicht neu geladen.

Fertiger Stand: `PixelblazeMapper_PANEL2_COMPLETE_20260911.1.toe`, Speicherbericht und SHA-256 in `saved-project.json`. Der zuvor gespeicherte `PixelblazeMapper_PANEL2_DRAFT_CLEAN_20260911.1.toe` bleibt als vollstaendige Rueckkehrmoeglichkeit erhalten. Layout-Undo betrifft nur den Entwurf. Der partielle Active-Apply-Revert wurde fuer diesen kombinierten Kapazitaets-/Routing-/Mapping-Wechsel geleert, damit er nicht nur einen Teil des Gesamtvorgangs zuruecksetzt. Fuer die vollstaendige Rueckkehr den vorherigen Projektstand laden; Snapshot-Daten sind zusaetzlich im Dokumentationsordner archiviert.

Panel 3 ist vorgemerkt: direkt unter Panel 1, zweite Reihe links, ebenfalls 30 x 30 cm. LED-Anzahl und Anschluss werden vom Benutzer noch angegeben.
