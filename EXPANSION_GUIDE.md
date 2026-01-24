# Printit Expansion Guide: Creative Sticker Features

## Overview

This guide explains how to implement various creative sticker features for the Printit project. Each section covers a specific feature idea, including implementation approach, code structure changes, and integration with the existing architecture.

## Current Architecture Reference

Before implementing new features, understand the existing structure:

### Core Components
1. **Main Application** (`printit.py`): Streamlit app with tab management
2. **Tab Modules** (`tabs/`): Each feature tab is a separate module
3. **Image Utilities** (`image_utils.py`): Image processing functions
4. **Printer Utilities** (`printer_utils.py`): Printer handling and job queue
5. **Configuration** (`config.toml`, `config_manager.py`): App settings
6. **Job Queue** (`job_queue.py`): Async print job processing

### Adding New Tabs
New features are typically implemented as new tab modules. The pattern:
1. Create `tabs/feature_name.py` with a `render()` function
2. Add the tab to `config.toml` under `[tabs].enabled`
3. Import and render in `printit.py` (already handles dynamic tab loading)

---

## Feature Implementation Guides

### 1. Isometric 3D Sticker Half Cube

**Concept**: Create stickers that appear as 3D half-cubes when assembled, with isometric projection.

**Implementation Approach**:

```python
# tabs/isometric_cube.py
def create_isometric_cube_faces(label_width, cube_size_mm):
    """
    Generate 3 faces of a half-cube in isometric projection.
    Returns a list of PIL Images for each face.
    """
    # Calculate isometric projection coordinates
    # Generate front, top, and side faces
    # Apply shading for 3D effect
    pass

def render(printer_info, preper_image, print_image):
    # UI for cube size, rotation, shading options
    # Preview of assembled cube
    # Option to print all faces at once
    pass
```

**Required Changes**:
1. New file: `tabs/isometric_cube.py`
2. Add to `config.toml`: `"Isometric Cube"` to enabled tabs list
3. Extend `image_utils.py` with isometric projection helper functions

**Integration Points**:
- Uses existing `preper_image()` for dithering
- Uses existing `print_image()` for printing
- Follows same parameter pattern as other tabs

**Creative Applications**:
- Architectural models
- Package design prototypes
- Educational geometry tools

### 2. Mosaic Stickers

**Concept**: Break a large image into multiple stickers that assemble into a mosaic.

**Implementation Approach**:

```python
# tabs/mosaic.py
def create_mosaic_tiles(image, grid_size, overlap_pixels):
    """
    Split image into grid of tiles with overlap for alignment.
    Returns list of (tile_image, position_x, position_y).
    """
    # Calculate tile dimensions
    # Create overlapping regions
    # Add alignment marks (crosshairs in corners)
    pass

def render(printer_info, preper_image, print_image):
    # Upload image
    # Grid size selector (2x2, 3x3, 4x4, etc.)
    # Overlap adjustment
    # Preview of assembled mosaic
    # Option to print all tiles or selected ones
    pass
```

**Required Changes**:
1. New file: `tabs/mosaic.py`
2. Add mosaic utilities to `image_utils.py`:
   - `split_image_to_grid()`
   - `add_alignment_marks()`
3. Update `config.toml` with `"Mosaic"` tab

**Integration Points**:
- Leverages existing image loading from `sticker.py`
- Uses `job_queue.py` for batch printing
- Could integrate with `history.py` for mosaic project tracking

**Creative Applications**:
- Large wall art from small stickers
- Collaborative art projects
- Puzzle-style promotions

### 3. Long Strips & Infinite Width/Height Stickers

**Concept**: Print continuous strips by aligning multiple labels, creating effectively infinite dimensions.

**Implementation Approach**:

```python
# tabs/continuous_strip.py
def create_continuous_strip(image, strip_direction, label_width, max_labels=10):
    """
    Create a continuous strip across multiple labels.
    direction: "horizontal" or "vertical"
    Returns list of images for each label segment.
    """
    # Calculate segmentation based on label dimensions
    # Add continuation marks (arrows, numbers)
    # Handle partial segments
    pass

def render(printer_info, preper_image, print_image):
    # Direction selector (horizontal/vertical)
    # Length in labels or millimeters
    # Preview of assembled strip
    # Print sequence guidance
    pass
```

**Required Changes**:
1. New file: `tabs/continuous_strip.py`
2. Extend `printer_utils.py`:
   - Add `print_sequence()` for ordered batch printing
   - Add alignment validation
3. Update `config.toml` with `"Continuous Strip"` tab

**Integration Points**:
- Uses `job_queue.py` with sequence tracking
- Could extend `history.py` to track multi-label projects
- Shares image processing with `sticker_pro.py`

**Creative Applications**:
- Timeline visualizations
- Continuous barcodes/QR codes
- Border decorations
- Measuring tapes/rulers

### 4. Stickers with Cutting Guides

**Concept**: Add dashed or dotted lines to indicate where to cut with scissors, plus registration marks.

**Implementation Approach**:

```python
# tabs/cutting_guides.py
def add_cutting_guides(image, guide_type, guide_spacing, label_width):
    """
    Add cutting guides around image perimeter.
    guide_type: "dashed", "dotted", "scissors_icon"
    Returns image with guides.
    """
    # Calculate guide positions
    # Add different guide styles
    # Include registration marks for alignment
    pass

def render(printer_info, preper_image, print_image, apply_threshold):
    # Guide style selector
    # Spacing adjustment
    # Registration mark options
    # Preview with and without guides
    pass
```

**Required Changes**:
1. New file: `tabs/cutting_guides.py`
2. Extend `image_utils.py`:
   - `add_cutting_guides()`
   - `add_registration_marks()`
3. Update `config.toml` with `"Cutting Guides"` tab

**Integration Points**:
- Can be combined with any existing tab (adds guides to output)
- Uses same printing pipeline
- Could be a post-processing option in `sticker.py` and `sticker_pro.py`

**Creative Applications**:
- DIY craft projects
- Paper model templates
- Puzzle pieces
- Gift tags with tear-off portions

### 5. Multi-line Text Creative Applications

**Concept**: Enhance the existing label tab with creative text layouts and effects.

**Implementation Approach**:

```python
# tabs/creative_text.py (or enhance tabs/label.py)
def create_text_effects(text, font, effect_type, label_width):
    """
    Apply creative effects to multi-line text.
    effect_type: "wave", "spiral", "perspective", "gradient"
    Returns styled text image.
    """
    # Parse text into lines
    # Apply geometric transformations
    # Add visual effects
    pass

def render(printer_info, get_fonts, preper_image, print_image):
    # Enhanced version of label.py with:
    # - Text effect selector
    # - Line-by-line formatting
    # - Visual preview with real-time updates
    # - Save/load text templates
    pass
```

**Required Changes**:
1. Option A: Enhance `tabs/label.py` with new features
2. Option B: Create `tabs/creative_text.py` for advanced features
3. Add text utilities to `image_utils.py` or new `text_utils.py`:
   - `apply_text_effect()`
   - `create_text_layout()`

**Integration Points**:
- Builds on existing `label.py` foundation
- Uses same font loading system
- Shares printing pipeline

**Creative Applications**:
- Poetry with visual formatting
- Concrete poetry (text forming shapes)
- Calligraphy practice guides
- Text-based art
- Secret messages (text within text)

### 6. Negative Space Stickers

**Concept**: Create stickers where the design is cut out (negative space), showing through to the surface beneath.

**Implementation Approach**:

```python
# tabs/negative_space.py
def create_negative_space(image, invert_method, border_size):
    """
    Convert image to negative space design.
    invert_method: "threshold", "edge_detect", "manual_mask"
    Returns inverted image with optional border.
    """
    # Apply inversion based on method
    # Clean up edges
    # Add border for structural integrity
    pass

def render(printer_info, preper_image, print_image, apply_threshold):
    # Image upload
    # Inversion method selector
    # Threshold adjustment
    # Border options
    # Preview on different background colors
    pass
```

**Required Changes**:
1. New file: `tabs/negative_space.py`
2. Extend `image_utils.py`:
   - `invert_for_negative_space()`
   - `apply_edge_detection()`
3. Update `config.toml` with `"Negative Space"` tab

**Integration Points**:
- Uses `apply_threshold()` from existing code
- Shares image processing pipeline
- Could integrate with `sticker_pro.py` options

**Creative Applications**:
- Window decals
- Stencils for painting
- Light filters (for lamps, etc.)
- Layered shadow art
- Reverse graffiti templates

### 7. Multi-layer Stickers

**Concept**: Create layered stickers with registration marks for precise alignment, potentially with transparent layers.

**Implementation Approach**:

```python
# tabs/multilayer.py
class MultiLayerProject:
    def __init__(self):
        self.layers = []  # List of (image, offset_x, offset_y, opacity)
        self.registration_marks = "crosshair"
    
    def add_layer(self, image, position, opacity=1.0):
        # Add layer to project
        pass
    
    def preview_assembled(self):
        # Composite all layers
        pass
    
    def generate_print_sheets(self):
        # Create separate images for each layer
        # Add registration marks
        # Add layer identification
        pass

def render(printer_info, preper_image, print_image):
    # Layer management UI
    # Position adjustment tools
    # Opacity controls
    # Registration mark style selector
    # Print all layers or selected ones
    pass
```

**Required Changes**:
1. New file: `tabs/multilayer.py`
2. New module: `multilayer_project.py` for project management
3. Extend `image_utils.py`:
   - `composite_layers()`
   - `add_registration_marks()`
4. Update `config.toml` with `"Multi-layer"` tab

**Integration Points**:
- Could integrate with `history.py` to save multilayer projects
- Uses `job_queue.py` for batch printing layers
- Shares image processing utilities

**Creative Applications**:
- Mixed media art (paper + transparency film)
- Color separation for screen printing
- Anaglyph 3D effects (red/blue glasses)
- Interactive layers (flip books, reveal layers)
- Educational models (anatomy, geology)

---

## Implementation Priority & Dependencies

### Phase 1 (Easiest, builds on existing code)
1. **Cutting Guides** - Simple image processing addition
2. **Creative Text** - Enhancement of existing label.py
3. **Negative Space** - Uses existing threshold functions

### Phase 2 (Moderate complexity)
4. **Mosaic Stickers** - Requires grid splitting logic
5. **Continuous Strips** - Requires sequence management

### Phase 3 (Most complex)
6. **Isometric Cube** - Requires 3D projection math
7. **Multi-layer Stickers** - Requires project management system

---

## Technical Considerations

### Printer Limitations
- Brother QL printers have fixed label widths
- Continuous strips require manual alignment
- Multi-layer requires precise registration
- Consider printer memory limits for complex images

### Image Processing
- All new features should use existing `preper_image()` pipeline
- Add new utilities to `image_utils.py` for reusability
- Consider performance for real-time previews

### User Experience
- Maintain consistent UI patterns with existing tabs
- Provide clear instructions for assembly/use
- Include previews before printing
- Save user settings in session state

### Code Organization
- Follow existing tab module pattern
- Use configuration system for defaults
- Add comprehensive logging
- Include error handling for edge cases

---

## Testing Strategy

1. **Unit Tests**: Test image processing functions in isolation
2. **Integration Tests**: Test tab rendering and user interactions
3. **Printer Simulation**: Test without actual printer using mock
4. **User Acceptance**: Test assembly instructions are clear

---

## Getting Started

To implement any of these features:

1. Choose a feature from Phase 1 to start
2. Create the tab module following existing patterns
3. Add necessary utilities to `image_utils.py`
4. Update `config.toml` to enable the tab
5. Test thoroughly before moving to next feature

Each feature can be developed independently, allowing for incremental improvement of the Printit system while maintaining backward compatibility with existing functionality.