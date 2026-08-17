# Phase 2 UI-Spezifikation: DMX-Ausgabe, Kamera und Hintergrundfoto

Stand: 13. August 2026  
Status: UI-/Integrationsentwurf, keine Produktionsänderung  
Zielkomponente: `/project1/pixelblaze_mapper`

## 1. Ziel

Phase 2 ergänzt den portablen Mapper um eine kompakte, sichere Art-Net-/DMX-Konfiguration. Eine importierte oder erweiterte Map soll automatisch die benötigte Kapazität berechnen, aber die aktive LED-Ausgabe erst nach verständlicher Prüfung und expliziter Bestätigung verändern.

Die Konfiguration muss drei Dinge gleichzeitig sichtbar machen:

1. **Was benötigt die aktuelle Map?** Pixelzahl, Kanäle und Universen.
2. **Was ist als Entwurf konfiguriert?** Netzwerkziel, Startadresse und Allokation.
3. **Was läuft tatsächlich?** zuletzt angewandte Map- und DMX-Konfiguration.

Der Mapper und die DMX-Konfiguration teilen sich ein Zustandsmodell, besitzen aber getrennte Entwürfe. Dadurch kann man eine Map gefahrlos importieren und in 3D prüfen, ohne die reale Ausgabe automatisch umzubauen.

## 2. Verifizierte Live-Baseline

| Eigenschaft | Aktueller Wert |
|---|---:|
| Aktive Map | 3.714 Pixel, 3D |
| Pixeltyp | RGB, 3 Kanäle pro Pixel |
| Benötigte DMX-Kanäle | 11.142 |
| Maximale RGB-Pixel pro Universum | 170 |
| Nutzkanäle pro vollem Universum | 510 |
| Universen | 22, fortlaufend 0 bis 21 |
| Letztes Universum | 144 Pixel / 432 Kanäle |
| Protokoll | Art-Net |
| Ausgabeformat | ein Paket pro CHOP-Kanal/Universum |
| Zieladresse | `10.0.0.244` |
| Lokale Adresse | `10.0.0.173` |
| Port | 6454 |
| Rate | 30 fps |
| Priorität | 100 |
| ArtSync | aktiv |

Die vorhandene Allokation entspricht:

```text
Universe0  = Pixel    0 .. 169
Universe1  = Pixel  170 .. 339
...
Universe20 = Pixel 3400 .. 3569
Universe21 = Pixel 3570 .. 3713  (144 Pixel)
```

Die Art-Net-Adresse wird aus einem fortlaufenden Port-Address-Wert `A` abgeleitet:

```text
Net      = floor(A / 256)
Subnet   = floor(A / 16) mod 16
Universe = A mod 16
```

Damit wird beispielsweise die fortlaufende Adresse 16 als `Net 0 / Subnet 1 / Universe 0` angezeigt.

## 3. Platzierung und Navigation

Die Oberfläche bleibt ein zusammengehöriger Mapper. Empfohlen wird eine kompakte obere Navigation:

```text
┌────────────────────────────────────────────────────────────────────┐
│ PIXELBLAZE PORTABLE MAPPER        MAP | PREVIEW | OUTPUT (DMX)    │
├────────────────────────────────────────────────────────────────────┤
│ aktiver Arbeitsbereich                                             │
├────────────────────────────────────────────────────────────────────┤
│ Map: 3714 / 3D   DMX: 22 universes / LIVE   Draft/Saved/Applied   │
└────────────────────────────────────────────────────────────────────┘
```

- **MAP** enthält Import, Quelltext, Fill/Contain und Export.
- **PREVIEW** vergrößert die 3D-Ansicht und zeigt Kamera-/Foto-Werkzeuge.
- **OUTPUT (DMX)** zeigt den nachfolgend beschriebenen Konfigurationsbereich.
- Der untere globale Status bleibt in allen Ansichten sichtbar.
- Ein farbiger Punkt neben `OUTPUT (DMX)` zeigt `LIVE`, `DRAFT`, `WARNING` oder `BLOCKED`.

Auf kleinen Fenstern kann OUTPUT als rechter Drawer über MAP erscheinen. Er darf den Editor nicht dauerhaft verkleinern. Die aktuelle 1280×800-Canvas bleibt die Zielgröße.

## 4. Kompaktes DMX-Panel

### 4.1 Vorgeschlagenes Layout

```text
┌ OUTPUT (DMX) ──────────────────────────────────────────────────────┐
│ LIVE  Art-Net · 10.0.0.244 · U0–U21 · 3714 RGB pixels · 30 fps   │
├ Map requirement ───────────────────────────────────────────────────┤
│ Source     [Applied map ▼]     Pixels [3714]    Format [RGB ▼]    │
│ Required   11,142 channels     22 universes     Last: 432 / 512   │
├ Address allocation ────────────────────────────────────────────────┤
│ [✓] Auto allocate             Start universe [0] Channel [1]     │
│ Range      U0 … U21           Capacity 3740 px   Spare 26 px      │
│ [▸ Show universe table]                                          │
├ Network ───────────────────────────────────────────────────────────┤
│ Mode [Art-Net Unicast ▼] Target [10.0.0.244] Local [10.0.0.173▼] │
│ Rate [30] fps                 [▸ Advanced]                         │
├────────────────────────────────────────────────────────────────────┤
│ ● DMX DRAFT MATCHES MAP       [REVERT] [REVIEW & APPLY OUTPUT]    │
└────────────────────────────────────────────────────────────────────┘
```

### 4.2 Immer sichtbare Felder

| Feld | Typ | Verhalten |
|---|---|---|
| Output enabled | Toggle | globales Senden an/aus; Umschalten benötigt Bestätigung, wenn LIVE |
| Source | Menu | `Applied map`, `Map draft`, später optional benannte Segmente |
| Pixel count | Read-only | aus der ausgewählten Map; niemals manuell überschreiben |
| Pixel format | Menu | Phase 2 zunächst `RGB (3 ch)`; `RGBW (4 ch)` sichtbar als später/disabled |
| Channel order | Menu | `RGB`, `RBG`, `GRB`, `GBR`, `BRG`, `BGR`; Standard `RGB` |
| Auto allocate | Toggle | berechnet fortlaufende Universen und Belegung automatisch |
| Start universe | Integer | fortlaufende Art-Net-Port-Address, Standard 0 |
| Start channel | Integer | 1-basiert; Standard 1; muss zum Pixelformat passen |
| Protocol mode | Menu | `Art-Net Unicast`, `Art-Net Broadcast`; aktueller Modus wird korrekt übernommen |
| Target address | IPv4 | Zielcontroller; bei Broadcast wird Broadcastadresse angezeigt/abgeleitet |
| Local interface | Menu | verfügbare lokale IPv4-Adapter, aktuelle Auswahl vorausgewählt |
| Frame rate | Integer | 1–60, Standard/LIVE 30 |

### 4.3 Advanced-Foldout

Der selten benötigte Bereich bleibt standardmäßig geschlossen:

| Feld | Standard | Regel |
|---|---:|---|
| UDP port | 6454 | 1–65535; Änderung erzeugt deutliche Warnung |
| Art-Net priority | 100 | 0–200 |
| ArtSync | an | Hinweis, dass der Empfänger ArtSync unterstützen muss |
| Channels per universe | 512 | für RGB effektiv nur 510 nutzbar |
| Universe naming | `Universe{n}` | read-only Vorschau der CHOP-Kanalnamen |
| FPS limit when preview hidden | 30 | verhindert unnötige Netzwerkbelastung |
| Blackout before reconfigure | an | sendet bei Adresswechsel optional einen kurzen Null-Frame |

`Blackout before reconfigure` darf erst implementiert werden, wenn sein zeitlicher Ablauf auf der realen Installation getestet wurde. Bis dahin bleibt der Schalter sichtbar, aber deaktiviert und mit `Phase 3` markiert.

## 5. Auto-Allokation

### 5.1 Grundformeln

Für `P` Pixel, `C` Kanäle pro Pixel, maximal 512 DMX-Kanäle und Startkanal `S`:

```text
firstCapacityChannels = 512 - (S - 1)
firstCapacityPixels   = floor(firstCapacityChannels / C)
remainingPixels       = max(0, P - firstCapacityPixels)
pixelsPerUniverse     = floor(512 / C)
requiredUniverses     = 1 + ceil(remainingPixels / pixelsPerUniverse), falls P > 0
```

Für RGB und `Start channel = 1`:

```text
pixelsPerUniverse = floor(512 / 3) = 170
requiredUniverses = ceil(P / 170)
```

Bei 3.714 Pixeln entstehen 22 Universen. 21 volle Universen enthalten je 170 Pixel; das letzte enthält 144 Pixel. Die Kanäle 511 und 512 bleiben in vollen RGB-Universen unbenutzt, damit kein Pixel über eine Universumsgrenze geteilt wird.

### 5.2 Startkanal

- Gültiger Wertebereich: 1 bis 512.
- Ein Pixel darf niemals über zwei Universen aufgeteilt werden.
- Empfohlen wird Startkanal 1.
- Für RGB muss ab Startkanal mindestens ein vollständiges 3-Kanal-Pixel Platz haben.
- Der UI zeigt die tatsächliche erste Belegung, beispielsweise `U4 / Ch 4–510`.
- Optionaler Schalter `Align first pixel to format` korrigiert eine unpassende Adresse auf den nächsten vollständigen Slot.

### 5.3 Importierte und erweiterte Maps

Nach jedem gültigen Import wird die benötigte Ausgabe als **DMX Draft** neu berechnet:

- Gleiche Pixelzahl und gleiches Format: bestehende 22-Universen-Allokation bleibt unverändert.
- Weniger Pixel: benötigte Universen werden reduziert; die UI warnt, dass bislang genutzte Enduniversen nach Apply entfallen.
- Mehr Pixel: fortlaufende Universen werden ergänzt und als `NEW` markiert.
- Nur Koordinaten geändert: DMX-Allokation bleibt `UNCHANGED`.
- 2D/3D beeinflusst DMX nicht; maßgeblich sind Pixelzahl und Pixelformat.
- MariMapper-Indexlücken `[0,0,0]` zählen weiterhin als Pixelslots und erhalten daher DMX-Adressen.
- Doppelte Koordinaten zählen als getrennte LEDs, weil der Arrayindex die elektrische Reihenfolge definiert.

### 5.4 Universe-Tabelle

Der Foldout zeigt eine kompakte, nicht standardmäßig editierbare Tabelle:

| Output channel | Net | Subnet | Universe | Pixel start | Pixel count | DMX range | Zustand |
|---|---:|---:|---:|---:|---:|---|---|
| Universe0 | 0 | 0 | 0 | 0 | 170 | 1–510 | LIVE |
| … | … | … | … | … | … | … | … |
| Universe21 | 0 | 1 | 5 | 3570 | 144 | 1–432 | LIVE |

Bei erweitertem Mapping werden zusätzliche Zeilen cyan als `NEW` markiert. Zeilen, die beim Verkleinern entfallen, erscheinen grau durchgestrichen als `REMOVE AFTER APPLY`.

Ein optionaler manueller Modus darf Universen verschieben oder reservieren. Er ist nicht der Standard und zeigt dauerhaft `MANUAL ALLOCATION`, weil automatische Map-Erweiterungen dann nicht ohne Konfliktentscheidung möglich sind.

## 6. Validierung und Fehlerzustände

### 6.1 Stufen

| Stufe | Farbe | Wirkung |
|---|---|---|
| OK | Grün | Apply möglich |
| Info | Blau | keine Aktion nötig |
| Warning | Gelb | Apply möglich, aber Review erforderlich |
| Blocked | Rot | Apply deaktiviert; Live-Ausgabe bleibt unverändert |

### 6.2 Blockierende Fehler

- Pixelzahl ist 0 oder nicht validiert.
- Map-Draft enthält gemischte Dimensionen, NaN/Infinity oder Parserfehler.
- `Start universe` liegt außerhalb des unterstützten Art-Net-Port-Address-Bereichs.
- Berechnetes Enduniversum überschreitet die Protokollgrenze.
- Startkanal lässt kein vollständiges Pixel mehr zu.
- Zwei manuelle Allokationsblöcke überlappen sich.
- Zieladresse oder lokaler Adapter ist syntaktisch ungültig.
- Die erzeugte Routingtabelle stimmt nicht mit der Zahl der Universe-CHOP-Kanäle überein.
- Erwartete Kanalkapazität ist kleiner als `Pixelcount × channelsPerPixel`.
- Apply-Transaktion kann keinen vollständigen Snapshot der Live-Konfiguration erzeugen.

### 6.3 Warnungen

- Pixelzahl weicht von der aktiven 3.714-Pixel-Map ab.
- Anzahl der Universen ändert sich.
- Ziel-IP, lokaler Adapter, Startuniversum oder Framerate ändert sich.
- Zieladresse ist nicht auf dem Subnetz des gewählten lokalen Adapters.
- Netzwerk-Erreichbarkeit konnte nicht geprüft werden. Das ist eine Warnung, kein Beweis für einen Fehler.
- Broadcast ist gewählt und erzeugt erhöhte Netzlast.
- ArtSync ist aktiv, Unterstützung des Empfängers ist unbekannt.
- Letztes Universum ist nur teilweise belegt; dies ist normalerweise informativ, nicht kritisch.

### 6.4 Verständliche Meldungen

Fehlertexte nennen stets Ursache, Ist-Wert und Lösung:

```text
BLOCKED: 4,200 RGB pixels require 25 universes (U0–U24),
but only U0–U21 are staged. Enable Auto Allocate or add 3 universes.
```

```text
WARNING: Applying this draft adds Universe22–Universe24 and changes
the active pixel count from 3,714 to 4,200. Current output remains live.
```

## 7. Apply-, Review- und Revert-Ablauf

### 7.1 Zustände

```text
LIVE CONFIG
    │ Änderung an Map oder Output
    v
DMX DRAFT ──validate──> READY TO REVIEW
    │ Fehler                  │ Review & Apply
    v                         v
BLOCKED                  APPLYING ATOMICALLY
                              │ Erfolg
                              v
                          NEW LIVE CONFIG
```

### 7.2 Review-Dialog

`REVIEW & APPLY OUTPUT` öffnet eine Zusammenfassung, bevor etwas verändert wird:

```text
Map             3714 → 4200 pixels
Universes       22 → 25 (U0–U24)
Destination     10.0.0.244 (unchanged)
Local adapter   10.0.0.173 (unchanged)
Rate            30 fps (unchanged)
Tables rebuilt  DMX_Universes + routing table + 25 CHOP channels

[Cancel]                         [Apply Map + DMX]
```

### 7.3 Atomarer Apply

Apply darf nicht schrittweise sichtbare Zwischenzustände erzeugen. Vorgesehener Ablauf:

1. Map-Draft und DMX-Draft erneut validieren.
2. Snapshot aus `map_active`, `DMX_Universes`, Routingtabelle und relevanten DMX-Out-Parametern erstellen.
3. Neue Tabellen und CHOP-Kanäle vollständig in Staging-Nodes erzeugen.
4. Anzahl, Namen und Kanalbelegung gegeneinander prüfen.
5. Map und Output in einem kontrollierten Umschaltpunkt aktivieren.
6. Einen Frame prüfen und Status/Hashes aktualisieren.
7. Bei jedem Fehler automatisch den Snapshot zurückschalten.

Die Produktionsintegration darf erst nach einem Test mit deaktivierter oder physisch sicherer Ausgabe erfolgen.

### 7.4 Revert

- `REVERT DRAFT` verwirft nur noch nicht angewandte Änderungen.
- `ROLL BACK LIVE` ist ein separater, stärker geschützter Befehl im Overflow-Menü.
- Rollback stellt Map, Allokation und Netzwerkparameter als zusammengehörigen Snapshot wieder her.
- Das UI zeigt danach `ROLLED BACK TO <timestamp/hash>`.
- Revert und Rollback dürfen nie synonym beschriftet sein.

## 8. Zusammenspiel mit der Mapper-UI

Die aktuelle Mapper-UI besitzt bereits `Draft`, `Saved`, `Applied` und `Apply to LEDs`. Phase 2 präzisiert diese Semantik:

| Situation | Mapper-Button | DMX-Panel |
|---|---|---|
| Koordinaten geändert, Pixelzahl gleich | `APPLY MAP` | `UNCHANGED / 22 universes` |
| Pixelzahl geändert | `REVIEW MAP + DMX` | automatisch geöffnet, neuer Draft |
| Nur Netzwerk/Startadresse geändert | unverändert | `REVIEW & APPLY OUTPUT` |
| Map ungültig | deaktiviert | Bedarf nicht berechenbar, BLOCKED |
| Map gültig, DMX ungültig | Preview/Export erlaubt | reales Apply BLOCKED |

Empfohlene gemeinsame Statusleiste:

```text
MAP  ● SAVED / ● APPLIED     OUTPUT  ● LIVE / ○ DRAFT     3714 RGB / 22 U
```

Die bisherige rote Apply-Zone bleibt erhalten. Bei unveränderter Pixelzahl führt sie nur den Map-Apply aus. Bei geänderter Pixelzahl öffnet sie automatisch den kombinierten Review-Dialog und darf die DMX-Anpassung nicht überspringen.

## 9. Vorgesehene TouchDesigner-Schnittstelle

Empfohlener isolierter Bereich:

```text
/project1/pixelblaze_mapper
  /ui
  /preview3d
  /output_config
    config_live          (Table DAT)
    config_draft         (Table DAT)
    universe_live        (Table DAT)
    universe_draft       (Table DAT)
    routing_draft        (Table DAT)
    validation           (Table DAT)
    controller           (Text DAT / Extension)
    ui_panel             (Container COMP)
    ui_preview           (OP Viewer TOP)
```

Vorgeschlagene öffentliche Parameter auf `output_config`:

```text
Enabled              Toggle
Protocol             Menu: artnet_unicast / artnet_broadcast
Targetaddress        String
Localaddress         Menu/String
Pixelcount           Int (read-only/controlled by map)
Pixelformat          Menu: rgb
Channelorder         Menu
Startuniverse        Int
Startchannel         Int
Autoallocate         Toggle
Universesrequired    Int (read-only)
Lastuniversepixels   Int (read-only)
Rate                 Int
Priority             Int
Artsync              Toggle
Draftstatus          String
Validationstate      Menu/String
Apply                Pulse
Revert               Pulse
```

Die bestehende Produktion wird nicht direkt von UI-Parametern exportiert. Nur der Integrationscontroller darf nach erfolgreicher Validierung und Snapshot-Erstellung die Live-Nodes aktualisieren.

## 10. Maussteuerung der 3D-Vorschau

Die Interaktion gilt nur, wenn der Mauszeiger über der Preview liegt. Editor, Buttons und Scrollbereiche dürfen keine Kamerabewegung auslösen.

| Aktion | Steuerung |
|---|---|
| Orbit | linke Maustaste ziehen |
| Pan | mittlere Maustaste oder `Shift` + linke Maustaste ziehen |
| Zoom/Dolly | Mausrad; `Ctrl` für feinere Schritte |
| Fit all | Doppelklick auf leeren Hintergrund oder Taste `F` |
| LED auswählen | einfacher Klick auf Punkt |
| Auswahl ergänzen | `Shift` + Klick |
| Fokus auf Auswahl | Doppelklick auf Punkt |
| Front | Taste `1` oder Button `FRONT` |
| Side | Taste `3` oder Button `SIDE` |
| Top | Taste `7` oder Button `TOP` |
| Isometric | Taste `0` oder Button `ISO` |
| Reset view | `Home` oder Button `RESET` |

### 10.1 Kamera-Toolbar

```text
[ORBIT] [PAN] [SELECT] | FRONT SIDE TOP ISO | [FIT] [RESET] [LOCK]
```

- `ORBIT`, `PAN`, `SELECT` sind eindeutige Werkzeugmodi; Shortcuts bleiben zusätzlich aktiv.
- `LOCK` verhindert versehentliches Verschieben bei Installation/Abnahme.
- Ein kleines Navigation-Gizmo zeigt X/Y/Z und ist anklickbar.
- Perspective/Orthographic ist ein Menü; Front/Side/Top verwenden standardmäßig orthografisch, ISO perspektivisch.
- Pitch wird beim Orbit auf knapp unter ±90° begrenzt, damit die Kamera nicht unerwartet umkippt.
- Zoom arbeitet um Zielpunkt oder ausgewählte LED, nicht um den Weltursprung.
- Kameraänderungen betreffen niemals Mappingkoordinaten oder Exportdateien.

### 10.2 Kamera-Parameter

Empfohlene Preview-Parameter:

```text
Interactionmode       orbit / pan / select
Projection            perspective / orthographic
Yaw, Pitch            Float
Distance              Float
Targetx/y/z           Float
Orthowidth            Float
Cameralocked          Toggle
Selectedindex         Int
Fitview               Pulse
Resetview             Pulse
Front/Side/Top/Iso    Pulse/Menu
```

Die vorhandenen `View`- und `Camerazoom`-Parameter können intern weiterverwendet werden; die neue Steuerung soll sie über einen zentralen Kamera-Controller aktualisieren und nicht mehrere widersprüchliche Expressions setzen.

## 11. Hintergrundfoto

Ein Foto hilft, die LED-Punktwolke visuell an Wand, Schrank oder Panel auszurichten. Es ist ausschließlich eine Preview-Hilfe und darf weder Rohkoordinaten noch Fill/Contain oder Exporte verändern.

### 11.1 Kompakte Controls

```text
BACKGROUND  [OPEN PHOTO] [×]
[✓] Visible   Opacity [35%]   Placement [Camera backplate ▼]
Fit [Contain ▼]   [Center] [Lock]
[▸ Calibration]
```

Immer sichtbar:

- `Open Photo`: PNG, JPG/JPEG, TIFF.
- `Visible`: Foto ein-/ausblenden, ohne den Pfad zu verlieren.
- `Opacity`: 0–100 %, Standard 35 %.
- `Placement`: `Camera backplate` oder `World plane`.
- `Photo fit`: `Contain`, `Cover`, `Stretch`; ausdrücklich **Photo fit**, damit es nicht mit Map-Fill/Contain verwechselt wird.
- `Center` und `Lock`.

Calibration-Foldout:

- Plane: XY, XZ, YZ oder frei.
- Offset X/Y/Z.
- Scale X/Y und optional uniform lock.
- Rotation X/Y/Z.
- Mirror X/Y und Rotation 90°.
- Exposure/Gamma nur für Ansicht.
- Depth bias, damit Foto und Punkte nicht flimmern.
- `Reset photo transform`.

### 11.2 Darstellungsmodi

**Camera backplate**

- Foto bleibt bildschirmfüllend hinter der 3D-Szene.
- Geeignet als räumliche Referenz während freier Kamera-Navigation.
- `Contain/Cover/Stretch` bezieht sich auf das Preview-Fenster.
- Keine perspektivische Kalibrierung zur Geometrie.

**World plane**

- Foto liegt als echte Ebene in der 3D-Szene.
- Geeignet für Frontaufnahme einer Wand oder Schrankrückwand.
- Ebene, Maßstab, Position und Rotation sind kalibrierbar.
- Optionales `Match current view` richtet eine Ebene zur aktuellen Kamera aus und sperrt anschließend die Transformation.

### 11.3 Sicherheit und Persistenz

- Bildpfad möglichst relativ zur `.toe` bzw. zum Projekt speichern.
- Fehlt die Datei, zeigt Preview ein Schachbrett und `BACKGROUND FILE MISSING`; Map und DMX bleiben verwendbar.
- Keine Bilddatei wird ungefragt kopiert oder überschrieben.
- Fotozustand gehört in die TouchDesigner-Session, nicht in Pixelblaze JSON oder MariMapper CSV.
- Hintergrundfoto wird niemals an LEDs oder DMX gesendet.

## 12. Abnahmetests für Phase 2

| ID | Test | Erwartung |
|---|---|---|
| D01 | Baseline 3.714 RGB, Start U0/Ch1 | 22 Universen, letztes 144 Pixel/432 Kanäle |
| D02 | Import mit gleicher Pixelzahl | DMX `UNCHANGED`, Map separat applybar |
| D03 | Import 4.200 Pixel | 25 Universen, U22–U24 als NEW |
| D04 | Import 938 Slots mit Lücken | 938 einschließlich `[0,0,0]`, 6 Universen |
| D05 | ungültige Map | DMX-Bedarf blockiert, Live bleibt unverändert |
| D06 | Start U16 | Anzeige Net0/Subnet1/Universe0; fortlaufende Allokation korrekt |
| D07 | Startkanal 511 bei RGB | blockiert, kein vollständiges Pixel |
| D08 | Ziel-IP ungültig | Apply blockiert |
| D09 | lokaler Adapter/Ziel anderes Subnetz | Warnung, keine stille Korrektur |
| D10 | Apply mit neuer Pixelzahl | Review zeigt Delta, atomarer Wechsel oder vollständiger Rollback |
| D11 | Revert Draft | Live-Tabellen unverändert |
| D12 | Rollback Live | Map und DMX gemeinsam auf Snapshot zurückgestellt |
| V01 | Orbit/Pan/Zoom | flüssig, keine Koordinatenänderung |
| V02 | Kamera Lock | alle Navigationsgesten ignoriert, Auswahl bleibt möglich |
| V03 | View Presets | Front/Side/Top ortho, ISO perspektivisch |
| B01 | Foto Backplate Contain/Cover | korrekte Seitenverhältnisse |
| B02 | Foto World Plane | Transformation und Lock funktionieren |
| B03 | Fotodatei fehlt | Warnung, Mapper/DMX bleiben funktionsfähig |

## 13. Implementierungsreihenfolge

1. `output_config` mit Live-/Draft-Tabellen und reinem Allokationsrechner anlegen.
2. Baseline 3.714/22 aus den aktuellen Produktionsnodes read-only importieren.
3. Validierungs-DAT und Universe-Vorschautabelle bauen.
4. OUTPUT-Panel ohne Produktionsverbindung implementieren und screenshotten.
5. Kamera-Controller für Orbit/Pan/Zoom und Presets isoliert in `preview3d` ergänzen.
6. Hintergrundfoto erst als Backplate, danach als World Plane ergänzen.
7. D01–D09 sowie V01–V03 und B01–B03 ohne Live-Mutation testen.
8. Erst danach atomaren Apply-/Rollback-Controller implementieren.
9. Reale Integration zunächst mit deaktivierter DMX-Ausgabe testen.
10. Nach erfolgreicher Abnahme einmal explizit speichern und dokumentieren.

## 14. Entscheidungsempfehlungen

| Entscheidung | Empfehlung |
|---|---|
| Standard-Allokation | automatisch, fortlaufend, keine Pixelteilung |
| Standard-Start | Universe 0, Channel 1 |
| Standard-Pixelformat | RGB, Reihenfolge RGB |
| Pixelzahländerung | Map-Preview erlauben, reales Apply nur gemeinsam mit DMX-Review |
| Manuelle Universen | Advanced-Modus, nicht Standard |
| Netzwerkprüfung | Warnung bei unbekannter Erreichbarkeit, nicht als alleiniger Blocker |
| Apply | atomar für Map + DMX, wenn sich Pixelzahl/Footprint ändert |
| Revert/Rollback | getrennte Begriffe und getrennte Aktionen |
| Mausnavigation | linke Taste Orbit, mittlere/Shift+links Pan, Rad Zoom |
| Foto-Standard | Camera backplate, 35 % Deckkraft, Photo fit Contain |

## 15. Nicht Bestandteil dieses Planungsschritts

- Keine Veränderung von `/project1/dmxout1`, `DMX_Universes`, Routingtabelle oder Universe-CHOPs.
- Keine Aktivierung neuer Universen.
- Keine Netzwerkpakete oder Testframes.
- Keine Umschaltung der aktiven Mappingkette.
- Kein `project.save()`.

