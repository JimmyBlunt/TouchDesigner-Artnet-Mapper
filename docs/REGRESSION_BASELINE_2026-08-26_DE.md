# Regressionstest – verbindliche Ausgangsbasis

Stand: 26.08.2026  
Projekt: `PixelblazeMapper_WORKING_PHASE2_EFFECTS_CORE.68.toe`  
Phase: Analyse und Dokumentation; keine funktionalen Korrekturen in dieser Phase

## Ziel und Abgrenzung

Diese Ausgangsbasis trennt drei Testebenen, die im Abschlussbericht nicht
miteinander vermischt werden dürfen:

1. **Statische Vertrags- und Unit-Tests** prüfen Python-Logik, Builder und
   gespeicherte Konfigurationen.
2. **Live-Tests in TouchDesigner** prüfen echte Shortcuts, Fenster, sichtbare
   Werte, Bindungen und Auswirkungen während das Projekt läuft.
3. **Beaufsichtigte Hardwaretests** prüfen die tatsächliche LED-Ausgabe. Kritische
   Ausgabe-, Apply-, Import-, Start- oder Blackout-Aktionen werden nicht
   unbeaufsichtigt ausgelöst.

## Automatische Basis

`python -m unittest discover -s tests -v` wurde im Projektordner ausgeführt.

- Ergebnis: **194 von 194 Tests bestanden**
- Laufzeit: **10,834 Sekunden**
- Fehler/Abbrüche: **0**

Das bestätigt die vorhandenen Codeverträge, ist aber kein Nachweis dafür, dass
jeder sichtbare Dialogwert live aktuell ist oder jeder Mausklick die gewünschte
Wirkung hat.

## Live-Projektzustand

- TouchDesigner: 2025.33070
- Aktives Projekt: CORE.68
- Soll-Timeline: 60 FPS
- Material beim Start der Messung: `matrix_rain`
- Materialgeschwindigkeit beim Start: `0.511`
- Gradient: `neon_cyan_magenta`
- Verbindliche Hardwarevorschau: `/project1/LED_PREVIEW_OUT`

Das laufende Projekt war durch Laufzeitoperationen als geändert markiert. Es
wurde für diese Analyse bewusst **nicht gespeichert**.

## Reale Leistungs-Messung

Die tatsächlich berechneten TouchDesigner-Frames wurden über zehn Sekunden
gezählt. Das ist nicht nur der Art-Net-Sendetakt, sondern der Cook-/Frame-Takt,
in dem neue Animationsbilder entstehen.

| Zustand | Frames in 10 s | Tatsächliche Rate |
|---|---:|---:|
| Sieben schwebende Dialogfenster geöffnet | 79 | 7,9 FPS |
| Dieselben sieben Fenster geschlossen | 137 | 13,7 FPS |
| Zielwert | 600 | 60 FPS |

Die geöffneten Dialogviewer verschärfen das Problem deutlich, sind aber nicht
die einzige Ursache. Auch ohne sie bleibt die Anwendung weit unter 60 FPS. Wenn
Art-Net gleichzeitig mit 60 Hz sendet, werden daher zwischen zwei neu
berechneten Bildern wiederholt identische Frames übertragen. Das kann als
Ruckeln oder kurze Stillstände wahrgenommen werden.

## Geschwindigkeitsregler – erster Live-Befund

Der sichtbare Parameter `Speed` wurde testweise von `0.511` auf `1.234`
gestellt. Nach dem Wechsel zwischen mehreren Materialien blieb `1.234`
erhalten. Anschließend wurde der Ausgangswert `0.511` wiederhergestellt.

Die aktuelle Bindung ist global:

`Zeitkoordinate = absTime.seconds * controls.Speed`

Damit besitzt die aktuelle Implementierung einen gemeinsamen
Geschwindigkeitswert für alle Materialien. Das widerspricht dem gewünschten
Verhalten „nur für das ausgewählte Material“, sofern pro Material ein eigener
Wert erwartet wird. In dieser Analysephase wurde die Bindung nicht geändert.

## Shortcut Strg+Umschalt+7 – realer Befund

Der Shortcut wurde mit einer echten Windows-Tastatureingabe geprüft:

- im TouchDesigner-Hauptfenster: Output Config öffnete sich;
- mit Fokus im Material Browser: Output Config öffnete sich erneut;
- der Keyboard-In-DAT protokollierte dabei die Tastendrücke für `7` mit
  `ctrl=1`, `shift=1` und Press/Release-Ereignissen;
- die Shortcut-Nodes meldeten keine TouchDesigner-Fehler.

Der Shortcut funktioniert damit im geprüften Zustand praktisch. Der Callback
verwendet jedoch den älteren Funktionsnamen `keyEvent`. Ob dies in der
eingesetzten TouchDesigner-Version ein unterstützter Vertrag oder nur eine
kompatible Altform ist, wird gesondert bewertet. Der reale Erfolg hat bei der
Fehlerklassifizierung Vorrang vor einer rein statischen Vermutung.

Nicht geprüft sind bisher alle denkbaren Fokuszustände, insbesondere aktive
Textfelder und modale Fenster. Genau dort kann der Tastendruck weiterhin
abgefangen werden.

## Sichtbare Inkonsistenzen der Output Config

Die sichtbare Output Config zeigte unter anderem:

- `10.0.0.244`
- `U0-U21`
- `3714 GRB PIXELS`
- `30 FPS`
- lokale IP `10.0.0.173`
- ArtSync `ON`

Die tatsächlich aktive Controller-Konfiguration enthielt dagegen:

- Ziel-IP `10.0.0.244`
- lokale IP `10.0.0.125`
- Startuniversum `1`
- Rate `60`
- ArtSync `0`
- Helligkeit `0.03`

Damit sind mehrere sichtbare Werte nachweislich nicht an den aktiven Zustand
gebunden oder veraltet. Der Dialog-Agent führt die vollständige Feld-für-Feld-
Bewertung durch.

## Verbindliche Bewertungsmatrix pro Dialog

Jeder Dialog erhält im Einzelbericht begründete Bewertungen für:

- Nutzbarkeit
- technische Umsetzung
- Zuverlässigkeit
- Wartbarkeit
- Vollständigkeit
- Innovativität

Zusätzlich werden konkrete Verbesserungen, Risiken und priorisierte nächste
Schritte genannt. Der Gesamtbericht vergleicht alle neun Dialoge, deckt
Doppelungen und fehlende Funktionen auf und trennt zwingende Fehlerbehebungen
von optionalen Optimierungen.

