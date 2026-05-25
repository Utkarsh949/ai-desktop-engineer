"""
project_scanner.py — Recursive local project scanner.
Produces file statistics, complexity metrics, and a health report.
"""

from __future__ import annotations

import ast
import hashlib
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import chardet
from core.logger import get_logger

log = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
#  Data models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class FileStats:
    path: str
    extension: str
    size_bytes: int
    line_count: int
    blank_lines: int
    comment_lines: int
    code_lines: int
    hash: str
    encoding: str = "utf-8"


@dataclass
class ProjectReport:
    project_path: str
    total_files: int = 0
    total_lines: int = 0
    total_code_lines: int = 0
    total_size_bytes: int = 0
    language_breakdown: dict[str, int] = field(default_factory=dict)
    duplicate_files: list[list[str]] = field(default_factory=list)
    largest_files: list[FileStats] = field(default_factory=list)
    complexity_hotspots: list[dict] = field(default_factory=list)
    dependency_files: list[str] = field(default_factory=list)
    health_score: int = 0
    scan_seconds: float = 0.0
    file_stats: list[FileStats] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def avg_file_size(self) -> int:
        if not self.total_files:
            return 0
        return self.total_size_bytes // self.total_files

    @property
    def language_labels(self) -> list[str]:
        return list(self.language_breakdown.keys())

    @property
    def language_counts(self) -> list[int]:
        return list(self.language_breakdown.values())


# ─────────────────────────────────────────────────────────────────────────────
#  Extension → language mapping
# ─────────────────────────────────────────────────────────────────────────────

_EXT_MAP: dict[str, str] = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".jsx": "React/JSX", ".tsx": "React/TSX", ".java": "Java",
    ".cpp": "C++", ".c": "C", ".h": "C/C++ Header",
    ".go": "Go", ".rs": "Rust", ".rb": "Ruby",
    ".php": "PHP", ".cs": "C#", ".swift": "Swift",
    ".kt": "Kotlin", ".scala": "Scala", ".sh": "Shell",
    ".yaml": "YAML", ".yml": "YAML", ".json": "JSON",
    ".toml": "TOML", ".sql": "SQL", ".html": "HTML",
    ".css": "CSS", ".scss": "SCSS", ".md": "Markdown",
}

_DEPENDENCY_FILES = {
    "requirements.txt", "pyproject.toml", "setup.py",
    "package.json", "package-lock.json", "yarn.lock",
    "Pipfile", "Pipfile.lock", "go.mod", "go.sum",
    "Cargo.toml", "Cargo.lock", "pom.xml", "build.gradle",
    "Gemfile", "Gemfile.lock", "composer.json",
}

_IGNORE_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "env", ".env", "dist", "build", ".next", ".nuxt",
    "target", "out", ".idea", ".vscode", ".mypy_cache",
    ".pytest_cache", "coverage",
}


# ─────────────────────────────────────────────────────────────────────────────
#  Scanner
# ─────────────────────────────────────────────────────────────────────────────

class ProjectScanner:
    def __init__(self) -> None:
        from config.config import cfg
        self._cfg = cfg

    def scan(
        self,
        project_path: str | Path,
        progress_cb=None,
    ) -> ProjectReport:
        root = Path(project_path).resolve()
        report = ProjectReport(project_path=str(root))
        t0 = time.time()

        if not root.exists():
            report.error = f"Path does not exist: {root}"
            return report

        if progress_cb:
            progress_cb("🔍 Scanning files…", 5)

        all_files = self._collect_files(root)
        report.total_files = len(all_files)

        hash_map: dict[str, list[str]] = defaultdict(list)
        lang_counts: dict[str, int] = defaultdict(int)
        stats_list: list[FileStats] = []

        for i, fpath in enumerate(all_files):
            if progress_cb and i % 20 == 0:
                pct = int(10 + (i / max(len(all_files), 1)) * 60)
                progress_cb(f"📄 Analysing {fpath.name}…", pct)

            fstats = self._analyse_file(fpath, root)
            if fstats is None:
                continue

            stats_list.append(fstats)
            report.total_lines += fstats.line_count
            report.total_code_lines += fstats.code_lines
            report.total_size_bytes += fstats.size_bytes

            lang = _EXT_MAP.get(fstats.extension, "Other")
            lang_counts[lang] += fstats.code_lines

            hash_map[fstats.hash].append(fstats.path)

            if fpath.name in _DEPENDENCY_FILES:
                report.dependency_files.append(str(fpath.relative_to(root)))

        report.file_stats = stats_list
        report.language_breakdown = dict(
            sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)
        )
        report.duplicate_files = [
            paths for paths in hash_map.values() if len(paths) > 1
        ]
        report.largest_files = sorted(stats_list, key=lambda s: s.size_bytes, reverse=True)[:10]

        if progress_cb:
            progress_cb("🔬 Analysing complexity hotspots…", 75)

        report.complexity_hotspots = self._python_complexity(root)

        report.health_score = self._health_score(report)
        report.scan_seconds = round(time.time() - t0, 2)

        if progress_cb:
            progress_cb("✅ Scan complete", 100)

        log.info(
            "Scan complete: %d files, %d LOC, health=%d, %.1fs",
            report.total_files, report.total_code_lines,
            report.health_score, report.scan_seconds,
        )
        return report

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _collect_files(self, root: Path) -> list[Path]:
        files = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in _IGNORE_DIRS]
            for fname in filenames:
                fpath = Path(dirpath) / fname
                ext = fpath.suffix.lower()
                if ext in self._cfg.supported_extensions:
                    if fpath.stat().st_size <= self._cfg.max_file_size:
                        files.append(fpath)
        return files

    def _analyse_file(self, fpath: Path, root: Path) -> FileStats | None:
        try:
            raw = fpath.read_bytes()
            enc_info = chardet.detect(raw)
            enc = enc_info.get("encoding") or "utf-8"
            text = raw.decode(enc, errors="replace")
        except Exception as e:
            log.debug("Skipping %s: %s", fpath, e)
            return None

        lines = text.splitlines()
        blank = sum(1 for ln in lines if not ln.strip())
        comment = sum(1 for ln in lines if ln.strip().startswith(("#", "//", "*", "/*", "<!--")))
        code_lines = len(lines) - blank - comment

        file_hash = hashlib.md5(raw).hexdigest()

        return FileStats(
            path=str(fpath.relative_to(root)),
            extension=fpath.suffix.lower(),
            size_bytes=fpath.stat().st_size,
            line_count=len(lines),
            blank_lines=blank,
            comment_lines=comment,
            code_lines=max(0, code_lines),
            hash=file_hash,
            encoding=enc,
        )

    def _python_complexity(self, root: Path) -> list[dict]:
        """Basic cyclomatic complexity estimation for Python files."""
        hotspots = []
        py_files = list(root.rglob("*.py"))
        for fpath in py_files[:50]:  # cap at 50 files
            try:
                src = fpath.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(src, filename=str(fpath))
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    complexity = self._cyclomatic(node)
                    if complexity >= 5:
                        hotspots.append({
                            "file": str(fpath.relative_to(root)),
                            "function": node.name,
                            "line": node.lineno,
                            "complexity": complexity,
                            "risk": "HIGH" if complexity >= 10 else "MEDIUM",
                        })

        return sorted(hotspots, key=lambda x: x["complexity"], reverse=True)[:20]

    @staticmethod
    def _cyclomatic(func_node: ast.AST) -> int:
        """Count branches inside a function for a basic complexity estimate."""
        complexity = 1
        branch_nodes = (
            ast.If, ast.For, ast.While, ast.ExceptHandler,
            ast.With, ast.Assert, ast.comprehension,
        )
        for node in ast.walk(func_node):
            if isinstance(node, branch_nodes):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity

    @staticmethod
    def _health_score(report: ProjectReport) -> int:
        score = 100
        # Duplicate files penalty
        score -= min(30, len(report.duplicate_files) * 5)
        # Large files penalty
        oversized = sum(1 for f in report.file_stats if f.line_count > 500)
        score -= min(20, oversized * 3)
        # Complexity hotspots penalty
        high_risk = sum(1 for h in report.complexity_hotspots if h["risk"] == "HIGH")
        score -= min(30, high_risk * 4)
        # No dependency files
        if not report.dependency_files:
            score -= 10
        return max(0, score)


project_scanner = ProjectScanner()
