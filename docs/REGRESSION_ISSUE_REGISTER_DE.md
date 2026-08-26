# Vorläufiges Fehler- und Entscheidungsregister

Dieses Register wird während der neun Dialogaudits fortgeschrieben. Es enthält
noch keine Freigabe zur Umsetzung.

| ID | Bereich | Befund | Einstufung | Nächster Schritt nach Rücksprache |
|---|---|---|---|---|
| PERF-01 | Gesamtprojekt | Nur ca. 7,9 FPS mit sieben Viewern und 13,7 FPS ohne sie, Ziel 60 FPS | Blocker | Cook-/Packer-Profil auswerten und blockierenden Frame-Start-Pfad entkoppeln |
| PERF-02 | Material/Art-Net | 24 neue Material-/Packframes in 2,031 s, Sender wiederholt Zwischenframes | Blocker | getrennte Messwerte für Render-, Pack- und Sendefrequenz einbauen |
| MAT-01 | Material Browser | Speed ist global und wird nicht pro Material gespeichert | Hoch | Produktmodell für Default, Material-Override und Global Master festlegen |
| MAT-02 | Material Player | `absTime * Speed` erzeugt bei Speedänderung große Phasensprünge | Hoch | kontinuierlichen Phasenakkumulator entwerfen |
| MAT-03 | Material Browser | doppelte, überlagerte Regler; sichtbarer und wirksamer Speed widersprechen sich | Blocker | Builder idempotent machen und eine einzige bidirektionale Wertquelle verwenden |
| MAT-04 | Panelbewegung | Panels teilen eine Uhr, besitzen aber stark verschiedene UV-Spannen; lokale Panel-UVs fehlen | Hoch | lokale UV-/Panel-ID-Semantik mit Nutzer festlegen |
| OUT-01 | Output Config | sichtbare Pixel-, IP-, FPS-, Universe- und ArtSync-Werte sind veraltet | Blocker | Dialog 7 entweder an Router binden oder read-only zusammenfassen |
| OUT-02 | Output Config | Eingaben, Draft und sichtbare UI sind entkoppelt; berechnete Werte editierbar | Blocker | verbindlichen Zustandsadapter und read-only Ableitungen einführen |
| OUT-03 | Output Config | Revert/Review ohne sichtbare Wirkung; acht überlagerte Buttoninstanzen | Blocker | Builder-Idempotenz und Button-Routing korrigieren |
| PRE-01 | LED Preview | Farbkette 3744 Samples, Instanz-/Map-Pfad 3740; vier Indizes fehlen | Blocker | verbindliche Pixelanzahl und Missing-Policy festlegen |
| PRE-02 | LED Preview | 25 Mappingzeilen tragen `state=missing` | Hoch | betroffene Indizes dokumentieren und gegen physische LEDs abgleichen |
| PRE-03 | LED Preview | sichtbarer Panelstart 1154 widerspricht 1180/1184 im aktiven Aufbau | Blocker | eine kanonische Panelgrenze definieren und alle Anzeigen daraus speisen |
| PRE-04 | LED Preview | mehrere sichtbare Corner-/Kompatibilitäts-/Opacity-Werte wirken im Output nicht | Hoch | wirkungslose Altparameter entfernen oder korrekt anbinden |
| ROUTE-01 | Art-Net Router | mehrere Statustexte widersprechen live aktivem Sender und Universebereich | Blocker | Status ausschließlich aus aktivem Routerplan und Sender ableiten |
| ROUTE-02 | Art-Net Router | Mehrcontroller-Takt nutzt globales Maximum statt unabhängiger Raten | Hoch | per-Controller-Scheduling entwerfen und testen |
| SHORT-01 | Shortcuts | Legacy-Callback funktioniert in geprüften Fällen, ist aber versionsfragil | Mittel | auf aktuellen Callbackvertrag migrieren und Fokusmatrix automatisieren |
| HELP-01 | Alle Dialoge | Inline-Hilfe und eindeutige Wert-/Wirkungserklärung fehlen | Mittel | gemeinsames deklaratives `i`-Hilfesystem gemäß Spezifikation bauen |

## Bereits bestätigte positive Punkte

- 194 bestehende automatische Tests bestehen.
- Die aktuelle Software-Aufteilung für Mitte, Oben und Unten ist im Routerplan
  konsistent und 510-Byte-ArtDMX-Pakete sind korrekt aufgebaut.
- Material Browser und Player besitzen funktionierende zentrale Parameter-
  bindungen; das Problem liegt vor allem in Zustand, Semantik und Performance.
- Oberes, mittleres und unteres Panel erhalten denselben Quellframe; es gibt
  keine drei getrennten Materialuhren.
- `Strg+Umschalt+7` öffnet Output Config in den bisher geprüften realen
  Fokuszuständen.

