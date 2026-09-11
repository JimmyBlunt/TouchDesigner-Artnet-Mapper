# Panel 3 abgeschlossen, 11.09.2026

Panel 3 enthält alle **880 gemessenen LEDs** und sitzt unter Panel 1. Der Benutzer hat die Ausrichtung zuletzt um 180° korrigiert und die Werte selbst eingetragen. Der Abschluss erfolgte danach auf seinen ausdrücklichen Wunsch durch den Assistenten.

- Aus der alten Vorlage wurden ausschließlich die 256 Bindungen mit Source-IDs **1952–2207** entfernt. Archivierte Scans bleiben erhalten, die Entwurfsänderung ist mit Undo nachvollziehbar.
- Panel 3 verwendet interne Source-IDs **4482–5361** und den 30-cm-Referenzmaßstab von Panel 1. Finale Werte stehen im aktiven Dokument; die gleichmäßige Skalierung beträgt 0.0364905.
- Aktive Zuordnung: **BACK_PANEL_249 / 10.0.0.249, physischer Ausgang 3, U127–U132**, Segment `BACK_SECOND_LEFT_PANEL3`, Art-Net-Pixeloffset 1190 relativ zu U120. Der physische Controller-Pixeloffset 941 ist keine Art-Net-Zieladresse.
- Der Controllerrahmen wurde von 7 auf **13 Universen U120–U132** erweitert. Panel 1, Panel 2 und die Seiten behalten ihre bisherigen Zuordnungen. Ein Offline-Paketvergleich bestätigt deren unveränderte Ausgabebytes. Neue Padding-Bereiche bleiben schwarz.
- Die aktive Gesamtkapazität beträgt **5362 Slots**, davon 4739 mit Layoutpunkten und 623 inaktive schwarze Slots. Panel 3 selbst hat keine fehlenden Slots.
- Aktive Map, Material-UVs, Show-Ausgabe und Preview wurden auf konsistente Länge geprüft. Die Preview blendet sämtliche inaktiven Slots aus. Es bestehen keine Operatorfehler. Netzwerk-LED-Ausgabe wurde nicht gestartet.

## Bedienverbesserung

Im Layout gibt es jetzt **REMOVE LEDs** neben SET TRANSFORM. Es entfernt einen ausdrücklich eingegebenen Bereich aus **LOCAL LEDs** des ausgewählten Objekts. Der Dialog zeigt Objekt, Anzahl und IDs; Cancel verändert nichts, Undo stellt die Bindungen wieder her. Leere, fremde und vollständige Objektbereiche werden abgewiesen. Das verhindert, dass ein leer gelassenes Feld unbeabsichtigt alles entfernt. Dieser Knopf arbeitet nur am 3D-Entwurf.

## Behobener Fehler bei Kapazitätsänderungen

Der erste Integrationsversuch wurde bei der Verifikation abgebrochen. Die innere Rücksetzung meldete ebenfalls einen Vertragsfehler; die äußere Transaktion stellte den vollständigen vorherigen aktiven Stand wieder her. Die Diagnose (`verify-diagnostics.json`) isolierte genau einen Unterschied: den abgeleiteten Endindex `lookup1:index2`. Sein unveränderter Ausdruck `me.inputs[1].numSamples-1` liefert bei einer größeren LED-Liste erwartungsgemäß einen neuen Wert.

Die Strukturprüfung bindet für genau diesen bekannten Parameter nun Ausdruck, Modus, Bindung und Verdrahtung, ohne den automatisch abgeleiteten Wert als Verdrahtungsänderung zu behandeln. Alle anderen Parameterprüfungen bleiben erhalten. Zusätzlich wachsen Map, UV-Tabelle und Schwarzmaske vor dem Cook gemeinsam; neue Slots bleiben bis zum geprüften Apply schwarz. Der erneute native Apply war erfolgreich, ohne stderr und ohne Operatorfehler.

63 gezielte Tests bestanden über Layout-Editor, Entfernen, Layout-Apply, Sparse-Apply und Parametervertrag. Der reale Offline-Plan prüft die vollständigen 880 Zieladressen sowie unveränderte ältere Panel-Ausgaben. Die native Integration prüft tatsächlich gekochte Daten und maskierte Preview-Slots.

## Sicherung und Fortsetzung

`before-cleanup.json` / `after-cleanup.json` sichern den Entwurf; `transaction-snapshot.json` den aktiven Zustand vor der erfolgreichen Übernahme. `active-result.json` und `active-integrated-document.json` dokumentieren das Ergebnis. `save.json` enthält den endgültigen TOE-Dateinamen und SHA-256. Der Checkpoint wird gespeichert, nicht erneut geöffnet. Ein isoliertes Map-Revert wurde nach der kombinierten Kapazitäts-/Routingänderung deaktiviert; zur vollständigen Rückkehr dient der vorherige gespeicherte Projektstand.

Für das nächste Panel bleibt der erprobte Scan-Paketabstand **1 ms** verfügbar. Es wurde noch keine neue Aufnahme angelegt oder gestartet: Position, LED-Anzahl, Anschluss/Controller und Startuniversum sind beim Benutzer angefragt. Die fünf Panel-3-Ansichten und das 3D-Ergebnis bleiben im aktuellen Scan-Arbeitsordner erhalten.
