from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:
    yaml = None

DEFAULT_CONFIG_NAME = "weHateTP.yml"
DEFAULT_JSON_NAME = "weHateTP.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "typewriter": {"cps": 14.0, "variance": 0.4, "newline_pause": 0.2, "punctuation_pause": 0.15},
    "warning": {"seconds": 3, "message": "TypeBot ACTIVE – By DarkFox", "final_message": "Ready."},
    "inject": {"duration_ms": 5000, "label": "TypeBot", "author": "By DarkFox"},
    "pypi": {"package_name": "weHateTP", "python_version": "3.12", "oidc": True},
    "github": {"owner": "SlabyLol", "repo": "weHateTP", "branch": "main"},
}


def _find_config(start: Optional[str] = None) -> Optional[Path]:
    current = Path(start or os.getcwd()).resolve()
    for parent in [current, *current.parents]:
        for name in (DEFAULT_CONFIG_NAME, DEFAULT_JSON_NAME):
            candidate = parent / name
            if candidate.is_file():
                return candidate
    return None


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    cfg = {k: (v.copy() if isinstance(v, dict) else v) for k, v in DEFAULT_CONFIG.items()}
    config_path = Path(path) if path else _find_config()
    if not config_path or not config_path.is_file():
        return cfg
    text = config_path.read_text(encoding="utf-8")
    user: Dict[str, Any] = {}
    if config_path.suffix in (".yml", ".yaml") and yaml is not None:
        user = yaml.safe_load(text) or {}
    else:
        try:
            user = json.loads(text)
        except json.JSONDecodeError:
            if yaml is not None:
                user = yaml.safe_load(text) or {}
    for section, values in user.items():
        if section in cfg and isinstance(cfg[section], dict) and isinstance(values, dict):
            cfg[section].update(values)
        else:
            cfg[section] = values
    return cfg


def save_example_config(path: Optional[str] = None) -> Path:
    if path:
        target = Path(path)
    elif yaml is not None:
        target = Path(DEFAULT_CONFIG_NAME)
    else:
        target = Path(DEFAULT_JSON_NAME)

    data = {
        "typewriter": DEFAULT_CONFIG["typewriter"],
        "warning": DEFAULT_CONFIG["warning"],
        "inject": DEFAULT_CONFIG["inject"],
        "pypi": DEFAULT_CONFIG["pypi"],
        "github": DEFAULT_CONFIG["github"],
    }

    if target.suffix in (".yml", ".yaml") and yaml is not None:
        target.write_text(
            "typewriter:\n  cps: 14.0\n  variance: 0.4\n  newline_pause: 0.2\n  punctuation_pause: 0.15\n\n"
            "warning:\n  seconds: 3\n  message: \"TypeBot ACTIVE – By DarkFox\"\n  final_message: \"Ready.\"\n\n"
            "inject:\n  duration_ms: 5000\n  label: TypeBot\n  author: \"By DarkFox\"\n\n"
            "pypi:\n  package_name: weHateTP\n  python_version: \"3.12\"\n  oidc: true\n\n"
            "github:\n  owner: SlabyLol\n  repo: weHateTP\n  branch: main\n",
            encoding="utf-8",
        )
    else:
        if target.suffix in (".yml", ".yaml"):
            target = target.with_suffix(".json")
        target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return target.resolve()


def generate_pypi_oidc_workflow(cfg: Dict[str, Any]) -> str:
    pypi = cfg.get("pypi", {})
    py_ver = pypi.get("python_version", "3.12")
    return f"""name: Publish to PyPI (OIDC)

on:
  release:
    types: [published]
  workflow_dispatch:

permissions:
  contents: read
  id-token: write

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
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
"""
