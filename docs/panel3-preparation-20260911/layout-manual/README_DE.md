# Panel 3: manueller Layout-Schritt

Der Benutzer hat Pannel 3 als Objekt 7 mit 880 Punkten und internen Source-IDs 4482–5361 hinzugefügt. Der Snapshot bewahrt den Entwurf vor der manuellen Ausrichtung. Rotation und Translation stehen auf 0, Skalierung auf 1.

Nächster angeleiteter Schritt: Scale X/Y/Z gemeinsam auf 0.06 setzen und SET TRANSFORM drücken. Dies ist eine grobe Verkleinerung zur Bearbeitung, keine abgeschlossene Kalibrierung auf 30 × 30 cm. Die endgültige Größe wird nach dem Ausrichten geprüft.

## Gleichmäßige Skalierung bestätigt, Drehung vorbereitet

Nativ geprüft: ausgewähltes Objekt `Pannel 3`, Skalierung `[0.06, 0.06, 0.06]`, Rotation/Translation noch jeweils 0, keine Operatorfehler. Die Ausgangsmessungen wurden offline per SVD auf Ebenheit geprüft: Singulärwerte `[40.98996578, 39.39452402, 0.80518256]`, Verhältnis kleinster/mittlerer Wert 0.02044. Die Punkte sind weitgehend eben; Messabweichungen werden erhalten.

Für eine erste Ausrichtung wird die Flächennormale auf die Y-Achse der bestehenden Rückwand gelegt. In der Ebene wird ein Rechteck mit geringer Hüllfläche gesucht (0.25°-Schritte, 0.1 % Flächentoleranz); Vorzeichen und Orientierung folgen möglichst der letzten Kameraansicht `capture-aca36f5f-4643-45fb-b372-b5a8502a0dc7/view.csv`. Summe der beiden Bildachsen-Korrelationen: 1.9631. Daraus ergeben sich vorgeschlagene Euler-Winkel X/Y/Z: **31.239°, −80.968°, −153.633°**. Rechte-Hand-Konvention X, dann Y, dann Z wie im Layout-Transform. Keine Drehung wurde durch den Assistenten angewendet.

Die Übereinstimmung mit der Kamerasicht bestätigt noch nicht die physische Orientierung des LED-Musters. Nach manueller Eingabe und SET TRANSFORM ist die Lage am Panel zu prüfen. Die endgültige Größe muss am bestehenden Panel-1-Maßstab ausgerichtet werden: dort entspricht das 30-cm-Panel einer LED-Hüllhöhe von 0.16875 Layout-Einheiten, nicht 0.30. Aktuelle Messausdehnung in der vorgeschlagenen Ausrichtung: Höhe 4.56884, Breite 4.62448 Scan-Einheiten.
