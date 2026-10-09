from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:
    yaml = None

DEFAULT_CONFIG_NAME = "weHateTP.yml"

DEFAULT_CONFIG: Dict[str, Any] = {
    "typewriter": {"cps": 12.0, "variance": 0.35, "newline_pause": 0.25, "punctuation_pause": 0.18},
    "warning": {"seconds": 3, "message": "CRITICAL ACTION AHEAD – REVIEW BEFORE CONTINUING", "final_message": "Proceeding..."},
    "oidc": {
        "provider": "github",
        "audience": "sts.amazonaws.com",
        "subject_claim": "repo:{owner}/{repo}:ref:refs/heads/{branch}",
        "role_arn": "arn:aws:iam::ACCOUNT_ID:role/GitHubActionsRole",
        "session_name": "weHateTP-session",
    },
    "git": {"auto_detect": True, "require_clean": False, "default_branch": "main"},
}


def _find_config(start: Optional[str] = None) -> Optional[Path]:
    current = Path(start or os.getcwd()).resolve()
    for parent in [current, *current.parents]:
        candidate = parent / DEFAULT_CONFIG_NAME
        if candidate.is_file():
            return candidate
    return None


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    cfg = {k: (v.copy() if isinstance(v, dict) else v) for k, v in DEFAULT_CONFIG.items()}
    if yaml is None:
        return cfg
    config_path = Path(path) if path else _find_config()
    if config_path and config_path.is_file():
        with open(config_path, encoding="utf-8") as f:
            user = yaml.safe_load(f) or {}
        for section, values in user.items():
            if section in cfg and isinstance(cfg[section], dict) and isinstance(values, dict):
                cfg[section].update(values)
            else:
                cfg[section] = values
    return cfg


def save_example_config(path: Optional[str] = None) -> Path:
    if yaml is None:
        raise RuntimeError("PyYAML is required. Install with: pip install pyyaml")
    target = Path(path or DEFAULT_CONFIG_NAME)
    content = """typewriter:
  cps: 12.0
  variance: 0.35
  newline_pause: 0.25
  punctuation_pause: 0.18

warning:
  seconds: 3
  message: "CRITICAL ACTION AHEAD – REVIEW BEFORE CONTINUING"
  final_message: "Proceeding..."

oidc:
  provider: github
  audience: sts.amazonaws.com
  subject_claim: "repo:{owner}/{repo}:ref:refs/heads/{branch}"
  role_arn: "arn:aws:iam::ACCOUNT_ID:role/GitHubActionsRole"
  session_name: weHateTP-session

git:
  auto_detect: true
  require_clean: false
  default_branch: main
"""
    target.write_text(content, encoding="utf-8")
    return target.resolve()


def generate_oidc_workflow(cfg: Dict[str, Any], owner: str, repo: str, branch: str = "main") -> str:
    oidc = cfg.get("oidc", {})
    role_arn = oidc.get("role_arn", "arn:aws:iam::ACCOUNT_ID:role/GitHubActionsRole")
    session = oidc.get("session_name", "weHateTP-session")
    return f"""name: OIDC Deploy

on:
  push:
    branches: ["{branch}"]
  workflow_dispatch:

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: {role_arn}
          role-session-name: {session}
          aws-region: us-east-1

      - name: Example – whoami
        run: |
          echo "OIDC identity assumed successfully"
          aws sts get-caller-identity || true
"""
