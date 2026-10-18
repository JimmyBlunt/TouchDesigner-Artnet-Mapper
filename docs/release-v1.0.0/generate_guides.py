"""Rebuild the local, dependency-free release guide from its reviewed content.

Run from any directory. This only writes documentation beside this script.
Screenshots are captured separately from TouchDesigner; diagrams are illustrations.
"""
from pathlib import Path
import html
import json

ROOT = Path(__file__).resolve().parent
SCREENS = []


def field(description, example):
    return dict(description=description, example=example)


def screen(key, target, title, summary, steps, fields=None, source=None, details=None):
    SCREENS.append(dict(key=key, target=target, native=bool(target), title=title,
                        summary=summary, steps=steps, fields=fields or {},
                        howto=key+'.html', source=source or [], details=details or []))


screen('launcher', '/project1/shortcut_hub/help_panel', 'Übersicht & Shortcuts',
       'Der Einstieg in Material, Scan, Layout, Routing und Show. OPEN öffnet den jeweiligen Dialog.',
       ['Arbeitsbereich mit OPEN oder Ctrl+Shift+Taste öffnen.', 'Im Dialog oben i für die Kurzinfo oder HOW-TO für den vollständigen Ablauf wählen.', 'Vor einer echten Ausgabe im Router Ziel, Helligkeit und Status prüfen.'],
       source=['pixelblaze_mapper/shortcut_hub.py', 'pixelblaze_mapper/build_shortcut_hub.py'],
       details=[('Direkte Wege', 'Ctrl+Shift+1 LED-Vorschau · 2 Materialien · 3 Bibliothek · 4 Player · 5 Pixel Mapper · 6 Art-Net Router · 7 Output-Status · 8 Show · 9 Übersicht · 0 GICO-Ports · L Layout · G Scan · S LED-Suche · C Controller/Ports. Tastenkürzel greifen in TouchDesigner; ein fokussiertes Eingabefeld kann Tasten abfangen. Einmal in eine freie Fläche klicken.'),
                ('Beispielablauf', 'Material mit Ctrl+Shift+2 auswählen, mit Ctrl+Shift+1 auf den Schrank prüfen, über Ctrl+Shift+8 eine Cue erstellen und speichern. Router und Controller-Ports öffnen eigene Ansichten; Navigation startet keine LED-Ausgabe.')])

screen('materials', '/project1/material_browser', 'Material Browser',
       'Core-Effekte und importierte Materialien suchen, vorprüfen und aktivieren.',
       ['Suchbegriff und SOURCE/GROUP wählen, SEARCH / APPLY drücken.', 'Eine Materialkarte auswählen und Vorschau prüfen.', 'APPLY SELECTED aktiviert die Auswahl; Player und NATIVE PARAMS bearbeiten die Parameter.', 'Für eine Show im Show Editor + AKTUELLES MATERIAL verwenden.'],
       {'unified_search': field('Name oder Teil eines Materialnamens. Leeren zeigt wieder alle Ergebnisse.', 'Plasma'),
        'mb_control_zoom': field('Ausschnitt des Materials; größer zoomt in das Bild.', '1.0'),
        'mb_control_speed': field('Animationsgeschwindigkeit.', '1.0'),
        'mb_control_focusx': field('Horizontaler Bildfokus.', '0.5'),
        'mb_control_focusy': field('Vertikaler Bildfokus.', '0.5'),
        'mb_control_gradient_strength': field('Anteil des ausgewählten Farbverlaufs.', '0.5')},
       ['pixelblaze_mapper/build_unified_material_browser.py'],
       [('Material oder Show?', 'Der Quellschalter im Player entscheidet, was im LED-Pfad anliegt. Eine Show kann im Hintergrund laufen, obwohl Material als Quelle gewählt ist. Im Show-Modus ist eine Materialvorschau nicht automatisch die aktive LED-Quelle.'),
        ('Beispiel', 'Plasma suchen, eine verfügbare Karte auswählen und APPLY SELECTED drücken. Vorschau und Status kontrollieren, MASTER SPEED auf 1 und Fokus auf 0.5 setzen. Anschließend eine Cue im Show Editor anlegen. Fehlende oder nicht unterstützte Imports erst in der Bibliothek klären.')])

screen('library', '/project1/madmapper_library/ui_panel', 'MadMapper-Bibliothek',
       'Katalog durchsuchen, GLSL-Kompatibilität prüfen und Materialien in das Projekt importieren.',
       ['Material suchen und Karte auswählen.', 'Vorschau und Kompatibilitätsstatus lesen.', 'Import über die angebotene Bestätigung ausführen.', 'Das importierte Material im Material Browser auswählen und aktivieren.'],
       {'search_field': field('Suche im Materialkatalog.', 'Noise')},
       ['pixelblaze_mapper/build_material_library_browser.py', 'pixelblaze_mapper/build_unified_material_browser.py'],
       [('Prüfen statt raten', 'Eine Katalogkarte bedeutet noch keinen erfolgreichen GLSL-Import. Unsupported, Compile-Fehler oder fehlende Assets sind Abbrüche. Erst ein erfolgreicher Import mit gültiger Vorschau ist als Material nutzbar. Bei schwarzem Bild auch die Parameter und Quelle prüfen.'),
        ('Beispiel', 'Noise suchen, ein unterstütztes Material vorprüfen, Import bestätigen und anschließend im vereinheitlichten Browser unter IMPORTED finden. Dort aktivieren und eine Cue erstellen. Der vollständige Katalog und die Zahl importierter Materialien sind unterschiedliche Zählungen.')])

PLAYER_FIELDS = {
    'player_speed': field('Master-Geschwindigkeit 0–2; 0 hält die Materialzeit an.', '1'),
    'player_scale': field('Materialskalierung 0.1–4.', '1'),
    'player_width': field('Breitenparameter 0–1.', '0.5'),
    'player_focusx': field('Fokus X 0–1.', '0.5'),
    'player_focusy': field('Fokus Y 0–1.', '0.5'),
    'player_zoom': field('Bildzoom 0.25–8.', '1'),
    'player_intensity': field('Intensität 0–2.', '0.5'),
    'player_contrast': field('Kontrast 0.1–4.', '1'),
}
screen('player', '/project1/madmapper_player_controls/ui_panel', 'Material Player',
       'Aktive Quelle und Materialbild mit gemeinsamen Reglern kontrollieren.',
       ['Quelle Material oder Show bewusst wählen.', 'Material im Browser aktivieren und Player-Vorschau prüfen.', 'Gemeinsame Regler schrittweise verändern; RESET VIEW setzt den Bildausschnitt zurück.', 'Parameter für die Show als Cue übernehmen oder über Aufnahme aufzeichnen.'],
       PLAYER_FIELDS, ['pixelblaze_mapper/build_unified_material_browser.py', 'pixelblaze_mapper/build_player_source_switch.py'],
       [('Status lesen', 'SOURCE benennt die aktive Quelle. Die große Vorschau zeigt das Material vor dem geometrischen LED-Mapping. Die tatsächliche Position auf dem Schrank prüfst du in LED PREVIEW. Die angeforderte Ausgaberate im Router ist kein Beleg für tatsächlich erreichte FPS.'),
        ('Beispiel', 'Material aktivieren; Speed 1, Scale 1, Fokus X/Y 0.5 und Zoom 1 einstellen. Intensity vorsichtig auf 0.5 setzen. Soll die Show die Ausgabe steuern, anschließend explizit Show als Quelle wählen.')])

screen('mapper', '/project1/pixelblaze_mapper/ui/canvas', 'Pixel Mapper',
       'Bestehende Mapping-Ansicht zum Prüfen der LED-Koordinaten. Neue Panel-Geometrie wird über Scan und Layout integriert.',
       ['Koordinaten und LED-Vorschau ansehen.', 'Für einen Panel-Scan Layout öffnen und das konkrete Objekt auswählen.', 'Änderungen im Layout validieren, dann in der Schrankansicht gegenprüfen.'],
       source=['pixelblaze_mapper/build_led_preview_contract.py', 'pixelblaze_mapper/build_layout_scene_ui.py'],
       details=[('Panel 8', 'Die Installation behält 299 adressierbare Plätze für Panel 8. 296 davon besitzen neue Messpositionen; lokale IDs 1, 61 und 93 bleiben ohne Messposition und schwarz. Diese Lücken dürfen weder aufgefüllt noch durch Umnummerieren verschoben werden.'),
                ('Koordinaten', 'Im aktuellen Layout gilt X = Höhe, Y = rechts und Z = Tiefe. Für das ersetzte Panel zeigt das Dreieck nach unten; seine kürzere Seite zeigt zur Schrankmitte. Die Bildschirmprojektion ist keine neue Messung.')])

ROUTER_FIELDS = {
    'router_target_ip': field('IPv4-Ziel des ausgewählten Controllers.', '10.0.0.251'),
    'router_start_universe': field('Art-Net-Paketadresse ab 0, nicht eine um eins erhöhte Anzeige.', '156'),
    'router_brightness': field('Helligkeitsfaktor 0–1. 0.02 entspricht 2 Prozent.', '0.02'),
    'router_enabled': field('0 = deaktiviert; 1 = freigegeben. SAFE APPLY startet den Sender nicht.', '0'),
    'router_rate': field('Angeforderte Rate 1–120 FPS; tatsächlichen Durchsatz separat prüfen.', '30'),
    'cal_panel': field('Kalibrierziel aus der angebotenen Auswahl.', 'all'),
    'cal_pattern': field('Kalibriermuster: panel_id, rows, columns oder chase.', 'panel_id'),
    'cal_chase': field('Index für das gezielte Kalibriermuster, ab 0.', '0'),
    'extra_brightness': field('Helligkeit eines zusätzlichen Controllers, 0–1.', '0.02'),
}
for prefix in ('ws', 'apa'):
    for suffix, info in [('ip', field('IPv4-Ziel des Controllers; veraltete Karten sind ausgeblendet.', '10.0.0.244')), ('universe', field('Startuniversum des Controllers. Aktuelle dynamische Karte verwenden.', '0')), ('brightness', field('Helligkeitsfaktor 0–1.', '0.02')), ('enabled', field('Freigabe 0/1; startet allein keine Ausgabe.', '0'))]:
        ROUTER_FIELDS[prefix+'_'+suffix] = info
screen('router', '/project1/multi_controller_output/ui_panel', 'Art-Net Router',
       'Controller auswählen, Routen und Status prüfen, Änderungen sicher anwenden und Ausgabe bewusst starten.',
       ['Controller aus der Auswahl wählen; LIVE CONFIG und Route lesen.', 'IP, Startuniversum, Helligkeit, Rate und Freigabe prüfen.', 'APPLY SAFE DRAFT übernimmt gültige Einstellungen bei ausgeschalteter Ausgabe.', 'Erst nach Kontrolle START wählen. ALL OFF beendet die Ausgabe.', 'Portdetails über CONTROLLER / PORTS öffnen.'],
       ROUTER_FIELDS, ['pixelblaze_mapper/router_dynamic_ui.py', 'pixelblaze_mapper/build_multi_controller_output.py'],
       [('Beispiel ohne Lichtausgabe', 'PANEL8_251 auswählen, 299 Plätze und zwei benötigte Universen am passenden Port kontrollieren. Helligkeit 0.02 und Freigabe 0 sind ein sicherer Entwurf. SAFE APPLY prüfen, anschließend Status erneut lesen. Kein START für einen reinen Konfigurationstest.'),
        ('Status richtig verstehen', 'Configured, enabled, running, disabled-only und unassigned sind verschiedene Zustände. Zugeordnete Quellplätze sind nicht automatisch sichtbare Messpunkte. Ausdrücklich schwarze Lücken bleiben erhalten. LIVE BRIGHTNESS wirkt auf den laufenden Sender; es übernimmt keine anderen Entwurfsfelder.'),
        ('Konflikte', 'Wenn eine andere Ansicht die Konfiguration geändert hat, zuerst RELOAD verwenden und den Entwurf erneut prüfen. Der Router blockiert veraltete Ausgangsdaten. Neue Controller und Portkapazitäten werden in Controller/Ports angelegt.')])

screen('output', '/project1/pixelblaze_mapper/output_config/ui_panel', 'Output-Status',
       'Schreibgeschützte Zusammenfassung der aktuellen Art-Net-Ausgabe.',
       ['Controller-, Quell- und Ausgabestatus lesen.', 'Für Änderungen ART-NET ROUTER öffnen.', 'Nach einer Änderung hier die Zusammenfassung erneut prüfen.'],
       source=['pixelblaze_mapper/build_phase2_output_ui.py', 'pixelblaze_mapper/router_status_source.py'],
       details=[('Ein Status, eine Konfiguration', 'Diese Ansicht ist keine zweite Senderkonfiguration. Änderungen erfolgen im Art-Net Router. Damit verhindern sich widersprechende alte und neue Ausgangseinstellungen keine konsistente Anzeige.'),
                ('Beispiel', 'Bei einer schwarzen Schrankvorschau zunächst Quelle und Mapping prüfen. Bei gültiger Vorschau, aber dunkler Hardware Router-Freigabe, Senderstatus und Controllerziel prüfen. Die Statusanzeige allein belegt keine physische Lichtausgabe.')])

SHOW_FIELDS = {'ed_show_name': field('Bestehende Auswahl wird unter ihrem Dateipfad aktualisiert; ein geänderter Name erzeugt eine Variante unter shows/.', 'Schrank Abend v1'),
               'ed_cue_name': field('Lesbarer Name der ausgewählten Cue.', 'Intro Blau'),
               'ed_cue_duration': field('Cue-Dauer in Sekunden; positive Zahl.', '12'),
               'ed_cue_transdur': field('Übergangsdauer in Sekunden, innerhalb der zulässigen Cue-Dauer.', '2'),
               'ed_cue_brightness': field('Cue-Helligkeit 0–1; multipliziert sich mit weiterer Ausgangshelligkeit.', '0.5')}
screen('show', '/project1/show_control/control_panel', 'Show laden, erstellen & spielen',
       'Shows bestehen aus geordneten Cues mit Material, Dauer, Übergang und optionaler Automation.',
       ['Vor einem Showwechsel die aktuelle Show unter ihrem Namen speichern.', 'SHOW AUSWAEHLEN öffnen und eine gespeicherte Show wählen, oder NEUE SHOW beginnen.', 'Material aktivieren und + AKTUELLES MATERIAL drücken.', 'Cue auswählen, Name/Dauer/Übergang/Helligkeit eintragen und UEBERNEHMEN drücken.', 'Quelle Show wählen, Vorschau und Transport prüfen; dann SPEICHERN.'],
       SHOW_FIELDS, ['pixelblaze_mapper/build_show_editor.py', 'pixelblaze_mapper/build_show_picker.py', 'pixelblaze_mapper/show_catalog.py', 'pixelblaze_mapper/build_show_sequencer.py'],
       [('Vorhandene Show auswählen', 'SHOW AUSWAEHLEN und LADEN öffnen dieselbe Auswahlliste validierter Show-JSONs mit Namen, Cue-Anzahl und Dateinamen. Mit Weiter/Zurück durch die Seiten gehen; die Auswahl lädt die Show mitsamt ihren verfügbaren Begleitdateien. Vor NEUE SHOW oder Laden zuerst speichern: ein Showwechsel ersetzt den aktuellen Editorinhalt. Während einer Aufnahme ist Laden/Neu gesperrt. NEUE SHOW leert Cues, Automation und Materialzustände; der vorherige Datensatz bleibt zusätzlich als Sitzungssicherung erhalten.'),
        ('Eine Variante anlegen', 'Show laden, den Namen beispielsweise auf Schrank Abend v2 ändern und SPEICHERN drücken. Ohne Namensänderung wird die exakt ausgewählte Datei aktualisiert. Mit geändertem Namen entsteht ein neuer, aus dem Namen abgeleiteter Dateipfad. Unterschiedliche Schreibweisen können auf denselben Dateinamen fallen. Der Status zeigt den tatsächlich verwendeten Pfad.'),
        ('Cues bearbeiten', 'Eine Zeile wählt die Cue zur Bearbeitung. + AKTUELLES MATERIAL übernimmt die aktuelle Materialauswahl. DUPLIZIEREN erstellt eine weitere Cue; LOESCHEN entfernt die ausgewählte Cue. NACH OBEN/NACH UNTEN ordnen sie um. Die Pfeile bei Übergang, Koordinaten und Verlauf wählen die verfügbaren Werte. Eingabefelder werden mit UEBERNEHMEN übernommen. Bei nicht auflösbaren Material-IDs zuerst Import oder Zuordnung reparieren.'),
        ('Transport und Quelle', 'PLAY startet, PAUSE hält die aktuelle Position, STOP stoppt und setzt den Showtransport zurück. PREV/NEXT wechseln Cues; GO springt wie NEXT an den Anfang der nächsten Cue. Automatische Überblendungen entstehen aus der konfigurierten Showzeit. LOOP wiederholt die Show. BLACKOUT schaltet das Showbild schwarz; ALL OFF im Router beendet die Netzwerkausgabe. Quelle Show ist separat erforderlich, damit das Showbild im LED-Pfad liegt.'),
        ('Automation aufnehmen', 'Zuerst das Material der gewünschten Cue im Player bereitstellen. AUFNAHME startet eine Aufnahme in die ausgewählte Cue; AUFNAHME → NEUE CUE erzeugt dafür eine neue Cue. Währenddessen gemeinsame beziehungsweise unterstützte native Parameter verändern. Aufnahme erneut drücken zum Beenden. Den Hinweistext auf leere oder blockierte Aufnahmen prüfen, dann Timeline öffnen und Kurven sowie Wiedergabe kontrollieren. AUFNAHME LOESCHEN entfernt die Aufnahme der ausgewählten Cue.'),
        ('Vollständiges Beispiel', 'NEUE SHOW → Name Schrank Abend v1. Material Plasma wählen → + AKTUELLES MATERIAL → Name Intro Blau, Dauer 12, Übergang 2, Helligkeit 0.5 → UEBERNEHMEN. Zweites Material aktivieren und als zweite Cue ergänzen, Dauer 8 und Übergang 2 setzen. Crossfade wählen. Show als Quelle wählen, PLAY und beide Cue-Wechsel in der Vorschau prüfen. STOP → SPEICHERN. Danach über SHOW AUSWAEHLEN erneut laden und Namen, zwei Cues sowie Werte kontrollieren.'),
        ('Welche Dateien gehören zusammen?', 'shows/<name>.json enthält Cues; <name>.automation.json die Aufnahmen/Bearbeitungen; <name>.materials.json die importierten Materialzustände. Zum Übertragen alle drei Dateien zusammen sichern. Zusätzlich das TouchDesigner-Projekt speichern: Show speichern ist nicht dasselbe wie die gesamte .toe-Datei speichern.'),
        ('Weiterführend', 'Die separate Anleitung sequencer.html erklärt Timeline, Überlappungen und Kurven. mk2.html erklärt direkte MK2-Bedienung und die beiden Aufnahmegesten. midi.html beschreibt die alternative MIDI-Zuordnung.')])

GICO_FIELDS = {'universes_per_port': field('Fester Reservierungsblock pro Hardwareport; nicht nur aktueller Bedarf.', '4'),
               'first_universe': field('Erstes Art-Net-Universum ab 0.', '0')}
for number in range(1, 5):
    for suffix, info in [('label', field('Lesbarer Name dieses physischen Ports.', 'Front links')), ('enabled', field('Portfreigabe 0/1.', '0')), ('source', field('Erste globale Quell-LED; leer = unzugeordnet.', '0')), ('count', field('Anzahl der LED-Plätze auf diesem Port.', '299')), ('reverse', field('Quellreihenfolge umkehren: 0/1.', '0')), ('order', field('Netzwerk-Farbfolge des Ports.', 'RGB'))]:
        GICO_FIELDS[f'p{number}_{suffix}'] = info
screen('gico', '/project1/multi_controller_output/gico_port_config/ui_panel', 'GICO-Portkonfiguration',
       'GICO verwendet feste gleich große Universenblöcke pro physischem Port.',
       ['Reservierte Universen und Startuniversum gegen Hardwarekonfiguration prüfen.', 'Pro Port Name, Quelle, Anzahl, Freigabe und Farbfolge eintragen.', 'Entwurf validieren und sichere Übernahme ausführen.', 'Router-Status und LED-Vorschau erneut prüfen.'],
       GICO_FIELDS, ['pixelblaze_mapper/build_gico_port_config_ui.py', 'pixelblaze_mapper/build_port_topology_ui.py'],
       [('Reserve ist nicht Bedarf', 'Ein RGB-Universum transportiert 170 vollständige LEDs mit 510 Kanälen. 299 LEDs benötigen zwei Universen. Wenn die Hardware vier pro Port reserviert, bleibt der nächste Port trotzdem vier Universen weiter. Nicht belegte Reserve bedeutet keinen Fehler.'),
        ('Beispiel', 'Für einen neuen Entwurf erst die tatsächliche GICO-Portreserve ablesen. Dann zum Beispiel Quelle 0, Anzahl 299, reverse 0, RGB eintragen. Erst prüfen und anwenden; Controller/Ports ermöglicht die alternative unabhängige Portstruktur, wenn die Hardware sie unterstützt.')])

LAYOUT_FIELDS = {
    'initialfile': field('Geladene Layoutdatei; Anzeige, nicht direkt bearbeiten.', 'mappings/<gespeicherte-layoutdatei>.json'),
    'format': field('Importformat; auto erkennt unterstützte Dateien.', 'auto'),
    'objectname': field('Name für neues Objekt oder Scan.', 'Panel 8'),
    'sourcestart': field('Expliziter globaler Quellstart; erst Routen prüfen.', '0'),
    'scanrange': field('Originale Scan-IDs für den Import; leer = alle.', '0-298'),
    'localrange': field('Lokale IDs des gewählten Objekts für Scan/Ersetzen/Entfernen.', '0-298'),
    'expectedcount': field('Erwartete adressierbare Gesamtzahl, nicht Zahl erfolgreicher Messungen.', '299'),
    'objectno': field('Objektnummer aus der angezeigten Liste.', '8'),
    'mode': field('Maus-/Tastenaktion für das ausgewählte Objekt.', 'move'),
    'axis': field('Achse für Rotation oder Skalierung.', 'z'),
    'step': field('Schrittweite in Einheiten beziehungsweise Grad.', '0.01'),
    'controller': field('Controlleridentität aus der Live-Konfiguration, nicht IP.', 'PANEL8_251'),
    'port': field('Physischer Port, ab 1.', '1'),
    'preserverouting': field('Routen bei Übernahme bewusst erhalten; aktuellen Dialoghinweis beachten.', '1')}
for prefix, description, example in [('t', 'Translation: X Höhe, Y rechts, Z Tiefe.', '0'), ('r', 'Rotation in Grad um die genannte Achse.', '90'), ('s', 'Skalierung; 1 erhält die Größe.', '1')]:
    for axis in 'xyz': LAYOUT_FIELDS[prefix+axis] = field(description, example)
screen('layout', '/project1/layout_scene_editor/ui_panel', 'Layout & Panel-Ausrichtung',
       'Objekte importieren, ausrichten und als Entwurf prüfen, bevor das aktive LED-Mapping ersetzt wird.',
       ['Aktuellen Workspace exportieren und konkretes Objekt auswählen.', 'Scan importieren oder Ergebnis prüfen; Original-IDs und fehlende LEDs erhalten.', 'Position, Rotation und Skalierung im Entwurf einstellen.', 'VALIDATE / PREPARE prüfen und nur den geprüften Entwurf übernehmen.', 'Aktive Vorschau, Routen und Quellenzahlen nach der Übernahme vergleichen.'],
       LAYOUT_FIELDS, ['pixelblaze_mapper/build_layout_scene_ui.py', 'pixelblaze_mapper/layout_scene_adapter.py', 'pixelblaze_mapper/build_layout_apply.py'],
       [('Beispiel Panel 8', 'Lokaler Bereich 0–298, erwartete Zahl 299; gemessen sind 296 Punkte. Die IDs 1, 61, 93 bleiben Lücken. Das Dreieck zeigt nach unten, seine kürzere Seite zur Schrankmitte. Objektnummer nicht aus der räumlichen Position erraten: die Objektliste mit Namen und Provenienz prüfen.'),
        ('Ausrichten', 'X entspricht Höhe, Y rechts und Z Tiefe. Translation bewegt, Rotation dreht in Grad, Skalierung ändert die Größe. Erst eine Änderung setzen, Vorschau ansehen und gegebenenfalls Undo verwenden. SET TRANSFORM übernimmt die Transformationsfelder; eine Routenbindung ist ein eigener Entwurfsschritt.'),
        ('Rollback', 'Vorher exportierten Workspace und .toe-Sicherung aufbewahren. Undo betrifft den Entwurf; nach einer dauerhaften Integration den gesicherten Projekt-/Workspace-Stand nutzen. IDs, Zieloffsets und Controllerbindungen gehören zur Wiederherstellung, nicht nur sichtbare Punkte.')])

SCAN_FIELDS = {'camera': field('OpenCV-Gerätenummer; mit CHECK CAMERA prüfen.', '0'),
    'exposure': field('Kameraabhängige Belichtung; Vorschau entscheidet über brauchbare Werte.', '-10'),
    'threshold': field('Detektionsschwelle 0–254; helle LED klar vom Hintergrund trennen.', '160'),
    'source_ids': field('Quell-IDs der vorbereiteten Aufnahme; global bei bestehendem Objekt, lokal bei neuer Aufnahme.', '0-298'),
    'anchors': field('Optionale Verifikationsanker; werden aufgenommen, aber nicht ersetzt.', '0,20,40'),
    'views': field('Pfade vorhandener 2D-CSV-Ansichten, getrennt durch |.', 'C:/Scans/view1.csv | C:/Scans/view2.csv'),
    'workspace': field('Vorhandener Arbeitsordner für Aufnahmen und Rekonstruktion.', 'C:/Scans/panel8'),
    'python': field('Installierter Python-Interpreter für die Offline-Rekonstruktion.', 'C:/path/to/python.exe'),
    'packet_gap': field('Abstand zwischen Netzwerkpaketen in ms, 0–2.', '1'),
    'brightness': field('Scanhelligkeit in Prozent, 1–10; nicht Faktor 0–1.', '5')}
screen('scan', '/project1/guided_scan/ui_panel', '3D-Scan: Aufnahme bis Ergebnis',
       'Jeder Scanlauf nimmt genau einen Kamerablick auf. Mehrere Ansichten ergeben die neue 3D-Geometrie.',
       ['Objekt im Layout wählen oder NEW ACQUISITION vorbereiten; Routing prüfen.', 'CHECK CAMERA: ganzes Panel sichtbar, Belichtung und Schwelle einstellen; CLOSE CAMERA.', 'CHECK SCAN PLAN prüfen, START SCAN / NEXT VIEW für eine Ansicht.', 'Erst nach Ende Kamera versetzen; weitere Ansichten aufnehmen.', 'Mindestens zwei unterschiedliche CSV-Ansichten wählen; PREPARE 3D → START 3D → REVIEW RESULT.'],
       SCAN_FIELDS, ['pixelblaze_mapper/build_scan_session_ui.py', 'pixelblaze_mapper/guided_scan_live.py', 'pixelblaze_mapper/scan_result_review.py'],
       [('Vorbereitung', 'Ein bestehendes Panel aus Layout heraus scannen, damit Quell-IDs und Routing konsistent bleiben. Neue Aufnahme erst mit korrektem Controller, Portbereich und Anzahl vorbereiten. Andere Live-Ausgaben müssen aus sein. CHECK SCAN PLAN zeigt Ziel, Universen und Umfang; nach jeder relevanten Änderung erneut prüfen.'),
        ('Kamera und Aufnahme', 'CHECK CAMERA öffnen. Das ganze Panel muss scharf und die einzelne LED eindeutig erkennbar sein. Belichtung ist kamerabhängig; -10 ist ein Beispiel, keine Garantie. CLOSE CAMERA gibt das Gerät frei. START SCAN nimmt einen Blick auf; während des Laufs nichts bewegen. STOP SCAN beendet einen fehlerhaften Lauf. Erst bei Abschluss Kamera zum nächsten Blick versetzen.'),
        ('Rekonstruktion', 'In BUILD 3D / SAVED SCANS mindestens zwei tatsächlich verschiedene Ansichten auswählen. FIND MATCHING VIEWS hilft bei vorhandenen Aufnahmen; ADD VIEW CSV ergänzt gezielt. PREPARE 3D erstellt den geprüften Job, START 3D startet die Berechnung. REVIEW RESULT zeigt Abdeckung, fehlende IDs und Ergebnis. Kein automatischer Ersatz des aktiven Layouts.'),
        ('Beispiel mit 299 LEDs', 'Neue Aufnahme mit Count 299 erzeugt lokale IDs 0–298. Drei Ansichten mit überlappender Sicht aufnehmen, ihre CSV-Dateien auswählen und rekonstruieren. Werden 296 Punkte erkannt, bleiben 3 IDs ungemessen. Fehlende IDs nachscannen oder schwarz lassen; die Adressierung bleibt 299 Plätze breit.'),
        ('Wenn es nicht weitergeht', 'Kamera belegt: Vorschau oder andere Kamera-App schließen. Plan veraltet: CHECK SCAN PLAN erneut ausführen. Keine Punkte: Belichtung, Schwelle und Route prüfen. 3D-Jobfehler: Status und Arbeitsordner prüfen, vorhandene CSV-Dateien erhalten. Eine alte Ergebnisansicht ist kein Beleg für den zuletzt aufgenommenen Scan.')])

CAPTURE_FIELDS = {'name': field('Eindeutiger Name der Aufnahme.', 'Panel8_299'), 'target': field('IPv4 des Controllers.', '10.0.0.251'),
 'interface': field('Lokale Netzwerkkarte für Art-Net.', '10.0.0.125'), 'universe': field('Startuniversum des Panels, ab 0.', '156'),
 'count': field('Adressierbare LED-Anzahl, lokale IDs 0 bis count−1.', '299'), 'rate': field('Angeforderte Rate in FPS.', '30'),
 'order': field('Netzwerk-Farbfolge, nicht automatisch die physische LED-Verdrahtung.', 'RGB'),
 'frame_start_universe': field('Optionaler Start des ganzen Controllerframes; zusammen mit Anzahl ausfüllen.', '156'),
 'frame_universe_count': field('Optional: gesamte Universenanzahl des Controllers; andere Ports werden schwarz gesendet.', '7')}
screen('new_capture', '/project1/guided_scan/new_capture_panel', 'Neue Aufnahme',
       'Eine Aufnahme mit originalen lokalen IDs und Routing vorbereiten; das Layout bleibt zunächst unverändert.',
       ['Controllerkonfiguration und Netzwerkkarte ablesen.', 'Name, Ziel, Startuniversum, LED-Anzahl und Farbfolge eintragen.', 'Optional beide Controllerframe-Felder ausfüllen.', 'CREATE ACQUISITION (OUTPUT OFF) wählen und im Scan-Dialog den Plan prüfen.'],
       CAPTURE_FIELDS, ['pixelblaze_mapper/build_scan_session_ui.py'],
       [('Beispiel', 'Panel8_299, Anzahl 299. Die Zahlen 156 und 7 im Beispiel sind nur mit der dazu passenden Controllerkonfiguration gültig. Keine Universen aus anderen Panels übernehmen. Die Funktion erstellt die Aufnahmedefinition, startet weder Kamera noch Lichtausgabe und bindet noch kein Layoutobjekt.')])

REVIEW_FIELDS = {'name': field('Name für das neue Entwurfsobjekt.', 'Panel 8 neuer Scan'),
                 'offset': field('Wird jeder originalen Scan-ID hinzugefügt; gegen freie globale Quellplätze prüfen.', '0')}
REVIEW_FIELDS.update({key: value for key, value in LAYOUT_FIELDS.items() if len(key) == 2 and key[0] in 'trs' and key[1] in 'xyz'})
screen('review', '/project1/guided_scan/review_panel', '3D-Ergebnis prüfen',
       'Messpunkte, IDs und Ausrichtung prüfen und das Ergebnis als neuen Layoutentwurf übernehmen.',
       ['Ergebnispfad und Messzahl mit dem gerade beendeten Job vergleichen.', 'Fehlende IDs und globalen Offset kontrollieren.', 'Optionale Translation/Rotation/Skalierung einstellen.', 'ADD AS NEW DRAFT OBJECT wählen; im Layout ausrichten und validieren.'],
       REVIEW_FIELDS, ['pixelblaze_mapper/build_scan_session_ui.py', 'pixelblaze_mapper/scan_result_review.py'],
       [('Keine stillen Ergänzungen', 'Der Offset wird zu originalen IDs addiert. Fehlende IDs bleiben fehlend; das Werkzeug erfindet keine Koordinaten. Die Übernahme erzeugt ein neues Entwurfsobjekt, kein automatisches Überschreiben eines bestehenden Panels.'),
        ('Beispiel', 'Für Panel 8 Ergebnis mit 296 gemessenen Punkten und lokalem Bereich 0–298 prüfen. Erst dann im Layout den Ersatz vorbereiten. Ein im Dialog gespeicherter alter Scan mit anderer Punktzahl muss zuerst durch das richtige Ergebnis ersetzt werden.')])

screen('led_search', '/project1/guided_scan/led_search_panel', 'LED-Suche',
       'Eine konkrete LED beziehungsweise ihre Nachbarn sichtbar machen und die Portlänge überprüfen.',
       ['Controller-IP wählen und AUSGAENGE LADEN ausführen.', 'Gewünschten OUT mit aktuell gemeldeter Anzahl auswählen.', 'Lokalen Index eingeben und SHOW oder Lauﬂicht bewusst starten.', 'STOP beendet den Test; letzten Index und Status prüfen.'],
       {'controller': field('IPv4 des Controllers; die Ausgangsliste wird live geladen.', '10.0.0.251'),
        'index': field('Lokaler Index ab 0; bei 299 LEDs sind 0–298 zulässig.', '298')},
       ['pixelblaze_mapper/led_search.py', 'pixelblaze_mapper/led_search_ui.py'],
       [('Beispiel Panel 8', 'Controller und OUT 1 mit 299 LEDs wählen. Index 298 entspricht der 299. LED. SHOW markiert die ausgewählte LED weiß und benachbarte LEDs farbig. Das ist eine echte Lichtausgabe und kein reiner UI-Test. Der Einzeltest endet spätestens nach 30 Sekunden; STOP kann ihn früher beenden.'),
        ('Lauflicht', 'Das Lauflicht schreitet alle zwei Sekunden weiter. Bei der letzten tatsächlich sichtbaren LED STOP drücken und Index beziehungsweise Nummer festhalten. Der aktuelle Controllerframe wird vor dem Test neu geladen; andere Ports im gemeinsamen Frame bleiben schwarz.')])

PORT_FIELDS = {'load_id': field('Vorhandenen Controller aus der Auswahl laden; neue ID nur für NEW DRAFT.', 'PANEL8_251'),
 'target': field('Ziel-IPv4 des Controllers.', '10.0.0.251'), 'interface': field('Lokale IPv4 aus Schnittstellenauswahl.', '10.0.0.125'),
 'udp_port': field('UDP-Zielport für Art-Net.', '6454'), 'first_ui': field('Art-Net-Startuniversum ab 0.', '156'),
 'brightness': field('Helligkeitsfaktor 0–1.', '0.02'), 'rate': field('Angeforderte Rate FPS.', '30'),
 'enabled': field('Controllerfreigabe 0/1; sichere Übernahme startet nicht.', '0'), 'order': field('Standard-Netzwerkfarbfolge.', 'RGB'),
 'profile': field('gico_equal für gleiche feste Portblöcke; independent nur bei geeigneter Hardware.', 'independent'),
 'remove_number': field('Physische Portnummer, deren Entfernung als Entwurf vorbereitet wird.', '3')}
for index in range(6):
    for suffix, info in [('label', field('Lesbarer Portname.', 'Panel 8')), ('enabled', field('Portfreigabe 0/1.', '1')), ('source', field('Erste globale Quell-LED; leer = unzugeordnet.', '0')), ('pixels', field('Adressierbare LED-Plätze.', '299')), ('reserve', field('Reservierte Universen; mindestens benötigter Bedarf.', '2')), ('reverse', field('Reihenfolge umkehren: 0/1.', '0')), ('order', field('Netzwerk-Farbfolge.', 'RGB')), ('target', field('Zielpixel-Offset; leer = automatisch nach Portstruktur.', '0'))]:
        PORT_FIELDS[f'row{index}_{suffix}'] = info
screen('ports', '/project1/multi_controller_output/gico_port_config/controller_ports/ui_panel', 'Controller & Ports',
       'Gespeicherte Controller auswählen und ihre Portstruktur als geprüften Entwurf bearbeiten.',
       ['Controller in der Auswahlliste wählen und LOAD / REVERT verwenden.', 'Ziel, Schnittstelle, Profil und Portzeilen prüfen.', 'VALIDATE DRAFT zeigt Bedarf, Reserve und Paketadressen.', 'SAFE APPLY (OUTPUT OFF) übernimmt; danach Router und Zuordnungen gegenprüfen.'],
       PORT_FIELDS, ['pixelblaze_mapper/build_port_topology_ui.py'],
       [('Entwurf und Livezustand', 'Die Liste wird aus den konfigurierten Controlleridentitäten erzeugt. LOAD / REVERT verwirft den aktuellen Entwurf und lädt dessen aktuellen Zustand. NEW DRAFT ist für einen wirklich neuen Controller. ADD PORT und REMOVE PORT ändern zunächst den Entwurf. STAGE DELETE bereitet eine Löschung vor; nicht für einen gewöhnlichen Wechsel verwenden.'),
        ('Beispiel', 'PANEL8_251 laden. OUT 1 soll 299 LED-Plätze und mindestens zwei RGB-Universen besitzen. Quelle und Zieloffset müssen zur bestehenden Installation passen; sie dürfen nicht aus diesem Beispiel übernommen werden. VALIDATE DRAFT kontrolliert Kapazität und Überlappungen. SAFE APPLY hält die Ausgabe ausgeschaltet.'),
        ('Portzeilen', 'Benötigte Universen ergeben sich aus LED-Anzahl und Zieloffset. Reservierte Universen sind Hardwarekapazität. Quelle leer bedeutet unzugeordnet. Auf Folgeseiten weitere Ports prüfen. GICO behält vier feste Hardwareplätze; unbenutzte Ports deaktivieren, statt die Hardwarestruktur umzunummerieren.')])

screen('sequencer', '', 'Sequencer & Timeline',
       'Cues auf einer Zeitachse bearbeiten, Übergänge und Automationskurven prüfen und die Show speichern.',
       ['Im Show Editor TIMELINE öffnen und Verbindungsstatus abwarten.', 'Clip auswählen; Dauer, Übergang und optional Überlappungen einstellen.', 'Spur aufklappen, Automationspunkte bearbeiten und Vorschau spielen.', 'Loopbereich und Transport prüfen; SPEICHERN und gespeicherte Show erneut laden.'],
       {'duration': field('Clip-Dauer in Sekunden, mindestens 0.1.', '12'), 'fadeDuration': field('Übergangs-/Überlappungsdauer in Sekunden.', '2'),
        'clipFadeIn': field('Eigene Einblendung dieses Clips in Sekunden.', '1'), 'clipFadeOut': field('Eigene Ausblendung dieses Clips in Sekunden.', '1'),
        'loopStart': field('Beginn des Loopbereichs in Show-Sekunden.', '0'), 'loopEnd': field('Ende des Loopbereichs, größer als Start.', '20'),
        'pointTime': field('Zeitpunkt relativ zum Clip, in Sekunden.', '3.5'), 'pointValue': field('Wert im zulässigen Bereich des gewählten Parameters.', '0.5'),
        'snap': field('Rasterweite für Ziehen; Aus erlaubt freie Positionierung.', '0.5'), 'zoom': field('Zeitmaßstab der Timeline.', '10')},
       ['pixelblaze_mapper/timeline_assets/index.html', 'pixelblaze_mapper/timeline_assets/timeline.js', 'pixelblaze_mapper/show_timeline_ui.py', 'pixelblaze_mapper/show_timeline.py'],
       [('Orientierung', 'Oben stehen Showname, Verbindung, Play/Pause/Stopp und Speichern. Das Raster bestimmt die Einrastschritte, Zoom die Darstellung. Gesamte Show passt die Ansicht an; Playhead folgen scrollt mit. Rechts bearbeitet der Inspector die ausgewählte Cue oder den ausgewählten Automationspunkt.'),
        ('Clips und Übergänge', 'Clip anklicken zum Auswählen. Clip ziehen ändert Reihenfolge beziehungsweise Anordnung im jeweiligen Zeitmodus; rechten Rand ziehen ändert die Länge. Dauer übernehmen setzt den Zahlenwert. Übergangsart und Überblendung werden mit Übergang übernehmen bestätigt. Die Grenze des Übergangs kann direkt gezogen werden. Zurück/Vor macht Bearbeitungen rückgängig beziehungsweise wiederholt sie.'),
        ('Echte Überlappungen', 'Echte Überlappungen aktivieren stellt das Show-Zeitmodell um. Benachbarte Clips laufen während der Überlappung gleichzeitig. Die im Inspector angezeigte tatsächliche Überlappung prüfen. Eigene Ein-/Ausblendungen betreffen die Deckkraft des einzelnen Clips; sie sind unabhängig vom Übergang zwischen zwei Clips. Grüne/gelbe Griffe und Kurven wählen lineare, glatte oder beschleunigte Verläufe.'),
        ('Automation', 'Spur öffnen, um aufgezeichnete Parameter zu sehen. Doppelklick auf eine Kurve setzt einen Punkt; Ziehen verändert Zeit und Wert. Rechts die Werte genau eingeben und Punkt übernehmen drücken. Entf oder Punkt löschen entfernt den gewählten Punkt. Bearbeitung aktiv schaltet die Edit-Ebene; gestrichelte Kurven zeigen die Originalaufnahme. Original wiederherstellen entfernt die Bearbeitung dieser Spur zugunsten der Aufnahme.'),
        ('Loop und Navigation', 'Loop aktivieren, Start und Ende in Show-Sekunden setzen und Bereich übernehmen wählen. Ganze Show markieren spannt den Bereich über die Show. Zeitleiste anklicken setzt den Abspielkopf. Leertaste bedient Wiedergabe, Strg+Z Undo und Strg+Umschalt+Z Redo; ein Eingabefeld kann Tastendrücke selbst verwenden.'),
        ('Vollständiges Beispiel', 'Eine gespeicherte Show mit zwei Cues laden und TIMELINE öffnen. Erste Cue wählen, Dauer 12 übernehmen, crossfade und 2 Sekunden Übergang setzen. Zweite Cue auf 8 Sekunden setzen. Falls gewünscht echte Überlappungen aktivieren und die neue Gesamtzeit kontrollieren. Auf einer vorhandenen automatisierten Spur bei 3.5 Sekunden einen zulässigen Wert, etwa 0.5, setzen. Show spielen, Übergang visuell kontrollieren, stoppen und speichern. Show erneut auswählen und die Kurve sowie Timingwerte gegenprüfen.'),
        ('Weitere Dialoge', 'Material-Pads · MK2 öffnet Padzuweisung, Bankwahl und direkte Hardwareverbindung. MIDI · Controller öffnet Gerätewahl und Learn-Mapping. Diese beiden Anbindungen sind unterschiedliche Wege; die Display-/Tastenbedienung der direkten MK2-Anbindung wird in mk2.html erklärt.')])

screen('mk2', '', 'MASCHINE MK2 · Kurzanleitung',
       'Direkte HID-Steuerung mit acht Pad-Bänken, Materialparametern, Showtransport und Aufnahme.',
       ['In der Timeline Material-Pads · MK2 öffnen; direkte Verbindung und Status prüfen.', 'STEP wählt Material Mode oder Show Mode.', 'Material Mode: BROWSE und Rad wählen Material; SELECT weist es einem Pad zu.', 'Show Mode: Transport und Cuewerte bedienen; REC oder REC+ERASE nimmt Parameter auf.', 'Aufnahme beenden und Show samt Begleitdateien speichern.'],
       {'padSearch': field('Material oder Cue in der browserbasierten Zuweisung suchen.', 'Plasma'),
        'padBank': field('Eine von acht Bänken mit je 16 Pads.', 'A'),
        'padKind': field('Materialpreset oder Show-Cue als Pad-Aktion.', 'material'),
        'padTarget': field('Ziel aus dem tatsächlich verfügbaren Katalog auswählen.', 'Plasma')},
       ['pixelblaze_mapper/mk2_workflow.py', 'pixelblaze_mapper/mk2_td.py', 'pixelblaze_mapper/maschine_mk2.py', 'pixelblaze_mapper/timeline_assets/pads.js'],
       [('STEP / BROWSE / SCENE / SELECT', 'STEP wechselt Material/Show. BROWSE öffnet im Material Mode den Katalog auf dem MK2, SCENE die Pad-Bank. Rad drehen wählt Einträge, Rad drücken bestätigt. Die zusätzliche Desktop-Materialvorschau ist standardmäßig abgeschaltet; die Bilder auf den MK2-Displays bleiben erhalten. Auswahl, Laden und Player funktionieren weiterhin. In BROWSE aktiviert SELECT die direkte Padzuweisung: Bank A–H und Pad wählen; bei belegtem Pad das Überschreiben ausdrücklich bestätigen. BROWSE beziehungsweise SELECT im Zuweisungsbild bricht ab.'),
        ('Acht obere Tasten und acht Regler', 'Im Hauptbild wählen die oberen Tasten die angezeigten TD-/MM-Parameterseiten. Die acht Regler bearbeiten die sichtbaren Parameter dieser Seite. Im Browser sind Taste 1 ALL, Taste 2 FAV, Taste 3 CAT und Taste 8 der Favoritenumschalter. Nicht belegte Tasten sind in diesem Kontext ohne Aktion. CAT öffnet Kategorien; Rad wählen und drücken.'),
        ('Gruppen A–H und Pads 1–16', 'Im Material Mode wechseln A–H acht Presetbänke. Ein Pad lädt sein Material mit gespeicherten Werten. Im Show Mode ohne Aufnahme wählen A–H Parameterblöcke und Pads 1–8 den Parameter zur Anzeige; Pads 9–16 lösen dort keine Materialwechsel aus. Die physische Zählung beginnt unten links mit 1–4 und endet oben mit 13–16.'),
        ('Rad und Presetbearbeitung', 'Im Pad-Raster wählt das Rad einen Platz, Druck öffnet dessen Kontextmenü. Belegte Materialpads bieten select, edit, browse, delete; leere Pads browse. Bei edit verändern Regler zunächst den Presetentwurf. Rad drücken beziehungsweise der Bestätigungsdialog erlaubt Speichern oder Abbrechen. Während eines ungespeicherten Entwurfs verhindert die Steuerung unbemerkten Datenverlust.'),
        ('Transport', 'PLAY startet die Show; die links/rechts-Transporttasten wählen vorherige/nächste Cue. RESTART geht an den Showanfang und startet. Die direkte Belegung implementiert PLAY nicht als Pause-Umschalter. Pause und Stop sind in der Timeline beziehungsweise Show Control verfügbar. Die übrigen nicht in der Grafik belegten Hardwaretasten haben in diesem Projekt keine zugewiesene Aktion.'),
        ('Aufnahme: zwei verschiedene Gesten', 'Im Show Mode REC drücken und loslassen startet eine neue Cue-Aufnahme. REC zusammen mit ERASE startet Automation in der laufenden Cue. Dabei werden nur die während dieser Aufnahme berührten Parameterkurven ersetzt; andere bleiben bestehen. REC während einer Aufnahme beendet sie. ERASE allein löscht keine Automation. Außerhalb einer Aufnahme bleiben Encoder im Show Mode gegen unbeabsichtigtes Überschreiben gesperrt. Clipwechsel/Transport/Moduswechsel während Aufnahme sind blockiert; zuerst REC beenden.'),
        ('Showwerte mit dem Rad', 'Im Show-Hauptbild wählt das Rad Länge, Übergangsart oder Übergangsdauer. Drücken schaltet die Bearbeitung um; Drehen ändert den ausgewählten Wert, erneutes Drücken beendet die Bearbeitung. Die Unterstreichung zeigt den Fokus, die invertierte Darstellung den Bearbeitungszustand.'),
        ('Linkes und rechtes Display', 'Material Mode zeigt Materialbild und Name, Modus sowie Parameterseiten. Das sind monochrome Vorschaubilder, keine laufenden Farbanimationen. Show Mode zeigt Material, Playing/Paused/Stopped, vergangene und verbleibende Sekunden, Fortschrittsbalken und Übergangssymbol. Unten stehen Länge, Übergangsart und Dauer. Rechts stehen Parameterwerte beziehungsweise der gezielt gewählte Parameter. BROWSE zeigt Liste, Favoriten/Kategorien und Materialzuweisungen; Padansicht zeigt Bank und Belegung.'),
        ('Leuchten verstehen', 'Materialpads: belegte Plätze dunkelblau/türkis, Auswahl hell, Tastendruck kurz rot. Im Show-Parameterbetrieb markiert Gelb die Auswahl und Blau geänderte/automatisierte Parameter. Aktive Gruppe ist gelb; Gruppen mit Inhalt beziehungsweise Parameteraktivität sind schwächer blau. REC blinkt während Aufnahme; ERASE blinkt zusätzlich bei Automation. Obere und Transporttasten haben feste Hardwarefarben; nur Pads und Gruppen sind RGB.'),
        ('Beispiel ohne Überschreiben', 'STEP → Material. BROWSE → ALL → Material mit Rad wählen. SELECT → freie Bank B → leeres Pad 1. Dann SCENE → B → Pad 1 zum Laden. In der Timeline die Bank und Zuordnung überprüfen. Für eine Show zuerst eine eigene Variante speichern; STEP → Show → REC loslassen → Regler bewegen → REC stoppen → Timeline-Kurven ansehen → SPEICHERN.'),
        ('Konfiguration und Prüfgrenze', 'config/material_pads.json speichert Bänke, Favoriten und Presetwerte; config/mk2_windows.json die Fensteranordnung. Softwaretests und ein erfolgreicher USB-Status belegen nicht automatisch jede physische Taste, Displaylesbarkeit oder Lichtfarbe. Eine neue vollständige Hardwareabnahme muss als eigener Gerätetest dokumentiert werden.')])

screen('midi', '', 'MIDI-Zuordnung',
       'Alternative MIDI-Eingabe mit bewusst erlernten Adressen und gespeicherten Zuordnungen.',
       ['Timeline → MIDI · Controller öffnen und Eingabegerät wählen.', 'MIDI aktivieren, beim gewünschten Ziel Lernen drücken und Regler/Pad bewegen.', 'Ziel, Min/Max und relativen/absoluten Modus prüfen.', 'Mapping speichern; Live-Werte freigeben beendet temporäre Overrides.'],
       {'midiDevice': field('Tatsächlich angeschlossenes MIDI-Eingabegerät wählen.', 'MASCHINE MK2'),
        'midiEnabled': field('MIDI-Eingabe aktivieren oder abschalten.', 'aktiv')},
       ['pixelblaze_mapper/timeline_assets/index.html', 'pixelblaze_mapper/show_midi.py'],
       [('Direktes MK2 oder MIDI', 'Die direkte MK2-Anbindung verwendet HID für Displays und Tastenlogik. Der MIDI-Dialog arbeitet dagegen mit MIDI-Nachrichten und gelernten Adressen aus dem Controller-Template. Dieselbe Handbewegung darf nicht unbeabsichtigt über beide Wege wirken; den gewünschten Betriebsweg bewusst wählen.'),
        ('Beispiel', 'Für einen Regler das Ziel Speed wählen, passenden Bereich und CC-Modus setzen, Lernen drücken und den Regler einmal bewegen. Angezeigte Adresse und Werte prüfen, Mapping speichern. Live-Werte gelten bis zum Clipwechsel oder Freigeben; eine Aufnahme macht ihre Bewegung dauerhaft.')])


screen('scan_library', '/project1/guided_scan/library_panel', 'Scan-Bibliothek',
       'Gespeicherte Kameraansichten und 3D-Ergebnisse auswählen, zuordnen und für weitere Messungen wiederverwenden.',
       ['CHOOSE FOLDER wählen und REFRESH FILES ausführen.', 'Nach 2D VIEWS oder 3D RESULTS filtern, Einträge und Vorschau prüfen.', 'ADD SELECTED VIEWS ergänzt 2D-Dateien; REVIEW 3D öffnet ein Ergebnis.', 'RESUME ORIGINAL setzt eine gespeicherte Sitzung fort; MISSING oder WEAK bereitet einen neuen Teilumfang vor.'],
       {'folder': field('Scanordner; der Index berücksichtigt zwei Unterordnerebenen.', 'C:/Scans'), 'query': field('Suchtext in Datei- und Ordnernamen.', 'Panel8')},
       ['pixelblaze_mapper/scan_library_ui.py'],
       [('Gezielt auswählen', 'Die Bibliothek zeigt Dateien mit Kontext und einer Punktvorschau. Mehrere 2D-Ansichten können gemeinsam ausgewählt werden. CLEAR SELECTION leert nur die Auswahl, nicht die Dateien. PREVIOUS/NEXT blättert durch Treffer. ORBIT verändert nur den Blick auf die Vorschau.'),
        ('Beispiel', 'Den bisherigen Panel-8-Ordner öffnen, 2D VIEWS filtern und passende Ansichten auswählen. ADD SELECTED VIEWS ergänzt den Scan-Dialog. Einen zugehörigen 3D-Datensatz auswählen und REVIEW 3D öffnen. NEW SCOPE: MISSING beziehungsweise WEAK bereitet Nachmessungen vor, startet aber nicht selbst die Kamera.'),
        ('Originalkontext', 'RESUME ORIGINAL benötigt genau eine originale 2D-Ansicht mit gespeicherten Metadaten. REVIEW 3D benötigt genau ein candidate_3d.csv mit quality_pending.json. Andere 3D-Dateien lassen sich vorprüfen und über Layout importieren. MISSING bedeutet in den ausgewählten Ansichten nie erkannt; WEAK bedeutet weniger als dreimal erkannt. Beide Aktionen beginnen einen neuen Teilumfang mit leerer Ansichtsliste, behalten die Dateien aber auf der Festplatte. Eine gleich klingende Datei allein beweist weder dasselbe Panel noch dieselbe Quelle.')])

screen('coverage', '/project1/guided_scan/coverage_visual_panel', 'Fehlende Bereiche',
       'Messabdeckung in gespeicherten Kameraansichten prüfen und einen gezielten nächsten Kamerablick planen.',
       ['FEHLENDE BEREICHE ANZEIGEN im Scan oder Ergebnis öffnen.', 'Legende und Zahl ungemessener IDs lesen.', 'VORHERIGE/NAECHSTE ANSICHT oder MEISTE HINWEISE wählen.', 'Nach einer weiteren Aufnahme REFRESH drücken; dann Ergebnis erneut prüfen.'],
       source=['pixelblaze_mapper/scan_coverage_visual_ui.py', 'pixelblaze_mapper/scan_coverage_visual.py'],
       details=[('Legende', 'Türkis: 3D-Punkt mit mindestens drei Ansichten. Gelb: 3D-Punkt mit weniger als drei Ansichten. Orange: in 2D erkannt, aber noch kein 3D-Ergebnis. Violett: Nachbarstellen als Orientierung für Lücken. Diese Kategorien beschreiben die vorhandenen Messdaten, keine erfundenen Ersatzpositionen.'),
                ('Beispiel', 'Bei drei fehlenden Panel-8-IDs die Ansicht mit den meisten Hinweisen öffnen. Sichtbare Nachbarstellen helfen beim nächsten Blickwinkel. Nie erkannte LEDs können in keiner Kameraansicht lokalisiert werden. Zusätzliche Aufnahme aus neuer Perspektive machen, danach REFRESH und neue Rekonstruktion prüfen.')])

screen('registration', '/project1/guided_scan/registration_panel', 'Teilscan ausrichten & ersetzen',
       'Neue Messpunkte anhand fester Anker ausrichten und ausschließlich ausdrücklich akzeptierte IDs im Entwurf ersetzen.',
       ['Layoutobjekt und seinen abgeschlossenen 3D-Scan bereitstellen.', 'Mindestens drei Fit-Anker und einen unabhängigen Prüfanker wählen.', 'Ersatz-IDs und maximale Abweichung eintragen; CALCULATE drücken.', 'RMS, Einzelabweichungen, COMPARE POINTS und EVIDENCE prüfen.', 'Nur bei bestandener Prüfung REPLACE IN DRAFT bestätigen; Layout validieren.'],
       {'fit_ids': field('Mindestens drei feste, räumlich verteilte Quell-IDs außerhalb des Ersatzbereichs.', '0,20,40'),
        'check_ids': field('Separater fester Prüfanker, nicht beim Fit verwendet.', '60'),
        'accepted_ids': field('Nur rekonstruierte ausgewählte IDs, deren Position ersetzt werden soll.', '80-90'),
        'max_error': field('Zulässige Abweichung in den Koordinateneinheiten des Zielobjekts; begründet wählen.', '0.01')},
       ['pixelblaze_mapper/scan_registration_ui.py', 'pixelblaze_mapper/scan_registration.py'],
       [('Voraussetzungen', 'Mindestens vier bereits vermessene feste LEDs außerhalb des Ersatzbereichs dienen als Anker: drei für die Anpassung und mindestens eine für eine unabhängige Kontrolle. Die Zahlenbeispiele sind kein gültiger Satz für jedes Panel. Anker müssen tatsächlich in alter Geometrie und neuem Scan vorhanden sein.'),
        ('Ergebnis lesen', 'PASS bedeutet, dass Fit- und Prüfabweichung die eingestellte Grenze einhalten. RMS fasst Abweichungen zusammen, worst zeigt den schlechtesten Punkt. COMPARE POINTS zeigt alte/neue Koordinaten und Verschiebung pro Ersatz-ID. EVIDENCE zeigt den Vorschlag im Detail. Ein zu großzügiger Grenzwert macht schlechte Messungen nicht gut.'),
        ('Ersetzen und zurücknehmen', 'REPLACE IN DRAFT fordert eine ausdrückliche Bestätigung der gelisteten IDs. Anker und übrige LEDs behalten Position und Identität. Bei veränderten Eingaben erneut CALCULATE verwenden. Die Änderung ist im Layout mit Undo rücknehmbar; die Originalscans bleiben erhalten. Die aktive Ausgabe wird dadurch nicht automatisch umgeschaltet.')])

screen('native_params', '/project1/material_browser/native_parameter_drawer', 'Native Materialparameter',
       'Materialeigene GLSL-Parameter getrennt von den gemeinsamen Player-Reglern bearbeiten.',
       ['Im Material Browser ein verfügbares Material aktivieren und NATIVE PARAMS öffnen.', 'Parameterzeile wählen; Typ, Bereich und aktuellen Wert prüfen.', 'Sichtbare Komponentenregler oder typabhängige Aktion verwenden.', 'Vorschau prüfen und ZURUECK ZU MATERIALIEN wählen.'],
       {f'native_param_editor_{i}': field('Komponente des gewählten Parameters; Bereich und Bedeutung hängen vom Material ab.', '0.5') for i in range(4)},
       ['pixelblaze_mapper/build_unified_material_browser.py'],
       [('Typgerechte Bedienung', 'Eine Zahl verwendet einen Regler, Vektor/Farbe mehrere Komponenten, diskrete Typen eine passende Aktion. Nicht jedes Material besitzt dieselben Felder. Ereignisse und Compile-Time-Parameter sind nicht beliebig als kontinuierliche Showautomation aufnehmbar; Meldungen und den angebotenen Typ beachten.'),
        ('Beispiel', 'Ein importiertes Material aktivieren, NATIVE PARAMS öffnen und einen kontinuierlichen Helligkeits-/Geschwindigkeitsparameter wählen. Wert im angezeigten zulässigen Bereich verändern und Vorschau vergleichen. Für dauerhaft reproduzierbare Bedienung ein Preset speichern oder eine unterstützte Showaufnahme erstellen.')])
SCREENS[-1]['embedded'] = True

screen('mk2_preview', '/project1/mk2_windows/preview_panel', 'MK2 Materialauswahl',
       'Optionale Desktop-Standbildvorschau; standardmäßig abgeschaltet. Die normale Materialauswahl erfolgt auf dem MK2.',
       ['Am MK2 BROWSE öffnen und mit dem Auswahlrad ein Material wählen.', 'Materialname und Vorschau auf den MK2-Displays prüfen; es öffnet automatisch kein zusätzliches Desktopfenster.', 'Das Rad drücken, um die gewählte Auswahl zu laden.', 'Das geladene Material bei Bedarf im Player oder in LED PREVIEW prüfen.'],
       source=['pixelblaze_mapper/mk2_material_preview.py', 'pixelblaze_mapper/mk2_windows.py'],
       details=[('Standardverhalten', 'Die Desktop-Vorschau ist deaktiviert, damit das Durchblättern keine zusätzliche große Vorschau erzeugt. BROWSE und das Auswahlrad arbeiten auf dem MK2; die Displaybilder, das Laden per Rad und der Player bleiben erhalten. Daraus folgt keine gemessene Aussage über die physische Drehgeschwindigkeit oder Latenz.'),
                ('Erhaltener optionaler Dialog', 'Der vorhandene Desktopdialog bleibt aus Kompatibilitätsgründen im Projekt und in der Hilfe dokumentiert. Er wird nur bei ausdrücklich gesetztem desktop_browse_preview: true in config/mk2_windows.json automatisch verwendet; der Release-Standard ist false. Diese Option ist für die normale MK2-Auswahl nicht nötig.'),
                ('Anzeige bei ausdrücklich aktivierter Vorschau', 'Oben stehen Materialname und Status, darunter ein eingefrorenes Bild. Vorschau (Standbild) bedeutet eine erzeugte Materialvorschau. Gespeichertes Vorschaubild bezeichnet einen Thumbnail-Fallback, Vorschau nicht verfügbar eine fehlende verwendbare Vorschau. Ein Thumbnail bestätigt keine Shader-Kompatibilität. Das Standbild aktiviert selbst kein Material und ist keine laufende Schrank-LED-Vorschau.'),
                ('Bedienung und Beispiel', 'BROWSE → ALL → Material auf dem MK2 wählen → Namen und Displaybild prüfen → Rad drücken. Erst die Ladeaktion aktiviert die Auswahl. Das zusätzliche Desktopfenster muss dazu weder geöffnet noch bedient werden.')])

screen('pxlblz_manager', '', 'PXLBLZ / Art-Net Installation',
       'Die TouchDesigner-Anlage als geprüftes Paket an das separate lokale PXLBLZ Studio und seinen Art-Net-Router übergeben.',
       ['Im Layout oder Pixel Mapper PXLBLZ / ART-NET öffnen; Status prüfen.', 'Exportpaket erstellen; Werte und maskierte Plätze prüfen.', 'Ausgabe testen · lokal ausführen; anschließend die Pattern-Koordinaten wählen und PXLBLZ synchronisieren.', 'Routing anwenden; die TouchDesigner-Ausgabe wird zuvor gestoppt.', 'Pattern-Vorschau prüfen; erst danach Ausgabe einschalten. Ausgabe stoppen beendet die Ausgabe.'],
       {'projection': field('Pattern-Koordinaten: entfaltete 2D-Fläche oder räumliche 3D-Positionen.', 'surface'),
        'routeSelect': field('Vorhandenen Ausgang für einen Änderungsentwurf wählen.', 'Tatsächlichen Routennamen aus der Liste wählen'),
        'target_ip': field('Ziel-IP des ausgewählten realen Controllers.', '10.0.0.251'),
        'physical_port': field('Physischer Port des ausgewählten Controllers, ab 1.', '1'),
        'pixel_start': field('Erster globaler Quellplatz, ab 0; aus der vorhandenen Route übernehmen.', '0'),
        'pixel_count': field('Adressierbare LED-Plätze dieser Route einschließlich maskierter IDs.', '299'),
        'universe_start': field('Erstes Art-Net-Universum, nullbasiert; mit dem Controller abgleichen.', '156'),
        'color_order': field('Physische Kanalreihenfolge des gewählten Ausgangs.', 'BGR'),
        'brightness': field('Helligkeitsfaktor von 0 bis 1.', '0.1'),
        'localIndex': field('Lokaler LED-Index im gewählten Ausgang, ab 0. Der Leuchttest sendet real.', '0')},
       ['tools/pxlblz_manager/ui.html', 'tools/pxlblz_manager/manager.mjs', 'tools/pxlblz_manager/service.mjs', 'pixelblaze_mapper/pxlblz_manager_ui.py'],
       [('Voraussetzungen und Einstieg', 'Der Manager läuft unter http://127.0.0.1:9990. Seine Oberfläche ist im Repository enthalten; er benötigt außerdem Node.js, das separat installierte PXLBLZ Studio mit lokalen Entwicklungsabhängigkeiten und den PXLBLZ-Router. Die Pfade und lokalen Dienste stehen in tools/pxlblz_manager/settings.json. Auf einem anderen Rechner diese Installation zuerst bereitstellen und Pfade anpassen. Der native Button startet den Manager und öffnet die Seite. Ctrl+Shift+S bleibt LED SEARCH.'),
        ('Prüfung und Export', 'Status prüfen liest TouchDesigner und die Router-Konfiguration und zeigt Unterschiede. Exportpaket erstellen schreibt Map, Aktivmaske, Routing, Layout-Sicherung und Prüfsummen in einen neuen Paketordner. Automatisch reparieren erstellt ableitbare Konfigurationen erneut; es vermisst keine LEDs und vergibt keine neuen IDs. Ausgabe testen · lokal nutzt ausschließlich einen Testempfänger auf diesem PC und bestätigt keine physische LED-Ausgabe.'),
        ('Statuszahlen und Verbindungsfehler', 'Die Zahlen und Ausgangsliste können aus dem zuletzt gespeicherten Exportpaket stammen. Bei Noch keine Prüfung oder fetch failed sind sie kein aktueller Live-Nachweis. Zuerst lokale TouchDesigner-, Studio- und Router-Dienste prüfen, dann Status prüfen und bei geänderter Anlage ein neues Exportpaket erstellen. Die Paketkapazität, die Zahl zugeordneter Layoutpunkte und die maskierten Ausgangsplätze sind unterschiedliche Größen.'),
        ('Synchronisieren und Anwenden', 'PXLBLZ synchronisieren verlangt einen bestandenen Test des aktuellen Pakets und unveränderte TouchDesigner-Quelldaten. Es erzeugt eine neue Map und eine Pattern-Kopie; das Originalpattern bleibt erhalten. 2D-Fläche ist für Flächenpatterns, 3D-Raum für räumliche Patterns. Die Aktion 2D-Fläche + Smooth-Trail-Test anlegen erzeugt das entsprechende Diagnosepattern. Routing anwenden verlangt das getestete und synchronisierte Paket, stoppt den TouchDesigner-Sender und liest die angewandte Router-Konfiguration zurück. Ausgabe einschalten ist ein zusätzlicher Schritt.'),
        ('Ausgang bearbeiten: vollständiges Beispiel', 'Status prüfen → Exportpaket erstellen → Ausgang in der Liste wählen → dessen aktuelle Werte ablesen. Bei einem Panel mit 299 Adressplätzen zählt pixel_count auch absichtlich maskierte Stellen; niemals nur die gemessenen 296 eintragen. Eine erforderliche Korrektur eingeben → Änderung als Entwurf speichern → Ausgabe testen · lokal → PXLBLZ synchronisieren → Routing anwenden → Vorschau prüfen. Diese Reihenfolge gilt nach jeder Paketänderung erneut. Die Beispielwerte in der Tabelle sind unabhängig und bilden keine direkt anwendbare komplette Route.'),
        ('Einzelne LED und Wiederherstellung', 'Einzelne LED testen · 0,75 s ist ein echter Hardwaretest am gewählten Ausgang. Vorher Ausgang, Index und Helligkeit prüfen. Letzten Stand wiederherstellen spielt die zuletzt gesicherte Router-Konfiguration und den Managerzustand zurück. Importierte Map-/Pattern-Kopien bleiben als wiederverwendbare Einträge erhalten. Prüfbericht und Dateien bietet Downloads für Map, Aktivmaske, Routing und Layout-Sicherung. Der Paketordner und Status zeigen, welche Version gerade gilt.')])
SCREENS[-1]['web_source'] = 'tools/pxlblz_manager/ui.html'


def workflow_svg(item):
    # Vertical layout keeps complete instructions legible, even on narrow screens.
    height = 92 + 110 * len(item['steps'])
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 {height}" role="img" aria-label="Ablauf {html.escape(item["title"])}">',
             '<rect width="960" height="100%" rx="20" fill="#101820"/>',
             '<style>text{font-family:Bahnschrift,Segoe UI,Arial,sans-serif;fill:#e1e5e6}.n{fill:#55d6e7;font-size:22px;font-weight:700}.t{font-size:18px}</style>',
             f'<text x="32" y="46" font-size="22">{html.escape(item["title"])} · Ablauf</text>']
    import textwrap
    for i, step in enumerate(item['steps']):
        y = 72 + i * 110
        parts += [f'<rect x="24" y="{y}" width="912" height="90" rx="12" fill="#232a25"/>',
                  f'<text class="n" x="46" y="{y+40}">{i+1:02d}</text>']
        for line_no, line in enumerate(textwrap.wrap(step, 83)):
            parts.append(f'<text class="t" x="100" y="{y+30+line_no*24}">{html.escape(line)}</text>')
        if i < len(item['steps'])-1: parts.append(f'<path d="M60 {y+94}v12m-4-4 4 4 4-4" stroke="#aeb7ba" fill="none"/>')
    return ''.join(parts)+'</svg>'


STYLE = '''*{box-sizing:border-box}body{margin:0;background:#0b111b;color:#e8eef6;font:16px/1.65 "Segoe UI",Arial,sans-serif}a{color:#83d9bd}header{padding:32px max(24px,calc((100vw - 1160px)/2));border-bottom:1px solid #263448;background:#101a28}header a{text-decoration:none}main{max-width:1160px;margin:0 auto;padding:32px 24px 70px}.eyebrow{font-size:12px;letter-spacing:.15em;text-transform:uppercase;color:#83d9bd}h1{font-size:clamp(30px,4vw,48px);line-height:1.15;margin:12px 0 20px;font-weight:650}h2{font-size:23px;margin-top:36px}h3{font-size:18px}p{max-width:88ch}.lede{font-size:20px;color:#b8c8da;max-width:75ch}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}.card,section.note{padding:24px;background:#142032;border:1px solid #263448;border-radius:14px}.card h2{margin:0 0 10px}.card a{text-decoration:none}table{width:100%;border-collapse:collapse;margin:20px 0;font-size:14px}th,td{text-align:left;vertical-align:top;padding:12px;border-bottom:1px solid #2a384c}th{color:#83d9bd}code{font-family:Consolas,monospace;font-size:.88em;overflow-wrap:anywhere;color:#c3ddf0}img{max-width:100%;height:auto;border-radius:12px;border:1px solid #263448}figure{margin:28px 0}figcaption,.muted{font-size:13px;color:#9aabc0}ol{padding-left:26px}li{margin:9px 0}.badge{display:inline-block;padding:3px 10px;background:#1a3540;color:#9de4ce;border-radius:20px;font-size:12px}.toc{display:flex;gap:10px;flex-wrap:wrap;margin:24px 0}.toc a{padding:6px 12px;background:#1a293b;border-radius:8px;text-decoration:none}.back{font-size:14px}footer{border-top:1px solid #263448;padding-top:20px;margin-top:40px;color:#9aabc0;font-size:13px}.tablewrap{overflow:auto}@media(max-width:650px){main{padding:24px 18px}th,td{padding:8px}table{font-size:12px}}@media print{body,header{background:white;color:#172336}a{color:#176b59}.card,section.note{background:white;border-color:#bbb}footer,.muted,figcaption{color:#555}img{max-height:700px;object-fit:contain}}'''


def page(title, body):
    return f'<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} · PixelblazeMapper</title><link rel="stylesheet" href="guide.css"></head><body><header><a href="index.html">PIXELBLAZEMAPPER <span class="badge">v1.0.0</span></a></header><main>{body}<footer>Dokumentationsstand 18. Oktober 2026 · Sydney. Anleitungen aus Projektquellen und lesender Live-Prüfung. Beispiele sind keine automatische Konfigurationsänderung. Hardwareabnahme siehe Prüfbericht.</footer></main></body></html>'


def generate():
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT/'diagrams').mkdir(exist_ok=True)
    (ROOT/'screenshots').mkdir(exist_ok=True)
    chosen_style = STYLE.replace('"Segoe UI",Arial,sans-serif', 'Bahnschrift,"Segoe UI",Arial,sans-serif')
    chosen_style += '''
/* Final user-approved text roles; comparison studies retain their original palettes. */
body{background:#101820;color:#e1e5e6}header{background:#101820;border-color:#354139}
h1,h2,h3,th{color:#e1e5e6}a,.eyebrow,.toc a,.badge{color:#aeb7ba}
.lede,.muted,figcaption,footer{color:#a9b2b5}
.card,section.note{background:#232a25;border-color:#354139}
.toc a,.badge{background:#232a25}code,td:last-child code{color:#55d6e7}
th,td,img,footer{border-color:#354139}
@media print{body,header{background:white;color:#172336}h1,h2,h3,th{color:#172336}a,code{color:#176b59}.card,section.note{background:white}}
'''
    (ROOT/'guide.css').write_text(chosen_style, encoding='utf-8')
    (ROOT/'help_catalog.json').write_text(json.dumps({'schema': 1, 'version': '1.0.0', 'locale': 'de-DE', 'screens': SCREENS}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    for s in SCREENS:
        (ROOT/'diagrams'/f'{s["key"]}-workflow.svg').write_text(workflow_svg(s), encoding='utf-8')
        body = f'<div class="eyebrow">Bedienung / {s["key"]}</div><h1>{html.escape(s["title"])}</h1><p class="lede">{html.escape(s["summary"])}</p><nav class="toc"><a href="#ablauf">Ablauf</a><a href="#details">Schritt für Schritt</a><a href="#felder">Eingaben</a><a href="index.html">Alle Dialoge</a></nav>'
        body += '<section id="ablauf"><h2>In welcher Reihenfolge?</h2><ol>'+''.join('<li>'+html.escape(step)+'</li>' for step in s['steps'])+'</ol></section>'
        body += f'<figure><img src="diagrams/{s["key"]}-workflow.svg" alt="{html.escape(s["title"])}: Ablaufdiagramm"><figcaption>Bedienablauf als Diagramm. Keine simulierte TouchDesigner-Aufnahme.</figcaption></figure>'
        screenshot = ROOT/'screenshots'/f'{s["key"]}.png'
        if screenshot.exists():
            body += f'<figure><a href="screenshots/{s["key"]}.png"><img src="screenshots/{s["key"]}.png" alt="TouchDesigner: {html.escape(s["title"])}"></a><figcaption>Reale Anwendungserfassung des Release-Prüflaufs. Angezeigte Werte sind ein Beispielzustand, keine Vorlage zum blinden Übernehmen.</figcaption></figure>'
            if s['key'] == 'mk2_preview':
                body += '<p class="muted">Diese Aufnahme dokumentiert den erhaltenen optionalen Desktopdialog. Im aktuellen Standardbetrieb bleibt dieses Fenster beim Durchblättern geschlossen.</p>'
        if s['key'] == 'mk2':
            body += '<figure><img src="diagrams/mk2-controls.svg" alt="Schematische MK2-Belegung mit nummerierten Pads"><figcaption>Beschriftete Belegung aus dem aktuellen Controller-Code; schematisch, kein Hardwarefoto.</figcaption></figure>'
        if s['key'] in ('show', 'sequencer'):
            animation = 'show-workflow.gif' if s['key'] == 'show' else 'sequencer-overlap.gif'
            if (ROOT/'diagrams'/animation).exists():
                body += f'<figure><img src="diagrams/{animation}" alt="Animierte schematische Erklärung des Showablaufs"><figcaption>Animierte Ablaufgrafik, keine Bildschirmaufnahme. Die Arbeitsschritte und Werte werden im folgenden Text zusätzlich erklärt.</figcaption></figure>'
        body += '<section id="details"><h2>Schritt für Schritt</h2>'
        for title, text in s['details']: body += f'<h3>{html.escape(title)}</h3><p>{html.escape(text)}</p>'
        body += '</section><section id="felder"><h2>Eingaben & Beispiele</h2>'
        if s['fields']:
            body += '<div class="tablewrap"><table><thead><tr><th>Feld</th><th>Bedeutung</th><th>Beispiel</th></tr></thead><tbody>'
            for name, info in s['fields'].items(): body += f'<tr><td><code>{html.escape(name)}</code></td><td>{html.escape(info["description"])}</td><td><code>{html.escape(str(info["example"]))}</code></td></tr>'
            body += '</tbody></table></div><p class="muted">Numerische Eingaben verwenden einen Punkt als Dezimaltrennzeichen. IPs, Pfade, Quellstarts und Universen zuerst mit der tatsächlichen Installation vergleichen.</p>'
        else: body += '<p>Dieser Bildschirm benötigt für den beschriebenen Prüfablauf keine Texteingabe.</p>'
        body += '</section><section class="note"><h3>Woran erkenne ich Erfolg?</h3><p>Die erwartete Ansicht öffnet, Status und Vorschau entsprechen der gewählten Aktion, und es erscheint kein Fehler. Änderungen beim nächsten Laden beziehungsweise im Live-Status erneut lesen. Ein erfolgreicher Bildschirmtest beweist weder physische LED-Ausgabe noch korrekte Kameramessung.</p></section>'
        body += '<h2>Quellennachweis</h2><p class="muted">Dateipfade im Projekt-Repository; die Onlinehilfe gibt keinen allgemeinen Dateisystemzugriff frei.</p><ul>'+''.join(f'<li><code>{html.escape(p)}</code></li>' for p in s['source'])+'</ul>'
        if s['target']: body += '<p class="muted">Dialog: <code>'+html.escape(s['target'])+'</code></p>'
        (ROOT/s['howto']).write_text(page(s['title'], body), encoding='utf-8')
    cards = ''.join(f'<article class="card"><div class="eyebrow">{i+1:02d} / {s["key"]}</div><h2><a href="{s["howto"]}">{html.escape(s["title"])}</a></h2><p>{html.escape(s["summary"])}</p></article>' for i,s in enumerate(SCREENS))
    body = '<div class="eyebrow">Bedienhandbuch · Major Release</div><h1>Vom Scan zur Show.</h1><p class="lede">Alle Arbeitsbereiche, ihre Reihenfolge und konkrete Eingabebeispiele. Kleine Kurzinfos bleiben direkt im Dialog; hier stehen die vollständigen Abläufe.</p><nav class="toc"><a href="show.html">Show starten</a><a href="scan.html">Panel scannen</a><a href="mk2.html">MK2-Belegung</a><a href="historical-docs.html">Historische Unterlagen</a><a href="design/index.html">Fünf Designvarianten</a></nav><section class="note"><h2 style="margin-top:0">Aktueller Installationsumfang</h2><p>10.330 Quellplätze im LED-Datenpfad sind nicht 10.330 neu gemessene LEDs. Panel 8 besitzt 299 adressierbare Plätze und 296 gemessene Positionen. IDs 1, 61 und 93 bleiben schwarz. Das Dreieck zeigt nach unten, die kürzere Seite zur Schrankmitte.</p><p>Releaseprojekt: <code>PixelblazeMapper_v1.0.0.toe</code>. Prüfberichte trennen Software, Live-UI und physische Hardware. Maßgeblich sind die finalen Release-Nachweise, nicht ältere Testergebnisse.</p></section><h2>Welchen Dialog brauchst du?</h2><div class="cards">'+cards+'</div>'
    (ROOT/'index.html').write_text(page('Bedienhandbuch', body), encoding='utf-8')
    historical = '<div class="eyebrow">Dokumentation / Archiv</div><h1>Historische Unterlagen</h1><p class="lede">Frühere Anleitungen und Prüfberichte bleiben als nachvollziehbare Versionsgeschichte erhalten. Ihre Dateinamen, LED-Zahlen, Controllerrollen und Testergebnisse beschreiben den damaligen Stand.</p><p>Für die aktuelle Bedienung gilt das <a href="index.html">v1.0.0-Handbuch</a>. Alte .toe-Dateinamen oder Installationsadressen nicht ungeprüft übernehmen.</p><table><tr><th>Unterlagen</th><th>Einordnung</th></tr>'
    for link,label,reason in [('HOWTO_CURRENT_SYSTEM_DE.md','Frühere Systemanleitung','Historischer Stand trotz des Dateinamens CURRENT.'),('TEST_REPORT_2026-08-18_DE.md','Testbericht August','Ergebnisse gelten für den damaligen Build.'),('MK2_CONTROL_SPEC_DE.md','MK2-Spezifikation','Anforderungen; keine alleinige aktuelle Abnahme.'),('mk2-v0.2.0/ABNAHME_DE.md','MK2 v0.2.0','Historische Implementierung und getrennte Hardwaregrenzen.'),('panel8-rescan-299-20261018/AUFNAHME_DE.md','Panel-8-Aufnahme','Scanvorbereitung vor dem inzwischen integrierten Ergebnis.'),('panel8-replacement-20261018','Panel-8-Ersatz','Mess- und Integrationsbelege; konkrete Dateien im Repository prüfen.')]:
        if (ROOT.parent/link).exists(): historical += f'<tr><td>{label}<br><code>docs/{link}</code></td><td>{reason}</td></tr>'
    historical += '</table><p>Weitere datierte Ordner unter docs/ sind Belege ihres jeweiligen Prüflaufs. Sie werden nicht rückwirkend auf einen neuen Stand umgeschrieben. Backups und Wiederherstellungsbelege stehen im Release-Prüfbericht.</p>'
    (ROOT/'historical-docs.html').write_text(page('Historische Unterlagen', historical), encoding='utf-8')
    lines = ['# v1.0.0 Dokumentationsinventar', '', 'Stand: 18. Oktober 2026, Australia/Sydney.', '', '## Aktuelle Hilfe', '', '[HTML-Handbuch](index.html) · [Help-Katalog](help_catalog.json) · [Historische Unterlagen](historical-docs.html) · [Einzelbewertung aller Screens](SCREEN_ASSESSMENT_DE.md)', '', '| Schlüssel | Dialog | Anleitung | Screenshot |', '|---|---|---|---|']
    for s in SCREENS:
        shot = f'[Erfasst](screenshots/{s["key"]}.png)' if (ROOT/'screenshots'/f'{s["key"]}.png').exists() else 'Noch nicht erfasst; Ablaufdiagramm vorhanden'
        lines.append(f'| {s["key"]} | `{s["target"] or "Web-Timeline / Unterdialog"}` | [{s["title"]}]({s["howto"]}) | {shot} |')
    lines += ['', '## Prüfgrenzen', '', '- Native Zielpfade und zentrale Feldnamen wurden lesend im laufenden Projekt geprüft.', '- Ablaufbeschreibungen sind mit den genannten Buildern und Runtime-Modulen abgeglichen.', '- Nicht vorhandene Screenshots werden nicht durch künstliche UI-Bilder ersetzt.', '- Historische Berichte bleiben unverändert und sind über den Archivindex eingeordnet.', '- Physische MK2-Tasten, Kameraaufnahmen und Lichtausgabe sind keine automatische Folge eines Softwaretests.', '- Nach neuen Screenshots `python docs/release-v1.0.0/generate_guides.py` ausführen, damit sie in den Seiten erscheinen.', '']
    (ROOT/'DOCUMENTATION_INVENTORY.md').write_text('\n'.join(lines), encoding='utf-8')
    print(f'Generated {len(SCREENS)} guides and {sum(len(s["fields"]) for s in SCREENS)} field hints.')


if __name__ == '__main__':
    generate()
