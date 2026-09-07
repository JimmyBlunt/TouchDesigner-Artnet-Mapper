# MariMapper: integrierte Voll-/Teilscan-Vorbereitung und belastbarer Ausbaupfad

Stand: 2026-09-07. Quellenprüfung, lokale Dateninventur und neue Offline-Implementierung. Keine Installation, kein Kameraöffnen, kein nativer Rekonstruktionslauf, keine LED-Ausgabe, kein Upload und kein Live-TD-Build durch diesen Teilauftrag.

**Späterer begrenzter Nachweis desselben Tages:** Der separat autorisierte native Offline-Smoke-Test ist inzwischen erfolgreich durchgeführt; Details, gefundener Integer-JSON-Fehler, 258/269 rekonstruierte IDs und ausdrücklich ausstehende geometrische Freigabe stehen in [MARIMAPPER_NATIVE_SMOKE.md](MARIMAPPER_NATIVE_SMOKE.md). Die folgenden ursprünglichen „noch nicht ausgeführt“-Angaben beschreiben den Stand vor diesem Nachtest. Kamera, Hardware-Capture und Layout-Übernahme bleiben ungeprüft/unverändert.

## Ergebnis und ehrlicher Fertigstellungsgrad

MariMapper lässt sich als separater Rekonstruktionsprozess mit einer geführten TouchDesigner-Oberfläche verbinden. Die vorhandene Installation ist nutzbar, ohne ihre nativen Bibliotheken in TouchDesigners Prozess zu importieren. Eine vollautomatische, geprüfte Aufnahme inklusive sicherer Mehrcontroller-Ausgabe ist damit **noch nicht implementiert**.

Neu vorhanden:

- `pixelblaze_mapper/scan_session.py`: unveränderliche Scan-Sitzung, stabile IDs, explizite Auswahl/Anker, Mehransichts-Nachweise, reine Testmusterbeschreibung, Review-/Merge-Gates.
- `pixelblaze_mapper/scan_worker.py`: hashgebundenes Offline-Manifest, strenger 2D-CSV-Eingang, echter Aufruf der geprüften MariMapper-`sfm()`-Funktion ausschließlich bei ausdrücklichem CLI-Flag. Standardaktion ist eine Geräte-freie Vorschau. Keine Installation oder Prozessstarts durch den Import.
- `pixelblaze_mapper/build_scan_session_ui.py`: additive Oberfläche `/project1/guided_scan/ui_panel`; Auswahl, gewünschte Kamera-ID, explizite Quellenindizes/Anker, bestehende Ansichten, Arbeitsordner und separater Python-Pfad. PREPARE schreibt nur einen Testplan in eine DAT. PREPARE OFFLINE JOB erzeugt nach Prüfung eine neue Manifestdatei und zeigt getrennte Vorschau-/Rekonstruktionsargumente. Kein automatischer Workerstart.
- `tests/test_scan_session.py`, `tests/test_scan_worker.py`: 28 bestandene reine Offline-Tests zum Zeitpunkt dieses Berichts. Kein Nachweis einer erfolgreichen realen Kameraaufnahme, SfM-Geometrie oder echten Mausbedienung der neuen Oberfläche.

ARM CAPTURE meldet ausdrücklich „nicht verfügbar“: exklusiver Routerzugriff und Kameraadapter fehlen. Die Kamera-ID ist eine Nutzeranforderung, keine Geräteerkennung. Registrierung und Geometrieprüfung dürfen weder durch ein Label noch durch einen vorhandenen Dateipfad vorgetäuscht werden.

## 1. Tatsächlicher Upstream und vorhandene lokale Umgebung

Der Name lautet **MariMapper**, offizielles Projekt `TheMariday/marimapper`. Geprüfter Commit: `7dc5f799a1b7c180573c2632f6d12a3be0cbf4fa`. Projektversion V3.4.2; Python >=3.9,<3.13. Deklarierte Abhängigkeiten umfassen NumPy, OpenCV, Open3D und exakt pycolmap 3.11.1. Die offiziellen Programme heißen `marimapper`, `marimapper_check_camera`, `marimapper_check_backend` und `marimapper_upload_mapping_to_pixelblaze`. Keine erfundene `--subset`-, Headless- oder JSON-Sitzungsoption. [Projektmetadaten](https://github.com/TheMariday/marimapper/blob/7dc5f799a1b7c180573c2632f6d12a3be0cbf4fa/pyproject.toml).

Die lokale Werkzeugumgebung existiert bereits:

| Bestandteil | Read-only-Fund |
| --- | --- |
| Isolierter Interpreter | `C:\Users\jbhtz\AppData\Roaming\uv\tools\marimapper\Scripts\python.exe` |
| Python laut pyvenv.cfg | 3.12.13 |
| MariMapper-Metadaten | 3.4.2, direct_url.json bestätigt obigen Commit |
| Installierte Paketmetadaten | NumPy 2.5.1, OpenCV 5.0.0.93, Open3D 0.19.0, pycolmap 3.11.1 |
| Vorhandene Programmstarter | `C:\Users\jbhtz\.local\bin\marimapper*.exe` |

Paketmetadaten beweisen **nicht**, dass alle nativen Module in dieser Umgebung fehlerfrei laden. Diese Prüfung und ein echter Offline-Rekonstruktionslauf wurden bewusst noch nicht ausgeführt. Der gewöhnliche Repository-Python besitzt diese Module nicht; das bedeutet nicht, dass MariMapper insgesamt fehlt. Der neue Worker prüft Paketversionen und Commit vor nativen Imports und lehnt ungeprüfte Varianten ab.

Der vom Nutzer genannte Datenpfad ohne `Desktop` existiert nicht. Tatsächlich gefunden wurde:

`C:\Users\jbhtz\OneDrive\Desktop\Pictures\Documents\~Projects~\Marrimapper-LED-Schrank`

Dort liegen Messdaten, kein lokaler Quellcode-Checkout. Keine Dateien darin verändert. 14 gefundene 3D-CSV-Dateien:

| Unterordner | Zeilen | vorhandene Indexspanne | 2D-Ansichten |
| --- | ---: | ---: | ---: |
| Wurzel | 1164 | 0–1183 | 8 |
| aLLEnEU1 | 785 | 0–1145 | 4 |
| hinten/1 | 200 | 0–202 | 6 |
| hinten/3 | 894 | 1–895 | 5 |
| hinten/3/Neuer Ordner | 872 | 1–895 | 3 |
| hinten/4 | 994 | 0–999 | 6 |
| hinten/5 | 810 | 0–809 | 4 |
| liegend | 1155 | 0–1179 | 17 |
| mitte_neu | 509 | 0–516 | 5 |
| oben_neu | 269 | 517–785 | 3 |
| stehend | 272 | 911–1182 | 3 |
| unten_neu | 367 | 789–1185 | 7 |
| untersteSeite_neu/398-1st | 368 | 0–397 | 5 |
| untersteSeite_neu/old-402 | 381 | 0–396 | 5 |

Indizes innerhalb jeder Datei eindeutig, aber häufig lückenhaft. Eine Indexspanne ist keine lückenlose Anzahl. Ordnernamen belegen keine globale Controller-/Objektzuordnung. Verschiedene Messungen können dieselben Zahlen für unterschiedliche physische Teilgruppen verwenden. Deshalb kein automatisches Zusammenhängen oder Umnummerieren anhand von Dateireihenfolge.

## 2. Formatverträge: CSV, Koordinaten-JSON und eigene Sitzung getrennt halten

MariMapper schreibt 2D-Beobachtungen als `index,u,v`, rekonstruierte 3D-Daten als `index,x,y,z,xn,yn,zn,error`, nach LED-Index sortiert. Ansichten werden beim Lesen über sortierte Dateinamen nummeriert. Der Writer verwendet für 3D wiederholt `led_map_3d.csv`; deshalb native Arbeit immer in einen neuen Ergebnisordner lenken, nie in die Originalmessung. [Dateiformate](https://github.com/TheMariday/marimapper/blob/7dc5f799a1b7c180573c2632f6d12a3be0cbf4fa/marimapper/file_tools.py), [Dateiprozess](https://github.com/TheMariday/marimapper/blob/7dc5f799a1b7c180573c2632f6d12a3be0cbf4fa/marimapper/file_writer_process.py).

| Format | Bedeutung / Vertrag |
| --- | --- |
| `index,u,v` CSV | Eine Kameraperspektive, Beobachtungsindex explizit; keine XYZ-Koordinaten |
| `index,x,y,z,xn,yn,zn,error` CSV | Messresultat mit Rohkoordinaten, Normale/Fehler; fehlende Zeilen nicht verdichten |
| Lokal `Exported/AllExported.json` | Verifiziertes schlichtes Array mit 3714 XYZ-Dreiergruppen, keine Wrapperstruktur, keine Nulltripel; zulässiger Koordinatenimport, **kein belegtes natives MariMapper-Sitzungsformat** |
| `pixelblaze-layout-scene`, Version 1 | Eigenes Scene-/Objekt-/Scan-/Identitätsschema des Mappers |
| `pixelblaze-scan-session`, Version 1 | Eigenes Sitzungs-/Provenienz-/Auswahlschema |
| `pixelblaze-marimapper-offline-worker`, Version 1 | Eigene Worker-Auftragsdatei, enthält geprüften Upstream-Commit, Eingabepfade/-Hashes und erlaubte Fähigkeiten |

Unbekannte JSON-Wrapper werden nicht erraten. Ein `[0,0,0]`-Punkt kann ein echter Ursprung sein; fehlende Messung benötigt ein eigenes Missing-Merkmal. Der aktuelle Layout-Importer archiviert Rohdaten und explizite Missing-Indizes. Normale und `error` müssen in Metadaten erhalten bleiben; nach Transformation benötigen Normalen eine eigene korrekte Behandlung. CSV allein enthält keinen zuverlässigen „gemessen versus interpoliert“-Beleg.

Für den neuen Worker bedeutet CSV-`index` ausdrücklich **source_index der gestagten Szene**. Native dateilokale Indizes dürfen nur mit einer vorher geprüften Zuordnung übersetzt werden. Nicht passende IDs führen zum Fehler, nicht zu einer stillen Bereichsausweitung. Ein Teilscan darf vorhandene Vollansichten nicht einfach als seine eigenen ausgeben: entweder bewusst eine neue, provenancegebundene Teilansicht erzeugen oder alle beobachteten Kontext-LEDs als ausdrückliche Anker deklarieren. Der aktuelle Wrapper filtert nicht heimlich.

## 3. Was MariMapper tatsächlich tut und warum der Scanner nicht in TD gehört

Der Scanner-Konstruktor startet mehrere Prozesse; er ist keine passive Konfiguration. Die Scanner-CLI besitzt einen zusammenhängenden `start`-/`end`-Bereich und interaktive Scanentscheidungen. Eine beliebige Menge einzelner LED-IDs ist kein belegter öffentlicher CLI-Vertrag. Deshalb importiert der neue Worker nur gezielt LED-Datentypen, SfM und CSV-Writer, niemals `Scanner`, Kamera oder Backend. [Scanner](https://github.com/TheMariday/marimapper/blob/7dc5f799a1b7c180573c2632f6d12a3be0cbf4fa/marimapper/scanner.py), [Argumente](https://github.com/TheMariday/marimapper/blob/7dc5f799a1b7c180573c2632f6d12a3be0cbf4fa/marimapper/scripts/arg_tools.py).

Die Erkennung beleuchtet LEDs einzeln, wartet auf Dunkelheit und bestimmt einen hellen Konturmittelpunkt. Die Bildkoordinaten sind nicht schlicht `(x/width,y/height)`: `u=x/width`, `v=(y+(width-height)/2)/width`. Diese Konvention muss ein eigener Kameraadapter exakt einhalten. Kamerazustände wie Belichtung, Autofokus und Gain werden beeinflusst. [Detektor](https://github.com/TheMariday/marimapper/blob/7dc5f799a1b7c180573c2632f6d12a3be0cbf4fa/marimapper/detector.py), [Kamera](https://github.com/TheMariday/marimapper/blob/7dc5f799a1b7c180573c2632f6d12a3be0cbf4fa/marimapper/camera.py).

Korrespondenzen werden über dieselbe beleuchtete LED-ID zwischen Ansichten gebildet. `sfm()` ruft pycolmap auf, benötigt mehr als eine Ansicht und verwendet unter anderem 50 initiale Inlier als Einstellung. Zwei vorhandene CSV-Dateien oder zwei sichtbare Punkte garantieren deshalb keine erfolgreiche Rekonstruktion. Der neue Sitzungsautomat prüft nur notwendige Vorbedingungen. [Datenbankaufbau](https://github.com/TheMariday/marimapper/blob/7dc5f799a1b7c180573c2632f6d12a3be0cbf4fa/marimapper/database_populator.py), [SfM](https://github.com/TheMariday/marimapper/blob/7dc5f799a1b7c180573c2632f6d12a3be0cbf4fa/marimapper/sfm.py).

Die reguläre Prozesskette skaliert, füllt Lücken, zentriert und schätzt Normalen. Automatische Lückenfüllung anhand benachbarter Indizes ist für unabhängige Objekte gefährlich. Der neue Offline-Worker verwendet bewusst nur die eigentliche SfM-Funktion: keine Interpolation, kein Rescale/Recenter, keine Normalenschätzung, keine Registrierung. Seine CSV-Normalen sind somit nicht als berechnet auszugeben. Resultate haben einen beliebigen SfM-Koordinatenrahmen. [SfM-Prozess](https://github.com/TheMariday/marimapper/blob/7dc5f799a1b7c180573c2632f6d12a3be0cbf4fa/marimapper/sfm_process.py), [LED-Hilfsfunktionen](https://github.com/TheMariday/marimapper/blob/7dc5f799a1b7c180573c2632f6d12a3be0cbf4fa/marimapper/led.py).

## 4. Sicherer Zielablauf und Implementierungsgrenzen

| Phase | Vorhanden | Noch erforderlich |
| --- | --- | --- |
| Objekt/Bereich wählen | Scene-IDs, explizite Source-Indizes, getrennte Anker, Revisionshash | 3D-Flächenauswahl mit komfortabler Auswahlvorschau |
| Plan vorbereiten | Reine Musterliste, maximal 10% vorgeschlagene Helligkeit, gewählte Kamera-ID | Kamerainventur ohne impliziten Aufnahmestart, routingspezifische Leistungsgrenzen |
| Aufnahme scharf schalten | Ehrliche Sperre statt vorgetäuschtem Erfolg | Bestätigter exklusiver Output-Lease, Routing-/Kamera-Preflight, Not-Aus |
| Ansichten aufnehmen | Bestehende CSVs anhängen und deren IDs prüfen | Frame-Acknowledgements, Dunkelreferenz, Bewegungsprüfung, Mehransichtsführung |
| Offline rekonstruieren | Separater expliziter CLI-Aufruf echter SfM-Funktion | Nativer Smoke-Test, Jobüberwachung/Cancel und Fortschritt im TD-Dialog |
| Registrieren/verifizieren | Pflichtreferenzen und gestagtes Candidate-Protokoll | Verifiziertes Fit-Verfahren, Residuen, Geometrie-/Ankerabdeckung, Review-UI |
| Teilmenge übernehmen | MergeRequest erhält Identitäten und prüft Szenenrevision | Menschliche Review-Entscheidung, Verbraucher prüft Registrierung tatsächlich |

Eine neue Sitzung bearbeitet genau einen ursprünglichen Objektkoordinatenrahmen. „Full“ bedeutet aktuell vollständiges gewähltes Objekt. Ein Scan über mehrere unabhängige Objekte benötigt getrennte Kandidaten/Registrierungen oder einen ausdrücklich definierten gemeinsamen Rahmen; die Software erfindet diesen nicht. Anker dürfen außerhalb des Zielobjekts liegen, aber niemals Teil der Ersatzmenge sein.

Nach einem ersten aufgenommenen Datensatz darf die Auswahl nicht still umgestellt werden. Abbruch ist ein terminaler Sitzungszustand; kein automatischer Wiederanlauf von Materialausgabe. Ein Fehler oder eine leere Rekonstruktion ist kein erfolgreicher Scan.

### Output-Adapter: notwendiger Vertrag, kein versteckter Direkt-Artnet

MariMappers Backend-Grundvertrag lautet `get_led_count()` und `set_led(index,on)`. Das Standard-ArtNet-Backend setzt zusammenhängende Universen voraus, verwendet 512 Kanäle und andere Standardwerte als der bestehende Mehrcontroller-Router. Direkte Benutzung würde bestehende Zuordnungen umgehen. [Backend-Leitfaden](https://github.com/TheMariday/marimapper/blob/7dc5f799a1b7c180573c2632f6d12a3be0cbf4fa/marimapper/backends/backend_writing_guide.md), [ArtNet-Implementierung](https://github.com/TheMariday/marimapper/blob/7dc5f799a1b7c180573c2632f6d12a3be0cbf4fa/marimapper/backends/artnet/artnet_backend.py).

Erforderlicher eigener Adapter:

1. Exklusiven, zeitlich begrenzten Scan-Lease vom bestehenden Router erwerben; aktive Material-/Show-Ausgabe kollisionsfrei anhalten, vorherigen Zustand nur dokumentieren.
2. Unveränderlichen Routing-Snapshot und Szene-/Konfigurationshash binden. Ausgesuchte Source-IDs müssen eindeutig auf einen erlaubten physischen Ausgang zeigen. Unbekannte IP, Doppelbelegung, Loch oder ungeprüfte LED-Anzahl blockieren.
3. Muster ausschließlich über die bestehenden Port-/Segment-/Farbfolge-/Helligkeitsregeln senden. Kein Broadcast-Fallback, keine automatische Aktivierung deaktivierter Controller.
4. Dunkel-/Einzel-LED-Schritte erst nach Framebestätigung fortsetzen. Zeitüberschreitung, Kamerafehler, Workerabsturz und Leaseablauf führen zu kontrolliertem Blackout des übernommenen Bereichs und disarm.
5. Explizite sparse-ID-Liste statt einer gefälschten Upstream-`--subset`-Option verwenden. Ein Adapter kann interne dichte Worker-Indizes übersetzen, muss aber beide Richtungen und jede Ergebnis-ID mit dem Manifest belegen. Aktueller Offline-Worker verwendet direkt Source-Indizes, ohne Verdichtung.

Diese Schritte sind Architektur und Abnahmekriterien, keine bereits vorhandene Hardwarefunktion.

### Kamera- und Mehransichtsführung

Zukünftige Oberfläche: Wunschkamera wählen → Vorschau ausdrücklich starten → Belichtung/Focus sperren → Dunkelbild kontrollieren → erste Ansicht aufnehmen → Kamera versetzen → Überlappung prüfen → weitere Ansichten aufnehmen. Eine Aufnahme darf nur das deklarierte LED-Objekt und notwendige Anker abdecken. Kamerabilder können private Räume abbilden; Speicherung und Löschung brauchen einen sichtbaren, vom Nutzer gewählten Ordner und klaren Aufbewahrungsstatus. Keine Cloudübertragung vorgesehen.

Teilscans brauchen ausreichenden räumlichen Kontext: mehrere robuste, über verschiedene Ansichten verteilte Anker, keine ausschließlich kollineare Referenz. „Drei Anker vorhanden“ ist allein kein numerischer Qualitätsnachweis. Vorschlag für späteren Quality-Report: Anzahl unabhängiger Ansichten pro Punkt, Reprojektionsfehler mit definierter Einheit, triangulierter Blickwinkel, Skalen-/Orientierungsplausibilität, Fit-RMSE und Maximalresiduum, separater Satz nicht zum Fit benutzter Prüfpunkte. Grenzwerte sind an Kamera/Abstand/Objekt zu kalibrieren, nicht pauschal zu erfinden.

### Registrierung und Layout-Übergabe

`Scan.registration` bildet neue Rohpunkte in den **ursprünglichen lokalen Rahmen** des Zielobjekts ab. Erst danach wirkt `SceneObject.transform`. Ein veränderter Scan darf weder Rohkoordinaten überschreiben noch die bereits vom Nutzer gesetzte Objektposition zurücksetzen.

`stage_registered_candidate(scan,candidates,registration_reference,quality_reference)` nimmt extern erzeugte, unabhängig überprüfte Ergebnisse entgegen. Pflichtreferenzen sind Provenienzbehälter, kein geometrischer Beweis. `request_handoff(accepted_ids,current_scene_revision)` liefert `(MergeRequest, Scan)`, legt keine Punkte live an und ändert keinen Output.

Der Layout-Verbraucher prüft Szene-ID, `sha256(export_scene_json(scene,indent=None).encode('utf-8'))`, Scan-ID und Registrierungs-/Qualitätsnachweis. Danach erhält `replace_region` nur die ausdrücklich akzeptierten lokalen IDs und Kandidaten-Slots. `led_id`, `local_index`, `source_index`, Objekttransformation und alle nicht ausgewählten Punkte bleiben identisch. Ursprüngliche Scans werden archiviert. Anker, fehlende Kandidaten und nicht genehmigte Interpolation sind gesperrt. Ein kompletter Pixelblaze-Export darf Lücken weder wegfiltern noch Nummern verdichten.

## 5. Offline-Worker bedienen und reproduzierbar prüfen

Vorbedingungen: vom Nutzer gewählter vorhandener Arbeitsordner; zwei oder mehr unterschiedliche `index,u,v`-Dateien, deren Indizes exakt zur ausgewählten Menge plus Ankern passen; gestagte Szene. In der Oberfläche PREPARE OFFLINE JOB erzeugt `scan-<session-id>.json` ausschließlich mit exklusivem Neuanlegen. `worker_plan` enthält Argumentlisten, keine zusammengesetzten Shellbefehle.

Arbeitsverzeichnis für den separaten Aufruf ist das Repository. Beispiel, **nicht im Rahmen dieses Auftrags ausgeführt**:

```powershell
& 'C:\Users\jbhtz\AppData\Roaming\uv\tools\marimapper\Scripts\python.exe' -m pixelblaze_mapper.scan_worker 'C:\USER-SELECTED-WORKSPACE\scan-SESSION.json'
```

Ohne weiteres Flag: Eingaben prüfen und Vorschau ausgeben; keine nativen Imports oder Ergebnisse schreiben. Für ausdrücklich gewünschte echte Offline-Rekonstruktion dasselbe Kommando um `--confirm-offline-reconstruction` erweitern. Kein Kamera-/Output-Zugriff in beiden Fällen. Aufrufer muss Paketpfad/Arbeitsverzeichnis beibehalten; Manifestpfade sind keine ausführbaren Befehle.

Manifest-Prüfungen: Schema/Version/Commit, Sitzungszustand, komplette eindeutige Ansichtsliste, genehmigte Quellverzeichnisse, Dateiendung/Header, Inhaltshashes, existierender Arbeitsordner, noch nicht existierender Ergebnis-Unterordner mit existierendem Elternordner. Bei tatsächlichem Lesen werden Hashes erneut geprüft. Doppelte/unerlaubte IDs, unvollständige/überzählige Spalten, nicht endliche Koordinaten und Abweichungen vom Ansichtsnachweis führen zum Fehler.

Der echte Worker reserviert einen neuen Ergebnisordner, schreibt `candidate_3d.csv` und `quality_pending.json`. Letztere erklärt ausdrücklich: beliebige SfM-Einheiten, keine Interpolation/Normalenschätzung/Registrierung, Review erforderlich, keine Kamera/Ausgabe/Layoutänderung. Sie ist **kein bestandener Qualitätsbericht**. Fehler nach Ordneranlage können einen unvollständigen neuen Ergebnisordner hinterlassen; Originaldaten bleiben unberührt. Kein stilles Überschreiben oder automatisches Retry in vorhandene Ergebnisse.

Der Worker ist eine Prozess-/Abhängigkeitsgrenze, keine Betriebssystem-Sandbox: ein normal gestarteter Python-Prozess hat weiterhin dessen OS-Rechte. Dateiprüfungen reduzieren unbeabsichtigte Pfadfehler, schützen aber nicht gegen einen lokalen Angreifer mit gleichzeitigem Schreibzugriff. Für produktiven unattended Betrieb fehlen Ressourcenlimits, Locking und überwachte Prozessbeendigung.

Reproduzierbarer Offline-Test:

```powershell
python -m unittest discover -s tests -p 'test_scan*.py' -v
```

Ergebnis dieser Revision: **28/28 bestanden**. `pytest` steht im gewöhnlichen Repository-Python nicht zur Verfügung; es wurde nichts nachinstalliert. Tests umfassen Identitäts-/Bereichsschutz, echte CSV-/Hashprüfung in temporären Testordnern, Zustandsübergänge, unveränderte Layout-Nachbarn, Fehlerfälle und sicheren CLI-Standard. Der Test des generierten TD-Runtimes kompiliert Quelltext; er beweist ausdrücklich keine funktionierende Panel-Bindung oder Mausbedienung. Echte SfM, Kamera, LEDs, Registrierung und die neue Oberfläche benötigen eigene Abnahme.

## 6. Lizenz, Distribution und offene Entscheidungen

Upstream enthält die GNU GPL Version 3. Vor einer Weitergabe integrierter/geänderter Pakete müssen Lizenztexte, Quellbereitstellung und die konkrete Kopplung geprüft werden. Ein separater Prozess ist keine pauschale Garantie, dass alle Lizenzpflichten entfallen. Die neuen Wrapper kopieren keinen Upstream-Quellcode; sie rufen die vorhandene Installation auf. In diesem Repository wurde keine eigene Root-Lizenz gefunden. Vor Veröffentlichung ist deshalb eine ausdrückliche Lizenzentscheidung sinnvoll. Dies ist eine technische Integrationswarnung, keine Rechtsberatung. [Upstream-Lizenz](https://github.com/TheMariday/marimapper/blob/7dc5f799a1b7c180573c2632f6d12a3be0cbf4fa/LICENSE).

Upstream-Änderungen dürfen nicht still übernommen werden: Versions-/Commit-Pinning, native Offline-Referenzprobe und Schema-/Backend-Vertragstests bei jedem Update. Der vorgefundene direkte Pixelblaze-Uploader wird nicht integriert: ein Controller-Upload wäre eine separate ausdrückliche Geräteänderung, keine notwendige Folge eines Layoutimports. Der vorhandene Mapper-Export bleibt die kontrollierbare Grenze. [Pixelblaze-Dokumentation](https://github.com/TheMariday/marimapper/blob/7dc5f799a1b7c180573c2632f6d12a3be0cbf4fa/docs/backends/PixelBlaze.md).

### Priorisierter nächster Ausbau mit Abnahme

- **P0 – Routing-/Kamera-Arming:** erst nach bestätigter Gerätezuordnung implementieren. Abnahme: kein Packet vor Arm, nur erlaubte LEDs, Ausfalltests mit garantiertem Disarm, kein automatischer Show-Restart.
- **P1 – Nativer Offline-Smoke-Test:** ausdrücklichen separaten Lauf auf kopierten/manifestgebundenen realen Ansichten durchführen, Eingabedaten unverändert; Ergebnis mit bestehender Messung vergleichen, nicht allein „Prozess erfolgreich“ melden.
- **P1 – Registrierung/Qualität:** Rohscan und Referenzscan nebeneinander, Ankerzuordnung und unabhängige Prüfpunkte sichtbar; keine Übergabe bei degeneriertem Fit, unklarer Skala oder veralteter Szene.
- **P1 – Teilscan-End-to-End:** bekannte LED-Teilmenge erneut erfassen; bytegleiche Identität und Koordinaten aller nicht gewählten LEDs nachweisen; Lücken/fehlgeschlagene Rekonstruktion bleiben explizit.
- **P2 – Bedienkomfort:** Kameraauswahl aus tatsächlicher Inventur, Bereichsauswahl im 3D-Fenster, mehrsprachige Statusführung, Fortschrittsanzeige, kontrollierte Jobbeendigung, eigenständiger Session-Save/Load-Dialog und Ergebnisvergleich.

Bis diese Abnahmen vorliegen, lautet die Produktbeschreibung korrekt: **geführte Scanplanung plus vorbereiteter Offline-Rekonstruktionspfad**, nicht „voll integrierter Scanner“.
