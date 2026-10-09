from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import (
    generate_oidc_deploy_workflow,
    generate_pypi_oidc_workflow,
    load_config,
    save_example_config,
)
from .inject import get_inject_script
from .typewriter import Color, Typewriter, c
from .warning import countdown_warning


def _ask_yn(prompt: str) -> bool:
    while True:
        try:
            answer = input(c(prompt, Color.YELLOW, Color.BOLD)).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            print(c("Aborted.", Color.RED))
            raise SystemExit(1)
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print(c("Please answer y or n.", Color.RED))


def cmd_type(args):
    cfg = load_config(args.config)
    tw_cfg = cfg.get("typewriter", {})
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    elif args.text is not None:
        text = args.text
    else:
        text = sys.stdin.read()
    if not text:
        print("No text provided.", file=sys.stderr)
        return 1
    Typewriter(
        cps=args.speed or tw_cfg.get("cps", 14.0),
        variance=args.variance if args.variance is not None else tw_cfg.get("variance", 0.4),
    ).write(text, end="" if args.no_newline else "\n")
    return 0


def cmd_warn(args):
    cfg = load_config(args.config)
    w = cfg.get("warning", {})
    countdown_warning(
        message=args.message or w.get("message", "TypeBot ACTIVE – By DarkFox"),
        seconds=args.seconds or w.get("seconds", 3),
        final_message=args.final or w.get("final_message", "Ready."),
    )
    return 0


def cmd_init(args):
    path = save_example_config(args.output)
    print(c(f"Config written: {path}", Color.GREEN, Color.BOLD))
    return 0


def cmd_connect(args):
    cfg = load_config(args.config)
    w = cfg.get("warning", {})
    countdown_warning(
        message=w.get("message", "GENERATING PYPI + OIDC WORKFLOWS"),
        seconds=w.get("seconds", 3),
        final_message="Generating…",
    )
    out = Path(".github") / "workflows"
    out.mkdir(parents=True, exist_ok=True)
    pypi_wf = generate_pypi_oidc_workflow(cfg)
    deploy_wf = generate_oidc_deploy_workflow(cfg)
    if args.dry_run:
        print(pypi_wf)
        print(deploy_wf)
    else:
        (out / "publish-pypi.yml").write_text(pypi_wf, encoding="utf-8")
        (out / "oidc-deploy.yml").write_text(deploy_wf, encoding="utf-8")
        print(c(f"Wrote {out / 'publish-pypi.yml'}", Color.GREEN, Color.BOLD))
        print(c(f"Wrote {out / 'oidc-deploy.yml'}", Color.GREEN, Color.BOLD))
    print()
    print(c("PyPI Trusted Publishing:", Color.CYAN, Color.BOLD))
    print("  1. https://pypi.org/manage/account/publishing/")
    print(f"  2. Owner={cfg.get('github', {}).get('owner', 'SlabyLol')} Repo={cfg.get('github', {}).get('repo', 'weHateTP')}")
    print("     Workflow=publish-pypi.yml Environment=pypi")
    print("  3. GitHub Environment named pypi")
    print("  4. Create a Release -> publishes via OIDC")
    return 0


def cmd_inject(args):
    cfg = load_config(args.config)
    w = cfg.get("warning", {})
    print(c("-- TypeBot Inject --", Color.RED, Color.BOLD))
    while not _ask_yn("Inject into the currently selected page? [y/n] "):
        print(c("Asking again...", Color.DIM))
    countdown_warning(
        message=w.get("message", "PREPARING INJECT"),
        seconds=w.get("seconds", 3),
        final_message="Script ready.",
    )
    print()
    print(get_inject_script(cfg))
    print()
    return 0


def cmd_start(args):
    cfg = load_config(args.config)
    w = cfg.get("warning", {})
    gh = cfg.get("github", {})
    pypi = cfg.get("pypi", {})
    print()
    print(c("========================================", Color.RED, Color.BOLD))
    print(c("       TypeBot  ·  weHateTP  v" + __version__, Color.RED, Color.BOLD))
    print(c("            By DarkFox", Color.DIM))
    print(c("========================================", Color.RED, Color.BOLD))
    print()
    Typewriter(cps=22, variance=0.25).write(c("Connecting to weHateTP...", Color.CYAN))
    print(c(f"  package  : {pypi.get('package_name', 'weHateTP')}", Color.GREEN))
    print(c(f"  github   : {gh.get('owner', 'SlabyLol')}/{gh.get('repo', 'weHateTP')}", Color.GREEN))
    print(c(f"  pypi oidc: {pypi.get('oidc', True)}", Color.GREEN))
    print(c(f"  version  : {__version__}", Color.GREEN))
    print()
    if not Path("weHateTP.yml").exists():
        save_example_config("weHateTP.yml")
        print(c("Created weHateTP.yml", Color.GREEN))
        cfg = load_config("weHateTP.yml")
        w = cfg.get("warning", {})
    else:
        print(c("Loaded weHateTP.yml", Color.GREEN))
    print()
    while not _ask_yn("Inject TypeBot into the selected page? [y/n] "):
        print(c("Asking again...", Color.DIM))
        print()
    countdown_warning(
        message=w.get("message", "TypeBot ACTIVE – By DarkFox"),
        seconds=w.get("seconds", 3),
        final_message=w.get("final_message", "Ready."),
    )
    script = get_inject_script(cfg)
    Path("typebot-inject.js").write_text(script + "\n", encoding="utf-8")
    print(c("Inject script -> typebot-inject.js", Color.GREEN, Color.BOLD))
    print()
    print(script)
    print()
    out = Path(".github") / "workflows"
    out.mkdir(parents=True, exist_ok=True)
    (out / "publish-pypi.yml").write_text(generate_pypi_oidc_workflow(cfg), encoding="utf-8")
    (out / "oidc-deploy.yml").write_text(generate_oidc_deploy_workflow(cfg), encoding="utf-8")
    print(c(f"PyPI OIDC  -> {out / 'publish-pypi.yml'}", Color.GREEN, Color.BOLD))
    print(c(f"Deploy OIDC -> {out / 'oidc-deploy.yml'}", Color.GREEN, Color.BOLD))
    print()
    print(c("-- weHateTP status --", Color.CYAN, Color.BOLD))
    print(c("  inject     : yes", Color.GREEN))
    print(c("  config     : weHateTP.yml", Color.GREEN))
    print(c("  pypi oidc  : publish-pypi.yml", Color.GREEN))
    print()
    print(c("PyPI Trusted Publishing:", Color.CYAN, Color.BOLD))
    print("  1. https://pypi.org/manage/account/publishing/")
    print(f"  2. Owner={gh.get('owner','SlabyLol')} Repo={gh.get('repo','weHateTP')}")
    print("     Workflow=publish-pypi.yml Environment=pypi")
    print("  3. GitHub Environment pypi")
    print("  4. Create a Release -> publishes via OIDC")
    print()
    Typewriter(cps=18, variance=0.3).write(c("weHateTP is live. TypeBot standing by.", Color.GREEN, Color.BOLD))
    print()
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="weHateTP", description="TypeBot · weHateTP – inject, typewriter, PyPI OIDC")
    parser.add_argument("--version", action="version", version=f"weHateTP {__version__}")
    parser.add_argument("-c", "--config", metavar="PATH")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("type")
    p.add_argument("text", nargs="?", default=None)
    p.add_argument("-f", "--file")
    p.add_argument("-s", "--speed", type=float)
    p.add_argument("-v", "--variance", type=float)
    p.add_argument("--no-newline", action="store_true")
    p.set_defaults(func=cmd_type)
    p = sub.add_parser("warn")
    p.add_argument("-m", "--message")
    p.add_argument("-s", "--seconds", type=int)
    p.add_argument("--final")
    p.set_defaults(func=cmd_warn)
    p = sub.add_parser("init")
    p.add_argument("-o", "--output", default="weHateTP.yml")
    p.set_defaults(func=cmd_init)
    p = sub.add_parser("connect")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_connect)
    p = sub.add_parser("inject")
    p.set_defaults(func=cmd_inject)
    p = sub.add_parser("start")
    p.set_defaults(func=cmd_start)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
