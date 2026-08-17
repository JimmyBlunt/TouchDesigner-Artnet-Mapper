# Agentenbericht: Portables Mapping-I/O

Status: **abgeschlossen und getestet**

## Ergebnis

Das neue Python-Modul `pixelblaze_mapper.mapper_io` ist unabhängig von
TouchDesigner und benötigt keine externen Pakete. Es stellt folgende Funktionen
bereit:

- Import materialisierter Pixelblaze-Arrays aus JSON sowie einer begrenzten,
  sicheren JSON5-Teilmenge (JavaScript-Kommentare und trailing commas)
- Erkennung und verlustfreie Aufbewahrung von Pixelblaze-JavaScript-Generatoren
  ohne `eval` oder andere Codeausführung
- Import von MariMapper-CSV mit `index,x,y,z`; die bestehenden
  TouchDesigner-Aliase `index,tx,ty,tz` werden ebenfalls akzeptiert
- strikte Sortierung nach LED-Index; negative oder doppelte Indizes sind Fehler
- Einfügen von `[0,0,0]` für fehlende Indizes samt gut lesbarer Warnung
- Validierung auf konsistente 2D-/3D-Dimensionen und endliche Zahlen
- Export als reines Pixelblaze-Koordinatenarray ohne Metadaten
- Export als MariMapper-CSV; optionale Spalten wie `xn,yn,zn,error` bleiben
  erhalten
- Fill und Contain als explizite Ableitung; die importierten Rohkoordinaten
  bleiben unverändert

## Reale BallsMatrix3-Prüfung

Die von TouchDesigner exportierte Fixture
`tests/fixtures/ballsmatrix3_normalized.csv` wird direkt im Test verwendet:

- 935 vorhandene Datenzeilen
- höchster Index 937
- Ergebnislänge 938 LED-Slots
- fehlende Indizes 894, 895 und 896
- alle drei Lücken werden als `(0.0, 0.0, 0.0)` materialisiert

## Angelegte/geänderte Dateien

- `pixelblaze_mapper/mapper_io.py`
- `pixelblaze_mapper/__init__.py`
- `tests/test_mapper_io.py`
- `tests/fixtures/pixelblaze_generator.js`
- `tests/fixtures/ballsmatrix3_normalized.csv` (reale Fixture, vom
  Hauptagenten aus TouchDesigner bereitgestellt)
- `docs/pixelblaze-mapper-plan/agent-io-report.md`

## Testresultat

Ausgeführt mit:

```text
python -m unittest discover -s tests -v
```

Ergebnis nach Hauptreview: 13 Tests erfolgreich, 0 Fehler. Ergänzt wurde ein
Regressionstest, der Dateipfade nur als explizite `Path`-Objekte akzeptiert,
damit lange JSON-/JavaScript-Texte niemals versehentlich als Pfad interpretiert
werden.

## Bekannte und beabsichtigte Grenzen

- JavaScript-Generatoren werden aus Sicherheitsgründen nicht von Python
  ausgeführt. Die Schnittstelle liefert ein `PixelblazeGenerator`-Objekt, kann
  dessen Quelltext verlustfrei exportieren und wirft bei `materialize()` eine
  klare `GeneratorExecutionUnavailable`-Exception. Eine spätere, explizit
  vertrauenswürdige JavaScript-/Pixelblaze-Adapterstufe kann daran anschließen.
- Die unterstützte JSON5-Teilmenge umfasst Kommentare und trailing commas. Sie
  führt keine JavaScript-Ausdrücke aus und unterstützt absichtlich keine
  unquotierten Objektfelder, Hex-Literale oder `NaN`/`Infinity`.
- Das Modul schreibt nicht selbst auf Datenträger. Die UI kann den Text über
  ihren Open-/Save-Dialog lesen beziehungsweise schreiben; dadurch bleibt die
  Dateiauswahl klar von Parsing und Validierung getrennt.
- Fill skaliert jede Achse unabhängig auf 0..1. Contain verwendet einen
  gemeinsamen Maßstab anhand der größten Ausdehnung und zentriert die übrigen
  Achsen um 0.5. Achsen ohne Ausdehnung liegen bei 0.5.
