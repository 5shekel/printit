# Printit Architecture Overview

## Core Components

Before implementing new features, understand the existing structure:

### 1. Main Application (`printit.py`)
- Streamlit app with tab management
- Dynamic tab loading based on configuration
- Printer detection and caching
- Session state management

### 2. Tab Modules (`tabs/`)
- Each feature tab is a separate Python module
- Follows pattern: `tabs/feature_name.py` with `render()` function
- Current tabs: `label.py`, `sticker.py`, `sticker_pro.py`, `text2image.py`, `webcam.py`, `cat.py`, `dog.py`, `history.py`, `faq.py`

### 3. Image Utilities (`image_utils.py`)
- Image processing and conversion functions
- Key functions: `preper_image()`, `apply_threshold()`, `resize_image_to_width()`, `add_border()`, `apply_histogram_equalization()`, `img_concat_v()`

### 4. Printer Utilities (`printer_utils.py`)
- Printer detection and status checking
- Print job processing with `process_print_job()`
- `PrinterInfo` dataclass for printer metadata
- Integration with brother_ql library

### 5. Job Queue (`job_queue.py`)
- Async print job processing with `PrintQueue` class
- Thread-safe job management
- Status tracking for print jobs

### 6. Configuration System
- `config.toml`: Application settings (non-sensitive)
- `config_manager.py`: Centralized configuration loading
- `.streamlit/secrets.toml`: API keys and sensitive data

### 7. Supporting Modules
- `logging_config.py`: Logging setup
- `job_queue.py`: Async job processing

## Adding New Tabs

New features are typically implemented as new tab modules. The pattern:

1. **Create tab module**: `tabs/feature_name.py` with a `render()` function
2. **Add to configuration**: Add tab name to `config.toml` under `[tabs].enabled`
3. **Import dependencies**: The tab will be automatically loaded by `printit.py`

### Tab Module Template
```python
"""Feature description tab content."""

import logging
import streamlit as st
from PIL import Image

logger = logging.getLogger("sticker_factory.tabs.feature_name")

def render(printer_info, preper_image, print_image, **kwargs):
    """Render the feature tab.
    
    Args:
        printer_info: Dictionary with printer details (label_type, label_width, etc.)
        preper_image: Function to prepare images for printing
        print_image: Function to queue print jobs
        **kwargs: Additional utility functions as needed
    """
    st.subheader(":printer: Feature Name")
    
    # Tab implementation here
    # Use st components for UI
    # Call utility functions for image processing
    # Use print_image() to send to printer
```

## Common Integration Points

### Image Processing Pipeline
All new features should use the existing `preper_image()` function for consistent dithering and resizing:
```python
grayscale_image, dithered_image = preper_image(input_image, label_width=printer_info['label_width'])
```

### Printing Pipeline
Use `print_image()` to queue print jobs:
```python
print_image(image_to_print, printer_info=printer_info)
```

### Configuration
Access app settings via `config_manager` module:
```python
from config_manager import APP_TITLE, PRIVACY_MODE, HISTORY_LIMIT
```

### Logging
Use the standard logging pattern:
```python
import logging
logger = logging.getLogger("sticker_factory.tabs.feature_name")
logger.info("Message")
```

## Development Workflow

1. **Create feature module** in `tabs/` directory
2. **Test locally** with `uv run streamlit run printit.py --server.port 8989`
3. **Add to config.toml** under `[tabs].enabled` list
4. **Test integration** with existing tabs
5. **Add utilities** to `image_utils.py` if needed for reusability

## Testing Considerations

- Test without physical printer using mock functions
- Verify image processing produces expected results
- Ensure UI components work responsively
- Test error handling for edge cases