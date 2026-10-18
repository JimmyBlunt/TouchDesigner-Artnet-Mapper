# Bereinigung und Wiederherstellung · v1.0.0

Vor der Bereinigung wurden Quellcode, Konfiguration, Shows und Arbeitsänderungen
unter `Backup/release-v1.0.0-before/` gesichert. Das vollständige laufende Projekt
liegt lokal als `PixelblazeMapper_BEFORE_RELEASE_1_0_0.toe` vor. Diese Sicherungen
sind lokale Wiederherstellungspunkte und nicht zwingend Teil des Git-Repositories.

## Entfernte Altlasten

Die lesende Prüfung fand für die folgenden sechs Root-DATs weder Verweise noch
Ein-/Ausgangsverbindungen. Sie wurden zuerst archiviert und in einem temporären
COMP vollständig aus dem Archiv wiederhergestellt. Erst nach erfolgreichem
Vergleich wurden die Originale entfernt.

- `effect_sample_uv_callbacks1`
- `legacy_source_mask_callbacks1`
- `esp_artnet_live_pack_callbacks1`
- `esp_artnet_test_pattern_callbacks1`
- `DMX_Universes_backup_pre_panels`
- `dmxout1_routingtable_backup_pre_panels`

[Kandidaten und Referenzprüfung](qa/legacy-candidates.json) ·
[Vollständige DAT-Inhalte](qa/legacy-dats-backup.json) ·
[Ergebnis mit restore_verified](qa/cleanup-result.json)

Vier Einträge sind unreferenzierte Standardcallback-Duplikate; zwei enthalten
alte Universen-/Routingtabellen. Nach dem Entfernen meldete der Prüfaufruf keine
Projektfehler. Die Ausgabe blieb ausgeschaltet.

## Gezielte Wiederherstellung

In TouchDesigner den Inhalt von `tools/release_cleanup.py` in einem geeigneten
Python-/Text-DAT-Kontext ausführen, damit seine Funktionen geladen sind.
Anschließend ausschließlich die Wiederherstellungsfunktion aufrufen:

```python
restore(op('/project1'))
```

`restore` rekonstruiert Namen, DAT-Typ, Text beziehungsweise Tabellenzellen und
Netzwerkpositionen aus dem Archiv. Existiert ein Name bereits, bricht die Funktion
ab, statt ihn zu überschreiben. Die Funktion `clean()` nicht zur Wiederherstellung
aufrufen. Für einen exakt vollständigen historischen Zustand einschließlich aller
Operatorparameter die vorherige `.toe`-Sicherung öffnen.

## Bewusst erhalten

Die deaktivierte `APA102_ESP`-Route und ältere Fixture-Daten bleiben bestehen.
Ihre funktionale Herkunft beziehungsweise vollständige Entbehrlichkeit war nicht
zweifelsfrei belegt. Eine deaktivierte Konfiguration ist nicht automatisch Müll.
Historische Anleitungen und Prüfnachweise werden über den
[Archivindex](historical-docs.html) eingeordnet, nicht rückwirkend umgeschrieben.
