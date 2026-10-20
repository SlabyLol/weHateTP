from __future__ import annotations

import argparse
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

from . import __version__
from .config import generate_pypi_oidc_workflow, load_config, save_example_config
from .inject import get_inject_script
from .server import HUB, start_server, stream_text
from .typewriter import Color, Typewriter, c
from .warning import countdown_warning


def _copy_clipboard(text: str) -> bool:
    try:
        if sys.platform == "win32":
            p = subprocess.run(["clip"], input=text.encode("utf-16-le"), check=False, capture_output=True)
            return p.returncode == 0
        if sys.platform == "darwin":
            return subprocess.run(["pbcopy"], input=text.encode(), check=False).returncode == 0
        p = subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode(), check=False, capture_output=True)
        if p.returncode == 0:
            return True
        return subprocess.run(["xsel", "--clipboard", "--input"], input=text.encode(), check=False, capture_output=True).returncode == 0
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


def _try_selenium_inject(url: str, port: int) -> bool:
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    except ImportError:
        return False
    try:
        opts = Options()
        driver = webdriver.Chrome(options=opts)
        driver.get(url)
        driver.execute_script(
            f"var s=document.createElement('script');s.src='http://127.0.0.1:{port}/inject.js';document.documentElement.appendChild(s);"
        )
        print(c("[OK] Selenium injected TypeBot", Color.GREEN, Color.BOLD))
        return True
    except Exception as e:
        print(c(f"[..] Selenium: {e}", Color.DIM))
        return False


def cmd_type(args):
    cfg = load_config(args.config)
    tw = cfg.get("typewriter", {})
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    elif args.text is not None:
        text = args.text
    else:
        text = sys.stdin.read()
    if not text:
        print("No text.", file=sys.stderr)
        return 1
    Typewriter(cps=args.speed or tw.get("cps", 14.0), variance=args.variance if args.variance is not None else tw.get("variance", 0.4)).write(text, end="" if args.no_newline else "\n")
    return 0


def cmd_warn(args):
    cfg = load_config(args.config)
    w = cfg.get("warning", {})
    countdown_warning(message=args.message or w.get("message", "TypeBot ACTIVE – By DarkFox"), seconds=args.seconds if args.seconds is not None else w.get("seconds", 3), final_message=args.final or w.get("final_message", "Ready."))
    return 0


def cmd_init(args):
    print(c(f"Config: {save_example_config(args.output)}", Color.GREEN, Color.BOLD))
    return 0


def cmd_connect(args):
    cfg = load_config(args.config)
    out = Path(".github") / "workflows"
    out.mkdir(parents=True, exist_ok=True)
    wf = generate_pypi_oidc_workflow(cfg)
    if args.dry_run:
        print(wf)
    else:
        (out / "publish-pypi.yml").write_text(wf, encoding="utf-8")
        print(c(f"Wrote {out / 'publish-pypi.yml'}", Color.GREEN))
    return 0


def cmd_inject(args):
    cfg = load_config(args.config)
    print(c("── TypeBot Inject ──", Color.RED, Color.BOLD))
    if not args.yes:
        while not _ask_yn("Prepare inject script? [y/n] "):
            print(c("Asking again…", Color.DIM))
    script = get_inject_script(cfg)
    Path("typebot-inject.js").write_text(script + "\n", encoding="utf-8")
    _copy_clipboard(script)
    print(script)
    return 0


def cmd_live(args):
    cfg = load_config(args.config)
    tw = cfg.get("typewriter", {})
    port = args.port or 8765
    cps = args.speed or tw.get("cps", 18.0)
    print()
    print(c("========================================", Color.RED, Color.BOLD))
    print(c("   TypeBot LIVE  ·  weHateTP  v" + __version__, Color.RED, Color.BOLD))
    print(c("            By DarkFox", Color.DIM))
    print(c("========================================", Color.RED, Color.BOLD))
    print()
    try:
        server = start_server(port)
    except OSError as e:
        print(c(f"Port {port} busy: {e} – try --port 8766", Color.RED))
        return 1
    demo_url = f"http://127.0.0.1:{port}/demo"
    print(c(f"[OK] Server http://127.0.0.1:{port}", Color.GREEN, Color.BOLD))
    print(c(f"     Demo  {demo_url}", Color.GREEN))
    print()
    injected = False
    if args.selenium or args.url:
        injected = _try_selenium_inject(args.url or demo_url, port)
    if not injected:
        print(c("[..] Opening browser…", Color.CYAN))
        try:
            webbrowser.open(demo_url)
        except Exception:
            print(c(f"     Open: {demo_url}", Color.YELLOW))
    live_js = f'(function(){{var s=document.createElement("script");s.src="http://127.0.0.1:{port}/inject.js";document.documentElement.appendChild(s);}})();'
    _copy_clipboard(live_js)
    print(c("Clipboard has one-line inject for any tab (F12→paste)", Color.DIM))
    print()
    print(c("Waiting for browser…", Color.CYAN))
    for _ in range(40):
        if HUB.clients > 0:
            break
        time.sleep(0.25)
    if HUB.clients:
        print(c(f"[OK] clients={HUB.clients}", Color.GREEN, Color.BOLD))
    else:
        print(c("[..] no client yet – open demo page", Color.YELLOW))
    print()
    print(c("LIVE – type below, text appears in the browser overlay", Color.CYAN, Color.BOLD))
    print(c("  /clear  /status  /demo  /quit", Color.DIM))
    print()
    intro = args.text or "TypeBot LIVE online. By DarkFox."
    print(c(">>>", Color.MAGENTA), intro)
    Typewriter(cps=cps, variance=0.25).write(intro)
    stream_text(intro, cps=cps)
    print()
    try:
        while True:
            try:
                line = input(c("typebot> ", Color.RED, Color.BOLD))
            except EOFError:
                break
            line = line.rstrip("\n")
            if not line:
                continue
            if line in ("/quit", "/exit", "/q"):
                HUB.publish("status", {"text": "stopped"})
                print(c("Bye.", Color.GREEN))
                break
            if line == "/clear":
                HUB.publish("clear", {})
                continue
            if line == "/status":
                print(c(f"clients={HUB.clients} status={HUB.status}", Color.CYAN))
                continue
            if line == "/demo":
                webbrowser.open(demo_url)
                continue
            print(c(">>>", Color.MAGENTA), end=" ")
            Typewriter(cps=cps, variance=0.25).write(line)
            stream_text(line, cps=cps)
            print()
    except KeyboardInterrupt:
        print()
        print(c("Stopped.", Color.YELLOW))
        HUB.publish("status", {"text": "stopped"})
    try:
        server.shutdown()
    except Exception:
        pass
    return 0


def cmd_start(args):
    return cmd_live(args)


def main(argv=None):
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-c", "--config", metavar="PATH")
    common.add_argument("-y", "--yes", action="store_true")
    common.add_argument("--no-warn", action="store_true")
    parser = argparse.ArgumentParser(prog="weHateTP", description="TypeBot LIVE · weHateTP", parents=[common])
    parser.add_argument("--version", action="version", version=f"weHateTP {__version__}")
    sub = parser.add_subparsers(dest="command")
    p = sub.add_parser("type", parents=[common])
    p.add_argument("text", nargs="?", default=None)
    p.add_argument("-f", "--file")
    p.add_argument("-s", "--speed", type=float)
    p.add_argument("-v", "--variance", type=float)
    p.add_argument("--no-newline", action="store_true")
    p.set_defaults(func=cmd_type)
    p = sub.add_parser("warn", parents=[common])
    p.add_argument("-m", "--message")
    p.add_argument("-s", "--seconds", type=int)
    p.add_argument("--final")
    p.set_defaults(func=cmd_warn)
    p = sub.add_parser("init", parents=[common])
    p.add_argument("-o", "--output", default=None)
    p.set_defaults(func=cmd_init)
    p = sub.add_parser("connect", parents=[common])
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_connect)
    p = sub.add_parser("inject", parents=[common])
    p.set_defaults(func=cmd_inject)
    p = sub.add_parser("live", parents=[common])
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--url", default=None)
    p.add_argument("--selenium", action="store_true")
    p.add_argument("-s", "--speed", type=float)
    p.add_argument("-t", "--text", default=None)
    p.set_defaults(func=cmd_live)
    p = sub.add_parser("start", parents=[common])
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--url", default=None)
    p.add_argument("--selenium", action="store_true")
    p.add_argument("-s", "--speed", type=float)
    p.add_argument("-t", "--text", default=None)
    p.set_defaults(func=cmd_start)
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        args.port = 8765
        args.url = None
        args.selenium = False
        args.text = None
        args.speed = None
        return cmd_live(args)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
