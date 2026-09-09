# Art-Net Router: alle Controller in einer einheitlichen Ansicht

Die Controller-Karte liest `controller_config`. Auch neu hinzugefügte Geräte
wie `BACK_PANEL_249` erscheinen automatisch; es gibt keine Sonderbehandlung
für die beiden ursprünglichen Controller. Mit **< / >** wechselt man zwischen
den Geräten. Name und `1 / N` zeigen die Auswahl eindeutig an.

## Livewerte und Eingaben

- **LIVE CONFIG**: wirksame IP, WIRE-Universen, Helligkeit, gewünschte Senderate
  und Farbreihenfolge. Die gewünschte FPS-Zahl ist keine gemessene Geräte-FPS.
- **IP address**: Ziel-IP des ausgewählten Controllers.
- **First WIRE universe**: direkt die Art-Net-Adresse, nullbasiert. Für das erste
  Rückwandpanel `120` eingeben, nicht `121`.
- **Enabled**: `0` deaktiviert, `1` zum Senden freigegeben. Erst START aktiviert
  die Ausgabe, wenn sie vorher ausgeschaltet war.
- **Requested rate FPS**: gewünschte Rate (1–120); tatsächliche Gesamt-Senderate
  steht oben. Sie kann durch TouchDesigner und Last niedriger sein.
- **Brightness**: `0` bis `1`, auch Dezimalkomma möglich (`0,3` = 30 Prozent).
- **BRIGHTNESS LIVE**: übernimmt ausschließlich diese Helligkeit für diesen
  Controller, ohne Senderneustart oder andere Entwurfsänderungen.
- **RELOAD**: verwirft die ungespeicherten Eingaben nur der ausgewählten Karte
  und lädt deren aktuelle Konfiguration. Navigation behält Entwürfe bei.
- **APPLY SAFE DRAFT**: validiert die geänderten Karten gemeinsam, übernimmt sie
  transaktional und lässt die Ausgabe aus. Extern geänderte Controller werden
  nicht mit veralteten Eingaben überschrieben; erst RELOAD benutzen.
- **START ENABLED / RETURN TO LIVE**: vorhandener sicherer Startpfad; übernimmt
  geprüfte Entwürfe und startet die freigegebenen Controller.
- **ALL OUTPUTS OFF**: unmittelbarer vorhandener Stopp-Pfad.

Routen zeigen Namen, Quellstart + Anzahl und Zieloffset, darunter die lokale
Netzwerkschnittstelle und UDP-Port. Physische Ports und Reservierung werden im
Controller-/Port-Konfigurationsdialog bearbeitet, nicht in dieser Kurzansicht.

## Warum ein Pixel nicht leuchtet

Die Summenzeile unterscheidet:

1. **enabled routes**: einer freigegebenen Route zugeordnet (nicht automatisch
   Beweis, dass die Hardware Pakete darstellt).
2. **disabled-only**: zugeordnet, aber ausschließlich deaktivierten Controllern.
3. **unassigned**: keine Route zu einem vorhandenen Controller.
4. **explicit black slots**: absichtlich ausgeblendete Quellplätze, etwa die
   freien 53 Plätze nach dem 203-LED-Rückwandscan.

Überlappende Routen werden nicht doppelt gezählt. Sobald mindestens ein
freigegebener Controller einen Pixel verwendet, zählt er nicht disabled-only.

## Beispiel: Rückwandhelligkeit

1. Mit < / > **BACK_PANEL_249** wählen und IP `10.0.0.249` überprüfen.
2. LIVE CONFIG zeigt WIRE U120–U121 und den aktuellen Helligkeitswert.
3. Brightness auf `0,3` setzen und BRIGHTNESS LIVE drücken.
4. LIVE CONFIG und LAST ACTION müssen 30 Prozent bestätigen. Die Animation
   läuft ohne Neustart weiter; andere Controllerwerte bleiben unverändert.

## Tests und technische Installation

`python -m unittest tests.test_router_dynamic_ui tests.test_router_extra_brightness_ui tests.test_multi_controller -q`

48 Tests erfolgreich beim Implementierungsstand. Abgedeckt: dritter Controller,
unveränderte Nachbarzeilen, WIRE 0, Dezimalkomma, ungültige Werte, mehrere
Kartenentwürfe, externe Änderung/Löschung und Zuordnungsunterscheidung.
Dies ersetzt nicht den tatsächlichen TouchDesigner-Klicktest.

UI-only Hot-Installation im TD-Kontext:

```python
from tools.install_router_cards_20260909 import install
result = install(globals())
```

Der Installer prüft, dass Controller-/Segmenttabellen und Sender-Ein/Aus-Zustand
unverändert bleiben. Nicht den gesamten Netzwerk-Builder für ein reines
Live-UI-Update ausführen. Der Builder integriert die Karte bei künftigen
regulären, sicheren Neuaufbauten ebenfalls.
