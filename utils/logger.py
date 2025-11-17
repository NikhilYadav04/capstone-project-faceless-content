import logging
import sys
from rich.logging import RichHandler
from utils.env import load_env

# --- Configuration ---

env = load_env()
LOG_LEVEL = env.get("LOG_LEVEL", "INFO").upper()

# --- Logger Setup ---

# We configure the root logger once when this module is imported.
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(message)s",  # RichHandler handles the formatting
    datefmt="[%X]",
    handlers=[
        RichHandler(
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            show_path=True,
            markup=True,
        )
    ],
)


def get_logger(name: str) -> logging.Logger:
    """
    Retrieves a logger instance configured with RichHandler.

    Args:
        name: The name for the logger (typically __name__).

    Returns:
        A logging.Logger instance.
    """
    # All loggers will inherit the root config,
    return logging.getLogger(name)
