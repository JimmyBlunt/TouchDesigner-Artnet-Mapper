"""Non-destructive contracts for the shortcut-reachable TouchDesigner dialogs.

This module intentionally describes *what can be checked without a running UI*.
It is used by the automated regression suite so a future builder change cannot
silently remove a shortcut target or reintroduce an unsafe direct-output action.
Live hardware actions (DMX enable/apply/blackout) are deliberately excluded from
automated clicking and must be confirmed in a supervised hardware session.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DialogContract:
    key: str
    label: str
    target: str
    implementation: str | None
    purpose: str
    safe_actions: tuple[str, ...] = ()
    guarded_actions: tuple[str, ...] = ()


DIALOGS: tuple[DialogContract, ...] = (
    DialogContract("1", "LED PREVIEW", "/project1/LED_PREVIEW_OUT", None,
                   "Verbindliche Foto- und LED-Vorschau."),
    DialogContract("2", "MATERIAL BROWSER", "/project1/material_browser",
                   "pixelblaze_mapper/build_unified_material_browser.py",
                   "Core- und importierte Materialien wählen.",
                   ("Suche", "Filter", "Seite", "Layout", "Materialwahl"),
                   ("Live-Vorschau öffnen",)),
    DialogContract("3", "MADMAPPER LIBRARY", "/project1/madmapper_library/ui_panel",
                   "pixelblaze_mapper/build_material_library_browser.py",
                   "Materialien suchen, prüfen und vorbereiten.",
                   ("Suche", "Filter", "Seite", "Kartenwahl"),
                   ("Import selected", "Refresh catalog")),
    DialogContract("4", "MATERIAL PLAYER", "/project1/madmapper_player_controls/ui_panel",
                   "pixelblaze_mapper/build_unified_material_browser.py",
                   "Aktuelles Material und Player-Zustand prüfen.",
                   ("Status lesen",), ("Materialwechsel",)),
    DialogContract("5", "PIXEL MAPPER", "/project1/pixelblaze_mapper/ui/canvas",
                   "pixelblaze_mapper/build_spatial_lookup_td.py",
                   "LED-Koordinaten und Mapping bearbeiten.",
                   ("Ansicht",), ("Mapping schreiben/exportieren",)),
    DialogContract("6", "ART-NET ROUTER", "/project1/multi_controller_output/ui_panel",
                   "pixelblaze_mapper/build_multi_controller_output.py",
                   "Controller-, Universen- und Kalibrierungssteuerung.",
                   ("Status lesen",), ("Output off", "Safe apply", "Start", "Kalibrierung")),
    DialogContract("7", "OUTPUT CONFIG", "/project1/pixelblaze_mapper/output_config/ui_panel",
                   "pixelblaze_mapper/build_phase2_output_ui.py",
                   "Schreibgeschützte Live-Zusammenfassung des Art-Net Routers.",
                   ("Live-Status lesen", "Art-Net Router öffnen"), ()),
    DialogContract("8", "SHOW CONTROL", "/project1/show_control/control_panel",
                   "pixelblaze_mapper/build_show_sequencer.py",
                   "Cues und Transport steuern.",
                   ("Transport-Status",), ("GO", "PLAY", "STOP", "BLACKOUT")),
    DialogContract("9", "SHORTCUT HELP", "/project1/shortcut_hub/help_panel",
                   "pixelblaze_mapper/build_shortcut_hub.py",
                   "Shortcut-Übersicht; nur Navigation."),
    DialogContract("0", "GICO PORT CONFIG",
                   "/project1/multi_controller_output/gico_port_config/ui_panel",
                   "pixelblaze_mapper/build_gico_port_config_ui.py",
                   "Globale GICO-Universenzahl und feste Portblöcke konfigurieren.",
                   ("Entwurf validieren",), ("Sicher anwenden",)),
)


def validate_dialog_contracts(dialogs: tuple[DialogContract, ...] = DIALOGS) -> tuple[str, ...]:
    issues: list[str] = []
    keys = [item.key for item in dialogs]
    targets = [item.target for item in dialogs]
    if keys != list("1234567890"):
        issues.append("shortcut keys must be 1 through 9 followed by 0")
    if len(set(targets)) != len(targets):
        issues.append("dialog targets must be unique")
    for item in dialogs:
        if not item.target.startswith("/project1/"):
            issues.append("target outside project1: " + item.target)
        if item.guarded_actions and not item.implementation:
            issues.append("guarded dialog has no implementation: " + item.label)
    return tuple(issues)
