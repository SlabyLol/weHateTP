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
    pypi = cfg.get("pypi", {})
    py_ver = pypi.get("python_version", "3.11")
    return f"""name: Publish to PyPI (OIDC)

on:
  release:
    types: [published]
  workflow_dispatch:

permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "{py_ver}"
      - run: pip install build
      - run: python -m build
      - uses: actions/upload-artifact@v4
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
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
"""
