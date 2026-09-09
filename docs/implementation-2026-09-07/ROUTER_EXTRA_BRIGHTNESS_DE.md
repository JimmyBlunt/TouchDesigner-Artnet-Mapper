# Helligkeit zusätzlicher Controller

Im ART-NET MULTI-CONTROLLER ROUTER befindet sich unter den beiden bisherigen
Controllerblöcken eine zusätzliche Zeile. Sie liest weitere Controller aus
`controller_config`, aktuell BACK_PANEL_249 / 10.0.0.249 / U120.

1. **Helligkeit 0..1** eingeben: `0.3` oder `0,3` bedeutet 30 Prozent.
2. **HELLIGKEIT LIVE SETZEN** klicken. Nur diese Helligkeitszelle wird verändert.
3. Rechts zeigt **Aktiv: … %** den übernommenen Wert. Kein Sender-Neustart,
   keine Übernahme anderer Entwurfsfelder und keine Änderung der Ports.
4. **LADEN** liest den aktuellen Tabellenwert erneut; unbestätigte Eingabe wird ersetzt.
5. Bei mehreren zusätzlichen Controllern wechseln **< / >** zwischen ihnen.

Die ursprünglichen beiden Controllerblöcke und der restliche Dialog sind
damit nicht vollständig dynamisch umgebaut. Die zusätzliche Auswahl ist
datengetrieben; neue Tabellenzeilen erscheinen nach LADEN bzw. Pfeilwechsel.
Es findet keine automatische Netzwerk-Erkennung unbekannter Geräte statt.

Prüfung: fünf automatisierte Validierungstests (Punkt/Komma, Grenzen,
ungültige und nicht endliche Werte). Echter Windows-Mausklick auf den Button
mit dem inzwischen vom Nutzer eingestellten Wert 0,9: Callback registriert
BACK_PANEL_249=0,9, Tabellenwert bestätigt, Sender blieb eingeschaltet,
keine Operatorfehler. Die Hardware-Helligkeitsänderung testet der Nutzer;
für den Klicktest wurde der aktuelle Wert nicht erhöht oder vermindert.
