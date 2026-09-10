# Panel 2 um 90 Grad im Uhrzeigersinn

Auf Benutzerwunsch wurde nur Panel 2 um seinen Mittelpunkt (0.9, 1.0, 0.4) gedreht. Die Frontansicht verwendet rechts=-Z und oben=X; daher bildet die Drehung relative (X,Z) auf (Z,-X) ab. Das ist eine Weltachsen-Drehung, keine blosse Addition zu einem lokalen Eulerwinkel.

Alle Messpunkte, LED-Bindungen, fehlenden IDs, anderen Objekte und Routen bleiben erhalten. Mittelpunkt, einheitlicher Massstab und Tiefenwerte bleiben unveraendert. Die Transformation wurde punktweise gegen die explizite 90-Grad-Matrix geprueft, ebenso Undo/Redo und JSON-Roundtrip. Native aktive Tabellen unveraendert, Sender aus, keine Operatorfehler. Rueckgaengiger Layout-Commit und eigener gespeicherter Zwischenstand `PixelblazeMapper_PANEL2_ROTATED_CW90_20260911.1.toe`; keine Neuladung.

Der Benutzer verlangte anschliessend zusaetzlich eine Links-rechts-Spiegelung. Dieser Zwischenstand ist deshalb nicht die abschliessende Ausrichtung; siehe `../panel2-mirrored-20260911/MIRROR_DE.md`.
