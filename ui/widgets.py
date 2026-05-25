"""
widgets.py — Reusable CustomTkinter widget components.
All widgets follow the neon-dark design language.
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

import customtkinter as ctk
from themes.themes import THEME, severity_color, score_color


# ─────────────────────────────────────────────────────────────────────────────
#  Stat Card
# ─────────────────────────────────────────────────────────────────────────────

class StatCard(ctk.CTkFrame):
    """Animated stat card showing a metric + label."""

    def __init__(self, master, label: str, value: str = "—",
                 accent: str = THEME.accent_cyan, **kwargs):
        super().__init__(
            master,
            fg_color=THEME.bg_card,
            border_color=accent,
            border_width=1,
            corner_radius=THEME.radius_lg,
            **kwargs,
        )
        self._accent = accent

        self._val_var = tk.StringVar(value=value)
        self._lbl_text = label

        ctk.CTkLabel(
            self, text=label,
            text_color=THEME.text_secondary,
            font=(THEME.font_ui, THEME.font_size_sm),
        ).pack(pady=(14, 2))

        self._val_lbl = ctk.CTkLabel(
            self, textvariable=self._val_var,
            text_color=accent,
            font=(THEME.font_family, THEME.font_size_xl, "bold"),
        )
        self._val_lbl.pack(pady=(0, 14))

    def update_value(self, value: str, accent: Optional[str] = None) -> None:
        self._val_var.set(value)
        if accent:
            self._val_lbl.configure(text_color=accent)


# ─────────────────────────────────────────────────────────────────────────────
#  Neon Button
# ─────────────────────────────────────────────────────────────────────────────

class NeonButton(ctk.CTkButton):
    def __init__(self, master, text: str, command=None,
                 accent: str = THEME.accent_cyan,
                 width: int = 140, height: int = 38, **kwargs):
        super().__init__(
            master, text=text, command=command,
            width=width, height=height,
            fg_color=accent,
            hover_color=THEME.bg_hover,
            border_color=accent,
            border_width=1,
            text_color="#000000",
            font=(THEME.font_ui, THEME.font_size_md, "bold"),
            corner_radius=THEME.radius_md,
            **kwargs,
        )


class DangerButton(ctk.CTkButton):
    def __init__(self, master, text: str, command=None, **kwargs):
        super().__init__(
            master, text=text, command=command,
            fg_color=THEME.accent_red,
            hover_color=THEME.bg_hover,
            border_color=THEME.accent_red,
            border_width=1,
            text_color="#FFFFFF",
            font=(THEME.font_ui, THEME.font_size_md, "bold"),
            corner_radius=THEME.radius_md,
            **kwargs,
        )


class SuccessButton(ctk.CTkButton):
    def __init__(self, master, text: str, command=None, **kwargs):
        super().__init__(
            master, text=text, command=command,
            fg_color=THEME.accent_green,
            hover_color=THEME.bg_hover,
            border_color=THEME.accent_green,
            border_width=1,
            text_color="#000000",
            font=(THEME.font_ui, THEME.font_size_md, "bold"),
            corner_radius=THEME.radius_md,
            **kwargs,
        )


# ─────────────────────────────────────────────────────────────────────────────
#  Section Header
# ─────────────────────────────────────────────────────────────────────────────

class SectionHeader(ctk.CTkFrame):
    def __init__(self, master, title: str, subtitle: str = "",
                 accent: str = THEME.accent_cyan, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        # Accent bar
        ctk.CTkFrame(
            self, width=3, height=30,
            fg_color=accent, corner_radius=2,
        ).pack(side="left", padx=(0, 10), pady=4)

        text_frame = ctk.CTkFrame(self, fg_color="transparent")
        text_frame.pack(side="left", fill="both")

        ctk.CTkLabel(
            text_frame, text=title,
            text_color=THEME.text_primary,
            font=(THEME.font_ui, THEME.font_size_lg, "bold"),
        ).pack(anchor="w")

        if subtitle:
            ctk.CTkLabel(
                text_frame, text=subtitle,
                text_color=THEME.text_secondary,
                font=(THEME.font_ui, THEME.font_size_sm),
            ).pack(anchor="w")


# ─────────────────────────────────────────────────────────────────────────────
#  Code Editor (syntax-highlighted textbox)
# ─────────────────────────────────────────────────────────────────────────────

class CodeEditor(ctk.CTkTextbox):
    """Monospaced code editor with line numbers and paste support."""

    def __init__(self, master, **kwargs):
        defaults = dict(
            fg_color=THEME.bg_input,
            text_color=THEME.text_code,
            font=(THEME.font_family, THEME.font_size_md),
            corner_radius=THEME.radius_md,
            border_color=THEME.border_card,
            border_width=1,
            wrap="none",
        )
        defaults.update(kwargs)
        super().__init__(master, **defaults)

    def get_code(self) -> str:
        return self.get("1.0", "end-1c").strip()

    def set_code(self, code: str) -> None:
        self.delete("1.0", "end")
        self.insert("1.0", code)

    def clear(self) -> None:
        self.delete("1.0", "end")


# ─────────────────────────────────────────────────────────────────────────────
#  Report Viewer (read-only markdown-style text)
# ─────────────────────────────────────────────────────────────────────────────

class ReportViewer(ctk.CTkTextbox):
    def __init__(self, master, **kwargs):
        defaults = dict(
            fg_color=THEME.bg_input,
            text_color=THEME.text_primary,
            font=(THEME.font_family, THEME.font_size_sm),
            corner_radius=THEME.radius_md,
            border_color=THEME.border_card,
            border_width=1,
            wrap="word",
            state="disabled",
        )
        defaults.update(kwargs)
        super().__init__(master, **defaults)

    def set_text(self, text: str) -> None:
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.insert("1.0", text)
        self.configure(state="disabled")

    def append_text(self, text: str) -> None:
        self.configure(state="normal")
        self.insert("end", text)
        self.see("end")
        self.configure(state="disabled")

    def clear(self) -> None:
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.configure(state="disabled")


# ─────────────────────────────────────────────────────────────────────────────
#  Progress Bar with label
# ─────────────────────────────────────────────────────────────────────────────

class LabeledProgress(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._status_var = tk.StringVar(value="Ready")
        self._pct_var = tk.StringVar(value="")

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            top, textvariable=self._status_var,
            text_color=THEME.text_secondary,
            font=(THEME.font_ui, THEME.font_size_sm),
        ).pack(side="left")

        ctk.CTkLabel(
            top, textvariable=self._pct_var,
            text_color=THEME.accent_cyan,
            font=(THEME.font_ui, THEME.font_size_sm, "bold"),
        ).pack(side="right")

        self._bar = ctk.CTkProgressBar(
            self,
            fg_color=THEME.bg_hover,
            progress_color=THEME.accent_cyan,
            height=6,
            corner_radius=3,
        )
        self._bar.pack(fill="x")
        self._bar.set(0)

    def update(self, status: str, pct: int) -> None:
        self._status_var.set(status)
        self._pct_var.set(f"{pct}%")
        self._bar.set(pct / 100)
        if pct >= 100:
            self._bar.configure(progress_color=THEME.accent_green)
        else:
            self._bar.configure(progress_color=THEME.accent_cyan)

    def reset(self) -> None:
        self._status_var.set("Ready")
        self._pct_var.set("")
        self._bar.set(0)
        self._bar.configure(progress_color=THEME.accent_cyan)


# ─────────────────────────────────────────────────────────────────────────────
#  Risk Badge
# ─────────────────────────────────────────────────────────────────────────────

class RiskBadge(ctk.CTkLabel):
    def __init__(self, master, score: int = 0, severity: str = "LOW", **kwargs):
        color = score_color(score)
        super().__init__(
            master,
            text=f"  {score}/100 · {severity}  ",
            text_color=color,
            fg_color=color,
            font=(THEME.font_ui, THEME.font_size_sm, "bold"),
            corner_radius=THEME.radius_sm,
            **kwargs,
        )

    def update_risk(self, score: int, severity: str) -> None:
        color = score_color(score)
        self.configure(
            text=f"  {score}/100 · {severity}  ",
            text_color=color,
            fg_color=color,
        )


# ─────────────────────────────────────────────────────────────────────────────
#  Sidebar Nav Button
# ─────────────────────────────────────────────────────────────────────────────

class NavButton(ctk.CTkButton):
    def __init__(self, master, text: str, icon: str = "", command=None, **kwargs):
        self._active = False
        label = f"  {icon}  {text}" if icon else f"  {text}"
        super().__init__(
            master, text=label, command=command,
            anchor="w",
            fg_color="transparent",
            hover_color=THEME.bg_hover,
            text_color=THEME.text_secondary,
            font=(THEME.font_ui, THEME.font_size_md),
            corner_radius=THEME.radius_md,
            height=42,
            **kwargs,
        )

    def set_active(self, active: bool) -> None:
        self._active = active
        if active:
            self.configure(
                fg_color=THEME.accent_cyan,
                text_color="#000000",
                border_color=THEME.accent_cyan,
                border_width=1,
            )
        else:
            self.configure(
                fg_color="transparent",
                text_color=THEME.text_secondary,
                border_width=0,
            )


# ─────────────────────────────────────────────────────────────────────────────
#  Audit History Row (for dashboard table)
# ─────────────────────────────────────────────────────────────────────────────

class AuditHistoryTable(ctk.CTkScrollableFrame):
    """A lightweight table for displaying past audit results."""

    _COLS = ("Name", "Language", "Risk", "Severity", "Issues", "Time")

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=THEME.bg_card,
            corner_radius=THEME.radius_md,
            **kwargs,
        )
        self._rows: list[ctk.CTkFrame] = []
        self._render_header()

    def _render_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color=THEME.bg_hover, corner_radius=THEME.radius_sm)
        header.pack(fill="x", pady=(0, 2))
        widths = [200, 100, 80, 100, 80, 80]
        for col, w in zip(self._COLS, widths):
            ctk.CTkLabel(
                header, text=col,
                text_color=THEME.text_secondary,
                font=(THEME.font_ui, THEME.font_size_sm, "bold"),
                width=w, anchor="w",
            ).pack(side="left", padx=6, pady=6)

    def add_row(self, name: str, language: str, risk: int,
                severity: str, issues: int, elapsed: str) -> None:
        row = ctk.CTkFrame(
            self,
            fg_color=THEME.bg_card,
            corner_radius=THEME.radius_sm,
            border_color=THEME.border_dim,
            border_width=1,
        )
        row.pack(fill="x", pady=1)

        sev_color = severity_color(severity)
        data = [name, language, f"{risk}/100", severity, str(issues), elapsed]
        widths = [200, 100, 80, 100, 80, 80]
        colors = [
            THEME.text_primary, THEME.text_secondary,
            score_color(risk), sev_color,
            THEME.text_primary, THEME.text_muted,
        ]

        for text, w, c in zip(data, widths, colors):
            ctk.CTkLabel(
                row, text=text, text_color=c,
                font=(THEME.font_ui, THEME.font_size_sm),
                width=w, anchor="w",
            ).pack(side="left", padx=6, pady=6)

        self._rows.append(row)

    def clear_rows(self) -> None:
        for row in self._rows:
            row.destroy()
        self._rows.clear()
