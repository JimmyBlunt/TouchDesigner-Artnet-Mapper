# Phase 2 – Bericht zum reinen DMX-Kern

Stand: 13. August 2026  
Status: implementiert, ohne Änderung am laufenden TouchDesigner-Projekt

## Dateien

- `pixelblaze_mapper/dmx_config.py`
- `pixelblaze_mapper/__init__.py` (öffentliche Exporte des DMX-Modells)
- `tests/test_dmx_config.py`
- `docs/pixelblaze-mapper-plan/phase2-dmx-core-report.md`

## Modell

`DmxConfig` beschreibt nur Daten und besitzt sichere Standardwerte für die
aktuelle Installation:

- logische Eingabereihenfolge `RGB`;
- physische Ausgabereihenfolge `GRB`;
- drei Kanäle pro Pixel;
- 510 verwendete Samples pro Universumsframe;
- Startuniversum 0, Startkanal 1;
- Ziel `10.0.0.244`, lokale Adresse `10.0.0.173`, Port 6454.

`build_plan()` erzeugt daraus unveränderliche `UniverseAllocation`-Objekte. Der
erste Bereich berücksichtigt einen optionalen, einsbasierten Startkanal. Alle
weiteren Universen beginnen auf Kanal 1. Jedes erzeugte Frame besitzt genau 510
Samples; unbenutzte Positionen werden deterministisch mit null aufgefüllt.

Für die Output-UI steht zusätzlich `allocate_dmx(config: Mapping) -> dict`
bereit. Der Adapter akzeptiert direkt den `OutputDraft`-Payload, liefert die
vereinbarten Kennzahlen, Tabellenzeilen und strukturierten Issues und wird über
`phase2_output_ui_contract.find_shared_allocator()` automatisch gefunden.
`capacity_pixels` bezeichnet dabei die Gesamtkapazität der bereits benötigten
Universen (bei 3.714 Pixeln: 22 × 170 = 3.740), nicht die aktuelle Belegung.

## Verifizierte Baselines

| Pixel | Universen | letztes Universum | aktive letzte Slots | Padding |
|---:|---:|---:|---:|---:|
| 3.714 | 22 | 144 Pixel | 432 | 78 |
| 938 | 6 | 88 Pixel | 264 | 246 |

Für 3.714 Pixel liefert das Modell außerdem 11.142 flache Werte und den
Lookup-Endindex 11.141.

## Tabellen und Adressen

Der Plan erzeugt direkt:

- `DMX_Universes`-Zeilen `Universe,index,pixel`;
- Routing-Zeilen `channel,net,subnet,universe`;
- Kanalnamen `Universe0..UniverseN-1`;
- Art-Net-Zerlegung über `net=u//256`, `subnet=(u//16)%16`,
  `universe=u%16`.

Das Startuniversum verschiebt ausschließlich die Art-Net-Adresse, nicht die
internen Kanalnamen.

## Validierung

Geprüft werden unter anderem Pixelzahl, Farbkanal-Permutation, Startkanal,
510/512-Grenze, IPv4-Adressen, Port, Art-Net-Überlauf, lückenlose Pixelbereiche,
eindeutige Routen, Samplezahl, aktive Slots und Padding-Summe.

`classify_diff()` liefert für eine geplante Änderung genau eine höchste
Risikoklasse:

- `unchanged`: DMX-Topologie und Indexfolge gleich;
- `append`: nur zusammenhängende neue End-Slots;
- `reindex`: Entfernen, Einfügen oder Umsortieren;
- `network`: Netzwerk-, Adress-, Farb- oder Frameparameter geändert.

`network` hat Vorrang, wenn gleichzeitig Pixel angehängt werden.

## Integrationsgrenze

Das Modul importiert weder `td` noch Netzwerkbibliotheken, schreibt keine DATs
und sendet kein Art-Net. Ein späterer TouchDesigner-Adapter muss zunächst einen
Plan erzeugen und validieren, dann seine Tabellen atomar anwenden und bei einem
Live-Fehler den vorherigen Snapshot wiederherstellen.
