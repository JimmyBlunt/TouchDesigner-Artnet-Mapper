# MK2 v0.2.2: Pixelschrift und Display-Abstände

Die aktive Workflow-Anzeige verwendet eine mitgelieferte, von Hand definierte
5×7-Pixelschrift. Zeichen rücken sechs Pixel weiter; die Zwischenräume bleiben
leer. Es gibt keine Graustufen, Betriebssystem-Schriftabhängigkeit oder
gebrochenen Skalierungsfaktoren. Die Einzelparameteransicht verwendet exakt
doppelt große Zeichen. Die alte Legacy-Anzeige bleibt unverändert.

- Parameter: sieben Pixel Schrift, eine freie Pixelzeile vor dem Balken,
  feste Spalten und 13 Pixel Zeilenabstand.
- Browse: zwei Pixel oberer Rand, zehn Pixel Zeilenabstand und getrennte
  Auswahlflächen.
- Tabs: maximal neun Zeichen pro 64-Pixel-Feld, ohne Überlauf ins nächste Feld.
- Lange Texte enden mit einem Auslassungszeichen. Umlaute und ß haben eigene
  Glyphen; andere lateinische Akzente fallen auf den Grundbuchstaben zurück,
  nicht unterstützte Zeichen auf ein sichtbares Fragezeichen.
- Fehlermeldungen erhalten eine eigene Fußzeile. Überlappende Textzeilen werden
  vollständig ausgeblendet, damit keine abgeschnittenen Textreste bleiben.
- Fehlende Vorschaubilder zeigen „Kein Bild“ vollständig auf zwei Zeilen.

## Reproduzierbare Abnahme

`python tools/preview_mk2_pixel_font.py` erstellt `pixelschrift.png` und zwölf
native LCD-Bilder für Material, Browse, Pads, Show, Parameterfokus und Bestätigung.
Die Übersicht vergrößert ausschließlich um einen ganzzahligen Faktor ohne Glättung.

`python tools/check_mk2_acceptance.py --json-report docs/mk2-v0.2.2/acceptance-simulation.json`
prüft die vollständige MK2-/Show-Suite. Die zusätzlichen 14 Schriftprüfungen
decken Glyphen, Zahlen, Umlaute, Unicode-Ersatz, leere Texte, exakte Vergrößerung,
Textgrenzen in 16 Ansichten, Balkenabstände, Tab-/Pad-Grenzen, Auswahlflächen,
Fehlerfußzeilen und Textkürzung ab.

Die Anzeige wurde im laufenden TouchDesigner auf den verbundenen MK2 übertragen.
`live-display-0.png`, `live-display-1.png` und `live-check.json` dokumentieren die
gesendeten Bilder und den USB-Status. Material-Modus und Home-Ansicht blieben
erhalten, keine Aufnahme war aktiv. Die subjektive Lesbarkeit am echten LCD
muss der Benutzer beurteilen; die gerenderten Pixel wurden visuell geprüft.
