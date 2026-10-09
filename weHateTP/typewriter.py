from __future__ import annotations

import random
import sys
import time
from typing import Iterable, Optional, TextIO


class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BG_RED = "\033[41m"
    BG_YELLOW = "\033[43m"
    BG_BLACK = "\033[40m"

    @staticmethod
    def enabled() -> bool:
        return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def c(text: str, *codes: str) -> str:
    if not Color.enabled():
        return text
    return "".join(codes) + text + Color.RESET


class Typewriter:
    def __init__(
        self,
        cps: float = 12.0,
        variance: float = 0.35,
        newline_pause: float = 0.25,
        punctuation_pause: float = 0.18,
        stream: Optional[TextIO] = None,
    ) -> None:
        if cps <= 0:
            raise ValueError("cps must be > 0")
        if not 0.0 <= variance <= 1.0:
            raise ValueError("variance must be between 0.0 and 1.0")
        self.cps = cps
        self.variance = variance
        self.newline_pause = newline_pause
        self.punctuation_pause = punctuation_pause
        self.stream = stream or sys.stdout

    def _delay(self, char: str) -> float:
        base = 1.0 / self.cps
        jitter = base * self.variance * (random.random() * 2 - 1)
        delay = max(0.01, base + jitter)
        if char in "\n":
            delay += self.newline_pause
        elif char in ".!?;:":
            delay += self.punctuation_pause
        return delay

    def write(self, text: str, end: str = "\n", flush: bool = True) -> None:
        for char in text:
            self.stream.write(char)
            if flush:
                self.stream.flush()
            time.sleep(self._delay(char))
        if end:
            self.stream.write(end)
            if flush:
                self.stream.flush()

    def write_lines(self, lines: Iterable[str], end: str = "\n") -> None:
        for line in lines:
            self.write(line, end=end)

    def __call__(self, text: str, end: str = "\n") -> None:
        self.write(text, end=end)


def typewrite(
    text: str,
    cps: float = 12.0,
    variance: float = 0.35,
    newline_pause: float = 0.25,
    punctuation_pause: float = 0.18,
    end: str = "\n",
    stream: Optional[TextIO] = None,
) -> None:
    tw = Typewriter(
        cps=cps,
        variance=variance,
        newline_pause=newline_pause,
        punctuation_pause=punctuation_pause,
        stream=stream,
    )
    tw.write(text, end=end)
