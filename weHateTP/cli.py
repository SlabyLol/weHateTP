from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import generate_oidc_workflow, load_config, save_example_config
from .git_detect import detect_git_context
from .inject import get_inject_script
from .typewriter import Color, Typewriter, c
from .warning import countdown_warning


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
        cps=args.speed or tw_cfg.get("cps", 12.0),
        variance=args.variance if args.variance is not None else tw_cfg.get("variance", 0.35),
    ).write(text, end="" if args.no_newline else "\n")
    return 0


def cmd_warn(args):
    cfg = load_config(args.config)
    w = cfg.get("warning", {})
    countdown_warning(
        message=args.message or w.get("message", "CRITICAL ACTION AHEAD"),
        seconds=args.seconds or w.get("seconds", 3),
        final_message=args.final or w.get("final_message", "Proceeding..."),
    )
    return 0


def cmd_detect(args):
    ctx = detect_git_context(args.path)
    print(c("── Git Auto-Detection ──", Color.CYAN, Color.BOLD))
    print(ctx.summary())
    return 0


def cmd_init(args):
    print(c(f"Config written: {save_example_config(args.output)}", Color.GREEN, Color.BOLD))
    return 0


def cmd_connect(args):
    cfg = load_config(args.config)
    ctx = detect_git_context()
    print(c("── GitHub Actions / OIDC ──", Color.CYAN, Color.BOLD))
    print(ctx.summary())
    owner = ctx.owner or "SlabyLol"
    repo = ctx.repo or "weHateTP"
    branch = ctx.branch or "main"
    w = cfg.get("warning", {})
    countdown_warning(message=w.get("message", "GENERATING OIDC WORKFLOW"), seconds=w.get("seconds", 3), final_message="Generating…")
    workflow = generate_oidc_workflow(cfg, owner=owner, repo=repo, branch=branch)
    if args.dry_run:
        print(workflow)
    else:
        out = Path(".github") / "workflows"
        out.mkdir(parents=True, exist_ok=True)
        (out / "oidc-deploy.yml").write_text(workflow, encoding="utf-8")
        print(c(f"Workflow written: {out / 'oidc-deploy.yml'}", Color.GREEN, Color.BOLD))
    return 0


def cmd_inject(args):
    cfg = load_config(args.config)
    w = cfg.get("warning", {})
    print(c("── TypeBot Inject ──", Color.RED, Color.BOLD))
    print(c("  TypeBot  |  By DarkFox  |  5s overlay", Color.RED))
    while True:
        try:
            answer = input(c("Inject into selected page? [y/n] ", Color.YELLOW, Color.BOLD)).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(c("\nAborted.", Color.RED))
            return 1
        if answer in ("y", "yes"):
            break
        if answer in ("n", "no"):
            print(c("Asking again…", Color.DIM))
            continue
        print(c("y or n.", Color.RED))
    countdown_warning(message=w.get("message", "PREPARING INJECT"), seconds=w.get("seconds", 3), final_message="Ready.")
    print()
    print(get_inject_script())
    print()
    return 0


def cmd_start(args):
    cfg = load_config(args.config)
    w = cfg.get("warning", {})
    ctx = detect_git_context()
    print(c("══════════════════════════════════════", Color.RED, Color.BOLD))
    print(c("          TypeBot  ·  weHateTP", Color.RED, Color.BOLD))
    print(c("            By DarkFox", Color.DIM))
    print(c("══════════════════════════════════════", Color.RED, Color.BOLD))
    print(ctx.summary())
    print()
    while True:
        try:
            answer = input(c("Inject TypeBot into selected page? [y/n] ", Color.YELLOW, Color.BOLD)).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(c("\nAborted.", Color.RED))
            return 1
        if answer in ("y", "yes"):
            break
        if answer in ("n", "no"):
            print(c("Asking again…", Color.DIM))
            continue
        print(c("y or n.", Color.RED))
    countdown_warning(message=w.get("message", "STARTING TypeBot"), seconds=w.get("seconds", 3), final_message="Starting…")
    script = get_inject_script()
    Path("typebot-inject.js").write_text(script + "\n", encoding="utf-8")
    print(c("Inject script saved: typebot-inject.js", Color.GREEN))
    print()
    print(script)
    print()
    owner = ctx.owner or "SlabyLol"
    repo = ctx.repo or "weHateTP"
    branch = ctx.branch or "main"
    workflow = generate_oidc_workflow(cfg, owner=owner, repo=repo, branch=branch)
    out = Path(".github") / "workflows"
    out.mkdir(parents=True, exist_ok=True)
    (out / "oidc-deploy.yml").write_text(workflow, encoding="utf-8")
    print(c(f"GitHub Actions workflow: {out / 'oidc-deploy.yml'}", Color.GREEN))
    if not Path("weHateTP.yml").exists():
        save_example_config("weHateTP.yml")
        print(c("Config: weHateTP.yml", Color.GREEN))
    print(c("Done.", Color.CYAN, Color.BOLD))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="weHateTP", description="TypeBot + GitHub Actions OIDC + inject")
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
    p = sub.add_parser("detect")
    p.add_argument("path", nargs="?", default=None)
    p.set_defaults(func=cmd_detect)
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
