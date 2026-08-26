# Konzept: einheitliche Schnellhilfe in allen Dialogen

Status: Entwurf für die spätere Umsetzung; in der Analysephase noch nicht in
TouchDesigner eingebaut.

## Ziel

Jeder sichtbare Wert, Button, Schalter, Regler und Status erhält ein kleines
`i`-Symbol. Die Hilfe soll ohne Wechsel in eine externe Dokumentation erklären,
was das Element bewirkt und woran eine erfolgreiche Wirkung erkennbar ist.

## Verhalten

- **Maus darüber:** kurze Hilfe mit Zweck, Einheit und aktuellem Wert.
- **Klick auf `i`:** ausführlicher Hilfebereich im selben Dialog.
- **Erneuter Klick oder Escape:** Hilfe schließen, ohne Werte zu verändern.
- **Tastaturfokus:** das Symbol muss per Tab erreichbar sein und einen
  verständlichen zugänglichen Namen besitzen.
- **Fehlerzustand:** Hilfe zeigt zusätzlich Ursache, erwarteten Wertebereich und
  sicheren nächsten Schritt.

Ein `i`-Klick darf niemals einen Parameter ändern, eine Datei schreiben, einen
Import starten oder Hardwareausgabe aktivieren.

## Pflichtfelder eines Hilfeeintrags

| Feld | Inhalt |
|---|---|
| Titel | Sichtbarer Elementname |
| Zweck | Ein Satz: Was steuert oder zeigt das Element? |
| Einheit/Bereich | z. B. FPS, Pixel, Universe, 0–2 oder IP-Adresse |
| Default | definierter Ausgangswert, falls vorhanden |
| Aktueller Istwert | live aus derselben Quelle wie die eigentliche Anzeige |
| Wirkung | betroffene Nodes, Materialien, Panels oder Controller in Alltagssprache |
| Erfolgszeichen | sicht- oder messbarer Nachweis, dass die Aktion gewirkt hat |
| Sicherheit | Warnung bei Netzwerk-, Hardware-, Import- oder Speicherwirkung |
| Mehr erfahren | Sprung zum passenden Abschnitt der Dialogdokumentation |

## Technischer Grundsatz

Hilfe und sichtbares Bedienelement müssen denselben Zustandsadapter verwenden.
Es darf keine zweite, manuell gepflegte Kopie des aktuellen Werts geben. Das
verhindert genau die im Output-Config- und Material-Browser-Audit gefundenen
Abweichungen zwischen Anzeige und wirksamem Systemwert.

Die Hilfedaten sollen deklarativ pro Dialog definiert werden. Ein gemeinsamer
Builder erzeugt daraus Symbol, Tooltip und Detailpanel. Wiederholtes Ausführen
des Builders muss bestehende Instanzen aktualisieren statt neue, überlagerte
Elemente anzulegen.

## Automatisierbare Abnahme

Für jedes Bedienelement wird geprüft:

1. Hilfe-ID ist eindeutig und dem sichtbaren Element zugeordnet.
2. Hover/Klick verändert keine fachlichen Parameter.
3. angezeigter Istwert entspricht der aktiven Quelle.
4. Wertebereich und Default entsprechen der Parameterdefinition.
5. Dokumentationsziel existiert.
6. Hilfepanel lässt sich per Maus, Escape und Tastaturfokus schließen.
7. wiederholter Build erzeugt keine Duplikate.

## Priorisierung

1. Router, Output Config, Show Control und Importaktionen wegen ihrer
   Hardware-/Persistenzwirkung.
2. Material Browser und Material Player wegen der vielen Werte und Presets.
3. Pixel Mapper wegen Koordinaten-, Import- und Exportsemantik.
4. LED Preview, MadMapper Library und Shortcut Help.

Die endgültigen Texte werden erst nach den neun Dialogaudits vervollständigt,
damit sie den nachgewiesenen Istzustand und nicht nur die beabsichtigte Funktion
beschreiben.

