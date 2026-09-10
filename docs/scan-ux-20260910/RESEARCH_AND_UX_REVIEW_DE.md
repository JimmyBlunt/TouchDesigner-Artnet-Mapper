# MariMapper: Recherche und UX-Bewertung

Stand: 10. September 2026. Referenz für die Ausgangsbewertung: Git `d22404935c18c7716059b9ca0781fc844560ed2d`. Dieses Dokument beschreibt Recherche, beobachtete Ausgangsprobleme und begründete Empfehlungen. Es behauptet keine gemessene Zeitersparnis, Nutzerstudie, getestete Hardwarequalität oder bereits abgeschlossene Umsetzung. Den tatsächlichen Implementierungs- und Prüfstand dokumentiert der zugehörige Änderungsbericht.

## Prüfgrundlage

Gelesen wurden `build_scan_session_ui.py`, `guided_scan_live.py`, `standalone_scan.py`, `scan_result_review.py`, `scan_session.py`, `scan_coverage.py`, `build_layout_scene_ui.py` und die deutschen Howtos vom 9. September. Der archivierte Screenshot `docs/implementation-2026-09-07/guided-scan-evidence/scan-plan-ui.png` wurde visuell geprüft. Er belegt die damalige Gestaltung, nicht die am 10. September laufende Oberfläche. Neuere Quelltexte enthalten zusätzliche Bedienelemente. Die Bewertung verbindet deshalb statische Codeprüfung und historischen visuellen Befund; eine aktuelle Laufzeitprüfung muss separat erfolgen.

## Vergleichslösungen und übertragbare Muster

| Primärquelle | Belegtes Muster | Folgerung für dieses Projekt |
|---|---|---|
| [MariMapper: Originalrepository und README](https://github.com/TheMariday/marimapper) | Kameraprüfung, Backend, Szenenvorbereitung und Aufnahme werden als aufeinanderfolgende Schritte erklärt. Eine Ansicht ergibt 2D-Daten; mehrere Ansichten ermöglichen die 3D-Rekonstruktion. Der Viewer unterscheidet rekonstruierte und interpolierte Punkte. | Aufnahme und 3D-Ergebnis sprachlich trennen. Nach jeder Ansicht einen sinnvollen nächsten Schritt anbieten. Die Herkunft eines Punktes darf nicht durch eine pauschale grüne Qualitätsanzeige verdeckt werden. |
| [MadMapper: offizieller Space Scanner Guide, insbesondere Seiten 6–8](https://madmapper.com/files/13-Space%20Scanner%20Guide-1.pdf) | Ein- und Ausgabe auswählen, Vorschau prüfen, Capture starten; das Ergebnis wird gespeichert und als Hintergrund für die weitere Arbeit eingesetzt. | Quelle, Ziel und Vorschau zusammen zeigen; nach Abschluss einen klaren Übergang ins Layout anbieten. Der Space Scanner ist ein Projektor-/Kamera-Verfahren, kein Beleg für MariMappers 3D-Registrierung. |
| [MadMapper: Online Material Library](https://docs.madmapper.com/madmapper/6/3.-media/online-material-library) | Bibliothek mit Kategorien, Favoriten und einer direkten Aktion zum Installieren und Hinzufügen ins Projekt. | Eine Scanbibliothek sollte Finden, Prüfen und Hinzufügen verbinden. Der Scanimport braucht keine manuelle Pfadpflege als primären Einstieg. Automatisches Hinzufügen zu Live ist daraus ausdrücklich nicht abzuleiten. |
| [Agisoft: Manual chunk alignment, Hersteller-Support](https://agisoft.freshdesk.com/support/solutions/articles/31000157701-manual-chunk-alignment-standard-edition-) | Projekte anhängen, enthaltene Chunks wählen, Ausrichtung im gemeinsamen Modell betrachten und erst danach zusammenführen. Aktivierung über Workspace oder Kontextmenü. | Vorhandene Scans als auswählbare Objekte darstellen. Hinzufügen, Ausrichten und Teilersatz als unterschiedliche Absichten führen; rohe Rekonstruktion nicht stillschweigend als passend behandeln. |
| [NN/G: Progressive Disclosure](https://www.nngroup.com/articles/progressive-disclosure/) | Häufige Funktionen bleiben sichtbar, seltene Details erscheinen auf Anfrage. Eine lineare Schrittfolge eignet sich schlechter, wenn Nutzer ständig zwischen abhängigen Einstellungen wechseln müssen. | Drei direkt anwählbare Arbeitsbereiche statt eines starren Assistenten. Kamera, Belichtung und Schwelle gemeinsam halten; Interpreter und Dateidetails nachrangig. |
| [NN/G: 10 Usability Heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/) | Sichtbarer Zustand, erkennbare Aktionen, Fehlerbehebung und kurze Hilfe am Ort des Problems. | Ein verständlicher Status mit nächster Aktion; Details ergänzen die Erklärung. Hilfe verweist auf konkrete Bedienhandlungen und den aktuellen Arbeitsschritt. |

Die genannten Produktbeschreibungen wurden am 10. September 2026 online abgerufen. MariMappers Hauptbranch weist auf bevorstehende inkompatible Änderungen hin. Diese Recherche ist daher keine Aufforderung zu einem unkontrollierten Paketupdate. Die installierte Integration und ihre Tests bleiben maßgeblich. Alte MadMapper-PDFs werden als Designbeispiele verwendet, nicht als Nachweis der aktuellsten Menüstruktur.

## Ausgangsbefund und Prioritäten

| Priorität | Konkreter Befund | Empfohlene Änderung | Überprüfbares Ziel |
|---|---|---|---|
| P1 | Guided Scan zeigt in `controls` 15 Aktionen für Vorbereitung, Aufnahme, 3D und Navigation gleichzeitig. Dazu kommt der Helligkeitsschieber. | Arbeitsbereiche „Vorbereiten“, „Ansichten“, „3D-Ergebnis“ mit erkennbarer aktueller Phase und kontextbezogener Hauptaktion. | Erstbesucher können den nächsten Arbeitsschritt ohne Lesen der technischen Felder benennen. Stop bleibt bei laufendem Prozess erreichbar. |
| P1 | Fünf breite Eingabereihen zeigen auch Interpreter, CSV-Pfadliste und Anker bei der einfachen Neuaufnahme. | Technische Details ein-/ausklappbar; Dateiauswahl und kompakte Ansichtsliste statt ausschließlich `|`-getrennter Pfade. | Eine neue vollständige Aufnahme erfordert keine Interpreter-Eingabe und keine manuelle CSV-Liste. |
| P1 | Vorhandene Scans sind über Dateiaktionen erreichbar; Auswahl erfolgt im Layout überwiegend über Nummern und Textfelder. | Durchsuchbare Scan-/Objektliste mit Name, LED-Anzahl, Quelle und Zustand; klare Aktionen für Hinzufügen und Teilersatz. | Einen vorhandenen Scan finden und hinzufügen, ohne seinen absoluten Dateipfad auswendig zu kennen. |
| P1 | Der Ergebnisdialog zeigt neun Transformationsfelder; das Layout bietet dieselben Transformationen. | Standardmäßig Name, Adressbereich und Ergebnis zeigen. Transformationswerte bei Bedarf aufklappen, Ausrichtung im Layout als Hauptweg erklären. | Die Erstübernahme gelingt mit Identitätstransformation; bestehende Spezialfälle bleiben möglich. |
| P1 | `open_review` schreibt vollständige fehlende ID-Liste, Bounds und Dateipfad in einen einzelnen Textblock. | Anzahl und kompakte ID-Bereiche zeigen; vollständige Herkunft und Bounds über Details. Kollisionen vor Übernahme erklären, freien globalen Startwert vorschlagen. | Lange Pfade oder große Lückenlisten verdecken die primäre Entscheidung nicht; Adresslücken bleiben erhalten. |
| P1 | Teilersatz kombiniert Scanindex, lokalen Objektindex und globale Quelladresse. Der Nutzer muss die drei Bezugssysteme auseinanderhalten. | Beim Teilersatz Zielobjekt und Zielbereich zuerst, dann Quelldatei und deren Bereich; Vorschau der Zuordnung und Registrierungsstatus. | Kein „Ersetzen“ ohne klar bezeichneten Zielbereich und passenden Koordinatenraum. |
| P2 | Englisch, deutsche Abdeckungsanzeige und technische Großbuchstaben mischen sich. | Durchgängige Aufgabenbegriffe und Satzschreibung für neue Hauptaktionen; Fachbegriffe kurz erklären. | „Ansicht“, „3D-Ergebnis“, „Entwurf“ und „Live“ haben jeweils eine Bedeutung. |
| P2 | Historischer Screenshot: beinahe identische graue Schaltflächen, sehr breite Textfelder und lange Hinweise konkurrieren um Aufmerksamkeit. | Eine akzentuierte Hauptaktion, kompakte Gruppen mit festen Abständen und sachlich zurückhaltende Detailflächen. | Primäraktion, aktiver Zustand und Fehler sind auch ohne Farbinterpretation erkennbar. |
| P2 | Technische Fehler können den Status dominieren; Wissen liegt überwiegend in externen Howtos. | Hilfe pro Phase: „Kein Kamerabild“, „LED fehlt“, „3D fehlgeschlagen“, „Scan hinzufügen oder ersetzen?“. | Jede Hilfekarte enthält wenige ausführbare Schritte und gegebenenfalls einen Link zur ausführlichen Anleitung. |

Bereits solide: Quelle und Draft werden getrennt; Rohscans besitzen Prüfsummen; doppelte Ergebnisübernahme wird verhindert; fehlende Adressen werden nicht verdichtet; Teilersatz erhält LED-Identitäten und bindet sich an eine Szenenrevision. Die Abdeckungsanzeige erklärt bereits, dass Beobachtungsanzahl keine bestätigte 3D-Qualität ist. Diese Eigenschaften sind ein guter Ausgangspunkt und müssen bei jeder UI-Vereinfachung bestehen bleiben.

## Empfohlene Abläufe

**Neue Aufnahme:** Neue Aufnahme anlegen → Kamera prüfen und LEDs festlegen → Scanplan prüfen → eine Ansicht aufnehmen → Abdeckung ansehen und Kamera umsetzen → weitere Ansicht → 3D berechnen → Ergebnis prüfen → als neues Objekt in den Entwurf → im Layout ausrichten. Der Scanstart nennt den tatsächlich betroffenen Controller-/Universumsbereich. Eine neue Ansicht darf dieselbe Aufnahmesitzung fortführen, ohne alle Felder erneut auszufüllen.

**Vorhandenes 3D-Ergebnis:** Bibliothek öffnen → Datei/Scan auswählen → Format, Anzahl, Adressbereich und Herkunft prüfen → zum Entwurf hinzufügen → Objekt ausrichten. Die Dateiquelle bleibt nachvollziehbar; ein Name darf nicht als alleinige Identität dienen.

**Teilrescan/Teilersatz:** Zielobjekt auswählen → lokaler Bereich und Vergleichsanker → passende Ansichten aufnehmen/importieren → Rekonstruktion und Registrierung prüfen → betroffene IDs vergleichen → ausdrücklich übernehmen. Automatisches Füllen unsichtbarer LEDs oder ungeprüftes Übertragen fremder Koordinatenräume wäre eine Verschlechterung. Falls die aktuelle Integration nur einen Teil dieses Ablaufs unterstützt, muss sie diese Grenze sichtbar nennen.

## Sinnvolle Innovationen

1. **Nächste sinnvolle Aktion aus dem vorhandenen Zustand ableiten.** Keine KI erforderlich: Sessionstatus, Zahl gültiger Ansichten, laufender Prozess und Ergebnisstatus reichen. Eine Empfehlung darf keine Freigabe vortäuschen und muss bei veralteten Daten erneut geprüft werden.
2. **Lücken zum Arbeitsauftrag machen.** Die ohnehin vorhandene Abdeckungsstatistik kann „IDs 12–18 noch nicht gesehen“ und „nächste Ansicht aus anderer Richtung“ anbieten. Eine spätere Auswahlfunktion könnte diese IDs markieren. Ihre automatische Übernahme in einen bereits aufgenommenen Umfang ist wegen der Sessionidentität gesondert zu gestalten.
3. **Herkunft direkt am Ergebnis.** „Rohaufnahme“, „rekonstruiert“, „manuell ausgerichtet“ und „registriert/geprüft“ sind verschiedene Aussagen. Kompakte Textkennzeichen schaffen Transparenz; Details enthalten Datei, Hash und Session.
4. **Adresskonflikte vorwegnehmen.** Ein freier globaler Startwert als überprüfbarer Vorschlag spart Rechenarbeit. Originale Scan-IDs und Lücken bleiben erhalten; ein Vorschlag ist keine automatische Neuadressierung vorhandener Objekte.

Diese Ideen sind eigene Ableitungen aus den Quellen und dem lokalen Datenmodell. Sie sind keine Behauptung, dass ein Vergleichsprodukt dieselben Funktionen bereitstellt.

## Bewertung nach der Implementierung

Die folgenden Prüfungen sind vorgesehen, nicht in diesem Forschungsdokument als bestanden behauptet:

| Perspektive | Prüfszenario / Kriterium |
|---|---|
| Bedienbarkeit | Neuaufnahme beginnen, zweite Ansicht ergänzen, existierende CSV importieren, Ergebnis hinzufügen und per Undo zurücknehmen. Nicht benötigte Felder müssen dabei verborgen bleiben können. |
| UI-Design | Aktuelle Screenshots aller Bereiche bei üblicher Fenstergröße: keine Überlagerungen, abgeschnittenen Hauptaktionen oder unlesbaren Statuszeilen. Tastaturfokus und Fehlermeldungen prüfen. |
| Benutzererlebnis | Ohne externe Hilfe erklären können: Was ist gespeichert? Was ist nur Entwurf? Was folgt als Nächstes? Wurde Live geändert? |
| Innovation | Kontextempfehlung ändert sich nachvollziehbar mit den echten Daten; fehlende Messpunkte werden nicht als Rekonstruktion ausgegeben. |
| Datenintegrität | Doppelte/ungültige Ansichten, Pfadänderung nach Review, Adresskollision, Nullpunkt als gültige Geometrie, Lücken sowie veraltete Szenenrevision testen. |
| Nachvollziehbarkeit | Geänderte Quelldateien, Tests, Bildschirmbelege, bekannte Grenzen und Git-Commit im Änderungsbericht aufführen. |

Für eine spätere vergleichende Nutzungsstudie: dieselben Aufgaben vor/nach der Änderung, benötigte Hilferufe, Fehlversuche und tatsächliche Abschlusszeit protokollieren. Ohne solche Daten sind Prozentangaben zur Effizienz oder numerische UX-Scores nicht belastbar.
