# MK2-Gerätesimulation – Abnahme 0.2.0

Stand: 12. Oktober 2026. Die Tests in `tests/test_mk2_device_simulation.py`
führen den unveränderten `Surface.start()`-Thread gegen ein vollständig ersetztes
HID-Endgerät aus. Kein physischer Controller wird geöffnet, kein laufendes
TouchDesigner-Projekt verändert. Eine deterministische Uhr ersetzt Wartezeiten.

## Durchgängige Prüffälle

| Test | Nachweis |
|---|---|
| Versionierte Eingabe und Ausgabe | Rohberichte erzeugen einmalige BROWSE-/STEP-Flanken, Radschritte und Pad-Druck; alle Gerätezugriffe laufen im Worker. Beide LCDs erhalten jeweils acht vollständige 265-Byte-Bänder. RGB- und Tastenberichte werden ebenfalls geschrieben. |
| Trennen und Wiederverbinden | Alter Handle wird geschlossen, bevor der neue geöffnet wird. Gehaltene Tasten und Pads sowie beliebige absolute Encoder-/Radpositionen werden zur neuen Ausgangsbasis. Erst erneutes Betätigen löst aus. Beide Displays werden vollständig neu übertragen. |
| Verbindungsmarker und REC | Vor den Eingaben jeder neuen USB-Sitzung sowie sofort beim Verlust eines geöffneten Geräts wird `connection_reset` gemeldet. Ein zuvor gehaltenes REC kann durch Loslassen nach dem Wiederverbinden keine neue Cue erzeugen. |
| Fehlendes Gerät | Fehlgeschlagene Suchläufe melden den Status, erzeugen jedoch keine Endlosschleife von Verbindungsmarkern. |
| Unvollständiges Schreiben | Ein verkürzter Rückgabewert wird als Übertragungsfehler behandelt. Der Handle wird geschlossen; beim nächsten Verbindungsaufbau werden auch zuvor vermeintlich geschriebene Bänder erneut übertragen. |
| Fehler beim Schließen | Meldet das Backend nach dem Abziehen auch beim Schließen einen Fehler, bleibt der Worker aktiv. Der Fehler wird angezeigt und die Verbindung nach der regulären Wartezeit erneut versucht. |
| Rohbericht bis Bildschirm | Ein BROWSE-Rohbericht wird vom echten Decoder verarbeitet, erreicht die echte `Controller`-Zustandsmaschine und ändert anschließend den vom echten Renderer erzeugten LCD-Inhalt. |
| Versionsgrenze | Eingaben behalten die Version des gelesenen Zustands. Ein während des Rückrufs ersetzter Zustand darf bereits gelesene Eingaben nicht nachträglich als neu kennzeichnen. Die Ablehnung veralteter Eingaben wird zusätzlich im Runtime-Test geprüft. |
| Grenzwerte aller Ansichten | Material-/Show-Modus, acht Ansichten und drei endliche Dauern ergeben 48 Varianten: unter anderem Null, sehr kleine und große Dauer, konstante Parameterbereiche, große Wertebereiche, lange Unicode-Namen, fehlende Vorschaubilder und Parameterüberlauf. Beide Bilder bleiben vollständige, erneut lesbare 256×64-PNGs. |
| Leere Daten | Leere Bibliothek, fehlendes aktives Material, leere Parameterliste und nicht belegte Pads verhindern das Rendern der jeweiligen Navigationsansichten nicht. |

## Gefundener und behobener Fehler

Beim USB-Wiederverbinden wurden bisher nur die Rohbericht-Decoder zurückgesetzt.
Der Hauptthread konnte weiterhin einen gehaltenen REC-Taster und eine ausstehende
REC-Aktion gespeichert haben. Das Loslassen nach dem Wiederverbinden hätte diese
alte Aktion als Start einer neuen Cue ausführen können.

Der Worker meldet jetzt den Sitzungswechsel und den Verbindungsverlust ausdrücklich.
Der Runtime-Adapter entfernt alte Warteschlangeneinträge sowie gehaltene Tasten und
ausstehende Tastenkombinationen. Eine bereits laufende Aufnahme bleibt dabei unter
Kontrolle des Hosts. Der Gerätetest prüft die Reihenfolge der Meldungen; separate
Runtime-Tests prüfen die Priorität bei voller Warteschlange und den Erhalt einer
laufenden Aufnahme.

Ein zweiter reproduzierter Fehler betraf das Schließen eines bereits abgezogenen
Geräts: Eine Backend-Ausnahme konnte bisher den Worker endgültig beenden. Der
Fehler wird jetzt abgefangen; Statusmeldung und reguläre Wiederholungswartezeit
bleiben erhalten. Der entsprechende Gerätetest scheiterte vor der Korrektur mit
einer unbehandelten Ausnahme und besteht danach.

## Wiederholung

Im Projektverzeichnis:

```powershell
python -m unittest discover -s tests -p 'test_mk2_device_simulation.py' -v
python -m unittest discover -s tests -p 'test_mk2_hardware.py' -v
```

Ergebnis dieser Abnahme: **10 Gerätesimulationen erfolgreich**. Zusätzlich bestehen
die **24 vorhandenen Hardware-/Displaytests**, darunter die aufgezeichnete
Encoder-Störfolge, langsame Drehung mit Hysterese, Umlauf, alle Übergangspiktogramme,
LED-Farbfähigkeiten und die unveränderte Achtparameterübersicht vor einer Auswahl.

## Grenzen der Simulation

Die Simulation prüft das vereinbarte USB-Protokoll, das tatsächliche Programm und
die Bilddaten. Sie beweist weder die reale Tastenzuordnung einer unbekannten
Firmware noch die sichtbare Darstellung, Helligkeit, Farbe, USB-Treiberstabilität
oder das mechanische Bediengefühl des angeschlossenen Controllers. Insbesondere
konnten bisher keine vom Nutzer bezeichneten BROWSE-/STEP-Tastenflanken als
Rohbericht aufgezeichnet werden. Die verwendeten Adressen bleiben durch die
Protokollreferenz, aber noch nicht durch diesen physischen Abnahmeschritt gedeckt.

Echte TouchDesigner-Shader, LED-Ausgabe, tatsächliche Aufnahme und hör-/sichtbare
Übergänge werden durch diese Gerätetests ebenfalls nicht ausgeführt. Andere
Simulationsgruppen prüfen Host- und Aufnahmeintegration mit separaten Fixtures.
Die physischen Prüfpunkte **H1/H2 bleiben offen**; bestandene Simulationen ersetzen
diese Abnahme nicht.
