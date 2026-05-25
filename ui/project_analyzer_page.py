"""
project_analyzer_page.py — Local project folder scanner.
Displays file stats, complexity hotspots, language breakdown,
duplicate detection, and project health score.
"""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING

import customtkinter as ctk

from themes.themes import THEME, score_color
from ui.widgets import LabeledProgress, NeonButton, SectionHeader, StatCard, SuccessButton

if TYPE_CHECKING:
    from ui.main_gui import App


class ProjectAnalyzerPage(ctk.CTkFrame):
    def __init__(self, master: "App", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._app = master
        self._report = None
        self._build()

    def _build(self) -> None:
        # ── Header ─────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 8))

        ctk.CTkLabel(
            hdr, text="📊  Local Project Analyzer",
            text_color=THEME.accent_blue,
            font=(THEME.font_ui, THEME.font_size_title, "bold"),
        ).pack(side="left")

        # ── Top: path selector ──────────────────────────────────────────────
        path_bar = ctk.CTkFrame(self, fg_color=THEME.bg_card,
                                corner_radius=THEME.radius_md,
                                border_color=THEME.border_card, border_width=1)
        path_bar.pack(fill="x", padx=24, pady=8)
        path_bar_inner = ctk.CTkFrame(path_bar, fg_color="transparent")
        path_bar_inner.pack(fill="x", padx=12, pady=10)

        self._path_var = tk.StringVar(value="No folder selected")
        ctk.CTkEntry(
            path_bar_inner, textvariable=self._path_var,
            fg_color=THEME.bg_input, border_color=THEME.border_card,
            text_color=THEME.text_primary,
            font=(THEME.font_family, THEME.font_size_sm),
            width=500, height=34,
        ).pack(side="left", fill="x", expand=True)

        NeonButton(path_bar_inner, "📁 Browse Folder",
                   command=self._browse, width=150, height=34,
                   accent=THEME.accent_blue).pack(side="left", padx=8)

        NeonButton(path_bar_inner, "🔍 Scan Project",
                   command=self._scan, width=140, height=34,
                   accent=THEME.accent_cyan).pack(side="left")

        # ── Progress ────────────────────────────────────────────────────────
        self._progress = LabeledProgress(self)
        self._progress.pack(fill="x", padx=24, pady=(0, 4))

        # ── Stat cards ──────────────────────────────────────────────────────
        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.pack(fill="x", padx=24, pady=4)

        self._c_files = StatCard(cards, "Files Scanned", "—", THEME.accent_blue)
        self._c_files.pack(side="left", expand=True, fill="both", padx=4)

        self._c_loc = StatCard(cards, "Lines of Code", "—", THEME.accent_cyan)
        self._c_loc.pack(side="left", expand=True, fill="both", padx=4)

        self._c_langs = StatCard(cards, "Languages", "—", THEME.accent_purple)
        self._c_langs.pack(side="left", expand=True, fill="both", padx=4)

        self._c_dups = StatCard(cards, "Duplicate Files", "—", THEME.accent_orange)
        self._c_dups.pack(side="left", expand=True, fill="both", padx=4)

        self._c_health = StatCard(cards, "Health Score", "—", THEME.accent_green)
        self._c_health.pack(side="left", expand=True, fill="both", padx=4)

        # ── Body: Language breakdown + Hotspots + File list ─────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=4)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        # Language breakdown
        left = ctk.CTkFrame(body, fg_color=THEME.bg_card,
                            corner_radius=THEME.radius_lg,
                            border_color=THEME.border_card, border_width=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        SectionHeader(left, "Language Breakdown", "Code lines per language").pack(
            fill="x", padx=16, pady=(14, 6))

        self._lang_frame = ctk.CTkScrollableFrame(
            left, fg_color="transparent",
        )
        self._lang_frame.pack(fill="both", expand=True, padx=8, pady=(0, 12))

        ctk.CTkLabel(
            self._lang_frame,
            text="Scan a project to see breakdown…",
            text_color=THEME.text_muted,
            font=(THEME.font_ui, THEME.font_size_sm),
        ).pack(pady=20)

        # Complexity hotspots + file list
        right = ctk.CTkFrame(body, fg_color=THEME.bg_card,
                             corner_radius=THEME.radius_lg,
                             border_color=THEME.border_card, border_width=1)
        right.grid(row=0, column=1, sticky="nsew")

        SectionHeader(right, "Complexity Hotspots", "Functions with high cyclomatic complexity").pack(
            fill="x", padx=16, pady=(14, 6))

        self._hotspot_frame = ctk.CTkScrollableFrame(
            right, fg_color=THEME.bg_input, corner_radius=THEME.radius_md, height=180,
        )
        self._hotspot_frame.pack(fill="x", padx=16, pady=(0, 8))

        self._hotspot_placeholder = ctk.CTkLabel(
            self._hotspot_frame,
            text="No data. Scan a Python project to detect hotspots.",
            text_color=THEME.text_muted,
            font=(THEME.font_ui, THEME.font_size_sm),
        )
        self._hotspot_placeholder.pack(pady=20)

        SectionHeader(right, "Largest Files", "Top files by line count").pack(
            fill="x", padx=16, pady=(8, 6))

        self._files_frame = ctk.CTkScrollableFrame(
            right, fg_color=THEME.bg_input, corner_radius=THEME.radius_md,
        )
        self._files_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        self._files_placeholder = ctk.CTkLabel(
            self._files_frame,
            text="No data.",
            text_color=THEME.text_muted,
            font=(THEME.font_ui, THEME.font_size_sm),
        )
        self._files_placeholder.pack(pady=20)

        # Export button
        SuccessButton(right, "💾 Export Report",
                      command=self._export_report, width=140, height=34).pack(
            anchor="e", padx=16, pady=(0, 12))

    # ── Actions ──────────────────────────────────────────────────────────────

    def _browse(self) -> None:
        folder = filedialog.askdirectory(title="Select project folder")
        if folder:
            self._path_var.set(folder)

    def _scan(self) -> None:
        path = self._path_var.get()
        if not path or path == "No folder selected":
            messagebox.showwarning("No Folder", "Select a project folder first.")
            return

        self._progress.reset()
        self._progress.update("Initialising scanner…", 5)
        self._clear_results()

        def worker():
            from analyzers.project_scanner import project_scanner

            def update(msg, pct):
                self.after(0, lambda: self._progress.update(msg, pct))

            report = project_scanner.scan(path, progress_cb=update)
            self.after(0, lambda: self._display_report(report))

        threading.Thread(target=worker, daemon=True).start()

    def _display_report(self, report) -> None:
        self._report = report

        if report.error:
            messagebox.showerror("Scan Error", report.error)
            return

        # Stat cards
        self._c_files.update_value(str(report.total_files), THEME.accent_blue)
        self._c_loc.update_value(f"{report.total_code_lines:,}", THEME.accent_cyan)
        self._c_langs.update_value(str(len(report.language_breakdown)), THEME.accent_purple)
        self._c_dups.update_value(
            str(len(report.duplicate_files)),
            THEME.accent_red if report.duplicate_files else THEME.accent_green,
        )
        self._c_health.update_value(
            f"{report.health_score}/100",
            score_color(100 - report.health_score),
        )

        # Language breakdown bars
        self._render_languages(report)

        # Hotspots
        self._render_hotspots(report)

        # Largest files
        self._render_file_list(report)

        # Dashboard notify
        if hasattr(self._app, "dashboard"):
            self._app.dashboard.add_scan_result(report.total_files, report.health_score)

    def _render_languages(self, report) -> None:
        for widget in self._lang_frame.winfo_children():
            widget.destroy()

        if not report.language_breakdown:
            ctk.CTkLabel(self._lang_frame, text="No source files found.",
                         text_color=THEME.text_muted).pack(pady=20)
            return

        max_lines = max(report.language_breakdown.values(), default=1)
        colors = [
            THEME.accent_cyan, THEME.accent_blue, THEME.accent_purple,
            THEME.accent_green, THEME.accent_orange, THEME.accent_yellow,
        ]

        for i, (lang, count) in enumerate(list(report.language_breakdown.items())[:12]):
            row = ctk.CTkFrame(self._lang_frame, fg_color="transparent")
            row.pack(fill="x", pady=3, padx=4)

            color = colors[i % len(colors)]
            pct = count / max_lines

            # Language label
            ctk.CTkLabel(
                row, text=lang, width=90, anchor="w",
                text_color=THEME.text_primary,
                font=(THEME.font_ui, THEME.font_size_sm),
            ).pack(side="left")

            # Bar
            bar_bg = ctk.CTkFrame(row, fg_color=THEME.bg_hover, height=14,
                                  corner_radius=4)
            bar_bg.pack(side="left", fill="x", expand=True, padx=6)
            ctk.CTkFrame(
                bar_bg, fg_color=color, height=14,
                corner_radius=4,
                width=max(8, int(180 * pct)),
            ).place(x=0, y=0, relheight=1.0)

            # Count
            ctk.CTkLabel(
                row, text=f"{count:,}", width=60, anchor="e",
                text_color=color,
                font=(THEME.font_family, THEME.font_size_sm),
            ).pack(side="right")

    def _render_hotspots(self, report) -> None:
        for widget in self._hotspot_frame.winfo_children():
            widget.destroy()

        if not report.complexity_hotspots:
            ctk.CTkLabel(
                self._hotspot_frame,
                text="No high-complexity functions detected.",
                text_color=THEME.text_muted,
                font=(THEME.font_ui, THEME.font_size_sm),
            ).pack(pady=16)
            return

        # Header row
        hdr = ctk.CTkFrame(self._hotspot_frame, fg_color=THEME.bg_hover,
                           corner_radius=6)
        hdr.pack(fill="x", pady=(0, 2))
        for col, w in [("Function", 200), ("File", 180), ("Complexity", 90), ("Risk", 60)]:
            ctk.CTkLabel(hdr, text=col, width=w, anchor="w",
                         text_color=THEME.text_muted,
                         font=(THEME.font_ui, THEME.font_size_sm, "bold")).pack(
                side="left", padx=6, pady=4)

        for h in report.complexity_hotspots[:15]:
            risk_color = THEME.accent_red if h["risk"] == "HIGH" else THEME.accent_orange
            row = ctk.CTkFrame(self._hotspot_frame, fg_color="transparent",
                               corner_radius=4)
            row.pack(fill="x", pady=1)
            for text, w, color in [
                (h["function"], 200, THEME.text_primary),
                (h["file"][-30:], 180, THEME.text_secondary),
                (str(h["complexity"]), 90, THEME.accent_yellow),
                (h["risk"], 60, risk_color),
            ]:
                ctk.CTkLabel(row, text=text, width=w, anchor="w",
                             text_color=color,
                             font=(THEME.font_family, THEME.font_size_sm)).pack(
                    side="left", padx=6, pady=3)

    def _render_file_list(self, report) -> None:
        for widget in self._files_frame.winfo_children():
            widget.destroy()

        if not report.largest_files:
            ctk.CTkLabel(self._files_frame, text="No files.",
                         text_color=THEME.text_muted).pack(pady=16)
            return

        for fs in report.largest_files[:10]:
            row = ctk.CTkFrame(self._files_frame, fg_color="transparent")
            row.pack(fill="x", pady=2, padx=4)

            ctk.CTkLabel(
                row, text=fs.path[-45:], anchor="w",
                text_color=THEME.text_primary,
                font=(THEME.font_family, THEME.font_size_sm),
            ).pack(side="left", fill="x", expand=True)

            size_kb = fs.size_bytes / 1024
            ctk.CTkLabel(
                row, text=f"{fs.line_count:,} LOC  {size_kb:.1f}KB",
                text_color=THEME.text_muted,
                font=(THEME.font_family, THEME.font_size_sm),
            ).pack(side="right")

    def _clear_results(self) -> None:
        for widget in self._lang_frame.winfo_children():
            widget.destroy()
        for widget in self._hotspot_frame.winfo_children():
            widget.destroy()
        for widget in self._files_frame.winfo_children():
            widget.destroy()

    def _export_report(self) -> None:
        if not self._report:
            messagebox.showwarning("No Data", "Scan a project first.")
            return

        from datetime import datetime
        r = self._report
        lines = [
            f"# Project Analysis Report",
            f"**Path:** {r.project_path}",
            f"**Scan Time:** {r.scan_seconds}s",
            f"",
            f"## Summary",
            f"- Total Files: {r.total_files}",
            f"- Total Lines of Code: {r.total_code_lines:,}",
            f"- Total Size: {r.total_size_bytes / 1024:.1f} KB",
            f"- Health Score: {r.health_score}/100",
            f"- Duplicate Files: {len(r.duplicate_files)}",
            f"",
            f"## Language Breakdown",
        ]
        for lang, count in r.language_breakdown.items():
            lines.append(f"- {lang}: {count:,} lines")

        lines += ["", "## Complexity Hotspots"]
        for h in r.complexity_hotspots:
            lines.append(f"- `{h['function']}` in `{h['file']}` (line {h['line']}) — complexity: {h['complexity']} [{h['risk']}]")

        if r.duplicate_files:
            lines += ["", "## Duplicate Files"]
            for group in r.duplicate_files:
                lines.append(f"- {', '.join(group)}")

        text = "\n".join(lines)
        path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown", "*.md")],
            initialfile=f"project_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        )
        if path:
            Path(path).write_text(text, encoding="utf-8")
            messagebox.showinfo("Saved", f"Report saved to:\n{path}")
