from __future__ import annotations

import sys
import time

from .typewriter import Color, c, Typewriter

BIG_DIGITS = {
    "3": [
        " ███████ ",
        "      ██ ",
        " ███████ ",
        "      ██ ",
        " ███████ ",
    ],
    "2": [
        " ███████ ",
        "      ██ ",
        " ███████ ",
        " ██      ",
        " ███████ ",
    ],
    "1": [
        "    ██   ",
        "  ████   ",
        "    ██   ",
        "    ██   ",
        "  ██████ ",
    ],
    "0": [
        " ███████ ",
        " ██   ██ ",
        " ██   ██ ",
        " ██   ██ ",
        " ███████ ",
    ],
}


def _print_big(digit: str, color_code: str) -> None:
    lines = BIG_DIGITS.get(digit, ["?"])
    for line in lines:
        print(c(line, color_code, Color.BOLD))
    sys.stdout.flush()


def countdown_warning(
    message: str = "CRITICAL ACTION AHEAD",
    seconds: int = 3,
    final_message: str = "GO!",
) -> None:
    print()
    print(c("=" * 50, Color.RED, Color.BOLD))
    print(c(f"  ⚠  WARNING  ⚠  {message}", Color.RED, Color.BOLD, Color.BG_BLACK))
    print(c("=" * 50, Color.RED, Color.BOLD))
    print()
    colors = [Color.RED, Color.YELLOW, Color.MAGENTA]
    for i in range(seconds, 0, -1):
        digit = str(i)
        color = colors[(seconds - i) % len(colors)]
        _print_big(digit, color)
        print()
        time.sleep(0.9)
    print(c("  ██████╗  ██████╗ ██╗", Color.GREEN, Color.BOLD))
    print(c(" ██╔════╝ ██╔═══██╗██║", Color.GREEN, Color.BOLD))
    print(c(" ██║  ███╗██║   ██║██║", Color.GREEN, Color.BOLD))
    print(c(" ██║   ██║██║   ██║╚═╝", Color.GREEN, Color.BOLD))
    print(c(" ╚██████╔╝╚██████╔╝██╗", Color.GREEN, Color.BOLD))
    print(c("  ╚═════╝  ╚═════╝ ╚═╝", Color.GREEN, Color.BOLD))
    print()
    if final_message:
        tw = Typewriter(cps=25, variance=0.2)
        tw.write(c(final_message, Color.GREEN, Color.BOLD), end="\n")
    print()
