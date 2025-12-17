"""Logging configuration for the Sticker Factory application."""

import logging
import logging.handlers
import os
from pathlib import Path

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).parent / "logs"
logs_dir.mkdir(exist_ok=True)

# Get or create logger
logger = logging.getLogger("sticker_factory")
logger.setLevel(logging.DEBUG)

# Remove any existing handlers to avoid duplicates
logger.handlers = []

# Create formatters
detailed_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

simple_formatter = logging.Formatter(
    "%(levelname)s - %(message)s"
)

# Console handler (INFO level and above)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(simple_formatter)
logger.addHandler(console_handler)

# File handler (DEBUG level and above) - rotating file
log_file = logs_dir / "sticker_factory.log"
file_handler = logging.handlers.RotatingFileHandler(
    log_file,
    maxBytes=10485760,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(detailed_formatter)
logger.addHandler(file_handler)

# Prevent propagation to root logger
logger.propagate = False

# Convenience function to get the logger
def get_logger(module_name=None):
    """Get the configured logger, optionally with module name."""
    if module_name:
        return logging.getLogger(f"sticker_factory.{module_name}")
    return logger
