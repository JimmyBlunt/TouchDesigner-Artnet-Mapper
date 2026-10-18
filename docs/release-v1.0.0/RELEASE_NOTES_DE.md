# Version 1.0.0 · 18. Oktober 2026

Die Bedienoberflächen verbinden die vorhandenen Scan-, Layout-, Material-,
Routing- und Show-Funktionen in einer kompakten Gestaltung mit Bahnschrift.
Zusammengehörige Aktionen stehen in dezent getrennten Bereichen; Eingaben und
Buttons haben abgerundete Ecken. Hintergrund: dunkles Cyan/Slate. Beschriftungen:
grauweiß; Werte: Cyan; Button- und aktive Schrift: Graphit.

- 24 bebilderte Anleitungen, 213 Feldhinweise, Info- und How-to-Zugänge.
- Direkte Controllerauswahl im Router und in der Portkonfiguration.
- Geprüfte Show-Auswahl, Neuerstellung, Bearbeitung sowie Speichern/Laden
  einschließlich Automation und Materialdaten.
- Portable Materialpfade und vollständige Bibliothek mit 638 Paketen,
  Originalquellen, Texturen und jeweiligen Lizenzhinweisen.
- Sechs unbenutzte historische DATs nach gesichertem Wiederherstellungstest
  entfernt. Alte Konfigurationen mit unklarer Verwendung bleiben erhalten.
- Panel 8: 299 Slots, 296 gemessene Positionen, fehlende IDs 1/61/93 bleiben
  schwarz; Dreieck nach unten und kurze Seite nach innen.

## Prüfung

1.782 Python-Tests und 5.117 Untertests bestanden; ein Windows-Symlink-Test
wegen fehlender Systemberechtigung übersprungen. Nach der abschließenden
Begrenzung der Vorschaubild- und Flächentexturauflösungen bestanden zusätzlich
39 gezielte Tests. Die Manager-Suite umfasst 10 bestandene Node-Tests.

Auch der vollständige Git-Export des Release-Commits `25c7448` wurde unabhängig
von lokalen, nicht versionierten Dateien getestet: **1.783 Tests bestanden,
1 übersprungen, 5.117 Untertests bestanden** in 105,37 Sekunden. Der zusätzliche
Test deckt die abschließende Texturauflösungsbegrenzung ab.
[Clean-Checkout-Ergebnis](qa/tests-clean-checkout.txt).

20 native Dialoge und 187 native Feldhinweise wurden auch nach dem Neustart
geprüft. Vier Webdialoge bestanden die Browserprüfung ohne Konsolen- oder
HTTP-Fehler. 181 Dokumentationsverweise wurden geprüft.

Der gespeicherte Release hat ausgeschaltete Sender. Nach dem Wiederöffnen
stimmen alle sieben zentralen Datenhashes, die erfassten Eingabewerte, 10.330
Quellslots und Theme 03 überein. TouchDesigner meldet keine Fehler/Warnungen.
Während der anschließenden Diagnose war die vom Benutzer gestartete Ausgabe
aktiv; sie wurde durch die lesende Wiederöffnungsprüfung nicht verändert.

TouchDesigner interpretiert die letzte Zahl eines Dateinamens als Speicherzähler.
Die Datei `PixelblazeMapper_v1.0.0.toe` ist deshalb ein bytegleiches Release-Abbild
des gespeicherten Projekts, das intern `PixelblazeMapper_v1.0.1.toe` heißen kann.
Das ändert die Anwendungsversion 1.0.0 nicht.

Siehe [Einzelbewertung aller Screens](SCREEN_ASSESSMENT_DE.md),
[Wiederöffnungsnachweis](qa/reopen-verification.json),
[native Kaltstartprüfung](qa/native-postreopen-check.json) und
[Browserprüfung](qa/browser-qa.json).

## Offene Hardware-/Integrationsprüfung

Bei der abschließenden Diagnose antwortet Controller `10.0.0.251` weder auf
Ping noch auf seine HTTP-API. Der Ethernet-Nachbareintrag bleibt unvollständig;
`10.0.0.253` antwortet. Der gemeinsame Sender läuft ohne gemeldeten Fehler,
mit U156–162 für `.251`, 299/357/195 LEDs und 1 ms Paketabstand. Es wurde
deshalb keine unbegründete Routingänderung vorgenommen. Stromversorgung,
Netzwerkverbindung und Geräteerreichbarkeit müssen vor der Hardwareabnahme
wiederhergestellt werden. [Diagnose](qa/controller-251-network.json).
Der Benutzer bestätigt Stromversorgung und leuchtende Netzwerk-LEDs sowie die
Funktion der anderen Controller. Ein gezielter Neustart von `.251` wurde
angefragt; seine erfolgreiche Wiedererreichbarkeit ist noch nicht bestätigt.

Der optionale externe PXLBLZ-Routerdienst unter Port 9988 ist ebenfalls nicht
erreichbar. Seine Manager-Oberfläche funktioniert und kennzeichnet gespeicherte
Paketdaten ausdrücklich. Physische Lichtausgabe, Kameraaufnahme und mechanische
MK2-Eingaben sind durch die Softwaretests nicht vollständig abgenommen.
