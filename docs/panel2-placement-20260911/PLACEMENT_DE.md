# Panel 2 oben rechts

Benutzer bestaetigt: Panel 2 sitzt in der rechten oberen Ecke, bezogen auf die zuvor festgelegte Frontansicht. Zielmasse wie Panel 1: 30 x 30 cm.

Die vorhandene rechte obere Layout-Vorlage umfasst Quellen 1184–1439 mit Mittelpunkt (0.9, 1.0, 0.4). Panel 1 sitzt links bei (0.9, 1.0, 0.6). Beide verwenden dieselbe normalisierte LED-Huelle mit maximaler Kantenlaenge 0.16875. Dies ist keine metrisch kalibrierte Raumregistrierung.

`tools/place_panel2_upper_right_20260911.py` berechnet eine starre Drehung und einheitliche Skalierung. Eine Hauptkomponentenanalyse bestimmt die Scanebene, ein enges umschliessendes Rechteck die Achsen. Die Kameraperspektive mit den meisten rekonstruierten Punkten (614) bestimmt die vorlaeufige Oben-/Rechts-Richtung. Die Orientierung muss der Benutzer visuell pruefen. Keine Verformung, Spiegelung oder Abflachung der Messpunkte.

Alle 680 Bindungen, Rohmessungen und 58 Fehlmarkierungen bleiben erhalten. Andere Objekte und Routen bleiben unveraendert. Die bisherige regelmaessige Layout-Vorlage wurde ebenfalls erhalten; ihre spaetere Ersetzung/Quellenzuordnung ist noch separat zu erledigen. Die isolierte Frontvorschau zeigt nur die beiden realen Scans.

Pruefungen: korrekte Zielgrenzen; positiver Rotationsdeterminant; analytischer und modellbasierter Transform identisch; andere Objekte/Scans/Routen/IDs unveraendert; JSON-Roundtrip und Undo/Redo erfolgreich. Native Uebernahme als ein Layout-Commit, aktive Tabellen per Hash unveraendert, Sender aus, keine Operatorfehler. Der Layout-Viewer wurde auf eine Frontansicht der beiden oberen Panels eingestellt.

Gespeichert als `PixelblazeMapper_PANEL2_UPPER_RIGHT_20260911.1.toe`, Hash im Speicherbericht. Kein Neuladen in diesem Schritt. `front-preview.png` ist eine aus den beiden Entwurfsobjekten erzeugte Vergleichsansicht. Die naechste Benutzerpruefung betrifft die Drehrichtung; danach folgt die explizite Behandlung der alten Vorlage und der Controller-Zuordnung.
