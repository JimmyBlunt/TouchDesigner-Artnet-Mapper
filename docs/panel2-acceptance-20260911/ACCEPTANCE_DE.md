# Rueckpanel 2: Teilresultat im Layout-Entwurf

Am 11.09.2026 auf ausdruecklichen Benutzerwunsch uebernommen: alle 680 rekonstruierten LEDs, einschliesslich der gueltigen violett markierten Nachbarpunkte. Violett bezeichnet in der Ansicht einen Nachbarschaftshinweis und ist kein Ausschlusskriterium.

Das neue Objekt `Rueckpanel 2` archiviert 738 Scanpositionen. 58 fehlen: 35 wurden beobachtet, konnten aber nicht in 3D rekonstruiert werden; 23 wurden nie erkannt. Verdeckung bleibt unbekannt. Fehlende Positionen haben keine LED-Bindung und werden nicht als gemessene Punkte dargestellt. Interne Nullplatzhalter sind explizit als fehlend markiert. Auch die letzten IDs 733–737 sind erhalten.

Die urspruenglichen LED-Identitaeten, lokalen Indizes und Messdaten bleiben erhalten. Der additive Entwurfs-Offset ist 3744 (reservierter Bereich 3744–4481); dies ist noch keine Controller-Zuordnung. Fehlende Positionen werden fuer weitere Resultatimporte reserviert. Originale Kameraansichten samt Identitaetsdateien, Ergebnis und Bericht sind durch SHA-256-Fingerprints dokumentiert. Die visuelle Bereichsansicht bleibt fuer weitere Scans erhalten.

Die Uebernahme erfolgte mit einem rueckgaengig machbaren Layout-Commit. Vorheriger Entwurf: `before.json`; vorbereiteter Vergleich: `prepared-document.json`; tatsaechlicher Entwurf: `accepted-document.json`; alle LED-Zustaende: `led-status.csv`. Vorherige Objekte, Scans und Routen wurden im lokalen Vergleich unveraendert geprueft. Aktive Mapping-, UV-, Controller- und Segmenttabellen sind laut nativer Hashpruefung unveraendert; Sender ausgeschaltet, keine Operatorfehler. 30 gezielte Tests bestanden, inklusive JSON-Roundtrip, Undo/Redo, fehlender Endpositionen, Identitaet, Kollisionen und veraenderter Eingabedateien. Zusaetzlich wurde das reale Resultat mit 738/680/58 geprueft.

Gespeichert als `PixelblazeMapper_PANEL2_ACCEPTED_20260911.1.toe`; Dateihash und Speicherbericht liegen daneben. Der gespeicherte Stand wurde in diesem Schritt nicht neu geladen.

Naechster Schritt: reale Breite/Hoehe erfragen, dann Massstab, Ausrichtung und Position von Panel 2 im Layout einstellen. Rohkoordinaten sind beliebig skalierte SfM-Koordinaten, noch keine verifizierte Registrierung. Danach Controller-Zuordnung und erforderliche Ausgabekapazitaet gesondert pruefen, bevor eine aktive Uebernahme erfolgt.

Spaeteres Ergaenzen der fehlenden LEDs braucht einen ausdruecklichen Weg zum Hinzufuegen neuer Bindungen: die normale Layout-Teil-Ersetzung kann derzeit nur vorhandene Bindungen ersetzen. Die urspruengliche Scan-Sitzung und alle erwarteten Zielidentitaeten sind dafuer im Archiv enthalten. Die 58 fehlenden LEDs werden in diesem Schritt nicht synthetisch ergaenzt.
