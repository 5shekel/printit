"""Logging configuration for the Sticker Factory application."""

import logging
import logging.handlers
import os
from pathlib import Path


# ANSI color codes for terminal output
class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels in terminal output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'            # Reset to default
    BOLD = '\033[1m'             # Bold
    
    def format(self, record):
        # Add color to the level name
        levelname = record.levelname
        color = self.COLORS.get(levelname, self.RESET)
        record.levelname = f"{color}{self.BOLD}{levelname}{self.RESET}"
        return super().format(record)


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

colored_formatter = ColoredFormatter(
    "%(levelname)s - %(message)s"
)

# Console handler (INFO level and above) with colors
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(colored_formatter)
logger.addHandler(console_handler)

# File handler (DEBUG level and above) - rotating file (no colors)
log_file = logs_dir / "sticker_factory.log"
file_handler = logging.handlers.RotatingFileHandler(
    log_file,
    maxBytes=10485760,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.WARNING)
file_handler.setFormatter(detailed_formatter)
# logger.addHandler(file_handler)

# Prevent propagation to root logger
logger.propagate = False

# Convenience function to get the logger
def get_logger(module_name=None):
    """Get the configured logger, optionally with module name."""
    if module_name:
        return logging.getLogger(f"sticker_factory.{module_name}")
    return logger
