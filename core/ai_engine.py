"""
ai_engine.py — Groq AI integration with Triple-Pass auditing,
risk scoring, code generation and debugging.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Callable, Generator, Optional

from groq import Groq
from core.logger import get_logger

log = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
#  Data models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ReviewResult:
    security_report: str = ""
    performance_report: str = ""
    architecture_report: str = ""
    combined_report: str = ""
    risk_score: int = 0
    severity: str = "LOW"        # LOW | MEDIUM | HIGH | CRITICAL
    language: str = "Unknown"
    issues_found: int = 0
    elapsed_seconds: float = 0.0
    model_used: str = ""
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "security_report": self.security_report,
            "performance_report": self.performance_report,
            "architecture_report": self.architecture_report,
            "combined_report": self.combined_report,
            "risk_score": self.risk_score,
            "severity": self.severity,
            "language": self.language,
            "issues_found": self.issues_found,
            "elapsed_seconds": self.elapsed_seconds,
            "model_used": self.model_used,
        }


@dataclass
class DebugResult:
    explanation: str = ""
    fixed_code: str = ""
    issues_detected: list[str] = field(default_factory=list)
    optimizations: list[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class GenerationResult:
    code: str = ""
    explanation: str = ""
    folder_structure: str = ""
    best_practices: list[str] = field(default_factory=list)
    error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
#  Prompts
# ─────────────────────────────────────────────────────────────────────────────

_SYS_BASE = (
    "You are an elite principal software engineer and security architect with "
    "20+ years of experience. You write incredibly specific, actionable, "
    "production-grade analysis. Always respond in structured Markdown."
)

_SECURITY_PROMPT = """Perform a SECURITY AUDIT of the following {language} code following OWASP Top 10 and CWE standards.

Return a Markdown report with these exact sections:
## 🔐 Security Audit Report
### Critical Vulnerabilities
List each as: `[SEVERITY] CWE-XXX — Description — Line reference — Fix`
### High Severity Issues
### Medium Severity Issues  
### Security Best Practices Violations
### Recommended Fixes (code snippets)
### Security Score: X/100

Be ruthlessly specific. Reference exact line numbers or patterns. Include exploit scenarios.

```{language}
{code}
```"""

_PERFORMANCE_PROMPT = """Perform a PERFORMANCE & COMPLEXITY ANALYSIS of the following {language} code.

Return a Markdown report with these exact sections:
## ⚡ Performance Analysis Report
### Time Complexity Issues
List as: `Function/Block — Current O(?) — Optimal O(?) — Impact`
### Space Complexity Issues
### Memory Leaks & Resource Handling
### N+1 Query Problems / Inefficient I/O
### CPU Hotspots
### Optimized Code Snippets
### Performance Score: X/100

Be specific about Big-O notation and real-world throughput impact.

```{language}
{code}
```"""

_ARCHITECTURE_PROMPT = """Perform an ARCHITECTURE & CODE QUALITY REVIEW of the following {language} code.

Return a Markdown report with these exact sections:
## 🏗️ Architecture Review Report
### SOLID Principle Violations
### Design Pattern Opportunities
### Code Smells Detected
List each as: `[Smell Type] — Location — Refactoring Strategy`
### Coupling & Cohesion Analysis
### Testability Assessment
### Maintainability Index
### Refactored Code Example
### Architecture Score: X/100

Focus on structural issues, not style preferences.

```{language}
{code}
```"""

_DEBUG_PROMPT = """You are a world-class debugger. Analyze the following {language} code and identify ALL bugs.

Return your response as valid JSON with this exact schema:
{{
  "explanation": "Clear explanation of what is wrong and why",
  "issues_detected": ["Issue 1 description", "Issue 2 description"],
  "optimizations": ["Optimization 1", "Optimization 2"],
  "fixed_code": "The complete corrected and optimized code here"
}}

Do NOT wrap in markdown code fences. Return raw JSON only.

Code to debug:
```{language}
{code}
```"""

_GENERATE_PROMPT = """REQUEST: {prompt}
LANGUAGE/FRAMEWORK: {language}

Write the complete implementation. Rules:
- Write exactly as much code as the task requires, no more and no less
- No placeholder comments like "# add your logic here" or "# TODO"
- No filler, no padding, no repeated boilerplate just to look longer
- Every function and class must be fully implemented and runnable
- Include clear inline comments only where the logic genuinely needs explaining
- Follow language-specific best practices and handle errors properly
- Use type hints and type annotations where the language supports them

After the code block, add these three sections separated by blank lines:

**How it works:**
A concise explanation of the architecture and key decisions.

**Folder structure** (only if the request involves multiple files):
A short tree showing how files should be organised.

**Best practices applied:**
A bullet list of the specific practices used in this implementation."""

_PASTE_ANALYZE_PROMPT = """Perform a COMPLETE ANALYSIS of the following code snippet.

Return a Markdown report with these sections:
## 🔍 Universal Code Analysis

### Language Detected
### Errors Found
List each: `[TYPE] Line X — Description — Fix`
### Code Issues Explanation
### Optimized Rewrite
```
paste the rewritten optimized version here
```
### Complexity Estimate
- Time Complexity: O(?)
- Space Complexity: O(?)
- Cyclomatic Complexity: X
### Risk Score: X/100 — [LOW|MEDIUM|HIGH|CRITICAL]
### Summary

```{language}
{code}
```"""


# ─────────────────────────────────────────────────────────────────────────────
#  Risk Scoring
# ─────────────────────────────────────────────────────────────────────────────

def _extract_scores(text: str) -> list[int]:
    """Extract all X/100 scores from a report string."""
    matches = re.findall(r"Score:\s*(\d+)/100", text, re.IGNORECASE)
    return [int(m) for m in matches if 0 <= int(m) <= 100]


def _severity_label(score: int) -> str:
    if score >= 80:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"


def _count_issues(text: str) -> int:
    """Heuristic: count bullet/list items that look like issues."""
    return len(re.findall(r"^\s*[-*•]\s+\[?(CRITICAL|HIGH|MEDIUM|LOW|BUG|ERROR|WARN)", text, re.MULTILINE | re.IGNORECASE))


# ─────────────────────────────────────────────────────────────────────────────
#  Engine
# ─────────────────────────────────────────────────────────────────────────────

class AIEngine:
    def __init__(self) -> None:
        from config.config import cfg
        self._cfg = cfg
        self._client: Optional[Groq] = None
        self._init_client()

    def _init_client(self) -> None:
        if self._cfg.groq_configured:
            try:
                self._client = Groq(api_key=self._cfg.groq_api_key)
                log.info("Groq client initialised — model: %s", self._cfg.groq_model)
            except Exception as exc:
                log.error("Failed to initialise Groq client: %s", exc)
                self._client = None
        else:
            log.warning("GROQ_API_KEY not set — AI features disabled")

    def _chat(
        self,
        system: str,
        user: str,
        max_tokens: int | None = None,
        stream_cb: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Single chat completion with optional streaming callback."""
        if not self._client:
            return "⚠️  Groq API key not configured. Add GROQ_API_KEY to your .env file."

        try:
            mt = max_tokens or self._cfg.max_tokens
            if stream_cb:
                collected = []
                with self._client.chat.completions.create(
                    model=self._cfg.groq_model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    max_tokens=mt,
                    stream=True,
                ) as stream:
                    for chunk in stream:
                        delta = chunk.choices[0].delta.content or ""
                        collected.append(delta)
                        if stream_cb:
                            stream_cb(delta)
                return "".join(collected)
            else:
                resp = self._client.chat.completions.create(
                    model=self._cfg.groq_model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    max_tokens=mt,
                )
                return resp.choices[0].message.content or ""
        except Exception as exc:
            log.error("Groq API error: %s", exc)
            return f"❌ API Error: {exc}"

    # ── Triple-Pass Audit ────────────────────────────────────────────────────

    def triple_pass_audit(
        self,
        code: str,
        language: str = "Auto-Detect",
        progress_cb: Optional[Callable[[str, int], None]] = None,
    ) -> ReviewResult:
        """
        Run three sequential AI passes:
          1. Security (OWASP)
          2. Performance / Big-O
          3. Architecture / Code smells
        Combine into a single structured result.
        """
        result = ReviewResult(language=language, model_used=self._cfg.groq_model)
        t0 = time.time()

        lang = language if language != "Auto-Detect" else "code"

        # Pass 1 — Security
        if progress_cb:
            progress_cb("🔐 Pass 1/3 — Security Audit…", 15)
        log.info("Triple-pass: security pass started")
        result.security_report = self._chat(
            _SYS_BASE,
            _SECURITY_PROMPT.format(language=lang, code=code),
        )

        # Pass 2 — Performance
        if progress_cb:
            progress_cb("⚡ Pass 2/3 — Performance Analysis…", 50)
        log.info("Triple-pass: performance pass started")
        result.performance_report = self._chat(
            _SYS_BASE,
            _PERFORMANCE_PROMPT.format(language=lang, code=code),
        )

        # Pass 3 — Architecture
        if progress_cb:
            progress_cb("🏗️ Pass 3/3 — Architecture Review…", 80)
        log.info("Triple-pass: architecture pass started")
        result.architecture_report = self._chat(
            _SYS_BASE,
            _ARCHITECTURE_PROMPT.format(language=lang, code=code),
        )

        # Combine
        result.combined_report = "\n\n---\n\n".join([
            result.security_report,
            result.performance_report,
            result.architecture_report,
        ])

        # Scoring
        all_scores = _extract_scores(result.combined_report)
        if all_scores:
            # Invert: lower audit scores → higher risk
            avg_audit = sum(all_scores) / len(all_scores)
            result.risk_score = max(0, min(100, int(100 - avg_audit)))
        else:
            result.risk_score = 50

        result.severity = _severity_label(result.risk_score)
        result.issues_found = _count_issues(result.combined_report)
        result.elapsed_seconds = round(time.time() - t0, 2)

        if progress_cb:
            progress_cb("✅ Audit complete", 100)
        log.info(
            "Triple-pass complete — risk=%d severity=%s issues=%d elapsed=%.1fs",
            result.risk_score, result.severity, result.issues_found, result.elapsed_seconds,
        )
        return result

    # ── Universal Paste Analyzer ─────────────────────────────────────────────

    def analyze_paste(
        self,
        code: str,
        language: str = "Auto-Detect",
        stream_cb: Optional[Callable[[str], None]] = None,
    ) -> str:
        lang = language if language != "Auto-Detect" else "code"
        log.info("Paste analysis: lang=%s len=%d", lang, len(code))
        return self._chat(
            _SYS_BASE,
            _PASTE_ANALYZE_PROMPT.format(language=lang, code=code),
            stream_cb=stream_cb,
        )

    # ── Debugger ────────────────────────────────────────────────────────────

    def debug_code(self, code: str, language: str = "Python") -> DebugResult:
        log.info("Debugging: lang=%s len=%d", language, len(code))
        raw = self._chat(
            _SYS_BASE,
            _DEBUG_PROMPT.format(language=language, code=code),
            max_tokens=self._cfg.max_tokens,
        )
        try:
            # Strip markdown fences if present
            cleaned = re.sub(r"```(?:json)?\n?", "", raw).strip().rstrip("`")
            data = json.loads(cleaned)
            return DebugResult(
                explanation=data.get("explanation", ""),
                fixed_code=data.get("fixed_code", ""),
                issues_detected=data.get("issues_detected", []),
                optimizations=data.get("optimizations", []),
            )
        except json.JSONDecodeError:
            # Fallback: return raw text as explanation
            return DebugResult(explanation=raw, fixed_code="")

    # ── Generator ───────────────────────────────────────────────────────────

    def generate_code(
        self,
        prompt: str,
        language: str = "Python",
        stream_cb: Optional[Callable[[str], None]] = None,
    ) -> GenerationResult:
        log.info("Code generation: lang=%s prompt=%s…", language, prompt[:60])
        raw = self._chat(
            _SYS_BASE,
            _GENERATE_PROMPT.format(prompt=prompt, language=language),
            max_tokens=8192,
            stream_cb=stream_cb,
        )

        # Parse plain markdown response — extract code block and sections
        code = ""
        explanation = ""
        folder_structure = ""
        best_practices: list[str] = []

        # Extract fenced code block(s)
        code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", raw, re.DOTALL)
        if code_blocks:
            code = "\n\n".join(b.strip() for b in code_blocks)
            remainder = re.sub(r"```(?:\w+)?\n.*?```", "", raw, flags=re.DOTALL).strip()
        else:
            # No fences — treat entire response as code
            code = raw.strip()
            remainder = ""

        # Extract "How it works" section
        m = re.search(r"\*\*How it works:\*\*\s*(.+?)(?=\*\*|$)", remainder, re.DOTALL | re.IGNORECASE)
        if m:
            explanation = m.group(1).strip()

        # Extract "Folder structure" section
        m = re.search(r"\*\*Folder structure\*\*.*?:\s*(.+?)(?=\*\*|$)", remainder, re.DOTALL | re.IGNORECASE)
        if m:
            folder_structure = m.group(1).strip()

        # Extract "Best practices" bullets
        m = re.search(r"\*\*Best practices applied:\*\*\s*(.+?)(?=\*\*|$)", remainder, re.DOTALL | re.IGNORECASE)
        if m:
            lines = m.group(1).strip().splitlines()
            best_practices = [l.lstrip("-•* ").strip() for l in lines if l.strip()]

        return GenerationResult(
            code=code,
            explanation=explanation or remainder,
            folder_structure=folder_structure,
            best_practices=best_practices,
        )

    # ── AI Builder (full project) ────────────────────────────────────────────

    def build_project(
        self,
        idea: str,
        language: str = "Python",
        progress_cb: Optional[Callable[[str, int], None]] = None,
    ) -> str:
        """Generate a complete project description with folder layout and multiple files."""
        system = (
            "You are a world-class software architect. When given an app idea, "
            "you produce a complete, production-ready project specification including "
            "folder structure, all source files with full implementations, "
            "README, requirements, and setup instructions. "
            "Format everything as structured Markdown."
        )
        user = f"""Build a complete, production-ready project for:

**{idea}**

Language/Stack: {language}

Include:
1. ## Project Overview
2. ## Architecture Diagram (ASCII)
3. ## Folder Structure (tree)
4. ## Complete Source Files (each in its own ``` code block with filename as header)
5. ## requirements.txt / package.json
6. ## Setup & Run Instructions
7. ## API Documentation (if applicable)
8. ## Best Practices Applied

Write REAL, runnable code. No pseudocode. No placeholders."""

        if progress_cb:
            progress_cb("🏗️ Architecting project…", 20)

        result = self._chat(system, user, max_tokens=self._cfg.max_tokens, stream_cb=None)

        if progress_cb:
            progress_cb("✅ Project generated", 100)

        return result

    def reload_config(self) -> None:
        """Re-read env and reinitialise client (called after settings save)."""
        from config.config import Config
        from importlib import reload
        import config.config as _cfg_mod
        reload(_cfg_mod)
        self._cfg = _cfg_mod.cfg
        self._init_client()


# ── Singleton ──────────────────────────────────────────────────────────────
ai_engine = AIEngine()
