# Materialzustand: speichersichere Grenze

Stand 2026-09-07. Behebt den beim tatsächlichen Speicherversuch gemeldeten `PicklingError` für eine veraltete `AdaptationResult`-Klasse. Dieser Patch wurde vom Material-Teilauftrag ausschließlich offline bearbeitet; Installation und nativer Save-/Reopen-Test liegen beim Hauptauftrag.

## Ursache und Vertrag

Die Library hält Shaderadaptionen und Parameterschemata in zwei OWNER-Storage-Caches. `_adaptation_for_item` kann deren Python-Module neu laden; bereits vorhandene Instanzen gehören dann nicht mehr zur aktuell unter ihrem Modulnamen registrierten Klasse. Pickle scheitert an dieser Identitätsabweichung. Zusätzlich waren Native-Parameterstore und P1-Materialstore als eigene Klasseninstanzen im dauerhaften Storage abgelegt.

Nach [Derivative: Storage](https://docs.derivative.ca/Storage) werden OP-Storage-Werte mit `.toe`/`.tox` gespeichert. Der dokumentierte [OP-Storage-Vertrag](https://derivative.ca/UserGuide/ObjectCHOP_Class#Storage) erlaubt mit `storeStartupValue(key, None)` einen alternativen Save-/Startwert für sitzungsspezifische Python-Objekte, ohne den laufenden Wert zu ersetzen. Genau diese Grenze nutzt der neue Helper `pixelblaze_mapper/material_storage.py`.

| Besitzer / Schlüssel | Laufender Wert | Gespeicherter Wert |
| --- | --- | --- |
| Library / `material_parameter_context_cache` | Shader-/Schema-Cache mit Klasseninstanzen | `None`; bei Bedarf neu aufgebaut |
| Library / `material_hover_context_cache` | Hover-Shadercache | `None`; bei Bedarf neu aufgebaut |
| Library / `madmapper_parameter_store` | einfaches Datendokument | Dasselbe primitive Dokument |
| Project1 / `p1_material_state_store` | einfaches Datendokument | Dasselbe primitive Dokument inkl. aktueller Phase |
| Project1 / `p1_material_runtime_cache` | laufender MaterialStateStore | `None` |
| Project1 / `p1_material_state_runtime_schema` | Initialisierungsmarker | `None`; Reopen initialisiert und rebaset |

Die beiden bestehenden JSON-DATs bleiben zusätzliche dauerhafte Kopien. Library-Aktiv-ID, Label, Browserauswahl und sämtliche per-Material-Werte werden nicht gelöscht. Alte Storeinstanzen werden über `to_dict()` migriert, unabhängig von ihrer Klassenidentität. Es gibt kein pauschales Leeren des OWNER-Storage. Der Helper ohne TD-Startup-API hält ausschließlich modul-lokale Caches und entfernt nur den explizit benannten alten Cache-Schlüssel.

P1 hält den laufenden Store im flüchtigen Cache über DAT-Modulneuerstellungen hinweg. Dauerhafte Einstellungen werden bei normalen Persist-Aktionen als Daten gespeichert. Jeder Phasentick aktualisiert nur `phase` und `last_time` im bereits gespeicherten, veränderlichen Datendokument; kein zusätzlicher `store()`, DAT-Neuschreiben, JSON-Encoding oder vollständiges Kopieren aller Materialien pro Frame. So enthält ein späterer Save die aktuelle Phase. Beim Reopen wird deren Zeitanker neu gesetzt, ohne die geschlossene Zeit als Animation nachzuholen. Die Storage-Kopie hat dabei Vorrang vor der möglicherweise älteren DAT-Phasenkopie.

## Tests und Übergabe

`tests/test_material_storage.py` führt tatsächliche eingebettete Runtime-Initialisierung und Persist-/Tick-/Initialize-Funktionen mit isolierten Fake-Operatoren aus. Vier neue Tests reproduzierten zunächst drei Fehler und genau den realen `AdaptationResult`-PicklingError nach `importlib.reload`. Ein weiterer Test deckte zunächst den sonst veralteten gespeicherten Phasenstand auf. Anschließend alle grün; weitere Prüfungen decken fehlende Startup-API, reine/detachierte Daten und nicht-endliche Zahlen ab.

Die Save-Simulation substituiert Startupwerte entsprechend dem dokumentierten TD-Vertrag und verwendet anschließend echtes Python-Pickle. Sie ist ausdrücklich kein nativer `.toe`-Save-/Reopen-Nachweis.

Installation durch den Hauptauftrag: neuen Helper verfügbar machen, Library-Runtime und P1-Runtime aus den aktualisierten Builderquellen installieren/initialisieren. Kein gesondertes Cache-Löschen und kein Material-Neuaktivieren nötig. Das bloße Kopieren einer Datei ohne Ausführung der neuen Runtime registriert noch keine Startupwerte. Den aktuellen Projektzustand vor der Installation sichern, sofern ein funktionierender Sicherungsweg vorhanden ist; ein fehlgeschlagener Save ist kein Backup.

Native Abnahme: Output bleibt OFF; vor/nach Installation aktive ID, alle Native-Werte, P1-Einstellungen und Phasenfortschritt vergleichen. Save muss ohne PicklingError abschließen. Beim Reopen müssen aktive ID und per-Material-Werte erhalten sein, Shadercaches leer starten und beim echten Gebrauch wieder aufbauen; die Phase darf keine geschlossene Zeit addieren. Andere Komponenten können unabhängig davon eigene nicht serialisierbare Storageobjekte besitzen—dieser Patch erklärt nicht ungeprüft das gesamte Projekt für speicherfähig.

## Tatsächlicher nativer Save-/Reopen-Vergleich

Der Hauptauftrag hat anschließend `PixelblazeMapper_20260907_STORAGE_REPAIRED.1.toe` gespeichert und wieder geöffnet. Der Material-Teilauftrag verglich **offline sämtliche materialbezogenen Dauerwerte**, nicht nur das aktive Material: `storage-repair/file-storage.json` (vom Hauptauftrag eingeschränkt aus der nativen TOE extrahierter Storage) gegen `storage-repair/after-reopen.json` und zusätzlich `after-migration.json` gegen den nativen Dateistand. Keine Live-/UI-/Schreibaufrufe an TD durch diesen Vergleich.

Präzise Ergebnisse einschließlich SHA-256 der vier Eingangsbelege, aller IDs, Feldanzahlen und jeder tatsächlichen Abweichung: [material-roundtrip-comparison.json](storage-repair/material-roundtrip-comparison.json).

| Geprüfter Dauerzustand | Umfang | Ergebnis |
| --- | --- | --- |
| Importierte Native-Werte | 8 Materialien, **137 Parameterwerte** einschließlich Vektor-/Farbkomponenten | Exakt identisch |
| Native-Schemata und Navigation | 137 Typzuordnungen, alle 8 Seitenstände, Dokumentversion und vollständige ID-Menge | Exakt identisch |
| P1-Materialeinstellungen | Der Dateistand enthält **1 Material, 14 Settingsfelder** einschließlich Farbvektoren | Exakt identisch |
| P1-Auswahl und Master | Aktive Material-ID, globaler Master und Dokumentversion | Exakt identisch |
| Temporäre Speicherung | Beide Shadercaches, P1-Runtimecache und Initialisierungsmarker | Alle vier in der TOE `null` |

Die acht Native-Materialdatensätze enthalten der ID-Reihenfolge nach 12, 29, 6, 33, 29, 15, 11 und 2 Werte; keine fehlende oder hinzugekommene ID. Dieselben Native-Dokumente sind bereits zwischen Migration und nativer Datei exakt gleich. Auch für P1 unterscheiden sich zwischen Migration und Datei keine Einstellungen, sondern ausschließlich die laufende Phase und deren Zeitstempel. Der P1-Dateistand enthält tatsächlich nur ein Material; der Vergleich behauptet keine nicht vorhandenen zusätzlichen P1-Datensätze.

Die einzige erlaubte Reopen-Differenz ist nachgerechnet: gespeicherte Phase **1490,3134564658585**, danach **1490,887598946071**. Die Initialisierungs-DAT nach Reopen enthält exakt die gespeicherte Phase mit neuem Zeitanker **0**. Bei anschließendem Zeitstempel **2,2666666666666666 s**, Speed **0,2532981530343008** und Master **1** ergibt sich ein erwarteter Zuwachs von **0,5741424802110818**; gemessen **0,5741424802124584**. Abweichung **1,38 × 10⁻¹²**, innerhalb der Vergleichstoleranz `1e-9`. Geschlossene Zeit wurde damit in dieser Beobachtung nicht als Animation nachgeholt.

`after-reopen.json` meldet keine Operatorfehler und keine Runtime-Picklefehler. Der Hauptauftrag führt einen weiteren nativen Save nach Reopen separat aus; dessen Ergebnis ist nicht Bestandteil dieses Belegs. `before-repair.json` enthält die damaligen klassenbasierten Stores nur als Typbeschreibung, nicht als vollständiges Wertedokument. Daraus lässt sich kein vollständiger Vor-Reparatur-Wertvergleich ableiten; die exakt belegte Kette beginnt bei `after-migration.json` und umfasst native Datei sowie Wiederöffnung.
