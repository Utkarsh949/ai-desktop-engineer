"""
themes.py — Colour palette & styling constants for the neon-dark UI.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class NeonTheme:
    # ── Base backgrounds ─────────────────────────────────────────────────────
    bg_deep: str = "#050810"        # deepest background
    bg_dark: str = "#0A0D1A"        # primary panel bg
    bg_card: str = "#0F1525"        # card / widget bg
    bg_input: str = "#12192E"       # input / textarea bg
    bg_hover: str = "#1A2340"       # hover state
    bg_active: str = "#1E2C4A"      # active / selected

    # ── Neon accents ─────────────────────────────────────────────────────────
    accent_cyan: str = "#00D4FF"    # primary neon
    accent_blue: str = "#4F8EFF"    # secondary
    accent_purple: str = "#9B59FF"  # tertiary
    accent_green: str = "#00FF88"   # success / low risk
    accent_yellow: str = "#FFD700"  # warning / medium risk
    accent_orange: str = "#FF8C00"  # high risk
    accent_red: str = "#FF3333"     # critical / error

    # ── Text ─────────────────────────────────────────────────────────────────
    text_primary: str = "#E8F0FF"
    text_secondary: str = "#8A9BC4"
    text_muted: str = "#4A5580"
    text_code: str = "#C8D8FF"

    # ── Borders ──────────────────────────────────────────────────────────────
    border_dim: str = "#1A2340"
    border_glow: str = "#00D4FF33"
    border_card: str = "#1E2C4A"

    # ── Severity ─────────────────────────────────────────────────────────────
    severity_critical: str = "#FF3333"
    severity_high: str = "#FF8C00"
    severity_medium: str = "#FFD700"
    severity_low: str = "#00FF88"

    # ── Font ─────────────────────────────────────────────────────────────────
    font_family: str = "Consolas"
    font_ui: str = "Segoe UI"
    font_size_sm: int = 11
    font_size_md: int = 13
    font_size_lg: int = 16
    font_size_xl: int = 20
    font_size_title: int = 26

    # ── Corner radius ─────────────────────────────────────────────────────────
    radius_sm: int = 6
    radius_md: int = 10
    radius_lg: int = 16

    # ── Padding ───────────────────────────────────────────────────────────────
    pad_sm: int = 6
    pad_md: int = 12
    pad_lg: int = 20


THEME = NeonTheme()

# CustomTkinter appearance configuration
CTK_COLOURS = {
    "CTkFrame": {
        "fg_color": [THEME.bg_card, THEME.bg_card],
        "border_color": [THEME.border_card, THEME.border_card],
        "border_width": 1,
    },
    "CTkButton": {
        "fg_color": [THEME.accent_cyan, THEME.accent_cyan],
        "hover_color": [THEME.accent_blue, THEME.accent_blue],
        "text_color": [THEME.bg_deep, THEME.bg_deep],
        "border_color": [THEME.accent_cyan, THEME.accent_cyan],
        "corner_radius": THEME.radius_md,
    },
    "CTkLabel": {
        "text_color": [THEME.text_primary, THEME.text_primary],
        "fg_color": "transparent",
    },
    "CTkEntry": {
        "fg_color": [THEME.bg_input, THEME.bg_input],
        "border_color": [THEME.border_card, THEME.accent_cyan],
        "text_color": [THEME.text_primary, THEME.text_primary],
        "placeholder_text_color": [THEME.text_muted, THEME.text_muted],
        "corner_radius": THEME.radius_md,
    },
    "CTkTextbox": {
        "fg_color": [THEME.bg_input, THEME.bg_input],
        "border_color": [THEME.border_card, THEME.border_card],
        "text_color": [THEME.text_primary, THEME.text_primary],
        "corner_radius": THEME.radius_md,
    },
    "CTkComboBox": {
        "fg_color": [THEME.bg_input, THEME.bg_input],
        "border_color": [THEME.border_card, THEME.accent_cyan],
        "button_color": [THEME.accent_cyan, THEME.accent_cyan],
        "text_color": [THEME.text_primary, THEME.text_primary],
        "corner_radius": THEME.radius_md,
    },
    "CTkScrollableFrame": {
        "fg_color": [THEME.bg_card, THEME.bg_card],
        "scrollbar_button_color": [THEME.accent_cyan, THEME.accent_cyan],
    },
    "CTkProgressBar": {
        "fg_color": [THEME.bg_hover, THEME.bg_hover],
        "progress_color": [THEME.accent_cyan, THEME.accent_cyan],
        "corner_radius": THEME.radius_sm,
    },
}


def severity_color(severity: str) -> str:
    return {
        "CRITICAL": THEME.severity_critical,
        "HIGH": THEME.severity_high,
        "MEDIUM": THEME.severity_medium,
        "LOW": THEME.severity_low,
    }.get(severity.upper(), THEME.text_secondary)


def score_color(score: int) -> str:
    """Return a colour based on a 0-100 risk score."""
    if score >= 75:
        return THEME.severity_critical
    if score >= 50:
        return THEME.severity_high
    if score >= 25:
        return THEME.severity_medium
    return THEME.severity_low
