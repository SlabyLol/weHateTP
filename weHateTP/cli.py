from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from . import __version__
from .config import generate_pypi_oidc_workflow, load_config, save_example_config
from .inject import get_inject_script
from .typewriter import Color, Typewriter, c
from .warning import countdown_warning


def _copy_clipboard(text: str) -> bool:
    try:
        if sys.platform == "win32":
            p = subprocess.run(
                ["clip"],
                input=text.encode("utf-16-le"),
                check=False,
                capture_output=True,
            )
            return p.returncode == 0
        if sys.platform == "darwin":
            p = subprocess.run(["pbcopy"], input=text.encode(), check=False)
            return p.returncode == 0
        p = subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=text.encode(),
            check=False,
            capture_output=True,
        )
        if p.returncode == 0:
            return True
        p = subprocess.run(
            ["xsel", "--clipboard", "--input"],
            input=text.encode(),
            check=False,
            capture_output=True,
        )
        return p.returncode == 0
    except OSError:
        return False


def _ask_yn(prompt: str, auto_yes: bool = False) -> bool:
    if auto_yes:
        print(c(prompt + "y", Color.YELLOW, Color.BOLD))
        return True
    while True:
        try:
            answer = input(c(prompt, Color.YELLOW, Color.BOLD)).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            print(c("Aborted.", Color.RED))
            raise SystemExit(1)
        if answer in ("y", "yes", ""):
            return True
        if answer in ("n", "no"):
            return False
        print(c("Please answer y or n.", Color.RED))


def _print_inject(script: str) -> None:
    path = Path("typebot-inject.js")
    path.write_text(script + "\n", encoding="utf-8")
    copied = _copy_clipboard(script)
    print()
    print(c("=" * 56, Color.RED))
    print(c("  TypeBot inject script", Color.RED, Color.BOLD))
    print(c("=" * 56, Color.RED))
    print()
    print(script)
    print()
    print(c(f"Saved: {path.resolve()}", Color.GREEN))
    if copied:
        print(c("Copied to clipboard – paste in browser (Ctrl+V)", Color.GREEN, Color.BOLD))
    print()
    print(c("How to inject:", Color.CYAN, Color.BOLD))
    print("  1. Open the website tab you want")
    print("  2. Press F12  →  Console")
    print("  3. Paste (Ctrl+V) and press Enter")
    print("  4. Red TypeBot box appears top-right for 5 seconds")
    print()


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
        seconds=args.seconds if args.seconds is not None else w.get("seconds", 3),
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
    if not args.yes:
        countdown_warning(
            message=w.get("message", "GENERATING PYPI OIDC WORKFLOW"),
            seconds=w.get("seconds", 3),
            final_message="Generating…",
        )
    out = Path(".github") / "workflows"
    out.mkdir(parents=True, exist_ok=True)
    pypi_wf = generate_pypi_oidc_workflow(cfg)
    if args.dry_run:
        print(pypi_wf)
    else:
        (out / "publish-pypi.yml").write_text(pypi_wf, encoding="utf-8")
        print(c(f"Wrote {out / 'publish-pypi.yml'}", Color.GREEN, Color.BOLD))
    print()
    print(c("PyPI Trusted Publishing:", Color.CYAN, Color.BOLD))
    print("  https://pypi.org/manage/account/publishing/")
    print("  Owner=SlabyLol  Repo=weHateTP  Workflow=publish-pypi.yml")
    return 0


def cmd_inject(args):
    cfg = load_config(args.config)
    w = cfg.get("warning", {})
    print()
    print(c("── TypeBot Inject ──", Color.RED, Color.BOLD))
    print(c("  TypeBot  |  By DarkFox  |  top-right 5s", Color.RED))
    print()
    if not args.yes:
        while not _ask_yn("Prepare inject script for this PC? [y/n] "):
            print(c("Asking again…", Color.DIM))
    if not args.no_warn:
        countdown_warning(
            message=w.get("message", "PREPARING INJECT"),
            seconds=0 if args.yes else w.get("seconds", 3),
            final_message="Script ready.",
        )
    script = get_inject_script(cfg)
    _print_inject(script)
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
    try:
        Typewriter(cps=28, variance=0.2).write(c("Connecting to weHateTP…", Color.CYAN))
    except Exception:
        print(c("Connecting to weHateTP…", Color.CYAN))
    print(c(f"  package  : {pypi.get('package_name', 'weHateTP')}", Color.GREEN))
    print(c(f"  github   : {gh.get('owner', 'SlabyLol')}/{gh.get('repo', 'weHateTP')}", Color.GREEN))
    print(c(f"  version  : {__version__}", Color.GREEN))
    print()
    if not Path("weHateTP.yml").exists() and not Path("weHateTP.json").exists():
        p = save_example_config()
        print(c(f"Created config: {p.name}", Color.GREEN))
        cfg = load_config(str(p))
        w = cfg.get("warning", {})
    else:
        print(c("Loaded config", Color.GREEN))
    print()
    if not args.yes:
        while not _ask_yn("Prepare TypeBot inject script? [y/n] "):
            print(c("Asking again…", Color.DIM))
            print()
    if not args.no_warn:
        countdown_warning(
            message=w.get("message", "TypeBot ACTIVE – By DarkFox"),
            seconds=0 if args.yes else w.get("seconds", 3),
            final_message=w.get("final_message", "Ready."),
        )
    script = get_inject_script(cfg)
    _print_inject(script)
    out = Path(".github") / "workflows"
    out.mkdir(parents=True, exist_ok=True)
    wf = out / "publish-pypi.yml"
    wf.write_text(generate_pypi_oidc_workflow(cfg), encoding="utf-8")
    print(c(f"PyPI workflow: {wf}", Color.GREEN))
    print()
    print(c("weHateTP is live. TypeBot standing by.", Color.GREEN, Color.BOLD))
    print()
    return 0


def main(argv=None):
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-c", "--config", metavar="PATH")
    common.add_argument("-y", "--yes", action="store_true", help="Skip y/n prompts")
    common.add_argument("--no-warn", action="store_true", help="Skip 3-2-1 countdown")
    parser = argparse.ArgumentParser(
        prog="weHateTP",
        description="TypeBot · weHateTP – inject, typewriter, PyPI OIDC",
        parents=[common],
    )
    parser.add_argument("--version", action="version", version=f"weHateTP {__version__}")
    sub = parser.add_subparsers(dest="command")
    p = sub.add_parser("type", help="Typewriter effect", parents=[common])
    p.add_argument("text", nargs="?", default=None)
    p.add_argument("-f", "--file")
    p.add_argument("-s", "--speed", type=float)
    p.add_argument("-v", "--variance", type=float)
    p.add_argument("--no-newline", action="store_true")
    p.set_defaults(func=cmd_type)
    p = sub.add_parser("warn", help="3-2-1 countdown", parents=[common])
    p.add_argument("-m", "--message")
    p.add_argument("-s", "--seconds", type=int)
    p.add_argument("--final")
    p.set_defaults(func=cmd_warn)
    p = sub.add_parser("init", help="Write config file", parents=[common])
    p.add_argument("-o", "--output", default=None)
    p.set_defaults(func=cmd_init)
    p = sub.add_parser("connect", help="Generate PyPI OIDC workflow", parents=[common])
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_connect)
    p = sub.add_parser("inject", help="TypeBot inject script + clipboard", parents=[common])
    p.set_defaults(func=cmd_inject)
    p = sub.add_parser("start", help="Full start: inject + config", parents=[common])
    p.set_defaults(func=cmd_start)
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        if not hasattr(args, "yes"):
            args.yes = True
        if not hasattr(args, "no_warn"):
            args.no_warn = False
        return cmd_start(args)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
