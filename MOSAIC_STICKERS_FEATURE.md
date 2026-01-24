# Mosaic Stickers Feature

## Concept
Break a large image into multiple stickers that assemble into a mosaic. Users can create wall-sized art from small printable labels with alignment marks for precise assembly.

## Implementation Approach

### Core Functionality
```python
# tabs/mosaic.py
import math
from PIL import Image, ImageDraw
import streamlit as st

def create_mosaic_tiles(image, grid_size, overlap_pixels=10, add_alignment=True):
    """
    Split image into grid of tiles with overlap for alignment.
    
    Args:
        image: PIL Image to split
        grid_size: Tuple (rows, columns) or single int for square grid
        overlap_pixels: Overlap region between tiles in pixels
        add_alignment: Whether to add alignment marks
    
    Returns:
        List of tuples: [(tile_image, position_x, position_y), ...]
    """
    # Handle grid size parameter
    if isinstance(grid_size, int):
        rows = cols = grid_size
    else:
        rows, cols = grid_size
    
    # Calculate tile dimensions
    img_width, img_height = image.size
    tile_width = math.ceil(img_width / cols)
    tile_height = math.ceil(img_height / rows)
    
    # Add overlap to tile dimensions
    tile_width_with_overlap = tile_width + overlap_pixels * 2
    tile_height_with_overlap = tile_height + overlap_pixels * 2
    
    tiles = []
    
    for row in range(rows):
        for col in range(cols):
            # Calculate source region (with overlap)
            left = max(0, col * tile_width - overlap_pixels)
            upper = max(0, row * tile_height - overlap_pixels)
            right = min(img_width, (col + 1) * tile_width + overlap_pixels)
            lower = min(img_height, (row + 1) * tile_height + overlap_pixels)
            
            # Extract tile
            tile = image.crop((left, upper, right, lower))
            
            # Create new tile with consistent size
            new_tile = Image.new("RGB", (tile_width_with_overlap, tile_height_with_overlap), (255, 255, 255))
            new_tile.paste(tile, (overlap_pixels - (left - col * tile_width), 
                                 overlap_pixels - (upper - row * tile_height)))
            
            # Add alignment marks if requested
            if add_alignment:
                draw = ImageDraw.Draw(new_tile)
                
                # Corner marks (crosshairs)
                mark_size = 5
                # Top-left
                draw.line([(overlap_pixels, mark_size), (overlap_pixels, 0)], fill=0)
                draw.line([(mark_size, overlap_pixels), (0, overlap_pixels)], fill=0)
                
                # Top-right
                draw.line([(tile_width_with_overlap - overlap_pixels, mark_size), 
                          (tile_width_with_overlap - overlap_pixels, 0)], fill=0)
                draw.line([(tile_width_with_overlap - mark_size, overlap_pixels),
                          (tile_width_with_overlap, overlap_pixels)], fill=0)
                
                # Bottom-left
                draw.line([(overlap_pixels, tile_height_with_overlap - mark_size),
                          (overlap_pixels, tile_height_with_overlap)], fill=0)
                draw.line([(mark_size, tile_height_with_overlap - overlap_pixels),
                          (0, tile_height_with_overlap - overlap_pixels)], fill=0)
                
                # Bottom-right
                draw.line([(tile_width_with_overlap - overlap_pixels, tile_height_with_overlap - mark_size),
                          (tile_width_with_overlap - overlap_pixels, tile_height_with_overlap)], fill=0)
                draw.line([(tile_width_with_overlap - mark_size, tile_height_with_overlap - overlap_pixels),
                          (tile_width_with_overlap, tile_height_with_overlap - overlap_pixels)], fill=0)
                
                # Tile identifier
                identifier = f"{row+1}-{col+1}"
                draw.text((5, 5), identifier, fill=0)
            
            tiles.append((new_tile, col, row))
    
    return tiles

def render(printer_info, preper_image, print_image):
    """Render the Mosaic Stickers tab."""
    st.subheader(":jigsaw: Mosaic Stickers")
    st.write("Split large images into printable tiles that assemble into mosaics")
    
    # Image upload
    uploaded_file = st.file_uploader("Choose an image", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        
        # Display original image
        st.image(image, caption="Original Image", use_container_width=True)
        
        # Mosaic configuration
        col1, col2, col3 = st.columns(3)
        with col1:
            grid_size = st.selectbox("Grid Size", 
                                    ["2x2", "3x3", "4x4", "5x5", "6x6"],
                                    index=1)
            rows_cols = int(grid_size[0])  # Extract number from "3x3"
        with col2:
            overlap = st.slider("Overlap (pixels)", 5, 30, 10,
                               help="Overlap region between tiles for alignment")
        with col3:
            add_marks = st.checkbox("Add Alignment Marks", value=True,
                                   help="Add crosshair marks to help with assembly")
        
        # Generate mosaic
        if st.button("Generate Mosaic Tiles", key="generate_mosaic"):
            with st.spinner(f"Creating {grid_size} mosaic..."):
                tiles = create_mosaic_tiles(
                    image=image,
                    grid_size=rows_cols,
                    overlap_pixels=overlap,
                    add_alignment=add_marks
                )
                
                # Store in session state
                st.session_state.mosaic_tiles = tiles
                st.session_state.mosaic_grid = (rows_cols, rows_cols)
                
                # Display preview
                st.success(f"Created {len(tiles)} mosaic tiles!")
                
                # Show assembly preview
                st.subheader("Assembly Preview")
                
                # Create grid preview
                preview_size = 100
                cols = rows_cols
                rows = rows_cols
                
                # Show tile grid
                for row in range(rows):
                    cols_display = st.columns(cols)
                    for col in range(cols):
                        tile_idx = row * cols + col
                        if tile_idx < len(tiles):
                            tile, tile_col, tile_row = tiles[tile_idx]
                            # Resize for preview
                            preview = tile.copy()
                            preview.thumbnail((preview_size, preview_size))
                            with cols_display[col]:
                                st.image(preview, caption=f"Tile {tile_row+1}-{tile_col+1}")
                
                # Assembly instructions
                with st.expander("Assembly Instructions"):
                    st.markdown(f"""
                    ### How to assemble your {grid_size} mosaic:
                    
                    1. **Print all {len(tiles)} tiles** (use "Print All Tiles" button below)
                    2. **Cut each tile** along the outer edges
                    3. **Align using marks**: Match the crosshair alignment marks
                    4. **Overlap regions**: The {overlap}px overlap helps with precise alignment
                    5. **Secure with adhesive**: Use glue, tape, or mounting putty
                    
                    **Pro tip**: Start from the center and work outward for best results!
                    """)
    
    # Print controls
    if 'mosaic_tiles' in st.session_state:
        tiles = st.session_state.mosaic_tiles
        grid_size = st.session_state.mosaic_grid
        
        st.subheader("Print Controls")
        
        # Print options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Print All Tiles", key="print_all_tiles"):
                total = len(tiles)
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, (tile, col_idx, row_idx) in enumerate(tiles):
                    status_text.text(f"Printing tile {i+1}/{total} ({row_idx+1}-{col_idx+1})...")
                    print_image(tile, printer_info=printer_info)
                    progress_bar.progress((i + 1) / total)
                
                status_text.text(f"All {total} tiles sent to printer queue!")
                st.success("Mosaic printing complete!")
        
        with col2:
            selected_tile = st.selectbox(
                "Print Specific Tile",
                [f"Tile {row+1}-{col+1}" for row in range(grid_size[0]) for col in range(grid_size[1])],
                key="tile_selector"
            )
            
            if st.button("Print Selected Tile", key="print_selected"):
                # Parse tile coordinates
                parts = selected_tile.split()[1].split("-")
                row = int(parts[0]) - 1
                col = int(parts[1]) - 1
                tile_idx = row * grid_size[1] + col
                
                if tile_idx < len(tiles):
                    tile, _, _ = tiles[tile_idx]
                    print_image(tile, printer_info=printer_info)
                    st.success(f"{selected_tile} sent to printer!")
```

## Required Changes

### 1. New Tab Module
Create `tabs/mosaic.py` with the above implementation.

### 2. Configuration Update
Add to `config.toml`:
```toml
[tabs]
enabled = [
    "Label",
    "Sticker", 
    "Sticker Pro",
    "Text2image",
    "Webcam",
    "Dog",
    "Cat",
    "History",
    "FAQ",
    "Isometric Cube",
    "Mosaic",  # Add this line
]
```

### 3. Utility Functions
Extend `image_utils.py` with mosaic utilities:
```python
def split_image_to_grid(image, grid_rows, grid_cols, overlap=10):
    """Split image into grid with overlap regions."""
    from PIL import ImageDraw
    import math
    
    width, height = image.size
    tile_width = math.ceil(width / grid_cols)
    tile_height = math.ceil(height / grid_rows)
    
    tiles = []
    for row in range(grid_rows):
        for col in range(grid_cols):
            left = max(0, col * tile_width - overlap)
            upper = max(0, row * tile_height - overlap)
            right = min(width, (col + 1) * tile_width + overlap)
            lower = min(height, (row + 1) * tile_height + overlap)
            
            tile = image.crop((left, upper, right, lower))
            tiles.append((tile, col, row))
    
    return tiles

def add_alignment_marks(image, mark_size=5, mark_type="crosshair"):
    """Add alignment marks to image corners."""
    from PIL import ImageDraw
    
    draw = ImageDraw.Draw(image)
    width, height = image.size
    
    if mark_type == "crosshair":
        # Top-left
        draw.line([(mark_size, 0), (mark_size, mark_size*2)], fill=0)
        draw.line([(0, mark_size), (mark_size*2, mark_size)], fill=0)
        
        # Top-right
        draw.line([(width-mark_size, 0), (width-mark_size, mark_size*2)], fill=0)
        draw.line([(width-mark_size*2, mark_size), (width, mark_size)], fill=0)
        
        # Bottom-left
        draw.line([(mark_size, height), (mark_size, height-mark_size*2)], fill=0)
        draw.line([(0, height-mark_size), (mark_size*2, height-mark_size)], fill=0)
        
        # Bottom-right
        draw.line([(width-mark_size, height), (width-mark_size, height-mark_size*2)], fill=0)
        draw.line([(width-mark_size*2, height-mark_size), (width, height-mark_size)], fill=0)
    
    return image
```

## Integration Points

### Uses Existing Functions
- `preper_image()`: Prepares each tile for printing
- `print_image()`: Queues individual tile print jobs
- Image loading from uploaded files (same as `sticker.py`)

### Session State Management
- Stores mosaic tiles in `st.session_state.mosaic_tiles`
- Remembers grid configuration for tile selection
- Maintains user preferences between interactions

### Job Queue Integration
- Batch printing uses existing `job_queue.py` system
- Progress tracking during batch operations
- Error handling for individual tile failures

## Creative Applications

### 1. Large Wall Art
- Create mural-sized images from small labels
- Collaborative community art projects
- Temporary gallery installations

### 2. Puzzle-Style Promotions
- Mystery images revealed when assembled
- Scavenger hunt components
- Interactive marketing materials

### 3. Educational Tools
- Map puzzles for geography lessons
- Anatomy diagrams for biology
- Historical timeline visualizations

### 4. Personal Projects
- Family photo mosaics
- Memory collages
- Custom wallpaper patterns

## Technical Considerations

### Image Quality
- Large images may need downsampling for label resolution
- Dithering affects tile appearance
- Overlap regions ensure seamless connections

### Printing Logistics
- Many tiles = many print jobs
- Paper/tape consumption considerations
- Color consistency across tiles

### Assembly Complexity
- Clear numbering/identification system
- Alignment mark visibility
- Instructions for proper sequencing

## Testing Strategy

### Unit Tests
- Test grid splitting accuracy
- Verify overlap calculations
- Check alignment mark placement

### Integration Tests
- Test with various image sizes and formats
- Verify batch printing functionality
- Check session state persistence

### User Testing
- Assembly instruction clarity
- Alignment mark effectiveness
- Print quality consistency

## Dependencies
- **Phase 2 Implementation** (Moderate complexity)
- Requires grid-based image processing
- Needs batch printing management
- Benefits from progress tracking

## Next Steps
1. Implement basic grid splitting
2. Add alignment mark options
3. Include assembly guide generation
4. Add support for non-square grids
5. Implement smart cropping for important features