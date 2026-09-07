# Kumulativer 3D-Layout- und 2D-Fixture-Editor

Stand: 07.09.2026. Additiver, noch separat live zu prüfender Editor unter
`/project1/layout_scene_editor/ui_panel`. Bestehender Pixel Mapper bleibt erhalten.
Import des Builders startet nichts; Aufbau nur explizit über
`pixelblaze_mapper.build_layout_scene_ui.build(initial_path=...)` in TouchDesigner.
Der konfigurierte aktuelle Layout-Dateipfad wird gelesen, nicht überschrieben.
Keine automatische Projekt-Speicherung, Controller-Verbindung oder Hardware-Ausgabe.

## Koordinaten und Identitäten

| Bereich | Inhalt | Auswirkung einer Bearbeitung |
| --- | --- | --- |
| Originalscan | Unveränderte Punkte und Scan-ID; explizite Registrierung in den ursprünglichen Objektrahmen | Bleibt archiviert |
| 3D-Layout | Transformation je Objekt | Weltposition; keine Neunummerierung |
| 2D-Fixture-Ausgabe | Eigene Transformation der lokalen 2D-Form | Anordnung der Fixtures; keine Änderung der UV-Abtastung |
| Material-UV | Separate Transformation derselben lokalen Form | Abtastposition im Material; keine Änderung der Fixture-Anordnung |
| Routing-Entwurf | Controller-Identität und physischer Port je Objekt | Nur Absicht im Entwurf; noch keine tatsächliche Router-Konfiguration |

Benutzerachsen: **X Höhe, Y rechts, Z hinten**. Die 3D-Kamera verwendet ausschließlich
zur Darstellung `(Y, X, -Z)`. Exporte behalten die Benutzerachsen. 2D-Projektion
`YX` bedeutet Y horizontal und X vertikal. Weitere explizite Projektionen:
`XY`, `XZ`, `ZX`, `YZ`, `ZY`. Projektion nimmt registrierte lokale Scanpunkte,
nicht die transformierten Weltpositionen; Skalierung/Normalisierung erfolgen
nicht unbemerkt. Ein zweidimensionaler Pixelblaze-Import erhält Z=0 und kann
anschließend ausdrücklich projiziert werden.

LED-ID, Objekt-ID, lokaler LED-Index und globaler Quellindex bleiben separat.
Farben sind stabil aus der Objekt-ID abgeleitet. Die Objektliste zeigt Anzahl,
globalen Bereich und ID; Herkunft zeigt benutzte Scans und fehlende Punkte.
Fehlende Punkte sind unsichtbar dargestellt, aber nicht aus den Daten gelöscht.

## Bedienung

1. `LOAD ACTIVE SNAPSHOT` liest direkt die autoritative Tabelle
   `/project1/pixelblaze_mapper/map_active`, ohne Dateipfad oder aktive Änderung.
   Gültige, disjunkte Routing-Quellbereiche werden eigene Objekte; übrige LEDs
   bilden `Unmapped`. Fehlende/ungültige/überlappende Routing-Daten führen mit
   sichtbarer Warnung zu einem vollständigen ungruppierten Objekt, nicht zu
   geratenen Gruppen. Reverse und Zieloffset verändern niemals Quellreihenfolge.
   Vollständiger Indexbereich 0..N-1, endliche XYZ und unveränderter zweiter
   Tabellen-Snapshot sind Voraussetzung. Originalpunkte werden eingefroren;
   neue stabile LED-IDs basieren auf Quellnamespace + globalem Index (keine
   behauptete Wiederherstellung früherer Scan-IDs). UDP-Ports werden nicht als
   physische Portbindungen interpretiert. Objektanzahl und exakter Count bleiben.
   `LOAD CURRENT FILE` liest dagegen den sichtbaren Dateipfad als neuen Entwurf.
   `OPEN SCENE` liest einen vollständigen Workspace oder älteren Scene-Export.
   Bestehende 3D-Entwürfe werden erst nach Bestätigung ersetzt. Vorher exportieren,
   wenn eine Kopie erhalten bleiben soll.
2. `APPEND SCAN`: Importformat und neuen Namen angeben, globalen Quellstart
   explizit setzen, optional ursprüngliche Scanindizes auswählen (`517-785`).
   Vorhandene globale Eigentümerschaft darf nicht überlappt werden.
3. Objekt über seine sichtbare Nummer auswählen. 3D: linke Maustaste bewegt
   das ausgewählte Objekt in der Benutzer-XY-Ebene. `mode` bestimmt `move`,
   `rotate` oder `scale`; bei Rotation/Skalierung gilt `axis`. Rechte Maustaste
   dreht die Kamera. Pfeile bewegen X/Y, Bild auf/ab Z. Numerische Werte werden
   erst mit `SET TRANSFORM` übernommen. `FRAME` passt die Ansicht an.
4. `PROJECT RANGE TO 2D` erzeugt die explizite Projektion. Das Feld `2D local LEDs`
   nimmt ausdrücklich lokale Objektindizes an, etwa `0-398` oder `0-9,20-29`;
   leer bedeutet das ganze Objekt. Mehrere disjunkte Bereiche desselben Objekts
   werden separate Fixtures mit unveränderten LED-IDs/lokalen/globalen Indizes.
   Jede teilweise Überschneidung blockiert ohne automatische Aufteilung; ein
   exakt bereits vorhandener Bereich kann nach Bestätigung mit derselben
   Fixture-ID erneut projiziert werden. Eingabereihenfolge nummeriert LEDs
   nicht neu. Dies funktioniert auch für ungruppierte Active-Snapshots, deren
   Routing zum Beispiel durch überlappende Bereiche eines deaktivierten
   Controllers nicht eindeutig als Objektaufteilung verwendet werden konnte.
   Die zwei Flächen zeigen links die Fixture-Anordnung und rechts Material-UV.
   Ein Klick nahe einem farbigen Punkt wählt das ganze Fixture. Ziehen oder
   Pfeiltasten bearbeiten nur die zuletzt angeklickte Fläche. `mode` gilt auch
   hier; 2D-Rotation ist um die Flächennormale. 3D-Zahlenfelder sind im 2D-Tab
   deaktiviert. Der UV-Bereich bleibt fest 0..1; links passt `FRAME` die Ansicht an.
5. `FIT UV` passt ausdrücklich das ausgewählte Fixture in 0..1 ein und verändert
   nur dessen UV-Transformation. Es normalisiert keine 3D- oder Ausgabeform.
   Wenn `/project1/res1` existiert, dient es nur als Hintergrundvorschau. Diese
   Vorschau ist **keine** aktive Sampling-Verbindung.
6. Ein Ziehen erzeugt beim Loslassen einen Undo-Schritt. Escape verwirft die
   Vorschau; Ctrl+Z/Y und die Undo-/Redo-Knöpfe betreffen den aktuellen 3D- oder
   2D-Entwurf. Tastatur ist auf die drei Editorflächen beschränkt, nicht global.
7. `EXPORT WORKSPACE` speichert Originalscans, Identitäten, 3D-Transformationen,
   Routing-Absicht und beide 2D-Transformationen gemeinsam. Das Laden setzt die
   Undo-Historie zurück. `EXPORT PIXELBLAZE 3D` ist dagegen nur ein dichtes
   XYZ-Array: Workspace als Identitäts-/Herkunftskopie behalten.

## Import, Teilscan und Exporte

Unterstützte Importformate: `pixelblaze`, `marimapper-json`, `marimapper-csv`.
MariMapper-JSON ist das tatsächlich beobachtete schlichte Array von XYZ-Punkten,
kein erfundener Marken-Wrapper. CSV `index,x,y,z` und vorhandene Koordinatenaliases
werden durch den bestehenden Parser gelesen. CSV `index,u,v` wird hier nicht
still als XYZ interpretiert. Generatorquellen werden im UI nicht ausgeführt;
der reine Modellparser benötigt dafür einen ausdrücklich bereitgestellten,
vertrauenswürdigen Materialisierer. Unbekannte Formate melden einen Fehler.

`REPLACE REGION` benötigt lokale Objektindizes und passende ursprüngliche
Scanindizes. Neue Punkte müssen bereits im ursprünglichen Objektrahmen liegen;
die Bestätigung ist eine Benutzerzusicherung, **keine** automatische Registrierung
oder Genauigkeitsprüfung. Unbeteiligte LEDs bleiben identisch. `GUIDED SCAN`
öffnet bei installiertem Builder `/project1/guided_scan/ui_panel` und übergibt
den aktuellen Objektentwurf. Der Runtime-Hook `accept_scan_request(request, scan)`
prüft Scene-ID/Revision, Scan-ID, LED-Identitäten und Verweise auf Registrierung
und Qualitätsbericht, bevor er einen einzigen Entwurfs-Undo-Schritt erzeugt.
Auch dieser Hook aktiviert kein Mapping und führt keine Rekonstruktion aus.

`EXPORT UV` prüft aktuelle 3D-Revision, vollständige globale LED-Abdeckung,
fehlende Punkte und 0..1-Grenzen **vor** der Dateiauswahl. Kein Klemmen,
keine automatische Neunummerierung. Nach einer 3D-Änderung bleiben vorhandene
Fixture-Daten erhalten, werden aber als veraltet markiert. Erneute Projektion
fordert bei geänderter Quelle ausdrücklich das Zurücksetzen des gesamten
2D-Workspaces; vorher Workspace exportieren. Dies ist eine sichere erste
Integrationsgrenze, noch kein differenzielles Fixture-Rebase. Wiederprojektion
eines bestehenden Fixtures setzt dessen beide Transformationen und 2D-Historie
nach Bestätigung zurück. Andere Fixtures bleiben beim gleichen Quellstand erhalten.

## Entwurf / Vorbereitung / aktive Ausgabe

Der Editor ruft optional den separat installierten, geprüften Runtime unter
`/project1/layout_apply/runtime` auf. Fehlt er, wird ohne automatische Installation
abgebrochen; Datei-Exporte bleiben möglich. Der Editor-Builder übernimmt niemals
aktive Daten. Ein Rebuild erhält beide Workspace-DATs und vorhandene Entwürfe,
setzt aber das Routing-Einverständnis auf `NO` und verwirft die UI-Vorbereitung.

1. LED-Ausgabe vorher ausdrücklich ausschalten. Der Apply-Runtime prüft bekannte
   Sender; die UI schaltet sie weder an noch aus.
2. Im sichtbaren Feld `Type YES: keep LIVE routes` ausdrücklich `YES` eintragen.
   **Vorhandenes Live-Routing bleibt erhalten. Controller-/Port-Bindungen des
   Entwurfs werden nicht angewendet.** Routing-/Anzahländerungen sind separat.
3. `VALIDATE / PREPARE` und Bestätigung erfassen den gesamten Workspace einschließlich
   beider 2D-Domänen, dessen Revision, aktiven Zustand und aktuellen Ausgabecount.
   Aktueller Tab bestimmt 3D/2D; das sichtbare Projektionsfeld bestimmt die Achsen.
   Dieser Schritt schreibt noch keine aktiven Koordinaten.
4. `APPLY (OUTPUT OFF)` benötigt eine weitere Bestätigung. Tab und Projektion
   müssen zur Vorbereitung passen; Workspace, aktiver Zustand, Ausgangsstatus
   und Downstream-Verbindungen werden erneut geprüft. 3D übernimmt Welt-XYZ und
   explizit projizierte UV. 2D übernimmt Material-UV und die separat gespeicherte
   Fixture-Anordnung, **nicht** physische XYZ. Kein stilles Klemmen/Normalisieren.
   Global-, Panel- und Hybrid-Sampling verwenden danach dieselbe ausdrücklich
   gewählte Workspace-UV-Platzierung. Materialquelle und Live-Routing bleiben.
5. `REVERT LAST` mit Bestätigung stellt ausschließlich die unveränderte letzte
   aktive Übernahme wieder her. Externe Änderungen blockieren diese Rücknahme.
   Der aktuelle Entwurf bleibt erhalten. Keine Ausgabe wird gestartet.

Die Transaktion erstellt einen vollständigen Snapshot, verifiziert das Ergebnis
und stellt bei Fehler zurück; Rollbackfehler werden ausdrücklich gemeldet.
Details: [Active-Apply-Vertrag](implementation-2026-09-07/LAYOUT_ACTIVE_APPLY.md).
Der ältere reine `apply_prepared(...)`-Vertrag für 3D/Routen bleibt separat für
Tests verfügbar; die UI verwendet ihn nicht für die neue Workspace-Übernahme.
Die vorliegende Änderung ist Source-/Offline-geprüft, noch keine Behauptung einer
erfolgreichen Live-Aktivierung.

## Prüfstatus und verbleibende Abnahme

### Dauerhafter Workspace und Projektspeicherung

`layout_session_storage.py` trennt dauerhaft gespeicherte primitive Daten von
laufenden Python-Klassen. `layout_session_snapshot` und `fixture_session_snapshot`
enthalten versionierte Daten für Originalscans, stabile Bindungen, Transformationen,
Routing-Entwurf, aktuelle Auswahl sowie beide Undo-/Redo-Historien. Änderungen und
Mausvorschauen aktualisieren diese Snapshots; ältere `draft_document` und
`fixture_document` bleiben als Import-/Fallback-DATs erhalten. Ein Modul-Neuladen
wandelt vorhandene alte Klasseninstanzen über ihre Daten statt über `pickle` um.

Die auf dem laufenden System gelesenen `OP.store`-/`storeStartupValue`-Docstrings
bestätigen alternative Speicher-/Startwerte. Nur laufende Klassenobjekte,
Mauszustände und vorbereitete Pläne erhalten Startupwert `None`; die primitiven
Snapshots bleiben gespeichert. Beim Wiederöffnen wird eine gespeicherte sichtbare
Mausvorschau als genau ein rückgängig machbarer Entwurfsschritt übernommen, nicht
als weiterhin gedrückte Maus. Aktive Ausgabe wird dabei nicht verändert.

Explizite Preflight-Hooks für den Haupttask:
`/project1/layout_scene_editor/runtime.module.prepare_save()` und
`/project1/layout_apply/runtime.module.prepare_save()`. Alternativ direkt die
Helper `prepare_save(editor_owner)` / `prepare_apply_save(apply_owner)` aufrufen.
Sie speichern **kein** Projekt, sondern liefern primitive Prüfmanifeste und setzen
die engen Startup-Regeln. Der Editor-Builder ruft seinen Hook beim Aufbau auf.
Der Apply-Hook verwirft nur vorbereitete Klassenpläne beim nächsten Öffnen;
`last_snapshot` und `last_applied_hash` für sinnvolles `REVERT LAST` bleiben exakt
erhalten, einschließlich Tuple-/Listenstruktur. Nichtprimitive Rücknahmedaten
blockieren den Preflight, anstatt still gelöscht zu werden.

Diese Lösung sichert den Layout-Bereich. Der Haupttask muss vor einer echten
TOE-Speicherung weiterhin das gesamte Projekt auf andere nicht speicherbare
Runtime-Objekte prüfen und Speichern/Wiederöffnen real nachweisen.

Offline-Prüfungen sind keine Live-UI-, GPU-, Hardware- oder End-to-End-Nachweise:

- 38 Modelltests: stabile Identitäten, Import/Export, Transformationen, fehlende
  Punkte, Teilscan und 3744-Punkte-Fall.
- 20 Adapter-/statische Tests: Undo, Routen, Mausvorschau-Vertrag, Scanübergabe,
  vorbereitete Transaktion, Konflikte/Rollback und Builder-Verträge.
  Drei davon sichern exklusive LED-Geometrie: TouchDesigner erzeugt beim Anlegen
  einer Geometry-COMP einen Torus. Im 3D- und beiden 2D-Renderern werden alle
  anderen direkten Kind-Operatoren nur in ihren Display-/Render-Flags deaktiviert;
  allein `led_shape` bleibt sichtbar. Kein Kind-Operator und keine Daten werden
  gelöscht. Der Haupttask hat den zuvor mitinstanzierten Torus live nachgewiesen.
- 26 Workspace-/TD-Grenztests: unabhängige 2D-Transformationen, Tastatur,
  Undo, Escape, veraltete Quelle, Abdeckung, gemeinsamer Export, Wiederherstellung
  aus persistenten DATs und getrennte Prepare-/Apply-/Revert-Einverständnisse.
  Dazu explizite Teilbereiche, identitätserhaltende Wiederprojektion, Blockieren
  von Überlappung und individuelle Hit-Auswahl mehrerer Fixtures pro Objekt.
- 6 Active-Snapshot-Tests: Disjunktheit, unzugeordnete Bereiche, Fallback,
  Identitätsstabilität, ungültige Daten und konkurrierende Tabellenänderung.
- 16 Tests des separaten Active-Apply-Moduls: Payload-/Zustandsprüfung, unveränderte
  physische XYZ bei 2D, Ausgabe-Sperre, Transaktion und Rücknahme.
- 7 Storage-Tests: primitive Snapshot-/Pickle-Roundtrips, Historien/IDs/Auswahl,
  Vorschau als Undo-Schritt, effektive Startup-Speicherung, echte isolierte
  `importlib.reload`-Reproduktion des PicklingError und Erhalt des Revert-Snapshots.
- Fixture-Modell wird zusätzlich durch eigene Tests des Fixture-Moduls geprüft.

Live-Abnahme durch den Haupttask: beide Flächen sichtbar, orthografischer
0..1-Ausschnitt, sichtbare Materialvorschau, echtes Klicken/Ziehen/Loslassen,
Tastaturfokus aller drei Flächen, Dateidialoge und erneutes Öffnen/Builder-Rebuild.
Bei jedem Schritt Hashes aktiver Mapping-/Routertabellen und deaktivierte Sender
unverändert halten. Erst danach aktive Sampling-/Router-Integration separat
reviewen. Große Objektlisten sind derzeit Textlisten ohne Scroll-/Suchfunktion;
3D-Auswahl erfolgt per Objektnummer statt geometrischem Picking.

Priorisierte nächste Schritte: (1) echte UI-Abnahme und messbare Framezeiten bei
3744 LEDs, (2) geschlossenes transaktionales Active-Apply mit Fehlereinspielung,
(3) differenzielles Fixture-Rebase, (4) Scroll-/Suchliste, 3D-Picking und sichtbare
Transformationsgriffe. Ziel: 0 aktive Änderungen beim Draft-Test; jeder Drag genau
ein Undo; vollständiger Workspace-Roundtrip bitgleich für IDs und Originalpunkte.
