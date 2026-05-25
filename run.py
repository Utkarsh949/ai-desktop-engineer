#!/usr/bin/env python3
"""
run.py — Entry point for AI Desktop Engineer.

Usage:
    python run.py
"""

from __future__ import annotations

import sys
import os

# ── Ensure project root is on sys.path ────────────────────────────────────────
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ── Dependency check ──────────────────────────────────────────────────────────
_REQUIRED = [
    ("customtkinter", "customtkinter"),
    ("groq", "groq"),
    ("dotenv", "python-dotenv"),
    ("rich", "rich"),
    ("PIL", "pillow"),
    ("httpx", "httpx"),
    ("chardet", "chardet"),
    ("git", "gitpython"),
]

_missing = []
for module, pkg in _REQUIRED:
    try:
        __import__(module)
    except ImportError:
        _missing.append(pkg)

if _missing:
    print("=" * 60)
    print("  Missing dependencies detected!")
    print("=" * 60)
    print(f"\n  Run: pip install {' '.join(_missing)}\n")
    print("  Or:  pip install -r requirements.txt\n")
    sys.exit(1)

# ── Launch ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from core.logger import get_logger
    log = get_logger("run")
    log.info("=" * 50)
    log.info("  AI Desktop Engineer — Starting")
    log.info("=" * 50)

    try:
        from ui.main_gui import launch
        launch()
    except Exception as exc:
        log.exception("Fatal startup error: %s", exc)
        sys.exit(1)
