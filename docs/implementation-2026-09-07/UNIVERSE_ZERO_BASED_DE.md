# Einheitliche Art-Net-Adressen (8. September 2026)

Controller & Ports, GICO-Eingabe und Guided-Scan-Zusammenfassung verwenden
jetzt die tatsächliche Art-Net-Adresse ab 0. Beispiel: Start 120, 256 RGB-LEDs,
510 Kanäle je Universe ergibt U120–U121. Keine zusätzliche Anzeigeverschiebung.

Kompatibilität: Bestehende Router-Tabellen bleiben unverändert. Nur das alte
GICO-Datenmodell/settings speichert weiterhin ab 1; sein UI-Adapter übersetzt
beim Lesen und Schreiben. Keine Migration historischer Installationstabellen.
Beim Hot-Update werden ungespeicherte Eingaben übernommen und die bisherigen
Universe-Anzeigen einmalig um 1 reduziert; die tatsächlichen Adressen bleiben gleich.

Safe Apply: Abschaltung prüft den Operatortyp dmxout statt des Namenspräfixes.
Constant/Select-Hilfsoperatoren werden nicht als Ausgänge behandelt; echte
DMX-Ausgänge werden auch bei abweichenden Namen geprüft. Fehler bleiben blockierend.

Tabellenüberschriften: Der obsolete, undurchsichtige port_header wird ausgeblendet;
er überlagerte bisher die obere Hälfte der einzelnen Spaltenüberschriften.

Verifiziert: 87 gezielte Unittests bestanden; Live-Abschaltprüfung bestanden,
Controller-/Segmenttabellen unverändert, Entwurf Start 120, keine Operatorfehler.
Kein Scan, keine LED-Ausgabe und keine neue Controller-Zuordnung gestartet.
Visuelle Abnahme der Tabelle und kompletter Safe-Apply-Aufbau folgen beim Benutzertest.
