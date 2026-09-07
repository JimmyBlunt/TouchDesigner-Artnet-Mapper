# Aktive Layout-Übernahme: 3D-Positionen und 2D-Material-UV

Stand 2026-09-07. Neues Modul `pixelblaze_mapper/build_layout_apply.py`, einschließlich Regression gegen unbeabsichtigte 3D-Änderungen im 2D-Modus. Der Teilauftrag hat die Live-Verbindungen ausschließlich gelesen; Installation und echte Übernahme bleiben beim Hauptauftrag.

## Verifizierter bestehender Datenweg

Live gelesen: `pixelblaze_mapper/map_active` enthält 3744 Punkte mit `index,tx,ty,tz`. Es ist über `map_active_out → selectDat → evaluate1` verbunden. `LedMap` liest `evaluate1` in seinem Callback, danach folgen `null4 → effect_sample_uv → topto1 → bestehende Show-/Ausgabekette`. `topto1` liest weiterhin `/project1/res1` als Material-TOP.

Die vorhandene `effect_sample_uv_callbacks`-Funktion liest die Tabelle `pixelblaze_mapper/effect_panel_uv`, nicht automatisch die neu geschriebenen 3D-Punkte. Auch die Show-UV-Callbacks benutzen diese Tabelle. Eine alleinige Änderung von `map_active` wäre deshalb keine vollständige Material-Mapping-Übernahme.

Der vorhandene `read_LED_map`-Callback verschiebt jede Achse mit negativem Minimum automatisch ins Positive. Ausschließlich beim ausdrücklichen **3D-Apply** erhält `LedMap` eine separate, geprüfte Callbackbindung: Tabellenpunkte werden indexgleich und ohne Verschiebung übernommen. **2D-Apply belässt sämtliche 3D-Callbackbindungen und tatsächlichen XYZ-Consumerwerte unverändert, einschließlich vorhandener Legacy-Verschiebungen.** Alter Callbacktext und alte Bindung werden im Snapshot erhalten; der Originalcallback wird nicht überschrieben.

## Bewusst unterschiedliche Modi

| Modus | Physische 3D-Positionen | Material-UV | Separate 2D-Anordnung |
| --- | --- | --- | --- |
| 3D | Geprüfte `Scene.world_points`, vollständige Source-Reihenfolge, negative Werte bleiben erhalten | Explizite Projektion XY/YX/XZ/ZX/YZ/ZY; Standard Y horizontal/X vertikal; außerhalb 0..1 blockiert | Workspace bleibt archiviert, aber keine automatische Abflachung |
| 2D | `map_active` wird **nicht geschrieben**; 3D-Callbackbindungen und tatsächliche `LedMap`-/`null4`-XYZ bleiben exakt unverändert | Vollständige Fixture-UV mit expliziter Translation/Rotation/Skalierung | Output-Fixturepunkte separat in `active_fixture_output`, niemals als Ersatz für die physischen XYZ |

In beiden Modi bleiben Routing, Universen, Controllerparameter, Source-Indizes und der globale Materialpfad `res1` unverändert. Dokumentierte Objekt-/Portbindungen sind bei diesem Apply weiterhin **Entwurfsabsicht** und werden nicht als fertiges Routing ausgegeben. Der Nutzer muss die Beibehaltung des vorhandenen Routings ausdrücklich bestätigen.

Die gemeinsam verwendete UV-Tabelle erhält pro LED die ausdrücklich gewählte UV sowohl in den globalen als auch den lokalen Spalten. Dadurch können die bisherigen Global/Panel/Hybrid-Schalter die bestätigte Workspace-Materialplatzierung nicht still neu einpassen. Dies ist eine sichtbare neue Workspace-Mapping-Semantik; sie muss im Apply-Dialog genannt werden. Die Show-Slots lesen weiterhin dieselbe Tabelle.

## Bereitgestellte Schnittstelle

Der Builder erzeugt nur neue, zunächst unverbundene Operatoren unter `/project1/layout_apply`; er aktiviert keinen Ausgang und ändert keine bestehende Callbackbindung. Die dortige `runtime.module` bietet:

- `prepare(mode, projection='YX', preserve_routing=True)`: liest aktuellen Layout-/Fixture-Entwurf, prüft ihn und speichert eine unveränderliche Vorbereitung. Der Parameter muss eine tatsächlich getroffene Bestätigung repräsentieren, keinen versteckten UI-Default.
- `apply()`: prüft denselben Workspace und aktiven Zustand erneut; erst danach wird geschrieben und am gekochten Datenweg verifiziert.
- `revert()`: stellt genau die letzte Übernahme wieder her, wenn seitdem kein anderer aktiver Mapping-/Routingstand entstanden ist.

Archivierte aktive Daten: `active_workspace` (verlustfreier Entwurf inklusive Rohscans, Objekttransform und beiden Fixture-Domänen), `active_map_3d` (autoritative XYZ), `active_fixture_output` (separate 2D-Anordnung), `active_settings` (Modus, Projektion, Revision, Anzahl, Routing-/UV-Semantik). Keine Dateien und keine TOE-Projekte werden automatisch gespeichert; dauerhafte Speicherung erfolgt über den vorhandenen bewussten Projekt-/Workspace-Save.

## Transaktionsgrenzen

Vor dem ersten Schreiben:

1. Ausgang muss bereits OFF sein; diese Funktion startet **und stoppt** keinen Sender. Ungültige Entwürfe verändern auch den Ausgangszustand nicht.
2. Vollständige, lückenlose Source-Abdeckung mit exakt aktueller LED-Anzahl. Append darf im Entwurf vorbereitet werden, eine veränderte Ausgangsanzahl braucht aber separat geprüftes Routing und wird hier blockiert.
3. 2D-Fixtures müssen zum exakten 3D-Szenenstand passen, alle IDs übernehmen und dürfen keine fehlenden/außerhalb liegenden UV-Punkte enthalten. Kein Clamp/Normalize.
4. Alle bekannten kanonischen Verbindungen, `res1`, Callbackbindungen, bestehende Routerkonfiguration und Downstream-Anzahlen werden geprüft.
5. Workspacehash umfasst 3D- und beide 2D-Domänen. Aktiver Hash umfasst betroffene Tabellen, Originalcallbacks, Callback-/Materialbindungen und feste Verbindungen. Zweiter Hashvergleich nach Snapshot verhindert veraltete Vorbereitungen.

Apply läuft synchron auf TDs Hauptthread mit einem eigenen Reentrancy-Lock. Es beansprucht keinen universellen Lock gegenüber beliebigen externen Skripten; gleichzeitige fremde Änderungen sind nicht erlaubt und werden soweit möglich über Hash/Verifikation erkannt.

Nach dem Schreiben werden XYZ-/UV-CHOPs, vorhandene Show-UVs und Sampler neu berechnet. Im 3D-Modus werden tatsächliche XYZ gegen die exakten neuen Tabellenpunkte geprüft. Im 2D-Modus werden stattdessen sämtliche XYZ-Kanalwerte von `LedMap` und `null4` exakt gegen den vorherigen Consumer-Snapshot geprüft, ebenso alle Callbackbindungen einschließlich `LedMap`. Ein vorhandener Legacy-Offset darf somit weder verschwinden noch als falscher Prüfungsfehler gegen die Rohdaten verglichen werden. Tabellen, tatsächliche UV-Werte, Anzahl, unverändertes Routing und unveränderte Verbindungen werden zusätzlich geprüft. Ein Fehler führt zur Wiederherstellung des Snapshots und erneutem Cook. Scheitert die Wiederherstellung, wird **ROLLBACK FAILED** ausdrücklich gemeldet; kein Erfolg und kein automatischer Output-Wiederanlauf. Fremde Routingänderungen werden nicht durch blindes Rückschreiben alter Routingtabellen überschrieben.

## Testnachweis und ausstehende Live-Abnahme

```powershell
python -m unittest discover -s tests -p 'test_layout_apply.py' -v
```

Die zwei zuerst ergänzten Regressionstests schlugen vor dem Fix fehl: 2D überschrieb die Legacy-Callbackbindung und verwarf unveränderte Display-XYZ mit bestehendem Offset. Nach dem Fix prüfen sie den tatsächlichen TD-Writer und Verifier auf unveränderte 3D-Verarbeitung. Weitere Tests decken physische Map, negative 3D-Koordinaten, Source-Anzahl/Routingbestätigung, fehlenden aktiven Snapshot, Bounds, Apply/Rollback, Ausgang ON/veraltete Zustände, Workspaceänderung, gefälschte Payload und Snapshot-Rennen ab.

Diese Tests benutzen kleine künstliche Fixtures und einen injizierten Speicheradapter. Sie beweisen kein echtes TD-Cook-/Verbindungsverhalten. Hauptauftrag muss den Live-Build, Prepare/Apply/Revert mit ausgeschalteten Ausgängen, exakte 3744 IDs, erhaltene negative XYZ, tatsächliche UV-CHOPwerte, unveränderte Routertabellen und Originalmaterialpfad prüfen. Kamerascans bleiben unabhängig davon unimplementiert/gesperrt; hier wird keine Rekonstruktion vorgetäuscht.
