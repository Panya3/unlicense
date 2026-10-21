import logging
import os
import sys
from typing import Any

import lief


def _enable_windows_vt() -> bool:
    if os.name != "nt":
        return True
    try:
        import ctypes
        from ctypes import wintypes
        kernel32 = ctypes.windll.kernel32

        # Enable VT mode on CONOUT$ (console screen buffer)
        generic_read_write = 0xC0000000
        file_share_read_write = 3
        open_existing = 3
        h_conout = kernel32.CreateFileW("CONOUT$", generic_read_write,
                                        file_share_read_write, None,
                                        open_existing, 0, None)
        if h_conout and h_conout != wintypes.HANDLE(-1).value:
            mode = wintypes.DWORD()
            if kernel32.GetConsoleMode(h_conout, ctypes.byref(mode)):
                kernel32.SetConsoleMode(h_conout, mode.value | 0x0004)
            kernel32.CloseHandle(h_conout)

        # Also enable on standard output and error handles
        for handle_id in (-11, -12):
            h = kernel32.GetStdHandle(handle_id)
            if h and h != wintypes.HANDLE(-1).value:
                mode = wintypes.DWORD()
                if kernel32.GetConsoleMode(h, ctypes.byref(mode)):
                    kernel32.SetConsoleMode(h, mode.value | 0x0004)
        return True
    except Exception:
        return False


def should_use_color(stream: Any = None) -> bool:
    if stream is None:
        stream = sys.stderr
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        if os.name == "nt":
            _enable_windows_vt()
        return True
    is_tty = hasattr(stream, "isatty") and stream.isatty()
    if is_tty:
        if os.name == "nt":
            return _enable_windows_vt()
        return True
    if os.name == "nt" and ("WT_SESSION" in os.environ
                            or "ConEmuPID" in os.environ):
        return _enable_windows_vt()
    if "TERM" in os.environ and os.environ["TERM"] != "dumb":
        return True
    return False


class ColoredFormatter(logging.Formatter):
    """
    Standard universal console formatter with ANSI colors.
    """

    RESET = "\x1b[0m"
    LEVEL_COLORS = {
        logging.DEBUG: "\x1b[90m",  # Dim Gray
        logging.INFO: "\x1b[1;32m",  # Bold Green
        logging.WARNING: "\x1b[1;33m",  # Bold Yellow
        logging.ERROR: "\x1b[1;31m",  # Bold Red
        logging.CRITICAL: "\x1b[1;37;41m",  # Bold White on Red
    }
    SHORT_NAMES = {
        "WARNING": "WARN",
    }

    def __init__(self, use_color: bool = True) -> None:
        super().__init__("%(levelname)s - %(message)s")
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        orig_levelname = record.levelname
        disp_name = self.SHORT_NAMES.get(orig_levelname, orig_levelname)
        padded_name = f"{disp_name:<5}"
        if self.use_color:
            color = self.LEVEL_COLORS.get(record.levelno, "")
            record.levelname = f"{color}{padded_name}{self.RESET}"
        else:
            record.levelname = padded_name
        try:
            return super().format(record)
        finally:
            record.levelname = orig_levelname


def setup_logger(logger: logging.Logger, verbose: bool) -> None:
    lief.logging.disable()
    log_level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(log_level)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level)

    use_color = should_use_color(stream_handler.stream)
    stream_handler.setFormatter(ColoredFormatter(use_color=use_color))
    logger.addHandler(stream_handler)
