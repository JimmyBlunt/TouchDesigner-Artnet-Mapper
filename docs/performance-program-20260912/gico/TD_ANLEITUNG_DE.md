# Aufnahmebereiter Test: TouchDesigner → GICO

Der neue Lauf verwendet einen temporären Script CHOP als Testpixelquelle und danach den vorhandenen TouchDesigner-Router, NumPy-Packer, ArtDmx-Serializer, Controller-Pacer und externen UDP-Worker. Er prüft die native TD-Ausgabe einschließlich Routing und Transport. Die Renderkosten beliebiger Materialien/GPU-Effekte sind damit noch nicht gemessen; das Testmuster ersetzt die Materialquelle.

## Aufnahme

Dasselbe untere Panel vollständig und fest aufnehmen. iPhone 13: Slo-Mo, 1080p mit 240 FPS; Kamera vor dem Startsignal laufen lassen. Unveränderte Originaldatei behalten. Aufnahme erst nach bestätigtem Testende stoppen. Keine Zeitlupenrampen oder Schnittbearbeitung durchführen; die tatsächliche Zeitbasis wird anhand Originalzeitstempeln und Kalibrierphasen geprüft.

Ablauf wie zuvor: 3 s gemeinsame Marker, 1 s schwarz, 21 Einzelmarker je 1 s, dann 15/25/30 optische Bilder/s mit jeweils 3 s Aufwärmen, 60 s Messung und 2 s schwarzer Pause. Rund 3 min 40 s reale Aufnahmezeit.

**Unterschied zum unabhängigen Sender:** Der native TD-Transport ist während des gesamten Laufs auf 30 FPS eingestellt. Nur der codierte Bildinhalt wechselt mit 15/25/30 FPS. IDs folgen dem monotonen Inhaltstakt; bei einem TD-Stall können IDs übersprungen werden. Tatsächliche native Einreichungen und Worker-Ergebnisse werden separat gespeichert. Eine wiederholte Einreichung derselben sichtbaren ID zählt nicht als neues optisches Bild.

## Umfang und Wiederherstellung

Nur GICO 10.0.0.244, U0–23, ArtDmx-Sequenz 0, ursprüngliche drei Segmentzuordnungen (517/269/398 LEDs). Weißer Kanalwert maximal 16/255. Die Controller-Helligkeit wird temporär auf 1 gesetzt, damit genau dieser kleine Kanalwert den unabhängigen Test reproduziert; alle anderen Controller bleiben während des Tests deaktiviert. Die Quelle enthält sonst ausschließlich Schwarz.

Das Modul prüft ausgeschaltete Ausgaben und die genaue Segmentzuordnung, bevor es die Testquelle einsetzt. 25 Muster einschließlich jedes Einzelmarkers werden durch den nativen Packer mit den Referenzpaketen verglichen. Keine Masken werden umgangen. Nach Ablauf, Fehler oder Abbruch: Sender stoppen, Schwarz über den Worker, Controller-/Quell-/Execute-/Pacing-Einstellungen und Perform-Modus zurücksetzen, temporäre Nodes entfernen, Wiederherstellung protokollieren. Das .toe wird dafür nicht überschrieben. Der vorhandene Worker-Watchdog schützt gegen ausbleibende TD-Einreichungen.

## Start durch den Agenten nach laufender Kamera

```powershell
& 'C:/Users/jbhtz/AppData/Roaming/uv/tools/marimapper/Scripts/python.exe' tools/gico_td_camera_test.py run --output measurements/gico-td-camera-001
```

Ein neues Ausgabeverzeichnis ist erforderlich. Der Lauf läuft im TD-Frame-Callback autonom und beendet sich selbst; während der Messung erfolgen keine wiederholten Bridge-Abfragen. Das Hostskript wartet nur auf den Abschlussbericht und führt im Fehlerfall zusätzlich einen Stop-/Restore-Aufruf aus.

## Bereits geprüfte Vorbereitung

- `measurements/gico-td-preflight-001`: 25 native Muster bytegenau gleich der Referenz; keine Netzwerk-Ausgabe; Routing und Quelltext unverändert restauriert.
- `measurements/gico-td-loopback-001`: nativer Kurzlauf samt Stop/Restore gelang. Die anschließende externe Paketprüfung scheiterte an einem fehlenden Python-Importpfad im neuen Hostskript; korrigiert, kein Hardwareziel beteiligt.
- `measurements/gico-td-loopback-002`: vollständiger Kurzlauf mit 3.888 lokal empfangenen Paketen (3.840 Daten plus 48 Schwarz), alle 24 Universen, keine ungültigen Header, falschen Lichtpositionen oder Kanalwerte. Keine Sendefehler. Alles wiederhergestellt.
- Abschließende native Prüfung: keine temporären Testnodes, kein aktiver Test, Ausgabe aus, keine TD-Fehler. GICO .244 antwortet auf Ping.

Die lokale Funktionsprüfung ist keine optische Hardwaremessung und keine langfristige 30-FPS-Abnahme. Der Hardwarelauf wartet auf die bestätigte Kameraaufnahme.
