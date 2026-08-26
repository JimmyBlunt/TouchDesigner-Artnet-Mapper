# Einheitliche Bewertungsmatrix für die neun Dialoge

Diese Matrix wird erst nach Abschluss der jeweiligen Detailanalyse ausgefüllt.
Sie sorgt dafür, dass alle neun Dialoge nach denselben Maßstäben bewertet werden.

## Skala

Jede Kategorie erhält **0 bis 10 Punkte**:

- 0–1: nicht nutzbar oder nicht vorhanden
- 2–3: kritisch fehlerhaft, nur eingeschränkt nutzbar
- 4–5: grundlegend vorhanden, aber mit deutlichen Lücken
- 6–7: gut nutzbar, einzelne relevante Schwächen
- 8–9: sehr gut, robust und weitgehend vollständig
- 10: außergewöhnlich vollständig, konsistent und nachweislich robust

Ein hoher Innovationswert kann niemals einen Zuverlässigkeits- oder
Sicherheitsmangel ausgleichen. Die Gesamtpunktzahl ist deshalb nur eine
Orientierung; Blocker werden separat ausgewiesen.

## Kategorien

| Kategorie | Bewertungsfragen |
|---|---|
| Nutzbarkeit | Ist der Dialog verständlich, effizient, gut lesbar und ohne unnötige Umwege bedienbar? |
| Technische Umsetzung | Sind Datenbindungen, Zustände, Aktionen und Fehlerbehandlung sauber realisiert? |
| Zuverlässigkeit | Stimmen sichtbare Werte mit dem aktiven System überein und wirken Aktionen reproduzierbar? |
| Wartbarkeit | Gibt es klare Zuständigkeiten, idempotente Builder, Tests und wenig versteckte Kopplung? |
| Vollständigkeit | Sind alle für den Zweck nötigen Informationen, Aktionen, Rückmeldungen und Hilfen vorhanden? |
| Innovativität | Unterstützt der Dialog den speziellen LED-/Show-Workflow auf eine besonders hilfreiche Weise? |

## Pflichtinhalt jedes Dialogabschlusses

1. Zweck und tatsächlicher Signal-/Datenweg
2. Inventar aller sichtbaren Werte, Felder, Buttons und Statusanzeigen
3. Ergebnis echter Maus-, Tastatur- und Eingabetests
4. Nachweis der erwarteten Wirkung und Wiederherstellung des Ausgangswerts
5. Abgleich sichtbarer Werte mit dem aktiven Systemzustand
6. vorhandene automatische Tests und noch nicht automatisierbare Hardwaretests
7. Screenshots und mindestens ein dokumentierter Anwendungsfall
8. Fehler, Risiken, Doppelungen und fehlende Funktionen
9. begründete Punkte in allen sechs Kategorien
10. Verbesserungen mit Priorität `Blocker`, `Hoch`, `Mittel` oder `Optional`

## Gesamtübersicht

Der Abschlussbericht enthält eine Vergleichstabelle aller Dialoge und trennt:

- bestätigte Fehler;
- technisch fragile, aktuell aber funktionierende Stellen;
- Bedienungs- und Dokumentationslücken;
- Doppelungen zwischen Dialogen;
- fehlende Funktionen;
- optionale Komfort- und Innovationsideen.

Erst danach folgt eine priorisierte Umsetzungsliste. Funktionale Änderungen
werden nur nach Rücksprache freigegeben.

