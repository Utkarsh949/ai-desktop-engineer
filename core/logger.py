"""
logger.py — Rotating file logger + Rich console handler.
Usage:
    from core.logger import get_logger
    log = get_logger(__name__)
    log.info("Hello")
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.logging import RichHandler
from rich.console import Console

_console = Console(stderr=True)
_loggers: dict[str, logging.Logger] = {}


def get_logger(name: str, log_dir: Path | None = None) -> logging.Logger:
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # ── Rich console handler ────────────────────────────────────────────────
    rich_handler = RichHandler(
        console=_console,
        show_time=True,
        show_path=False,
        rich_tracebacks=True,
        markup=True,
    )
    rich_handler.setLevel(logging.INFO)
    logger.addHandler(rich_handler)

    # ── Rotating file handler ───────────────────────────────────────────────
    if log_dir is None:
        from config.config import cfg
        log_dir = cfg.logs_dir

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    _loggers[name] = logger
    return logger
