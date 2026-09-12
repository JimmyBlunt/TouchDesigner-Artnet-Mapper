# Isolierter UDP-Worker: Änderungen und Grenzen

Stand: 12.09.2026. Die Abnahme stabiler 30 FPS ist weiterhin offen. Die folgenden
Loopbackmessungen bestätigen keine physisch ausgegebenen LED-Bilder.

## Vertrag zwischen TouchDesigner und Worker

`sender_external_source.ExternalSocket` sammelt die Universen eines vollständigen
TD-Bildes und übergibt sie gemeinsam an `ExternalPacketSender`. Zieladresse,
Paketformat, doppelte Universen, leere Batches und das IPC-Größenlimit werden vor
der Übergabe geprüft. Der Worker authentifiziert und validiert erneut.

`frame_pacing` bleibt standardmäßig ausgeschaltet. Ohne `frame_rate` sendet der
Worker unmittelbar den neuesten verfügbaren Batch. Bei eingeschalteter Option
produziert TD mit `min(120, 2 * Zielrate)`; die konfigurierte Zielrate wird dabei
nicht verändert. Der Worker hält maximal einen noch nicht gesendeten Batch.
Neue vollständige Daten ersetzen ältere wartende Daten. Ohne neue Daten wird
kein Bild wiederholt und kein künstlicher FPS-Zähler erhöht.

Der optionale Worker-Takt ist phasenfest und monoton. Nach einer Verzögerung
springt die Deadline über alle verstrichenen Slots zum nächsten zukünftigen
Slot. Es gibt keine Schleife zum Nachsenden verpasster Bilder. Ein verspäteter
Slot und der folgende pünktliche Slot dürfen weniger als eine volle Periode
auseinanderliegen; dafür summiert sich normaler Aufweck-Jitter nicht dauerhaft
zu einer niedrigeren Bildrate. Zulässig sind endliche positive Raten bis 120.

Der externe Transport unterstützt einen aktivierten Controller. Änderung von
Paketabstand oder aktivem Worker-Zieltakt erfordert Stop/Start. Einstellungen
wie Prozesspriorität werden bei der Prozesserzeugung übernommen.

## Laufzeit, Dateizugriffe und Fehlerverhalten

- Statusdateien werden im TD-Prozess höchstens 100 ms gecacht. `process.poll()`
  bleibt bei jedem Statusaufruf aktuell; Prozessende und Cleanup lesen frisch.
- Worker-Start ist auf fünf Sekunden begrenzt. Die Start-Grace-Periode ohne
  erste Eingabe beträgt weiterhin fünf Sekunden; nach gültiger Eingabe greift
  der Ein-Sekunden-Watchdog. Ungültige IPC-Daten verlängern ihn nicht.
- Während der Taktwartezeit bleibt der UDP-Empfang aktiv; angeforderte
  Socket-Wartezeiten betragen höchstens 50 ms. Nach dem Warten wird der
  Watchdog erneut geprüft, bevor ein wartendes Bild ausgegeben werden darf.
- Periodische Statusdatei-Ersetzungen sind best effort: Bei `PermissionError`
  wird ohne Retry/Sleep übersprungen. Andere `OSError` werden gezählt. Der
  nächste erfolgreiche Snapshot enthält die inzwischen aktuellen Zähler.
  Start- und Abschlussdateien behalten den auf 200 ms begrenzten Retry.
- Der physische Sendesocket verwendet Nonblocking und angeforderte 1 MiB
  `SO_SNDBUF`. Die tatsächlich vom OS gewährte Größe wird gemeldet. Jeder
  `OSError`, einschließlich `EWOULDBLOCK`, beendet die Ausgabe sichtbar;
  fehlgeschlagene Pakete werden nicht als Erfolg gezählt oder still verworfen.
- Der Abschluss setzt den Sendesocket auf den bisherigen Timeout von 200 ms
  zurück und sendet zweimal Schwarz für alle vorgemerkten Universen. Das gilt
  auch nach einem Fehler mitten im Batch. Ein Schwarz-Socketfehler steht im
  Endstatus. Dies bestätigt lokale Sendungen, nicht Empfang beim Controller.
- Die Stop-Datei wird an Empfangsschleifen-/Batchgrenzen frisch geprüft.
  Innerhalb langer Batches sind negative Ergebnisse höchstens 20 ms gecacht.
  Ein einmal erkanntes Stop bleibt gesetzt.

Die genannten Grenzen begrenzen unsere Warte-/Cache-Logik. Windows-Scheduling,
Dateisystemaufrufe und andere OS-Arbeit können länger blockieren. Insbesondere
`write_text`/`replace` bleiben synchrone OS-Aufrufe. Sie sind jetzt getrennt vom
Paket-Sendetimer messbar; damit werden verbleibende Dateistalls nicht versteckt.

## Zähler richtig lesen

| Feld | Bedeutung |
|---|---|
| `queued_batches` | Vom TD-Adapter erfolgreich lokal übergebene Batches |
| `submitted_batches` | Vom Worker gültig empfangene Batches |
| `sent_batches` | Vollständig lokal gesendete Batches |
| `stale_batches` | Vor der Ausgabe bewusst durch neuere Daten ersetzte Batches |
| `local_drops` | Nicht angenommene lokale IPC-Übergaben |
| `send_errors` | Fehler während einer normalen UDP-Ausgabe |
| `blackout_packets` | Erfolgreiche lokale Schwarzsendungen |
| `frame_rate` | Gewünschter Worker-Takt oder `null` für unmittelbare Ausgabe |
| `send_buffer_bytes` | Tatsächliche Socket-Sendepuffergröße |
| `status_write_ms`, `max_status_write_ms` | Dauer der periodischen Statusoperationen |
| `status_write_skipped`, `status_write_errors` | Dateisperren bzw. andere I/O-Fehler |

Die Dauer einer Statusoperation kann erst im nächsten erfolgreichen Snapshot
oder Endstatus stehen. `stale_batches` ist keine Messung verlorener UDP-Pakete.
Ein beim Stop noch wartender Batch kann die Bilanz zusätzlich offen lassen.

## Messbelege und negativer Prioritätstest

| Versuch | Empfangsrate | Messfenster | Beleg |
|---|---:|---:|---|
| Phasenfester Takt, normale Priorität | 29,749719 FPS | 60,000566 s | `frame-clock-perform-60s.json` |
| AboveNormal-Vergleich | 29,299391 FPS | rund 120 s | `priority-30fps-120s.json` |

Der erste Versuch empfing pro Universum 1.785 Pakete im Messfenster. Der
Worker-Abschluss umfasst auch die Ränder außerhalb dieses Fensters: 2.638
gültige Eingaben, 1.876 gesendete Batches, 762 ersetzte Batches, 58 Schwarzpakete,
keine Fehler. Die Empfangspausen lagen teilweise bei etwa 193 ms; der gemessene
maximale reine Sendeloop betrug 8,611 ms. Ein guter Durchschnitt ersetzt daher
keine Stabilitätsabnahme.

AboveNormal verbesserte die Leistung in diesem Vergleich nicht: pro Universum
3.516 empfangene Pakete, teilweise nur 23 Pakete in einer vollständigen Sekunde,
Worker-Sendeloop maximal 232,237 ms. Die Prioritätsdatei
`priority-30fps-120s-priority.json` belegt Normal → AboveNormal → Normal für TD.
`priority='normal'` bleibt der Worker-Standard; nur `above_normal` ist optional.
High/Realtime werden weder angeboten noch verwendet. Die wechselnde Hostlast
verhindert eine isolierte kausale Aussage über Priorität allein.

Diese beiden JSON-Läufe stammen vor den späteren Nonblocking-/Stopcache-
Änderungen und sind kein Abnahmenachweis dieser letzten Version.

## Tests und unabhängiger Review

Die gezielten Mocktests prüften Fehler vor dem ersten und nach einem gesendeten
Paket, sichtbaren Fail-Stop, wiederhergestellten Blackout-Timeout und Schwarz für
alle bekannten Universen. Ein simulierter 29-Paket-Batch stoppte 11 ms nach dem
Stop-Signal; drei Dateiprüfungen genügten, danach wurden 58 Schwarzpakete gesendet.
Weitere Tests prüfen Status-Sperren mit anschließendem Aufholen, begrenzte
Abschluss-Retries, Prioritätsvalidierung und Plattform-Fallback. Alle diese
gezielten Tests bestanden.

Der anschließende vollständige gezielte Lauf über
`test_external_packet_sender`, `test_sender_external_source`,
`test_generated_sender_runtime`, `test_sender_pacing` und `test_sender_packet_gap`
umfasste 54 Tests in 79,783 s: 44 bestanden, zehn Loopback-Prozesstests scheiterten
bereits am Worker-Startlimit von fünf Sekunden. Die zuvor geprüfte frühere
Worker-Version hatte 27/27 Tests bestanden. Nach dem Schließen von Chrome und
der Speicherentlastung bestanden im Wiederholungslauf alle **75/75 Tests in
27,497 Sekunden**, einschließlich Prozessintegration, generiertem Sender,
Pacing und sechs zusätzlichen Router-UI-Tests. Das Startlimit blieb unverändert.

Der unabhängige Review fand außerdem: Eine während laufender Ausgabe auf 0 oder
negativ geänderte Controller-Rate kann die Pacer-Validierung außerhalb des
generierten `try/stop` erreichen. Root hat den gesamten Konfigurations-/Pacer-
Block mit Fehlerabbruch abgesichert (`EXTERNAL_FRAME_CLOCK_V2`);
`tests/test_sender_external_runtime_review.py` enthält die reproduzierbare
Runtime-Prüfung für 0, negative, nichtnumerische und nichtendliche Raten sowie
Headroom-/Restart-/Mehrcontroller-Prüfungen. Alle bestanden.

Keine Hardware, Scandaten oder Controller-Firmware wurden für diese Tests
verändert. Die Liveinstallation wurde anschließend separat geprüft:
`nonblocking-clock-v2-install.json` bestätigt identische Routing-Payloads,
Masken und vier Routing-/Layouttabellen bei ausgeschalteter Ausgabe.

## Router-Status und native Messung

`router_status_source.py` reduziert die doppelte Abfrage der Quellpixelzahl auf
eine pro Statusaktualisierung. `mapping_counts_cached` verwendet den vollständigen
typisierten Inhalt aller Eingaben als Schlüssel; geänderte oder ungültige Daten
werden nicht durch einen alten Validierungserfolg verdeckt. Die Installation
ist reversibel und im Builder enthalten. `router-status-cache-install.json`
bestätigt unveränderte Konfigurationstabellen und keine TD-Fehler.

Der neue native 60-s-Lauf `nonblocking-clock-memory-free-60s.json` empfing auf
allen 29 Universen 29,316455 FPS, ohne Sendefehler oder lokale Drops. Letzter
Paketloop 0,631 ms, maximal 8,087 ms, Statusdatei maximal 6,482 ms. Trotzdem
mindestens 22 Bilder in einer vollständigen Sekunde und bis 142,991 ms Abstand:
die stabile 30-FPS-Abnahme bleibt offen. Priorität und Perform Mode wurden
wiederhergestellt; die Ausgabe ist aus.
