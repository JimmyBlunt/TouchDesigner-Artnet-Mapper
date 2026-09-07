# Frisches Regressionsaudit – Dialoge 2, 3 und 4 einschließlich Native Params

Stand: 7. September 2026. Repository: `C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper`, HEAD `725d6b02cbf76cb1ff008e09d12b4db1a9a8b82a` (31. August 2026). Analyse und Empfehlungen, **keine funktionalen Änderungen**. Die vorhandenen Änderungen an README, `.gitignore`, Arbeits-TOE und unversionierten Dateien wurden nicht verändert. In den geprüften Verzeichnisebenen wurde keine AGENTS.md gefunden.

## Evidenz und Abgrenzung

Dieser Teilbericht beruht auf frischer Quellcodeprüfung, den alten Audits `MATERIAL_BROWSER_PLAYER_REGRESSION_AUDIT_DE.md` und `MADMAPPER_LIBRARY_REGRESSION_AUDIT_DE.md`, den neueren P1-/Native-Parameter-Dokumenten, 93 ausgeführten Offline-Tests und einer zusätzlichen isolierten Zustandsprobe. Keine TouchDesigner-Callbacks, GPU-Cooks, Live-HTTP-Schreibzugriffe, Hardwareaktionen oder echten Mausereignisse wurden durch diesen Teilprüfer ausgeführt. Neue echte UI-Beobachtungen des Hauptaudits sind separat zuzuordnen. Ein alter Screenshot vom 26. August ist **kein** aktueller Funktionsnachweis.

Zeilenreferenzen beziehen sich auf den genannten HEAD im aktuellen Arbeitsverzeichnis. „Belegt“ bedeutet entweder unmittelbar aus ausführbarem Code abgeleitet oder ausdrücklich durch eine Offline-Probe bestätigt; es bedeutet nicht automatisch „in der geöffneten TOE installiert und per Maus abgenommen“.

Aktuelle lokale Bestandsaufnahme: **638 Katalogeinträge, 28 Importpakete mit `material-import.json`, 26 `prepared.frag`**. Das ist eine Dateizählung, keine Aussage über 26 GPU-kompilierbare Materialien. Die alten 6/4-Importzahlen sind veraltet.

### Ergänzte heutige Live-Leseevidenz des Hauptaudits

Die anschließend geprüfte Datei [live-baseline.json](live-baseline.json) stammt aus der aktiven **CORE.88.toe** unter `Backup/Projektdatei`, Ziel 60 FPS. Dialogziele 2/3/4 existieren und melden keine Operatorfehler. Source ist `imported`, `browser_state.selected_id` und `live_preview_id` sind `mat_ab0287bb394c824f13df` (**Bubble Rings** laut lokalem Katalog). Der Player zeigt trotzdem `SOURCE: IMPORTED | MATERIAL: arcs`: MP-01 ist damit nicht nur ein Codebefund, sondern im heutigen Statusdump sichtbar.

Baseline-Speed zentral sowie beide UI-Slider: 0,253298; Global Master: 1; Gradient Acid; Frame Zoom 0,658971. Diese Übereinstimmung im Ausgangszustand ist **kein** Nachweis eines funktionierenden Rückkanals nach Änderungen (MB-01).

**Echte ergänzende Mausprüfung des Hauptaudits:** Nach API-Öffnung des Browsers wechselte ein tatsächlicher NEXT-Klick erfolgreich von Seite 1 auf 2. Dabei änderte sich der zunächst angezeigte Katalog von `25 CORE + 11 IMPORTED` / 36 Ergebnissen auf `25 CORE + 28 IMPORTED` / 53 Ergebnisse. Damit ist ein **veralteter Öffnungszustand mit verzögerter Aktualisierung bei der ersten Aktion** beobachtet, nicht ein Verlust von 17 Importen. Plausibler Quellpfad: Runtimeinitialisierung enthält `refresh(reset_page=False)` (`build_unified_material_browser.py:1065`–`1068`), während reines Viewer-Öffnen den alten gespeicherten Paneltext zeigen kann. Akzeptanz: erster sichtbarer Frame nach Öffnen zeigt den aktuellen Katalog, ohne dazu einen Navigationseingriff zu verlangen. Screenshots: [vorher](screenshots/02-material-browser.png), [nach NEXT](screenshots/02-material-browser-page2.png).

Ein echter NATIVE-PARAMS-Klick zeigte **15 Parameter von Bubble Rings** im kompakten Drawer; ZURÜCK funktionierte. [Native-Screenshot](screenshots/02-native-parameters.png). Ohne absichtlichen Sliderklick erschien allerdings `NATIVE PARAMETER UPDATED - mat_scale` und ein nativer Scale-Wert um 0,2581. Diese unerwartete Callbackanzeige wird als MP-06 getrennt behandelt; ohne nativen Vorherwert ist noch keine konkrete Wertänderung bewiesen.

Sender ist aus (`enabled=false`, `send_count=0`, `packet_count=0`). Die Hauptaudit-Auswertung von [timing-samples.json](timing-samples.json) über etwa 31,3 s meldet rund **39,65 Cooks/s** für live_preview/Gradient/res1 und **42,14 Cooks/s** für math1 bei Ziel 60. Das sind Operator-Cookraten bei abgeschaltetem Sender, keine gemessenen Art-Net-/Hardware-FPS und noch keine bewiesene Ursache. Sie unterstützen eine erneute Profilierung, nicht die Wiederverwendung der alten 11,8-FPS-Diagnose.

## Kurzfazit und Veränderung gegenüber dem alten Audit

| Früherer Befund | Heutiger Quellcodestand | Was noch nicht damit bewiesen ist |
|---|---|---|
| Materialwechsel verliert Speed/Framing/Farben; absolute Zeit springt | `material_state.py:133`–`198` integriert Phase und verwaltet Zustände je Schlüssel; Adapter `build_p1_material_state.py:165`–`272` installiert Anwendung/Persistenz | Richtige aktive Identität, atomare Wechsel, vollständiger Neustart mit tatsächlichen TD-Callbackreihenfolgen |
| Doppelte Browser-Regler | Gezielte Duplikatbereinigung `build_unified_material_browser.py:49`–`68`, Aufruf `:1078` | Bereinigung in der aktuellen TOE; bidirektionaler Value-Sync ist dadurch nicht implementiert |
| Dialog 4 zeigt nur Roh-TOP | Echte `ui_panel`-Oberfläche mit Vorschau, acht Reglern und Telemetrie `build_unified_material_browser.py:324`–`385` | Trefferflächen, lesbare Werte, aktuelle Shortcutverdrahtung und Synchronität |
| Importierte Vorschau wird nach Neustart nicht gefunden | `_managed_import_status` validiert Manifest und `prepared.frag`, `_normalize` übernimmt Pfad (`build_material_library_browser.py:395`–`449`) | Ein vollständiger Live-Preview-Neustart; der neue Test prüft die Pfadauflösung, nicht GPU oder Originalquellen-Ausfall |
| Hover kann aktives Material überschreiben | Eigenes `hover_preview`/`hover_shader`, explizite Trennung `build_material_library_browser.py:1052`–`1100`, `:1365`–`1403` | Die **explizite** Live-Preview bleibt weiterhin dasselbe TOP wie die importierte Produktionsquelle |
| Gradient oft ohne sichtbare Wirkung | Commit `725d6b0` erzwingt einen gemeinsamen Duotone-Postprozess | Neutraler Bypass, Schwarztreue, korrekte Helligkeit und ein unbeschädigter Original-Look |

Die funktionale Entwicklung ist deutlich weiter als am 26. August. Dennoch verhindern Zustands-/Preview-Isolation und die neue Gradientsemantik eine belastbare Freigabe allein anhand grüner Tests.

## Dialog 2 – Material Browser

### Inventar und Bindungen

| Sichtbares Element / Kontext | Aktuelle Bindung und Semantik | Prüfstatus / Lücke |
|---|---|---|
| Suche, SEARCH / APPLY | Filterruntime, Quell-/Gruppentokens (`build_unified_material_browser.py:907`–`945`, `:1104`–`1116`) | Code vorhanden; frischer echter Eingabe-/Apply-Test separat offen |
| SOURCE, GROUP, Gruppenauswahl | Quelle zyklisch All/core/imported; Gruppenmenü (`:947`–`964`) | Zustandslogik vorhanden; Treffer-/No-result-Abnahme offen |
| VIEW 4×2 / 8×4, Vor/Zurück, Seitenstatus | 8/32 Einträge, Clamping, gespeicherte Seite (`:966`–`1018`) | Tests überwiegend Quelltextverträge; echte wiederholte Paging-Klicks erforderlich |
| Bis 32 Bild-/Textkarten | Core-TOPs oder gespeicherte Importbilder; Bild und Label haben Auswahlcallbacks (`:150`–`163`, `:978`–`1063`) | Auswahl mutiert Produktion; kein gefahrloser Read-only-Klick |
| MASTER SPEED, STOP/0.5x/1x/2x | Schreibt **Speed**, Bereich 0–2 (`:262`, `:266`–`270`) | Ist Material-Speed, nicht der separate `Globalmasterspeed` |
| FOCUS X/Y | Schreibt zentrale Focusx/y 0–1 (`:263`–`264`) | Nur UI→Engine-Callback |
| FRAME ZOOM | Schreibt Framezoom 0,25–4 (`:265`) | Player und Zustandsmodell erlauben bis 8 |
| RESET VIEW | `material_control_surface.reset_frame()`, Fokus 0,5/0,5, Zoom 1 (`:272`–`275`; `material_control_surface.py:175`–`182`) | Kein Material-/Farbreset |
| NEON / AMBER / ACID / FIRE/ICE / MONO | A/B-Farben, Gradientname, erzwungener Gradient-GPU-Cook (`:277`–`281`; `material_control_surface.py:157`–`172`) | Kein Bypass; neue Semantik siehe G-01 |
| NATIVE PARAMS | Öffnet Drawer im **Browser**, nicht im Player (`:389`–`479`) | Separat unten inventarisiert |
| READY / aktive Materialmeldung | Textstatus (`:534` und `:914`, `:1040`, `:1062`) | `DMX OFF` ist in READY hart codiert, kein gemessener Ausgabestatus |

### Befunde

**MB-01 · P1 · Sichtbare Regler werden nicht aus dem zentralen Zustand zurückgeführt.** `_slider()` setzt `value0` beim Build (`build_unified_material_browser.py:234`–`240`); `_value_execute()` schreibt ausschließlich vom Slider zum zentralen Parameter (`:165`–`179`). Der Player-Updatepfad (`:289`–`320`) aktualisiert Status und FPS, keine Regler. State-Restore (`build_p1_material_state.py:181`–`201`) setzt ebenfalls nur die zentralen Parameter. Damit fehlt im Repository ein Rückkanal für Materialwechsel, Presetbuttons, RESET VIEW, native Parameterfenster und die zweite Oberfläche. Die frühere Duplikatkorrektur löst dieses Problem nicht. Akzeptanz: Browser und Player offen; Parameter in jedem der vier Wege ändern; beide Anzeigen und Engine stimmen innerhalb 100 ms überein; programmatischer Sync löst keinen Rückschreibzyklus aus. Tests müssen echte Ereignisfolgen und mindestens einen Mausdrag enthalten.

**MB-02 · P1 · Materialaktivierung beginnt vor Erfolg und ohne Transaktion.** `select_slot()` aktiviert State und wendet Zielparameter bereits in `:1033`–`1035` an; fehlende Library, fehlender Katalogeintrag oder Compilefehler führen erst später zum Abbruch (`:1042`–`1059`). Folge: Das alte sichtbare Material kann mit Zielparametern weiterlaufen; State-Key und tatsächlicher Renderer können auseinanderliegen. Bei Core-Wechsel werden `Source` und `Material` nacheinander gesetzt (`:1037`–`1038`), während der zentrale Parametercallback beide überwacht (`build_p1_material_state.py:338`). Die konkrete TD-Callbackreihenfolge ist zusätzlich live zu prüfen. Empfehlung: Ziel vorbereiten/kompilieren, dann atomarer Commit von aktiver ID, Quelle und State; bei jedem Fehler exakten Vorgängerzustand behalten. Akzeptanz: fehlende Library, fehlender Record, defekter Shader sowie Core↔Import lassen bei Fehlschlag Source, aktive ID, alle Werte, Phase und Output-Hash unverändert.

**MB-03 · P2 · Zwei verschiedene „Master“-Begriffe und irreführender Ausgabestatus.** Sichtbar „MASTER SPEED“ schreibt `Speed`; `Globalmasterspeed` existiert separat mit 0–4 (`build_p1_material_state.py:327`). Die Labels suggerieren einen globalen Wert, tatsächlich ist Speed materialbezogen. Zusätzlich behauptet `refresh()` unabhängig vom Sender `DMX OFF` (`build_unified_material_browser.py:914`), obwohl eine Materialkarte eine bereits aktive Ausgabe verändern kann. Akzeptanz: „Material Speed“ und „Global Master“ unterscheidbar, Faktorwirkung erklärt; Ausgabestatus ausschließlich aus zentralem gemessenem Senderzustand oder ausdrücklich „Browser startet keine Ausgabe“.

**MB-04 · P2 · Bereichs-/Feedbackvertrag bleibt uneinheitlich.** Browser-Zoom endet bei 4, Player-Zoom bei 8; Player-Scale bei 4, Zustand erlaubt 128 (`material_state.py:62`, `build_unified_material_browser.py:265`, `:350`, `:354`). Aktive Core-/Importkarte und aktive Gradient-/Tempo-Presets bekommen im Renderpfad keine eigene Auswahlfarbe (`:978`–`1018`). Keine kontextspezifischen Tooltips oder exakte Werteingabe im Builder. Empfehlung: Zentraler Bereichsvertrag, sichtbare Zahlen und Herkunft „Default/Override“, eindeutige Auswahl; Werte außerhalb des UI-Normalbereichs dürfen nicht still verschwinden. Akzeptanz: Material mit Scale 7 und Zoom 8 öffnen, Wert sehen, unverändert verlassen und exakt wiederherstellen; Gradient per Custom-RGB als Custom markieren.

## Dialog 3 – MadMapper Library

### Inventar und Bindungen

| Element | Implementierung / Verhalten |
|---|---|
| Suche/Apply, GROUP, COMPAT, REFRESH CATALOG | Lokaler Katalog, tolerante Suche, Facetten, gezielter Refresh (`build_material_library_browser.py:541`–`624`) |
| VIEW 4×2/8×4, PREVIOUS/NEXT, Seitenstatus | 8/32 Einträge; wiederholbare Button-CHOP-Flanken und deaktivierte Randnavigation (`:219`–`241`, `:516`–`520`, `:626`–`710`) |
| Bild/Text/gesamte Kartenfläche | Eigene Hit-Area und Auswahl-/Hovercallbacks (`:181`–`217`, `:243`–`266`, `:720`–`752`) |
| Auswahlbild, Name, Gruppe, Kompatibilitätsgrund, Tags | `select_slot`, gespeicherter `selected_id` und Detailbereich (`:712`–`752`) |
| SHOW STORED PREVIEW | Validiertes lokales Bild; kein Produktionsquellenwechsel (`:754`–`771`) |
| OPEN LIVE PREVIEW | Adaption und Compile auf **live_preview** (`:1169`–`1224`); bei aktiver importierter Quelle produktionswirksam |
| IMPORT SELECTED → CONFIRM IMPORT | Zwei-Schritt-Bestätigung, verwalteter Paketimport, vorbereiteter Shader und Historie (`:787`–`846`) |
| Hover | Eigenes GLSL-TOP, Quell-/Wertecache bis 16 Materialien, Restore von Karte und Detail (`:1052`–`1167`) |
| Backendparameter | Catalogfile, Importroot, Approvedroots, Cards/Page, Coordinate Mode, Raster/Hybrid, Hoverloopseconds; nicht als vollständiger sichtbarer Inspector in Dialog 3 umgesetzt |

### Befunde

**ML-01 · P1 · „Isolated local TOP“ ist für OPEN LIVE PREVIEW nicht wahr, wenn Import bereits produziert.** `live_preview.outputConnectors[0].connect(imported_output)` (`build_material_library_browser.py:1357`–`1358`) publiziert genau das TOP, dessen Shader OPEN LIVE PREVIEW in `:1191` überschreibt. Der Unified Browser nutzt dieses Output als Source (`build_unified_material_browser.py:1165`–`1171`). Der Status „production source unchanged“ (`Library:1221`) schützt lediglich den Switchindex, nicht den Bildinhalt. Bei Compilefehler wird eine Fehlervorschau angezeigt, aber der vorherige Produktionsshader nicht zurückgesetzt (`:1201`–`1214`). Der Hoverpfad ist inzwischen korrekt separat; das darf nicht auf OPEN LIVE übertragen werden. Empfehlung: Wirklich isolierter Kandidatenrenderer plus expliziter „LIVE ÜBERNEHMEN“-Schritt. Akzeptanz: Aktives Material A mit Output-Fingerprint; in Dialog 3 B vorhören und defektes C kompilieren; Fingerprint, aktive ID, Phase und Produktionsparameter bleiben A, bis Übernahme bewusst erfolgt.

**ML-02 · P1 · Browserauswahl ist fälschlich die aktive Materialidentität.** `_current_key()` nimmt bei Source imported `browser_state.selected_id` (`build_p1_material_state.py:206`–`215`); Native-Parameter lesen ebenfalls `_selected()` (`build_material_library_browser.py:956`–`960`, `:1023`). Ein reiner Library-Kartenklick ändert selected_id (`:726`), ohne einen vollständigen Wechsel des aktiven Renderers oder der State-Identität vorzunehmen. Szenario: A produziert; in Library B auswählen; zentrale Speedänderung oder Native Params anschließend bedienen. Dann kann B als Stateziel behandelt werden, obwohl A noch rendert; Uniforms von B können in das TOP von A geschrieben werden. Akzeptanz: Stabile `active_material_id`, `selected_catalog_id`, `preview_material_id` getrennt; B-Suche und Kartenwahl ändern weder State noch Werte von A; Drawer zeigt explizit, welches dieser Ziele bearbeitet wird.

**ML-03 · P2 · Wiederfinden von prepared.frag ist repariert, eigenständiges Paketabspielen nicht gesichert.** `_managed_import_status()` ist streng und vorhanden; der neue Test führt tatsächlich zwei frische Runtime-Normalisierungen gegen ein temporäres Paket aus (`tests/test_material_library_browser.py:224`). OPEN LIVE nutzt aber nicht einfach den gefundenen Shader: `_parameter_context()` ruft `_adaptation_for_item()`, das zwingend ursprüngliche `.fs`, Katalog und source_root erneut liest (`build_material_library_browser.py:903`–`925`, `:1185`). Ein intaktes verwaltetes Importpaket genügt daher nicht, wenn der ursprüngliche Sourcebaum verschoben/gelöscht ist. Empfehlung: Vertrag klären: selbsttragendes Importpaket mit Schema/Includes oder sichtbar dokumentierte Originalquellen-Abhängigkeit. Akzeptanz: Neustart-Test mit intaktem Paket und nicht verfügbarem Original liefert entweder funktionsfähige Wiedergabe oder vorab verständliche, eindeutige Blockade ohne Produktionsmutation.

**ML-04 · P2 · Weggefilterte Auswahl bleibt aktionsfähig.** `apply_filters()` baut `_filtered`, Seite und Render neu, prüft aber selected_id nicht (`:603`–`624`); `_selected()` sucht weiter im Gesamtkatalog (`:712`–`714`). Der alte Auditbefund ist im aktuellen Code weiterhin nachvollziehbar. Akzeptanz: Auswahl entweder löschen und Aktionsbuttons deaktivieren oder als „außerhalb des Filters“ mit Materialname markieren; Importbestätigung nach Filter-/Auswahlwechsel erneut und zielgenau erforderlich.

**ML-05 · P2 · Vorschau-/Importregeln bleiben widersprüchlich.** OPEN LIVE blockiert adaptable ohne prepared-Pfad (`:1174`–`1183`), während Hover adaptierbare Originale direkt prüft (`:1052`–`1099`). Für Bediener ist unklar, warum dieselbe Karte beim Hover animiert, aber im großen Preview erst Import verlangt. Empfehlung: Gemeinsame Kandidatenfreigabe und eindeutige Labels „Gespeichertes Bild / Vorschau / Importieren / Live übernehmen“. Import bleibt bewusst schreibend; Vorschau muss die Isolation aus ML-01 erfüllen.

**ML-06 · P2 · Refresh/Hover brauchen Profildaten, keine pauschale FPS-Behauptung.** Refresh normalisiert alle 638 Einträge samt Dateiexistenz-/Manifestprüfungen (`:585`–`591`, `:395`–`411`). Höchstens ein Hover-Renderer und Cache von 16 Einträgen sind sinnvoll; ein Materialwechsel kann dennoch synchron kompilieren. Empfehlung: Relevante Daten gecacht nach Quellstamp, kurze Hover-Verzögerung gegen versehentliches Streifen vieler Karten, sichtbarer Lade-/Compilezustand. Akzeptanz: gemessene p50/p95/p99 von Refresh, Hover und Bildwechsel bei 4×2/8×4; Render-/Send-FPS parallel protokollieren; keine Aussage „ruckelfrei“ aus Offline-Tests.

**ML-07 · P1 Prüfbedarf · Echter NEXT-Klick ohne Seitenfortschritt trotz korrekter Callbackverdrahtung.** Beim ergänzenden Hauptaudit blieb die Library nach echtem NEXT-Klick und verzögerter Nachbeobachtung auf **PAGE 5/20, 638 Ergebnissen** ([Screenshot](screenshots/03-madmapper-library.png)). Anschließende reine Live-Leseprüfung durch diesen Teilprüfer: `next_page_click` und `previous_page_click` sind beide `chopexec`, aktiv, `offtoon=True`, `channel=*`, auf den richtigen jeweiligen `.../next_page/out1` bzw. `.../previous_page/out1` gebunden; Quelltext ruft korrekt `runtime.module.change_page(±1)` auf. Keine Operatorfehler. NEXT ist `momentary`, enabled/displayed, Layer 120, `clickthrough=False`, mit `rollover=1`; nach Release sind state/lselect/value0/out1.v1 jeweils 0. Tabelle und gespeicherter Runtimepagewert stehen beide auf 4 (nullbasiert). Die internen Buttoncallbacks sind ebenfalls aktiv und verdrahten panel.state→value0→Parameter-CHOP→out1.

Damit sind falscher Callbackpfad, deaktivierter Button, Togglemodus oder offensichtlich fehlende Verdrahtung **nicht** die nachgewiesene Ursache. Der Code nimmt eine Momentary-Flanke über einen CHOP ab (`build_material_library_browser.py:219`–`239`, `:1548`–`1549`); eine zwischen Auswertungen verlorene kurze Flanke war zunächst ein Timingkandidat. **Auch wiederholte normale Klicks und eine gehaltene Drag-Geste vollständig innerhalb von NEXT (870,887→902,887) blieben laut Hauptaudit jedoch auf PAGE 5.** Damit ist die kurze Klickdauer gerade nicht als Ursache bestätigt; ein Timingfix darf nicht als bewiesene Lösung angeboten werden. Die genaue Fehlerquelle bleibt offen und braucht Beobachtung der Zwischenzustände während einer realen Geste. Ein früher nicht reagierender Browser-PREV verwendet direkt PanelExecute/state (`build_unified_material_browser.py:134`–`148`), darf also nicht ohne Nachweis derselben Ursache zugeordnet werden. Akzeptanz: 20 kurze und 20 gehaltene NEXT/PREV-Klicks bei 4×2 und 8×4, jede Geste genau ein Schritt, keine verschluckten oder doppelten Flanken, korrekte Grenzen und keine Materialauswahl durch Navigation. Bisheriger echter NEXT-Test bleibt bis zur Aufklärung **nicht bestanden**, auch wenn die Offline-Pagingtests grün sind.

## Dialog 4 – Material Player und Native Params

### Player-Inventar

Player ist jetzt eine 1180×720-Oberfläche (`build_unified_material_browser.py:326`). Titel, Source-/Materialstatus und FPS-Zeile stehen über einer 720×506-Vorschau. Acht Slider: Material-Speed 0–2, Scale 0,1–4, Width 0–1, Focus X/Y 0–1, Zoom 0,25–8, Intensity 0–2, Contrast 0,1–4 (`:348`–`360`). OPEN MATERIAL BROWSER und RESET VIEW sind vorhanden (`:361`–`369`). Vorschau priorisiert seit `725d6b0` den Gradient-Postprozess (`:339`–`346`), obwohl der Titel noch „RAW MATERIAL“ heißt.

Weiterhin nur über zentrale Parameterseiten oder andere Dialoge: Source/Materialwahl, Color A/B, Gradientmenü, Koordinatenmodus, Trail/Direction/Rotation/Seed/Transition/Density/Hybrid/Raster und echter Global Master. Intensity/Contrast sind zentrale Core-Uniforms (`effects/build_core_effects.py:110`–`111`), nicht generische native Materialparameter; im Importadapter werden Scale/Width/Framing/Coordinate gebunden, aber keine gleichnamige globale Intensity/Contrast (`build_material_library_browser.py:1333`–`1351`). Player sollte für importierte Quellen die Wirkung erklären oder nicht wirksame Controls deaktivieren.

### Ergänzte echte Player-Mausabnahme und Uniformprüfung

Das Hauptaudit hat anschließend **alle acht sichtbaren Player-Slider mit echten Mausaktionen** geprüft. Je Aktion wurde genau der beabsichtigte zentrale Parameter geändert; die Änderungen wurden nacheinander kumuliert und am Ende gemeinsam wiederhergestellt. Die unabhängig ausgewerteten Dateien [ui-before.json](ui-before.json), `ui-speed/scale/width/focusx/focusy/zoom/intensity/contrast.json` und [ui-restored.json](ui-restored.json) enthalten zentrale Werte, Statekopien und Uniforms von Core, Import, Gradient und Sampler. Damit liegt für diese acht Regler jetzt mehr als ein String-/Callbacktest vor.

| Mausaktion | Tatsächlicher neuer Wert | Core-Bindung | Aktiver Import `live_preview` | Urteil |
|---|---:|---|---|---|
| Speed | 0,99208443 | Phase `uParams0.y` läuft weiter | `uTDMaterial0.x` trägt denselben Phasenwert | UI→Parameter PASS; gemeinsame Phase bestätigt, exakte Tempo-Steigung nicht aus einzelnen Snapshots beweisbar |
| Scale | 2,03456464 | `uParams0.z` aktualisiert | `uTDMaterial0.y` gleicher Wert | UI und beide Uniformbindungen PASS |
| Width | 0,74934037 | `uParams0.w` aktualisiert | `uTDMaterial0.z` gleicher Wert | UI und beide Uniformbindungen PASS |
| Focus X | 0,74934037 | `uParams4.x` aktualisiert | `uTDMaterial1.x` gleicher Wert | UI und beide Uniformbindungen PASS |
| Focus Y | 0,24802111 | `uParams4.y` aktualisiert | `uTDMaterial1.y` gleicher Wert | UI und beide Uniformbindungen PASS |
| Frame Zoom | 2,17216359 | `uParams4.z` aktualisiert | `uTDMaterial0.w` gleicher Wert | UI und beide Uniformbindungen PASS |
| Intensity | **0** | `uParams1.y` wird 0 | Keine Änderung irgendeines statischen Importuniforms | UI→Core PASS, gemeinsame Intensitätswirkung für Import **nicht vorhanden** |
| Contrast | 2,05514512 | `uParams1.z` aktualisiert | Keine Änderung irgendeines statischen Importuniforms | UI→Core PASS, gemeinsame Kontrastwirkung für Import **nicht vorhanden** |

Der Importadapter verwendet Scale/Width/Focus/Zoom auch tatsächlich in seiner Frame-UV-Formel (`madmapper_td_adapter.py:304`–`321`); Width wirkt dort als horizontale Streckung `0.5/width`, nicht automatisch wie der namensgleiche Effektregler jedes nativen Materials. Bei Intensity/Contrast ändern sich weder Gradient- noch Sampleruniforms; beim Import ändert sich zwischen den beiden letzten Prüfungen lediglich die normale laufende Phase. Der Gleichlauf beider Phaseuniforms ist in jedem Snapshot sichtbar.

Der nach dem Intensity-Drag beruhigte [Screenshot bei Intensity 0](screenshots/04-intensity-zero-not-black.png) zeigt weiterhin eine blaugrüne, nicht schwarze Fläche, Source IMPORTED und OUTPUT OFF. Das bestätigt die Bedienabweichung: Der vermeintlich gemeinsame Intensitätsregler dunkelt den aktiven Import nicht ab. **Dieser konkrete Screenshot isoliert nicht die Gradient-Schwarz-Anhebung als Ursache**, weil Intensity schon gar nicht an den Import gebunden ist. G-01 bleibt ein gesonderter mathematischer Beweis der Postprozessformel; es werden keine exakten gerenderten RGB-Werte aus einem zeitlich inkonsistenten Pixelread behauptet.

Restore-Prüfung: Acht zentrale Werte stimmen in `ui-before`/`ui-restored` exakt überein; native State-Tabelle ist bytegleich; sämtliche statischen Uniformwerte sind wieder gleich. Nur Core-/Importphase ist erwartungsgemäß gemeinsam fortgeschritten. Alle zehn Snapshots melden `sender_enabled=false`. Laut Hauptaudit wurden darüber hinaus die ursprünglichen vollpräzisen Material-State-Settings wiederhergestellt; die gerundeten zentralen UI-Werte sind nicht als Ersatz für diese Präzision verwendet worden. Kein Render-/Hardware-Blackout wurde beansprucht.

### Native-Params-Inventar

Der Drawer gehört tatsächlich **Dialog 2**, erreichbar über NATIVE PARAMS beziehungsweise automatisch nach erfolgreicher Importwahl; hier gemeinsam mit Player-State geprüft. 16 Zeilen pro Seite, zwei Spalten, ein gemeinsamer Editor mit bis vier Komponenten (`build_unified_material_browser.py:389`–`479`). Materialname, Zahl der Parameter, Seitentext; Typ-/Gruppen-/Wertlabel; ausgewählte Zeile farbig (`:630`–`650`, `:715`–`765`). Float/Int über Slider; Bool ON/OFF, Event TRIGGER, Long/Enum zyklisch; Point/Size/Range/Color über Komponenten (`:652`–`698`, `:799`–`815`). PREVIOUS/NEXT nur bei Überlauf; RESET MATERIAL unmittelbar; ZURÜCK unten und oben; erklärter Fehlerzustand ohne Parameter (`:700`–`714`). Kein Farbrad, keine numerische Direkteingabe und kein Undo-/Reset-Bestätigungsschritt im Builder.

### Befunde

**MP-01 · P2 · Importstatus liest die falsche Tabelle.** Player sucht `selected_id` in `material_parameter_state` (`build_unified_material_browser.py:292`–`302`). Der Producer schreibt dorthin ausschließlich Header `key/json` und Zeile `document/<JSON>` (`build_material_library_browser.py:343`–`349`); selected_id liegt in `browser_state`. Deshalb wird im normalen Datenvertrag keine Import-ID gefunden, während `CONTROLS.par.Material` weiterhin den zuletzt gewählten Core-Namen enthält. Akzeptanz: Status verwendet stabile aktive Render-ID aus ML-02 und zeigt Namen/Quelle/Overridezustand des tatsächlich dargestellten Materials; Null-/gelöschter Record verständlich behandelt.

**MP-02 · P1 · Nativer Fehler-Rollback besitzt keinen unabhängigen Snapshot.** `ImportedMaterialStateStore.to_dict()` gibt `entry.types` und `entry.values` als gemeinsame Dictionary-Referenzen zurück (`imported_material_state.py:107`–`113`). `set_material_parameter()` speichert dieses Objekt als `previous_document`, mutiert anschließend Werte und restauriert im Fehlerfall daraus (`build_material_library_browser.py:1030`–`1044`). Isolierte Probe am 7. September: Ausgangs-gain 1 → `before = store.to_dict()` → gain 3 → `from_dict(before)` ergibt **3 statt 1**. Zusätzlich stellt `_activate_parameter_shader()` bei Compilefehler nur Shadertext zurück, nicht Uniforms/Schema-Tabelle (`:987`–`998`), und RESET MATERIAL löscht den Eintrag vor erneuter Aktivierung ohne Transaktionsschutz (`:1010`–`1019`). Empfehlung: unabhängiger Snapshot und gemeinsamer Commit/Rollback für Werte, Shader, Uniforms, Tabellen und vorbereitete Datei. Akzeptanz: injizierter Fehler bei uniform set, GPU compile und Dateischreiben lässt alle fünf Zustandsbereiche byte-/wertgleich zum Vorgänger; Resetfehler ebenso.

**MP-03 · P1 · Native-Drag ist unnötig teuer.** Pro Sliderereignis ruft `native_editor_value_changed()` snapshot → set → snapshot (`build_unified_material_browser.py:784`–`789`). Jeder dieser drei Wege verwendet `_parameter_context()`; jeder Kontext adaptiert **zweimal** (`build_material_library_browser.py:922`–`929`). Jede Adaption lädt zwei Module erneut und liest den kompletten Katalog (`:906`–`915`). Ein normaler Uniformdrag kann somit sechs Adaptionsdurchläufe plus mehrfaches Persistieren/Schema-Neuschreiben und einen erzwungenen Cook auslösen (`:931`–`954`, `:1036`–`1040`). Das ist ein Quellcode-Kostenmodell, keine heute gemessene Millisekundenzahl. Empfehlung: Schema/Adaption je Material+Source-/Include-Hash cachen; Uniformdrag nur Zielwert setzen; Compile-Time-Änderungen separat und gedrosselt übernehmen; Tabelle bei Commit statt jedem Sample. Akzeptanz: 100 Dragereignisse ohne Sourceänderung → null Katalogreloads/Shaderadaptionen, höchstens ein Uniformupdate pro Renderframe; numerische Werte und Persistenz korrekt; definierte p95-Interaktionslatenz ≤50 ms auf Zielrechner, ohne erhöhte Send-Aussetzer.

**MP-04 · P2 · Event-Reset kann nach einem Materialwechsel das falsche Material treffen.** `pulse_material_parameter(name)` plant einen Frame später `set_material_parameter(name, -1, 0)` ohne Material-ID (`build_material_library_browser.py:1047`–`1049`). Der Setter löst dann die **aktuelle** Auswahl auf. Bei Event in A und Wechsel zu B kann A auf 1 verbleiben und B auf 0 gesetzt werden bzw. der Reset fehlschlagen. Akzeptanz: Reset bindet Material-ID und Generation des Triggers; A-Event, B-Auswahl im selben Frame und Neustart/Reset werden durch echte Zustandsfolgetests abgedeckt.

**MP-05 · P2 · Persistenzumfang und Speicherzeitpunkt sind nur teilweise erklärt.** Core-State speichert ausdrücklich Speed/Scale/Width/Framing/Gradient/A/B/Coordinate, nicht Intensity, Contrast, Trail, Direction, Rotation, Seed, Transition, Density oder Hybridmix (`material_state.py:44`–`56`, Adapter `:165`–`178`). Das entspricht dem dokumentierten P1-Teilumfang, ist aber kein vollständiges „Material-Preset“. Phasen werden im laufenden Store getickt; die JSON-Tabelle wird bei Änderungen/Activate geschrieben, nicht pro Tick oder per dediziertem Before-Save-Checkpoint (`build_p1_material_state.py:148`–`154`, `:260`–`280`). Bei Initialisierung wird die Tabellenkopie vorgezogen (`:226`–`228`). Exakte Phase beim Speichern nach langer unveränderter Wiedergabe ist damit nicht durch die jetzigen Tests belegt. Native-Paging hat zusätzlich Backendseiten à 6 (`Library:961`) und UI-Seiten à 16 plus globalem Browser-Page-Store (`Unified:731`, `:831`): keine einheitliche per-Material-Pagequelle. Akzeptanz: explizite Liste persistent/global/laufzeitbezogen; Save/Reopen-Test nach 60 Sekunden ohne Controländerung; zwei Materialien mit unterschiedlichen erweiterten Werten und Drawer-Seiten reproduzierbar wiederöffnen.

**MP-06 · P1 Prüfbedarf · Drawer-Anzeige kann als Parameterbearbeitung behandelt werden.** Der beobachtete Footer nach bloßem Öffnen ist nicht Teil von `toggle_native_parameters()` oder `render_native_parameters()`: Diese Wege sollen nur anzeigen (`build_unified_material_browser.py:568`–`577`, `:715`–`765`). Beim Rendern wird der Parametername im gemeinsamen Editor abgelegt, der Sliderwert programmatisch gesetzt (`:660`, `:693`) und der Parameterexecute-Handler anschließend sofort wieder aktiviert (`:698`). Es gibt zwar lokale Deaktivierung beim Befüllen (`:685`–`686`), aber der Callback selbst besitzt **keine** Prüfung „UI wird befüllt“, keine Bindung an eine echte Benutzergeste und keinen Vergleich mit dem bereits gespeicherten Wert (`:184`–`199`, `:777`–`793`). Ein verzögert zugestelltes Value-Change-Ereignis oder eine beim erneuten Aktivieren erkannte Wertänderung könnte deshalb einen Schreibpfad auslösen; die genaue TD-Ereignisursache ist noch nicht nachgewiesen.

Zusätzliche Offline-Verhaltensprobe: Die echte Funktion `native_editor_value_changed` wurde per AST isoliert und mit Fake-Library/Controls ausgeführt. Snapshot `mat_scale=0.2581`, Callbackwert ebenfalls `0.2581` → Ergebnis `True`, dennoch Setteraufruf `('mat_scale', -1, 0.2581)` und Status `NATIVE PARAMETER UPDATED - mat_scale`. Damit ist ein **unnötiger Schreib-/Cookpfad bei unverändertem Wert** bestätigt; der Footer allein beweist gerade nicht, dass sich der Wert geändert hat. Der globale Scale-Wert 3,91768 aus der Baseline ist ein anderer Parameter und kein gültiger Vorherwert für mat_scale.

Empfehlung: UI-Befüllung als explizite, über Eventgrenzen gültige Transaktion; Handler gegen programmatische Initialisierung/alte Editorbindung absichern, identische Werte als No-op behandeln. Akzeptanz: native Zustandstabelle, native Werte, Shadertext, Uniforms und Schreib-/Cookzähler vor/nach zehn Öffnen/Schließen-/Zeilenwechselzyklen vergleichen; **keine** Set-/Persist-/Compile-/Dateischreibaktion allein durch Navigation, keine UPDATED-Meldung. Danach separater echter Sliderdrag muss genau das richtige Material/den richtigen Parameter verändern. Noch keine funktionale Korrektur vorgenommen.

## G-01 – verpflichtende Detailprüfung des letzten Commits 725d6b0

**P1, bei Nutzung von Material-Intensity=0 als Dunkelstellung vor Live-Einsatz zwingend prüfen.** Der Commit setzt zwischen `visual_source_switch` und `res1` einen GLSL-Postprozess (`build_p1_material_state.py:63`–`105`). Für Core und Import ist der Mischfaktor fest **1**, für Movie/Show **0** (`:91`–`95`). Es gibt keine sichtbare Enable-, Stärke- oder Original-Option. RGB wird nach Luminanz in Color B→A umgefärbt:

`luma = clamp(dot(rgb, (0.2126, 0.7152, 0.0722)), 0, 1)`; `palette = mix(B, A, smoothstep(0,1,luma))`; `output = palette × (0.38 + 0.80 × luma)` (`:25`–`31`).

| Eingangsfall | Aus der Formel resultierender Effekt | Fachliche Auswirkung |
|---|---|---|
| Schwarz RGB (0,0,0), Source materials/imported | `0.38 × B`; Neon B=(0,0.72,0.86) → **(0,0.2736,0.3268)** | Dunkle Pixel werden sichtbar farbig; nicht schwarztreu |
| Core Fill oder colorize mit Intensity=0 | Core gibt Schwarz aus (`effects/core_effects.frag:383`, `:397`); Gradient macht daraus obigen Sockel | Player-Intensity 0 bedeutet im Endbild nicht mehr dunkel |
| Weiß / luma=1 | `1.18 × A` | Komponenten können 1 überschreiten; genaue Clippingwirkung hängt vom TOP-Format ab und braucht GPU-Test |
| Ursprünglich mehrfarbiges Importmaterial | Farbinformation wird komplett durch zwei globale Farben ersetzt | Native Farbregler ändern teils nur Luminanz/indirekte Form, nicht erwartete Originalfarbe |
| Core bereits durch A/B koloriert | Zweite A/B-Kolorierung nach Luminanz | Nichtlineare Doppelanwendung; Presetfarben bestimmen zusätzlich Kontrastverlauf |
| Source movie/show | Mischfaktor 0 | Shaderformel bewahrt Source-RGB; kein belegter Show-Blackoutdefekt aus dieser Änderung |

Die neue Stufe macht Presets sichtbar, ändert aber **alle** Materiallooks schon ohne einen neuen Gradientklick. `apply_gradient()` erzwingt zusätzlich den Cook (`material_control_surface.py:169`–`171`); sie ist nicht der Enable-Schalter. Titel „RAW MATERIAL“ ist nun sachlich falsch. Direkte Änderung des Gradient-Menüs allein bleibt ebenfalls unvollständig: Der Parametercallback speichert nur den Namen über `controls_changed()`; er ruft `apply_gradient()` nicht auf (`build_p1_material_state.py:260`–`272`, `:288`–`289`). RGB-Änderungen können einen alten Presetnamen stehen lassen.

Empfehlung zur Reviewentscheidung: Original als expliziter Default/Bypass, optionaler Gradient mit definierter Stärke, schwarztreue und monotone Helligkeitsfunktion, getrennte Regeln für Core und nativen Import-Look; Color-/Gradient-Anwendung als atomare State-Änderung. Akzeptanz: GPU-Pixeltest für Schwarz, Weiß, RGB-Grundfarben, Graurampe, Intensity 0 und Alpha; Core+Import bei fünf Presets, Color-Custom, Switch/Reopen; Movie und Show einschließlich Blackout pixelgleich; Native-Farbreglerwirkung dokumentiert. Histogramm/Pixelhash und sichtbarer realer Gradientbuttonklick gehören beide zur Abnahme. Bestehende Tests prüfen den Formeltext und die Verkabelungsstrings, **nicht** diese fachlichen Eigenschaften.

## Testqualität und gezielter Ausbau

Am 7. September ausgeführt: `python -m unittest tests.test_material_state tests.test_material_control_surface tests.test_material_browser_player_regression tests.test_unified_material_browser tests.test_material_library_browser tests.test_material_library tests.test_material_library_paging tests.test_imported_material_state tests.test_madmapper_parameters tests.test_madmapper_td_adapter tests.test_sync_madmapper_library -v` → **93 Tests, OK, 2,448 s** (isolierter lokaler Lauf). Temporäre Importfixture-Schreibvorgänge dieser bestehenden Tests betreffen nur deren Testverzeichnisse; kein Live-Projekt wurde beschrieben.

| Testklasse | Aussagekraft | Fehlende Schicht |
|---|---|---|
| MaterialStateStore und ImportedMaterialStateStore | Reale Python-Logik: Phase, Werte, Schema-Merge, JSON-/Seitenmodell | TD-Ereignisfolge, vollständige Save/Reopen-Persistenz, unabhängiger Rollback-Snapshot |
| Bibliotheksimport/Adapter/Paging | Reale Dateisicherheits-/Parsing-/Paginierungslogik und künstliche Fixtures | GPU-Kompilierung des vollständigen Bestands, tatsächliche Materialbilder und Bedienbarkeit |
| Persisted-managed-import-Test | Frische Runtime-Normalisierung löst vorhandenen Pfad wirklich auf | Führt OPEN LIVE PREVIEW nicht erfolgreich durch, testet keine fehlende Originalquelle |
| Unified-/Library-Builder-Verträge | Python parse/compile, erwartete Namen/Strings/Callbackpfade | Instanziierung, doppelte Controls, Focus/Hitareas, Callback-Ausführung und Ausgabeschutz |
| Neue Gradienttests in 725d6b0 | Existenz von Shaderformel, Postprozess-Cook und Previewpriorität | Keine gerenderten Pixel, Schwarz-/Weißverträge oder Presetwirkung |
| Zusatzprobe dieses Audits | Beweist aliasierenden Rollback-Snapshot (1 wird nach Restore 3) | Noch kein integrierter Fail-Injection-Test im Produktionsadapter |

### Reproduzierbare kleine Offline-Beweise

Die folgende Python-Probe kann aus der Repositorywurzel in einer normalen Python-Sitzung laufen. Sie benötigt kein TouchDesigner, liest/schreibt keine Live-Daten und verändert keine Dateien:

```python
from pixelblaze_mapper.imported_material_state import ImportedMaterialStateStore
from pixelblaze_mapper.madmapper_parameters import parameter_schema
from pixelblaze_mapper.material_control_surface import GRADIENT_PRESETS

schema = parameter_schema({"INPUTS": [
    {"NAME": "gain", "TYPE": "float", "DEFAULT": 1, "MIN": 0, "MAX": 4}
]})
store = ImportedMaterialStateStore()
store.merge("audit-a", schema)
before = store.to_dict()
store.set_value("audit-a", schema[0], 3)
restored = ImportedMaterialStateStore.from_dict(before)
print("Erwarteter Rollbackwert: 1; tatsächlicher Wert:",
      restored.values("audit-a")["gain"])
print("Snapshot aliasiert:", before["materials"]["audit-a"]["values"]["gain"] == 3)

# Exakte Reduktion von GRADIENT_SHADER_SOURCE für source.rgb=(0,0,0), mix=1.
for key, preset in GRADIENT_PRESETS.items():
    print("Schwarzeingang nach Gradient", key,
          tuple(round(0.38 * c, 6) for c in preset.color_b))
```

Erwartetes Ist-Ergebnis bei HEAD 725d6b0: Rollbackwert **3,0**, Alias **True**; Neon-Schwarz wird `(0.0, 0.2736, 0.3268)`, Acid-Schwarz `(0.0, 0.0684, 0.38)`. Der erste Teil wurde isoliert ausgeführt; der zweite ist eine direkte CPU-Auswertung der eindeutig reduzierten Shaderformel, kein GPU-Bildtest. Nach einer freigegebenen Korrektur muss ein echter Regressionstest den Rollbackwert 1 erwarten und die beschlossene Gradient-Schwarzsemantik testen.

Sinnvolle nächste Tests vor weiteren UI-Politurmaßnahmen: transaktionaler Materialwechsel; Library-Vorschau bei laufendem Import A; selektiert B/aktiv A; Native-Compilefehler mit Rollback aller Ressourcen; Trigger plus Sofortwechsel; identische Werteanzeige in Browser/Player/Parameterfenster; Gradient-Schwarztest; echte Mausabnahme für 2/3/4 samt Native-Back/Paging und Kaltstart. Hardwaretests nur beaufsichtigt und ausdrücklich autorisiert. Die im alten Audit gemessenen 11,8 FPS sind historische Daten und werden hier nicht als aktuelle Messung ausgegeben.

## Bewertung 0–10 und Abnahmeschwelle

Scores sind aktuelle **Code-/Test-Reife einschließlich der ergänzten Teil-Mausabnahme**, mit offen ausgewiesener noch fehlender vollständiger Ereignisfolgen-/GPU-Abnahme. Sie sind keine Fortschreibung alter Live-Scores und keine Hardwarefreigabe.

| Kriterium | Dialog 2 | Dialog 3 | Dialog 4 inkl. Native | Begründung |
|---|---:|---:|---:|---|
| Nutzbarkeit | 6 | 7 | 6 | Kompakte Wahl/Filter und echter Player vorhanden; inkonsistente Labels/Sync, aktive vs selektierte ID und Nativebedienung bleiben unklar |
| Technische Umsetzung | 6 | 6 | 6 | Wiederverwendbare pure State-/Adapterlogik, eigener Hover; keine gemeinsame Transaktion/Identitätsquelle |
| Zuverlässigkeit | 4 | 4 | 4 | Fehlwechsel, nicht isolierte explizite Preview, Rollbackalias und Gradient-Schwarzregression trotz grüner Suite |
| Wartbarkeit | 5 | 5 | 5 | Große eingebettete Runtimeblöcke, harte Projektpfade und direkte modulinterne Zugriffe; native Hotpath-Reloads |
| Vollständigkeit | 6 | 7 | 6 | Kernworkflows vorhanden; Original-/Gradientmodus, vollständiger Presetvertrag, Undo/Resetabsicherung und echte Integrationstests fehlen |
| Innovativität | 8 | 8 | 8 | Gemeinsamer Core/Importbrowser, adaptiver nativer Schemaeditor, sichere Importpakete, Hover und kontinuierliche Materialphase |
| Arithmetischer Mittelwert | **5,8** | **6,2** | **5,8** | Sicherheit/Zuverlässigkeit darf nicht durch den Mittelwert überstimmt werden |

## Dokumentation und optimierter Workflow nach Freigabe

1. **Vor jeder funktionalen Änderung:** aktive TOE und installierte DAT-Versionen gegen HEAD erfassen; Quelle, aktive/selektierte IDs, Werte, Senderstatus und Fingerprint dokumentieren. Historische Audit-FAILs als historisch markieren, nicht löschen.
2. **Reviewpaket P1:** G-01 (Gradiententscheidung), ML-01/02 (Preview/aktive Identität), MB-01/02 (Sync/Transaktion), MP-02/03 (Rollback/Hotpath). Jeweils zuerst ausführbarer Verhaltenstest, dann Implementierung und sichere UI-Abnahme; kein pauschales Builder-Neuausführen während einer Liveproduktion.
3. **Operatorworkflow:** Material suchen → gespeichertes Bild/isolierte Vorschau → ausgewähltes Material und Outputstatus prüfen → bewusst live übernehmen → materialbezogene Werte ändern → optional getrennten Global Master einstellen → Override/Default und Speicherstatus sehen. Native RESET MATERIAL soll Umfang nennen und Undo oder Bestätigung anbieten.
4. **Dokumentation zusammenführen:** `MATERIAL_BROWSER_CONTROLS_DE.md:43` („Gradient eventuell unsichtbar“) widerspricht 725d6b0; Player „RAW“ widerspricht Postprozess; `GICO_PORT_CONFIG_AND_MADMAPPER_PARAMETERS_DE.md` erklärt MASTER SPEED anders als der zusätzliche Global Master. P1-Dokument nennt korrekt Teilzustand, darf aber nicht als vollständiger Presetvertrag gelesen werden. Alte Importzahlen und frühere reine-Viewer-Beschreibung mit Versions-/Datumsbanner versehen.
5. **Hilfen in der Oberfläche:** pro Control Einheit, Bereich, Default, Quelle/Core/Import-Wirkung; Native Name/Gruppe/Compile-Time-Warnung; aktives Material klar getrennt von Auswahl und Preview; Stateänderung/Persistenzstatus; reproduzierbare Start-/Stop-/Restore-Schritte mit frischen Screenshots.
6. **Performanceabnahme:** Browser geschlossen/4×2/8×4, Library Hover an/aus, Player offen, Native kontinuierlicher Drag, Core/Import und Gradient Original/An messen. Render-FPS, tatsächliche vollständige Send-Frames, p95 Cook-/Interaktionslatenz, Shaderkompilierungen und Dateizugriffe getrennt ausweisen. Optimierungen erst mit diesen Vorher-/Nachherdaten bewerten.

Keine der Empfehlungen wurde in diesem Audit umgesetzt; Änderungen beschränken sich auf diesen Bericht.
