"""
ai_generator_page.py — AI Code Generator and AI Builder tabs.
Users type prompts → AI generates production-grade code.
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
    ReportViewer, SectionHeader, SuccessButton,
)

if TYPE_CHECKING:
    from ui.main_gui import App


_PROMPT_EXAMPLES = [
    "Create JWT authentication middleware with refresh tokens",
    "Generate FastAPI CRUD API with SQLAlchemy and Pydantic",
    "Build a React dashboard with charts and dark theme",
    "Write a Redis caching decorator for Python functions",
    "Create a rate limiter middleware for Express.js",
    "Generate a binary search tree with all traversal methods",
    "Build a Kafka producer/consumer in Python",
    "Write a Docker Compose file for a full-stack app",
    "Create a GitHub Actions CI/CD pipeline",
    "Generate a complete REST API with authentication",
]


class AIGeneratorPage(ctk.CTkFrame):
    def __init__(self, master: "App", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._app = master
        self._generated_code = ""
        self._build()

    def _build(self) -> None:
        # ── Header ─────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 8))

        ctk.CTkLabel(
            hdr, text="✨  AI Code Generator",
            text_color=THEME.accent_purple,
            font=(THEME.font_ui, THEME.font_size_title, "bold"),
        ).pack(side="left")

        # Mode tabs
        self._mode_var = tk.StringVar(value="generate")
        mode_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        mode_frame.pack(side="right")

        for label, val, color in [("Code Generator", "generate", THEME.accent_purple),
                                   ("AI Builder", "builder", THEME.accent_cyan)]:
            ctk.CTkRadioButton(
                mode_frame, text=label, variable=self._mode_var, value=val,
                command=self._switch_mode,
                text_color=THEME.text_secondary,
                fg_color=color,
                font=(THEME.font_ui, THEME.font_size_sm),
            ).pack(side="left", padx=10)

        # ── Body ────────────────────────────────────────────────────────────
        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True, padx=24, pady=4)
        self._body.columnconfigure(0, weight=1)
        self._body.columnconfigure(1, weight=1)
        self._body.rowconfigure(0, weight=1)

        # ── LEFT: Prompt panel ──────────────────────────────────────────────
        left = ctk.CTkFrame(self._body, fg_color=THEME.bg_card,
                            corner_radius=THEME.radius_lg,
                            border_color=THEME.border_card, border_width=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self._prompt_header = SectionHeader(
            left, "Code Request", "Describe what you want to build"
        )
        self._prompt_header.pack(fill="x", padx=16, pady=(14, 6))

        # Language selector
        ctrl = ctk.CTkFrame(left, fg_color="transparent")
        ctrl.pack(fill="x", padx=16, pady=6)

        ctk.CTkLabel(ctrl, text="Language:",
                     text_color=THEME.text_secondary,
                     font=(THEME.font_ui, THEME.font_size_sm)).pack(side="left")

        self._lang_var = tk.StringVar(value="Python")
        ctk.CTkComboBox(
            ctrl, variable=self._lang_var,
            values=["Python", "JavaScript", "TypeScript", "Java",
                    "C++", "Go", "Rust", "React", "FastAPI", "Django",
                    "Express.js", "Spring Boot", "Flutter", "SQL"],
            width=160, height=32,
            fg_color=THEME.bg_input,
            border_color=THEME.border_card,
            button_color=THEME.accent_purple,
            text_color=THEME.text_primary,
        ).pack(side="left", padx=(6, 0))

        # Prompt examples
        ctk.CTkLabel(
            left, text="💡 Example prompts:",
            text_color=THEME.text_secondary,
            font=(THEME.font_ui, THEME.font_size_sm),
        ).pack(anchor="w", padx=16, pady=(8, 2))

        ex_frame = ctk.CTkScrollableFrame(left, fg_color="transparent", height=80)
        ex_frame.pack(fill="x", padx=16, pady=(0, 4))

        for ex in _PROMPT_EXAMPLES[:5]:
            btn = ctk.CTkButton(
                ex_frame, text=ex,
                fg_color=THEME.bg_hover, hover_color=THEME.bg_active,
                text_color=THEME.text_secondary,
                font=(THEME.font_ui, THEME.font_size_sm),
                height=26, anchor="w", corner_radius=6,
                command=lambda t=ex: self._set_prompt(t),
            )
            btn.pack(fill="x", pady=1)

        # Prompt box
        ctk.CTkLabel(
            left, text="Your Request:",
            text_color=THEME.text_secondary,
            font=(THEME.font_ui, THEME.font_size_sm),
        ).pack(anchor="w", padx=16, pady=(8, 2))

        self._prompt_box = ctk.CTkTextbox(
            left, height=140,
            fg_color=THEME.bg_input,
            text_color=THEME.text_primary,
            font=(THEME.font_ui, THEME.font_size_md),
            corner_radius=THEME.radius_md,
            border_color=THEME.border_card, border_width=1,
            wrap="word",
        )
        self._prompt_box.pack(fill="x", padx=16, pady=(0, 8))
        self._prompt_box.insert("1.0", "Describe what you want to build…")

        self._progress = LabeledProgress(left)
        self._progress.pack(fill="x", padx=16, pady=(0, 6))

        btns = ctk.CTkFrame(left, fg_color="transparent")
        btns.pack(fill="x", padx=16, pady=(0, 14))

        self._gen_btn = NeonButton(
            btns, "✨ Generate Code",
            command=self._generate,
            width=180, height=42,
            accent=THEME.accent_purple,
        )
        self._gen_btn.pack(side="left")

        NeonButton(
            btns, "🗑️ Clear", command=self._clear,
            width=80, height=42, accent=THEME.text_muted,
        ).pack(side="left", padx=8)

        # ── RIGHT: Output panel ─────────────────────────────────────────────
        right = ctk.CTkFrame(self._body, fg_color=THEME.bg_card,
                             corner_radius=THEME.radius_lg,
                             border_color=THEME.border_card, border_width=1)
        right.grid(row=0, column=1, sticky="nsew")

        SectionHeader(right, "Generated Code", "Production-ready output").pack(
            fill="x", padx=16, pady=(14, 6))

        # Output tabs
        self._out_tab_var = tk.StringVar(value="code")
        out_tab_row = ctk.CTkFrame(right, fg_color="transparent")
        out_tab_row.pack(fill="x", padx=16, pady=(0, 6))

        for label, val in [("Code", "code"), ("Explanation", "explain"),
                            ("Structure", "structure"), ("Best Practices", "practices")]:
            ctk.CTkRadioButton(
                out_tab_row, text=label, variable=self._out_tab_var, value=val,
                command=self._switch_output_tab,
                text_color=THEME.text_secondary,
                fg_color=THEME.accent_purple,
                font=(THEME.font_ui, THEME.font_size_sm),
            ).pack(side="left", padx=4)

        self._output_editor = CodeEditor(right)
        self._output_editor.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        self._output_editor.set_code("# Generated code will appear here…\n")

        # Export row
        export_row = ctk.CTkFrame(right, fg_color="transparent")
        export_row.pack(fill="x", padx=16, pady=(0, 14))

        SuccessButton(export_row, "📋 Copy Code",
                      command=self._copy_code, width=130, height=36).pack(side="left")
        SuccessButton(export_row, "💾 Save File",
                      command=self._save_file, width=120, height=36).pack(side="left", padx=6)
        SuccessButton(export_row, "📁 Save Project",
                      command=self._save_project, width=130, height=36).pack(side="left", padx=6)
        NeonButton(export_row, "🔬 Audit This Code",
                   command=self._audit_code, width=140, height=36,
                   accent=THEME.accent_blue).pack(side="left", padx=6)

        # Store output parts
        self._outputs: dict[str, str] = {
            "code": "", "explain": "", "structure": "", "practices": ""
        }

    # ── Mode switch ──────────────────────────────────────────────────────────

    def _switch_mode(self) -> None:
        mode = self._mode_var.get()
        if mode == "builder":
            self._prompt_header._lbl_text = "Project Builder"
            self._gen_btn.configure(text="🏗️ Build Full Project")
        else:
            self._gen_btn.configure(text="✨ Generate Code")

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _set_prompt(self, text: str) -> None:
        self._prompt_box.delete("1.0", "end")
        self._prompt_box.insert("1.0", text)

    def _get_prompt(self) -> str:
        return self._prompt_box.get("1.0", "end-1c").strip()

    # ── Generation ───────────────────────────────────────────────────────────

    def _generate(self) -> None:
        prompt = self._get_prompt()
        if not prompt or prompt.startswith("Describe"):
            messagebox.showwarning("No Prompt", "Please enter a code request.")
            return

        mode = self._mode_var.get()
        lang = self._lang_var.get()
        self._progress.update("✨ Generating…", 20)
        self._output_editor.set_code("# Generating…\n")

        def worker():
            from core.ai_engine import ai_engine

            if mode == "builder":
                def update(msg, pct):
                    self.after(0, lambda: self._progress.update(msg, pct))
                result_text = ai_engine.build_project(prompt, language=lang, progress_cb=update)
                self.after(0, lambda: self._display_project(result_text))
            else:
                result = ai_engine.generate_code(prompt, language=lang)
                self.after(0, lambda: self._display_generation(result))

        threading.Thread(target=worker, daemon=True).start()

    def _display_generation(self, result) -> None:
        self._outputs["code"] = result.code or "# No code generated"
        self._outputs["explain"] = result.explanation or "No explanation"
        self._outputs["structure"] = result.folder_structure or "No structure provided"
        self._outputs["practices"] = "\n".join(
            f"• {p}" for p in result.best_practices
        ) if result.best_practices else "No practices listed"

        self._generated_code = result.code
        self._out_tab_var.set("code")
        self._output_editor.set_code(result.code or "# No code generated")
        self._progress.update("✅ Code generated", 100)

    def _display_project(self, text: str) -> None:
        self._outputs["code"] = text
        self._generated_code = text
        self._output_editor.set_code(text)
        self._progress.update("✅ Project generated", 100)

    def _switch_output_tab(self) -> None:
        tab = self._out_tab_var.get()
        content = self._outputs.get(tab, "")
        self._output_editor.set_code(content or "# No data. Generate first.")

    # ── Export ───────────────────────────────────────────────────────────────

    def _copy_code(self) -> None:
        code = self._outputs.get(self._out_tab_var.get(), "")
        if code:
            self.clipboard_clear()
            self.clipboard_append(code)
            messagebox.showinfo("Copied", "Code copied to clipboard!")

    def _save_file(self) -> None:
        code = self._generated_code
        if not code:
            messagebox.showwarning("Nothing", "Generate code first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python", "*.py"), ("JavaScript", "*.js"),
                       ("TypeScript", "*.ts"), ("All files", "*.*")],
        )
        if path:
            Path(path).write_text(code, encoding="utf-8")
            messagebox.showinfo("Saved", f"Saved to:\n{path}")

    def _save_project(self) -> None:
        """Save entire generated project (markdown) to an exports file."""
        from config.config import cfg
        from datetime import datetime
        code = self._generated_code
        if not code:
            messagebox.showwarning("Nothing", "Generate a project first.")
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fpath = cfg.exports_dir / f"project_{ts}.md"
        fpath.write_text(code, encoding="utf-8")
        messagebox.showinfo("Project Saved", f"Project saved to:\n{fpath}")

    def _audit_code(self) -> None:
        code = self._generated_code
        if not code:
            messagebox.showwarning("Nothing", "Generate code first.")
            return
        review_page = getattr(self._app, "code_review", None)
        if review_page:
            review_page._editor.set_code(code)
            self._app._show_page("review")

    def _clear(self) -> None:
        self._prompt_box.delete("1.0", "end")
        self._prompt_box.insert("1.0", "Describe what you want to build…")
        self._output_editor.clear()
        self._output_editor.set_code("# Generated code will appear here…\n")
        self._generated_code = ""
        self._progress.reset()
        for k in self._outputs:
            self._outputs[k] = ""
