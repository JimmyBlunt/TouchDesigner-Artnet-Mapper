# Panel 3: manueller Layout-Schritt

Der Benutzer hat Pannel 3 als Objekt 7 mit 880 Punkten und internen Source-IDs 4482–5361 hinzugefügt. Der Snapshot bewahrt den Entwurf vor der manuellen Ausrichtung. Rotation und Translation stehen auf 0, Skalierung auf 1.

Nächster angeleiteter Schritt: Scale X/Y/Z gemeinsam auf 0.06 setzen und SET TRANSFORM drücken. Dies ist eine grobe Verkleinerung zur Bearbeitung, keine abgeschlossene Kalibrierung auf 30 × 30 cm. Die endgültige Größe wird nach dem Ausrichten geprüft.

## Gleichmäßige Skalierung bestätigt, Drehung vorbereitet

Nativ geprüft: ausgewähltes Objekt `Pannel 3`, Skalierung `[0.06, 0.06, 0.06]`, Rotation/Translation noch jeweils 0, keine Operatorfehler. Die Ausgangsmessungen wurden offline per SVD auf Ebenheit geprüft: Singulärwerte `[40.98996578, 39.39452402, 0.80518256]`, Verhältnis kleinster/mittlerer Wert 0.02044. Die Punkte sind weitgehend eben; Messabweichungen werden erhalten.

Für eine erste Ausrichtung wird die Flächennormale auf die Y-Achse der bestehenden Rückwand gelegt. In der Ebene wird ein Rechteck mit geringer Hüllfläche gesucht (0.25°-Schritte, 0.1 % Flächentoleranz); Vorzeichen und Orientierung folgen möglichst der letzten Kameraansicht `capture-aca36f5f-4643-45fb-b372-b5a8502a0dc7/view.csv`. Summe der beiden Bildachsen-Korrelationen: 1.9631. Daraus ergeben sich vorgeschlagene Euler-Winkel X/Y/Z: **31.239°, −80.968°, −153.633°**. Rechte-Hand-Konvention X, dann Y, dann Z wie im Layout-Transform. Keine Drehung wurde durch den Assistenten angewendet.

Die Übereinstimmung mit der Kamerasicht bestätigt noch nicht die physische Orientierung des LED-Musters. Nach manueller Eingabe und SET TRANSFORM ist die Lage am Panel zu prüfen. Die endgültige Größe muss am bestehenden Panel-1-Maßstab ausgerichtet werden: dort entspricht das 30-cm-Panel einer LED-Hüllhöhe von 0.16875 Layout-Einheiten, nicht 0.30. Aktuelle Messausdehnung in der vorgeschlagenen Ausrichtung: Höhe 4.56884, Breite 4.62448 Scan-Einheiten.

## Drehung bestätigt, Größe und Zielposition vorbereitet

Nativ geprüft: Rotation `[31.239, -80.968, -153.633]` übernommen, Skalierung weiterhin 0.06, Translation 0; keine Operatorfehler. `current-rotation.png` zeigt den tatsächlich gerenderten Entwurf vor der Platzierung. Die physische Orientierung des Musters ist weiterhin vom Benutzer zu bestätigen.

Der vorhandene Platzhalter direkt unter Panel 1 besitzt 256 Punkte mit Source-IDs 1952–2207 und Grenzen `[0.615625, 1, 0.515625]` bis `[0.784375, 1, 0.684375]`. Sein Mittelpunkt `[0.7, 1, 0.6]` bestimmt den vorgesehenen Platz. Die längere LED-Hüllkante von Panel 3 wird mit einheitlicher Skalierung auf die 0.16875-Referenzausdehnung gebracht; Originalpunkte und Proportionen bleiben erhalten. Das ist die bestehende Panel-Referenzkalibrierung, keine neue Vermessung der physischen Außenkanten.

Vorgeschlagene manuelle Felder: Scale X/Y/Z jeweils `0.03649053`; Translate X `0.62302434`, Y `0.82087416`, Z `0.68790139`. Die Drehwinkel bleiben gleich. Translation verschiebt den ursprünglichen Scan-Ursprung; deshalb entsprechen die drei Feldwerte nicht direkt dem Zielmittelpunkt. Die resultierende LED-Hülle wäre ungefähr `[0.61664046, 0.99661739, 0.515625]` bis `[0.78335954, 1.00338261, 0.684375]`.

Nur berechnet und erklärt, nicht durch den Assistenten angewendet. Der vorhandene Platzhalter bleibt bis zum separaten manuellen Entfernen bestehen; aktive Map und Hardware-Zuordnung wurden nicht geändert.

## Platzierung durch Benutzer bestätigt

Die anschließende native Prüfung bestätigt sämtliche vorgeschlagenen Transformwerte, 880 Punkte und keine Operatorfehler; Messwerte stehen in `panel3-placed-check.json`. `panel3-placed-native.png` zeigt die aktuelle Layout-Ansicht mit dem noch vorhandenen Platzhalter. `panel3-front-review.png` ist eine separate Datenzeichnung der unveränderten Messpunkte mit dem tatsächlich eingetragenen Transform: horizontal −Z, vertikal X. Sie zeigt ausschließlich Panel 3 zur Bestätigung der physischen Musterorientierung durch den Benutzer. Keine Layout-Mutation bei dieser Prüfung.
