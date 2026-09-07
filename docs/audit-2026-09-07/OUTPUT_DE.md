# Frischer Audit – Dialoge 6, 7 und 0

Stand: 07.09.2026. Analyse aktueller Arbeitsbaumquellen, vorhandener Tests und früherer Audits. Keine funktionale Änderung, kein Aufruf einer laufenden TD-Funktion, kein UDP-/Hardwareverkehr, keine UI-Eingabe, kein Speichern und kein Commit durch diesen Teil-Audit. Bestehende uncommittete Dateien wurden erhalten. Kein `AGENTS.md` im Projekt gefunden. Livezustand und echte UI-Abnahme werden separat durch den Hauptaudit erfasst; Quellbefunde sind nicht automatisch Befunde der geladenen `.toe`.

## Kurzurteil und Abgrenzung zu alten Audits

Der reine Routing-/Packingkern ist gut abgesichert. Die Schwachstelle liegt an den Übergängen zwischen Feldentwurf, Routertabellen, GICO-Portmodell und sichtbarer Betriebsanzeige. Besonders kritisch sind ein nicht atomarer Router-Apply und die doppelte Universe-Umrechnung für GICO-Startuniversen größer als 1.

Dialog 7 ist im aktuellen Builder **kein altes Draft-Mockup mehr**, sondern eine schreibgeschützte Live-Zusammenfassung. Die alten Befunde zu editierbaren Ableitungen, Revert und überlappenden Altbuttons aus `docs/OUTPUT_CONFIG_REGRESSION_AUDIT_DE.md` dürfen deshalb nicht ungeprüft als aktuelle Defekte übernommen werden. Die aktuelle Rolle ist in `docs/P0_DIALOG_CONSOLIDATION_DE.md:9` und `pixelblaze_mapper/build_phase2_output_ui.py:135` implementiert. Ebenso existiert Sendertelemetrie inzwischen (`build_multi_controller_output.py:699`), ist aber noch nicht in diesen Dialogen sichtbar.

Alle nachfolgenden Dateiverweise sind relativ zum Projektroot; Zeilen beziehen sich auf den am 07.09.2026 gelesenen Arbeitsbaum.

## Gemeinsame Topologie: sechs Universen sind nicht die Router-Defaultkonfiguration

510 Kanäle / 3 Farbkanäle = 170 RGB-Pixel pro Universe. Das GICO-Modell berechnet bei sechs Universen je Port korrekt folgende Blöcke (`gico_port_config.py:280`, `build_gico_port_config_ui.py:254`):

| Port | UI-Universen bei Start 1 | Wire-Soll | Zielstart | Kapazität | vorbereitete Zuordnung |
|---|---|---|---:|---:|---|
| 1 | U1–U6 | U0–U5 | 0 | 1020 | Quelle 0–516, 517 Pixel |
| 2 | U7–U12 | U6–U11 | 1020 | 1020 | Quelle 517–785, 269 Pixel |
| 3 | U13–U18 | U12–U17 | 2040 | 1020 | Quelle 786–1183, 398 Pixel |
| 4 | U19–U24 | U18–U23 | 3060 | 1020 | 896 Pixel vorgesehen, Quelle leer: nicht geroutet |

Die sechs Universen sind **reservierte Portkapazität**, nicht sechs vollständig mit LEDs belegte Universen. Port 1 benötigt vier nichtleere Frames (170/170/170/7), Port 2 zwei (170/99), Port 3 drei (170/170/58). Der übrige reservierte Bereich wird schwarz gepackt; Port 4 ohne Quellzuweisung vollständig schwarz. Der GICO-Plan reserviert bei vier vorhandenen Ports 24 Universen, auch wenn Port 4 keinen Routingabschnitt erzeugt (`gico_port_config.py:100`; `multi_controller.py:371`).

Demgegenüber verwendet `default_router_config()` weiterhin **vier** Universen je Port, 12 reservierte Universen und Zielstarts 0/680/1360 (`multi_controller.py:406`, `:417`, `:423`). `docs/GICO_PORT_CONFIG_AND_MADMAPPER_PARAMETERS_DE.md:9` beschreibt sechs; `docs/P0_P1_APPROVED_DECISIONS_DE.md:12` beschreibt den früheren Viererblock. Das sind unterschiedliche Generationen, keine austauschbaren Aussagen. Ein neu aufgebauter Router wird durch das bloße Erzeugen des GICO-Dialogs nicht auf sechs umgestellt: GICO baut/validiert nur seinen eigenen Entwurf (`build_gico_port_config_ui.py:315`). Der aktuelle Hardware-/Livevertrag muss anhand des Hauptaudit-Snapshots bestätigt werden, nicht aus einer Dokumentüberschrift.

### Ergänzung: gelesener Live-Snapshot des Hauptaudits

Der vom Hauptaudit erfasste und hier lokal gelesene `live-baseline.json` bestätigt die **installierte Sechserkonfiguration**: WS start0, reserved24, 60 FPS, Brightness0,7, Enabled1; Sender dagegen disabled, Controllerliste leer, send_count/packet_count jeweils0 (`live-baseline.json:9740`, `:9895`). „Enabled1“ ist somit keine aktuell sendende Ausgabe.

Port 1–3 entsprechen den Sechserblöcken oben. **Port 4 ist inzwischen zugeordnet:** source1284, count896, destination3060, also Quelle1284–2179 und Ziel3060–3955 (`live-baseline.json:9741`, `:9415`). Der Entwurfsdefault „Quelle leer“ ist nicht der aktuelle Zustand. WS routet damit 2080 Quellpixel in 4080 reservierte Zielplätze. Die zusätzlich vorhandene, deaktivierte APA-Route Quelle1187–2353 überlappt Quelle1284–2179; das Routermodell erlaubt dieses Fan-out als Warnung. Ohne physische Prüfung wird nicht behauptet, dass diese Port4-Zuordnung falsch ist.

Dialog 7 zeigt passend OUTPUT OFF, READY/SENDER OFF und U0–U23/4080 px; damit ist die read-only Neufassung auch im geladenen Projekt nachgewiesen (`live-baseline.json:7452`, `:7546`). Router-Action-Status behauptet dagegen noch **LIVE – shared 510-byte sender: WS2812_NODE**, obwohl der Sender aus ist (`live-baseline.json:6660`): R6-02 ist hier konkret in umgekehrter Richtung bestätigt (veralteter LIVE-Text, nicht laufender Sender bei OFF-Text). Das statische „3 physical ports / U1–U9“ widerspricht zusätzlich vier belegten Ports und 24 reservierten Universen.

**G0-07 / P1 – nachgewiesene Duplikate im geladenen UI:** GICO enthält `apply1` bis `apply17` (17 sichtbare Buttons an x250/y54) und `validate1` bis `validate17` (17 sichtbare Buttons an x20/y54); Router enthält `open_gico_config1` bis `open_gico_config17`. Beleg: Inventar `live-baseline.json:8377`, `:8756`, `:9617`. Der Helper sucht exakt den angefragten Namen und prüft nach `create` nicht den tatsächlich entstandenen Namen (`build_gico_port_config_ui.py:25`); suffigierte Altinstanzen werden nicht bereinigt. Warum TD ursprünglich suffixiert hat, ist hier nicht nachgewiesen. Die Überlagerung und fehlende Idempotenzbereinigung sind aber belegt. Welcher Button einen echten Klick erhält, muss UI/Handler-Abnahme klären; kein Klickfehler wird aus dem Inventar allein erfunden. Akzeptanz: ein sichtbarer Button und ein eindeutig gebundener Handler pro Aktion nach drei Builds; tatsächliche Knotennamen werden kanonisiert, bekannte Altduplikate gezielt entfernt; echter Klick auf Validate genau ein Callback. Apply bleibt ohne neue Freigabe unberührt.

## Dialog 6 – ART-NET ROUTER

Ziel: `/project1/multi_controller_output/ui_panel`; Shortcut Strg+Umschalt+6 (`dialog_contracts.py:47`). Oberfläche 1180×720 (`build_multi_controller_output.py:884`).

### Vollständiges funktionales Inventar

| Element | Bindung / Wirkung | Validierung / Hilfe |
|---|---|---|
| WS IP, Start universe, Brightness, Enabled | Initial aus erstem Controller; Apply schreibt Tabellenzeile 1 | IP-Parser, Universe 0..32767, Helligkeit 0..1, Enabled 0/1 (`:312`) |
| APA IP, Start universe, Brightness, Enabled | Initial aus zweitem Controller; Apply schreibt Tabellenzeile 2 | Gleicher Parser; nicht anhand Controllername gebunden (`:350`, `:899`) |
| Panel | Textfeld; all/middle/upper/lower | Liste im Label, Prüfung in `_write_calibration` (`:330`) |
| Pattern | Textfeld; panel_id/rows/columns/chase | Liste im Label; kein Auswahlmenü (`:330`, `:933`) |
| Chase index | Textfeld; 0..3743 | Globale Grenze, keine panelbezogene Grenze (`:338`, `:935`) |
| APPLY SAFE DRAFT | `apply_safe` | Schreibt Felder, baut Router neu, liest anschließend Validation (`:348`) |
| START ENABLED | `start_enabled` | Stop → Apply → Live-Modus → Sender starten (`:377`) |
| ALL OUTPUTS OFF | `all_off` | Native Ausgänge deaktivieren und Shared Sender stoppen (`:369`) |
| START CALIBRATION | `start_calibration` | Stop → Kalibrierung prüfen → Apply → Muster packen/starten (`:392`) |
| NEXT PANEL / NEXT PATTERN | `_cycle` → `start_calibration` | Nicht bloße Auswahl: startet Ausgabe (`:415`) |
| RETURN TO LIVE | `start_enabled` | Stoppt, übernimmt aktuelle Felder erneut und startet – kein reiner Moduswechsel (`:942`) |
| GICO PORT CONFIG | Viewer öffnen | Navigation, angelegt vom GICO-Builder (`build_gico_port_config_ui.py:304`) |
| Status/Hinweise | Titel, Safety, Signalfluss, Controller-Titel, Firmwarehinweis, Advanced, Action Status, Startwarnung, Unassigned, Kalibrierhilfe | Fast alle statisch; nur Action Status wird vom Handler aktualisiert (`:307`, `:892`) |
| Erweiterte Parameter | `controller_config`, `segment_config`, `calibration_config` | NIC, UDP-Port, Rate, Farbreihenfolge, ArtSync, Reverse, Bereiche nur als Tabellen; kein vollständiger nichttechnischer Editor (`:907`) |

Sieben Aktionsbuttons sind auf aktive Panel-Execute-Handler mit `state/offToOn` verdrahtet (`:909`, `:938`). Das beweist den Quellvertrag, nicht echte Mausbedienbarkeit im geladenen Projekt. Feldbezogene i-Hilfe, Werteherkunft und Statusalter sind im Builder nicht implementiert; vorhandene Hilfe besteht aus Beschriftungen und statischen Texten.

### Konkrete Defekte und priorisierte Verbesserungen

| ID / Priorität | Befund und Evidenz | Akzeptanzkriterium |
|---|---|---|
| R6-01 / P0 | **Apply ist nicht atomar und stoppt bei späterem Eingabefehler nicht.** `_write(1,'ws')` ändert die echte Routertabelle, bevor APA und Kalibrierung geprüft werden; der Stop im Builder wird dann gar nicht erreicht. Exceptionpfad schreibt nur BLOCKED (`:348–367`, Stop erst `:733`). In-Memory-Reproduktion: gültige neue WS-IP + ungültige APA-IP → `False`, WS-IP/Universe/Helligkeit/Enabled trotzdem geändert. Der Sender liest Controllerzeilen pro Tick (`:660`): im Livebetrieb können Teiländerungen wirksam werden. | Alle Felder zunächst in separatem Modell parsen und gesamte Konfiguration validieren. Bei Fehler keinerlei Routermutation; für Safe Apply definierter Stop vor Commit. Fault-injection für jedes spätere Feld, Tabellen-/Sendervergleich und Rollback bei Builderfehler. |
| R6-02 / P1 | **Status und Mappinghilfe bleiben veraltet.** Safety behauptet OFF unabhängig vom Sender; WS-Titel U1–U9, Firmwaretext quarantänisiert 510–516 und nennt Zielstarts 510/1020 (`:893`, `:895`, `:906`), obwohl selbst Defaultsegmente 517 Pixel Mitte und Starts 680/1360 haben. `controller_summary` setzt Enabled=0 und SAFE statisch (`:780`). | Safety/Port-/Universe-/Unassigned-Angaben aus einer gemeinsamen Liveprojektion; OFF/LIVE/CALIBRATION/ERROR in derselben Quelle; keine alten Quarantänetexte; Test für Vierer- und Sechserblöcke. |
| R6-03 / P1 | **Rate ist nicht pro Controller wirksam.** Tick drosselt auf Maximum aller Raten und sendet jeden Controller (`:667`, `:676`). 60/30-Konfiguration sendet beide mit gemeinsamem Takt; Einzelwerte in Dialog 7 wirken dagegen unabhängig. | Entweder explizite gemeinsame Rate mit Validierung oder getrennte Due-Times/Telemetrie; Fakeclock-Test 60/30 belegt Verhältnis 2:1. |
| R6-04 / P1 | **ArtSync ist ein wirkungsloser freier Konfigurationswert im aktiven Sender.** Native DMX-Operatoren erhalten ArtSync, der aktive Shared-Sender erzeugt im Tick nur ArtDMX und liest kein ArtSync-Sendeflag (`:486`, `:675–684`; native Einstellung `:831`). Bei ArtSync=1 kann die Zusammenfassung trotzdem ON melden. | ArtSync ausdrücklich als nicht unterstützt sperren/anzeigen oder implementieren und Offlinepakettest pro Framezyklus ergänzen. Nicht bei aktuell OFF als beobachtete Hardwarestörung darstellen. |
| R6-05 / P2 | **RETURN TO LIVE und NEXT-Aktionen haben größere Nebenwirkungen als ihre Namen erkennen lassen.** RETURN übernimmt unbestätigte Felder über Apply; NEXT startet Kalibrierung (`:415`, `:942`). | Auswahl und Start trennen oder klare Sende-/Apply-Beschriftung; Test „nach Feldänderung Return“ dokumentiert genau erwartete Übernahme und Senderwirkung. |
| R6-06 / P2 | **Editor ist positionsgebunden, nicht controlleridentitätsgebunden.** WS/APA verwenden Indizes 0/1 und Zeilen 1/2 (`:350`, `:899`). Tabellenreihenfolge ist laut Modell nicht fest an Namen gekoppelt. | Zeilen nach stabiler Controller-ID auflösen; umgekehrte Reihenfolge und dritter Controller korrekt/erkennbar behandeln. |

Optimierung: vorhandene tatsächliche Sende-FPS, Packzeit, Paketanzahl und Fehler aus `status().telemetry` anzeigen, getrennt von konfigurierten FPS; letzte erfolgreiche Sendung und Snapshotalter ergänzen. Der alte Befund „Telemetrie fehlt vollständig“ ist überholt; es fehlt die nutzbare Darstellung.

## Dialog 7 – OUTPUT CONFIG

Ziel: `/project1/pixelblaze_mapper/output_config/ui_panel`; Shortcut Strg+Umschalt+7. Einzige Bearbeitungsautorität bleibt Router. Aktuelle Implementierung: `build_phase2_output_ui.py`, Projektion `output_config_summary.py`.

### Vollständiges Inventar und Zustandsfluss

| Element | Quelle / Bindung | Befund |
|---|---|---|
| READ ONLY notice und Source note | Statische Rollen-/Herkunftshinweise | Korrekte Abgrenzung, keine Draft-/Apply-/Revert-Funktion (`build_phase2_output_ui.py:150`, `:172`) |
| OUTPUT STATE | Sendererror/Validationerror → BLOCKED, sonst Sender enabled → LIVE, sonst OUTPUT OFF | Robuste Unterscheidung grundsätzlich vorhanden (`output_config_summary.py:82`) |
| LIVE SOURCE | `/project1/math1.numSamples` | Keine alte 3714-Konstante (`build_phase2_output_ui.py:104`) |
| SENDER | `sender.module.status()` → ON/OFF plus Modus | Fehlende/fehlerhafte Senderquelle erzeugt Fehlerstatus (`:89`) |
| CONTROLLERS | Live controller/segment rows plus aktive Sendernamen | Ziel, NIC, Port, Universen, Kapazität, Order, Rate, Brightness, ArtSync (`output_config_summary.py:170`) |
| VALIDATION | Routervalidation | Nur Zahl von Fehlern/Warnungen, nicht deren Gründe (`:179`) |
| OPEN ART-NET ROUTER | `open_router` → `openViewer` | Einziger Button; fehlendes Ziel wirft RuntimeError (`build_phase2_output_ui.py:122`, `:187`) |

Alle abgeleiteten Werte sind Text-COMPs, keine editierbaren Parameter. Builder ersetzt nur den isolierten COMP und entfernt damit alte Duplikate (`:135`). Aktualisierung über Execute DAT alle 15 Timelineframes plus 0,25-s-Zeitdrossel (`:98`, `:182`), initial erzwungen (`:213`).

### Defekte / Verbesserungen

| ID / Priorität | Befund und Evidenz | Akzeptanzkriterium |
|---|---|---|
| O7-01 / P1 | **Universe-Zählweise ist unbeschriftet und kann dem Wireverkehr widersprechen.** Projektion zeigt `start_universe` unverändert (`output_config_summary.py:118`), Sender subtrahiert für WS>=1 eine Eins (`build_multi_controller_output.py:497`). GICO speichert schon Wirebasis. Derselbe Text „U…“ bezeichnet damit nicht verlässlich UI oder Wire. | Getrennte explizite UI- und Wire-Spalten aus kanonischem Konverter; Startwerte 0/1/2/7 plus Sechserblöcke testen. |
| O7-02 / P2 | **Kapazität sieht wie tatsächliche Pixelbelegung aus.** Ausgabe „N px“ zeigt reservierte Kapazität (`output_config_summary.py:117`, `:172`). Bei sechs Universen × vier Ports wären das 4080 px, nicht die zugeordneten 1184 Seiten-LEDs. | Getrennt „Quelle“, „geroutet“, „reservierte Kapazität“, „unbelegt“; Beispiel 1184/4080 eindeutig beschriftet. |
| O7-03 / P2 | **Validierungsgründe werden verborgen.** Modell sammelt Fehlermeldungen, `display_rows` gibt nur deren Anzahl aus (`:137`, `:179`); keine Diagnoseverlinkung zur konkreten Tabellenzeile. | Erste relevante Meldung + aufklappbare Liste mit Feld/Controller und Navigation; vollständig in mehreren Fehler-/Warnfällen prüfen. |
| O7-04 / P2 | **Aktualitätsvertrag fehlt.** Framegebundene Aktualisierung und kein sichtbarer Zeitstempel können bei pausierter/anders laufender Timeline eine alte Anzeige wie Live wirken lassen (`build_phase2_output_ui.py:182`). Außerdem werden `ROUTER`/`OWNER` einmalig gebunden (`:76`); Neuaufbau während offener Anzeige ist nicht abgesichert. Dies ist ein zu prüfender Laufzeitrisikofall, kein hier reproduzierter TD-Fehler. | Monotone, von Timelineposition unabhängige Aktualisierung, Snapshotalter/STALE; Tests Pause, 30/60 FPS, Loop, Router neu erstellt/fehlt. |
| O7-05 / P2 | **Konfigurierte Werte erscheinen als Betriebswerte.** fps und ArtSync sind Tabellenwerte, nicht tatsächlicher Durchsatz bzw. nachgewiesenes ArtSync; bestehende Telemetrie wird verworfen (`output_config_summary.py:132`, `:170`). | „Soll-FPS“ / „Ist-FPS“, tatsächlicher Modus und Supportstatus getrennt, keine ON-Behauptung für unwirksame Funktion. |

Kein erneuter zweiter Outputeditor erforderlich. Der jetzige read-only Rollenvertrag ist eine wesentliche Verbesserung gegenüber dem August-Mockup. Kontext-Hilfe beschränkt sich auf globale Herkunft und Rollenhinweise; keine Erklärung für reserved pixels, Universebasis oder BLOCKED+SENDER ON.

## Dialog 0 – GICO PORT CONFIG

Ziel: `/project1/multi_controller_output/gico_port_config/ui_panel`; Shortcut Strg+Umschalt+0; zusätzlich Routerbutton. Builder 1180×720 (`build_gico_port_config_ui.py:269`).

### Vollständiges Inventar

| Element | Bindung / Bedeutung | Grenzen / Rückmeldung |
|---|---|---|
| UNIVERSES PER PORT | Globales Textfeld → Integer | Positiv, bestimmt alle vier Kapazitäten; keine Art-Net-Gesamtgrenze im GICO-Modell |
| FIRST UI UNIVERSE | Textfeld → Integer | Positiv, one-based; Apply schreibt minus 1 |
| Port 1–4 Label | Text → Segmentname nach Uppercase/Leerzeichenersatz | Keine Routingwirkung vor Apply |
| Port 1–4 Enabled | Text → `bool(int(...))` | Fälschlich jedes nichtnull Integer akzeptiert |
| Port 1–4 Source Start | Optionaler Integer; leer/none/null → None | Keine obere Quellgrenze im Modell |
| Port 1–4 Pixels | Integer | 0..universes_per_port×170; 0 erzeugt keine Route |
| Port 1–4 Reverse | Text → `bool(int(...))` | Gleiches Flagproblem wie Enabled |
| Port 1–4 Order | Text, uppercased | Sechs RGB-Permutationen |
| Port 1–4 Derived block | UI-U-Intervall, Zielstart, Kapazität, Quellintervall | Nur bei Validate neu berechnet; deaktiviert/0 Pixel nicht ausdrücklich „nicht geroutet“ |
| VALIDATE DRAFT | `_draft` → `build_gico_plan` → settings/ports schreiben | Keine Router-/Senderänderung; Warnungen im Status |
| APPLY SAFE DRAFT | Stop → Validate → Controller/Segmente ändern → Routerbuilder | Stoppt Ausgabe; startet sie nicht; kein Revert/Rollback |
| Help + Status | Globaler Constraint, leere Quelle; READY/VALID/BLOCKED/APPLIED | Kein Live-Diff, keine fieldbezogenen Fehlermarker, keine kontextuelle Hilfe |

Quellen: Parsing `:130`, Validierung/Derived `:162`, Apply `:196`, sämtliche Felder/Buttons `:276–301`. Settings und ports persistieren als eigene DATs; Feldänderungen haben keinen automatischen Validation-/Dirty-Handler. Ein grünes VALID DRAFT und alte Derived-Werte können deshalb nach weiterer Bearbeitung sichtbar bleiben.

### Defekte / Verbesserungen

| ID / Priorität | Befund und Evidenz | Akzeptanzkriterium |
|---|---|---|
| G0-01 / P0 | **Doppelte one-/zero-based-Umrechnung.** Apply speichert `first_universe-1` (`:206`), Sender zieht für WS-Werte>=1 erneut 1 ab (`build_multi_controller_output.py:497`). Bei UI1 entsteht korrekt Wire0; UI2 ergibt Wire0 statt1, UI7 ergibt Wire5 statt6. | Routermodell konsequent Wire-zero-based; einzige UI-Konversion an Grenze. End-to-end Offline-Test vom Textfeld über Routermodell bis ArtDMX-Header für UI1,2,7 und oberes Ende. |
| G0-02 / P1 | **VALID DRAFT kann außerhalb der Quelle/Art-Net-Grenze liegen; Apply kann dennoch Erfolg melden.** Modell prüft keine Source-Ende- oder Max-Universe-Grenze (`gico_port_config.py:137`, `:220`). Probe source_start=99999,count=1: nicht blockierend. Apply verändert Tabellen; Hauptbuilder gibt bei Routervalidationfehler regulär zurück (`build_multi_controller_output.py:792`); GICO zeigt danach unconditionally APPLIED SAFELY (`build_gico_port_config_ui.py:232`). | Gesamten resultierenden Router vor Commit validieren; kein APPLIED bei Routererrors; alle Tabellen atomar behalten/rollbacken. Quellenende 3744/3745, Universe-Overflow und Builderfehler als Verhaltenstest. |
| G0-03 / P1 | **Enabled/Reverse-Fehleingaben werden still als wahr akzeptiert.** `bool(int())` normalisiert 2 und -1 zu True (`:136`, `:139`), bevor der strenge Modellvalidator sie sehen kann. Im Speicher reproduziert. | Echte Toggles oder Parser nur 0/1; 2,-1,leer,Text blockieren mit Feld/Portangabe; keine Draft-/Routermutation. |
| G0-04 / P1 | **GICO-Draft und aktuelle Routerkonfiguration sind unverbundene Zustände ohne Diff.** Neue GICO-DATs starten bei sechs, Routerdefault bei vier; bestehende Routeränderungen werden nicht zurückgelesen (`:254–265`, `multi_controller.py:417`). Apply ersetzt sämtliche WS-Segmente (`:209–226`), nicht nur veränderte Portfelder. | Explicit „Draft vs live“, Versions-/Konfliktcheck, Übernahme aus Router wo eindeutig möglich; Mappingänderungen und entfallende Segmente vor Apply zeigen. Keine stillschweigende Hardwareumstellung. |
| G0-05 / P2 | **Derived/VALID-Status altert nach Feldänderung; deaktivierte Ports sehen weiter zugewiesen aus.** Keine Edit-Callbacks; Derived prüft nur Quellzuweisung, nicht `routable` (`:169`). | Bei jeder Feldänderung DIRTY, Apply neuvalidiert; Derived unterscheidet disabled/source missing/zero pixels/routed. Revert setzt letzten bestätigten Entwurf zurück. |
| G0-06 / P2 | **Stopfehler sind außerhalb des Apply-try.** `_stop_output()` steht vor dem try; falls `set_enabled(False)` und Fallback `stop()` scheitern, keine sichtbare BLOCKED-Rückmeldung und native Stopps werden evtl. nicht erreicht (`:183`, `:197`, `:202`). | Best-effort alle Ausgänge stoppen, Fehler aggregieren, niemals Commit wenn Stop nicht bestätigt; Mocksender mit Ausnahmen auf beiden Methoden. |

Die positive Eigenschaft bleibt: ein leerer Source Start für Port 4 wird nicht erfunden, nicht geroutet und als Warnung ausgewiesen. Enabled ist dabei nicht gleich „routable“. Diese Unterscheidung sollte sichtbar pro Port stehen.

## Ausgeführte Tests und Beweisgrenzen

Am 07.09.2026 offline mit `python -B -m unittest` ausgeführt:

- `tests.test_multi_controller`
- `tests.test_router_calibration`
- `tests.test_realtime_packer`
- `tests.test_gico_port_config`
- `tests.test_gico_port_config_ui`
- `tests.test_output_config_summary`

**56 Tests, 6,119 s, alle bestanden.** Keine Netzwerksockets, keine TD-Ausführung. Zusätzliche kurzlebige In-Memory-Probes extrahierten tatsächliche Runtime-Strings mittels AST und verwendeten ersetzte `op`-/Feld-/Statusobjekte:

| Probe | Beobachtung |
|---|---|
| Router gültige WS-Werte, danach APA-IP INVALID | `apply_safe=False`; vier WS-Zellen bereits geschrieben; BLOCKED-Meldung |
| GICO Enabled=2, Reverse=-1 | Beide werden True |
| GICO Quelle 99999, Count 1 | Plan nicht blockierend |
| Komposition GICO → WS-Sender, UI1/2/7 | Wire0/0/5 statt Soll0/1/6 |

Der umfangreiche Testpass widerlegt die Defekte nicht: Viele Builder-Tests prüfen lediglich Stringvorkommen und Kompilierbarkeit. `test_gico_port_config_ui.py:25` bezeichnet seine statische Prüfung ausdrücklich als ausreichend; sie übt keinen Apply-/Rollback-/Fehlerpfad aus. Der Modelltest mit nichtbool Flags beweist nur den Modellvalidator, nicht den verlustbehafteten UI-Parser. Output-Tests verwenden Start1 und Viererblöcke, nicht den aktuellen GICO-Durchstich (`test_output_config_summary.py:33`). Keine dieser Suiten beweist echte Maus-/Tabnavigation, Fensterfokus, Überlagerung, Farb-/Layoutqualität, Projekt-Neustart, geladene Runtimeversion oder LED-Hardwarewirkung.

## Abnahmefälle für nachfolgende Reparatur / getrennte Freigabe

| ID | Szenario | Erwartung / Sicherheitsgrenze |
|---|---|---|
| OUT-01 | Alle drei Shortcuts aus Netzwerk-/Dialog-/Textfeldfokus; Navigation 6→0,7→6 | Richtiger sichtbarer Viewer, eindeutiger Fokus, kein Sender-/Routingwechsel; echte UI separat prüfen |
| OUT-02 | GICO sechs, UI1, vier Ports inkl. leerer Port4-Quelle | 24 reservierte Universen; obige Tabelle exakt; Port4 ohne Route; kein Hardwareverkehr beim Validate |
| OUT-03 | UI2 und UI7 bis Offlinepaketheader | Erste Wireuniversen 1 bzw.6; keine zweite Subtraktion |
| OUT-04 | Ungültiger jeweils letzter Router-/GICO-Wert | BLOCKED mit Feldname; vollständiger Altzustand erhalten; kein nur teilweise angewandter Draft |
| OUT-05 | Ungültiger Source-Endbereich/Universeoverflow | Bereits Validate blockiert; Apply zeigt keinen Erfolg und behält Routertabellen |
| OUT-06 | Sechs↔vier, Live extern geändert, Dialog erneut öffnen | Konflikt und konkrete alte/neue Portblöcke sichtbar; keine implizite Übernahme |
| OUT-07 | Sender off/live/calibration/error und Validationwarning/error | Dialoge widerspruchsfrei; Soll/Ist, UI/Wire, Kapazität/Belegung unterscheidbar; Fehler lesbar |
| OUT-08 | 30/60-Hz-Controller, Fakeclock, ArtSync an/aus | Vertrag nachgewiesen oder nicht unterstützte Kombination klar blockiert |
| OUT-09 | Timelinepause/Loop/FPS-Wechsel, Router fehlt/neu gebaut | Keine eingefrorene Anzeige ohne STALE; fehlende Quelle kontrolliert dargestellt |
| OUT-10 | Beaufsichtigte Hardwaregrenzen 169/170,509/510,516/517,785/786,1183/1184 | Nur nach separater Hardwarefreigabe: Panel-ID und schwarze Reserven exakt; Softwaretest allein reicht nicht |

## Einheitliche Scores (0–10)

Bewertet wird aktuelle Quellimplementierung samt Offlineevidenz; keine fingierte neue Live-/Hardwareabnahme. 10 bedeutet vollständige, zuverlässig nachgewiesene Umsetzung. Kriterien gleich gewichtet.

| Kriterium | Dialog 6 | Dialog 7 | Dialog 0 |
|---|---:|---:|---:|
| Nutzbarkeit | 5 | 7 | 5 |
| Implementierung | 6 | 8 | 6 |
| Zuverlässigkeit | 4 | 6 | 4 |
| Wartbarkeit | 5 | 8 | 5 |
| Vollständigkeit | 6 | 6 | 6 |
| Innovation | 7 | 5 | 7 |
| **Mittel** | **5,5** | **6,7** | **5,5** |

Dialog 6: gute räumliche Kalibrierung und optimierter Packer, aber Teilmutation bei Fehlern und falsche Safety-Texte begrenzen Zuverlässigkeit. Dialog 7: einfache, angemessene Single-Authority-Projektion deutlich besser als früher, aber Diagnose, Zählweise und Aktualitätsnachweis unvollständig. Dialog 0: sinnvolles hardwarebezogenes Portmodell und explizit nicht zugeordneter Port4, jedoch fehlerhafter Übergang zum Router und fehlender atomarer Apply.

Empfohlene Reihenfolge: P0 Transaktion und Universekonverter → P1 gesamte Draftvalidierung, Livewahrheit und Parser → P2 Diagnose/Telemetrie/verständliche Felder → getrennte UI-, Persistenz- und beaufsichtigte Hardwareabnahme. Dieser Audit implementiert nichts davon.
