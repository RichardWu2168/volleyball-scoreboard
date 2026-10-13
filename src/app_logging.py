import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_log_directory():
    # Return the directory used to store application logs.

    if sys.platform == "win32":
        app_data = os.getenv("LOCALAPPDATA")

        if app_data:
            log_directory = (
                Path(app_data)
                / "VolleyballScoreboard"
                / "logs"
            )
        else:
            log_directory = Path.home() / "VolleyballScoreboard" / "logs"
    else:
        log_directory = (
            Path.home()
            / ".local"
            / "share"
            / "volleyball-scoreboard"
            / "logs"
        )

    log_directory.mkdir(parents=True, exist_ok=True)

    return log_directory


def setup_logging():
    # Configure application logging.

    log_file = get_log_directory() / "volleyball_scoreboard.log"

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | "
        "%(name)s | %(message)s"
    )

    file_handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler],
        force=True,
    )

    logging.info("Logging initialized.")
    logging.info("Log file: %s", log_file)
