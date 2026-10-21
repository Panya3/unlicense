import logging

import lief


def setup_logger(logger: logging.Logger, verbose: bool) -> None:
    lief.logging.disable()
    log_level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(log_level)

    # Create a console handler with standard formatting without ANSI escape codes
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(
        logging.Formatter("%(levelname)s - %(message)s"))
    # ponytail: plain text logger; upgrade with colorama or curses if user explicitly requests colored output
    logger.addHandler(stream_handler)
