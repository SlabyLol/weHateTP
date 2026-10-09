# weHateTP

**TypeBot · weHateTP** – By DarkFox

Typewriter effect, TypeBot browser inject, PyPI Trusted Publishing via OIDC.

## Install

```bash
pip install -e .
```

## Start

```bash
weHateTP start
```

Full flow: banner → weHateTP.yml → y/n inject → 3-2-1 → inject script → PyPI OIDC workflows.

## PyPI OIDC

1. https://pypi.org/manage/account/publishing/
2. Owner=SlabyLol Repo=weHateTP Workflow=publish-pypi.yml Environment=pypi
3. GitHub Environment `pypi`
4. Create a Release → publishes via OIDC
