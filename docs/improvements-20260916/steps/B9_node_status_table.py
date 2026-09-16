"""B9 - Tabelle /project1/node_status: lebendig von tot unterscheidbar machen.

Das war der Hauptbefund der Analyse: nicht ein Fehler im Code, sondern dass
sich von aussen nicht erkennen laesst, welcher Zweig laeuft. Drei
konkurrierende LED-Vorschauen, von denen zwei nie gekocht haben; zwei
Wahrheiten ueber die LED-Positionen, von denen die aeltere produktiv
mitlaeuft; ein fertig verdrahteter, aber stillgelegter Show-Sequencer.

Ohne forensische Auswertung von totalCooks und cookFrame konnte niemand -
auch der Autor nicht - entscheiden, was gefahrlos anzufassen ist.

Die Tabelle loescht nichts und kostet keine Laufzeit. Sie haelt nur fest,
was am 16.09.2026 am laufenden System gemessen wurde. Statuswerte:
aktiv, ruhend, prototyp, stillgelegt, altlast, altlast-aktiv, tot,
verwaist, vorlage.

Die eigentliche Regel dahinter: wer einen Zweig veraendert, aktualisiert
hier die Zeile. Sonst verfaellt die Tabelle wie jede andere Dokumentation.
"""

PATH = '/project1'
NAME = 'node_status'

HEADER = ['pfad', 'status', 'befund', 'geprueft']
ROWS = [
    ('/project1/multi_controller_output', 'aktiv', 'Einziger aktiver Art-Net-Sender (artnet_510_sender_callbacks), 3 Controller, 59 Universen', '2026-09-16'),
    ('/project1/LED_PREVIEW_OUT', 'aktiv', 'Verbindliche Vorschau, >55.000 Cooks', '2026-09-16'),
    ('/project1/material_browser', 'aktiv', 'Katalog-Browser, 638 Eintraege', '2026-09-16'),
    ('/project1/madmapper_library', 'aktiv', 'Material-Bibliothek und ISF-Adapter', '2026-09-16'),
    ('/project1/layout_scene_editor', 'aktiv', 'Layout-/Szenen-Editor, 11 Objekte, 6241 LEDs', '2026-09-16'),
    ('/project1/guided_scan', 'aktiv', 'Scan-Workflow ueber MariMapper/COLMAP', '2026-09-16'),
    ('/project1/mcp_webserver_base', 'aktiv', 'MCP-Bruecke, Web Server DAT Port 9981', '2026-09-16'),
    ('/project1/show_control', 'ruhend', 'Fertiger A/B-Sequencer, transport=stopped, Source steht auf imported', '2026-09-16'),
    ('/project1/pixelblaze_mapper/preview3d', 'tot', 'preview_out nie gekocht (totalCooks 0, cookFrame -1); Treiber in B8 stillgelegt', '2026-09-16'),
    ('/project1/pixelblaze_mapper/preview3d/phase2_interaction_background_prototype', 'prototyp', '353 Knoten, seit Projektstart eingefroren; eigenes README erklaert die Absicht', '2026-09-16'),
    ('/project1/chopexec1', 'stillgelegt', 'Erzwang 1.776.293 Cooks auf script4 ohne Wirkung; in B1 abgeschaltet', '2026-09-16'),
    ('/project1/script1', 'tot', 'Genau ein Cook in Frame 534', '2026-09-16'),
    ('/project1/script2', 'tot', 'Genau ein Cook in Frame 534', '2026-09-16'),
    ('/project1/script3', 'tot', 'Genau ein Cook in Frame 534; NUM_LEDS fest auf 1154', '2026-09-16'),
    ('/project1/script4', 'tot', 'Kein Ausgang, NUM_LEDS fest auf 1152 gegen real 5545', '2026-09-16'),
    ('/project1/evaluate1', 'altlast-aktiv', 'Alte LED-Positionsquelle, laeuft noch produktiv parallel zu layout_apply/active_map_3d', '2026-09-16'),
    ('/project1/read_LED_map', 'altlast-aktiv', 'Teil derselben alten Positionskette', '2026-09-16'),
    ('/project1/LedMap', 'altlast-aktiv', 'Liest evaluate1 zellweise aus, 274 ms Erstaufbau', '2026-09-16'),
    ('/project1/legacy_source_mask', 'altlast', 'Speist ueber shuffle1/rename1/lookup1/merge1 eine Sackgasse, ~0,3 ms/Frame', '2026-09-16'),
    ('/project1/dmxout1', 'tot', 'active=False, bindet alte lokale Adresse 10.0.0.178', '2026-09-16'),
    ('/project1/esp_artnet_out', 'tot', 'Legacy-ESP-Bulk-Pfad, ersetzt durch multi_controller_output', '2026-09-16'),
    ('/project1/DMX_Universes_backup_pre_panels', 'altlast', 'Stand vor dem Panel-Ausbau, 9 statt 23 Zeilen', '2026-09-16'),
    ('/project1/dmxout1_routingtable_backup_pre_panels', 'altlast', 'Stand vor dem Panel-Ausbau', '2026-09-16'),
    ('/project1/BallsMatrix3___normalized_coordinates', 'verwaist', 'Keine Verbindungen, von keinem DAT referenziert', '2026-09-16'),
    ('/project1/backwall_10_panels_coordinates', 'verwaist', 'Archivstand', '2026-09-16'),
    ('/project1/backwall_panel_layout', 'verwaist', 'Archivstand', '2026-09-16'),
    ('/project1/schrankwand_only_normalized_coordinates', 'verwaist', 'Archivstand', '2026-09-16'),
    ('/project1/schrankwand_plus_backpanels_coordinates', 'verwaist', 'Archivstand', '2026-09-16'),
    ('/project1/Preview', 'verwaist', 'Palette-Komponente, Eingaenge unverbunden, nirgends referenziert', '2026-09-16'),
    ('/project1/material_card_*', 'tot', '25 Knoten der Vorgaengergeneration des Browsers, display=False', '2026-09-16'),
    ('/project1/select_material_*', 'tot', '25 Callbacks der Vorgaengergeneration, schreiben am Zustandssystem vorbei', '2026-09-16'),
    ('/project1/noise_Simplex4D', 'verwaist', 'Keine Ausgaenge', '2026-09-16'),
    ('/project1/readPixelBlaze_Table1', 'vorlage', 'Unveraenderter TouchDesigner-Stub', '2026-09-16'),
]


def apply():
    parent_op = op(PATH)
    table = parent_op.op(NAME) or parent_op.create(tableDAT, NAME)
    table.clear()
    table.appendRow(HEADER)
    for row in ROWS:
        table.appendRow(list(row))
    table.nodeX, table.nodeY = -1200, 1200
    return f'{table.path}: {len(ROWS)} entries'


def revert():
    table = op(PATH).op(NAME)
    if table:
        table.destroy()
        return f'{PATH}/{NAME} removed'
    return 'nothing to revert'
