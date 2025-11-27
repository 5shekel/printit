"""
Configuration for the Sticker Factory application.

Loads settings from config.toml and secrets.toml.
"""

import streamlit as st
import tomllib
from pathlib import Path


def _load_config():
    """Load config.toml from the workspace root."""
    config_path = Path(__file__).parent / "config.toml"
    try:
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    except FileNotFoundError:
        st.error(f"config.toml not found at {config_path}")
        return {}
    except Exception as e:
        st.error(f"Error loading config.toml: {e}")
        return {}


_CONFIG = _load_config()

# ============================================================================
# TAB CONFIGURATION
# ============================================================================

# Get enabled tabs from config.toml [tabs] section
def get_enabled_tabs():
    """Return list of enabled tab names in order from config.toml."""
    return _CONFIG.get("tabs", {}).get("enabled", [
        "Sticker",
        "Sticker Pro",
        "Label",
        "Text2image",
        "Webcam",
        "Cat",
        "History",
        "FAQ",
    ])


def get_enabled_tab_count():
    """Return count of enabled tabs."""
    return len(get_enabled_tabs())


# Create ENABLED_TABS dict for backward compatibility
ENABLED_TABS = {tab: True for tab in get_enabled_tabs()}

# ============================================================================
# APPLICATION SETTINGS (from config.toml)
# ============================================================================

# Get settings from config.toml with fallback defaults
_app_config = _CONFIG.get("app", {})
LABEL_TYPE = _app_config.get("label_type", "62")
APP_TITLE = _app_config.get("title", "STICKER FACTORY")

_ui_config = _CONFIG.get("ui", {})
HISTORY_LIMIT = _ui_config.get("history_limit", 15)
ITEMS_PER_PAGE = _ui_config.get("items_per_page", 5)
QUEUE_VIEW = _ui_config.get("queue_view", True)

_txt2img_config = _CONFIG.get("txt2img", {})
TXT2IMG_URL = _txt2img_config.get("url", "http://localhost:7860")

# ============================================================================
# API CONFIGURATION (from secrets.toml)
# ============================================================================

# API keys are kept in secrets.toml for security
CAT_API_KEY = st.secrets.get("cat_api_key", "")

__all__ = [
    'get_enabled_tabs',
    'get_enabled_tab_count',
    'ENABLED_TABS',
    'LABEL_TYPE',
    'APP_TITLE',
    'HISTORY_LIMIT',
    'ITEMS_PER_PAGE',
    'QUEUE_VIEW',
    'TXT2IMG_URL',
    'CAT_API_KEY',
]
