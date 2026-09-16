"""Canonical, non-destructive TouchDesigner navigation shortcuts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ShortcutSpec:
    key: str
    label: str
    target: str
    purpose: str

    @property
    def combo(self) -> str:
        return f"Ctrl+Shift+{self.key.upper()}"


SHORTCUTS = (
    ShortcutSpec("1", "LED PREVIEW", "/project1/LED_PREVIEW_OUT", "Verbindliche Foto-/Schrankansicht mit gemappten LEDs"),
    ShortcutSpec("2", "MATERIAL BROWSER", "/project1/material_browser", "Core- und importierte Materialien auswählen"),
    ShortcutSpec("3", "MADMAPPER LIBRARY", "/project1/madmapper_library/ui_panel", "MadMapper-Materialien suchen, prüfen und importieren"),
    ShortcutSpec("4", "MATERIAL PLAYER", "/project1/madmapper_player_controls/ui_panel", "Aktuelles Rohmaterial und Player-Steuerung prüfen"),
    ShortcutSpec("5", "PIXEL MAPPER", "/project1/pixelblaze_mapper/ui/canvas", "LED-Koordinaten und Mapping bearbeiten"),
    ShortcutSpec("6", "ART-NET ROUTER", "/project1/multi_controller_output/ui_panel", "Controller, IP, Universen und sichere Ausgabe bedienen"),
    ShortcutSpec("7", "OUTPUT CONFIG", "/project1/pixelblaze_mapper/output_config/ui_panel", "Schreibgeschützten Live-Status prüfen und Art-Net Router öffnen"),
    ShortcutSpec("8", "SHOW CONTROL", "/project1/show_control/control_panel", "Cues, Übergänge und Show-Ablauf steuern"),
    ShortcutSpec("9", "SHORTCUT HELP", "/project1/shortcut_hub/help_panel", "Diese Shortcut-Übersicht öffnen"),
    ShortcutSpec("0", "GICO PORT CONFIG", "/project1/multi_controller_output/gico_port_config/ui_panel", "Globale Universen pro Port und feste GICO-Portblöcke konfigurieren"),
    ShortcutSpec("l", "LAYOUT + 2D EDITOR", "/project1/layout_scene_editor/ui_panel", "Layout, Objekte und 2D-Fixtures gemeinsam bearbeiten"),
    ShortcutSpec("g", "GUIDED SCAN", "/project1/guided_scan/ui_panel", "Geführten Scan vorbereiten und Messfortschritt prüfen"),
    ShortcutSpec("s", "LED SEARCH", "/project1/guided_scan/led_search_panel", "Controller, Ausgang und LED direkt fuer den Leuchttest waehlen"),
    ShortcutSpec("c", "CONTROLLER PORTS", "/project1/multi_controller_output/gico_port_config/controller_ports/ui_panel", "Controller und unabhängige Portkapazitäten als Entwurf bearbeiten"),
)


def validate_shortcuts(shortcuts=SHORTCUTS) -> tuple[str, ...]:
    issues: list[str] = []
    keys: set[str] = set()
    targets: set[str] = set()
    for item in shortcuts:
        if len(item.key) != 1 or item.key.lower() not in '0123456789abcdefghijklmnopqrstuvwxyz':
            issues.append(f"invalid key: {item.key!r}")
        if item.key.lower() in keys:
            issues.append(f"duplicate key: {item.key}")
        keys.add(item.key.lower())
        if not item.target.startswith("/project1/"):
            issues.append(f"target outside /project1: {item.target}")
        if item.target in targets:
            issues.append(f"duplicate target: {item.target}")
        targets.add(item.target)
    return tuple(issues)


def shortcut_rows(shortcuts=SHORTCUTS) -> tuple[tuple[str, ...], ...]:
    return (("shortcut", "label", "target", "purpose"),) + tuple(
        (item.combo, item.label, item.target, item.purpose) for item in shortcuts
    )
