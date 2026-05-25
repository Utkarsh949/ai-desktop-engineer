"""
github_import_page.py — GitHub repository import via API (no webhooks).
Allows cloning repos, browsing branches, and sending to analyzer.
"""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import TYPE_CHECKING

import customtkinter as ctk

from themes.themes import THEME
from ui.widgets import LabeledProgress, NeonButton, SectionHeader, SuccessButton

if TYPE_CHECKING:
    from ui.main_gui import App


class GitHubImportPage(ctk.CTkFrame):
    def __init__(self, master: "App", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._app = master
        self._cloned_path: Path | None = None
        self._build()

    def _build(self) -> None:
        # ── Header ─────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="🐙  GitHub Repository Import",
            text_color=THEME.accent_green,
            font=(THEME.font_ui, THEME.font_size_title, "bold"),
        ).pack(anchor="w", padx=24, pady=(20, 4))

        ctk.CTkLabel(
            self,
            text="Import GitHub repositories via API — no webhooks required",
            text_color=THEME.text_secondary,
            font=(THEME.font_ui, THEME.font_size_md),
        ).pack(anchor="w", padx=24, pady=(0, 12))

        # ── URL input panel ─────────────────────────────────────────────────
        url_panel = ctk.CTkFrame(self, fg_color=THEME.bg_card,
                                 corner_radius=THEME.radius_lg,
                                 border_color=THEME.border_card, border_width=1)
        url_panel.pack(fill="x", padx=24, pady=4)

        SectionHeader(url_panel, "Repository URL", "Paste any public GitHub repo URL").pack(
            fill="x", padx=16, pady=(14, 6))

        row = ctk.CTkFrame(url_panel, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=6)

        self._url_var = tk.StringVar()
        ctk.CTkEntry(
            row, textvariable=self._url_var,
            placeholder_text="https://github.com/owner/repository",
            fg_color=THEME.bg_input,
            border_color=THEME.border_card,
            text_color=THEME.text_primary,
            font=(THEME.font_ui, THEME.font_size_md),
            height=38,
        ).pack(side="left", fill="x", expand=True)

        NeonButton(row, "🔍 Fetch Info",
                   command=self._fetch_info, width=130, height=38,
                   accent=THEME.accent_green).pack(side="left", padx=8)

        # Branch selector
        branch_row = ctk.CTkFrame(url_panel, fg_color="transparent")
        branch_row.pack(fill="x", padx=16, pady=6)

        ctk.CTkLabel(branch_row, text="Branch:",
                     text_color=THEME.text_secondary,
                     font=(THEME.font_ui, THEME.font_size_sm)).pack(side="left")

        self._branch_var = tk.StringVar(value="main")
        self._branch_combo = ctk.CTkComboBox(
            branch_row, variable=self._branch_var,
            values=["main", "master", "develop"],
            width=180, height=32,
            fg_color=THEME.bg_input,
            border_color=THEME.border_card,
            button_color=THEME.accent_green,
            text_color=THEME.text_primary,
        )
        self._branch_combo.pack(side="left", padx=8)

        NeonButton(branch_row, "📥 Clone & Analyze",
                   command=self._clone_repo, width=160, height=32,
                   accent=THEME.accent_cyan).pack(side="left", padx=8)

        url_panel.pack(fill="x", padx=24, pady=4)

        # ── Progress ────────────────────────────────────────────────────────
        self._progress = LabeledProgress(self)
        self._progress.pack(fill="x", padx=24, pady=8)

        # ── Repo info panel ─────────────────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=4)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # Left: repo metadata
        left = ctk.CTkFrame(body, fg_color=THEME.bg_card,
                            corner_radius=THEME.radius_lg,
                            border_color=THEME.border_card, border_width=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        SectionHeader(left, "Repository Info", "Metadata from GitHub API").pack(
            fill="x", padx=16, pady=(14, 6))

        self._info_box = ctk.CTkTextbox(
            left,
            fg_color=THEME.bg_input, text_color=THEME.text_primary,
            font=(THEME.font_family, THEME.font_size_sm),
            corner_radius=THEME.radius_md, border_color=THEME.border_card,
            border_width=1, state="disabled", wrap="word",
        )
        self._info_box.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        # Right: file tree
        right = ctk.CTkFrame(body, fg_color=THEME.bg_card,
                             corner_radius=THEME.radius_lg,
                             border_color=THEME.border_card, border_width=1)
        right.grid(row=0, column=1, sticky="nsew")

        SectionHeader(right, "File Tree", "Repository structure").pack(
            fill="x", padx=16, pady=(14, 6))

        self._tree_box = ctk.CTkTextbox(
            right,
            fg_color=THEME.bg_input, text_color=THEME.text_secondary,
            font=(THEME.font_family, THEME.font_size_sm),
            corner_radius=THEME.radius_md, border_color=THEME.border_card,
            border_width=1, state="disabled", wrap="none",
        )
        self._tree_box.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        action_row = ctk.CTkFrame(right, fg_color="transparent")
        action_row.pack(fill="x", padx=16, pady=(0, 14))

        SuccessButton(action_row, "📊 Open in Analyzer",
                      command=self._open_in_analyzer, width=160, height=36).pack(side="left")

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _set_info(self, text: str) -> None:
        self._info_box.configure(state="normal")
        self._info_box.delete("1.0", "end")
        self._info_box.insert("1.0", text)
        self._info_box.configure(state="disabled")

    def _set_tree(self, text: str) -> None:
        self._tree_box.configure(state="normal")
        self._tree_box.delete("1.0", "end")
        self._tree_box.insert("1.0", text)
        self._tree_box.configure(state="disabled")

    # ── Actions ──────────────────────────────────────────────────────────────

    def _fetch_info(self) -> None:
        url = self._url_var.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Enter a GitHub repository URL.")
            return

        self._progress.update("🔍 Fetching repository info…", 20)

        def worker():
            from services.github_importer import github_importer
            try:
                parsed = github_importer.parse_repo_url(url)
                if not parsed:
                    self.after(0, lambda: messagebox.showerror("Error", "Invalid GitHub URL"))
                    return

                owner, repo = parsed
                info = github_importer.get_repo_info(owner, repo)
                branches = github_importer.list_branches(owner, repo)
                tree_items = github_importer.get_file_tree(owner, repo, branches[0] if branches else "main")

                info_text = (
                    f"Name: {info.get('full_name', 'Unknown')}\n"
                    f"Description: {info.get('description') or 'None'}\n"
                    f"Language: {info.get('language', 'Unknown')}\n"
                    f"Stars: {info.get('stargazers_count', 0):,}\n"
                    f"Forks: {info.get('forks_count', 0):,}\n"
                    f"Open Issues: {info.get('open_issues_count', 0)}\n"
                    f"Size: {info.get('size', 0):,} KB\n"
                    f"Default Branch: {info.get('default_branch', 'main')}\n"
                    f"License: {info.get('license', {}).get('name', 'None') if info.get('license') else 'None'}\n"
                    f"Last Updated: {info.get('updated_at', 'Unknown')[:10]}\n"
                    f"Branches: {', '.join(branches[:10])}\n"
                    f"Visibility: {info.get('visibility', 'public')}\n"
                )

                tree_text = "\n".join(
                    f"{'  ' * item['path'].count('/') if '/' in item['path'] else ''}{item['path']}"
                    for item in tree_items[:200]
                )
                if len(tree_items) > 200:
                    tree_text += f"\n\n... and {len(tree_items) - 200} more files"

                def update():
                    self._branch_combo.configure(values=branches)
                    if branches:
                        self._branch_var.set(branches[0])
                    self._set_info(info_text)
                    self._set_tree(tree_text)
                    self._progress.update("✅ Repository info loaded", 100)

                self.after(0, update)

            except Exception as exc:
                self.after(0, lambda: (
                    self._progress.update("❌ Error", 0),
                    messagebox.showerror("GitHub Error", str(exc)),
                ))

        threading.Thread(target=worker, daemon=True).start()

    def _clone_repo(self) -> None:
        url = self._url_var.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Enter a GitHub repository URL.")
            return

        branch = self._branch_var.get()
        self._progress.update("📥 Cloning repository…", 10)

        def worker():
            from services.github_importer import github_importer

            def update(msg, pct):
                self.after(0, lambda: self._progress.update(msg, pct))

            try:
                path = github_importer.clone_repo(url, branch=branch, progress_cb=update)
                self._cloned_path = path

                def done():
                    self._progress.update(f"✅ Cloned to {path}", 100)
                    messagebox.showinfo("Cloned", f"Repository cloned to:\n{path}\n\nClick 'Open in Analyzer' to analyze.")

                self.after(0, done)
            except Exception as exc:
                self.after(0, lambda: (
                    self._progress.update("❌ Clone failed", 0),
                    messagebox.showerror("Clone Error", str(exc)),
                ))

        threading.Thread(target=worker, daemon=True).start()

    def _open_in_analyzer(self) -> None:
        if not self._cloned_path:
            messagebox.showwarning("Not Cloned", "Clone a repository first.")
            return
        analyzer = getattr(self._app, "project_analyzer", None)
        if analyzer:
            analyzer._path_var.set(str(self._cloned_path))
            self._app._show_page("analyzer")
            messagebox.showinfo("Ready", "Repository loaded in Project Analyzer.\nClick 'Scan Project' to begin.")
