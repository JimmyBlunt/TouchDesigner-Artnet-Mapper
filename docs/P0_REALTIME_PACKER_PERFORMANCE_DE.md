# P0: Echtzeit-Packer und Sender-Performance

Stand: 26. August 2026
Scope: Offline-Implementierung und Regression; kein Art-Net-Hardwaretest, kein
TOE-Save.

## Ausgangsproblem

Der bisherige `onFrameStart`-Pfad führte für jeden Controller erneut folgende
Arbeiten aus:

1. `controller_config` und `segment_config` vollständig in Dataclasses lesen,
2. den Routerplan neu validieren und aufbauen,
3. aus drei CHOP-Kanälen ein Tupel mit 3.744 RGB-Tupeln erzeugen,
4. alle Controller packen, obwohl nur ein Controller-Packer abgefragt wurde,
5. den Script CHOP mit `cook(force=True)` auch nach einem normalen Frame-Cook
   erneut berechnen,
6. dessen Integerwerte nochmals in `bytes` zurückkonvertieren.

Die reine Referenzoperation benötigte offline bereits ungefähr 8 bis 11 ms. Die
in TouchDesigner zusätzlich erforderlichen CHOP-Schreibvorgänge und erzwungenen
Render-Cooks sind darin noch nicht enthalten.

## Umsetzung

`pixelblaze_mapper/realtime_packer.py` kompiliert einen bereits validierten
`RouterPlan` in feste Pixel-Schreiboperationen. Segmentauswahl, Zielposition,
Reverse und Farbkanalreihenfolge werden nur bei einer Änderung der beiden
Konfigurationstabellen neu aufgelöst.

Der Live-Sender:

- liest `source_select` einmal pro Sendeframe,
- erzeugt kein 3.744-Pixel-Zwischentupel,
- packt nur die aktivierten Controller,
- erzeugt alle Universe-Payloads aus demselben Quellsnapshot,
- verwendet ausschließlich nicht erzwungene Dependency-Cooks,
- sendet weiter Sequence 0 und exakt 510 Bytes je ArtDMX-Universe.

Die sichtbaren Controller-Script-CHOPs bleiben als deaktivierte Diagnose- und
DMX-Referenz vorhanden. Auch sie verwenden den kompilierten Packer, falls sie
manuell betrachtet werden; der Live-Sender ist nicht mehr von ihren
CHOP-Schreibschleifen abhängig.

## Read-only-Telemetrie

`artnet_510_sender_callbacks.module.status()` liefert zusätzlich:

- Tick- und Rate-Skip-Anzahl,
- Sendeframe- und Paketzähler,
- letzte, mittlere und maximale Sendelaufzeit,
- gemessene Sendefrequenz,
- Packanzahl,
- letzte, mittlere und maximale Packlaufzeit,
- Anzahl der Routerplan-Neukompilierungen.

Die Werte ändern keine Konfiguration und aktivieren keine Ausgabe.

## Offline-Benchmark

Aufruf:

```text
python tools/benchmark_realtime_packer.py --iterations 500
```

Ergebnis des Abschlusslaufs auf dem Entwicklungsrechner:

| Pfad | Median |
|---|---:|
| bisheriger Referenzpacker, alle Controller | 10,528 ms |
| kompiliert, alle Controller | 6,022 ms |
| kompiliert, nur aktuell relevanter WS-Controller | 3,037 ms |

- alle Controller: **42,8 % kürzer**
- nur WS-Controller: **71,2 % kürzer**
- Payloads: **byte-identisch**

Die absoluten Zeiten schwanken mit Systemlast. Entscheidend sind Byte-Identität
und der innerhalb desselben Prozesses gemessene relative Unterschied.

## Regression

- 251 Tests bestanden,
- 4 bereits vorhandene erwartete Fehler,
- keine unerwarteten Fehler,
- eingebettete TouchDesigner-Callbacktexte separat kompiliert,
- exakte 510 Bytes, GRB/Reihenfolge, Helligkeit, Rundung, Clamping, Reverse,
  reservierte schwarze Bereiche und Sequence 0 verifiziert.

## Verbleibende Risiken und Live-Abnahme

1. Der reale TouchDesigner-Cookgewinn muss nach Builderintegration in der neuen
   Core-Datei gemessen werden; der Offline-Benchmark enthält keine GPU- oder
   Viewer-Kosten.
2. Der nicht erzwungene `source_select`-Cook muss in der laufenden Timeline
   bestätigen, dass pro Frame der aktuelle Renderstand gelesen wird.
3. Hardwareausgabe muss beaufsichtigt bei geringer Helligkeit kontrollieren,
   dass Universe-Grenzen und Farbreihenfolge unverändert sind.
4. Falls die Renderkette selbst weiterhin unter 60 FPS bleibt, verhindert der
   schnellere Packer zwar zusätzliche Blockierung, erzeugt aber keine neuen
   Renderframes zwischen langsamen GPU-Cooks.
