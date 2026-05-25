"""
main_gui.py — Main CustomTkinter application window.
Sidebar navigation, page routing, and application bootstrap.
"""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from themes.themes import THEME
from ui.widgets import NavButton

# ── Configure CustomTkinter appearance ────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        from config.config import cfg

        self._cfg = cfg
        self.title(f"  {cfg.app_title}  v{cfg.app_version}")
        self.geometry(cfg.window_size)
        self.minsize(1100, 700)
        self.configure(fg_color=THEME.bg_deep)

        # Set window icon if available
        icon_path = Path(__file__).parent.parent / "assets" / "icon.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

        self._pages: dict[str, ctk.CTkFrame] = {}
        self._nav_buttons: dict[str, NavButton] = {}
        self._active_page = ""

        self._build_layout()
        self._show_page("dashboard")

        # Check config
        self.after(500, self._check_config)

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        # Root grid: sidebar | content
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar ───────────────────────────────────────────────────────
        self._sidebar = ctk.CTkFrame(
            self,
            width=230,
            fg_color=THEME.bg_dark,
            corner_radius=0,
            border_color=THEME.border_dim,
            border_width=1,
        )
        self._sidebar.grid(row=0, column=0, sticky="nsew")
        self._sidebar.grid_propagate(False)

        # Logo
        logo_frame = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=(20, 8))

        ctk.CTkLabel(
            logo_frame,
            text="⬡",
            text_color=THEME.accent_cyan,
            font=(THEME.font_ui, 32, "bold"),
        ).pack(side="left")

        title_frame = ctk.CTkFrame(logo_frame, fg_color="transparent")
        title_frame.pack(side="left", padx=8)

        ctk.CTkLabel(
            title_frame,
            text="AI Engineer",
            text_color=THEME.text_primary,
            font=(THEME.font_ui, 15, "bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame,
            text="Desktop Suite",
            text_color=THEME.text_muted,
            font=(THEME.font_ui, 10),
        ).pack(anchor="w")

        # Divider
        ctk.CTkFrame(
            self._sidebar, height=1,
            fg_color=THEME.border_dim,
        ).pack(fill="x", padx=16, pady=10)

        # ── Navigation items ──────────────────────────────────────────────
        nav_items = [
            ("dashboard",   "dashboard",  "⬡",  "Dashboard"),
            ("review",      "review",     "🔬", "Code Review"),
            ("debugger",    "debugger",   "🐛", "AI Debugger"),
            ("generator",   "generator",  "✨", "Code Generator"),
            ("analyzer",    "analyzer",   "📊", "Project Analyzer"),
            ("github",      "github",     "🐙", "GitHub Import"),
            ("settings",    "settings",   "⚙️",  "Settings"),
        ]

        nav_scroll = ctk.CTkScrollableFrame(
            self._sidebar, fg_color="transparent",
            scrollbar_button_color=THEME.border_dim,
        )
        nav_scroll.pack(fill="both", expand=True, padx=8)

        for page_id, _, icon, label in nav_items:
            btn = NavButton(
                nav_scroll,
                text=label,
                icon=icon,
                command=lambda pid=page_id: self._show_page(pid),
            )
            btn.pack(fill="x", pady=2)
            self._nav_buttons[page_id] = btn

        # ── Sidebar footer ─────────────────────────────────────────────────
        footer = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=14)

        from config.config import cfg
        status_text = (
            f"✓ Groq ready" if cfg.groq_configured
            else "⚠ API key missing"
        )
        status_color = THEME.accent_green if cfg.groq_configured else THEME.accent_orange

        self._status_lbl = ctk.CTkLabel(
            footer,
            text=status_text,
            text_color=status_color,
            font=(THEME.font_ui, THEME.font_size_sm),
        )
        self._status_lbl.pack(anchor="w")

        ctk.CTkLabel(
            footer,
            text=f"v{cfg.app_version}",
            text_color=THEME.text_muted,
            font=(THEME.font_ui, 10),
        ).pack(anchor="w")

        # ── Content area ───────────────────────────────────────────────────
        self._content = ctk.CTkFrame(
            self,
            fg_color=THEME.bg_deep,
            corner_radius=0,
        )
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(0, weight=1)

        # ── Page title bar ─────────────────────────────────────────────────
        self._title_bar = ctk.CTkFrame(
            self._content,
            height=48,
            fg_color=THEME.bg_dark,
            corner_radius=0,
            border_color=THEME.border_dim,
            border_width=1,
        )
        self._title_bar.pack(fill="x")
        self._title_bar.pack_propagate(False)

        self._page_title_lbl = ctk.CTkLabel(
            self._title_bar,
            text="Dashboard",
            text_color=THEME.text_primary,
            font=(THEME.font_ui, THEME.font_size_md, "bold"),
        )
        self._page_title_lbl.pack(side="left", padx=20, pady=12)

        # Model indicator
        self._model_lbl = ctk.CTkLabel(
            self._title_bar,
            text=f"Model: {self._cfg.groq_model}",
            text_color=THEME.text_muted,
            font=(THEME.font_family, THEME.font_size_sm),
        )
        self._model_lbl.pack(side="right", padx=16)

        # ── Page container ─────────────────────────────────────────────────
        self._page_container = ctk.CTkFrame(
            self._content,
            fg_color=THEME.bg_deep,
            corner_radius=0,
        )
        self._page_container.pack(fill="both", expand=True)
        self._page_container.grid_columnconfigure(0, weight=1)
        self._page_container.grid_rowconfigure(0, weight=1)

        # ── Instantiate all pages ──────────────────────────────────────────
        self._build_pages()

    def _build_pages(self) -> None:
        from ui.dashboard_page import DashboardPage
        from ui.code_review_page import CodeReviewPage
        from ui.ai_debugger_page import AIDebuggerPage
        from ui.ai_generator_page import AIGeneratorPage
        from ui.project_analyzer_page import ProjectAnalyzerPage
        from ui.github_import_page import GitHubImportPage
        from ui.settings_page import SettingsPage

        page_map = {
            "dashboard": DashboardPage,
            "review":    CodeReviewPage,
            "debugger":  AIDebuggerPage,
            "generator": AIGeneratorPage,
            "analyzer":  ProjectAnalyzerPage,
            "github":    GitHubImportPage,
            "settings":  SettingsPage,
        }

        for page_id, PageClass in page_map.items():
            page = PageClass(self._page_container)
            page.grid(row=0, column=0, sticky="nsew")
            self._pages[page_id] = page

        # Expose convenience references for cross-page navigation
        self.dashboard       = self._pages["dashboard"]
        self.code_review     = self._pages["review"]
        self.ai_debugger     = self._pages["debugger"]
        self.ai_generator    = self._pages["generator"]
        self.project_analyzer = self._pages["analyzer"]
        self.github_import   = self._pages["github"]
        self.settings_page   = self._pages["settings"]

    # ── Navigation ─────────────────────────────────────────────────────────

    def _show_page(self, page_id: str) -> None:
        if page_id not in self._pages:
            return

        # Raise the requested page
        self._pages[page_id].tkraise()
        self._active_page = page_id

        # Update nav button states
        for pid, btn in self._nav_buttons.items():
            btn.set_active(pid == page_id)

        # Update title bar
        titles = {
            "dashboard":  "⬡  Dashboard",
            "review":     "🔬  Triple-Pass Code Review",
            "debugger":   "🐛  AI Debugger",
            "generator":  "✨  AI Code Generator",
            "analyzer":   "📊  Project Analyzer",
            "github":     "🐙  GitHub Import",
            "settings":   "⚙️   Settings",
        }
        self._page_title_lbl.configure(text=titles.get(page_id, page_id))

    # ── Config check ────────────────────────────────────────────────────────

    def _check_config(self) -> None:
        from config.config import cfg
        if not cfg.groq_configured:
            self._status_lbl.configure(
                text="⚠ API key missing",
                text_color=THEME.accent_orange,
            )
            # Show a gentle reminder
            if messagebox.askyesno(
                "Setup Required",
                "No Groq API key detected.\n\n"
                "AI features require a Groq API key.\n\n"
                "Go to Settings to configure it?",
            ):
                self._show_page("settings")

    def update_status(self, configured: bool, model: str) -> None:
        """Called from settings page after saving config."""
        if configured:
            self._status_lbl.configure(
                text="✓ Groq ready",
                text_color=THEME.accent_green,
            )
        else:
            self._status_lbl.configure(
                text="⚠ API key missing",
                text_color=THEME.accent_orange,
            )
        self._model_lbl.configure(text=f"Model: {model}")


def launch() -> None:
    """Entry point — create and run the application."""
    from core.logger import get_logger
    log = get_logger("main")
    log.info("Launching AI Desktop Engineer")

    try:
        app = App()
        app.mainloop()
    except KeyboardInterrupt:
        log.info("Application terminated by user")
    except Exception as exc:
        log.exception("Fatal error: %s", exc)
        raise
