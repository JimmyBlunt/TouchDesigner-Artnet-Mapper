# Controller- und Porteditor – Offlineimplementierung

07.09.2026. Quellimplementierung bereit, **nicht durch diesen Teilauftrag live installiert**. Keine Ausgabe gestartet, keine TOE gespeichert und kein Commit erstellt.

## Bedienoberfläche

Der bestehende GICO-Dialog und Shortcut0 bleiben erhalten. Ein zusätzlicher Button **CONTROLLERS & PORTS** öffnet `/project1/multi_controller_output/gico_port_config/controller_ports/ui_panel`; **BACK TO GICO** führt zurück. Sechs Portzeilen je Seite, beliebig viele Seiten für das unabhängige Profil.

- Controller-ID eingeben und LOAD/REVERT für einen bestehenden Controller oder NEW DRAFT für einen neuen Controller verwenden.
- Ziel-IP, lokale Schnittstelle, UDP-Port, erste UI-Universe, Rate, Helligkeit, Enabled und Standardfarbreihenfolge bearbeiten. Neue Controller sind zunächst disabled und auf Loopback als ungefährlichen Platzhalter gesetzt; vor realer Nutzung müssen Ziel/NIC ausdrücklich eingetragen werden.
- Pro Port Label, Enabled, Source Start, Pixelzahl, reservierte Universen, Reverse, Farbreihenfolge und optionalen Zielpixelstart bearbeiten. Leerer Zielstart bedeutet automatische Blockallokation; explizite Werte erhalten bestehende Ausnahmen wie den APA102-Präfix512.
- ADD PORT und REMOVE PORT # verändern nur den Entwurf. STAGE DELETE markiert den ausgewählten Controller einschließlich seiner Routen zum Entfernen; die echte Entfernung erfolgt erst mit SAFE APPLY. LOAD verwirft diese Markierung.
- VALIDATE DRAFT prüft Hardwarefähigkeit und die gesamte resultierende Routerkonfiguration ohne Hardwarewirkung. SAFE APPLY verwendet die P0-Transaktion und lässt Ausgabe aus. Eine seit LOAD extern geänderte Routerkonfiguration blockiert Apply bis zum erneuten Laden.

Ein Profilwechsel oder geänderte Portreserve ist keine Konfiguration der Controllerfirmware. Die Firmware muss dieselbe physische Aufteilung unterstützen; dieser Editor konfiguriert ausschließlich das Routing in TouchDesigner.

## Wahrheitsgetreue Hardwareprofile

| Profil | Reserve | Physische Slots | Beispiele |
|---|---|---|---|
| `gico_equal` | Gleich auf allen vier Ports | Vier feste Slots; unbenutzte deaktivieren, nicht entfernen | 6/6/6/6, Zielstarts0/1020/2040/3060 |
| `independent` | Pro Port editierbar | Neue Ports hinzufügen/entfernen | 4/2/6, automatische Zielstarts0/680/1020 |

Der bekannte `WS2812_NODE` kann nicht als unabhängiges Profil umdeklariert werden. Unterschiedliche GICO-Reserven werden zurückgewiesen. „Benötigte Universen“ und „reservierte Universen“ sind getrennt: die bekannten GICO-LED-Zahlen517/269/398/896 benötigen4/2/3/6 Universen bei jeweils6 reservierten Universen. Leere Quellen bleiben ausdrücklich ungeroutet.

Generic-Apply für WS synchronisiert die GICO-Settings/Porttabellen in derselben Transaktion. Fremde Controller und Segmente werden unverändert übernommen. Vorhandene unabhängige Routersegmente werden als virtuelle Portabschnitte importiert; ist eine solche Zuordnung nicht eindeutig oder blocküberlappend, wird sie nicht still umgebaut, sondern blockiert. Ein neuer generischer Entwurf bedeutet nicht, dass die Fähigkeiten eines unbekannten Controllers automatisch erkannt wurden.

## Weitere Reparaturen im Routingbereich

- GICO-Builder normalisiert Singletonnamen und bereinigt zugehörige numerische Altduplikate, auch wenn bereits ein kanonischer Node existiert. Drei wiederholte Hilfs-Builderläufe sind offline geprüft. Momentary-Werte werden zurückgesetzt und Handler während Reparatur deaktiviert.
- Alter GICO-Dialog zeigt benötigte/reservierte Universen getrennt.
- Router-Safety und Controllerüberschriften lesen den tatsächlichen Sender-/Routerstatus, inklusive Ist-FPS und aktueller Quellpixelzahl. Aktionsmeldungen heißen ausdrücklich LAST ACTION. Falsche Quarantäne-/U1–U9-Texte wurden aus der aktiven Oberfläche entfernt; Routerfelder sind als zero-based Wireuniversen beschriftet.
- Routing-/Packer-/Senderkonfigurationen verwenden aktuelle Quellpixelzahl; der Packer-Cache berücksichtigt Änderungen dieser Zahl. Bestehende3744-Pixel-Szenen behalten ihre bisherige Semantik. Die alte räumliche Kalibrierung bleibt an ihre tatsächlich vorhandenen Koordinaten gebunden und ist damit keine automatische Kalibrierung neu erfundener LEDs.

## Tests und offene Grenzen

**90 Tests bestanden, letzter Lauf3,330 s**: P0-Transaktion, Topologiemodell, tatsächlicher eingebetteter Editorruntime mit Mock-DATs, GICO-Modell/UI, bestehender Router, Kalibrierung, Packer und OutputSummary.

Neue Nachweise: unabhängige4/2/6-Blöcke, Ablehnung ungleicher GICO-Kapazität, Controller-/Portanlage und -entfernung, Erhaltung fremder Routen, APA-Präfix512, Quell-/Blocküberschneidungen, Universegrenzen, sechszeilige Pagination, reine Draftmutation, Stale-Snapshot-Blockade, gestufte Controllerlöschung und Rollback nach Builderfehler. **Echte UI-Layout-/Fokus-/Mausprüfung und TD-Builderintegration stehen noch aus** und müssen der Hauptintegration folgen.

Noch nicht gelöst: getrennte Netzwerkinterfaces im Shared Sender, unabhängige Controllerraten und ArtSync-Verhalten. Die aktuellen Senderbeschränkungen bleiben verbindlich; die generische Konfiguration allein erweitert die physischen Senderfähigkeiten nicht. Feldbezogene Soforthilfe und automatisches Dirty-Markieren bei jeder einzelnen Tastatureingabe sind ebenfalls noch keine vollständige Abnahme.

Der separat kopierte P0-Checkpoint liegt unter `p0-routing-checkpoint/`, die damalige Abnahme ist in `P0_ROUTING.md` dokumentiert.
