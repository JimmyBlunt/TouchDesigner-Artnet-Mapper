# Core 67 – gespeicherter Funktionsstand

Gespeichert am 25. August 2026 als
`Backup/Projektdatei/PixelblazeMapper_WORKING_PHASE2_EFFECTS_CORE.67.toe`.

## Material Browser

- Die sichtbaren Material-Thumbnails führen nun selbst eine Auswahl aus.
  Zuvor war nur der Textbereich der Karte verbunden, weshalb Klicks auf das
  Vorschau-Bild keine Änderung am Live-Material auslösten.
- Der Browser lädt seinen Katalog beim Start erneut, damit die 31 Kernmaterialien
  nach einem erneuten Öffnen verfügbar bleiben.
- Auswahl, Seitenwechsel, Gruppen-/Kompatibilitätsfilter und Layoutwechsel wurden
  automatisiert geprüft. Der aktive, wiederhergestellte Zustand ist
  `materials / matrix_rain`.

## LED-Ausgabe / Art-Net

- Die dokumentierte physische Aufteilung verwendet 510 Kanäle (= 170 RGB-Pixel)
  je Universum und vier Universen je Controller-Port.
- Routing der drei Seiten-Panels:
  - Mitte: Pixel 0–516 → U1–U4
  - Oben: Pixel 517–785 → U5–U6; U7–U8 bleiben schwarz
  - Unten: Pixel 786–1183 → U9–U11
- Der Controller ist auf GRB und die nullbasierte Art-Net-Drahtadresse eingestellt.

## Dialog-Check

- Klick-Handler in Material Browser, Material-Bibliothek, Show Control und
  Multi-Controller-Ausgabe wurden auf Scriptfehler geprüft.
- Sicherheitskritische Schaltflächen (Ausgabe abschalten, sichere Konfiguration
  anwenden, Materialdateien importieren) wurden nicht automatisch ausgelöst,
  damit die laufende LED-Ausgabe und bestehende Dateien nicht verändert werden.

## Versionsverwaltung

- Core 66 ist in Git als Commit `4da9c67` gesichert.
- Core 67 ist der vollständige aktuelle TouchDesigner-Speicherstand. Er wird mit
  dieser Dokumentation als Folgestand versioniert.
