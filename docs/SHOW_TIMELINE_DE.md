# Show Timeline

Im Show-Editor oben rechts **TIMELINE** anklicken. Der Editor öffnet ein separates Browserfenster unter `http://127.0.0.1:9991/`. TouchDesigner muss geöffnet sein und Frames ausführen.

- Eine Spur pro Cue/Materialaufnahme. Spur anklicken, um Automation und Übergang aufzuklappen.
- Clip horizontal ziehen: in der bestehenden Show-Reihenfolge umordnen. Die Reihenfolge bleibt sequenziell; im Überlappungsmodus beginnt der nächste Clip bereits vor dem Ende seines Vorgängers. Freie Lücken oder mehr als zwei gleichzeitige Material-Layer sind nicht vorgesehen.
- Rechten Cliprand ziehen oder im Inspector die Dauer eingeben. Nachfolgende Clips rücken mit. Original-Samples jenseits einer gekürzten Dauer bleiben erhalten und werden beim Verlängern wieder sichtbar.
- Kurve doppelklicken: neuen Punkt setzen. Punkt ziehen oder Zeit/Wert im Inspector eingeben. **Entf** löscht den gewählten Punkt.
- Über das Dropdown am Spuranfang einen zusätzlichen Parameter hinzufügen. Unterstützt werden die vom Player verwendeten numerischen Parameter; Farben/Vektoren und Compile-Time-Schalter sind ausgeschlossen.
- Interpolation: Linear, Step, Smooth/S-Kurve, Ease In, Ease Out. Smooth ist eine interpolierte S-Kurve ohne separate Bézier-Tangenten.
- **Bearbeitung aktiv** schaltet die manuelle Ebene an/aus. **Original wiederherstellen** entfernt die manuelle Parameterkurve. Aufzeichnungen bleiben unverändert und erscheinen gestrichelt hinter der Bearbeitung.
- Übergänge: Typ und Dauer im Inspector, Verlauf in der Übergangsspur. Den unteren Startgriff horizontal ziehen: Übergangsdauer ändern, Clip-Ende bleibt fest. Den oberen Endgriff ziehen: Übergang und Clip gemeinsam verlängern/verkürzen, Übergangsstart bleibt fest. Bei alten Shows und räumlichen Übergängen formen Zwischenpunkte den Verlauf zwischen 0 und 1. Beim neuen Crossfade zeigt diese Spur nur die Überlappungsdauer; den Helligkeitsverlauf bestimmen die eigenen Clip-Blenden. Bei einem Schnitt entfällt die Übergangsspur.
- Zeitlineal anklicken: Wiedergabeposition setzen. Die Transporttasten steuern den vorhandenen Show-Player; die Timeline verwendet dessen Uhr.
- **Gesamte Show**, Zoom, Raster, horizontaler/vertikaler Scrollbalken und **Playhead folgen** helfen bei langen Shows.
- Mausrad über Zeitlineal oder Bereichsbalken: Zoom um die Mausposition. Es ist keine Zusatztaste nötig.
- Rechte Trennlinie im Spurkopf ziehen: linke Spaltenbreite ändern. Unterkante eines Spurkopfs ziehen: Clipspur von 56 bis 28 px, Automationsspur von 106 bis 53 px verkleinern oder bis 320 px vergrößern. Diese Ansichtsgrößen bleiben im Browser gespeichert.
- Bereichsbalken: links/rechts begrenzen, in der Mitte verschieben oder auf freier Fläche einen neuen Bereich aufziehen. Start/Ende lassen sich zusätzlich in Sekunden eingeben. **Ganze Show markieren** setzt den Bereich auf die gesamte Show; **Loop** schaltet Wiederholung ein. Bereich und Aktivierung gehören zur Automation, sind rückgängig machbar und werden mit der Show gespeichert. Während einer Aufnahme ist die Bereichswiederholung ausgesetzt, damit eine Aufnahme nicht über einen Zeitsprung überschrieben wird.
- **Strg+Z**, **Strg+Umschalt+Z**: Undo/Redo (bis zu 80 Änderungen pro Sitzung). Änderungen im anderen Show-Editor setzen diese Historie zurück, damit keine fremden Änderungen überschrieben werden.
- **Speichern** verwendet die bestehenden Show-Dateien unter `shows/`: `.json`, `.automation.json` und `.materials.json`. Während einer Aufnahme sind Timeline-Schreibbefehle gesperrt.

## Daten und Wiedergabe

### Echte Überlappungen und eigene Clip-Blenden (Version 1)

Neue Shows verwenden automatisch `timing_mode="overlap"`. Alte Shows bleiben beim
Laden unverändert und zeigen **Echte Überlappungen aktivieren**. Die Umstellung ist
rückgängig machbar; der TouchDesigner-Host sichert zuvor Show, Aufnahmen und
Materialparameter unter `.controller-runtime/timing-backups/`. Erst **Speichern**
übernimmt die neuen Daten in die vorhandenen Show-Dateien.

Die Clip-Dauer umfasst nun die gesamte sichtbare Zeit einschließlich Ein- und
Ausblendung. Zwei Clips mit je 10 Sekunden und 3 Sekunden Überlappung laufen
insgesamt 17 Sekunden. Der nächste Clip beginnt bei Sekunde 7; seine Animation
und Automation laufen ab dann mit eigener lokaler Zeit 0. Beim vollständigen
Übernehmen bei Sekunde 10 springen Zeit und Parameter nicht zurück.

Im Inspector sind **Einblendung**, **Ausblendung** und ihre Kurven unabhängig
wählbar: Linear, Smooth, Ease In und Ease Out. Die beiden farbigen Griffe im Clip
ändern die Blendzeiten auch direkt mit der Maus. Null Sekunden bedeutet keine
jeweilige Clip-Blende. Eine Ausblendung des letzten Clips führt zu Schwarz;
die erste Einblendung beginnt aus Schwarz. Bei sich innerhalb eines sehr kurzen
Clips überschneidenden Ein-/Ausblendungen multiplizieren sich beide Hüllkurven.

**Überlappung zum nächsten Clip** bestimmt separat, wann der nächste Clip startet.
Die versetzten Clip-Blöcke und die markierte Überlappungsfläche zeigen das echte
Zeitintervall. Der Inspector zeigt neben dem gewünschten Wert die tatsächlich
verwendete Dauer: Sie wird begrenzt, falls sonst drei Clips gleichzeitig laufen
oder der Folgeclip bereits vor dem Vorgänger enden würde. Am letzten Clip gibt
es keinen Überlappungsbereich. Beim Show-Loop wird nach dem letzten Clip wieder
am ersten begonnen; eine zusätzliche Überlappung über die Loop-Naht gibt es nicht.

Ein Crossfade verwendet die Clip-Hüllkurven genau einmal. Passende lineare
Ein-/Ausblendungen bleiben deshalb ohne zusätzliche Verdunklung. Übersteigt die
Summe beider Hüllkurven 1, wird sie normalisiert; kürzere oder unterschiedlich
geformte Blenden können absichtlich dunklere Abschnitte erzeugen. Ohne beide
Blenden werden zwei überlappende Crossfade-Clips gleichgewichtet gemischt.
Räumliche Übergänge (z. B. Wipe) behalten zusätzlich ihre räumliche Maske.
Die Übergangsspur zeigt beim neuen Crossfade deshalb nur die Überlappungsdauer
mit zwei Zeitgriffen. Die Helligkeitsverläufe bearbeitet man an den eigenen
Ein-/Ausblendungen. Bei räumlichen Übergängen und alten Shows bleibt die
bearbeitbare Übergangskurve verfügbar.

Bei der Umstellung alter Shows bleiben Clip-Dauern, originale Aufnahmen und
Materialwerte unverändert. Die Gesamtdauer verkürzt sich um die Überlappungen.
Einblendungen werden aus der vorherigen effektiven Überlappung, Ausblendungen
aus der eigenen abgeleitet. Die erste Einblendung bleibt zunächst 0; die letzte
Ausblendung übernimmt die bisher eingestellte Übergangsdauer. Vorhandene
Loop-Bereiche werden auf Clip und lokale Zeit übertragen; ein dadurch ungültig
werdender Bereich wird deaktiviert. Legacy-Shows behalten weiterhin die bisherige
Preroll-Zeitführung und den Übergang am Ende des vorherigen Clips.

Abnahme der Griffkorrektur vom 15.10.2026: 33 Timeline-Softwaretests bestanden.
`tools/test_timeline_crossfade.cjs` prüft echte Mausbewegungen gegen einen isolierten
Python-HTTP-Backend: beide Griffe, Undo, Abbruch, Klick ohne Änderung, Grenzen,
Mindestdauer, Zoom/Scroll und Neuladen. Edge/Playwright, 1440×1000 und 900×850;
keine Anwendungsfehler, lediglich die separat ausgewiesene fehlende favicon.ico.
Start mit Node, Playwright in NODE_PATH und Python als erstem Skriptargument;
optionales zweites Argument ist der Screenshot-Ordner. Der Test verändert keine
laufende TouchDesigner-Show. Browser plugin not available; daher Playwright.

`tracks` enthält die Originalaufnahmen. Optionale `edits`, `transitions` und `loop_region` in derselben Automationsdatei speichern die manuellen Ebenen, Übergangskurven und Bereichsgrenzen. Bestehende Dateien bleiben lesbar. Ältere Programmversionen ohne Timeline unterstützen diese neuen Ebenen nicht.

## MASCHINE MK2 und MIDI

**MIDI · Controller** öffnet das Parameter-Mapping. Die MIDI-Eingabe läuft nativ in TouchDesigner und bleibt auch bei geschlossenem Browser aktiv. Material-Pads, Pad-Beleuchtung und Displaybilder haben eine separate direkte MK2-Anbindung unter **Material-Pads · MK2** (siehe unten).

1. Den offiziellen MASCHINE MK2 Windows-Treiber und Controller Editor einrichten. [NI Treiber und Downloads](https://support.native-instruments.com/support/solutions/articles/69000882238-native-instruments-drivers-other-files).
2. MASCHINE MK2 mit **SHIFT + CONTROL** in den MIDI-Modus schalten. [NI Anleitung](https://support.native-instruments.com/support/solutions/articles/69000880031-native-instruments-switching-your-controller-to-midi-mode).
3. MIDI-Eingang wählen und **MIDI aktiv** einschalten. Die Geräteliste folgt den von TouchDesigner erkannten Eingängen. Bei fehlendem Gerät zuerst Windows-Treiber prüfen und gegebenenfalls TouchDesigner nach der Treiberinstallation neu öffnen.
4. Ziel und Wertebereich wählen, **Lernen** drücken, Hardware-Regler bewegen oder Pad drücken. Der Lernimpuls wird nur zugeordnet und löst noch keine Aktion aus. **Mapping speichern** sichert weitere Änderungen.

Vorbereitet sind acht Regler und acht Aktionen (Play, Pause, Stopp, vorheriger/nächster Clip, Aufnahme, Loop, Live-Werte freigeben). Die Adressen werden bewusst gelernt, weil sie vom Controller-Editor-Template abhängen. Ein MIDI-Eingang + Kanal + CC/Note ist eindeutig; erneutes Lernen verschiebt eine doppelte Zuordnung. CC und Note-on werden unterstützt, Note-off wird ignoriert. Regler können absolut, relativ mit Zweierkomplement (1/127) oder relativ um 64 arbeiten. Für den Einstieg im Controller Editor absolute CCs wählen. Die Wertebereiche lassen sich passend zum Material einstellen.

Parameter wirken auf den **laufenden Clip** und überschreiben seine Automation vorübergehend. Nicht vorhandene Parameter werden mit einer Meldung übersprungen. Für importierte Materialien die passenden `mat_…`-Ziele wählen. Clipwechsel, Deaktivieren, Trennen des Eingangs und **Live-Werte freigeben** geben die Automation wieder frei. Mit der vorhandenen Aufnahme werden die MIDI-Werte in die Aufnahme übernommen. Die Aufnahmeaktion wählt dazu den laufenden Clip und startet ihn wie die bestehende Aufnahmefunktion von vorn. Andere Transportaktionen sind während der Aufnahme gesperrt; Aufnahme erneut drücken beendet sie.

Das Mapping wird getrennt von der Show unter `config/timeline_midi.json` gespeichert. Es enthält keine Show-Automation und gehört nicht zur Timeline-Undo-Historie. Beim Projektöffnen wird es wieder geladen. Ohne vorhandenen, gewählten MIDI-Eingang bleibt der Empfänger deaktiviert.

Importierte Materialparameter ohne `mat_`-Präfix werden als `mat__<Originalname>` gespeichert und beim Schreiben der Uniforms zurückzugeordnet. Bestehende `mat_*`-Aufnahmen behalten ihre Identität. Im Überlappungsmodus läuft die Automation beider Clips ab ihrem jeweiligen sichtbaren Beginn; beim Wechsel des aktiven Slots startet sie nicht erneut. Alte Shows behalten ihre bisherige Zeitführung.

Der lokale HTTP-Server bindet ausschließlich an `127.0.0.1`. Schreibbefehle benötigen einen Sitzungstoken, werden gegen die aktuelle Dokumentrevision geprüft und auf dem TouchDesigner-Hauptthread ausgeführt. Es gibt keine zweite Wiedergabe-Engine. Beim Öffnen werden keine Transportbefehle ausgelöst.

## Installation aus den Quellen

`build_show_editor.build()` installiert den Timeline-Knopf und die nötigen Hooks mit. Für eine gezielte Aktualisierung im TouchDesigner-Textport:

```python
from pixelblaze_mapper.show_timeline_ui import install
install()
```

Die Projektdatei muss anschließend gespeichert werden, damit Knopf und Frame-Callback nach dem Wiederöffnen erhalten bleiben. Die Quellmodule und `pixelblaze_mapper/timeline_assets/` müssen mit dem Projekt verfügbar bleiben. Der HTTP-Server startet erst beim Öffnen der Timeline. Undo/Redo wird nicht in der TOE gespeichert.

Bei bereits installierter Timeline aktualisiert ihr Frame-Callback nach einem Neustart automatisch die gespeicherten Show-Callbacks für den Überlappungsmodus. Eine laufende Aufnahme verschiebt diese Aktualisierung bis zum Aufnahmeende. Vorhandene Shows werden dadurch nicht automatisch umgestellt; neue Shows verwenden das neue Modell.

## Prüfung

Abnahme **Überlappungen v1, 16.10.2026**:

- 486 Softwaretests bestanden, ohne Fehler oder übersprungene Tests. Enthalten sind Wiedergabe, Zeitwechsel, Aufnahme, Automationen, MIDI, MK2, alte Shows und die Installation nach einem Neustart.
- Der isolierte Commit-Stand besteht zusätzlich alle 433 dort enthaltenen Softwaretests. Die Differenz stammt aus anderen, bereits vorhandenen lokalen MK2-/Projektänderungen; diese gehören nicht zu diesem Commit.
- 14 Browser-Abläufe für Migration, beide Fade-Griffe, wirksame Kurveneditoren, Überlappungsgrenzen, Undo, Abbruch, Tastatur, kleine Ansicht und Speichern/Neuladen bestanden. Zusätzlich bestehen die 9 bisherigen Crossfade-Grifftests.
- 42 echte GPU-Fälle gegen die LED-Berechnung geprüft; größte Abweichung 0,001961 (8-Bit-Farbauflösung).
- Laufende TouchDesigner-Installation aktualisiert. Show **Test1** mit 15 Clips umgestellt und gespeichert; ursprüngliche Show und Dateien unter `.controller-runtime/timing-backups/` gesichert. Aufnahmekurven und gespeicherte Materialwerte unverändert, keine Operatorfehler. Aktives Material, Material-Modus und UV-Zuordnung beim Installieren erhalten.
- Keine erneute physische MK2-Abnahme behauptet. Die Browserrad-Beschleunigung wurde nicht geändert. Die sichtbaren Fade-Griffe bedient man in der Timeline; maximal zwei Clips können gleichzeitig laufen.

Einzelergebnisse: [Software](show-overlap-v1/acceptance.json), [Browser](show-overlap-v1/browser.json), [GPU](show-overlap-v1/gpu.json), [Live-Installation](show-overlap-v1/live-install.json), [Show-Umstellung](show-overlap-v1/live-migration.json). Der Bericht zur gesamten MK2-Abnahme führt die gesonderte physische Geräteprüfung weiterhin als offen.

[Isolierter Commit-Test](show-overlap-v1/staged-acceptance.json) · [Desktop-Vorschau](show-overlap-v1/timeline.png) · [Kleine Ansicht](show-overlap-v1/timeline-small.png)

```powershell
python -m unittest discover -s tests -p 'test_show*.py'
```

Die Tests decken Originalerhalt, Interpolation, beide A/B-Richtungen, Blackout, Cue-Zeiten, Undo/Redo, externe Änderungen, abgelaufene Befehle, HTTP-Übertragung und Zugriffsschutz ab. Die Browser-Bedienung wurde mit einer isolierten Testshow geprüft; die laufende reale Show wurde zur Anzeige und Integration verwendet.

## Material-Pads und MK2-Displays

In der Timeline **Material-Pads · MK2** öffnen und **Pad-Gruppe A–H** wählen. Jede Gruppe enthält 16 Karten wie auf der Hardware: Pads 1–4 unten, 13–16 oben. Beim ersten Einrichten übernimmt Gruppe A bis zu 16 unterschiedliche Materialien aus der Show. B–H starten leer. Vorhandene Belegungen werden übernommen.

1. Eine Pad-Karte anklicken. Das wählt die Browser-Zuweisung aus, ohne ein Material zu laden.
2. **Pad-Aktion** wählen: Material Player laden oder Show-Clip starten.
3. Material/Clip suchen, in **Zuweisung** auswählen, **Zuweisung speichern** drücken. „Pad leeren“ entfernt die Belegung. Alle acht Gruppen und Pad-Presets liegen projektweit in `config/material_pads.json` (Schema 2).
4. **MK2-Pads und Displays direkt verbinden** aktivieren. **STEP aus** wählt Material Mode: Pads laden ihre Presets. **STEP an** wählt Show Mode: Gruppen wählen Achterblöcke und Pads 1–8 einzelne Parameter. Die Browser-Aktion „Material laden“ bleibt ausdrücklich verfügbar; im Show-Modus bleibt die Show auf dem Ausgang.

Material Mode zeigt links das aktive Material mit Vorschau, rechts acht Parameter. Die oberen Tasten wählen TD/native Parameterseiten, die acht Encoder ändern die Werte. **BROWSE** öffnet die Materialliste; das große Rad wählt, sein Druck lädt. **SCENE** öffnet die Pad-Übersicht mit Zuordnen, getrenntem Preset-Edit und Bestätigungsdialogen. A–H wechseln die Gruppe. Ein unveränderter Presetentwurf schließt nach 20 Sekunden Inaktivität, ein veränderter fragt nach Save/Cancel.

Show Mode zeigt Clip, Laufzeit, Übergang und Fortschritt. Das große Rad wählt Clipdauer, Übergangstyp oder Übergangsdauer; Druck aktiviert/beendet die Bearbeitung. Änderungen gelten sofort. Encoder wirken nur während einer Aufnahme. **REC** erstellt eine neue Cue, **REC + ERASE** nimmt im bestehenden Clip auf und ersetzt nur die berührten Parameterkurven. Unberührte Kurven bleiben erhalten. REC beendet die Aufnahme. PLAY, < / > und RESTART bedienen den Transport.

Thumbnails sind statische Originalbilder, monochrom mit 256×64 Pixeln je Display. Die Browser-Vorschau zeigt dieselben übertragenen Pixel und zusätzlich farbige Pad-Karten. Gruppen und Pads verwenden RGB; obere Tasten und Transporttasten haben feste Farben und werden über Helligkeit/Blinken unterschieden. Vollständige Aufgaben, Randfälle und Abnahme: [MK2 v0.2.0 Spezifikation](MK2_CONTROL_SPEC_DE.md). Dauerhafter Gesamttest: `python tools/check_mk2_acceptance.py`.

Die direkte Oberfläche nutzt USB-HID der **MASCHINE MK2**, VID `17cc`, PID `1140`, Interface 2 auf Windows. Sie benötigt keinen MIDI-Eingang und ersetzt das separate Parameter-MIDI-Mapping nicht. Andere MASCHINE-Modelle verwenden andere Protokolle. Bei geschlossenem Browser bleibt die Verbindung aktiv; der Schalter beendet den Zugriff. Die Verbindung versucht nach Abziehen und Wiederanstecken automatisch erneut zu öffnen. Eine andere Anwendung darf das Gerät nicht exklusiv belegen.

Lokale Abhängigkeiten liegen unter `.controller-runtime/td311` für TouchDesigners Python 3.11 bzw. `.controller-runtime` für Python 3.12. Für eine Neuinstallation lassen sich die Pakete aus `tools/controller-requirements.txt` mit einem zur jeweiligen Python-Version passenden pip über `--target` in diesen Ordner installieren. Es werden weder Windows-Treiber noch Firmware oder NI-Templates geändert. Diese binären Bibliotheken sind nicht Teil des Git-Repositories.

Die USB-Paketformate orientieren sich an den Protokollinformationen im [Ardour MK2-Treiber](https://github.com/Ardour/ardour/blob/master/libs/surfaces/maschine2/m2_dev_mk2.cc). Die Implementierung rendert eigene Bildrahmen und überträgt nur geänderte 8-Zeilen-Bänder. HID-Zugriff und Bildkonvertierung laufen in einem separaten Worker; Geräteereignisse werden mit Versionsprüfung und Ablaufzeit an den TouchDesigner-Hauptthread übergeben.

`tests/test_show_pads.py` prüft Band-Adressen und Bilddaten, physische Pad-Reihenfolge, Druckfilterung ohne Wiederholungen beim Halten, veraltete Zuweisungen, Aufnahmesperre, Material-/Clip-Auslösung und Rücknahme bei Speicherfehlern. USB-Schreibbestätigungen belegen die Übertragung; die optische Hardwareanzeige und echte Pad-Betätigung müssen am Gerät bestätigt werden.
