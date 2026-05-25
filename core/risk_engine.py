"""
risk_engine.py — Commit-level and file-level risk scoring.
Produces a 1–100 risk score based on heuristic + AI severity flags.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class RiskFactors:
    lines_changed: int = 0
    files_changed: int = 0
    has_security_issues: bool = False
    has_high_complexity: bool = False
    has_duplicate_code: bool = False
    ai_severity: str = "LOW"   # LOW | MEDIUM | HIGH | CRITICAL
    dependency_changes: bool = False
    config_file_changes: bool = False
    test_coverage_present: bool = True


_SEVERITY_WEIGHT = {"LOW": 0, "MEDIUM": 20, "HIGH": 45, "CRITICAL": 70}


def calculate_risk_score(factors: RiskFactors) -> int:
    """
    Calculate a 0–100 composite risk score.
    Higher = riskier.
    """
    score = 0

    # Lines changed (logarithmic scale)
    if factors.lines_changed > 0:
        import math
        score += min(20, int(math.log10(factors.lines_changed + 1) * 10))

    # Files changed
    score += min(10, factors.files_changed)

    # AI severity flag
    score += _SEVERITY_WEIGHT.get(factors.ai_severity, 0)

    # Heuristic modifiers
    if factors.has_security_issues:
        score += 15
    if factors.has_high_complexity:
        score += 10
    if factors.has_duplicate_code:
        score += 5
    if factors.dependency_changes:
        score += 8
    if factors.config_file_changes:
        score += 7
    if not factors.test_coverage_present:
        score += 10

    return max(0, min(100, score))


def severity_from_score(score: int) -> str:
    if score >= 75:
        return "CRITICAL"
    if score >= 50:
        return "HIGH"
    if score >= 25:
        return "MEDIUM"
    return "LOW"


def color_for_severity(severity: str) -> str:
    """Return a hex colour for UI display."""
    return {
        "CRITICAL": "#FF3333",
        "HIGH": "#FF8C00",
        "MEDIUM": "#FFD700",
        "LOW": "#00FF88",
    }.get(severity, "#AAAAAA")


def parse_ai_severity(report_text: str) -> str:
    """Heuristically derive severity from a report string."""
    text_lower = report_text.lower()
    if "critical" in text_lower:
        return "CRITICAL"
    if "high" in text_lower:
        return "HIGH"
    if "medium" in text_lower:
        return "MEDIUM"
    return "LOW"


def extract_risk_from_report(report: str) -> int:
    """Pull a Risk Score: X/100 value out of an AI report."""
    match = re.search(r"risk score[:\s]+(\d+)/100", report, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 50
