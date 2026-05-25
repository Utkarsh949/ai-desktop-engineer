"""
tests/test_core.py — Unit tests for core modules (no API calls needed).
Run with: python -m pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


# ── Risk Engine Tests ──────────────────────────────────────────────────────────

def test_risk_score_low():
    from core.risk_engine import RiskFactors, calculate_risk_score
    f = RiskFactors(lines_changed=10, files_changed=1, ai_severity="LOW")
    score = calculate_risk_score(f)
    assert 0 <= score <= 40


def test_risk_score_critical():
    from core.risk_engine import RiskFactors, calculate_risk_score
    f = RiskFactors(
        lines_changed=1000,
        files_changed=20,
        ai_severity="CRITICAL",
        has_security_issues=True,
        has_high_complexity=True,
        dependency_changes=True,
        test_coverage_present=False,
    )
    score = calculate_risk_score(f)
    assert score >= 70


def test_severity_labels():
    from core.risk_engine import severity_from_score
    assert severity_from_score(0) == "LOW"
    assert severity_from_score(30) == "MEDIUM"
    assert severity_from_score(55) == "HIGH"
    assert severity_from_score(80) == "CRITICAL"


def test_parse_ai_severity():
    from core.risk_engine import parse_ai_severity
    assert parse_ai_severity("There are critical issues here") == "CRITICAL"
    assert parse_ai_severity("High severity SQL injection") == "HIGH"
    assert parse_ai_severity("No major problems found") == "LOW"


def test_extract_risk_score():
    from core.risk_engine import extract_risk_from_report
    report = "## Summary\nRisk Score: 73/100\nSeverity: HIGH"
    assert extract_risk_from_report(report) == 73


# ── Config Tests ───────────────────────────────────────────────────────────────

def test_config_loads():
    from config.config import cfg
    assert cfg.app_title == "AI Desktop Engineer"
    assert len(cfg.languages) > 5
    assert len(cfg.supported_extensions) > 10


def test_config_directories_created():
    from config.config import cfg
    assert cfg.logs_dir.exists()
    assert cfg.projects_dir.exists()
    assert cfg.exports_dir.exists()
    assert cfg.snippets_dir.exists()


# ── GitHub Importer Tests ──────────────────────────────────────────────────────

def test_parse_github_url_https():
    from services.github_importer import GitHubImporter
    imp = GitHubImporter()
    result = imp.parse_repo_url("https://github.com/owner/my-repo")
    assert result == ("owner", "my-repo")


def test_parse_github_url_git():
    from services.github_importer import GitHubImporter
    imp = GitHubImporter()
    result = imp.parse_repo_url("https://github.com/owner/repo.git")
    assert result == ("owner", "repo")


def test_parse_github_url_invalid():
    from services.github_importer import GitHubImporter
    imp = GitHubImporter()
    result = imp.parse_repo_url("https://gitlab.com/owner/repo")
    assert result is None


# ── Project Scanner Tests ──────────────────────────────────────────────────────

def test_scanner_nonexistent_path():
    from analyzers.project_scanner import ProjectScanner
    scanner = ProjectScanner()
    report = scanner.scan("/nonexistent/path/xyz")
    assert report.error is not None


def test_scanner_on_project_root():
    """Scan this very project directory."""
    from analyzers.project_scanner import ProjectScanner
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scanner = ProjectScanner()
    report = scanner.scan(root)
    assert report.total_files >= 0
    assert report.health_score >= 0


def test_cyclomatic_complexity():
    from analyzers.project_scanner import ProjectScanner
    import ast
    src = """
def complex_func(x, y):
    if x > 0:
        if y > 0:
            for i in range(x):
                if i % 2 == 0:
                    pass
    elif x < 0:
        while y > 0:
            y -= 1
    return x + y
"""
    scanner = ProjectScanner()
    tree = ast.parse(src)
    func = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    complexity = scanner._cyclomatic(func)
    assert complexity >= 5


# ── Logger Tests ───────────────────────────────────────────────────────────────

def test_logger_creates_file():
    from core.logger import get_logger
    from config.config import cfg
    log = get_logger("test_module")
    log.info("Test log entry")
    log_file = cfg.logs_dir / "app.log"
    assert log_file.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
