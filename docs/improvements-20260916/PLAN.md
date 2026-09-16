# Verbesserungsplan 2026-09-16

Grundlage: vollständige Projektanalyse vom 16.09.2026 (fünf parallele Teilanalysen
am laufenden System über die TouchDesigner-MCP-Verbindung).

- **Branch:** `improve/audit-20260916`
- **Baseline-Commit:** `4f35d5a` (Arbeitsstand) + `4ad5ca3` (TouchDesigner-Snapshot)
- **Baseline-Datei:** `PixelblazeMapper_BASELINE_20260916.toe`, direkt aus der
  laufenden Instanz gespeichert, damit Git und Live-System übereinstimmen.

## Versionierungsverfahren

TouchDesigner-Netzwerke lassen sich nicht sinnvoll diffen. Deshalb wird jede
Netzwerkänderung **zusätzlich als ausführbares Skript** unter `steps/` abgelegt:
idempotent, mit `apply()` und `revert()`. Das ergibt eine lesbare, umkehrbare
Historie dessen, was am Netz verändert wurde — etwas, das eine `.toe`-Kopie
nicht leisten kann. `.toe`-Schnappschüsse werden nur an Gruppengrenzen
committet, nicht pro Einzeländerung.

Ein Commit pro Änderung. Commit-Nachricht nennt Wirkung und Messwert.

## Risikoklassen

| Klasse | Bedeutung |
|---|---|
| **B** | Kein Einfluss auf die Hardware-Ausgabe. Wird eigenständig umgesetzt. |
| **C** | Beeinflusst Rendering oder Projektstruktur, nicht das Ausgabeprotokoll. Eigenständig, mit Vorher-/Nachher-Messung. |
| **D** | Greift in die laufende Art-Net-Ausgabe ein. Wird vorbereitet und committet, aber **erst nach ausdrücklicher Freigabe aktiviert.** |

---

## Gruppe B — sichere Korrekturen

| ID | Änderung | Ort | Status |
|---|---|---|---|
| B1 | Toten Frame-Cook abschalten (1.776.293 Cooks ins Leere) | `/project1/chopexec1` → `script4` | erledigt |
| B2 | Tastenbelegung korrigieren (`pgup`/`pgdn`/`esc`) | `layout_scene_editor/keyboard` + `layout_scene_td.key()` | erledigt |
| B3 | Suchfeld auf Enter reagieren lassen | `material_browser/unified_search` | erledigt |
| B4 | Überlagerung der Parameterschublade auflösen | `material_browser/native_parameter_drawer` | erledigt |
| B5 | Statusanzeige des Routers drosseln (87 ms alle 250 ms) | `multi_controller_output/router_status_execute` | erledigt |
| B6 | Destruktive Buttons farblich kennzeichnen | `layout_scene_editor/ui_panel` | erledigt |
| B7 | Shortcut-Buttons beschriften (14 leere Labels) | `shortcut_hub/help_panel/open_*` | erledigt |
| B8 | `preview3d`-Treiber an Viewer-Sichtbarkeit koppeln | `pixelblaze_mapper/preview3d/animation_driver` | erledigt |
| B9 | Tote Pfade markieren statt löschen (`node_status`-Tabelle) | `/project1/node_status` (neu) | erledigt |

## Gruppe C — Performance

| ID | Änderung | Ort | Erwartung | Status |
|---|---|---|---|---|
| C1 | LED-Abtastpunkte vektorisieren | `effect_sample_uv_callbacks` | 261 ms → < 5 ms | offen |
| C2 | Durchleite-Knoten entfernen | `/project1/res1` | ein GPU-Blit/Frame gespart | offen |
| C3 | Undo-Historie deduplizieren | `layout_scene_editor` Storage | 160 MB → wenige MB, Kaltstart 82 s → < 1 s | offen |

## Gruppe D — Eingriffe in die Live-Ausgabe (Freigabe erforderlich)

| ID | Änderung | Ort | Warum heikel |
|---|---|---|---|
| D1 | Echte Schwarzschaltung beim Stoppen | `routing_transaction.stop_outputs()` | Sendet erstmals aktiv Nullpakete an die Controller |
| D2 | `time.sleep()` aus dem Main-Thread | `artnet_510_sender_callbacks` | Verändert das Sendetiming der laufenden Installation |
| D3 | Watchdog im Direktmodus | `multi_controller_output` | Kann die Ausgabe selbsttätig abschalten |

D1 behebt den schwerwiegendsten Befund der Analyse: Stopp, Absturz und
Netzwerkausfall lassen die LEDs derzeit im letzten Bild eingefroren stehen,
statt sie zu löschen.

---

## Nicht in diesem Durchgang

Bewusst zurückgestellt, weil sie größere Eingriffe sind und eigene Abstimmung
verdienen: das Auflösen der doppelten LED-Positionsquelle, das Auslagern des
353-Knoten-Prototyps, die Konsolidierung der Konfigurationsquellen, das
Entfernen der 63 toten Browser-Knoten und die Vereinheitlichung der
Panelgrößen. Sie stehen im Analysebericht mit Begründung.
