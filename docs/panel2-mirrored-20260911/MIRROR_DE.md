# Panel 2: kleines Quadrat oben rechts

Nach der angeforderten 90-Grad-Drehung im Uhrzeigersinn verlangte der Benutzer eine Spiegelung nach rechts und praezisierte: das kleine Quadrat muss oben rechts in der Ecke sein. Die Links-rechts-Spiegelung in der Frontansicht erfuellt diese Vorgabe, wie in `front-preview.png` sichtbar.

Die Spiegelung erfolgt um die senkrechte Mittelachse am vorhandenen Mittelpunkt (0.9, 1.0, 0.4): Z wird zu 0.8-Z; X und Y bleiben identisch. Das Transform-Modell bildet dies mit einer negativen lokalen Skalierungskomponente und einer passend zusammengesetzten Rotation ab. Absolute Groesse, Hoehe, Tiefenwerte und Position bleiben erhalten.

Geprueft: punktweise Spiegelmatrix, unveraenderte X/Y-Werte, gespiegelte Z-Werte, gleiche Ausdehnung und Mittelpunkt, 680 unveraenderte Bindungen, unveraenderte Rohscans und 58 Fehlmarkierungen, andere Objekte und Routen unveraendert, Undo/Redo und JSON-Roundtrip. Ein nativer Layout-Commit; aktive Tabellen per Hash unveraendert, Sender aus, keine Operatorfehler.

Gespeichert als `PixelblazeMapper_PANEL2_ORIENTED_20260911.1.toe`; Speicherbericht mit SHA-256 liegt daneben. Kein Neuladen in diesem Schritt. Orientierung anhand des vom Benutzer genannten Merkmals umgesetzt; keine Behauptung einer physisch kalibrierten Registrierung. Die originale regelmaessige Layout-Vorlage und die aktive Controller-Zuordnung bleiben fuer den folgenden gesonderten Integrationsschritt erhalten.
