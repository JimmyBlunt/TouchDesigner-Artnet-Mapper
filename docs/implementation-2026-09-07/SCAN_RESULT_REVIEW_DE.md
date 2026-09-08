# 3D-Ergebnisprüfung und Entwurfsübergabe

## Bedienung

Nach abgeschlossener Offline-Rekonstruktion öffnet `3D RESULT / PATH` den neuen
Dialog `3D RESULT REVIEW`. Er zeigt Punktanzahl, fehlende beobachtete IDs,
Koordinatengrenzen, Kandidatenpfad und ausdrücklich den nicht registrierten Zustand.

| Feld | Bedeutung |
| --- | --- |
| New object name | Name des neuen, separat auswählbaren Entwurfsobjekts |
| Global source offset | Globaler Index = Offset + ursprüngliche Scan-ID; keine Verdichtung von Lücken |
| Translation X/Y/Z | Verschiebung im Layout; X Höhe, Y rechts, Z Tiefe |
| Rotation degrees X/Y/Z | Drehung in Grad gemäß vorhandener Layout-Transform-Reihenfolge |
| Scale X/Y/Z | Skalierung pro Achse; 1 unverändert |
| Add as new draft object | Nach Bestätigung als neues Objekt hinzufügen; vorhandene Objekte nicht ersetzen |
| Back to Guided Scan | Zur Scanoberfläche zurückkehren |

Die Transformation wirkt auf den Entwurf, die eingelesenen Rohkoordinaten bleiben
erhalten. Nach dem Hinzufügen öffnet sich die 3D-Layoutansicht. Dort können die
vorhandenen Transformationsregler und Maus-/Tastaturwerkzeuge zur Feinpositionierung
verwendet werden. Strg+Z in der 3D-Ansicht nimmt das Hinzufügen zurück.

Es gibt bewusst keinen automatischen Fit und keine behauptete automatische
Registrierung. Für einen Ersatzscan muss das gemeinsame Koordinatensystem zunächst
belegt werden. Dieser Dialog implementiert vorerst die zusätzliche Entwurfsaufnahme,
nicht den qualitätsgeprüften Ersatz bestehender Bereiche.

## Grenzen und Schutzprüfungen

- Nur ein erfolgreich validiertes Offline-Ergebnis ist zulässig.
- Kandidat und Qualitätsbericht werden gehasht; Änderungen nach der Prüfung
  blockieren die Übergabe. Importiert werden dieselben geprüften Kandidatenbytes.
- Doppelte Kandidaten und Überschneidungen globaler Indizes werden abgewiesen.
- Ursprüngliche Scan-ID-Lücken bleiben erhalten. Fehlende Punkte werden nicht
  interpoliert, nicht mit Nachbarpunkten ersetzt und nicht dicht umnummeriert.
- Bestehende Objekte und Controller-/Port-Zuordnungen bleiben unverändert.
- Kein Live-Apply, kein Einschalten von Kamera oder Art-Net.
- Die bisherige erwartete Gesamtanzahl bleibt erhalten. Eine zusätzliche,
  lückenhafte Testaufnahme ist daher nicht automatisch ein exportierbares oder
  aktivierbares Gesamtprojekt. Vollständigkeit und Routing sind getrennt zu klären.

## Reale Abnahme am 08.09.2026

Verwendet: zuletzt rekonstruierter Rückwand-Test `audit-3`, 196 Punkte;
fehlende beobachtete IDs 59,70,72,73,74,78,80.

1. Scanfenster für diesen Test über die TD-Schnittstelle geöffnet, nachdem der
   Navigations-Klick keine verlässlich sichtbare Wirkung zeigte. Dieser Einstieg
   ist deshalb in diesem Lauf kein bestandener Navigations-Klicktest.
2. **Echter Klick** auf `3D RESULT / PATH` öffnete den neuen Reviewdialog.
3. Offset **3744 über echte Tastatureingabe** gesetzt, Standardtransformation
   beibehalten. `ADD AS NEW DRAFT OBJECT` und Bestätigung per Mausklick.
4. Layout zeigt zwei Objekte, 3940 Punkte; neues Objekt farblich separat sichtbar.
5. Lesende Kontrolle: alle 196 Scan-IDs stimmen, für jede gilt globaler Index =
   3744 + Scan-ID. Das vorhandene Objekt ist exakt unverändert.
6. Koordinaten-Klick auf Undo traf in dieser Fensterposition nicht zuverlässig
   den Button; kein Erfolg behauptet. **Strg+Z** nahm die Ergänzung erfolgreich zurück.
7. Entwurfs-Datenhash wieder exakt wie vor dem Test:
   `4705657686cb95032cd2c2a9d0afcb42be2254caed4b9b331d6ed9fdc94e7375`.
8. Aktive Map durchgehend unverändert:
   `dbcaf4e56561ae3bc68731d89e12e661502a42950274886b1f75645d17f1282f`.
   Keine TD-Projektfehler, Sender aus. Testobjekt nicht im aktuellen Entwurf;
   Redo-Historie kann es wiederherstellen.

Sechs neue automatische Tests prüfen Quelle/Transformation, unveränderte
Bestandsobjekte, Undo, Kollisionen/Duplikate, geänderte Dateien, falsche Ergebnisse
und das Verhindern eines stillen Exports lückenhafter Daten.

Gesamter gezielter Regressionslauf: **337 Tests bestanden**. Nach Storage-/Pickle-
Vorprüfung ohne Warnung gespeichert unter
`Backup/Implementation/PixelblazeMapper_20260908_SCAN_RESULT_REVIEW.1.toe`.

Offen: jede einzelne Transformationsachse mit echter Eingabe testen, Back-Button,
vollständige Prepare→Reconstruct→Review-Klickkette, messtechnische Registrierung,
qualitätsgeprüfter Ersatzscan, physische Kamera-/LED-Abnahme und Wiederöffnen der
neuen TOE. Kein Anspruch auf abgeschlossene Gesamtabnahme.
