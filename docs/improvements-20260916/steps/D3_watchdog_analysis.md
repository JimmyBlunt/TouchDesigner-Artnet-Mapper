# D3 - Watchdog im Direktbetrieb: warum ich ihn nicht gebaut habe

Im Analysebericht steht als Vorschlag: "Ein Timer-CHOP, der bei ausbleibendem
tick() oder gesetztem _last_error blackout sendet, schliesst die Luecke bei
Absturz und Frame-Drop."

Beim Umsetzen hat sich gezeigt, dass dieser Vorschlag die Luecke nicht
schliessen kann, die er schliessen soll. Ich halte das lieber fest, als etwas
zu bauen, das Sicherheit nur vortaeuscht.

## Das Problem

Ein Watchdog innerhalb von TouchDesigner laeuft im selben Hauptthread wie
`tick()` selbst. Die drei Faelle, gegen die er schuetzen soll:

| Fall | Kann ein prozessinterner Watchdog helfen? |
|---|---|
| TouchDesigner stuerzt ab | Nein. Kein Python laeuft mehr, auch der Watchdog nicht. |
| TouchDesigner friert ein (modaler Dialog, langer Cook) | Nein. Genau der Thread, der den Watchdog ausfuehren muesste, steht. |
| Ausnahme im Sendetakt | Ja - aber das deckt bereits D1 ab, weil `tick()` im Fehlerfall `stop()` ruft und `stop()` dann schwarz sendet. |
| Netzwerkausfall | Nein. Die Pakete gehen ins Leere; ob sie ankommen, weiss der Sender nicht. |

Wir haben diesen Einfrierfall in dieser Sitzung zweimal selbst erlebt: einmal
durch einen modalen Ueberschreiben-Dialog, einmal durch einen zu schweren
Skriptdurchlauf. In beiden Faellen stand TouchDesigner minutenlang. Ein
Watchdog im selben Prozess haette in beiden Faellen geschwiegen.

## Was tatsaechlich hilft

Der richtige Watchdog existiert bereits und laeuft ausserhalb von
TouchDesigner: `external_packet_sender._worker` mit `WATCHDOG_SECONDS = 1.0`.
Bleiben die Frames aus, setzt er `stop_reason = 'idle_watchdog'` und sendet im
finally-Block jedes beruehrte Universum zweimal schwarz. Das ist genau die
gewuenschte Zusage, und sie funktioniert auch dann, wenn TouchDesigner steht.

Er ist nur abgeschaltet: `external_sender_settings = {'enabled': False}`.

Die letzte gespeicherte Statistik legt nahe, warum:

    submitted_batches  9681
    sent_batches       6541
    stale_batches      3139      (rund ein Drittel)
    send_errors           0

Ein Drittel der Frames erreichte den Worker zu spaet. Das ist ein
Auslieferungsproblem zwischen TouchDesigner und dem Worker, kein Fehler im
Watchdog.

## Empfehlung

Statt eines prozessinternen Ersatzes, der im Ernstfall nicht laeuft: die
Ursache der 3139 verspaeteten Sendungen klaeren und den externen Sender wieder
aktivieren. Damit loest sich D3 *und* D2 auf einmal - dort blockiert der
Paket-Abstand niemanden, und der Watchdog wirkt auch bei einem Absturz.

Das ist Feldarbeit an laufender Hardware und gehoert nicht in einen
Fernzugriff ohne Sicht auf die Wand.
