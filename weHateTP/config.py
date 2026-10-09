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
    "typewriter": {"cps": 14.0, "variance": 0.4, "newline_pause": 0.2, "punctuation_pause": 0.15},
    "warning": {"seconds": 3, "message": "TypeBot ACTIVE – By DarkFox", "final_message": "Ready."},
    "inject": {"duration_ms": 5000, "label": "TypeBot", "author": "By DarkFox"},
    "pypi": {"package_name": "weHateTP", "python_version": "3.11", "oidc": True},
    "github": {"owner": "SlabyLol", "repo": "weHateTP", "branch": "main"},
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
        raise RuntimeError("PyYAML required: pip install pyyaml")
    target = Path(path or DEFAULT_CONFIG_NAME)
    target.write_text("""typewriter:
  cps: 14.0
  variance: 0.4
  newline_pause: 0.2
  punctuation_pause: 0.15

warning:
  seconds: 3
  message: "TypeBot ACTIVE – By DarkFox"
  final_message: "Ready."

inject:
  duration_ms: 5000
  label: TypeBot
  author: "By DarkFox"

pypi:
  package_name: weHateTP
  python_version: "3.11"
  oidc: true

github:
  owner: SlabyLol
  repo: weHateTP
  branch: main
""", encoding="utf-8")
    return target.resolve()


def generate_pypi_oidc_workflow(cfg: Dict[str, Any]) -> str:
    gh = cfg.get("github", {})
    pypi = cfg.get("pypi", {})
    branch = gh.get("branch", "main")
    py_ver = pypi.get("python_version", "3.11")
    return f"""name: Publish to PyPI (OIDC)

on:
  release:
    types: [published]
  workflow_dispatch:

permissions:
  id-token: write
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "{py_ver}"
      - name: Install build tools
        run: pip install build
      - name: Build package
        run: python -m build
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  publish:
    needs: build
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    steps:
      - name: Download artifact
        uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - name: Publish to PyPI (Trusted Publishing / OIDC)
        uses: pypa/gh-action-pypi-publish@release/v1
"""


def generate_oidc_deploy_workflow(cfg: Dict[str, Any]) -> str:
    gh = cfg.get("github", {})
    branch = gh.get("branch", "main")
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
      - uses: actions/checkout@v4
      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::ACCOUNT_ID:role/GitHubActionsRole
          role-session-name: weHateTP-session
          aws-region: us-east-1
      - name: Verify identity
        run: |
          echo "OIDC assumed"
          aws sts get-caller-identity || true
"""
