# Panel 5: größtmögliche gemessene Übernahme

Der Benutzer akzeptiert das Ergebnis mit Lücken und möchte so viele Daten
wie möglich übernehmen. Alle 341 rekonstruierten 3D-Punkte wurden deshalb
in den Layout-Entwurf übernommen. Die elf anderen lokalen IDs bleiben als
fehlend reserviert: 123, 197, 231, 234, 235, 243, 244, 252, 253, 261, 270.
Die vier ursprünglichen 2D-Ansichten, auch Beobachtungen ohne 3D-Ergebnis,
bleiben erhalten und sind mit Dateiprüfsummen im Scanarchiv referenziert.
Es wurden keine Punkte ergänzt, geschätzt oder umnummeriert.

## Entwurf und Ausrichtung

- Objekt `Panel 5 | unter Panel 3 | 30 x 30 cm`, ID
  `9d1130c2-e47f-4f98-acaa-1f31b2332e57`.
- Reservierte interne Source-Slots 6172–6523 (352 insgesamt), davon 341 gebunden.
- Position dritte Reihe links, unter Panel 3, Mittelpunkt (0,5; 1; 0,6).
- Einheitliche Skalierung auf denselben normalisierten 30-cm-Referenzrahmen
  wie die vorherigen Panels. Die tatsächliche Punktverteilung füllt diesen
  Rahmen nicht vollständig aus; keine Streckung auf eine künstliche Quadratfläche.
- Vorläufige Drehung anhand der Kameraansicht; endgültige Ausrichtung ausstehend.
- 256 alte Platzhalterbindungen 2464–2719 ausschließlich aus dem Entwurf
  entfernt. Die ursprünglichen Scandaten und alle anderen Objekte bleiben erhalten.
- Erste LED (lokal 0, gezählt 1) grün vergrößert, letzte LED (lokal 351,
  gezählt 352) rot vergrößert. Beide sind tatsächlich rekonstruiert.

Die native Frontansicht ist geöffnet und auf Panel 5 gerichtet. Darin liegt
Grün links unten; Rot am rechten Rand des kleineren dichten Bereichs links
oberhalb der Mitte. `panel5-front-review.png` dokumentiert die tatsächliche
Vorschau. Markierungen folgen der späteren Drehung/Spiegelung.

## Prüfung und Sicherung

Reale Prüfschritte: Scan-/Bericht-/Beobachtungsidentität und Prüfsummen,
mindestens zwei Beobachtungen für jeden übernommenen Punkt, freie reservierte
Source-Slots, genaue Platzhalterauswahl, unveränderte bisherige Messpunkte und
Routen. Native Übernahme mit unverändertem aktiven Datenhash, ausgeschalteter
Ausgabe und ohne Operatorfehler abgeschlossen. Keine neue Kameraufnahme oder
LED-Ausgabe ausgelöst.

`before.json` sichert die Ausgangslage. `draft-prepared.json` enthält den
vorbereiteten Entwurf, `draft-plan.json` Transformation und fehlende IDs,
`native-draft-result.json` den Übernahmenachweis. `save.json` referenziert den
Projektcheckpoint samt SHA-256. Reproduzierbare Vorbereitung:
`tools/prepare_panel5_draft_20260911.py` und `tools/place_panel5_20260911.py`.

Die aktive Zuordnung bleibt bis zur Ausrichtung unverändert. Nach der
Ausrichtungsangabe folgt die Integration mit Controller 249 / Port 5,
U139–141. U138 bleibt schwarz; die elf fehlenden Slots bleiben ausgeschaltet.

## Ausrichtung bestätigt und aktive Integration abgeschlossen

Der Benutzer bestätigte die gezeigte Form und Ausrichtung mit „genau so!“.
Keine zusätzliche Drehung oder Spiegelung vorgenommen. Diese Ausrichtung
wurde anschließend in die aktive Zuordnung übernommen:

- 341 gültige LEDs auf 352 reservierten Source-Slots 6172–6523.
- Elf fehlende Slots schwarz und aus der aktiven Vorschau ausgeblendet.
- Segment `BACK_THIRD_LEFT_PANEL5`, Controller `BACK_PANEL_249`, Port 5,
  U139–141, Art-Net-Pixeloffset 3230 relativ zu U120.
- Controllerrahmen auf U120–141 erweitert (22 gesendete Universen),
  einschließlich des vollständig schwarzen freien U138.
- Gesamtkapazität 6524, davon 5377 Layoutpunkte und 1147 inaktive Slots.
- Die 256 früheren Platzhalter 2464–2719 sind jetzt auch aktiv maskiert.

Der reale Offline-Paketvergleich prüfte alle 352 Panel-5-Zieladressen,
die schwarzen Lücken/Padding-Bereiche sowie unveränderte Pakete für Panel
1–4 und die Seiten. Die native Transaktion prüfte übereinstimmende Längen
von Map, UVs, Maske, Material-Abtastung, Show-Ausgabe und Vorschau sowie
unsichtbare inaktive Slots. Keine Operatorfehler. Netzwerk-LED-Ausgabe wurde
nicht gestartet. Keine Controller-Firmwarekonfiguration geändert.

`tools/integrate_panel5_active_20260911.py` enthält die geprüfte Vorbereitung
und aktive Transaktion mit Rücksetzung bei Fehlern. `active-before.json`
und `transaction-snapshot.json` sichern den vorherigen aktiven Stand;
`offline-active-check.json`, `active-result.json` und
`active-integrated-document.json` protokollieren das Ergebnis.
`complete-save.json` enthält den fertigen Projektcheckpoint samt SHA-256.
Ein isoliertes Map-Revert wurde nach der kombinierten Kapazitäts-/Routingänderung
zurückgesetzt; vollständige Rückkehr über den vorherigen Projektcheckpoint.

Die sichtbaren Endpunktmarkierungen bleiben zur Orientierung erhalten.
Das nächste Panel wurde noch nicht vorbereitet. Bei weiterer fortlaufender
Belegung dieses Controllers wäre U142 das nächste freie Startuniversum.
