from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class GitContext:
    is_repo: bool = False
    root: Optional[str] = None
    branch: Optional[str] = None
    remote_url: Optional[str] = None
    remote_name: Optional[str] = None
    owner: Optional[str] = None
    repo: Optional[str] = None
    is_github: bool = False
    is_dirty: bool = False
    latest_commit: Optional[str] = None

    def summary(self) -> str:
        if not self.is_repo:
            return "Not inside a Git repository."
        parts = [f"Root: {self.root}", f"Branch: {self.branch or 'unknown'}"]
        if self.remote_url:
            parts.append(f"Remote ({self.remote_name}): {self.remote_url}")
        if self.is_github and self.owner and self.repo:
            parts.append(f"GitHub: {self.owner}/{self.repo}")
        parts.append("Working tree: DIRTY" if self.is_dirty else "Working tree: clean")
        if self.latest_commit:
            parts.append(f"HEAD: {self.latest_commit[:8]}")
        return "\n".join(parts)


def _run(cmd: list, cwd: Optional[str] = None) -> Optional[str]:
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=5, check=False)
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def _parse_github_url(url: str):
    m = re.match(r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$", url)
    if m:
        return m.group(1), m.group(2)
    m = re.match(r"https?://(?:www\.)?github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", url)
    if m:
        return m.group(1), m.group(2)
    m = re.match(r"ssh://git@github\.com/([^/]+)/([^/]+?)(?:\.git)?$", url)
    if m:
        return m.group(1), m.group(2)
    return None, None


def detect_git_context(path: Optional[str] = None) -> GitContext:
    ctx = GitContext()
    start = Path(path or os.getcwd()).resolve()
    root = _run(["git", "rev-parse", "--show-toplevel"], cwd=str(start))
    if not root:
        return ctx
    ctx.is_repo = True
    ctx.root = root
    ctx.branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root)
    ctx.latest_commit = _run(["git", "rev-parse", "HEAD"], cwd=root)
    status = _run(["git", "status", "--porcelain"], cwd=root)
    ctx.is_dirty = bool(status)
    remotes = _run(["git", "remote"], cwd=root)
    if remotes:
        remote_list = remotes.splitlines()
        preferred = "origin" if "origin" in remote_list else remote_list[0]
        ctx.remote_name = preferred
        url = _run(["git", "remote", "get-url", preferred], cwd=root)
        if url:
            ctx.remote_url = url
            owner, repo = _parse_github_url(url)
            if owner and repo:
                ctx.owner = owner
                ctx.repo = repo
                ctx.is_github = True
    return ctx
