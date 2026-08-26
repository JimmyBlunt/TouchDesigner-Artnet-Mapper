# P0: Dialogkonsolidierung

Stand: 26.08.2026. Diese Änderung ist zunächst nur in Buildern, reinem Python
und Offline-Tests vorbereitet. Sie wurde noch nicht in eine laufende
TouchDesigner-Datei eingebaut und verändert keine Hardwareausgabe.

## Verbindliche Zuständigkeit

`/project1/multi_controller_output` ist die einzige bearbeitbare
Art-Net-Ausgabekonfiguration. Dialog 7 unter
`/project1/pixelblaze_mapper/output_config/ui_panel` ist ausschließlich eine
schreibgeschützte Live-Zusammenfassung.

Die Zusammenfassung bezieht alle sichtbaren Werte aus folgenden Livequellen:

- Pixelzahl: `/project1/math1.numSamples`;
- Controller und Netzwerkeinstellungen: Router-Tabelle `controller_config`;
- tatsächlich reservierte Zielbereiche: Router-Tabelle `segment_config`;
- Validierung: Router-Tabelle `validation`;
- Senderzustand: `artnet_510_sender_callbacks.status()`.

Es gibt dort keine Draft-Tabelle, keine editierbaren Ableitungen und keine
Apply-/Revert-/Export-Aktion. Der einzige Button öffnet den Art-Net Router.
„Configured enabled“ und „Sender live“ werden bewusst getrennt dargestellt.

## Idempotenz

Der Output-Config-Builder ersetzt ausschließlich den isolierten COMP
`output_config` am gleichen öffentlichen Pfad. So können alte Custom-Parameter,
statische Texte und mehrfach angelegte Button-Handler nicht überleben.

Der Material-Browser behält Katalog, Importzustand, Materialquellen und Karten.
Vor seinem Layout-Aufbau löscht er ausschließlich numerisch suffigierte
Duplikate seiner generierten Singleton-Control-Familien. Kanonische Controls
und Materialquellen bleiben unberührt. Momentary-Handler werden typgeprüft und
unter genau einem Namen wiederverwendet.

## Abnahme vor TouchDesigner-Integration

1. Pure-Python-Tests für Liveableitung, Statusunterscheidung und Fehleranzeige.
2. Quellvertrag: keine Draft-/Apply-/Revert-Funktionen in Dialog 7.
3. Read-only-Vertrag: alle abgeleiteten Werte sind Text-Components.
4. Duplikat-Vertrag für Material-Browser-Namen und Handler.
5. Erst nach gemeinsamer Integration: Dialog 7 zweimal bauen, OP-Namen zählen,
   Routerwerte ändern und sichtbare Aktualisierung prüfen.
