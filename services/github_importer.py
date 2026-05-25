"""
github_importer.py — GitHub repository import via API (no webhooks).
Supports cloning public repos and fetching file trees via GitHub REST API.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Optional

import httpx
from core.logger import get_logger

log = get_logger(__name__)


class GitHubImporter:
    """Fetch repository metadata and clone repos without webhooks."""

    _API = "https://api.github.com"

    def __init__(self) -> None:
        from config.config import cfg
        self._cfg = cfg

    @property
    def _headers(self) -> dict[str, str]:
        h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self._cfg.github_configured:
            h["Authorization"] = f"Bearer {self._cfg.github_token}"
        return h

    # ── URL Parsing ──────────────────────────────────────────────────────────

    @staticmethod
    def parse_repo_url(url: str) -> tuple[str, str] | None:
        """Return (owner, repo) from a GitHub URL, or None."""
        patterns = [
            r"github\.com[:/]([^/]+)/([^/.]+?)(?:\.git)?$",
        ]
        for p in patterns:
            m = re.search(p, url)
            if m:
                return m.group(1), m.group(2)
        return None

    # ── Repo Metadata ────────────────────────────────────────────────────────

    def get_repo_info(self, owner: str, repo: str) -> dict:
        url = f"{self._API}/repos/{owner}/{repo}"
        try:
            with httpx.Client(timeout=15) as c:
                r = c.get(url, headers=self._headers)
                r.raise_for_status()
                return r.json()
        except httpx.HTTPStatusError as e:
            log.error("GitHub API error %s: %s", e.response.status_code, e.response.text)
            raise RuntimeError(f"GitHub API error {e.response.status_code}: {e.response.text}") from e
        except Exception as e:
            log.error("GitHub request failed: %s", e)
            raise

    def list_branches(self, owner: str, repo: str) -> list[str]:
        url = f"{self._API}/repos/{owner}/{repo}/branches"
        try:
            with httpx.Client(timeout=15) as c:
                r = c.get(url, headers=self._headers, params={"per_page": 100})
                r.raise_for_status()
                return [b["name"] for b in r.json()]
        except Exception as e:
            log.warning("Could not list branches: %s", e)
            return ["main", "master"]

    def get_file_tree(self, owner: str, repo: str, branch: str = "main") -> list[dict]:
        """Return flat list of file paths in the repo at given branch."""
        url = f"{self._API}/repos/{owner}/{repo}/git/trees/{branch}"
        try:
            with httpx.Client(timeout=30) as c:
                r = c.get(url, headers=self._headers, params={"recursive": "1"})
                r.raise_for_status()
                data = r.json()
                return [
                    item for item in data.get("tree", [])
                    if item.get("type") == "blob"
                ]
        except Exception as e:
            log.error("Could not fetch file tree: %s", e)
            return []

    # ── Clone ────────────────────────────────────────────────────────────────

    def clone_repo(
        self,
        url: str,
        destination: Path | None = None,
        branch: str | None = None,
        progress_cb: Optional[Callable[[str, int], None]] = None,
    ) -> Path:
        """
        Clone a public GitHub repository to a local directory.
        Returns the path to the cloned repo.
        """
        parsed = self.parse_repo_url(url)
        if not parsed:
            raise ValueError(f"Cannot parse GitHub URL: {url}")

        owner, repo_name = parsed
        dest = destination or (self._cfg.projects_dir / f"{owner}_{repo_name}")

        if dest.exists():
            log.info("Removing existing clone at %s", dest)
            shutil.rmtree(dest)

        cmd = ["git", "clone", "--depth", "1"]
        if branch:
            cmd += ["--branch", branch]

        # Inject token into URL if available
        clone_url = url
        if self._cfg.github_configured and "github.com" in url:
            clone_url = url.replace(
                "https://github.com",
                f"https://{self._cfg.github_token}@github.com",
            )

        cmd += [clone_url, str(dest)]

        if progress_cb:
            progress_cb(f"📥 Cloning {owner}/{repo_name}…", 10)

        log.info("Cloning: %s → %s", url, dest)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode != 0:
                raise RuntimeError(f"git clone failed:\n{result.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Clone timed out after 5 minutes")

        if progress_cb:
            progress_cb(f"✅ Cloned to {dest}", 100)

        log.info("Clone complete: %s", dest)
        return dest

    # ── Single file fetch ────────────────────────────────────────────────────

    def fetch_file(self, owner: str, repo: str, path: str, ref: str = "main") -> str:
        """Fetch raw content of a single file from GitHub."""
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"
        try:
            with httpx.Client(timeout=15) as c:
                r = c.get(url, headers=self._headers)
                r.raise_for_status()
                return r.text
        except Exception as e:
            log.error("Failed to fetch file %s: %s", path, e)
            raise


github_importer = GitHubImporter()
