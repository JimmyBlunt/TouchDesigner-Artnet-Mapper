# Bekannte LED-IDs ausrichten und Teilbereiche im Entwurf ersetzen

Stand: 10.09.2026. Umsetzung: `scan_registration.py`, `scan_registration_ui.py`.

## Bedienablauf

1. In Layout das bestehende Objekt und den zu erneuernden Teilbereich auswählen. Den Scan aus diesem Objekt starten, damit Objekt-, LED- und Quellenidentitäten erhalten bleiben.
2. Im Scanumfang zusätzlich mindestens vier **unveränderte, bereits vermessene Referenz-LEDs** als Anker angeben. Sie gehören nicht zur Ersetzungsauswahl. Mindestens drei Anker müssen eine Fläche aufspannen; eine gerade LED-Reihe genügt nicht. Gut verteilte weitere Anker verbessern die Prüfbarkeit.
3. Überlappende Ansichten aufnehmen oder die zu dieser Sitzung gehörenden gespeicherten Ansichten verwenden. Jeder verwendete Anker und jede zu ersetzende LED braucht Beobachtungen in mindestens zwei Ansichten. Das 3D-Ergebnis öffnen.
4. In der Ergebnisprüfung **ALIGN / PARTIAL REPLACE** öffnen. Die Quellen-IDs werden aus der Sitzung vorbelegt: alle bis auf den letzten rekonstruierten Anker für die Anpassung, der letzte als unabhängiger Prüfanker. Diese Rollen sind ausdrücklich editierbar; die Zuordnung zur physischen LED wird nicht geschätzt.
5. Fit-Anker, separate Prüfanker, die exakt zu ersetzenden Quellen-IDs und **MAXIMUM FIT / CHECK DEVIATION** prüfen. Der Startwert `0.01` ist ein editierbarer Eingabewert, keine automatisch ermittelte Genauigkeitsgarantie. Die Einheit ist das ursprüngliche Koordinatensystem des Zielobjekts, nicht Pixel oder zwingend Meter.
6. **CALCULATE** berechnet nur einen Vorschlag. Die Anzeige enthält Fit-RMS, unabhängigen Prüf-RMS, größten Fehler, Grenzwert, Skalierung, Rotation, Verschiebung, Ersetzungsauswahl und erhaltene ausgewählte IDs. Jeder Fit- und Prüffehler muss den Grenzwert einhalten.
7. **COMPARE POINTS** zeigt vor/nach-Koordinaten und Verschiebungsbetrag im Weltkoordinatensystem. **EVIDENCE** öffnet den vollständigen Prüfdatensatz.
8. **REPLACE IN DRAFT** nennt die tatsächliche Auswahl und Prüfergebnisse nochmals in einer Bestätigung. Erst deren Annahme erzeugt eine einzelne rückgängig machbare Layoutänderung. Die bearbeitete Auswahl erscheint im Layout; **Undo** stellt den vorherigen Entwurf wieder her.

Fehlende rekonstruierte Auswahlpunkte werden in der vorgeschlagenen UI-Auswahl ausgelassen. Die Ergebnisprüfung und der Registrierungsbericht zeigen diese nicht ersetzten IDs; die vorhandenen Koordinaten bleiben erhalten. Wenn eine fehlende ID ausdrücklich angefordert wird, blockiert die Berechnung, statt einen Punkt zu interpolieren oder Indizes zusammenzuschieben.

## Was überprüft wird

- Ergebnisdatei und `quality_pending.json` müssen unverändert zur geöffneten Prüfung passen. Die Sitzungs-ID muss übereinstimmen; die rekonstruierten IDs müssen zum ursprünglichen Aufnahmeumfang gehören.
- Szenen-ID und Szenenrevision müssen dem Scanplan entsprechen. Für jede verwendete LED werden stabile LED-ID, Objekt-ID, lokaler Index und Quellenindex verglichen.
- Anker müssen aus der ausdrücklich angelegten Ankerliste stammen, Ersatzpunkte aus der getrennten Ersetzungsauswahl. Anker dürfen nicht ersetzt werden. Fit- und Prüfanker sind disjunkt.
- Fehlende Referenzpunkte, fehlende Rekonstruktionen, unzureichende Ansichten, kollineare oder nahezu kollineare Anker, nicht endliche Zahlen und veränderte Prüfdaten blockieren die Übernahme.
- Die Prüfung wird unmittelbar vor der Entwurfsübernahme erneut berechnet. Auch Änderungen während des Bestätigungsdialogs werden abgefangen.

Es gibt keine Suche nach nächstgelegenen Punkten, automatische Indexzuordnung, Ausreißerentfernung, Spiegelung, anisotrope Skalierung oder erfundene Ersatzkoordinaten. Ein altes Ergebnis ohne passende ursprüngliche Sitzung und Ankerbelege kann weiterhin als neues Rohscanobjekt geprüft werden; eine identitätstreue Teilersetzung wird daraus nicht behauptet.

## Verfahren und Grenzen

Die Implementierung berechnet eine orientierungserhaltende Ähnlichkeitstransformation aus **bekannten Paaren**: positive einheitliche Skalierung, Rotation und Translation. Für die Rotation wird Horns Quaternionformulierung verwendet; ein begrenzter Jacobi-Eigenwertlöser löst die symmetrische 4×4-Matrix. Die Skalierung minimiert anschließend den quadratischen Fehler in Zielkoordinaten. Die Umsetzung benötigt nur die Python-Standardbibliothek.

Die Methode folgt dem Primärbeitrag [Horn, „Closed-form solution of absolute orientation using unit quaternions“ (1987)](https://people.csail.mit.edu/bkph/papers/Absolute_Orientation_Scanned.pdf). Das verwandte Optimierungsziel der Ähnlichkeitstransformation ist in der [Eigen-Dokumentation zu Umeyama](https://www.eigen.tuxfamily.org/dox/group__Geometry__Module.html) beschrieben. Diese Quellen begründen das mathematische Verfahren; sie liefern keine allgemeingültige Fehlertoleranz für die konkrete Installation.

Anker werden zunächst über ihre archivierten Scanregistrierungen und Objekttransformationen in Weltkoordinaten gebracht und danach in den ursprünglichen Rahmen des Zielobjekts zurückgerechnet. Damit bleiben vorhandene Objekttransformationen bei einer Teilersetzung erhalten. Eine allgemeine affine Verzerrung lässt sich durch die zugelassene Ähnlichkeitstransformation nicht korrigieren und muss an den Fehlern erkannt werden.

Ein kleiner Ankerfehler allein beweist weder die Richtigkeit aller rekonstruierten LEDs noch die tatsächliche metrische Genauigkeit. Die Zuverlässigkeit hängt auch von richtigen, unveränderten Referenz-LEDs, räumlicher Verteilung, Aufnahmequalität und einer angemessenen Toleranz ab. Der separate Prüfanker wurde nicht zum Fit verwendet. Weitere räumlich verteilte Prüfanker sind möglich.

## Nachvollziehbarkeit und Datenhaltung

Der Vorschlag enthält Dateihashes, Szenenrevision, Sitzungsdigest, exakte Anker-/Ersatz-IDs, Transformationsparameter, jeden Ankerfehler, Grenzwert und einen Gesamtdigest. Bei der Übernahme wird dieser JSON-Beleg im `warnings`-Metadatenfeld des neu archivierten Scans mit dem Präfix `Registration evidence:` gespeichert und damit über das vorhandene Layoutformat dauerhaft exportiert/gesichert. Rohpunkte werden unverändert archiviert; die Transformation liegt separat in `Scan.registration`.

Die Teilersetzung behält LED-IDs, lokale Indizes, Quellenindizes, Objekttransformation und Routen bei. Nicht angenommene LEDs behalten auch ihre bisherigen Scanbindungen. Alte Scans werden nicht verändert oder entfernt. Die UI greift ausschließlich auf den Entwurf zu und startet weder Kamera, Prozesse noch LED-Ausgabe.

## Prüfung

`python -m unittest tests.test_scan_registration tests.test_scan_management_ux tests.test_scan_result_review tests.test_scan_session`

Ergebnis: 43 Tests bestanden. Der neue Registrierungsbereich umfasst Rotations-/Skalierungs-/Translationsfälle, Euler-Singularitäten bei ±90°, 40 reproduzierbare zufällige räumliche Transformationen mit unabhängigen Prüfpunkten, Reflexionen, degenerierte/nicht endliche Eingaben, falsche stabile Identitäten, unabhängige Fehlmessungen, fehlende Punkte, veraltete Szenen/Sitzungen/Dateien, manipulierte Belege, UI-Abbruch, Änderungen während der Bestätigung und Undo. Die Tests blockieren Hardware-/Prozessaufrufe. Sichtprüfung des tatsächlich gebauten TouchDesigner-Panels wird getrennt im Integrationsprotokoll dokumentiert.
