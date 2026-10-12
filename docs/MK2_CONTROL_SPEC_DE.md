# MASCHINE MK2 – Bedienungsspezifikation 0.2.0

Stand: 12. Oktober 2026. Grundlage: Nutzerbeschreibung und bestätigte Rückfragen.
Diese Datei ist Aufgabenliste und Abnahmegrundlage. Ein bestandener Softwaretest
ersetzt keine Prüfung der tatsächlichen Tasten, LEDs und Displays am Gerät.

## Zuständigkeiten und Lieferung

| Bereich | Agent | Lieferumfang |
|---|---|---|
| A – Bedienzustände, Navigation, Pad-Bänke | `mk2_workflow` | Zustandsmaschine, Konfigurationsmigration, dauerhafte Funktionstests |
| B – USB-Eingaben, Displays und LEDs | `mk2_hardware` | Hardware-Protokoll, Encoder-/Tastenerkennung, Anzeige je Zustand, Protokoll- und Bildtests |
| C – Material Player, Show und Aufnahme | `mk2_touchdesigner` | Adapter zu echten Parametern und Transport, Aufnahmeintegration, Funktionstests |
| D – Integration und Abnahme | Hauptagent | Browser-Konfiguration, dauerhafte Speicherung, Integrationstests, Versionsstand und getrennte Commits |

Jeder Bereich wird erst nach seinen Funktionstests als softwareseitig erledigt
geführt. Commits enthalten ausschließlich zugehörige Dateien; vorhandene fremde
Arbeitsänderungen werden nicht mitgenommen. Es wird kein Remote-Push ausgeführt.

## Gemeinsame Regeln

- **G01** STEP schaltet den Modus um: aktiviert = Show Mode; deaktiviert = Material Mode.
  Die Anzeige folgt auch einem Moduswechsel im Material Player.
- **G02** Der Grundzustand zeigt stets das tatsächlich aktive Material bzw. den
  tatsächlich laufenden Show-Clip, nicht eine nur hervorgehobene Browserauswahl.
- **G03** Acht obere Tasten wählen Parameterseiten, acht Encoder bearbeiten die
  acht Parameter der gewählten Seite, soweit der aktuelle Modus das erlaubt.
- **G04** Seite 1 heißt **TD** und enthält in dieser Reihenfolge: Master Speed,
  Scale, Width, Focus X, Focus Y, Frame Zoom, Intensity, Contrast.
- **G05** Native MadMapper-Parameter folgen in stabilen Achtergruppen. Fehlende
  Plätze bleiben leer; nicht unterstützte Parameter werden als solche angezeigt.
- **G06** Die Anzeigen verwenden Namen/Abkürzungen, Zahlen und umrahmte Wertebalken.
  Der Wertebereich stammt aus der tatsächlichen Parameterdefinition.
- **G07** Zuordnungen und Pad-Presets überleben einen Neustart. Acht Gruppen A–H
  enthalten je 16 Plätze. Die bisherige 16er-Bank wird verlustfrei nach A migriert.
- **G08** Gerätezugriff läuft außerhalb des TouchDesigner-Hauptthreads. Änderungen
  am Projekt werden ausschließlich auf dem Hauptthread ausgeführt. Alte bzw.
  abgelaufene Eingaben dürfen nach einem Zustandswechsel keine falsche Aktion auslösen.

## Material Mode

- **M01 – Grundanzeige:** Links aktiver Name und Vorschaubild mit „Material Mode“;
  rechts acht Parameter in zwei Spalten mit jeweils vier Zeilen. Die widersprüchliche
  zweite Nennung „linkes Display“ in der Rohbeschreibung wird als rechtes Display verstanden.
- **M02 – Seitenauswahl:** Oben erscheinen nur vorhandene Parameterseiten als
  Kästchen unter den zugehörigen Tasten. Ausgewählte Seite ist deutlich markiert.
- **M03 – Direkte Bearbeitung:** Die acht Encoder ändern ihre Parameter sofort.
  Normale Navigation verändert keinen anderen Parameter.
- **M04 – Browse:** BROWSE öffnet links die Materialliste. Rechts stehen Nummer,
  Name, Kategorie, vorhandene Gruppe/Pad-Zuordnung und Vorschaubild.
  Großes Rad navigiert, Druck lädt das ausgewählte Material und setzt es aktiv.
- **M05 – Pad-Übersicht:** SCENE zeigt die 16 Plätze der gewählten Gruppe, acht je
  Display, mit Rahmen und Materialname. Rad wählt einen Platz, Druck öffnet dessen Menü.
- **M06 – Pad-Menü:** Belegt: Select, Edit, Browse, Delete. Leer: nur Browse.
  „Edit“ ist ausdrücklich ergänzt, da die Rohbeschreibung danach diesen Ablauf fordert.
  Select aktiviert das gespeicherte Material einschließlich Preset.
- **M07 – Zuweisen:** Browse aus einem Pad öffnet die Materialliste. Rad-Druck
  führt zur Zusammenfassung mit Confirm/Cancel; Confirm ist vorausgewählt.
  Erst Confirm speichert die Zuordnung. Cancel lässt sie unverändert.
- **M08 – Preset bearbeiten:** Edit bearbeitet eine Kopie der Pad-Parameter.
  Das Material wird dadurch nicht aktiv. Save übernimmt, Cancel verwirft den Entwurf.
- **M09 – 20 Sekunden ohne Eingabe:** Unveränderter Entwurf kehrt zur Übersicht
  zurück. Bei Änderungen erscheint Save/Cancel; es wird weder still gespeichert
  noch still verworfen. Jede Bearbeitung setzt die Inaktivitätszeit zurück.
- **M10 – Gruppen und Pads:** A–H wechseln die Bank. Aktive Gruppe leuchtet hell,
  andere belegte Gruppen schwach blau. Ein betätigtes Pad blinkt kurz rot.
  Ein leerer Platz lädt nichts; eine nicht verfügbare Zuordnung meldet den Fehler.

## Show Mode

- **S01 – Grundanzeige:** Links laufender Material-/Clipname, „Show Mode“,
  Playing/Stopped bzw. Paused sowie abgelaufene und verbleibende Zeit.
- **S02 – Clipfortschritt:** Ein schmaler Balken zeigt den Fortschritt des aktuellen
  Clips und kennzeichnet Ein-/Ausblendungsbereiche. Er wird aus dem echten Transport berechnet.
- **S03 – Übergang:** Kleine, zum Übergangsmodus passende Grafik, deren Füllung
  den tatsächlichen Übergangsfortschritt zeigt. Zusätzlich Clipdauer,
  Übergangsmodus und Übergangsdauer als Text/Zahl.
- **S04 – Radbearbeitung:** Rad navigiert den Fokus zwischen Clipdauer,
  Übergangsmodus und Übergangsdauer. Druck wechselt zwischen Navigieren und
  Bearbeiten. Beim Drehen im Bearbeitungsmodus werden Werte sofort wirksam;
  der nächste Druck beendet nur die Eingabe, er ist kein späterer Apply-Schritt.
- **S05 – Parameteranzeige:** Obere Tasten wählen TD-/native Parameterseiten.
  Gruppen A–H wählen Achterblöcke; Pads 1–8 wählen darin den einzelnen Parameter
  für die große rechte Anzeige mit Name, Zahl und Reglerbalken.
  Gruppen/Parameter mit Automation bzw. Änderungen werden markiert.
  Diese Gruppen-/Pad-Bedeutung wurde vom Nutzer bestätigt.
- **S06 – Schutz vor versehentlicher Änderung:** Die acht kleinen Encoder
  verändern im normalen Showbetrieb keine Materialparameter.
- **S07 – REC:** Startet eine Aufnahme als neue Cue. Nochmaliges REC beendet
  die Aufnahme und Cue-Erstellung. Die vorhandene Funktion des Show-Editors bleibt maßgeblich.
- **S08 – REC + ERASE:** Spielt den vorhandenen Clip ab und nimmt Parameteränderungen
  in diesem Clip auf. Vorhandene Kurven der aufgenommenen Parameter werden ersetzt,
  neue Kurven ergänzt; nicht bearbeitete Kurven bleiben erhalten. Kein neuer Clip.
  Die Tastenkombination darf nicht vorab versehentlich eine neue Cue erzeugen.
- **S09 – Aufnahmebedienung:** Während beider Aufnahmearten stehen dieselben
  Parameterseiten und Encoderzuordnungen wie im Material Mode zur Verfügung.
  REC bzw. REC+ERASE blinken entsprechend der verfügbaren Hardwarebeleuchtung.
  Erneutes REC beendet die Aufnahme, ebenso ein ordentlich behandeltes Clipende.
- **S10 – Transport:** PLAY startet die Wiedergabe; < und > wechseln den Clip;
  RESTART beginnt die Show am Anfang. Während einer Aufnahme werden konfliktträchtige
  Modus-/Clipwechsel blockiert, bis die Aufnahme beendet ist.

## Hardwaregrenzen und konkretisierte Randfälle

- MK2-LCDs sind monochrom. Grüne/gelbe Übergangsbereiche werden durch unterschiedliche
  Muster ersetzt. Die Browserdarstellung darf Farbe nutzen.
- Die oberen acht Tasten haben festfarbige Beleuchtung, kein frei adressierbares RGB.
  Gewünscht blau/gelb wird dort durch schwach/hell ersetzt. Gruppen und Pads verwenden
  die tatsächlich vorhandenen RGB-Kanäle. Keine Softwareanzeige behauptet unmögliche Farben.
- BROWSE- und Pad-Auswahl laden nur nach der jeweils beschriebenen Bestätigung.
  Ein fehlgeschlagener Ladevorgang behält das bisherige Material.
- Presetänderungen werden bei Wechsel/Verlassen mit offenem Entwurf nicht still verloren.
- Namen dürfen abgeschnitten werden, wenn die Pixelfläche nicht reicht; Auswahl und
  Detailansicht müssen das Ziel weiterhin eindeutig erkennen lassen.
- Parameter außerhalb des gültigen Bereichs werden begrenzt. Unbekannte Materialien,
  ungültige Konfigurationen und getrennte Geräte erzeugen eine sichtbare Fehlermeldung.
- Bei mehr als acht Seiten/64 darstellbaren Parametern muss die Oberfläche den
  zusätzlichen Umfang kenntlich machen; keine stillschweigende falsche Zuordnung.
- Wiederverbinden darf weder einen gehaltenen Knopf als neuen Druck interpretieren
  noch alte Warteschlangeneingaben ausführen.
- Auch Transporttasten einschließlich ERASE haben feste LED-Farben. Die Aufnahme
  wird durch Blinken der vorhandenen Beleuchtung angezeigt.
- Native Bool-Werte und einzelne Vektorkomponenten sind aufnehmbar. Compile-Time-
  Schalter sind nur im Material Mode editierbar; Ereignisparameter werden als
  nicht editierbar angezeigt.
- Bei importierten Materialien wirken Intensity und Contrast während einer
  Überblendung auf das gemeinsame Mischbild. Getrennte Tonwertkorrektur beider
  Übergangspartner benötigt einen späteren Umbau der Render-Pipeline.

## Dauerhafte Abnahme

| Testgruppe | Nachzuweisen |
|---|---|
| A1 | Modusmatrix, acht Standardparameter, Seitenauswahl, Bankmigration A–H |
| A2 | Browse, Pad-Menüs, Zuweisungsbestätigung, Cancel ohne Mutation |
| A3 | Getrennter Presetentwurf, Save/Cancel, exakt 20 Sekunden Inaktivität |
| A4 | REC/ERASE in beiden Druckreihenfolgen, Debounce, Aufnahme-/Transport-Sperren |
| B1 | Reale Report-Adressen, erster Encoderwert als Basis, Umlauf/negative Drehung |
| B2 | Tastenflanken, kein wiederholtes Auslösen beim Halten, Pad-Druckfilter |
| B3 | Zwei vollständige 256×64-Bilder, alle Ansichten, Fortschritt/Werte ändern Bilddaten |
| B4 | LED-Berichte, unterstützte Farben/Helligkeiten, Blinkzustände und Wiederverbinden |
| C1 | Echte Parameterwerte/-bereiche, Materialwechsel, Vorschau ohne Aktivierung |
| C2 | Sofortige Clipänderung bei erhaltenem Transport, Abweisung ungültiger Werte |
| C3 | Neue Cue versus bestehender Clip, aufgenommene Kurven abspielbar, andere Kurven erhalten |
| D1 | Browser-Zuweisung pro Bank, persistente Datei, Neustart/Migration, Zugriffsschutz |
| D2 | Bestehende Show-/Timeline-Tests bleiben erfolgreich; keine fremden Änderungen im Commit |
| H1 | Am Gerät: STEP/BROWSE/SCENE, Rad samt Druck, acht Encoder, acht obere Tasten, A–H und Pads |
| H2 | Am Gerät: beide Displays, LED-Zustände, REC/ERASE/PLAY/< > /RESTART und tatsächliche Aufnahme/Wiedergabe |

H1/H2 bleiben offen, bis am physischen Controller geprüft. Die Prüfergebnisse,
Testbefehle, Commit-IDs und offene Abweichungen werden im Abschlussprotokoll ergänzt.

Die zusammenhängende Software-Simulation wurde für Version 0.2.1 durchgeführt:
[308 erfolgreiche Tests, Anforderungsmatrix und gefundene Fehler](mk2-v0.2.0/SIMULATION_DE.md).
