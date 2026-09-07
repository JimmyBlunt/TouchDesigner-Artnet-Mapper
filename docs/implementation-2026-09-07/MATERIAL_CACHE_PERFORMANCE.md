# Material-Runtime: gemessener Engpass und begrenzter Cache-Patch

Stand 2026-09-07. Zusätzliche Diagnose nach dem P0/P1-Live-Build, ergänzt um kurze Read-only-Nachmessungen nach Cache- und Preview-Freeze-Installation. Die Fensterbestückung war nicht über alle Stichproben identisch; keine isolierte Gesamtbeschleunigung behauptet.

## Read-only-Live-Messung

Vier feste Operatorabfragen über die vorhandene lokale TD-API, jeweils etwa drei Sekunden Abstand. Kein `.module`-Zugriff auf den Bibliotheks-Runtime durch den Messcode, keine rekursive Operatorsuche, kein Cook/Parameter-/UI-Schreibaufruf.

| Unix-Zeit | Library Runtime totalCooks | zuletzt gemeldete CPU-Cookzeit ms | Live Preview totalCooks |
| ---: | ---: | ---: | ---: |
| 1788755326.444 | 175 | 1189.52 | 176053 |
| 1788755329.551 | 176 | 1081.51 | 176077 |
| 1788755332.668 | 177 | 1148.17 | 176099 |
| 1788755335.768 | 178 | 1136.00 | 176123 |

In 9,324 Sekunden drei weitere Library-Runtime-Cooks mit jeweils rund 1,1 Sekunden zuletzt gemeldeter CPU-Zeit; Live Preview 70 weitere Cooks, etwa **7,51 Cooks/s**. Gradient/Res1 ebenfalls +70, Math1 +73. `material_state_runtime.totalCooks` konstant 19 und `material_state_table.totalCooks` konstant 11. Der neue kontinuierliche Phasecode ist damit in dieser Stichprobe **nicht** als wiederholter Text-DAT-Neuladeengpass belegt.

Diese Werte sind Operator-Cookraten, keine ArtNet-FPS und kein sauber isolierter Gesamtsystembenchmark. Der sichtbare Browser stand inzwischen auf einer anderen Materialgruppe/Thumbnailbestückung als beim früheren Audit. Timeline-/absTime-Frames können bei ausgelassenen Echtzeitframes nicht mit tatsächlich gekochten Materialframes gleichgesetzt werden. GPU-Zeitwerte sind Momentaufnahmen, kein vollständiges GPU-Profil.

## Nachvollziehbare Ursache und Patch

Vor dem Patch lief bei Initialisierung des Bibliotheks-Text-DAT-Moduls ein uneingeschränktes `refresh(reset_page=False)`: Katalog lesen, 638 Einträge normalisieren, pro Eintrag lokale Importpfade prüfen und anschließend 32 Karten rendern. Zusätzlich wurden Adaptermodule neu geladen und persistierter Parameterzustand erneut eingelesen. Die Player-Statusanzeige griff alle 15 Frames auf `library.module._items` zu. Ein vermeintlich einfacher Namenslookup stellte so eine Abhängigkeit zum teuren Bibliotheks-Runtime her.

Begrenzt geändert in `build_material_library_browser.py` und `build_unified_material_browser.py`:

- Normalisierte Einträge und gefilterte Identitätslisten liegen in OWNER-Storage; Modulneuerstellung stellt diese Referenzen ohne Thumbnail-Render wieder her.
- Katalogdatei-/Importwurzel-Stamps und freigegebene Pfade invalidieren den Library-Cache; der Unified-Cache prüft Manifest, Katalog und Importwurzel. Explizites Refresh/Import aktualisiert die Daten. Änderungen innerhalb bestehender Importpakete bleiben zusätzlich durch die vorhandenen Source-/Include-Stamps im Parameterkontext abgesichert; ein externer Metadatenwechsel kann weiterhin ein ausdrückliches Refresh erfordern.
- Parameter-/Hover-Kontextcaches überleben Modulneuerstellung. Bestehende differenzierte Source-/Include-Prüfungen wurden nicht entfernt.
- Ein gültiger in OWNER gespeicherter Parameterstore wird nicht bei jedem Modulneuladen aus seiner eigenen DAT wieder aufgebaut.
- Erfolgreiches Aktivieren speichert `active_label` zusammen mit `active_label_id`. Ältere Projekte bekommen den Namen anhand der tatsächlich veröffentlichten active/live-ID aus dem einmal geladenen Katalog; nicht anhand einer bloßen Browserauswahl.
- Player-Status liest nur Tabelle und gespeicherten Namensindex. Kein Bibliotheks-`.module`-Zugriff im Statuspfad.

Nicht geändert: Navigations-/Buttoncallbacks, Sender, Shaderlook, Intensität/Gradient, Phaseintegration oder `imported.cook(force=True)`. Die Stichprobe beweist keinen doppelten Imported-Cook pro tatsächlich berechnetem Materialframe. Force-Cook ohne gezielte Animationsprüfung zu entfernen wäre deshalb nicht ausreichend begründet.

## Abnahme und verbleibende Risiken

52 passende Offline-Tests bestanden: fünf neue Cache-/Label-Verhaltenstests, 15 Library-Vertragstests, 16 Unified-Vertragstests, acht eingebettete P1-Verhaltenstests und acht Player-Regressionsverträge. Ein Teil dieser Tests prüft weiterhin Quelltext/Bindungsverträge; das ersetzt keine Mausprüfung.

Erforderliche Live-Abnahme durch den Hauptauftrag: gleiche Materialgruppe und Fensterbestückung, 20–30 Sekunden Operator-Cookraten vor/nach Patch, Library-Runtime-CPU-Cookzeiten, korrektes aktives Label bei Core/Import/Legacy-Restore, explizites Refresh nach geändertem Import, native Parameter nach Include-Änderung sowie echte NEXT/PREV-/Kartenauswahl. Separate noch beobachtete Buttonprobleme dürfen nicht durch eine reine Cachebeschleunigung als behoben gelten.

Der Cache ist ein Performanceindex, keine neue Autorisierung für Shaderpfade. Vor Verwendung eines Materials bleiben die bestehenden Validierungs-/Compilegrenzen maßgeblich. Er darf nicht genutzt werden, um bewusst neu gesetzte Approvedroots oder den geprüften Importpfad zu umgehen.

## Nachmessung des Cache-Patches

Nach Installation: 9,381 Sekunden (Unix 1788755606,270–1788755615,651), Library geöffnet und Unified-Browser geschlossen. Library Runtime blieb bei **274 Cooks**, Unified Runtime bei 5, State Runtime bei 22 und State Table bei 12. Die noch angezeigten rund 1125 ms Library-CPU-Zeit waren damit ein alter Installations-Cook, kein fortdauernder Engpass. Live/Gradient/Res1 jeweils +136 (**14,50 Cooks/s**), Math1 +147 (**15,67 Cooks/s**). Die Timeline lief mit ungefähr 60 Frames/s; das sind nicht 60 tatsächlich berechnete Materialbilder/s.

Der wiederholte teure Runtime-Neuladevorgang wurde in dieser Stichprobe nicht mehr beobachtet. Der Unterschied zu 7,51 Material-Cooks/s zuvor ist wegen der anderen Fensterbestückung kein isolierter Cache-Benchmark.

## Weiterer Befund: unsichtbare Vorschauen liefen weiter

Spätere kurze Stichprobe mit mehreren geöffneten Dialogen: In 5,149 Sekunden liefen **alle 25 `card_top_0` bis `card_top_24` jeweils 30-mal**, obwohl der Unified-Browser auf Seite 2 ausschließlich 21 importierte Bilder zeigte. Die versteckten Core-Karten behielten teilweise ihre Viewer-Verweise. Die Core-GLSL-Vorschauen haben zeitabhängige Uniforms; ausschließlich `display=False` beseitigte die beobachtete Berechnungsnachfrage nicht. Ein zusätzlicher per-frame Force-Cook der Core-Vorschauen ist im untersuchten Code nicht belegt.

Auch `hover_preview` und `detail_preview` liefen jeweils +30, obwohl Hover-ID und Hover-Slot leer waren und keine dieser temporären Vorschauen benötigt wurde. Die Library-/Unified-/State-Runtimes waren dabei bereits konstant. Live/Gradient/Res1 jeweils +30 (**5,83 Cooks/s**), Math1 +33, TOP-to-CHOP +41. Einzelne große zuletzt angezeigte CPU-/GPU-Werte sind ohne Cookzuwachs keine Dauerlast; insbesondere ist der GPU-Wert eines Select-TOPs kein Beweis für dessen isolierte Eigenkosten.

### Begrenzte Vorschaukorrektur

`build_unified_material_browser.py::_sync_core_preview_activity` friert off-page `preview_N` und `card_top_N` am letzten Bild über das TOP-Lock ein und entsperrt die aktuelle sichtbare Core-Auswahl. `build_material_library_browser.py::_sync_preview_activity` hält Hover/Detail nur dann animiert, wenn die veröffentlichte Auswahl und der tatsächliche Viewer-Verweis diese Vorschau brauchen. Einmalige Compile-/Validierungscooks entsperren den Kandidaten vorübergehend; Fehler stellen den vorherigen Lockzustand wieder her.

Produktionsshaderzeit, Produktions-Live-TOP, Gradient, Sender und LED-Vorschauauflösung bleiben unverändert. Der Patch betrifft die beiden Browser-Builder, nicht `effects/build_core_effects.py`. Eine Installation muss auch den aktuellen Browserzustand neu rendern, damit die Locks angewendet werden; bloßes Austauschen unaufgerufenen Quelltexts genügt nicht.

Erst vier neue Tests rot, anschließend fünf Vorschau-Verhaltenstests plus 68 Material- und 16 Unified-Tests grün (**89**). Darunter echte isolierte Helper-Ausführung mit Fake-Operatoren und Fehlerpfadprüfung; keine Behauptung, diese Tests hätten native Maus-Hover bewiesen. Der Hauptauftrag meldete anschließend die gesamte Offline-Suite mit **540 Tests in 23,815 Sekunden grün**.

### Finale Live-Abnahme: Seite 2 nach Freeze-Installation

Der Hauptauftrag öffnete Seite 2/2 durch einen echten NEXT-Klick. Bubble Rings blieb aktiv; Layout2D war ebenfalls geöffnet, Output laut Hauptauftrag OFF. Zwei feste Read-only-Abfragen im Abstand von **5,168 Sekunden**, Unix 1788758927,775–1788758932,942. Rohdaten einschließlich Locks, letzter CPU-/GPU-Zeitwerte, Browserzustand und Viewer-Verweisen: [preview-freeze-live-evidence.json](preview-freeze-live-evidence.json). Keine UI-Steuerung, kein `.module`, keine rekursive Suche und kein Cook-/Parameter-Schreibaufruf im Beobachter.

| Operatorgruppe | Zuwachs vor Freeze / 5,149 s | Zuwachs nach Freeze / 5,168 s | Nachzustand |
| --- | ---: | ---: | --- |
| 25 Core-Card-TOPs | jeweils 30 | jeweils **0** | alle locked |
| 25 zugehörige Core-GLSL-TOPs | nicht separat erfasst | jeweils **0** | alle locked |
| Inaktive Hover-/Detail-TOPs | jeweils 30 | jeweils **0** | beide locked |
| Live, Gradient, Res1 | jeweils 30 | jeweils **59** | nicht locked; 11,42 Cooks/s |
| Math1 | 33 | **64** | 12,39 Cooks/s |
| TOP-to-CHOP | 41 | **76** | 14,71 Cooks/s |
| Library-/Unified-/State-Runtime, State Table | jeweils 0 | jeweils **0** | kein wiederholtes Laden |

Alle 50 versteckten Core-TOPs und die beiden inaktiven temporären Vorschauen blieben damit nachweislich stehen, während der Produktionspfad weiterlief. Browserzustand und aktive Material-ID waren zwischen beiden finalen Samples identisch; die 21 sichtbaren Viewer zeigten ausschließlich importierte Bilder. `LedMap` und `effect_sample_uv` hatten ebenfalls keinen Cookzuwachs. Die gemessene Materialrate stieg gegenüber der vorherigen kurzen Stichprobe von 5,83 auf 11,42 Cooks/s; wegen weiterer Dialog-/Zeitpunktunterschiede wird daraus **keine isolierte Verdoppelung durch diesen Patch** abgeleitet. Weiterhin unter 60 Material-Cooks/s; kein vollständiges GPU-Profil erstellt.

Diese Messung nimmt den Ruhefall auf Seite 2 ab. Zur vollständigen interaktiven Vorschauabnahme gehören zusätzlich echte Rückkehr auf eine Core-Seite sowie Hover-Eintritt/-Austritt und Detailauswahl; sie sind nicht durch diese unbewegte Stichprobe ersetzt.
