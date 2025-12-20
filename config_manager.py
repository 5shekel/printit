"""Centralized configuration management for the Sticker Factory app."""

import tomllib
import logging
from pathlib import Path

logger = logging.getLogger("sticker_factory.config_manager")


def load_config():
    """Load config.toml from the workspace root. Called once at app startup."""
    config_path = Path(__file__).parent / "config.toml"
    try:
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
            logger.info("Config loaded successfully from config.toml")
            return config
    except FileNotFoundError:
        logger.error(f"config.toml not found at {config_path}")
        return {}
    except Exception as e:
        logger.error(f"Error loading config.toml: {e}")
        return {}


# Load config once at module import time
CONFIG = load_config()

# Export commonly used settings
APP_CONFIG = CONFIG.get("app", {})
UI_CONFIG = CONFIG.get("ui", {})
TABS_CONFIG = CONFIG.get("tabs", {})
LOGGING_CONFIG = CONFIG.get("logging", {})

PRIVACY_MODE = APP_CONFIG.get("privacy_mode", True)
APP_TITLE = APP_CONFIG.get("title", "STICKER FACTORY")
HISTORY_LIMIT = UI_CONFIG.get("history_limit", 15)

ENABLE_FILE_LOGGING = LOGGING_CONFIG.get("file", False)
FILE_LOG_LEVEL = LOGGING_CONFIG.get("file_level", "WARNING")
ENABLE_STDOUT = LOGGING_CONFIG.get("stdout", True)
STDOUT_LOG_LEVEL = LOGGING_CONFIG.get("stdout_level", "INFO")
