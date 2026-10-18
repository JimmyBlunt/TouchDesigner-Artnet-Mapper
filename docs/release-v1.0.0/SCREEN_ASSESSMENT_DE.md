# Einzelbewertung der Bedienoberflächen · v1.0.0

Stand: 18. Oktober 2026. Diese Bewertung beschreibt die vorliegenden
Software- und Bediennachweise. Sie bestätigt weder einen bereits gespeicherten
Release-Checkpoint noch Commit oder Push.

Die vollständige Python-Prüfung ergibt **1.782 bestanden, 1 übersprungen und
5.117 bestandene Untertests** in 115,58 Sekunden. Der übersprungene
Windows-Symlink-Fall hängt von der Berechtigung des ausführenden Benutzers ab.
[Vollständiges Ergebnis](qa/tests-pytest-full.txt) · [Testumgebung](TESTING_DE.md).

## Bewertungsmaßstab

**UI geprüft** bedeutet: nativer Dialog existiert, Info reagiert auf Hover,
Verlassen, Anheften und Schließen, How-to-Ziel stimmt, Feldhinweise funktionieren,
Hilfebuttons sind eindeutig, Schriftdatei ist erreichbar und Hilfe bleibt im
Panel. Der aktuelle Nachweis umfasst 20 native Dialoge und 187 native Feldhinweise.
Er behauptet nicht, jede produktive Aktion jedes Dialogs physisch ausgelöst zu
haben. Vier zusätzliche Webdialoge ergänzen den Hilfekatalog auf 24 Anleitungen
und 213 Feldhinweise. Alle besitzen echte Anwendungsscreenshots.

**Ablauf geprüft** benennt zusätzlich konkret ausgeführte, reversible
Bedien-/Datenaktionen. Sender bleiben bei diesen Prüfungen ausgeschaltet.
Automatisierte Modelltests ergänzen die Live-Nachweise, ersetzen aber keine
vollständige physische Geräteprüfung.

Die finale Gestaltung verwendet Bahnschrift, Hintergrund `#101820`, Flächen
`#232a25` und Rahmen `#354139`. Titel und Labels sind `#e1e5e6`, Werte und
Variablen `#55d6e7`, Button-/Funktions- und aktive Beschriftung `#aeb7ba`,
sekundärer Text `#a9b2b5`. Zusammengehörige Aktionen sind gruppiert und
Bedienelemente abgerundet.

## Jeder Bildschirm

| Bildschirm / Anleitung | Ergebnis und konkret belegter Umfang | Verbleibende Prüfgrenze |
|---|---|---|
| [Übersicht & Shortcuts](launcher.html) | UI geprüft; native Ziele und aktualisierte Shortcuts vorhanden, sieben Shortcut-Regressionsprüfungen bestanden. Router und Controller-Ports direkt erreichbar. | Tastenkürzel können bei aktivem Texteingabefeld abgefangen werden. |
| [Material Browser](materials.html) | UI geprüft; Materialparameter, Auswahl und gespeicherte Werte nach Pfadkorrektur unverändert. Lokale Materialdateien und Vorschauen auflösbar. | Keine Behauptung, alle 638 Materialien auf jeder GPU getestet zu haben. |
| [MadMapper-Bibliothek](library.html) | UI geprüft; 638 Quellen/Vorschauen erreichbar, 638 Importmanifeste und 585 vorbereitete Shader vorhanden. Originalkatalog bytegleich. | Kompatibilitäts- und Quarantänestatus bleiben maßgeblich; Thumbnail ist kein Rendernachweis. |
| [Material Player](player.html) | UI und Reglerhinweise geprüft; Player-/Materialzustand bei Portabilitätsänderungen erhalten. | Keine erneute physische LED-Abnahme für alle Material-/Parameterkombinationen. |
| [Pixel Mapper](mapper.html) | UI geprüft; native Felder/Ziele vorhanden, Mapping-/Exportablauf anhand Buildern dokumentiert. | Keine neue vollständige Vermessung der Anlage im Release-Prüflauf. |
| [Art-Net Router](router.html) | UI und Ablauf geprüft: alle vier Controller über Auswahl erreichbar, Routingtabellen unverändert, Ausgabe aus. | Reale Farbreihenfolge, Paketqualität und Dauerlast benötigen Hardware-/Netztest. |
| [Output-Status](output.html) | UI geprüft; schreibgeschützter Status und Weg zum Router dokumentiert. | Ein konfiguriertes Enabled-Flag beweist keinen laufenden Sender oder empfangendes Gerät. |
| [Show Control](show.html) | UI und Ablauf geprüft: Auswahl/Laden, leere Show ohne Sidecars, genaue ausgewählte Dateinamen beim Speichern, neue leere Show; Play bleibt bei leerer Show gestoppt/schwarz. Originalshow wiederhergestellt. | Neuer Aufnahme-/Transporttest mit physischem MK2 und Lichtausgabe separat. |
| [GICO-Portkonfiguration](gico.html) | UI geprüft; Eingabefelder und How-to vorhanden, Port-/Routermodell durch Regressionen abgedeckt. | Keine unbegründete Übernahme neuer Portbelegungen oder Controller-Firmwareprüfung. |
| [Layout & Fixture-Editor](layout.html) | UI geprüft; Layout-/Fixturefelder und Prozessfolge dokumentiert; bestehende Geometrie erhalten. | Kein erneutes manuelles Ausrichten aller Panels zur physischen Anlage. |
| [Geführter Scan](scan.html) | UI geprüft; Vorbereitung, Kamera, Aufnahmen, Rekonstruktion und Übernahme dokumentiert. Software-/Videotests bestanden. | Keine neue Kameramessung oder neue 3D-Rekonstruktion physischer LEDs in diesem Release-Test. |
| [Neue Aufnahme](new_capture.html) | UI geprüft; Eingabebeispiele und Aufnahmevorbereitung vorhanden. | Automatisch verarbeitetes Testvideo ersetzt keine angeschlossene Kamera und Beleuchtungsprüfung. |
| [Scan-Ergebnis](review.html) | UI geprüft; Qualität/Abdeckung/Entwurfsübernahme dokumentiert. | Ein bestandener UI-Test bestätigt keine geometrische Qualität eines beliebigen neuen Scans. |
| [LED-Suche](led_search.html) | UI geprüft; Controller, Ausgang und lokale ID dokumentiert; Shortcut S verifiziert. | Leuchttest sendet real und wurde nicht als Folge der Hilfetestung ausgelöst. |
| [Controller & Ports](ports.html) | UI und Ablauf geprüft: alle vier Controller auswählbar, Entwürfe/Validierung/sicheres Anwenden dokumentiert; Routingtabellen erhalten. | Neue Controllerkapazitäten müssen mit tatsächlicher Hardware übereinstimmen. |
| [Sequencer](sequencer.html) | Browser geprüft: bestehende Test1-Show gerendert, Kontextinfo geöffnet, Raster/Fit reagieren, kompakte Ansicht erfasst und ausführliche Hilfe ausgeliefert. | Kein Transport- oder physischer LED-Test durch diesen Browserlauf. |
| [MK2-Steuerung](mk2.html) | Webdialog und Kontextinfo öffnen/schließen; Belegung/Displays anhand aktuellem Controllercode dokumentiert, beschriftete Grafik vorhanden. | Mechanische Tasten, Regler, HID-Verbindung und Displaylesbarkeit am Gerät separat prüfen. |
| [MIDI](midi.html) | Webdialog und Kontextinfo öffnen/schließen; tatsächliche DOM-Felder und Eingabehinweise geprüft. | Kein physisches MIDI-Lernen oder Versand einer Controllerbewegung im Browserlauf. |
| [Scan-Bibliothek](scan_library.html) | UI geprüft; Auswahl, Resume, Review und Teilumfang anhand Quelllogik dokumentiert. | Eine vorhandene Datei allein bestätigt keine passende Scan-/Panelzuordnung. |
| [Fehlende Bereiche](coverage.html) | UI geprüft; Ansichtswahl und Farblegende dokumentiert, echte Erfassung vorhanden. | Nie erkannte LEDs bekommen keine erfundenen Positionen. |
| [Teilscan ausrichten](registration.html) | UI geprüft; Anker, Prüfanker, Grenze und Ersatz-IDs mit Beispielen erläutert. | Kein neuer physischer Registrierungs-/Ersatzvorgang im UI-Test. |
| [Native Materialparameter](native_params.html) | UI und vier Komponentenhinweise geprüft; native Materialparameter nach Portabilitätsänderung erhalten. | Materialabhängige Events/Compile-Time-Eingaben sind nicht pauschal aufnehmbare kontinuierliche Automation. |
| [MK2-Materialauswahl](mk2_preview.html) | Erhaltener optionaler Dialog: UI/Hilfe zuvor geprüft und Standbild erfasst. Die automatische Desktopvorschau ist anschließend standardmäßig abgeschaltet (`desktop_browse_preview: false`); normale Auswahl erfolgt auf dem MK2, dessen Displaybilder erhalten bleiben. | Der Screenshot dokumentiert die optionale Ansicht, nicht das aktuelle automatische Verhalten. Keine physische Messung der Radgeschwindigkeit oder Latenz. |
| [PXLBLZ-Manager](pxlblz_manager.html) | Sichere Web-UI geprüft: Info öffnet/schließt, Ausgabe aus, verständliche Abhängigkeitsmeldung. | Externer lokaler Router unter `http://127.0.0.1:9988` nicht erreichbar. Synchronisieren/Anwenden/physische Ausgabe deshalb nicht als erfolgreich abgenommen. |

## Belege und praktische Grenzen

- [Native Hilfefunktionen](qa/native-ui-help-checks.json) und [Ziel-/Feldprüfung](qa/documentation-native-readback.json)
- [Show- und Controllerauswahl](qa/workflow-live.json)
- [Browserprüfungen einschließlich Farbrollen](qa/browser-qa.json)
- [Material-Portabilität live](qa/material-portability-live.json) und [Offline-Assetprüfung](qa/material-assets-offline.json)
- [Dokumentationsverweise, SVGs und DOM-Felder](qa/documentation-validation.json)
- [Wiederherstellung der entfernten DATs](qa/cleanup-result.json)

Die Offline-Assetprüfung liest alle 638 Quellen, findet 83 referenzierte native
Texturdateien ohne fehlende Dateien oder Exceptions und bewertet 586 als
adaptable/52 als unsupported. Das ist eine aktuelle, lesende Adapterbewertung;
der unveränderte historische Katalog enthält weiterhin 585/53 und 585 vorhandene
vorbereitete Shader. Keine dieser Zahlen ist eine komplette GPU-Abnahme.

Beim PXLBLZ-Manager können Zahlen aus einem älteren Exportpaket sichtbar bleiben,
obwohl der lokale Routerdienst fehlt. Sie sind dann kein Live-Nachweis der
aktuellen Anlage. Dienst bereitstellen, Status prüfen und bei geändertem Layout
neu exportieren, bevor der vollständige externe Ablauf abgenommen wird.

Die neue Gestaltung und Hilfe sind softwareseitig geprüft. Physische LED-Farben,
Kameramessung, mechanische MK2-Eingaben und Langzeit-Netzlast bleiben ausdrücklich
getrennte Prüfungen. Der endgültige Speicher-/Git-/Remote-Nachweis wird separat
nach dem tatsächlichen Abschluss geführt.
