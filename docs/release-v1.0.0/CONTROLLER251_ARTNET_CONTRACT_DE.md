# Controller 251: Art-Net-Abgleich nach Wechsel des Stromversorgungsstrangs

Prüfung am 18.10.2026. Der Benutzer hat Controller `10.0.0.251` neu gestartet
und an einen anderen Stromversorgungsstrang angeschlossen. Die aktuelle
Controller-Konfiguration wurde über `/api/config` gelesen; ein tatsächlich
versendeter, stark gedimmter Live-Frame wurde direkt am `sendto`-Aufruf des
laufenden TouchDesigner-Senders protokolliert. Das ist ein Nachweis der an das
Betriebssystem übergebenen Bytes, kein Mitschnitt am Netzwerkkabel.

## Erwartet und gesendet

| Eigenschaft | Empfänger / Erwartung | Aktueller Sender | Ergebnis |
|---|---|---|---|
| Ziel | UDP 6454 | `10.0.0.251:6454`, Quelle `10.0.0.125:6454` | Passend |
| Pakettyp | ArtDMX | `Art-Net\0`, OpCode `0x5000` little endian, Protokollversion 14 big endian | Passend |
| Universe-Adressen | Ausgangsbezogen 156–162, nullbasiert | 156, 157, 158, 159, 160, 161, 162 | Passend |
| Nutzdaten | 170 RGB-Pixel pro Universe im konfigurierten Mapping | Genau 510 Bytes je Universe; 528 Bytes einschließlich ArtDMX-Header | Passend |
| Sequenz | 0 schaltet Sequenzprüfung aus | 0 bei allen sieben Paketen | Zulässig; keine eindeutige Bildnummer |
| Physical-Feld | Kein Ausgangsselektor dieser Firmware | 0 | Ausgang über Universe-Zuordnung bestimmt |
| Frame-Abschluss | Alle benötigten Universen empfangen | Sieben Pakete pro Bild, kein ArtSync | Passend |
| Sammelzeitlimit | 100 ms ab erstem Paket einer Sammelgruppe | Gemessene Spanne erstes bis letztes `sendto`: 9,972 ms | Einzelner erfasster Frame unter dem Limit |
| Bildrate | Ausgabe maximal konfiguriert 60 FPS | TD-Zielrate 30 FPS für diesen Controller | Keine erforderliche feste 60-FPS-Zufuhr |

Das globale `startUniverse=0` aus der Statusanzeige überschreibt hier nicht die
expliziten Universe-Adressen der drei Ausgänge. Ein Wechsel des Senders auf U0
wäre für diese Konfiguration falsch.

| Physischer Ausgang | LEDs / Speicherbeginn im Controller | Universen | TD-Pixeloffset im 7-Universe-Paketbereich |
|---|---|---|---|
| 1 (API-ID 0) | 299 / 0 | U156–157 | 0 |
| 2 (API-ID 1) | 357 / 299 | U158–160 | 340 |
| 3 (API-ID 2) | 196 / 656 | U161–162 | 850 |

Die unterschiedlichen Speicher- und Paketoffsets sind beabsichtigt: Jeder
physische Ausgang beginnt auf einer Universe-Grenze. Nach Ausgang 1 bleiben
41 und nach Ausgang 2 weitere 153 Paket-Pixel ungenutzt. Alle entsprechenden
Bytes im erfassten Frame sind null. Ausgang 3 hat 195 zugeordnete Positionen;
sein 196. Hardwareplatz bleibt schwarz, ebenso die übrigen 144 Paket-Pixel.
Es wurden keine fehlenden Positionen erfunden oder verschoben.

**Farbfolge:** TD sendet für diese Segmente BGR. Die Firmwareeinstellung RGB
gibt das empfangene Tripel im APA102-Pfad in derselben physischen Reihenfolge
weiter; sie kompensiert dabei intern den festen FastLED-BGR-Treiber. Somit
erreicht physisch BGR die APA102-LEDs. Sender-BGR plus Empfänger-RGB ist hier
konsistent. Beide Seiten auf BGR umzustellen würde doppelt tauschen.

[Erfasste Pakete und aktuelle Hardwarekonfiguration](qa/controller251-sender-contract.json)
enthalten Header, vollständige Nutzdaten, Ziel und Zeitpunkte. Der Test hat
genau einen Live-Frame bei Helligkeit 0,02 sowie anschließend einen vollständigen
schwarzen Frame gesendet. Beide Frames wurden vollständig empfangen
(14 Pakete, zwei vollständige Frames; keine zusätzlichen Fehler).

## Was weiterhin fehlschlägt

Der Empfang ist trotz passenden Formats nicht verlustfrei. Beim unabhängigen
Schwarzbildsender liefen während der jeweiligen 30 Sekunden keine HTTP-Abfragen
an `.251`; die Zähler wurden vor und nach der Ausgabe gelesen.

| Test | Gesendete / empfangene Pakete | Vollständige / verworfene Gruppen |
|---|---|---|
| Unabhängiger Sender, 10 FPS, 1 ms Abstand, andere Controller aktiv | 2.093 / 2.083 | 289 / 10 |
| Gleicher Test, sämtliche TD-Ausgaben gestoppt | 2.093 / 2.088 | 294 / 5 |

In beiden Fenstern: keine neuen Queue-Drops, Socketfehler, Sequenzfehler oder
Timeouts; keine erkennbaren Zählerrücksetzungen. Der unveränderte
Heap-Minimalwert und die durchgehend steigenden Empfangszähler liefern keinen
Hinweis auf einen Neustart während dieser Tests. Das ersetzt keine
Reset-Ursachenmessung. Der vorher gemeldete vollständige Hänger ist weiterhin
nicht erklärt oder als behoben nachgewiesen.

`rxPackets` zählt im geprüften Firmwarequelltext vor der eigenen Empfangsqueue.
Der beobachtete Verlust liegt daher vor dieser Zählstelle; Senderbetriebssystem,
Netzwerk und Empfangsstack sind damit noch nicht voneinander unterschieden.
Ein Queue-Überlauf oder falsches LED-Mapping ist durch diese Messung nicht belegt.

`framesIncomplete` zählt verworfene Sammelgruppen. Ein erneut eintreffendes
Universe verwirft eine noch unvollständige Gruppe; ein Sammel-Timeout würde
zusätzlich `timeouts` erhöhen. Die Firmware gibt nur vollständige Gruppen aus
und hält sonst das vorige Bild. Sequenz 0 garantiert allerdings keine eindeutige
Zuordnung aller Pakete zum selben Senderbild.

Auch die begrenzten TD-Tests mit 10 FPS und Helligkeit 0,02 wurden wegen neuer
unvollständiger Gruppen abgebrochen. Paketabstände von 1, 2 und 3 ms beseitigten
den Fehler nicht; die ursprüngliche Einstellung von 1 ms wurde wiederhergestellt.

Nachweise: [TD 1 ms](qa/controller251-new-supply-dim10.json),
[TD 2 ms](qa/controller251-new-supply-gap2-dim10.json),
[TD 3 ms](qa/controller251-new-supply-gap3-dim10.json),
[unabhängig](qa/controller251-new-supply-standalone-black10.json),
[andere Ausgaben gestoppt](qa/controller251-new-supply-standalone-quiet-black10.json).

## Verbleibender Zustand

`.251` ist erreichbar, aber weiter aus der Live-Ausgabe genommen. Helligkeit 0,7,
Zielrate 30 und Paketabstand 1 ms sind wiederhergestellt. Keine Firmware oder
Empfängerkonfiguration wurde verändert. `.244` und `.253` laufen wieder.
`.253` empfing anschließend 450 vollständige Frames in 15,004 Sekunden:
**29,99 FPS**, ohne neue unvollständige, veraltete, verworfene oder überschriebene
Frames und ohne Queue-Drops.
[Messung](qa/performance-after251-supply-contract.json).

TouchDesigner meldet keine Fehler oder Warnungen. Das gespeicherte Release-TOE
ist unverändert (SHA256
`C4B629A00848601ABD08D7055453C62A52B20CD060668888EE11DC28C28F475B`).

Die Quelltextprüfung und ihre Versionsgrenze stehen im
[Empfänger-Quelltextabgleich](qa/controller251-receiver-source-review.md).
