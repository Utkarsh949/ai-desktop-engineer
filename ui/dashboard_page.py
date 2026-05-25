"""
dashboard_page.py — Main dashboard with stat cards, activity log,
risk overview, and recent audit table.
"""

from __future__ import annotations

import datetime
import random
import tkinter as tk
from typing import TYPE_CHECKING

import customtkinter as ctk

from themes.themes import THEME, score_color, severity_color
from ui.widgets import StatCard, SectionHeader, AuditHistoryTable, RiskBadge

if TYPE_CHECKING:
    from ui.main_gui import App


class DashboardPage(ctk.CTkFrame):
    def __init__(self, master: "App", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._app = master
        self._build()

    def _build(self) -> None:
        # ── Header ─────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 0))

        ctk.CTkLabel(
            hdr, text="⬡  Engineering Command Centre",
            text_color=THEME.accent_cyan,
            font=(THEME.font_ui, THEME.font_size_title, "bold"),
        ).pack(side="left")

        self._time_lbl = ctk.CTkLabel(
            hdr, text="",
            text_color=THEME.text_muted,
            font=(THEME.font_family, THEME.font_size_sm),
        )
        self._time_lbl.pack(side="right")
        self._tick_clock()

        # ── Stat Cards Row ─────────────────────────────────────────────────
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", padx=24, pady=16)

        self._card_audits = StatCard(cards_frame, "Total Audits", "0",
                                     accent=THEME.accent_cyan)
        self._card_audits.pack(side="left", expand=True, fill="both", padx=4)

        self._card_risk = StatCard(cards_frame, "Avg Risk Score", "—",
                                   accent=THEME.accent_orange)
        self._card_risk.pack(side="left", expand=True, fill="both", padx=4)

        self._card_issues = StatCard(cards_frame, "Issues Found", "0",
                                     accent=THEME.accent_red)
        self._card_issues.pack(side="left", expand=True, fill="both", padx=4)

        self._card_files = StatCard(cards_frame, "Files Scanned", "0",
                                    accent=THEME.accent_blue)
        self._card_files.pack(side="left", expand=True, fill="both", padx=4)

        self._card_health = StatCard(cards_frame, "Avg Health Score", "—",
                                     accent=THEME.accent_green)
        self._card_health.pack(side="left", expand=True, fill="both", padx=4)

        # ── Middle row: Recent Audits + Activity Log ───────────────────────
        mid = ctk.CTkFrame(self, fg_color="transparent")
        mid.pack(fill="both", expand=True, padx=24, pady=4)
        mid.columnconfigure(0, weight=3)
        mid.columnconfigure(1, weight=2)
        mid.rowconfigure(0, weight=1)

        # Recent Audits table
        left = ctk.CTkFrame(mid, fg_color=THEME.bg_card,
                            corner_radius=THEME.radius_lg,
                            border_color=THEME.border_card, border_width=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        SectionHeader(left, "Recent Audits", "Latest code review results").pack(
            fill="x", padx=16, pady=12)

        self._audit_table = AuditHistoryTable(left)
        self._audit_table.pack(fill="both", expand=True, padx=8, pady=(0, 12))

        # Activity Log
        right = ctk.CTkFrame(mid, fg_color=THEME.bg_card,
                             corner_radius=THEME.radius_lg,
                             border_color=THEME.border_card, border_width=1)
        right.grid(row=0, column=1, sticky="nsew")

        SectionHeader(right, "Activity Log", "Real-time events").pack(
            fill="x", padx=16, pady=12)

        self._log_box = ctk.CTkTextbox(
            right,
            fg_color=THEME.bg_input,
            text_color=THEME.text_secondary,
            font=(THEME.font_family, THEME.font_size_sm),
            corner_radius=THEME.radius_md,
            state="disabled",
            wrap="word",
        )
        self._log_box.pack(fill="both", expand=True, padx=8, pady=(0, 12))

        # ── Bottom: Quick Tips / Status ────────────────────────────────────
        bottom = ctk.CTkFrame(self, fg_color=THEME.bg_card,
                              corner_radius=THEME.radius_lg,
                              border_color=THEME.border_card, border_width=1)
        bottom.pack(fill="x", padx=24, pady=(4, 16))

        tips = [
            "💡  Tip: Use Triple-Pass Audit for production code reviews",
            "🔐  Security Pass checks OWASP Top 10 vulnerabilities",
            "⚡  Performance Pass analyses Big-O complexity",
            "🏗️  Architecture Pass detects code smells and SOLID violations",
        ]
        tip = random.choice(tips)
        ctk.CTkLabel(
            bottom, text=tip,
            text_color=THEME.text_muted,
            font=(THEME.font_ui, THEME.font_size_sm),
        ).pack(padx=16, pady=10, anchor="w")

    # ── Public API ────────────────────────────────────────────────────────────

    def log_event(self, message: str) -> None:
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self._log_box.configure(state="normal")
        self._log_box.insert("end", f"[{ts}] {message}\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def add_audit_row(self, name: str, language: str, risk: int,
                      severity: str, issues: int, elapsed: float) -> None:
        self._audit_table.add_row(
            name, language, risk, severity, issues, f"{elapsed:.1f}s"
        )
        # Update stat cards
        self._update_counters(risk, issues)
        self.log_event(f"Audit complete: {name} — risk={risk} severity={severity}")

    def add_scan_result(self, files: int, health: int) -> None:
        cur = self._card_files._val_var.get()
        try:
            total = int(cur) + files
        except ValueError:
            total = files
        self._card_files.update_value(str(total), THEME.accent_blue)
        self._card_health.update_value(
            str(health),
            score_color(100 - health),
        )
        self.log_event(f"Project scan: {files} files, health={health}/100")

    def _update_counters(self, risk: int, issues: int) -> None:
        # Audits
        cur = self._card_audits._val_var.get()
        try:
            new_total = int(cur) + 1
        except ValueError:
            new_total = 1
        self._card_audits.update_value(str(new_total))

        # Issues
        cur_issues = self._card_issues._val_var.get()
        try:
            new_issues = int(cur_issues) + issues
        except ValueError:
            new_issues = issues
        self._card_issues.update_value(str(new_issues), THEME.accent_red)

        # Risk average
        self._card_risk.update_value(str(risk), score_color(risk))

    def _tick_clock(self) -> None:
        now = datetime.datetime.now().strftime("%A, %d %b %Y  %H:%M:%S")
        self._time_lbl.configure(text=now)
        self.after(1000, self._tick_clock)
