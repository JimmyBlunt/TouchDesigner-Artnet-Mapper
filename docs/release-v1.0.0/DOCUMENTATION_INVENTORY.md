# v1.0.0 Dokumentationsinventar

Stand: 18. Oktober 2026, Australia/Sydney.

## Aktuelle Hilfe

[HTML-Handbuch](index.html) · [Help-Katalog](help_catalog.json) · [Historische Unterlagen](historical-docs.html) · [Einzelbewertung aller Screens](SCREEN_ASSESSMENT_DE.md)

| Schlüssel | Dialog | Anleitung | Screenshot |
|---|---|---|---|
| launcher | `/project1/shortcut_hub/help_panel` | [Übersicht & Shortcuts](launcher.html) | [Erfasst](screenshots/launcher.png) |
| materials | `/project1/material_browser` | [Material Browser](materials.html) | [Erfasst](screenshots/materials.png) |
| library | `/project1/madmapper_library/ui_panel` | [MadMapper-Bibliothek](library.html) | [Erfasst](screenshots/library.png) |
| player | `/project1/madmapper_player_controls/ui_panel` | [Material Player](player.html) | [Erfasst](screenshots/player.png) |
| mapper | `/project1/pixelblaze_mapper/ui/canvas` | [Pixel Mapper](mapper.html) | [Erfasst](screenshots/mapper.png) |
| router | `/project1/multi_controller_output/ui_panel` | [Art-Net Router](router.html) | [Erfasst](screenshots/router.png) |
| output | `/project1/pixelblaze_mapper/output_config/ui_panel` | [Output-Status](output.html) | [Erfasst](screenshots/output.png) |
| show | `/project1/show_control/control_panel` | [Show laden, erstellen & spielen](show.html) | [Erfasst](screenshots/show.png) |
| gico | `/project1/multi_controller_output/gico_port_config/ui_panel` | [GICO-Portkonfiguration](gico.html) | [Erfasst](screenshots/gico.png) |
| layout | `/project1/layout_scene_editor/ui_panel` | [Layout & Panel-Ausrichtung](layout.html) | [Erfasst](screenshots/layout.png) |
| scan | `/project1/guided_scan/ui_panel` | [3D-Scan: Aufnahme bis Ergebnis](scan.html) | [Erfasst](screenshots/scan.png) |
| new_capture | `/project1/guided_scan/new_capture_panel` | [Neue Aufnahme](new_capture.html) | [Erfasst](screenshots/new_capture.png) |
| review | `/project1/guided_scan/review_panel` | [3D-Ergebnis prüfen](review.html) | [Erfasst](screenshots/review.png) |
| led_search | `/project1/guided_scan/led_search_panel` | [LED-Suche](led_search.html) | [Erfasst](screenshots/led_search.png) |
| ports | `/project1/multi_controller_output/gico_port_config/controller_ports/ui_panel` | [Controller & Ports](ports.html) | [Erfasst](screenshots/ports.png) |
| sequencer | `Web-Timeline / Unterdialog` | [Sequencer & Timeline](sequencer.html) | [Erfasst](screenshots/sequencer.png) |
| mk2 | `Web-Timeline / Unterdialog` | [MASCHINE MK2 · Kurzanleitung](mk2.html) | [Erfasst](screenshots/mk2.png) |
| midi | `Web-Timeline / Unterdialog` | [MIDI-Zuordnung](midi.html) | [Erfasst](screenshots/midi.png) |
| scan_library | `/project1/guided_scan/library_panel` | [Scan-Bibliothek](scan_library.html) | [Erfasst](screenshots/scan_library.png) |
| coverage | `/project1/guided_scan/coverage_visual_panel` | [Fehlende Bereiche](coverage.html) | [Erfasst](screenshots/coverage.png) |
| registration | `/project1/guided_scan/registration_panel` | [Teilscan ausrichten & ersetzen](registration.html) | [Erfasst](screenshots/registration.png) |
| native_params | `/project1/material_browser/native_parameter_drawer` | [Native Materialparameter](native_params.html) | [Erfasst](screenshots/native_params.png) |
| mk2_preview | `/project1/mk2_windows/preview_panel` | [MK2 Materialauswahl](mk2_preview.html) | [Erfasst](screenshots/mk2_preview.png) |
| pxlblz_manager | `Web-Timeline / Unterdialog` | [PXLBLZ / Art-Net Installation](pxlblz_manager.html) | [Erfasst](screenshots/pxlblz_manager.png) |

## Prüfgrenzen

- Native Zielpfade und zentrale Feldnamen wurden lesend im laufenden Projekt geprüft.
- Ablaufbeschreibungen sind mit den genannten Buildern und Runtime-Modulen abgeglichen.
- Nicht vorhandene Screenshots werden nicht durch künstliche UI-Bilder ersetzt.
- Historische Berichte bleiben unverändert und sind über den Archivindex eingeordnet.
- Physische MK2-Tasten, Kameraaufnahmen und Lichtausgabe sind keine automatische Folge eines Softwaretests.
- Nach neuen Screenshots `python docs/release-v1.0.0/generate_guides.py` ausführen, damit sie in den Seiten erscheinen.
