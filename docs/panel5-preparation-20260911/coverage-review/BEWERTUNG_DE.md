# Panel 5: Abdeckung nach vier Ansichten

Auf Benutzerfrage, ob die bisherigen Aufnahmen reichen, wurden die vier
gespeicherten Ansichten geprüft und die Offline-3D-Rekonstruktion ausgeführt.
Keine Kamera oder LED-Ausgabe gestartet; kein Layout verändert.

- 352 erwartete lokale IDs 0–351.
- 344 mindestens einmal, 342 mindestens zweimal und 336 mindestens dreimal
  beobachtet; keine Fehler beim Lesen der Ansichten.
- Offline-Job regulär beendet, 341 rekonstruierte LEDs (96,875 %).
- Acht IDs nie erkannt: 123, 234, 235, 243, 244, 252, 261, 270.
- Drei weitere ohne 3D: 197 und 253 jeweils nur einmal beobachtet;
  231 zweimal beobachtet, aber nicht rekonstruiert.
- Insgesamt elf fehlende 3D-Positionen. Keine Position ergänzt oder IDs verschoben.

Die Punktwolke ist weitgehend planar (SVD-Verhältnis kleinste/mittlere Achse
ca. 0,0249). Die Roh-`error`-Werte haben Median 0,438777 und Maximum 2,228363.
Diese Werte allein belegen keine metrische Genauigkeit oder endgültige
Registrierung. Keine automatische aktive Übernahme.

Die native Ansicht „FEHLENDE BEREICHE“ wurde geöffnet und bildlich geprüft.
Die erste Aufnahme liefert Nachbarhinweise für alle acht nie erkannten IDs
und zeigt alle drei erkannten, aber nicht rekonstruierten LEDs. In dieser
Kameraperspektive liegen viele Hinweise im dichten Bereich links oben und
an den beiden schmalen Reihen rechts; ein orangefarbener Punkt liegt weiter
mittig auf der schrägen Punktreihe. Violette Markierungen zeigen ausschließlich
gemessene Nachbarpunkte, keine erfundenen Positionen fehlender LEDs.

Bewertung: Für eine partielle Übernahme ist das Ergebnis grundsätzlich
verwendbar, wobei elf Slots als fehlend und schwarz erhalten bleiben müssen.
Für bessere Vollständigkeit sind zwei weitere Ansichten mit guter Sicht auf
die markierten Bereiche sinnvoll. Acht bisher nie erfasste LEDs brauchen
mindestens zwei neue Beobachtungen aus verschiedenen Blickwinkeln, bevor eine
3D-Rekonstruktion möglich wird; eine weitere Ansicht allein genügt dafür nicht.
Gemeinsame sichtbare LEDs zu den bisherigen Ansichten beibehalten.

`state.json` enthält die Ausgangslage, `offline-start.json` den Job,
`reconstruction-review.json` Ergebnis und räumliche Abdeckung,
`quality-summary.json` die geometrische Kurzprüfung. `missing-areas.png`
ist die tatsächliche native Lückenansicht. `save.json` referenziert den
Projektcheckpoint einschließlich Prüfsumme. Scan-CSV-Dateien und Ergebnis
bleiben im bisherigen Panel-5-Arbeitsordner erhalten.
