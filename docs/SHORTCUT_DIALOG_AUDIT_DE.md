# Audit: neun Shortcut-Dialoge

Stand: Core 67. Dieses Dokument definiert die automatische, **nicht-destruktive**
Prüfung für alle per `Ctrl+Shift+1` bis `Ctrl+Shift+9` erreichbaren Dialoge.

| Shortcut | Dialog | Ziel | Automatisch geprüft | Nur beaufsichtigt ausführen |
|---|---|---|---|---|
| 1 | LED Preview | `LED_PREVIEW_OUT` | Zielpfad und Vorschau-Verknüpfung | – |
| 2 | Material Browser | `material_browser` | Suche, Filter, Seiten, Layout und Material-Karten über Runtime-Tests | Live-Vorschau |
| 3 | MadMapper Library | `madmapper_library/ui_panel` | Suche, Filter, Karten- und Seitenlogik | Katalog-Refresh, Import |
| 4 | Material Player | `madmapper_player_controls` | Zielpfad und Statusverknüpfung | aktiver Materialwechsel |
| 5 | Pixel Mapper | `pixelblaze_mapper/ui/canvas` | Zielpfad, 3D-/Mapping-Module | Mapping schreiben oder exportieren |
| 6 | Art-Net Router | `multi_controller_output/ui_panel` | Konfigurations- und Router-Tests | Output Off, Apply, Start, Kalibrierung |
| 7 | Output Config | `output_config/ui_panel` | Live-/Draft-Kontrakte und Validierung | Draft anwenden, Export |
| 8 | Show Control | `show_control/control_panel` | Sequencer-/Transportlogik | GO, Play, Stop, Blackout |
| 9 | Shortcut Help | `shortcut_hub/help_panel` | alle neun Zuordnungen, Navigation-only-Schutz | – |

## Testausführung

`python -m pytest tests/test_dialog_contracts.py tests/test_shortcut_hub.py`

Diese Tests senden weder Art-Net noch speichern sie das Projekt oder ändern ein
Mapping. Die Fachtests der jeweiligen Dialoge liegen zusätzlich unter `tests/`,
etwa `test_unified_material_browser.py`, `test_material_library_browser.py`,
`test_multi_controller.py`, `test_show_sequencer.py` und `test_mapper_io.py`.

## Sicherheitsgrenze

Ein echter Mausklick auf hardware- oder dateiwirksame Schaltflächen ist kein
sicherer automatischer Regressionstest: Er kann LEDs ausschalten, eine laufende
Show unterbrechen, Art-Net-Universen ändern oder Materialdateien importieren.
Die Tests verifizieren daher die Verdrahtung und die Callback-Logik; eine reale
Auslösung erfolgt nur als klar angekündigter, rücksetzbarer Abnahmetest.
