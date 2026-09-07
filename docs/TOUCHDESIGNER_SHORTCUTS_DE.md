# TouchDesigner-Shortcuts

Diese Kürzel öffnen ausschließlich Bedienfelder und Vorschauen. Sie starten
keine DMX-Ausgabe, wechseln keinen Effekt und speichern das Projekt nicht.

Vor der Eingabe einmal auf eine freie Stelle im TouchDesigner-Netzwerk klicken.
Während ein Textfeld aktiv ist, kann das Textfeld den Tastendruck abfangen.

| Shortcut | Fenster | Wann verwenden? |
|---|---|---|
| `Strg+Umschalt+1` | LED PREVIEW | Verbindliche Schrank-/Fotoansicht mit den ausgerichteten LED-Panels kontrollieren. |
| `Strg+Umschalt+2` | MATERIAL BROWSER | Core- und bereits integrierte Materialien suchen und auswählen. |
| `Strg+Umschalt+3` | MADMAPPER LIBRARY | Externe MadMapper-Materialien durchsuchen, prüfen und importieren. |
| `Strg+Umschalt+4` | MATERIAL PLAYER | Das aktuelle Material ohne 3D-Mapping und seine Player-Steuerung prüfen. |
| `Strg+Umschalt+5` | PIXEL MAPPER | LED-Positionen, Koordinaten und Mapping-Dateien bearbeiten. |
| `Strg+Umschalt+6` | ART-NET ROUTER | Ziel-IP, lokale Schnittstelle, Universen, Helligkeit und sichere Ausgabe bedienen. |
| `Strg+Umschalt+7` | OUTPUT CONFIG | Schreibgeschützten Live-Status kontrollieren und bei Bedarf den Art-Net Router öffnen. |
| `Strg+Umschalt+8` | SHOW CONTROL | Cues, Übergänge, Wiedergabe und Blackout einer Show steuern. |
| `Strg+Umschalt+9` | SHORTCUT HELP | Diese Übersicht direkt in TouchDesigner öffnen. |
| `Strg+Umschalt+0` | GICO PORT CONFIG | Globale Universen pro Port sowie feste GICO-Portblöcke konfigurieren und vor dem sicheren Anwenden validieren. |
| `Strg+Umschalt+L` | LAYOUT + 2D EDITOR | Gemeinsamen Layout- und 2D-Fixture-Editor öffnen. |
| `Strg+Umschalt+G` | GUIDED SCAN | Geführten Scan vorbereiten und Messfortschritt prüfen. Das Öffnen startet keinen Scan. |
| `Strg+Umschalt+C` | CONTROLLER PORTS | Generische Controller und individuelle Portkapazitäten als Entwurf bearbeiten. |

Die Übersicht (`Strg+Umschalt+9`) bietet zusätzlich pro Zeile einen **OPEN**-Button.
Jeder Tastendruck beziehungsweise Klick prüft den aktuellen Operatorpfad. Fehlt ein
noch nicht installierter Dialog, meldet TouchDesigner `Shortcut target missing`
mit dem Pfad; kein anderer Dialog und keine Ausgabe werden stattdessen gestartet.

Die neuen Ziele sind `/project1/layout_scene_editor/ui_panel`,
`/project1/guided_scan/ui_panel` und
`/project1/multi_controller_output/gico_port_config/controller_ports/ui_panel`.
Die bisherige Ziffernbelegung 0–9 bleibt unverändert. L/G/C waren in der geprüften
projektinternen Shortcut-/Keyboard-Inventur frei; native Tastatur-/Fokuskonflikte
müssen bei der Live-Abnahme geprüft werden. Installation durch
`pixelblaze_mapper/build_shortcut_hub.py`; der Builder speichert das Projekt nicht.

## Verbindlicher Signalweg

`Aktives Material -> visual_source_switch -> res1 -> math1 -> Foto-Composite -> LED_PREVIEW_OUT`

`math1 -> Art-Net Router` läuft parallel zur Vorschau.

`LED_PREVIEW_OUT` ist die einzige verbindliche Hardwarevorschau und zeigt das
Schrankfoto mit den darauf ausgerichteten Rückwand- und Seitenpanels. Die Bilder im
Material Browser, in der MadMapper Library und im Material Player sind
Rohvorschauen für Auswahl und Diagnose.

## Sicherer Arbeitsablauf

1. Mit `Strg+Umschalt+2` ein Material auswählen.
2. Mit `Strg+Umschalt+4` das Rohmaterial prüfen.
3. Mit `Strg+Umschalt+1` das Ergebnis auf der gemappten Installation kontrollieren.
4. Erst danach mit `Strg+Umschalt+6` den Art-Net Router öffnen.
5. Helligkeit, IP, Universen und `Enabled` prüfen; anschließend bewusst starten.
6. Für einen sofortigen Stopp im Router `ALL OUTPUTS OFF` verwenden.

Nach Änderungen das `.toe`-Projekt mit `Strg+S` speichern, damit Shortcuts und
Bookmarks im Projekt erhalten bleiben.

## Foto-Kalibrierung und Universen

Die vollständige Einzelpunkt-Kalibrierung stammt aus
`PixelblazeMapper_WORKING_PHASE2_PHOTO.33.toe` vom 16.08.2026, 09:54 Uhr.
Sie enthält für jedes der zehn Rückwandfelder vier Ecken, also insgesamt 80
editierbare X-/Y-Werte. Die Werte liegen am COMP
`/project1/pixelblaze_mapper/preview3d/phase2_interaction_background_prototype`
auf der Parameterseite **Einzelfaecher**.

Im aktuellen 3.740-Pixel-Mapping beginnen die zehn Rückwandfelder bei
Quellpixel 1180. Ab dort folgen exakt zehn Blöcke mit je 256 Pixeln. Dieser
Wert gehört zur Vorschau-/Koordinatenstruktur und darf nicht mit einem
Art-Net-Startuniversum verwechselt werden.

Art-Net-Universen bestimmen ausschließlich, an welchen Empfänger die bereits
berechneten RGB-Werte gesendet werden. Eine geänderte Universe-Nummer kann die
Hardwareausgabe verschieben, ändert aber keine Foto-Ecke. Zum Wiederherstellen
der gespeicherten Einzelkalibrierung dient
`pixelblaze_mapper/restore_photo_calibration.py`; das Modul verändert weder
DMX-Nodes noch Netzwerkstatus und speichert das Projekt nicht automatisch.

Die Animationsachsen werden separat in `/project1/effect_sample_uv` angepasst.
Für die um −90° gerenderte Seitenwand gilt `U = ursprüngliches Y` als
vorne/hinten und `V = ursprüngliches X` als Höhe. Das ursprüngliche Z ist nur
die Relief-/Tiefenachse und darf die 2D-Animation nicht steuern. Dadurch laufen
vertikale Effekte auf Rückwand und Seitenpanels in derselben Richtung.
