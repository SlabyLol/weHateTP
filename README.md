# weHateTP

**TypeBot + GitHub Actions OIDC + inject**  
By DarkFox

## Install

```bash
pip install -e .
```

## Commands

| Command | Description |
|---------|-------------|
| `weHateTP start` | Inject + generate Actions workflow |
| `weHateTP inject` | TypeBot overlay script (y/n + 3-2-1) |
| `weHateTP connect` | Generate OIDC GitHub Actions workflow |
| `weHateTP type` | Typewriter effect |
| `weHateTP warn` | Big colored 3-2-1 countdown |
| `weHateTP detect` | Auto-detect Git context |
| `weHateTP init` | Write weHateTP.yml |

## TypeBot inject

```bash
weHateTP inject
```

Paste the script into the browser console (F12).  
Red **TypeBot** box top-right, **By DarkFox** below, visible 5 seconds.

## GitHub Actions OIDC

Workflow at `.github/workflows/oidc-deploy.yml`.  
Set your AWS role ARN in `weHateTP.yml` → `oidc.role_arn`.

Repo: https://github.com/SlabyLol/weHateTP
