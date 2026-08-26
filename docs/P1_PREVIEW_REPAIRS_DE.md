# P1: MadMapper- und LED-Preview-Reparaturen

Stand: 26. August 2026. Dieses Dokument beschreibt die reproduzierbaren
Quelländerungen für P1, Punkte 4 und 5. Die Änderungen werden erst durch das
Ausführen der jeweiligen Builder im freigegebenen Core-70-Projekt wirksam.

## Persistente MadMapper-Live-Preview

Der Runtime-Code des MadMapper-Browsers löst einen vorhandenen verwalteten
Import jetzt beim Katalog-Refresh erneut auf. Ein Import gilt nur dann als
vertrauenswürdig, wenn

- seine ID dem verwalteten Format `mat_` plus 20 Hex-Zeichen entspricht,
- sein Paket direkt unter dem freigegebenen Importordner liegt,
- `material-import.json` dieselbe Material-ID enthält und
- `prepared.frag` innerhalb der freigegebenen Pfadwurzeln liegt.

Damit steht `prepared_shader_path` auch nach einem Neustart wieder zur Verfügung
und `OPEN LIVE PREVIEW` verlangt für einen bereits vorbereiteten Import keinen
erneuten Import. Ein automatischer Regressionstest lädt den eingebetteten
Runtime-Code zweimal aus demselben Testpaket und prüft den wiederhergestellten
Pfad.

## LED-Preview-Reset und Altparameter

Der installierte Reset-Callback setzt nun die acht aktiven Side-Ecken und alle
80 Ecken der zehn aktiven Rückwandfelder auf ihre jeweiligen Vorgabewerte
zurück. Der Button heißt entsprechend `Reset active side + rear panels`; sein
Status meldet 88 zurückgesetzte Werte.

Die acht alten Rear-Grobecken und die vier Rear-Split-Kompatibilitätswerte
bleiben für die Kompatibilität alter Projektstände erhalten, sind aber
schreibgeschützt und mit `LEGACY INACTIVE` gekennzeichnet. Sie werden vom Reset
nicht mehr als aktive Geometrie dargestellt.

## Sicherheitsgrenze

Die Builder speichern kein Projekt und verändern keine Art-Net-/DMX-Ausgabe.
Die Übernahme in Core 70 sowie sichtbare Klick- und Bildtests in TouchDesigner
erfolgen separat und beaufsichtigt.
