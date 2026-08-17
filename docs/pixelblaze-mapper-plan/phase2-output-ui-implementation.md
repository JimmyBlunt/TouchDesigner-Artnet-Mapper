# Phase 2 OUTPUT(DMX) UI – isolierter Implementierungsstand

Stand: 13. August 2026

## Status

Der TouchDesigner-API-Endpunkt antwortete beim Implementierungsversuch wiederholt mit HTTP 404. Deshalb wurde der isolierte, idempotente Builder lokal vorbereitet und geprüft, aber noch nicht in die laufende Session ausgeführt.

Es wurden keine Produktionsnodes verändert und `project.save()` wurde nicht aufgerufen.

## Dateien

- `pixelblaze_mapper/phase2_output_ui_contract.py`
- `pixelblaze_mapper/build_phase2_output_ui.py`

## Zielstruktur in TouchDesigner

```text
/project1/pixelblaze_mapper/output_config
  config_live
  config_draft
  universe_live
  universe_draft
  validation
  interface
  callbacks
  click_revert_draft
  ui_panel
  ui_preview
  README_output_config
```

Der Builder darf ausschließlich diesen Nodebereich erzeugen oder aktualisieren.

## UI-Inhalt

- sichtbare Live-Baseline mit 3.714 GRB-Pixeln und 22 Universen;
- getrennte Live- und Draft-Tabellen;
- Mapbedarf, Kanalzahl, Allokation, Netzwerkparameter und Universenvorschau;
- Revert Draft als lokale UI-Aktion;
- `Review & Apply` sichtbar, aber deaktiviert;
- Blocked-Hinweis für fehlenden gemeinsamen Allokator und Transaktionscontroller;
- Capture-TOP mit 1.100 × 650 Pixeln.

## Allokatorbindung

`phase2_output_ui_contract.py` definiert nur Dataclasses und den Adaptervertrag. Es implementiert absichtlich keine konkurrierende Allokationslogik. Der kanonische Allokator ist inzwischen gebunden.

Kanonischer Adapterpunkt:

- `pixelblaze_mapper.dmx_config.build_plan(DmxConfig(...))`

`build_with_shared_allocator()` übersetzt den stabilen UI-Draft in `DmxConfig` und normalisiert ausschließlich das Resultat von `build_plan()`. Apply bleibt unabhängig davon gesperrt, bis der Transaktionscontroller freigegeben ist.

## Lokale Prüfung

- beide Python-Dateien mit `py_compile` geprüft;
- statische Live-Snapshot-Tabelle: 22 Zeilen;
- Summe der Pixelslots: 3.714;
- letztes Universum: 144 Pixel / DMX-Endkanal 432;
- gemeinsamer Allokator: `pixelblaze_mapper.dmx_config.build_plan` gebunden;
- Allokator-Ergebnis: 22 Universen, 11.142 flache Samples, Kapazität 3.740 Pixel;
- `tests/test_dmx_config.py` konnte in der aktuellen Python-3.12-Umgebung nicht über pytest gestartet werden, weil pytest dort nicht installiert ist; der direkte Adapter-/Baseline-Test und `py_compile` waren erfolgreich;
- keine OneDrive-Datei geschrieben.

## Ausführung nach Wiederherstellung des MCP/API-Zugriffs

In TouchDesigner:

```python
exec(open(
    r'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper/'
    r'pixelblaze_mapper/build_phase2_output_ui.py'
).read())
```

Danach sind erforderlich:

1. Screenshot von `/project1/pixelblaze_mapper/output_config/ui_preview`;
2. Node-Error-Prüfung für `/project1/pixelblaze_mapper/output_config`;
3. Kontrolle, dass `Review & Apply` deaktiviert ist;
4. Kontrolle, dass `/project1/dmxout1`, `DMX_Universes`, `Universe_Config` und die Routingtabelle unverändert blieben;
5. weiterhin kein `project.save()`.
