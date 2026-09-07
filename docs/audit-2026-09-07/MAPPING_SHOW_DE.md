# Frischer Quellcode-Audit: Mapping, Preview, Show und Hilfe

Stand: 07.09.2026. Zuständig: Dialog 1 LED Preview, Dialog 5 Pixel Mapper, Dialog 8 Show Control, Dialog 9 Shortcut Help; Photo Calibration als verschachtelte Bedienoberfläche. Analyse ausschließlich lesend; dieses Dokument sowie zwei JSON-Evidenzdateien wurden neu geschrieben. Keine Builder ausgeführt, keine Live-Parameter, Dateien des Nutzers, Hardwareausgabe oder `.toe` geändert. Keine Commits.

## Evidenz und Abgrenzung

Aktuelle Python-/Shaderquellen, passende Offline-Tests und frühere Audit-/P1-Dokumente wurden neu geprüft. Im Repository und den geprüften Benutzer-/Projekt-Elternverzeichnissen wurde keine `AGENTS.md` gefunden. Bestehende uncommittete Änderungen bleiben unangetastet. Die extrahierte `PHOTO.33`-Datei ist ein historischer Snapshot, **kein Nachweis des heute geladenen Projekts**.

Dieses Teilgutachten hat keine eigene Live-UI-Prüfung durchgeführt. Die vom Hauptaudit frisch lesend erfassten Dateien `live-baseline.json` und `timing-samples.json` wurden zusätzlich ausgewertet. Sie betreffen `PixelblazeMapper_WORKING_PHASE2_EFFECTS_CORE.88.toe` aus `Backup/Projektdatei`. Dateiverweise sind repositoryrelativ mit aktueller Quellzeile. Priorität P1 bedeutet eine vor produktiver Freigabe zu klärende Funktions-/Bedienlücke; P2 ist Verbesserung ohne unmittelbar bewiesenen Ausfall. Ein Quellcodebefund wird nicht als beobachtetes Hardwareproblem ausgegeben.

Die Core-68-Berichte vom 26.08. enthalten wichtige historische Beobachtungen, sind aber nicht als aktueller Istzustand übernommen: 3.744er-Previewvertrag, Rear-Start 1184, vollständiger Kalibrierungsreset, A/B-Richtung und dynamische Loop-/Blackout-Beschriftung sind inzwischen im Code vorhanden. `docs/P1_CORE71_LIVE_ACCEPTANCE_DE.md` meldet dafür eine frühere Softwareabnahme; auch diese ist kein frischer End-to-End-Test vom 07.09.

## Kurzurteil

Der kanonische Indexvertrag und die portable Logik sind deutlich weiter als im Core-68-Audit. Die größten verbleibenden Risiken liegen **zwischen** getesteten Komponenten: gemeinsamer UV-Sampler trotz cue-eigener Koordinatenmodi; Zeitneustart am sichtbaren A/B-Übergang; Toggle-Buttons mit nur einer Ereignisflanke; Entwurfskoordinaten in der verbindlich genannten Vorschau. Eine grüne Suite beweist diese Verbindungen bisher nicht.

### Frischer Live-Abgleich aus dem Hauptaudit

Alle zehn Shortcutziele existieren und melden keine Operatorfehler. Für Dialog 1 enthält der Zieloperator wie erwartet keine untergeordneten Controls. Dialog 5 hat alle neun beschriebenen sichtbaren Buttons (`btn_open_pb1`, `btn_open_csv1`, `btn_reload1`, `btn_fill1`, `btn_contain1`, `btn_revert1`, `btn_export_pb1`, `btn_export_csv1`, `btn_apply1`). Die Statusfelder zeigen jedoch **PIXELS 3714**, Quelle `mapping_sidewall_upright_x90.json`, DRAFT ON / SAVED ON / APPLIED OFF sowie EXPORTED – AllExported.json. Die Fußzeile lautet sogar „Apply validates exactly 3714 pixels before live LED routing.“ Das widerspricht dem aktuellen Controllerguard 3744. Das Feld `editor_mock` zeigt Beispielkoordinaten und alte `../core/raw_map`-/`normalized_map`-Pfade statt einer echten aktuellen Tabellenansicht. Die versteckten `saved_chip`, `applied_chip`, `preview_target` sind keine heute sichtbaren Bedienelemente. **PM-04 / P1: direkt belegte irreführende Live-Inventur**, keine bloße historische Vermutung. Der Status darf Entwurfszahl 3714 zeigen, muss diese aber klar von der aktiven Sollzahl 3744 trennen; die Guard-Fußzeile darf 3714 nicht versprechen.

Dialog 8 zeigt alle acht Transportbuttons, CUE 03 / Barcode Finale / Slot A / Noisy Barcode / Neon / targets all / 12.00 s / STOPPED; Loop OFF, Blackout ON. `btn_blackout.value0=False` bei Label BLACKOUT ON ist für den nachträglich direkt ausgelesenen aktuellen **momentary**-Button normal und kein aktueller Togglefehler. Die aktive Gesamtquelle war `imported`, nicht Show; der ausgelesene Sender war `enabled=false`, `send_count=0`. Diese Momentaufnahme ist sicher, macht das statische ART-NET SAFE-Badge aber nicht dynamisch korrekt. Dialog 9 enthält alle zehn sichtbaren Textzeilen inklusive 0 und aktualisierter 7-Beschreibung; ein vorhandener Operator und sichtbarer Hilfetext sind noch kein echter Shortcuttest.

Ergänzend hat dieser Teilagent auf Bitte des Hauptaudits die tatsächlichen Callbacktexte/Parameter per TouchDesigner-API **nur gelesen**: `mapping-show-readonly.json` bestätigt aktuell aktive Previewkoordinaten=`map_active`, 3744 Samples, Side1184, Rear2560, Rear-Start1184 und vollständigen 88er-Reset ohne Operatorfehler. Das ist ein aktueller positiver Befund; LP-01 beschreibt ein mögliches späteres Zurückschalten durch Controlleraktionen, nicht die heutige Initialbindung. Die Live-Showsampler verwenden tatsächlich denselben `effect_uv_in`; Live-Shader `coordinateSpace` ist unverändert pass-through und Live-`render_sync` enthält weiterhin `elapsed × speed` sowie Fluid-Noise-Fallback. SC-01/02/05 sind damit nicht nur Unterschiede einer unbenutzten Quelldatei. LOOP/BLACKOUT sind live momentary, obwohl der aktuelle Builder toggle erzeugt: SC-03 ist Rebuild-/Reproduzierbarkeitsrisiko, kein derzeit nachgewiesener Live-Klickfehler.

Aus `timing-samples.json`: 31,3 s Fenster, Material-/Raw-Preview/`res1` jeweils 1241 Cooks ≈39,65/s; `math1` 1319 ≈42,14/s. Diese Cookraten sind weder identisch mit tatsächlichen geänderten Bildframes noch mit dem 60-FPS-Projektzeittakt. Der statische UV-Node kochte im Fenster nicht erneut; das ist für unveränderte Koordinaten erwartbar und allein kein Stotterfehler. Die Messung erlaubt keinen 60-FPS-End-to-End-PASS und keinen Hardware-FPS-Schluss, da der Sender aus war.

## 1 — LED Preview

### Inventar und Bindungen

| Element / Funktion | Binding / Quelle | Aktueller Nachweis |
|---|---|---|
| Ctrl+Shift+1 | `shortcut_hub.py:21` → `/project1/LED_PREVIEW_OUT` | Definition und Test bestanden; heute kein eigener echter Tastentest |
| Fotoausgabe | `build_shortcut_hub.py:79–80`, `restore_photo_calibration.py:219–225` → `prototype_out` | stabiler Select-TOP-Alias; kein eigener interaktiver Dialog-Container |
| LED-Anzahl und Missing | `build_led_preview_contract.py:24–50,58–78` | exakt 3744; Entwurfs-Missing wird schwarz; keine eigene sichtbare Qualitätslegende |
| Side-/Rear-Trennung | `restore_photo_calibration.py:161–171` | Side 0–1183; Rear 1184–3743; zehn × 256 |
| Kamerainteraktion | `phase2_preview/build_phase2_preview.py:77–86,136–145` | Kamera auf `interactive_camera/renderView`; nicht auf den Shortcut-Select-TOP gebunden |
| Projektspezifische Buttons/Felder im Shortcut | `build_shortcut_hub.py:79–80` | Builder erzeugt nur Select TOP; Foto-/Kameraparameter sind untergeordnet, siehe Photo Calibration |

**LP-01 / P1 — Entwurf kann die als verbindlich bezeichnete Vorschau ersetzen.** `td_controller._write_derived()` setzt `preview3d.Coordinatedat` bei Import, Fit und Revert ausdrücklich auf `map_raw` (`td_controller.py:247–256`). Die Photo-Kalibrierung verwendet denselben `preview3d/instance_data`-Strom (`phase2_preview/build_two_plane_calibration.py:20`). Die aktive Ausgabemap bleibt dabei unverändert. Schon ein nicht angewandter, aber gleich großer 3744er-Entwurf kann somit das Foto räumlich verändern. Ein kleinerer Entwurf kollidiert zusätzlich mit dem strikten Preview-Anzahlguard. Die Dokumentation nennt diesen Ausgang trotzdem einzige verbindliche Hardwarevorschau (`TOUCHDESIGNER_SHORTCUTS_DE.md:28–31`). Der Anzahlguard schützt nicht gegen falsche, aber gleich große Entwurfsgeometrie. **Quellcodebestätigtes Integrationsrisiko, keine aktuelle Live-Reproduktion.**

Abnahme: getrennte aktive und Entwurfs-Vorschau oder unübersehbares DRAFT mit Herkunft/Hash. Import und FILL/CONTAIN eines abweichenden 3744er-Entwurfs dürfen bei unverändertem `map_active` weder Koordinatenhash noch Geometrie der als LIVE gekennzeichneten Vorschau ändern. Test für 3743, 3744, 3745 und Missing-Fälle; aktive Ausgabe unverändert.

**LP-02 / P2 — Bild ohne Herkunft/Frische und erreichbare Hilfe.** Der Alias zeigt weder aktive Quelle, Mappingversion, Warnungen, Panel-/Portgrenzen noch Updatealter. Die behauptete Kamerabedienung ist weiterhin an ein anderes Panel gebunden. Ein TOP-Viewer kann im Netzwerk sinnvoll sein, bietet aber keinen vollständigen Bedienvertrag für den Anwender.

Abnahme: Previewrahmen mit LIVE/DRAFT, aktiver Quelle, Mappinghash, 3744er-/Missingstatus, tatsächlicher Update-FPS und letztem Updatealter; Schaltfläche zur Kalibrierung. Ein Prüfpunkt pro Panelgrenze 516/517, 785/786, 1183/1184, 3743 muss eindeutig lokalisierbar sein. Kamerahilfe nur dort zeigen, wo Mausereignisse tatsächlich ankommen.

### Photo Calibration — verschachteltes Inventar

| Gruppe | Felder / Bindung | Auditbewertung |
|---|---|---|
| Hintergrund | Enabled, Image File, Open/Clear, Opacity, Contain/Cover/Stretch; `build_phase2_preview.py:45–67,169–180` | Bildpfad und Fit getrennt von Hardware; Dateidialog im heutigen Audit nicht ausgelöst |
| Hintergrundgeometrie | Simple/Cornerpin + acht X/Y-Ecken; `build_phase2_preview.py:68–72,90–110` | Simple-Modus benötigt keine Eckwerte; modeabhängige Deaktivierung nicht erkennbar |
| Freie Kamera | LED opacity, Home/Frame/Reset, Axes/Pivot, Mouse Controls; `build_phase2_preview.py:73–86` | Kontext unterscheidet sich von kalibriertem Foto; Hilfetext muss dies erklären |
| Foto | Calibrationenabled, Showside, Showrear, Sideopacity, Rearopacity; `build_two_plane_calibration.py:66–94` | Previewparameter, kein Art-Net-Schalter |
| Aktive Side-Ecken | Sidetlx/y, Sidetrx/y, Sideblx/y, Sidebrx/y; `build_two_plane_calibration.py:97–106` | acht Werte; Bestandteil des aktuellen Reset |
| Rear-Einzelfächer | F00…F09 × tlx/tly/trx/try/blx/bly/brx/bry; `restore_photo_calibration.py:94–119` | 80 Werte, direkt an zehn Corner Pins gebunden |
| Legacy-Rear | acht Grobecken + vier Splitwerte; `restore_photo_calibration.py:54–58,137–145` | inzwischen read-only und als LEGACY INACTIVE markiert, alter Resetbefund behoben |
| Reset | `Resetcalibration` → 8 Side + 80 Rear; `restore_photo_calibration.py:60–78,122–134` | vollständiger 88-Werte-Reset im Code; heutiger Klick-/Bildtest offen |
| Trennung / Status | Panelsstartindex read-only 1184; Status; `restore_photo_calibration.py:190–194` | kanonischer Start im Code, kein alter 1154-/1180-Befund übernommen |
| Feinsteuerung per Tastatur | historische Einzelfach-/Ecken-/Achsen-/Schritt-Auswahl und +/- | im Core-68-Bericht beschrieben; aktuelle aktive Installation in diesem Teil nicht auslesbar, deshalb nicht als frisch bestanden gewertet |

**PC-01 / P2 — Wiederherstellen setzt alle individuellen Rear-Ecken zurück.** `_ensure_panel_parameters()` schreibt nicht nur Defaults, sondern jedes Mal `parameter.val = value` (`restore_photo_calibration.py:109–110`); `restore()` ruft dies immer auf (:183). Das ist für ausdrücklich gewünschtes Restore richtig, aber nicht ein ungefährlicher allgemeiner Reparatur-/Initialisierungsschritt. `restore()` setzt außerdem Hintergrund-/Rear-Opacity (:190–191). Hilfe muss den Verlust aktueller Kalibrierung und Umfang von Restore versus Reset eindeutig nennen. Empfehlung: vorheriger Kalibrierungssnapshot mit Undo und Diff; nicht still als beliebig wiederholbare Initialisierung ausführen.

Abnahme: 88 aktive Werte mit verändertem Prüfsatz vollständig speichern, Restore/Reset ausführen und Undo liefert exakt denselben Satz; kein Mapping-/Outputhash verändert. Acht Hintergrund-Ecken und freie Kamera ausdrücklich außerhalb des 88er-Resetumfangs dokumentieren. Ecknamen im Dialog lesbar statt nur `F04bly`; Gesamtpanel „rear“ im Effekt-UV-Kontext von zehn Foto-Einzelfächern unterscheiden.

## 5 — Pixel Mapper

### Inventar und Bindungen

Die neun Aktionsnamen folgen dem aktuellen Controller und wurden im frischen Live-Inventar des Hauptaudits wiedergefunden. Die ursprüngliche Canvas-Erzeugung liegt nicht in einem aktuellen dedizierten Python-Builder; `dialog_contracts.py:45–48` nennt stattdessen `build_spatial_lookup_td.py`, der keine vollständige Mapper-Canvas rekonstruiert. Daher keine Behauptung, jeder heutige Bildschirmbutton sei neu angeklickt worden.

| Kontrolle | Controller / Datenziel | Wirkung und Grenze |
|---|---|---|
| OPEN PIXELBLAZE | `td_controller.py:51–76,210–211` | Import JSON/MAP/TXT/JS, Generator optional 3744; ersetzt Entwurf |
| OPEN MARIMAPPER CSV | :51–76,212–213 | CSV-Import, Missing indextreu; ersetzt Entwurf |
| RELOAD | :79–84,218–219 | lädt Sourcepath neu; ohne Pfad blockiert |
| FILL | :87–97 | Entwurfsnormalisierung je Achse, aktives Mapping nicht angewandt |
| CONTAIN | :87–97 | proportionaler gemeinsamer Maßstab; kein aktueller Mausnachweis der historischen Rückklick-Lücke |
| REVERT | :100–110,220–221 | Entwurf aus gecachtem aktiven Zustand / aktiver Tabelle; Quelle wird geleert |
| EXPORT PIXELBLAZE | :113–138,214–215 | exportiert rohen Entwurf; Dateischreibwirkung, nicht automatisch angewandte normalisierte Map |
| EXPORT MARIMAPPER CSV | :113–138,216–217 | Entwurf mit Indizes/Metadaten; Dateischreibwirkung |
| APPLY TO LEDS | :141–205,222–223 | Anzahl + Missing/Finite-Guard, normalisiert oder erhält Raumkoordinaten, aktive Tabelle und Anschluss ändern sich |
| Preserve room coordinates | :32–38,166–172 | zusätzliches Custom-Parameterfeld, Default False; nicht durch Canvas-Inventur als sichtbar nachgewiesen |
| Status / Pixelcount / Dimensions / Bounds | :290–307 | aus übergebenem Mapping; keine unabhängige Anzeige aktiver und Entwurfswerte |
| Draft / Applied / Saved / Lastaction / Sourcepath / Fitmode | :87–110,135–137,228–244,305–307 | mehrere Flags; Semantik teils Dateistatus, teils Live-/Entwurfsstatus |
| 3D-/Fotovorschau | :249–256 | teilt den Previewkoordinatenpfad, siehe LP-01 |

**PM-01 / P1 — Cache und aktive Tabelle können unterschiedliche Wahrheit liefern.** `initialize()` liest `map_active`, speichert aber via `setdefault` (`td_controller.py:41–47`); `revert`, `set_fit_mode`, Export und Apply bevorzugen `_states[ui_owner.path]` vor Tabellen (:93,102,122,145,317–318). Nach externen Mapping-/Rescanänderungen wird ein existierender Cache dadurch nicht aktualisiert. Nach Modulreload ist der Cache leer; `initialize()` setzt dann Draft=Active im Cache, ohne `map_raw` neu zu schreiben. UI und nachfolgende Aktionen können dadurch ein anderes Mapping verwenden als die persistente Entwurfstabelle. Nach normalisiertem Apply speichert der Cache sogar `draft`, nicht `applied_mapping` als aktiv (:188). Für Raw-Revert mag das Absicht sein, ist aber nicht derselbe Zustand wie `map_active`.

Abnahme: Zustandsmatrix initialisieren → Import → Modulreload → FILL → Export → Revert sowie externe Änderung der aktiven Tabelle. Zu jedem Schritt aktive/Entwurfs-/Exporthash und UI-Flags vergleichen. Persistenter Draft/Active-Zustand mit Generation/Hash, eindeutige Normalisierungssemantik; kein `setdefault` als stiller Synchronisationsersatz. Keine automatische Live-Reparatur im Audit.

**PM-02 / P1 — Apply aktualisiert den vorgebauten Effekt-UV-Lookup nicht.** Apply schreibt `map_active` und Produktion, ruft aber keinen UV-Rebuild/Invalidierung auf (`td_controller.py:173–205`). `build_effect_surface_uv.py:134–136` erzeugt den Lookup einmal aus aktuellem räumlichem Referenz-/Koordinatenbestand; sein Laufzeitcallback liest anschließend nur Lookupwerte (:43–70). Eine gültige neue Raum-Map kann daher aktive Geometrie und Effektabtastung auseinanderlaufen lassen. Die reine 3744-Prüfung erkennt diesen Zustand nicht. Gemeinsam mit dem Zustandsmodell lösen, nicht durch unkontrollierten Builderaufruf im Klickcallback.

Abnahme: gleich große Map mit kontrolliert veränderten Raumkoordinaten anwenden, dann Lookupgeneration und erwartete UVänderung nachweisen. Bei Fehler aktive Map, Lookup, Kabelverbindung und Status atomar auf vorherigen Zustand zurücksetzen; keine teilweise übernommene Kombination.

**PM-03 / P2 — Herkunft und destruktive Entwurfsaktionen zu wenig sichtbar.** FILL/CONTAIN betrifft normalisierte Arbeitsdaten, Exporte verwenden aber Raw-Entwurf, und Apply ist ohne Preserve normalisiert. Ein einzelner Bounds-/Pixelcountwert beschreibt nicht alle drei Darstellungen. RELOAD und REVERT verwerfen den Entwurf ohne Änderungsbestätigung (`td_controller.py:79–110`), obwohl Apply selbst streng validiert ist.

Abnahme: separate LIVE/DRAFT-Karten mit Quelle, Hash, Count, Missing, Bounds und angewandter Normalisierung; vor Verlust eines veränderten Drafts Vorschau der betroffenen Daten + Abbrechen. Hilfe zu Raw-Export versus angewandten Koordinaten und Preserve direkt am Element. Erfolgsfall und abgelehnter Fall pro Import-/Export-/Applypfad durch echte UI-Ereignisse in beaufsichtigter Sitzung nachweisen.

## 8 — Show Control

### Inventar und Bindungen

| Element | Bindung | Istvertrag |
|---|---|---|
| Ctrl+Shift+8 | `shortcut_hub.py:28` | öffnet `/project1/show_control/control_panel` |
| PREV, PLAY, PAUSE, STOP, NEXT, GO | `build_show_sequencer.py:254–267,285–298` | Buttons → Panel Execute → command → sequencer → sync → render |
| LOOP, BLACKOUT | :288 sowie :79–89 | Toggle-COMPs; Beschriftung/Farbe aus `integrate_live_show.py:257–262` |
| Cue-Status | `integrate_live_show.py:244–254` | Cue, Name, ausgehender Slot, Material, Preset, Targets, elapsed, Transport |
| Transition-Status | :235–256 | Richtung, Typ, Progress, B mix, Next, Loop, Blackout |
| Titel | :399 | statisch ART-NET SAFE; kein tatsächlicher Senderstatus |
| Cue-Daten | `build_show_sequencer.py:101–139` | festes `demo_show.json` → `cue_table` + `show_json`; im Dialog kein Dateiauswahldialog, Cueeditor, Seek oder Speichern |
| Schema | `show_sequencer.py:44–100,135–217` | vollständige Parametersätze, Dauer, Transition, Brightness, Targetgruppen streng strukturell validiert |
| A/B-Renderer | `integrate_live_show.py:306–353` | getrennte Farbsampler, gemeinsame UV, Maskierung vor Mix, danach kanonischer Ausgang |

Die frühere falsche A/B-Richtung und starre Cue-A-Statusbeschreibung sind korrigiert (`integrate_live_show.py:236–256`). LOOP/BLACKOUT haben jetzt sichtbare Zustandslabels. Daraus folgt aber nicht, dass ihre reale Mausereignisfolge korrekt ist.

**SC-01 / P1 — Cue-Koordinatenmodus und Hybridmix erreichen die tatsächliche Abtastung nicht.** `_apply_slot()` schreibt cue-eigenen Modus und Hybridmix in Shaderuniforms (`integrate_live_show.py:207,217`). `effects/core_effects.frag:71–77` gibt `coordinateSpace(uv)` jedoch unverändert zurück; der per-LED-Sampler ist allein zuständig. Beide Showsampler erhalten denselben `effect_uv_in`, gebunden an `/project1/effect_sample_uv` (`integrate_live_show.py:302–317`). Dessen Callback liest `madmapper_player_controls.Coordinatemode/Hybridmix` (`build_effect_surface_uv.py:29–30,49–50`), nicht die A/B-Cues. Somit können z. B. A=global und B=panel_local nicht gleichzeitig korrekt dargestellt werden; verbliebene Material-Player-Einstellungen beeinflussen die Show.

Abnahme: getrennte UV-Auswahl pro Slot aus demselben kanonischen Lookup; A global/B panel_local, A panel_local/B hybrid mit Mix 0/0.5/1 sowie umgekehrte A/B-Richtung. Farben an mindestens zwei nicht identischen lokalen/globalen UVs je echter Panelgruppe numerisch vergleichen. Änderungen am außerhalb der Show liegenden Material-Player-Modus dürfen das Showresultat nicht verändern.

**SC-02 / P1 — Animationsphase springt bei jedem automatischen Cue-Handoff.** Beide Slotzeiten sind `current elapsed × own speed` (`integrate_live_show.py:204`). Während des Crossfades läuft die nächste Szene bereits mit der Zeit des aktuellen Cues. Beim Handoff setzt der Sequencer `elapsed=0` (`show_sequencer.py:420`), wodurch die bereits sichtbare nächste Szene zurückspringt. Offline mit echter Demo: unmittelbar davor Cue 0, elapsed 19.999, Incoming-Speed 1.15, Phase 22.99885; direkt danach Cue 1, Phase 0. Das ist kein bloß zu langsamer Speed, sondern ein diskontinuierlicher Zeitursprung. PAUSE friert zwar cuezeitgetriebene Shaderparameter ein, beseitigt diesen Grenzfehler nicht.

Abnahme: slot-/cueeigene integrierte Phasen mit definierter Vorlaufsemantik. Bei automatischen Übergängen darf die neu aktuelle Slotphase gegenüber dem zuletzt sichtbaren Frame nur um den erwarteten `dt × speed` zunehmen, nicht zurückspringen. Prüfen bei 30/60 FPS, unterschiedlichen Cuezeiten/Speeds, Loop, Pause/Resume und manuellen Sprüngen; gewünschter Reset bei manuellem GO explizit festlegen. Material-Speed, globaler Material-Master und Cuezeit getrennt erklären: Show verwendet aktuell keinen globalen Master-Speed in :204.

**SC-03 / P1-Rebuildrisiko — Builder würde funktionierende momentary-Buttons als fehlerhafte Toggles wiederaufbauen.** `_button()` erzeugt für diese beiden Buttons `buttontype='toggle'` (`build_show_sequencer.py:82,288`). Der zugehörige Panel Execute reagiert aber nur auf `state` Off→On, `valuechange=False` (:294–298). Ein zweiter Klick On→Off ruft deshalb nach diesem Buildervertrag kein `command()` auf; Loop/Blackout blieben fachlich eingeschaltet. Das spätere Schreiben von Label/Farbe synchronisiert nicht den Panel-Togglezustand (`integrate_live_show.py:257–262`). **Frischer Live-Gegencheck: CORE88 besitzt bereits momentary-Buttons mit offToOn=True; dieser aktuelle Livepfad ist strukturell korrekt.** Der Befund betrifft Drift zwischen repariertem Projekt und reproduzierbarer Quelle. Kein heutiger riskanter Blackout-Klick erfolgte durch diesen Teilagenten.

Abnahme: jeweils vier reale Klicks ergeben fachlich und sichtbar 0→1→0→1→0, zusätzlich derselbe Test nach externem command/Restore. Entweder momentary Button mit fachlichem Toggle oder beide relevanten Ereignisflanken mit eindeutigem Setter; keine Rekursion/Doppelausführung.

**SC-04 / P1 — Safety-Badge ist keine Live-Sicherheitsinformation.** `network_output_enabled=0` wird beim Integrieren hart geschrieben und Titel lautet ART-NET SAFE (`integrate_live_show.py:390–399`). Gleichzeitig schaltet die Integration die Live-Quelle auf Show (:401); der bestehende Ausgangspfad bleibt angeschlossen (:341–353). „Dieser Builder aktiviert keinen Sender“ ist richtig, „diese Show ist hardwareseitig sicher/aus“ daraus nicht ableitbar. PLAY/NEXT/BLACKOUT verändern bei bereits laufender Showquelle das reale Farbsignal. Der Quelltest `test_live_show_integration.py:11–15` beweist nur Abwesenheit bestimmter Zeichenfolgen, keinen Senderzustand.

Abnahme: Badge aus tatsächlicher Quelle und Router-/Senderstatus, z. B. PREVIEW ONLY / LIVE ARMED / LIVE SENDING / STATUS UNKNOWN. Bei unbekanntem Status niemals grün SAFE. Der Dialog muss auch im Betrieb zeigen, ob Transport gerade den Liveausgang bestimmt. BLACKOUT klar als Show-Gain, nicht universeller Not-Aus; Router ALL OUTPUTS OFF bleibt getrennt.

**SC-05 / P1 — unbekannte Effekte werden still ersetzt.** `Cue.effect` wird nur als nichtleerer Text geprüft (`show_sequencer.py:151`), im Liveadapter ersetzt `CATALOG.get(effect, CATALOG['fluid_noise'])` jeden unbekannten oder importierten, nicht im Corekatalog vorhandenen Schlüssel (`integrate_live_show.py:190`). Ein syntaktisch gültiger Showimport kann darum ein anderes Material als angefordert abspielen. Abnahme: Preflight aller Cueeffekte gegen Resolver/Katalog, unaufgelöste IDs vor PLAY blockieren und Cue-ID sichtbar melden; kein stiller Fallback. Entweder importierte Materialien explizit unterstützen oder UI-/Schemaumfang als Core-only kennzeichnen.

**SC-06 / P2 — Transitionendpunkte und Helligkeit sind unvollständig abgesichert.** `show_renderer.py:86–94,174–178` benutzt bei Wipe/Radial `threshold <= mix`. Offline: Wipe bei mix=0,u=0 liefert Gewicht B=1; Radial bei mix=0,uv=(.5,.5) ebenfalls 1. Vor Übergang kann dadurch schon eine Rand-/Zentrumsgruppe aus dem nächsten Cue sichtbar sein. Außerdem gilt nur die Brightness des ausgehenden Cues für beide Slots (`show_sequencer.py:450`, `show_renderer.py:119–123`); unterschiedliche Brightnesswerte wechseln am Cuewechsel sprunghaft. Letzteres kann bewusst gewählte Cue-Semantik sein, ist aber für einen nahtlosen Crossfade zu entscheiden. Abnahme: alle LEDs bei mix0 exakt A und bei mix1 exakt B, alle sechs Transitionen und Richtungen; Crossfade verschieden heller konstanter Farben ohne unerwarteten Grenzsprung oder ausdrücklich dokumentierter Cut-Gain.

### Performance und Geschwindigkeit: getrennte Diagnose

`ShowSequencer` ist deterministisch und der Bulk-Renderer cached Zielmasken (`show_renderer.py:20–31`), das ist solide. Die Offline-Suite prüft für Crossfade im Mittel <8 ms, nicht die gesamte TouchDesigner-/Netzwerkkette (`tests/test_show_renderer.py:94–114`). Der Transport kappt ein einzelnes Echtzeitdelta auf 1 s (`integrate_live_show.py:367`); bei längeren Stalls wird Showzeit verworfen statt aufgeholt. Das ist eine Policyfrage und darf nicht als akkurate Wallclock-Synchronisation verkauft werden.

Empfehlung: erst gleiche Frame-ID und Zeitpunkt an Shaderzeit, A/B-Sampler, LED-Renderer, Preview und Sender messen; erst dann optimieren. 60-FPS-Timeline oder hohe UI-FPS sind kein Beleg für 60 unterschiedliche Bilder. Messbar abnehmen: über 60 s Soll 60 FPS, sichtbare effektive Updates ≥59/s bei laufendem nichtstatischem Material, P95/P99 Frameintervalle und größte Lücke ausweisen; Cue-/Phasengrenzen separat testen. Shaderkomplexität, Sampling, Pythonmix und Netzwerk-Takt einzeln budgetieren; keinen fehlenden Update-/Zeitvertrag durch einfach höheren Speed kaschieren.

## 9 — Shortcut Help und Querprüfung 0 / 7

### Vollständiges Navigationsinventar

Die zentrale Reihenfolge lautet heute **1,2,3,4,5,6,7,8,9,0**, nicht mehr neun Dialoge (`shortcut_hub.py:20–30`). Alle Kombinationen sind Ctrl+Shift+Ziffer.

| Taste | Name | Ziel |
|---|---|---|
| 1 | LED PREVIEW | `/project1/LED_PREVIEW_OUT` |
| 2 | MATERIAL BROWSER | `/project1/material_browser` |
| 3 | MADMAPPER LIBRARY | `/project1/madmapper_library/ui_panel` |
| 4 | MATERIAL PLAYER | `/project1/madmapper_player_controls/ui_panel` |
| 5 | PIXEL MAPPER | `/project1/pixelblaze_mapper/ui/canvas` |
| 6 | ART-NET ROUTER | `/project1/multi_controller_output/ui_panel` |
| 7 | OUTPUT CONFIG | `/project1/pixelblaze_mapper/output_config/ui_panel` |
| 8 | SHOW CONTROL | `/project1/show_control/control_panel` |
| 9 | SHORTCUT HELP | `/project1/shortcut_hub/help_panel` |
| 0 | GICO PORT CONFIG | `/project1/multi_controller_output/gico_port_config/ui_panel` |

Hilfe enthält Titel, Sicherheitszeile, zehn Kombination-/Name-/Zweckzeilen und Fußzeile (`build_shortcut_hub.py:99–116`), keine Klickbuttons, Links, Suchfunktion oder Statusanzeige. Die zehnte Zeile startet bei y=62 und endet y=100; Fußzeile y=22–56. Rechnerisch keine Überlappung, aber nur 6 px Abstand; dies ist keine gerenderte DPI-/Textumbruchprüfung.

Callback `keyEvent()` prüft press, Ctrl, Shift, kein Alt und bekannte Taste, öffnet das Ziel und meldet Erfolg/Missing (`build_shortcut_hub.py:52–62`). Der Builder setzt aktive Keyboarderfassung und den Filter dynamisch aus allen zehn Tasten (:93–97). **0 und 7 haben im aktuellen Code denselben Handler und dieselbe Filterquelle.** Ein separater Fehler nur bei diesen zwei Tasten ist damit aus dem Pythonquellstand nicht belegt. Möglich bleiben veralteter eingebetteter Callback/Keyfilter, fehlendes konkretes Ziel, Fokus-/Editorbindung oder Fensteröffnung/-sichtbarkeit; ohne frische reale Tastenfolge nicht als behoben markieren.

**SH-01 / P1-Testlücke — statische Liste ist keine Shortcutzuverlässigkeit.** Der frühere reale Core-68-Test belegte 1–9, nicht neu hinzugefügte 0 und nicht den heutigen `.toe`-Stand. Die zwölf aktuellen Shortcut-Tests prüfen Definitionen, Quellstrings und Dokumentnamen; keiner sendet eine Taste oder bestätigt ein sichtbares Fenster. `keyEvent` ist ein zuvor nachgewiesen funktionierender Vertrag, keine pauschal defekte Callbacksignatur.

Frischer erster Hauptauditversuch: Ctrl+Shift+7 zweimal bei TouchDesigner-Netzwerkfokus, einmal ausdrücklich mit leerer Netzwerkfläche fokussiert, öffnete kein neues Fenster. Anschließendes direktes Lesen (`shortcut-readonly.json`) zeigt active=True, perform=False, Keyfilter **1 2 3 4 5 6 7 8 9 0**, korrekten Callback ohne Fehler, beide Zieloperatoren vorhanden und beide TARGETS-Zuordnungen korrekt. Der 10-Zeilen-Keyboard-FIFO enthält zu diesem Zeitpunkt nur ältere 4/5/6/4/2-Ereignisse, **keinen 7- oder 0-Eintrag**; `ui.status` zeigt noch den Projektladehinweis. Die fehlgeschlagene Eingabe ist damit vor beziehungsweise an der Tastenerfassung zu lokalisieren, nicht mit einem fehlenden Ziel oder vergessenen Python-Mapping zu erklären.

**Späterer realer Gegencheck des Hauptaudits: Ctrl+Shift+7 aus dem aktiven Routerdialog öffnete/fokussierte den bereits vorhandenen Output-Config-Viewer sichtbar als überlagertes Fenster — PASS für diesen Dialogfokus.** Shortcut7 ist somit nicht generell defekt. Die frühere fehlende Reaktion bei Netzwerkfokus/Eingabezustellung bleibt als fokusabhängiger beziehungsweise injektionsabhängiger offener Fall bestehen; genaue Fokus-/OS-/Eingabeursache noch nicht getrennt. Ein API-Öffnen allein bleibt Navigationsfallback und darf nicht mit diesem späteren echten Tastatur-PASS vermischt werden. Für0 hier keine separate reale Tastenevidenz.

Abnahme 0/7 priorisiert: pro Taste mindestens 20 unabhängige Press/Release-Folgen mit Hauptfenster-, Floating-Viewer-, Suchfeld- und echtem Editorfokus; Tastaturlog, Callbackzeit, Ziel vorhanden, `ui.status` und eindeutiges sichtbares Fenster gemeinsam protokollieren. Editor-Ausnahme bewusst dokumentieren. Bestehende Fenster/Fokus danach wiederherstellen. Globalen Gültigkeitsbereich explizit festlegen; Builder setzt aktuell keinen Panel-/Fokusfilter. Keine pauschale Behauptung über heutige externe-App-Erfassung ohne Liveprüfung.

**SH-02 / P2 — Hilfe/Dokumente widersprechen aktuellen Daten.** `TOUCHDESIGNER_SHORTCUTS_DE.md:54–55` nennt weiterhin „aktuellen“ 3740er-/1180-Stand; :68 nennt V=X, während `effect_surface_uv.py:43` V=1−X liefert. Der vereinfachte Signalweg (:24–26) lässt kanonische UV-/Sampler-/Showswitchstufen weg. Die älteren Dialogaudits widersprechen teilweise den P1-Abnahmedokumenten; Tests kontrollieren nur Vorhandensein der Shortcutnamen (`test_shortcut_help_dialog_regression.py:74–79`). Der Hilfebuilder mischt englische Titel/Sicherheit/Fußzeile und deutsche Beschreibungen. Die Inline-Hilfe ist ausdrücklich nur Entwurf (`INLINE_HELP_SPEC_DE.md:3–4`) und hier nicht in Buildern umgesetzt.

Abnahme: eine aktuelle Einstiegshilfe mit Versionsdatum/geladenem Projekt, automatisch aus kanonischen Verträgen erzeugte Pixel-/Range-/Shortcutdaten; historische Audits als historisch markieren. Zehn anklickbare Öffnen-Zeilen, Missing-Zielstatus und lokalisierte Hilfetexte; null fachliche Mutationen durch Hilfeklick. Pro sichtbarem Feld/Knopf Zweck, Einheit, Wirkung, Sicherheitsgrenze, Erfolgszeichen und Fehlerpfad direkt erreichbar. Kalibrierung zusätzlich als verschachtelten Workflow verlinken.

## Frisch ausgeführte Offline-Prüfung

Am 07.09.2026 mit lokalem Python, alle sieben Läufe erfolgreich:

| Auswahl in `tests` | Anzahl | Aussage |
|---|---:|---|
| `test_show*.py` | 32 | echte portable Sequencer-/Rendererberechnung plus statische Builderverträge |
| `test_shortcut*.py` | 12 | Daten-/String-/Dokumentverträge, kein Keyboard-End-to-End |
| `test_pixel_mapper_dialog_regression.py` | 6 | echte Dateiinhalte und Serializer-Roundtrips; kein UI-/Apply-Transaktionstest |
| `test_led_preview_regression.py` | 6 | Alias-/Builderstringverträge, keine gerenderten Frames |
| `test_photo_calibration_restore.py` | 8 | AST-/Stringverträge, kein echter Reset-/Undo-Klick |
| `test_effect_surface_uv.py` | 8 | portable Koordinatenberechnung, kein Nachweis cue-eigener Showsampler |
| `test_live_show_integration.py` | 3 | trotz Name ausschließlich Quellstrings |
| **Gesamt** | **75** | **75 bestanden; 0 Live-UI-/Hardwaretests in diesem Teilgutachten** |

Reproduktion: `python -m unittest discover -s tests -p test_show*.py` und jeweils die sechs weiteren Muster aus der Tabelle. Zusätzliche direkte Offlineproben mit `load_show('shows/demo_show.json')`, `ShowSequencer.advance()` und `transition_b_weight()` bestätigten die numerischen Phase-/Endpunktwerte in SC-02/SC-06. Diese Proben sind echte ausgeführte Berechnung, aber kein GPU-/Hardwarebildvergleich. Die teilweise noch von expected failures sprechenden Modulkommentare in Preview-/Showtests sind selbst veraltet.

## Priorisierte Umsetzungsempfehlung und Scores

Keine Umsetzung in dieser Analysephase. Reihenfolge:

1. P1: Show-UV pro Slot, reale Toggleflanken, Phasenkontinuität und ehrlicher Live-/Outputstatus; danach Cue-Resolver-Preflight.
2. P1: aktive/Entwurfs-Preview und Mapperzustand/UV-Generation gemeinsam konsistent machen.
3. P1-Abnahme: echte 0-/7-Fokusmatrix und wiederholte Showbuttonklicks; alle relevanten Zustände über Liveadapter statt direkten Kernaufruf nachweisen.
4. P2: Endpunktinvarianten, Brightness-/Stall-/Master-Speed-Semantik entscheiden; Instrumentierung vor Leistungsoptimierung.
5. P2: current/historical Dokumentation trennen, eingebettete Hilfe und Kalibrierungs-Undo; danach robuste unabhängige Canvas-/Dialogbuilder und Zustandsadapter statt versteckter Projektabhängigkeiten.

Skala 0–10; indikative Bewertung des aktuellen Quellstands mit den oben benannten Integrationsrisiken, **keine unbedingte Livefreigabe**. U = Nutzbarkeit, I = Implementierung, R = Zuverlässigkeit, M = Wartbarkeit, C = Vollständigkeit, N = Innovativität.

| Dialog | U | I | R | M | C | N | Begründung |
|---|---:|---:|---:|---:|---:|---:|---|
| 1 LED Preview | 5 | 7 | 5 | 6 | 5 | 8 | kanonische Vollständigkeit repariert; Entwurfspfad/Livebedeutung und Telemetrie offen; Fotoidee stark |
| Photo Calibration (nested) | 5 | 7 | 6 | 6 | 6 | 8 | 88er-Reset und Legacykennzeichnung gut; versteckte Felder, Restore ohne Undo, heutige Klickwirkung unbewiesen |
| 5 Pixel Mapper | 4 | 6 | 5 | 5 | 5 | 6 | gute portable Parser/Guards; live falsche Guard-Fußzeile 3714, mehrere Zustandswahrheiten, UV-/Previewintegration und Canvasreproduzierbarkeit lückenhaft |
| 8 Show Control | 5 | 6 | 4 | 6 | 5 | 7 | starker Kern/Bulkmix, aber Show-UV, Phasengrenze, Togglepfad und Safetybadge unterlaufen Livevertrag |
| 9 Shortcut Help | 7 | 7 | 6 | 8 | 5 | 5 | zentrale zehn sichere Ziele, keine neue Fokusmatrix für0/7, keine kontextsensitive/klickbare Hilfe und Dokumentdrift |

Die niedrigere Show-Zuverlässigkeit ist durch neu gefundene Integrationsbefunde begründet, nicht durch Übernahme bereits reparierter Core-68-Fehler. Die Shortcut-Zuverlässigkeit ist wegen fehlender heutiger Ende-zu-Ende-Evidenz konservativ bewertet, nicht als Beweis eines Defekts bei0/7.
