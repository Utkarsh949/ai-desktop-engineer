"""
config.py — Centralised configuration & environment loader.
All settings are resolved once at import-time so the rest of the
application can do `from config import cfg` and access typed values.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root (one level above config/)
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env", override=True)
load_dotenv(_ROOT / ".env.example", override=False)  # fallback


# ─────────────────────────────────────────────────────────────────────────────
#  Config dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Config:
    # ── AI ─────────────────────────────────────────────────────────────────
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    groq_model: str = field(default_factory=lambda: os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"))
    max_tokens: int = field(default_factory=lambda: int(os.getenv("MAX_TOKENS", "4096")))

    # ── GitHub ──────────────────────────────────────────────────────────────
    github_token: str = field(default_factory=lambda: os.getenv("GITHUB_TOKEN", ""))

    # ── Paths ───────────────────────────────────────────────────────────────
    root_dir: Path = field(default_factory=lambda: _ROOT)
    projects_dir: Path = field(
        default_factory=lambda: Path(os.getenv("PROJECTS_DIR", str(_ROOT / "projects")))
    )
    logs_dir: Path = field(
        default_factory=lambda: Path(os.getenv("LOGS_DIR", str(_ROOT / "logs")))
    )
    snippets_dir: Path = field(default_factory=lambda: _ROOT / "snippets")
    exports_dir: Path = field(default_factory=lambda: _ROOT / "exports")

    # ── Scanner ─────────────────────────────────────────────────────────────
    max_file_size: int = field(
        default_factory=lambda: int(os.getenv("MAX_FILE_SIZE", str(512 * 1024)))
    )
    supported_extensions: tuple[str, ...] = (
        ".py", ".js", ".ts", ".jsx", ".tsx",
        ".java", ".cpp", ".c", ".h", ".hpp",
        ".go", ".rs", ".rb", ".php", ".cs",
        ".swift", ".kt", ".scala", ".sh",
        ".yaml", ".yml", ".json", ".toml",
        ".sql", ".html", ".css", ".scss",
    )

    # ── UI ──────────────────────────────────────────────────────────────────
    app_theme: str = field(default_factory=lambda: os.getenv("APP_THEME", "dark"))
    accent_color: str = field(
        default_factory=lambda: os.getenv("ACCENT_COLOR", "#00D4FF")
    )
    app_title: str = "AI Desktop Engineer"
    app_version: str = "2.0.0"
    window_size: str = "1400x860"

    # ── Groq model catalogue ─────────────────────────────────────────────────
    available_models: tuple[str, ...] = (
        "llama-3.3-70b-versatile",
        "llama3-8b-8192",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    )

    # ── Supported languages (UI dropdown) ───────────────────────────────────
    languages: tuple[str, ...] = (
        "Auto-Detect",
        "Python", "JavaScript", "TypeScript",
        "Java", "C++", "C", "Go", "Rust",
        "Ruby", "PHP", "C#", "Swift", "Kotlin",
        "SQL", "HTML", "CSS", "Shell",
    )

    def __post_init__(self) -> None:
        # Ensure all directories exist
        for d in (self.projects_dir, self.logs_dir, self.snippets_dir, self.exports_dir):
            d.mkdir(parents=True, exist_ok=True)

    @property
    def groq_configured(self) -> bool:
        return bool(self.groq_api_key and not self.groq_api_key.startswith("gsk_your"))

    @property
    def github_configured(self) -> bool:
        return bool(self.github_token and not self.github_token.startswith("ghp_your"))


# ── Singleton ──────────────────────────────────────────────────────────────
cfg = Config()
