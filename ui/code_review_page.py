"""
code_review_page.py — Triple-Pass AI code review tab.
Supports paste, file upload, folder upload, and manual GitHub repo URL.
"""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING

import customtkinter as ctk

from themes.themes import THEME, score_color, severity_color
from ui.widgets import (
    CodeEditor, LabeledProgress, NeonButton, ReportViewer,
    RiskBadge, SectionHeader, SuccessButton,
)

if TYPE_CHECKING:
    from ui.main_gui import App


class CodeReviewPage(ctk.CTkFrame):
    def __init__(self, master: "App", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._app = master
        self._current_code = ""
        self._build()

    def _build(self) -> None:
        # ── Page header ────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 8))

        ctk.CTkLabel(
            hdr, text="🔬  Triple-Pass AI Code Review",
            text_color=THEME.accent_cyan,
            font=(THEME.font_ui, THEME.font_size_title, "bold"),
        ).pack(side="left")

        self._risk_badge = RiskBadge(hdr, score=0, severity="NONE")
        self._risk_badge.pack(side="right", padx=4)

        # ── Main 2-column layout ────────────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=4)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # ── LEFT: Input panel ───────────────────────────────────────────────
        left = ctk.CTkFrame(body, fg_color=THEME.bg_card,
                            corner_radius=THEME.radius_lg,
                            border_color=THEME.border_card, border_width=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        SectionHeader(left, "Source Code Input", "Paste, upload file, or import from GitHub").pack(
            fill="x", padx=16, pady=(14, 6))

        # Controls row
        ctrl = ctk.CTkFrame(left, fg_color="transparent")
        ctrl.pack(fill="x", padx=16, pady=6)

        ctk.CTkLabel(ctrl, text="Language:",
                     text_color=THEME.text_secondary,
                     font=(THEME.font_ui, THEME.font_size_sm)).pack(side="left")

        from config.config import cfg
        self._lang_var = tk.StringVar(value="Auto-Detect")
        ctk.CTkComboBox(
            ctrl, variable=self._lang_var,
            values=list(cfg.languages),
            width=140, height=32,
            fg_color=THEME.bg_input,
            border_color=THEME.border_card,
            button_color=THEME.accent_cyan,
            text_color=THEME.text_primary,
        ).pack(side="left", padx=(6, 0))

        NeonButton(ctrl, "📂 File", command=self._upload_file,
                   width=80, height=32).pack(side="left", padx=(10, 2))
        NeonButton(ctrl, "📁 Folder", command=self._upload_folder,
                   width=90, height=32).pack(side="left", padx=2)

        # Code editor
        self._editor = CodeEditor(left)
        self._editor.pack(fill="both", expand=True, padx=16, pady=(4, 8))

        self._editor.set_code("# Paste your code here or upload a file above…\n\n")

        # Source label
        self._source_lbl = ctk.CTkLabel(
            left, text="",
            text_color=THEME.text_muted,
            font=(THEME.font_family, THEME.font_size_sm),
        )
        self._source_lbl.pack(padx=16, pady=(0, 2), anchor="w")

        # Progress bar
        self._progress = LabeledProgress(left)
        self._progress.pack(fill="x", padx=16, pady=(4, 8))

        # Action buttons
        btns = ctk.CTkFrame(left, fg_color="transparent")
        btns.pack(fill="x", padx=16, pady=(0, 14))

        NeonButton(
            btns, "🚀 Run Triple-Pass Audit",
            command=self._run_audit,
            width=200, height=40,
            accent=THEME.accent_cyan,
        ).pack(side="left")

        NeonButton(
            btns, "🔍 Quick Analyze",
            command=self._run_quick,
            width=150, height=40,
            accent=THEME.accent_blue,
        ).pack(side="left", padx=8)

        NeonButton(
            btns, "🗑️ Clear",
            command=self._clear,
            width=80, height=40,
            accent=THEME.text_muted,
        ).pack(side="left")

        # ── RIGHT: Report panel ─────────────────────────────────────────────
        right = ctk.CTkFrame(body, fg_color=THEME.bg_card,
                             corner_radius=THEME.radius_lg,
                             border_color=THEME.border_card, border_width=1)
        right.grid(row=0, column=1, sticky="nsew")

        SectionHeader(right, "AI Analysis Report", "Results from the three audit passes").pack(
            fill="x", padx=16, pady=(14, 6))

        # Tab switcher
        self._tab_var = tk.StringVar(value="combined")
        tab_row = ctk.CTkFrame(right, fg_color="transparent")
        tab_row.pack(fill="x", padx=16, pady=(0, 6))
        for label, val in [("Combined", "combined"), ("Security", "security"),
                            ("Performance", "perf"), ("Architecture", "arch")]:
            ctk.CTkRadioButton(
                tab_row, text=label, variable=self._tab_var, value=val,
                command=self._switch_tab,
                text_color=THEME.text_secondary,
                fg_color=THEME.accent_cyan,
                border_color=THEME.border_card,
                font=(THEME.font_ui, THEME.font_size_sm),
            ).pack(side="left", padx=6)

        self._report_viewer = ReportViewer(right)
        self._report_viewer.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        # Export row
        export_row = ctk.CTkFrame(right, fg_color="transparent")
        export_row.pack(fill="x", padx=16, pady=(0, 14))

        SuccessButton(export_row, "📋 Copy Report",
                      command=self._copy_report, width=140, height=36).pack(side="left")
        SuccessButton(export_row, "💾 Export .md",
                      command=self._export_md, width=140, height=36).pack(side="left", padx=8)

        # Store reports
        self._reports: dict[str, str] = {
            "combined": "", "security": "", "perf": "", "arch": ""
        }

    # ── File / folder upload ─────────────────────────────────────────────────

    def _upload_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Select source file",
            filetypes=[
                ("All source", "*.py *.js *.ts *.jsx *.tsx *.java *.cpp *.go *.rs *.rb *.php *.cs *.swift *.kt"),
                ("All files", "*.*"),
            ]
        )
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="utf-8", errors="replace")
            self._editor.set_code(text)
            self._source_lbl.configure(text=f"📄 {Path(path).name}")
            # Auto-detect language from extension
            ext_map = {
                ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
                ".java": "Java", ".cpp": "C++", ".go": "Go", ".rs": "Rust",
                ".rb": "Ruby", ".php": "PHP", ".cs": "C#",
            }
            ext = Path(path).suffix.lower()
            if ext in ext_map:
                self._lang_var.set(ext_map[ext])
        except Exception as e:
            messagebox.showerror("Error", f"Could not read file:\n{e}")

    def _upload_folder(self) -> None:
        folder = filedialog.askdirectory(title="Select project folder")
        if not folder:
            return
        # Collect all source files and concatenate (capped at 300KB)
        from config.config import cfg
        parts = []
        total = 0
        for ext in cfg.supported_extensions:
            for fpath in Path(folder).rglob(f"*{ext}"):
                if fpath.stat().st_size > cfg.max_file_size:
                    continue
                try:
                    content = fpath.read_text(encoding="utf-8", errors="replace")
                    header = f"\n\n{'='*60}\n# FILE: {fpath.relative_to(folder)}\n{'='*60}\n"
                    parts.append(header + content)
                    total += len(content)
                    if total > 300_000:
                        parts.append("\n\n[...truncated: project too large for single review...]")
                        break
                except Exception:
                    pass
            if total > 300_000:
                break

        combined = "".join(parts) or "# No source files found"
        self._editor.set_code(combined)
        self._source_lbl.configure(text=f"📁 {Path(folder).name} ({len(parts)} files)")

    # ── Analysis ─────────────────────────────────────────────────────────────

    def _run_audit(self) -> None:
        code = self._editor.get_code()
        if not code or code.startswith("# Paste"):
            messagebox.showwarning("No Code", "Please paste or upload code first.")
            return

        self._progress.reset()
        self._report_viewer.set_text("⏳ Running Triple-Pass Audit…\n\nThis may take 20-60 seconds.")

        lang = self._lang_var.get()

        def worker():
            from core.ai_engine import ai_engine

            def update(msg: str, pct: int):
                self.after(0, lambda: self._progress.update(msg, pct))

            result = ai_engine.triple_pass_audit(code, language=lang, progress_cb=update)

            self.after(0, lambda: self._display_result(result))

        threading.Thread(target=worker, daemon=True).start()

    def _run_quick(self) -> None:
        code = self._editor.get_code()
        if not code or code.startswith("# Paste"):
            messagebox.showwarning("No Code", "Please paste or upload code first.")
            return

        self._progress.update("🔍 Analyzing…", 10)
        lang = self._lang_var.get()

        def worker():
            from core.ai_engine import ai_engine
            collected = []

            def stream_cb(chunk: str):
                collected.append(chunk)
                text = "".join(collected)
                self.after(0, lambda: self._report_viewer.set_text(text))

            ai_engine.analyze_paste(code, language=lang, stream_cb=stream_cb)
            self.after(0, lambda: self._progress.update("✅ Done", 100))

        threading.Thread(target=worker, daemon=True).start()

    def _display_result(self, result) -> None:
        self._reports["combined"] = result.combined_report
        self._reports["security"] = result.security_report
        self._reports["perf"] = result.performance_report
        self._reports["arch"] = result.architecture_report

        self._tab_var.set("combined")
        self._report_viewer.set_text(result.combined_report or "No report generated.")
        self._risk_badge.update_risk(result.risk_score, result.severity)
        self._progress.update("✅ Audit complete", 100)

        # Notify dashboard
        if hasattr(self._app, "dashboard"):
            name = self._source_lbl.cget("text") or "Pasted Code"
            self._app.dashboard.add_audit_row(
                name, result.language, result.risk_score,
                result.severity, result.issues_found, result.elapsed_seconds,
            )

    def _switch_tab(self) -> None:
        tab = self._tab_var.get()
        self._report_viewer.set_text(self._reports.get(tab, "No data. Run an audit first."))

    def _clear(self) -> None:
        self._editor.clear()
        self._editor.set_code("# Paste your code here…\n")
        self._report_viewer.clear()
        self._progress.reset()
        self._risk_badge.update_risk(0, "NONE")
        self._source_lbl.configure(text="")
        for k in self._reports:
            self._reports[k] = ""

    def _copy_report(self) -> None:
        tab = self._tab_var.get()
        text = self._reports.get(tab, "")
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("Copied", "Report copied to clipboard!")

    def _export_md(self) -> None:
        tab = self._tab_var.get()
        text = self._reports.get(tab, "")
        if not text:
            messagebox.showwarning("Nothing to export", "Run an audit first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown", "*.md")],
            initialfile=f"audit_report_{tab}.md",
        )
        if path:
            Path(path).write_text(text, encoding="utf-8")
            messagebox.showinfo("Saved", f"Report saved to:\n{path}")
