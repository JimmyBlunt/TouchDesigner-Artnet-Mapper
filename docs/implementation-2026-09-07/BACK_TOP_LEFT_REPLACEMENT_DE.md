# Rückwand oben links, Vorderansicht – Entwurf 2026-09-09

Benutzerbestätigung: 30 × 30 cm, Blick von vorne in den Schrank auf die LED-Seite, LED0 oben links. Die alten Rückwandfelder sind Platzhalter.

Vorher gesichert: `Backup/Implementation/PixelblazeMapper_20260909_BEFORE_BACK_REPLACE.1.toe`.
Ergebnis: `Backup/Implementation/PixelblazeMapper_20260909_BACK_TOP_LEFT_DRAFT.1.toe`.

Vorderansicht auf Y=1 vom Inneren: X oben, Z zunehmend nach links. Daher ersetzt wurde Quelle1440–1695 (oberes Feld, höherer Z-Bereich), nicht die linke Spalte im Material-UV. Scanquelle1440–1642 enthält die 203 Messungen. Quelle1643–1695 ist frei. Andere Quellen behalten Index, LED-Identität und Weltkoordinaten exakt; geprüft für jede LED. Gesamtzahl im Entwurf3691. Expected count3744 bleibt als bestehender Ausgabevertrag stehen: aktive Übernahme/Export ist NICHT freigegeben.

Originalscan unverändert archiviert. Für die explizite Neuzuordnung wurden neue Binding-Identitäten erzeugt; alte stabile IDs wurden nicht umnummeriert. Änderung in einem Undo-Schritt. Der separate provisorische Import an3744–3946 wurde dabei entfernt.

Ausrichtung: beste Ebene, orientierte Rechteckanpassung mit LED0 als oberem linken Eckanker, reine Drehung und gleichmäßige Skalierung. Tiefe nicht abgeflacht. Auf bisherige normierte LED-Hülle eingepasst; 30cm ist Benutzermaß, keine behauptete metrische Kalibrierung des gesamten Schrankmodells. Physische Registrierung und Orientierung noch visuell abnehmen. Eine vollständige Kabel-/Zeilenorientierung ist nicht allein durch einen Eckanker bewiesen.

Ergebnis LED0 ungefähr(X=.984232,Y=1.001121,Z=.682719). Beide Objekt- und aktiven Map-Prüfungen ohne Fehler; aktive Map unverändert, Ausgabe aus, Speichern erfolgreich. Implementierung `tools/replace_back_top_left_20260909.py` ist eine eng abgesicherte einmalige Draft-Migration und keine generische Replace-UI.
