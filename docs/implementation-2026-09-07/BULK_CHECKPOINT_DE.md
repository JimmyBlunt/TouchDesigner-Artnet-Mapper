# Gesicherte verhaltensgleiche LED-Übertragung

07.09.2026. Neue Datei: `Backup/Implementation/PixelblazeMapper_20260907_DEMAND_BULK_VERIFIED.1.toe`.
Der Dateiname enthält DEMAND, aber **native DMX-Demand-Gates sind nicht installiert**. Deren isolierte Untersuchungen sind nicht bestanden bzw. nicht abgeschlossen und verbleiben außerhalb dieser Freigabe.

## Tatsächlich geändert

Im vorhandenen `script4_callbacks.onCook` ersetzt eine gesammelte Übergabe an drei CHOP-Kanäle die 3456 einzelnen Sample-Zuweisungen. Die Initialisierung, Effektberechnung, Zufallsaufrufe, LED-Anzahl und Triggerfrequenz sind unverändert. Der Helfer akzeptiert ausschließlich den exakt geprüften Originalquelltext und die passende laufende Funktion.

Beim synchronen Live-Quellwechsel wurden das bestehende LED-Zustandsobjekt, der Framezähler und der Zufallszustand unmittelbar wiederhergestellt. Keine zusätzlichen Effektaufrufe während der Übergabe. Der normale Neustart initialisiert diesen alten Effekt weiterhin wie zuvor; der Patch macht dessen Simulation nicht über Neustarts persistent.

## Abnahme

- Zehn neue gezielte Offline-Tests: Quellbereichsschutz, exakte Float32-Werte, Zufallsfolge, Effektzustände sowie Übernahme/Rücknahme.
- 120 native Vergleiche mit echten 3×1152-Sample-CHOPs: Float32-Bytes, Effektzustände und private Zufallsfolgen identisch. Globaler Zufallszustand beim isolierten Test unverändert.
- Isolierte Callback-Zeit: 0,220246 s → 0,194809 s, etwa 11,55 % weniger für diesen Rechenschritt. Kein Nachweis einer entsprechenden Gesamt-FPS-Steigerung.
- Nachmessung: etwa 29,7–32,1 Materialberechnungen/s. Last schwankt; keine stabile 60-FPS-Abnahme. Der alte Effekt behält ungefähr 60 Simulationsaufrufe/s.
- Gesamte vorgefundene Arbeitskopie: 603 Tests in 22,283 s, OK mit einem NumPy-Skip. Die Arbeitskopie enthält zusätzliche, noch nicht freigegebene Untersuchungen; diese Zahl ist keine Hardwarefreigabe.
- Speicherstatus meldet `saved successfully`; tatsächlicher Neuaufruf meldet `loaded successfully`. 22 Prüfungen bestanden: Materialeinstellungen, Browser-/Showzustände, Map, UV, Routing, Workspace und vollständige Historien sowie persistierter Callback-Quellhash. Sieben Fixture-Undo-Einträge erhalten.
- Keine Operator- oder Picklefehler. Shared Sender OFF, alle drei nativen DMX-Ausgänge OFF, null gesendete Pakete nach Neuöffnung.

Belege im Unterordner `performance-next/`: `legacy-bulk-native-probe.json`, `bulk-install.json`, `before-save.json`, `save.json`, `after-reopen.json`, `compare.json`, `before-bulk-passive.json`, `after-bulk-passive.json`.

## Nächster bestätigter Arbeitsschritt

Guided Scan mit echter Kameraauswahl und nativen MariMapper-Einstellungen erweitern. MariMappers Kamera-/Erkennungs-/Mehransichtsablauf beibehalten; Art-Net-Ansteuerung muss den bestehenden 510-Kanal-Router, Portreserven und einen exklusiven Scanbetrieb respektieren. Kein Aufnahmestart allein durch Builder, Dialogöffnung oder Projektladen. Physische Aufnahme und Ergebnisübernahme benötigen eine gesonderte Abnahme.
