"""
settings_page.py — Configuration and settings UI.
Allows editing API keys, model selection, and app preferences.
"""

from __future__ import annotations

import os
from pathlib import Path
from tkinter import messagebox
from typing import TYPE_CHECKING

import customtkinter as ctk
import tkinter as tk

from themes.themes import THEME
from ui.widgets import NeonButton, SectionHeader, SuccessButton

if TYPE_CHECKING:
    from ui.main_gui import App


class SettingsPage(ctk.CTkFrame):
    def __init__(self, master: "App", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._app = master
        self._build()

    def _build(self) -> None:
        from config.config import cfg

        ctk.CTkLabel(
            self, text="⚙️  Settings & Configuration",
            text_color=THEME.text_primary,
            font=(THEME.font_ui, THEME.font_size_title, "bold"),
        ).pack(anchor="w", padx=24, pady=(20, 4))

        ctk.CTkLabel(
            self,
            text="Configure API keys and application preferences",
            text_color=THEME.text_secondary,
            font=(THEME.font_ui, THEME.font_size_md),
        ).pack(anchor="w", padx=24, pady=(0, 12))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=4)

        # ── Groq API ───────────────────────────────────────────────────────
        groq_panel = self._make_panel(scroll, "🤖 Groq AI Configuration")

        self._groq_key_var = tk.StringVar(value=cfg.groq_api_key)
        self._add_field(
            groq_panel, "API Key",
            "Get your key at https://console.groq.com",
            self._groq_key_var, show="*",
        )

        ctk.CTkLabel(groq_panel, text="Model:",
                     text_color=THEME.text_secondary,
                     font=(THEME.font_ui, THEME.font_size_sm)).pack(
            anchor="w", padx=16, pady=(8, 2))

        self._model_var = tk.StringVar(value=cfg.groq_model)
        ctk.CTkComboBox(
            groq_panel, variable=self._model_var,
            values=list(cfg.available_models),
            width=300, height=36,
            fg_color=THEME.bg_input, border_color=THEME.border_card,
            button_color=THEME.accent_cyan, text_color=THEME.text_primary,
            font=(THEME.font_ui, THEME.font_size_sm),
        ).pack(anchor="w", padx=16, pady=(0, 12))

        # ── GitHub ─────────────────────────────────────────────────────────
        gh_panel = self._make_panel(scroll, "🐙 GitHub Configuration (Optional)")

        self._gh_token_var = tk.StringVar(value=cfg.github_token)
        self._add_field(
            gh_panel, "Personal Access Token",
            "For private repos — create at github.com/settings/tokens",
            self._gh_token_var, show="*",
        )

        # ── Paths ──────────────────────────────────────────────────────────
        paths_panel = self._make_panel(scroll, "📁 Storage Paths")

        self._projects_dir_var = tk.StringVar(value=str(cfg.projects_dir))
        self._add_field(paths_panel, "Projects Directory", "", self._projects_dir_var)

        self._exports_dir_var = tk.StringVar(value=str(cfg.exports_dir))
        self._add_field(paths_panel, "Exports Directory", "", self._exports_dir_var)

        # ── AI Parameters ──────────────────────────────────────────────────
        ai_panel = self._make_panel(scroll, "⚡ AI Parameters")

        ctk.CTkLabel(ai_panel, text="Max Tokens per Response:",
                     text_color=THEME.text_secondary,
                     font=(THEME.font_ui, THEME.font_size_sm)).pack(
            anchor="w", padx=16, pady=(8, 2))

        self._tokens_var = tk.IntVar(value=cfg.max_tokens)
        ctk.CTkSlider(
            ai_panel,
            from_=512, to=8192,
            variable=self._tokens_var,
            number_of_steps=15,
            fg_color=THEME.bg_hover,
            progress_color=THEME.accent_cyan,
            button_color=THEME.accent_cyan,
            width=300,
        ).pack(anchor="w", padx=16, pady=(0, 4))

        ctk.CTkLabel(ai_panel, textvariable=self._tokens_var,
                     text_color=THEME.accent_cyan,
                     font=(THEME.font_family, THEME.font_size_sm)).pack(
            anchor="w", padx=16, pady=(0, 12))

        # ── About ──────────────────────────────────────────────────────────
        about_panel = self._make_panel(scroll, "ℹ️  About")
        about_lines = [
            ("Application", "AI Desktop Engineer"),
            ("Version", cfg.app_version),
            ("Python", f"{__import__('sys').version.split()[0]}"),
            ("UI Framework", "CustomTkinter"),
            ("AI Provider", "Groq (Llama 3 / Mixtral)"),
        ]
        for label, value in about_lines:
            row = ctk.CTkFrame(about_panel, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=2)
            ctk.CTkLabel(row, text=f"{label}:", width=120, anchor="w",
                         text_color=THEME.text_secondary,
                         font=(THEME.font_ui, THEME.font_size_sm)).pack(side="left")
            ctk.CTkLabel(row, text=value,
                         text_color=THEME.text_primary,
                         font=(THEME.font_ui, THEME.font_size_sm)).pack(side="left")
        ctk.CTkFrame(about_panel, height=12, fg_color="transparent").pack()

        # ── Save button ────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", pady=12)

        SuccessButton(btn_row, "💾 Save Configuration",
                      command=self._save, width=200, height=42).pack(side="left")

        NeonButton(btn_row, "🔄 Test Connection",
                   command=self._test_connection, width=170, height=42,
                   accent=THEME.accent_blue).pack(side="left", padx=12)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _make_panel(self, parent, title: str) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(
            parent, fg_color=THEME.bg_card,
            corner_radius=THEME.radius_lg,
            border_color=THEME.border_card, border_width=1,
        )
        panel.pack(fill="x", pady=6)
        SectionHeader(panel, title).pack(fill="x", padx=16, pady=(14, 6))
        return panel

    def _add_field(
        self, parent, label: str, hint: str, variable: tk.StringVar,
        show: str = "",
    ) -> ctk.CTkEntry:
        ctk.CTkLabel(
            parent, text=f"{label}:",
            text_color=THEME.text_secondary,
            font=(THEME.font_ui, THEME.font_size_sm),
        ).pack(anchor="w", padx=16, pady=(8, 2))

        entry = ctk.CTkEntry(
            parent, textvariable=variable,
            show=show,
            width=420, height=36,
            fg_color=THEME.bg_input,
            border_color=THEME.border_card,
            text_color=THEME.text_primary,
            font=(THEME.font_family, THEME.font_size_sm),
        )
        entry.pack(anchor="w", padx=16, pady=(0, 2))

        if hint:
            ctk.CTkLabel(
                parent, text=hint,
                text_color=THEME.text_muted,
                font=(THEME.font_ui, 10),
            ).pack(anchor="w", padx=16, pady=(0, 8))

        return entry

    # ── Save ─────────────────────────────────────────────────────────────────

    def _save(self) -> None:
        env_path = Path(__file__).parent.parent / ".env"

        lines = [
            f"GROQ_API_KEY={self._groq_key_var.get().strip()}",
            f"GROQ_MODEL={self._model_var.get()}",
            f"GITHUB_TOKEN={self._gh_token_var.get().strip()}",
            f"PROJECTS_DIR={self._projects_dir_var.get().strip()}",
            f"EXPORTS_DIR={self._exports_dir_var.get().strip()}",
            f"MAX_TOKENS={self._tokens_var.get()}",
        ]
        env_path.write_text("\n".join(lines), encoding="utf-8")

        # Reload engine config
        try:
            from core.ai_engine import ai_engine
            ai_engine.reload_config()
        except Exception:
            pass

        from config.config import cfg
        configured = bool(self._groq_key_var.get().strip())
        if hasattr(self._app, "update_status"):
            self._app.update_status(configured, self._model_var.get())

        messagebox.showinfo("Saved", "Configuration saved.\nAPI key will take effect immediately.")

    def _test_connection(self) -> None:
        key = self._groq_key_var.get().strip()
        if not key:
            messagebox.showwarning("No Key", "Enter a Groq API key first.")
            return

        import threading

        def worker():
            try:
                from groq import Groq
                client = Groq(api_key=key)
                resp = client.chat.completions.create(
                    model=self._model_var.get(),
                    messages=[{"role": "user", "content": "Reply with: OK"}],
                    max_tokens=10,
                )
                reply = resp.choices[0].message.content
                self.after(0, lambda: messagebox.showinfo(
                    "Connection OK",
                    f"✅ Groq API connected successfully!\nModel response: {reply}"
                ))
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror(
                    "Connection Failed", f"❌ {exc}"
                ))

        threading.Thread(target=worker, daemon=True).start()
