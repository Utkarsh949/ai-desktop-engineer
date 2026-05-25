"""
ai_debugger_page.py — Dedicated AI debugging tab.
Paste broken code → AI explains + rewrites fixed version.
"""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING

import customtkinter as ctk

from themes.themes import THEME
from ui.widgets import (
    CodeEditor, LabeledProgress, NeonButton,
    ReportViewer, SectionHeader, SuccessButton, DangerButton,
)

if TYPE_CHECKING:
    from ui.main_gui import App


class AIDebuggerPage(ctk.CTkFrame):
    def __init__(self, master: "App", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._app = master
        self._fixed_code = ""
        self._build()

    def _build(self) -> None:
        # ── Header ─────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 8))

        ctk.CTkLabel(
            hdr, text="🐛  AI Debugger",
            text_color=THEME.accent_red,
            font=(THEME.font_ui, THEME.font_size_title, "bold"),
        ).pack(side="left")

        ctk.CTkLabel(
            hdr, text="Paste broken code → AI detects bugs and rewrites",
            text_color=THEME.text_secondary,
            font=(THEME.font_ui, THEME.font_size_md),
        ).pack(side="left", padx=20)

        # ── Body ────────────────────────────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=4)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # ── LEFT: Input ─────────────────────────────────────────────────────
        left = ctk.CTkFrame(body, fg_color=THEME.bg_card,
                            corner_radius=THEME.radius_lg,
                            border_color=THEME.border_card, border_width=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        SectionHeader(left, "Broken Code", "Paste the problematic code").pack(
            fill="x", padx=16, pady=(14, 6))

        ctrl = ctk.CTkFrame(left, fg_color="transparent")
        ctrl.pack(fill="x", padx=16, pady=6)

        ctk.CTkLabel(ctrl, text="Language:",
                     text_color=THEME.text_secondary,
                     font=(THEME.font_ui, THEME.font_size_sm)).pack(side="left")

        self._lang_var = tk.StringVar(value="Python")
        ctk.CTkComboBox(
            ctrl, variable=self._lang_var,
            values=["Python", "JavaScript", "TypeScript", "Java",
                    "C++", "Go", "Rust", "PHP", "C#"],
            width=140, height=32,
            fg_color=THEME.bg_input,
            border_color=THEME.border_card,
            button_color=THEME.accent_red,
            text_color=THEME.text_primary,
        ).pack(side="left", padx=(6, 0))

        NeonButton(ctrl, "📂 Upload", command=self._upload,
                   width=90, height=32, accent=THEME.accent_red).pack(side="left", padx=8)

        self._broken_editor = CodeEditor(left)
        self._broken_editor.pack(fill="both", expand=True, padx=16, pady=(4, 8))
        self._broken_editor.set_code("# Paste your broken code here…\n\ndef example():\n    x = [1,2,3\n    return x  # Missing closing bracket\n")

        self._progress = LabeledProgress(left)
        self._progress.pack(fill="x", padx=16, pady=(0, 6))

        btns = ctk.CTkFrame(left, fg_color="transparent")
        btns.pack(fill="x", padx=16, pady=(0, 14))

        DangerButton(
            btns, "🐛 Debug & Fix Code",
            command=self._debug, width=180, height=42,
        ).pack(side="left")

        NeonButton(
            btns, "🗑️ Clear", command=self._clear,
            width=80, height=42, accent=THEME.text_muted,
        ).pack(side="left", padx=8)

        # ── RIGHT: Output panels ────────────────────────────────────────────
        right = ctk.CTkFrame(body, fg_color=THEME.bg_card,
                             corner_radius=THEME.radius_lg,
                             border_color=THEME.border_card, border_width=1)
        right.grid(row=0, column=1, sticky="nsew")

        # Issues explanation
        SectionHeader(right, "Bug Report", "What the AI found").pack(
            fill="x", padx=16, pady=(14, 6))

        self._issues_frame = ctk.CTkScrollableFrame(
            right, fg_color=THEME.bg_input, corner_radius=THEME.radius_md,
            height=140,
        )
        self._issues_frame.pack(fill="x", padx=16, pady=(0, 8))

        self._explanation_lbl = ctk.CTkLabel(
            self._issues_frame,
            text="Run debug to see issue analysis…",
            text_color=THEME.text_muted,
            font=(THEME.font_ui, THEME.font_size_sm),
            wraplength=480, justify="left",
        )
        self._explanation_lbl.pack(anchor="w", padx=8, pady=8)

        # Fixed code
        SectionHeader(right, "Fixed Code", "AI-corrected version").pack(
            fill="x", padx=16, pady=(8, 6))

        self._fixed_editor = CodeEditor(right)
        self._fixed_editor.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        self._fixed_editor.set_code("# Fixed code will appear here…\n")

        # Action row
        action_row = ctk.CTkFrame(right, fg_color="transparent")
        action_row.pack(fill="x", padx=16, pady=(0, 14))

        SuccessButton(action_row, "📋 Copy Fixed Code",
                      command=self._copy_fixed, width=160, height=36).pack(side="left")
        SuccessButton(action_row, "💾 Save Fixed Code",
                      command=self._save_fixed, width=150, height=36).pack(side="left", padx=8)
        NeonButton(action_row, "🚀 Audit Fixed Code",
                   command=self._audit_fixed, width=160, height=36,
                   accent=THEME.accent_blue).pack(side="left")

    # ── Actions ──────────────────────────────────────────────────────────────

    def _upload(self) -> None:
        path = filedialog.askopenfilename(
            title="Select file to debug",
            filetypes=[("Source files", "*.py *.js *.ts *.java *.cpp *.go *.rs"),
                       ("All files", "*.*")]
        )
        if path:
            try:
                self._broken_editor.set_code(Path(path).read_text(encoding="utf-8", errors="replace"))
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _debug(self) -> None:
        code = self._broken_editor.get_code()
        if not code:
            messagebox.showwarning("Empty", "Paste some code first.")
            return

        lang = self._lang_var.get()
        self._progress.update("🔍 Detecting bugs…", 20)
        self._explanation_lbl.configure(text="Analysing…")
        self._fixed_editor.set_code("Working…\n")

        def worker():
            from core.ai_engine import ai_engine
            result = ai_engine.debug_code(code, language=lang)

            def display():
                self._progress.update("✅ Debug complete", 100)
                self._fixed_code = result.fixed_code or "# Could not generate fixed code"
                self._fixed_editor.set_code(self._fixed_code)

                # Build explanation text
                lines = []
                if result.explanation:
                    lines.append(f"📋 Explanation:\n{result.explanation}\n")
                if result.issues_detected:
                    lines.append("🐛 Issues Found:")
                    for i, issue in enumerate(result.issues_detected, 1):
                        lines.append(f"  {i}. {issue}")
                if result.optimizations:
                    lines.append("\n⚡ Optimizations Applied:")
                    for opt in result.optimizations:
                        lines.append(f"  • {opt}")

                self._explanation_lbl.configure(
                    text="\n".join(lines) or "No specific issues detected.",
                )

                if result.error:
                    messagebox.showerror("Debug Error", result.error)

            self.after(0, display)

        threading.Thread(target=worker, daemon=True).start()

    def _copy_fixed(self) -> None:
        if self._fixed_code:
            self.clipboard_clear()
            self.clipboard_append(self._fixed_code)
            messagebox.showinfo("Copied", "Fixed code copied to clipboard!")

    def _save_fixed(self) -> None:
        if not self._fixed_code:
            messagebox.showwarning("Nothing to save", "Debug code first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python", "*.py"), ("JavaScript", "*.js"),
                       ("All files", "*.*")],
        )
        if path:
            Path(path).write_text(self._fixed_code, encoding="utf-8")
            messagebox.showinfo("Saved", f"Fixed code saved to:\n{path}")

    def _audit_fixed(self) -> None:
        if not self._fixed_code:
            messagebox.showwarning("Nothing to audit", "Debug code first.")
            return
        # Switch to Code Review page and paste the fixed code
        review_page = getattr(self._app, "code_review", None)
        if review_page:
            review_page._editor.set_code(self._fixed_code)
            self._app._show_page("review")
            messagebox.showinfo("Transferred", "Fixed code sent to Code Review tab.")

    def _clear(self) -> None:
        self._broken_editor.clear()
        self._broken_editor.set_code("# Paste your broken code here…\n")
        self._fixed_editor.clear()
        self._fixed_editor.set_code("# Fixed code will appear here…\n")
        self._fixed_code = ""
        self._progress.reset()
        self._explanation_lbl.configure(text="Run debug to see issue analysis…")
