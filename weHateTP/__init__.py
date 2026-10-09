from .typewriter import Typewriter, typewrite
from .warning import countdown_warning
from .git_detect import detect_git_context
from .config import load_config, save_example_config
from .inject import get_inject_script, get_bookmarklet

__version__ = "1.3.0"
__all__ = [
    "Typewriter",
    "typewrite",
    "countdown_warning",
    "detect_git_context",
    "load_config",
    "save_example_config",
    "get_inject_script",
    "get_bookmarklet",
    "__version__",
]
