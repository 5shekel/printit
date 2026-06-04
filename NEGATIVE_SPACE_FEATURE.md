# Negative Space Stickers Feature

## Concept
Create stickers where the design is cut out (negative space), showing through to the surface beneath. This creates reverse stencils, window decals, and layered shadow art where the background shows through the cut-out areas.

## Implementation Approach

### Core Functionality
```python
# tabs/negative_space.py
from PIL import Image, ImageDraw, ImageFilter, ImageOps
import streamlit as st
import numpy as np

def create_negative_space(image, invert_method, border_size=2, threshold=128):
    """
    Convert image to negative space design.
    
    Args:
        image: PIL Image to convert
        invert_method: "threshold", "edge_detect", "manual_mask", "gradient"
        border_size: Border width to add for structural integrity
        threshold: Threshold value for binarization (0-255)
    
    Returns:
        PIL Image with negative space design
    """
    # Convert to grayscale if needed
    if image.mode != 'L':
        grayscale = image.convert('L')
    else:
        grayscale = image
    
    if invert_method == "threshold":
        # Simple threshold inversion
        # Create binary mask
        binary = grayscale.point(lambda x: 0 if x > threshold else 255)
        # Invert: black becomes white (cut out), white becomes black (keep)
        inverted = ImageOps.invert(binary)
        
        # Add border for structural integrity
        if border_size > 0:
            bordered = ImageOps.expand(inverted, border=border_size, fill=255)
            # Erode the border to create cut line
            from PIL import ImageFilter
            bordered = bordered.filter(ImageFilter.MinFilter(3))
            inverted = bordered
    
    elif invert_method == "edge_detect":
        # Edge detection for outline-based negative space
        # Apply edge detection
        edges = grayscale.filter(ImageFilter.FIND_EDGES)
        # Enhance edges
        edges = edges.point(lambda x: 255 if x > 50 else 0)
        
        # Dilate edges to make them thicker
        from PIL import ImageFilter
        edges = edges.filter(ImageFilter.MaxFilter(3))
        
        # Create negative space by keeping edges, removing interior
        inverted = ImageOps.invert(edges)
        
        # Fill small holes
        inverted = inverted.filter(ImageFilter.MinFilter(3))
        inverted = inverted.filter(ImageFilter.MaxFilter(3))
    
    elif invert_method == "gradient":
        # Gradient-based negative space
        # Create gradient mask
        width, height = grayscale.size
        gradient = Image.new('L', (width, height))
        draw = ImageDraw.Draw(gradient)
        
        # Create vertical gradient
        for y in range(height):
            value = int(255 * (y / height))
            draw.line([(0, y), (width, y)], fill=value)
        
        # Blend with image
        blended = Image.blend(grayscale, gradient, alpha=0.5)
        
        # Threshold based on blended values
        binary = blended.point(lambda x: 0 if x > threshold else 255)
        inverted = ImageOps.invert(binary)
    
    else:  # manual_mask or default
        # Simple inversion for manual masking
        inverted = ImageOps.invert(grayscale)
        # Apply threshold to clean up
        inverted = inverted.point(lambda x: 0 if x < threshold else 255)
    
    # Convert back to RGB for consistency
    if inverted.mode != 'RGB':
        result = inverted.convert('RGB')
    else:
        result = inverted
    
    # Add registration marks for alignment
    draw = ImageDraw.Draw(result)
    mark_size = 10
    
    # Corner marks (crosshairs)
    width, height = result.size
    
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
    
    return result

def render(printer_info, preper_image, print_image, apply_threshold):
    """Render the Negative Space tab."""
    st.subheader(":frame_with_picture: Negative Space Stickers")
    st.write("Create cut-out designs that show through to surfaces beneath")
    
    # Image upload
    uploaded_file = st.file_uploader("Choose an image", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        
        # Display original
        st.image(image, caption="Original Image", use_container_width=True)
        
        # Negative space configuration
        col1, col2, col3 = st.columns(3)
        with col1:
            invert_method = st.selectbox("Inversion Method",
                                        ["threshold", "edge_detect", "gradient", "manual"],
                                        help="Method for creating negative space")
        
        with col2:
            threshold = st.slider("Threshold", 0, 255, 128,
                                 help="Brightness threshold for inversion")
        
        with col3:
            border_size = st.slider("Border Size", 0, 10, 2,
                                   help="Border width for structural integrity")
        
        # Preview options
        preview_bg = st.selectbox("Preview Background",
                                 ["white", "black", "red", "blue", "checkerboard"],
                                 help="Background color to preview negative space effect")
        
        # Generate negative space
        if st.button("Create Negative Space", key="create_negative"):
            with st.spinner("Creating negative space design..."):
                negative_image = create_negative_space(
                    image=image,
                    invert_method=invert_method,
                    border_size=border_size,
                    threshold=threshold
                )
                
                # Store in session state
                st.session_state.negative_image = negative_image
                st.session_state.original_image = image
                
                # Create preview with different backgrounds
                preview_images = []
                
                # White background
                white_bg = Image.new("RGB", negative_image.size, (255, 255, 255))
                white_bg.paste(negative_image, (0, 0))
                preview_images.append(("White Background", white_bg))
                
                # Black background
                black_bg = Image.new("RGB", negative_image.size, (0, 0, 0))
                black_bg.paste(negative_image, (0, 0))
                preview_images.append(("Black Background", black_bg))
                
                # Checkerboard background (for transparency simulation)
                checker_size = 20
                checker = Image.new("RGB", negative_image.size, (255, 255, 255))
                draw = ImageDraw.Draw(checker)
                for x in range(0, negative_image.width, checker_size * 2):
                    for y in range(0, negative_image.height, checker_size * 2):
                        draw.rectangle([x, y, x + checker_size, y + checker_size], fill=(200, 200, 200))
                for x in range(checker_size, negative_image.width, checker_size * 2):
                    for y in range(checker_size, negative_image.height, checker_size * 2):
                        draw.rectangle([x, y, x + checker_size, y + checker_size], fill=(200, 200, 200))
                checker.paste(negative_image, (0, 0))
                preview_images.append(("Checkerboard (Transparency)", checker))
                
                # Display previews
                st.success("Negative space design created!")
                
                cols = st.columns(min(3, len(preview_images)))
                for idx, (title, preview) in enumerate(preview_images):
                    with cols[idx % 3]:
                        st.image(preview, caption=title, use_container_width=True)
                
                # Application ideas
                with st.expander("Application Ideas"):
                    st.markdown(f"""
                    ### Creative uses for your negative space design:
                    
                    **{invert_method.replace('_', ' ').title()} Method Applications**:
                    
                    1. **Window Decals**:
                       - Apply to glass surfaces
                       - Light shines through cut-out areas
                       - Creates shadow patterns
                    
                    2. **Stencils**:
                       - Use for painting or spraying
                       - Create repeating patterns
                       - Multi-layer stencil art
                    
                    3. **Light Filters**:
                       - Place over lights or lamps
                       - Create patterned shadows
                       - Mood lighting effects
                    
                    4. **Layered Art**:
                       - Layer over colored paper
                       - Create depth with spacing
                       - Shadow box displays
                    
                    5. **Reverse Graffiti**:
                       - Apply to dirty surfaces
                       - Clean through cut-outs
                       - Temporary public art
                    
                    **Tips for best results**:
                    - Use {border_size}px border for structural strength
                    - Threshold {threshold} works best for {invert_method}
                    - Print on transparent film for window applications
                    - Layer multiple negatives for complex effects
                    """)
    
    # Print controls
    if 'negative_image' in st.session_state:
        negative_image = st.session_state.negative_image
        
        st.subheader("Print Options")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            # Print negative space design
            if st.button("Print Negative Space", key="print_negative"):
                print_image(negative_image, printer_info=printer_info)
                st.success("Negative space design sent to printer!")
        
        with col2:
            # Print original for comparison
            if st.button("Print Original", key="print_original_neg"):
                print_image(st.session_state.original_image, printer_info=printer_info)
                st.success("Original image sent to printer!")
        
        with col3:
            # Print with dithering
            if st.button("Print Dithered", key="print_dithered_neg"):
                grayscale, dithered = preper_image(negative_image, printer_info['label_width'])
                print_image(dithered, printer_info=printer_info)
                st.success("Dithered negative space sent to printer!")
        
        # Advanced options
        with st.expander("Advanced Options"):
            st.write("Customize negative space further")
            
            col_a, col_b = st.columns(2)
            with col_a:
                # Add text overlay
                add_text = st.checkbox("Add Text Label", value=False)
                if add_text:
                    text_label = st.text_input("Text to add", "NEGATIVE SPACE")
                    text_position = st.selectbox("Text Position", 
                                                ["top", "bottom", "left", "right"])
            
            with col_b:
                # Create mirror image
                create_mirror = st.checkbox("Create Mirror Image", value=False)
                if create_mirror:
                    mirror_type = st.selectbox("Mirror Type",
                                              ["horizontal", "vertical", "both"])
            
            if st.button("Apply Advanced Options", key="apply_advanced"):
                modified = negative_image.copy()
                
                if add_text and text_label:
                    from PIL import ImageFont, ImageDraw
                    draw = ImageDraw.Draw(modified)
                    try:
                        font = ImageFont.truetype("fonts/5x5-Tami.ttf", 20)
                    except:
                        font = ImageFont.load_default()
                    
                    # Calculate text position
                    bbox = draw.textbbox((0, 0), text_label, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    
                    if text_position == "top":
                        x = (modified.width - text_width) // 2
                        y = 10
                    elif text_position == "bottom":
                        x = (modified.width - text_width) // 2
                        y = modified.height - text_height - 10
                    elif text_position == "left":
                        x = 10
                        y = (modified.height - text_height) // 2
                    else:  # right
                        x = modified.width - text_width - 10
                        y = (modified.height - text_height) // 2
                    
                    draw.text((x, y), text_label, font=font, fill=(0, 0, 0))
                
                if create_mirror:
                    if mirror_type == "horizontal":
                        modified = ImageOps.mirror(modified)
                    elif mirror_type == "vertical":
                        modified = ImageOps.flip(modified)
                    else:  # both
                        modified = ImageOps.mirror(modified)
                        modified = ImageOps.flip(modified)
                
                st.session_state.modified_negative = modified
                st.image(modified, caption="Modified Negative Space", use_container_width=True)
                
                if st.button("Print Modified Version", key="print_modified"):
                    print_image(modified, printer_info=printer_info)
                    st.success("Modified negative space sent to printer!")
```

## Required Changes

### 1. New Tab Module
Create `tabs/negative_space.py` with the above implementation.

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
    "Mosaic",
    "Continuous Strip",
    "Cutting Guides",
    "Creative Text",
    "Negative Space",  # Add this line
]
```

### 3. Utility Functions
Extend `image_utils.py` with negative space utilities:
```python
def invert_for_negative_space(image, method="threshold", threshold=128):
    """Convert image to negative space design."""
    from PIL import ImageOps, ImageFilter
    
    if image.mode != 'L':
        image = image.convert('L')
    
    if method == "threshold":
        # Threshold-based inversion
        binary = image.point(lambda x: 0 if x > threshold else 255)
        return ImageOps.invert(binary)
    
    elif method == "edge":
        # Edge detection based
        edges = image.filter(ImageFilter.FIND_EDGES)
        edges = edges.point(lambda x: 255 if x > 50 else 0)
        return ImageOps.invert(edges)
    
    else:
        # Simple inversion
        return ImageOps.invert(image)

def apply_edge_detection(image, threshold=50):
    """Apply edge detection to image."""
    from PIL import ImageFilter
    
    if image.mode != 'L':
        image = image.convert('L')
    
    edges = image.filter(ImageFilter.FIND_EDGES)
    return edges.point(lambda x: 255 if x > threshold else 0)
```

## Integration Points

### Uses Existing Functions
- `apply_threshold()`: For threshold-based inversion
- `preper_image()`: For dithering before printing
- `print_image()`: Standard printing pipeline

### Image Processing
- Multiple inversion methods
- Edge detection for outlines
- Gradient-based negative space
- Border addition for structure

### Creative Applications
- Window decals and stencils
- Light filters and shadow art
- Layered compositions
- Reverse graffiti templates

## Creative Applications

### 1. Window Decals
- Privacy window films
- Decorative glass patterns
- Seasonal window displays
- Business window signage

### 2. Stencils & Templates
- Painting and spraying guides
- DIY craft project templates
- Educational tracing aids
- Repeat pattern creation

### 3. Light & Shadow Art
- Lamp shade patterns
- Projector templates
- Shadow puppet designs
- Light box compositions

### 4. Mixed Media
- Collage and scrapbooking
- Photo album decorations
- Journal page elements
- Card making supplies

### 5. Educational Tools
- Anatomy diagrams
- Map outlines for coloring
- Scientific illustrations
- Historical document reproductions

## Technical Considerations

### Structural Integrity
- Border addition prevents fragile designs
- Minimum line thickness for cutability
- Registration marks for alignment

### Print Quality
- Dithering affects cut-out clarity
- Threshold adjustment for different images
- Transparency simulation for preview

### Material Considerations
- Works best on transparent films
- Paper thickness affects cutting
- Adhesive compatibility for applications

## Testing Strategy

### Unit Tests
- Test inversion algorithms
- Verify edge detection accuracy
- Check border addition logic

### Integration Tests
- Test with various image types
- Verify printing functionality
- Check preview generation

### User Testing
- Cut-out quality assessment
- Application instruction clarity
- Material compatibility guidance

## Dependencies
- **Phase 1 Implementation** (Easiest)
- Uses existing threshold functions
- Builds on basic image processing
- Minimal new dependencies

## Next Steps
1. Implement basic threshold inversion
2. Add edge detection method
3. Include gradient-based negative space
4. Add advanced customization options
5. Integrate with other features