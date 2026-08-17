# Phase 2 – Read-only-Analyse der DMX-/Art-Net-Kette

Stand: 13. August 2026  
Prüfmodus: Live-Projekt über TouchDesigner-MCP, ausschließlich lesend  
Produktionsprojekt gespeichert/verändert: **nein**  
Ergebnis: Alle hier untersuchten Produktionsknoten melden **0 Fehler**.

## 1. Verifizierte Produktionskette

```text
/project1/pixelblaze_mapper/map_active_out       DAT 3715 × 4
  -> /project1/selectDat                         DAT 3715 × 4
  -> /project1/evaluate1                         DAT 3715 × 4
  -> /project1/LedMap                            CHOP tx,ty,tz × 3714
  -> /project1/null4                             CHOP tx,ty,tz × 3714
  -> /project1/topto1                            CHOP r,g,b × 3714
  -> /project1/math3
  -> /project1/merge3
  -> /project1/null5                             CHOP r,g,b × 3714
       ├-> /project1/select4                     g
       ├-> /project1/select5                     r
       └-> /project1/select3                     b
             -> /project1/merge2                 g,r,b × 3714
             -> /project1/shuffle1               1 Kanal × 11142 Samples
             -> /project1/rename1                Kanal „Universe“
             -> /project1/lookup1                22 Kanäle × 510 Samples
                  ^
                  |
             /project1/Universe_Config           22 Kanäle × 510 Samples
                  ^
                  |
             /project1/DMX_Universes             DAT 23 × 3
             -> /project1/rename2
             -> /project1/select1
             -> /project1/math2
             -> /project1/merge1                 22 Kanäle × 510 Samples
             -> /project1/dmxout1                 Art-Net
                  ^
                  |
             /project1/dmxout1_routingtable       DAT 23 × 4
```

Die 3.715 DAT-Zeilen bestehen aus einer Headerzeile und 3.714 LED-Zeilen. Ab
`LedMap` entspricht jedes Sample exakt einem LED-Index. Das ist die entscheidende
Schnittstelle: Ändert sich die Anzahl der Map-Slots, ändert sich die Samplezahl
der kompletten RGB-Kette.

## 2. Abhängigkeiten vom Mapping bis zum Netzwerkpaket

### 2.1 LED-Index ist Streamposition

`map_active_out` hat die Spalten `index,tx,ty,tz`. Der aktuelle Datenstrom
verwendet 3.714 aufeinanderfolgende Slots. Ein fehlender MariMapper-Index muss
deshalb als eigener Nullpunkt erhalten bleiben; er darf nicht aus der Tabelle
entfernt werden. Andernfalls verschieben sich alle folgenden RGB-Werte und damit
die physische LED-Zuordnung.

Die sichere Invariante lautet:

```text
Map-Slot i == CHOP-Sample i == RGB-Pixel i == physische LED i
```

`[0,0,0]` bei einer Indexlücke reserviert den richtigen Streamplatz. Die drei
historischen BallsMatrix3-Lücken 894–896 ergeben daher 938 Slots, nicht 935.

### 2.2 Farbreihenfolge ist GRB

`null5` liefert die logischen Kanäle `r,g,b`. Die drei Select CHOPs ordnen sie
vor der Serialisierung explizit um:

| Node | selektierter Kanal | Position im Ausgabepixel |
|---|---:|---:|
| `/project1/select4` | `g` | 1 |
| `/project1/select5` | `r` | 2 |
| `/project1/select3` | `b` | 3 |

`merge2` führt sie in der Reihenfolge `g,r,b` zusammen. `shuffle1` serialisiert
die drei Kanäle zu einem flachen Stream mit

```text
flatSampleCount = pixelCount × 3
                = 3714 × 3
                = 11142
```

Diese Reihenfolge ist Produktionsverhalten und muss beim Auto-Konfigurieren
explizit als `Color order = GRB` dargestellt werden. Ein Import einer Map darf
die Farbreihenfolge nicht implizit ändern.

### 2.3 Universumsaufteilung

Ein DMX-Universum kann zwar 512 Kanäle tragen, ein vollständiges RGB-Pixel
benötigt aber drei Kanäle. Diese Realisierung verwendet deshalb:

```text
channelsPerPixel       = 3
usableChannelsUniverse = floor(512 / 3) × 3 = 510
pixelsPerUniverse      = 170
universeCount          = ceil(pixelCount / 170)
```

Für 3.714 Pixel:

```text
universeCount = ceil(3714 / 170) = 22
lastStart      = 21 × 170         = 3570
lastPixels     = 3714 - 3570      = 144
lastChannels   = 144 × 3          = 432
```

Die DMX-Kanäle 511 und 512 jedes Universums bleiben unbenutzt. Dadurch wird nie
ein RGB-Pixel auf zwei Universen verteilt.

### 2.4 `/project1/DMX_Universes`

Die tatsächliche Table-DAT-Größe ist **23 × 3**:

```text
Universe,index,pixel
0,0,170
1,170,170
...
20,3400,170
21,3570,144
```

Die ersten 21 Universen enthalten je 170 Pixel. Universum 21 enthält die
verbleibenden 144 Pixel.

Wichtiger Befund: Der Parameterdialog der Table DAT meldet für `rows` noch den
veralteten Wert 9. Maßgeblich ist zur Laufzeit `numRows == 23`, nicht dieser
stale Parameterwert. Validierung und Generator dürfen deshalb nicht auf einen
manuell gepflegten Rows-Parameter vertrauen, sondern müssen den tatsächlichen
Tabelleninhalt prüfen.

### 2.5 `/project1/Universe_Config` und Lookup

`Universe_Config` ist ein Script CHOP, liest `DMX_Universes` und erzeugt die 22
Indexkanäle `Universe0` bis `Universe21`, jeweils mit 510 Samples. `lookup1`
verwendet diese Indizes, um den serialisierten 11.142-Sample-GRB-Strom in
Universen zu zerlegen. Hinter `lookup1` liegen somit 22 Kanäle mit je 510
Samples vor.

Die exakte Verdrahtung und Parametrierung lautet:

```text
shuffle1
  -> rename1                    rename: * -> Universe

Universe_Config (Input 0) ─┐
                           ├-> lookup1 -> rename2
rename1         (Input 1) ─┘

lookup1:
  index1    = 0
  index2    = 11141
  chanmatch = onetomany

rename2:
  Universe*Universe -> Universe*
```

`lookup1.index2 == 11141` ist exakt `3 × 3714 - 1` und damit eine weitere
harte Abhängigkeit von der aktuellen Pixelzahl. Ein Auto-Rebuild muss diesen
Wert auf `3 × P - 1` setzen oder die Lookup-Domäne vollständig aus der aktuellen
Samplezahl ableiten. Andernfalls skaliert beziehungsweise adressiert eine neue
Map gegen die alte 3.714-Pixel-Domäne.

Die letzte Nutzlast umfasst nur 432 Werte, während der gemessene Ausgangskanal
510 Samples lang ist. Damit existieren 78 Positionen außerhalb der Nutzlast.
**Das aktuelle Callback-Verhalten dieser 78 Samples konnte in diesem
Read-only-Durchgang nach einem MCP-Neustartproblem nicht mehr direkt aus dem
Scripttext verifiziert werden.** Vor einer produktiven Neukonfiguration ist
deshalb zwingend zu prüfen, ob `Universe_Config` sie nullt, mit einem Randwert
füllt oder ob erst eine nachgeschaltete Stufe sie maskiert. Das Zielverhalten des
neuen Generators muss deterministisch null sein und darf keine Werte eines
folgenden Universums referenzieren.

Hinter `rename2` teilt sich die Kette in einen aktiven und einen reservierten
Pfad:

```text
rename2
  ├-> select1  channames=Universe* -> math2 ─┐
  └-> select2  channames=__none__ (0 Kanäle) ├-> merge1 -> dmxout1
                                               ┘
```

`math2` ist damit der aktive Werteskalierungsweg. Seine genaue Range-/Gain-
Parametrierung konnte nach dem genannten MCP-Neustartproblem nicht abschließend
ausgelesen werden und ist vor einer Implementierung separat als Baseline zu
sichern. `select2` ist derzeit ein
leerer, reservierter Bypass; weil sein Filter `__none__` keinen Kanal trifft,
beeinflusst er die Ausgabe nicht. `merge1` empfängt `[math2, select2]` und gibt
22 Kanäle × 510 Samples aus.

Für eine variable Universumszahl müssen alle aktiven Kanalfilter
Wildcard-basiert (`Universe*`) bleiben. Fest ausgeschriebene Listen würden neue
Universen lautlos abschneiden. Ebenso muss der Bypass bewusst leer bleiben oder
eine explizite Betriebsart bekommen; er darf nicht versehentlich dieselben
Universen parallel einspeisen.

### 2.6 Art-Net-Routing

`/project1/dmxout1` ist aktiv und nutzt Art-Net mit:

| Einstellung | Live-Wert |
|---|---|
| Ziel-/Netzadresse | `10.0.0.244` |
| lokale Adresse | `10.0.0.173` |
| UDP-Port | `6454` |
| Routing-Tabelle | `/project1/dmxout1_routingtable` |

Die Routing-Tabelle ist **23 × 4**, Header plus 22 Datenzeilen:

```text
channel,net,subnet,universe
Universe0,0,0,0
Universe1,0,0,1
...
Universe19,0,1,3
Universe20,0,1,4
Universe21,0,1,5
```

Die aktuelle Zuordnung folgt für einen nullbasierten logischen Universumsindex
`u` diesen Formeln:

```text
net      = floor(u / 256)
subnet   = floor(u / 16) mod 16
universe = u mod 16
```

Damit liegt `Universe15` auf `0/0/15`, `Universe16` auf `0/1/0` und
`Universe21` auf `0/1/5`.

## 3. Sichere Regeln für Map-Import und -Erweiterung

### Muss-Bedingungen vor einem Apply

1. Der Parserstatus ist gültig; alle Koordinaten sind endlich und konsistent 2D
   oder 3D.
2. Die interne Liste ist streng indexadressiert und hat exakt
   `maxIndex + 1` Slots.
3. Negative und doppelte Indizes blockieren Apply.
4. Fehlende Indizes bleiben als `[0,0,0]` erhalten und erzeugen eine Warnung;
   sie zählen vollständig zur Pixel- und DMX-Länge.
5. Der aktive Mapping-Hash sowie die komplette aktive DMX-Konfiguration werden
   unmittelbar vor Apply als Rollback-Snapshot erfasst.
6. Die neue Pixelzahl wird bis zum Ende der Farbkette simuliert:
   `P -> 3P -> ceil(P/170) -> lastPixels`.
7. Kein Universum darf mehr als 170 RGB-Pixel oder 510 aktive Kanäle enthalten.
8. Die Kanalnamen aus Universe_Config, Lookup-Ausgabe, Filterstrecke,
   `merge1` und Routing-Tabelle müssen exakt dieselbe Menge
   `Universe0..UniverseN-1` bilden.
9. `lookup1.index2` entspricht exakt `3 × pixelCount - 1`; bei einer leeren Map
   bleibt Output deaktiviert, statt einen negativen Index zu setzen.
10. Art-Net-Zieladresse, lokale NIC, Port und Farbreihenfolge werden niemals durch
   einen Mapping-Import verändert.
11. Eine Pixelzahländerung benötigt eine getrennte, gut sichtbare Bestätigung
    für **Map anwenden + DMX neu konfigurieren**. Reine Vorschau bleibt vorher
    möglich.

### Erweiterung einer vorhandenen Map

Anhängen ist sicher, wenn neue LEDs neue, aufeinanderfolgende Indizes ab dem
bisherigen `pixelCount` erhalten. Einfügen in der Mitte ist technisch möglich,
verschiebt aber alle nachfolgenden physischen Adressen und muss deshalb als
risikoreiche Neuverkabelung behandelt werden. Zusammenführen sollte daher drei
explizite Modi anbieten:

- **Replace:** aktive Map vollständig ersetzen;
- **Append:** neue Map ab dem nächsten freien Index anhängen;
- **Place at index:** bewusster Startindex, mit Kollisionsprüfung und sichtbarer
  Vorschau der verschobenen/überschriebenen Bereiche.

Ohne ausdrückliche Zustimmung darf nur `Append` automatisch neue Slots erzeugen.
Koordinatennormalisierung (Fill/Contain) und Index-/DMX-Adressierung bleiben
getrennt: Fit verändert Positionen, nie die Reihenfolge oder Pixelzahl.

## 4. Vorschlag für eine intuitive DMX-Konfiguration

### 4.1 UI-Bereich „LED Output / Art-Net“

Der Mapper sollte einen eigenen, zunächst eingeklappten Bereich erhalten:

| Feld | Standard/Aktuell | Verhalten |
|---|---|---|
| Output enabled | aktueller Zustand | Master-Schutz; während Rebuild kurz aus |
| Protocol | Art-Net | read-only, solange kein anderer Output implementiert ist |
| Pixel count | aus Map | read-only |
| Channels per pixel | 3 | RGB |
| Color order | GRB | explizites Menü, aktuelle Produktion |
| Start universe | 0 | logischer Offset |
| Pixels per universe | Auto: 170 | aus 512/3, optional kleiner |
| Required universes | Auto | `ceil(P / pixelsPerUniverse)` |
| Last universe pixels | Auto | Restwert |
| Target address | 10.0.0.244 | getrennt vom Mapping speichern |
| Local interface | 10.0.0.173 | Dropdown aus verfügbaren NICs |
| Port | 6454 | Art-Net-Standard |

Darunter sollte eine Vorschautabelle alle erzeugten Zeilen zeigen:

```text
Logical | Channel    | Pixels | DMX used | Net | Subnet | Universe | Status
0       | Universe0  | 170    | 510      | 0   | 0      | 0        | OK
...
21      | Universe21 | 144    | 432      | 0   | 1      | 5        | OK
```

Der Benutzer sieht damit vor Apply sowohl die logische als auch die Art-Net-
Adresse. Die Begriffe „Universe 16“ und „Subnet 1 / Universe 0“ werden nicht
verwechselt.

### 4.2 Auto-Berechnung

Für `P > 0`, `C = channelsPerPixel` und maximal 512 DMX-Slots:

```text
pixelsPerUniverse = floor(512 / C)
usedPerFull        = pixelsPerUniverse × C
universeCount      = ceil(P / pixelsPerUniverse)

for logical in 0 .. universeCount-1:
    startPixel = logical × pixelsPerUniverse
    pixelCount = min(pixelsPerUniverse, P - startPixel)
    usedSlots  = pixelCount × C
    artnet     = encode(startUniverse + logical)
```

Für diese RGB-Anlage ergibt das 170 Pixel und 510 Slots pro vollem Universum.
Die beiden nicht nutzbaren Slots bleiben immer null.

### 4.3 Validierung vor Commit

Der Konfigurator baut zunächst ausschließlich temporäre Tabellen und prüft:

- Tabellenzeilen und logische Universen sind lückenlos und eindeutig;
- `startPixel` jeder Zeile entspricht der Summe aller vorherigen Pixel;
- Summe `pixel` entspricht exakt der Map-Länge;
- letzter Bereich endet exakt bei `P`, weder Überlauf noch Verlust;
- jeder `usedSlots`-Wert liegt zwischen 1 und 510;
- alle erzeugten CHOP-Kanäle haben genau 510 Samples;
- die 78 nicht verwendeten Slots des letzten aktuellen Universums werden nach
  MCP-Neustart direkt geprüft; die Neukonfiguration setzt Padding garantiert
  auf null;
- Lookup-Domäne ist `0..3P-1` und nicht die alte feste Baseline;
- Kanalnamen und Routing-Zeilen stimmen 1:1 überein;
- Art-Net-Adressen liegen im zulässigen Bereich und kollidieren nicht;
- Ziel-IP und lokale IP sind syntaktisch gültig; die lokale IP gehört zu einem
  verfügbaren Netzwerkadapter;
- `dmxout1` sieht nach Umschaltung exakt die erwartete Kanal-/Samplezahl und
  meldet keinen neuen Fehler.

Erst ein grüner Dry Run aktiviert **Apply DMX Configuration**.

### 4.4 Atomarer Apply und Rollback

Empfohlene Transaktion:

1. Snapshot von `map_active`, `DMX_Universes`, Routing-Tabelle, allen relevanten
   Filter-/Rename-Parametern sowie den Netzwerkparametern von `dmxout1` anlegen.
2. DMX-Ausgabe deaktivieren, damit kein halbfertiger Frame gesendet wird.
3. Neue Mapping-Tabelle und beide temporär validierten DMX-Tabellen einsetzen.
4. `Universe_Config` forcieren, danach `lookup1` bis `merge1` kochen.
5. Live-Invarianten erneut prüfen: Map-Samples `P`, flach `3P`, Universen `N`,
   je 510 Samples, Routing `N` Zeilen, 0 neue Fehler.
6. Einen vollständig nullgesetzten Frame senden, danach die DMX-Ausgabe wieder
   aktivieren und den ersten Animationsframe senden.
7. Snapshot als „last known good“ speichern und Transaktion protokollieren.

Bei jeder Exception oder Abweichung:

1. Ausgabe sofort deaktivieren;
2. sämtliche Tabellen und Parameter aus dem Snapshot wiederherstellen;
3. Kette forcieren und dieselben Invarianten gegen die alte Konfiguration prüfen;
4. erst dann alte Ausgabe wieder aktivieren;
5. UI-Status `ROLLED BACK` mit konkretem Prüffehler anzeigen.

Ein Projekt-Save darf erst nach erfolgreicher Live-Verifikation erfolgen, nicht
innerhalb der Umschalttransaktion.

## 5. Empfohlene Schutzklassen

### Grün – ohne DMX-Umbau

- gleiche Pixelzahl wie aktiv;
- identische Indexmenge;
- nur Koordinaten oder Fill/Contain geändert;
- Universums- und Netzwerkkonfiguration bleibt unverändert.

### Gelb – DMX-Rebuild mit Bestätigung

- Pixel wurden nur am Ende angehängt oder entfernt;
- daraus folgt eine neue letzte Universumsbelegung oder Universumszahl;
- Ziel-IP, lokales Interface, Port und Farbreihenfolge bleiben gleich.

### Rot – getrennte Expertenbestätigung

- Indizes in der Mitte eingefügt, entfernt oder umsortiert;
- Startuniversum, Art-Net-Adresse, Farbreihenfolge oder Kanäle pro Pixel ändern
  sich;
- Universumsadressen kollidieren oder lokale NIC ist nicht verfügbar;
- Import würde die maximale konfigurierte Anlagenkapazität überschreiten.

## 6. Konkrete Abnahmetests für Phase 2

| ID | Test | Erwartung |
|---|---|---|
| D01 | bestehende 3.714er Map | 22 × 510, letzte Zeile 144 Pixel |
| D02 | BallsMatrix3 mit 938 Slots | 6 Universen; 170,170,170,170,170,88 Pixel |
| D03 | exakt 170 Pixel | 1 Universum, 510 aktive Slots |
| D04 | 171 Pixel | 2 Universen, 170 + 1 Pixel |
| D05 | Indexlücke | Slot bleibt erhalten; keine Streamverschiebung |
| D06 | ungültiger/duplizierter Index | Apply blockiert |
| D07 | falscher Filter `Universe0..5` | Validator erkennt fehlende Kanäle |
| D08 | nicht-null Padding | Validator blockiert Commit |
| D09 | nicht verfügbare lokale IP | Output bleibt deaktiviert, Rollback |
| D10 | provozierter Cook-Fehler | vollständiger Rollback, alte 22 Universen intakt |
| D11 | GRB-Testbild | LED 0 sendet G,R,B auf DMX 1,2,3 |
| D12 | Subnet-Grenze | Logical 15→0/0/15, 16→0/1/0 |

Hinweis für D02: 938 zählt die drei fehlenden BallsMatrix3-Indizes als echte
Slots. Bei 170 Pixeln pro Universum sind `ceil(938/170) = 6` Universen nötig;
das letzte enthält 88 Pixel beziehungsweise 264 aktive Kanäle.

## 7. Fazit

Die bestehende Kette ist intern konsistent und fehlerfrei: 3.714 Map-Slots,
11.142 GRB-Werte, 22 Universen mit 510 Samples und 22 passende Art-Net-Routen.
Die wichtigste technische Verbesserung ist kein neuer Mapping-Parser, sondern
eine transaktionale DMX-Konfiguration, die Pixelzahl, Kanalnamen, Lookup-Indizes
und Routing als **eine atomare Einheit** behandelt. Der Mapping-Import darf
Koordinaten und Slotzahl vorschlagen; Netzadresse, NIC, Port und Farbreihenfolge
bleiben bewusst separate Output-Einstellungen.

## 8. Noch einmal read-only zu verifizieren

Die folgenden beiden Detailpunkte sind keine offenen Architekturentscheidungen,
sondern konkrete Baseline-Messungen für den nächsten MCP-Lauf:

1. Callback-/Scripttext von `/project1/Universe_Config` und die tatsächlichen
   Werte der Samples 432–509 in `Universe21`;
2. vollständiger Parameterdump von `/project1/math2`, insbesondere Range, Gain,
   Clamp und die vom DMX Out erwartete Werteskala.

Bis diese beiden Messungen vorliegen, dürfen die entsprechenden Nodes nicht
automatisch neu erzeugt oder überschrieben werden. Alle übrigen Pfade, Größen,
Kanalnamen, Lookup-Parameter, Tabelleninhalte und Netzwerkwerte dieses Dokuments
wurden live verifiziert.
