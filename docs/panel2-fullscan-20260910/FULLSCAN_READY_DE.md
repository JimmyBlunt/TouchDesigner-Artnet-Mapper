# Panel 2: manuell bedienbarer Vollscan vorbereitet

Die eigenständige Aufnahme unterstützt jetzt ein optionales Paar aus Controller-Frame-Start und Controller-Universenzahl. Der Panel-Start bleibt separat. Ein gültiger Framebereich muss das gesamte Panel enthalten; falsche/halbe Einstellungen werden vor Kamera- oder Netzwerknutzung abgewiesen.

Aktuell: Controller 10.0.0.249, Panel 2 mit 738 LEDs ab U122, Controllerbereich U120–126 (Start120, Anzahl7). Der Segmentoffset340 bildet zwei Universen à170 Plätze vor Panel2 ab. Der reguläre Dialog CHECK SCAN PLAN bestätigt Panel U122–126 und SEND U120–126; alle anderen Plätze bleiben schwarz. Der Scope enthält genau738 lokale IDs0–737.

Die Bibliothek rekonstruiert Panel-Start und begleitende Schwarzuniversen aus neuen Capturebelegen mit exakter Einstellungsrevision und stabilen Identitäten. Nicht darstellbare Routen und die frühere manuell überschriebene Diagnoseaufnahme werden weiterhin abgewiesen. Keine automatische Controllererkennung: Einstellungen werden explizit erfasst und mit der Sitzung gespeichert.

Neue Vollscan-Sitzung und eigener Ordner Scans/back_panel2_738_249_20260910_fullscan. Der alte Fünf-LED-Test bleibt unverändert archiviert; seine Ansicht wird nicht in die neue Aufnahme gemischt. Nutzerwerte Kamera0, Belichtung−10, Schwelle160, Helligkeit6,5% bleiben erhalten.

108 gezielte Tests bestanden. Native Installation und reguläre UI-Aktionen stage_capture/prepare erfolgreich; alle738 Ziele und sieben Frameuniversen geprüft. Mapping, UVs, Routingtabellen und Entwurf hashgleich, keine Operatorfehler. Keine Kamera/Scan-Prozesse durch die Vorbereitung gestartet. Eigenständiger TOE-Checkpoint gespeichert (saved-project.json); dieser Checkpoint wurde während der laufenden Nutzeranleitung nicht erneut geladen.

Der Nutzer startet die Aufnahme selbst über CHECK SCAN PLAN, danach START SCAN / NEXT VIEW und Start Scan im Bestätigungsdialog. Dieser Stand bestätigt die korrekte Softwarevorbereitung, keinen abgeschlossenen Vollscan.

Die Screenshot-Randnotiz zur veralteten Coverage-Anzeige ist für später in LATER_UI_NOTE_DE.md erfasst.
