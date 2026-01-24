# Stickers with Cutting Guides Feature

## Concept
Add dashed or dotted lines to indicate where to cut with scissors, plus registration marks for precise alignment. This feature helps users create craft projects, puzzles, paper models, and other DIY creations that require precise cutting.

## Implementation Approach

### Core Functionality
```python
# tabs/cutting_guides.py
from PIL import Image, ImageDraw
import streamlit as st

def add_cutting_guides(image, guide_type, guide_spacing, cut_margin=5, add_registration=True):
    """
    Add cutting guides around image perimeter.
    
    Args:
        image: PIL Image to add guides to
        guide_type: "dashed", "dotted", "scissors_icon", "perforated"
        guide_spacing: Spacing between guide marks in pixels
        cut_margin: Distance from image edge to cut line in pixels
        add_registration: Whether to add registration marks
    
    Returns:
        PIL Image with cutting guides added
    """
    # Create a copy with extra margin for guides
    width, height = image.size
    guide_image = Image.new("RGB", (width + cut_margin * 2, height + cut_margin * 2), (255, 255, 255))
    guide_image.paste(image, (cut_margin, cut_margin))
    
    draw = ImageDraw.Draw(guide_image)
    
    # Define cut line positions
    cut_left = cut_margin
    cut_right = width + cut_margin
    cut_top = cut_margin
    cut_bottom = height + cut_margin
    
    # Add cutting guides based on type
    if guide_type == "dashed":
        # Dashed line around perimeter
        dash_length = 10
        gap_length = 5
        
        # Top edge
        x = cut_left
        while x < cut_right:
            draw.line([(x, cut_top), (min(x + dash_length, cut_right), cut_top)], fill=0, width=2)
            x += dash_length + gap_length
        
        # Bottom edge
        x = cut_left
        while x < cut_right:
            draw.line([(x, cut_bottom), (min(x + dash_length, cut_right), cut_bottom)], fill=0, width=2)
            x += dash_length + gap_length
        
        # Left edge
        y = cut_top
        while y < cut_bottom:
            draw.line([(cut_left, y), (cut_left, min(y + dash_length, cut_bottom))], fill=0, width=2)
            y += dash_length + gap_length
        
        # Right edge
        y = cut_top
        while y < cut_bottom:
            draw.line([(cut_right, y), (cut_right, min(y + dash_length, cut_bottom))], fill=0, width=2)
            y += dash_length + gap_length
    
    elif guide_type == "dotted":
        # Dotted line around perimeter
        dot_spacing = guide_spacing
        
        # Top edge
        for x in range(cut_left, cut_right, dot_spacing):
            draw.ellipse([x-2, cut_top-2, x+2, cut_top+2], fill=0)
        
        # Bottom edge
        for x in range(cut_left, cut_right, dot_spacing):
            draw.ellipse([x-2, cut_bottom-2, x+2, cut_bottom+2], fill=0)
        
        # Left edge
        for y in range(cut_top, cut_bottom, dot_spacing):
            draw.ellipse([cut_left-2, y-2, cut_left+2, y+2], fill=0)
        
        # Right edge
        for y in range(cut_top, cut_bottom, dot_spacing):
            draw.ellipse([cut_right-2, y-2, cut_right+2, y+2], fill=0)
    
    elif guide_type == "scissors_icon":
        # Scissors icons at corners
        icon_size = 15
        
        # Top-left corner
        draw.polygon([(cut_left, cut_top + icon_size),
                     (cut_left + icon_size//2, cut_top),
                     (cut_left + icon_size, cut_top + icon_size)], fill=0)
        
        # Top-right corner
        draw.polygon([(cut_right - icon_size, cut_top + icon_size),
                     (cut_right - icon_size//2, cut_top),
                     (cut_right, cut_top + icon_size)], fill=0)
        
        # Bottom-left corner
        draw.polygon([(cut_left, cut_bottom - icon_size),
                     (cut_left + icon_size//2, cut_bottom),
                     (cut_left + icon_size, cut_bottom - icon_size)], fill=0)
        
        # Bottom-right corner
        draw.polygon([(cut_right - icon_size, cut_bottom - icon_size),
                     (cut_right - icon_size//2, cut_bottom),
                     (cut_right, cut_bottom - icon_size)], fill=0)
        
        # Add "CUT HERE" text
        from PIL import ImageFont
        try:
            font = ImageFont.truetype("fonts/5x5-Tami.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        draw.text((cut_left + 20, cut_top + 5), "CUT", font=font, fill=0)
        draw.text((cut_right - 40, cut_top + 5), "HERE", font=font, fill=0)
    
    elif guide_type == "perforated":
        # Perforated line (alternating long/short dashes)
        long_dash = 15
        short_dash = 5
        gap = 3
        
        # Top edge - alternating pattern
        x = cut_left
        is_long = True
        while x < cut_right:
            dash_len = long_dash if is_long else short_dash
            end_x = min(x + dash_len, cut_right)
            draw.line([(x, cut_top), (end_x, cut_top)], fill=0, width=2)
            x = end_x + gap
            is_long = not is_long
        
        # Repeat for other edges...
    
    # Add registration marks if requested
    if add_registration:
        mark_size = 8
        
        # Corner registration marks (crosshairs)
        # Top-left
        draw.line([(cut_left - mark_size, cut_top), (cut_left + mark_size, cut_top)], fill=0, width=1)
        draw.line([(cut_left, cut_top - mark_size), (cut_left, cut_top + mark_size)], fill=0, width=1)
        
        # Top-right
        draw.line([(cut_right - mark_size, cut_top), (cut_right + mark_size, cut_top)], fill=0, width=1)
        draw.line([(cut_right, cut_top - mark_size), (cut_right, cut_top + mark_size)], fill=0, width=1)
        
        # Bottom-left
        draw.line([(cut_left - mark_size, cut_bottom), (cut_left + mark_size, cut_bottom)], fill=0, width=1)
        draw.line([(cut_left, cut_bottom - mark_size), (cut_left, cut_bottom + mark_size)], fill=0, width=1)
        
        # Bottom-right
        draw.line([(cut_right - mark_size, cut_bottom), (cut_right + mark_size, cut_bottom)], fill=0, width=1)
        draw.line([(cut_right, cut_bottom - mark_size), (cut_right, cut_bottom + mark_size)], fill=0, width=1)
    
    return guide_image

def render(printer_info, preper_image, print_image, apply_threshold):
    """Render the Cutting Guides tab."""
    st.subheader(":scissors: Cutting Guides")
    st.write("Add cutting lines and registration marks for craft projects")
    
    # Input options
    input_method = st.radio("Create from", 
                           ["Upload Image", "Use Label Text", "Create Shape"],
                           horizontal=True)
    
    result_image = None
    
    if input_method == "Upload Image":
        # Image upload
        uploaded_file = st.file_uploader("Choose an image", type=['png', 'jpg', 'jpeg'])
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Original Image", use_container_width=True)
            
            # Store original for processing
            st.session_state.original_image = image
    
    elif input_method == "Use Label Text":
        # Use existing label functionality
        st.info("Enter text to create a label with cutting guides")
        
        text = st.text_area("Label Text", "CUT ME OUT!")
        
        if st.button("Create Text Label", key="create_text_label"):
            from tabs.label import calculate_actual_image_height_with_empty_lines
            from PIL import ImageFont, ImageDraw
            
            # Create text label (simplified version)
            try:
                font = ImageFont.truetype("fonts/5x5-Tami.ttf", 40)
            except:
                font = ImageFont.load_default()
            
            label_width = printer_info['label_width']
            line_spacing = 20
            padding = 20
            
            # Calculate height
            draw_temp = ImageDraw.Draw(Image.new("RGB", (1, 1)))
            lines = text.split("\n")
            total_height = padding * 2
            for line in lines:
                if line.strip():
                    bbox = draw_temp.textbbox((0, 0), line, font=font)
                    total_height += (bbox[3] - bbox[1]) + line_spacing
            
            # Create image
            image = Image.new("RGB", (label_width, total_height), (255, 255, 255))
            draw = ImageDraw.Draw(image)
            y = padding
            
            for line in lines:
                if line.strip():
                    bbox = draw.textbbox((0, y), line, font=font)
                    text_width = bbox[2] - bbox[0]
                    x = (label_width - text_width) // 2
                    draw.text((x, y), line, font=font, fill=(0, 0, 0))
                    y += (bbox[3] - bbox[1]) + line_spacing
            
            st.session_state.original_image = image
            st.image(image, caption="Text Label", use_container_width=True)
    
    else:  # Create Shape
        # Shape creation
        shape_type = st.selectbox("Shape Type",
                                 ["Rectangle", "Circle", "Triangle", "Star", "Heart"])
        
        col1, col2 = st.columns(2)
        with col1:
            shape_width = st.slider("Shape Width", 50, printer_info['label_width'], 200)
            shape_height = st.slider("Shape Height", 50, 500, 200)
        with col2:
            fill_color = st.color_picker("Fill Color", "#FF0000")
            outline_color = st.color_picker("Outline Color", "#000000")
        
        if st.button("Create Shape", key="create_shape"):
            # Create shape image
            image = Image.new("RGB", (shape_width, shape_height), (255, 255, 255))
            draw = ImageDraw.Draw(image)
            
            # Convert hex colors to RGB
            fill_rgb = tuple(int(fill_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            outline_rgb = tuple(int(outline_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            
            # Draw shape
            if shape_type == "Rectangle":
                draw.rectangle([10, 10, shape_width-10, shape_height-10], 
                              fill=fill_rgb, outline=outline_rgb, width=3)
            elif shape_type == "Circle":
                draw.ellipse([10, 10, shape_width-10, shape_height-10], 
                            fill=fill_rgb, outline=outline_rgb, width=3)
            # ... other shapes
            
            st.session_state.original_image = image
            st.image(image, caption=f"{shape_type} Shape", use_container_width=True)
    
    # Cutting guide configuration (shown if we have an image)
    if 'original_image' in st.session_state:
        image = st.session_state.original_image
        
        st.subheader("Cutting Guide Settings")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            guide_type = st.selectbox("Guide Type",
                                     ["dashed", "dotted", "scissors_icon", "perforated"],
                                     help="Style of cutting guide")
        with col2:
            guide_spacing = st.slider("Guide Spacing", 5, 50, 15,
                                     help="Spacing between guide marks")
        with col3:
            cut_margin = st.slider("Cut Margin", 0, 20, 5,
                                  help="Distance from edge to cut line")
        
        col4, col5 = st.columns(2)
        with col4:
            add_registration = st.checkbox("Add Registration Marks", value=True,
                                          help="Add crosshairs for alignment")
        with col5:
            preview_guides = st.checkbox("Preview with Guides", value=True)
        
        # Generate preview
        if st.button("Add Cutting Guides", key="add_guides"):
            with st.spinner("Adding cutting guides..."):
                result_image = add_cutting_guides(
                    image=image,
                    guide_type=guide_type,
                    guide_spacing=guide_spacing,
                    cut_margin=cut_margin,
                    add_registration=add_registration
                )
                
                st.session_state.guide_image = result_image
                
                # Show comparison
                if preview_guides:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.image(image, caption="Original", use_container_width=True)
                    with col_b:
                        st.image(result_image, caption="With Cutting Guides", use_container_width=True)
                else:
                    st.image(result_image, caption="With Cutting Guides", use_container_width=True)
                
                # Assembly instructions
                with st.expander("Cutting Instructions"):
                    st.markdown(f"""
                    ### How to use your cutting guide:
                    
                    1. **Print the image** with cutting guides
                    2. **Cut along the {guide_type} lines**
                    3. **Use registration marks** for precise alignment if needed
                    4. **Remove excess margin** outside the cut lines
                    
                    **Cutting tips**:
                    - Use sharp scissors for clean cuts
                    - Cut just outside the guide lines (not through them)
                    - The {cut_margin}px margin gives you room for error
                    - Registration marks help with multi-piece projects
                    """)
    
    # Print controls
    if 'guide_image' in st.session_state:
        result_image = st.session_state.guide_image
        
        st.subheader("Print Options")
        
        col1, col2 = st.columns(2)
        with col1:
            # Print with guides
            if st.button("Print with Cutting Guides", key="print_with_guides"):
                print_image(result_image, printer_info=printer_info)
                st.success("Image with cutting guides sent to printer!")
        
        with col2:
            # Print without guides (original)
            if st.button("Print Original (No Guides)", key="print_original"):
                print_image(st.session_state.original_image, printer_info=printer_info)
                st.success("Original image sent to printer!")
        
        # Advanced options
        with st.expander("Advanced Options"):
            st.write("Apply image processing before adding guides")
            
            threshold = st.slider("Threshold", 0, 255, 128,
                                 help="Convert to black and white at this threshold")
            
            if st.button("Apply Threshold + Guides", key="threshold_guides"):
                # Apply threshold to original image
                thresholded = apply_threshold(st.session_state.original_image, threshold)
                # Add guides to thresholded image
                final_image = add_cutting_guides(
                    image=thresholded,
                    guide_type=guide_type,
                    guide_spacing=guide_spacing,
                    cut_margin=cut_margin,
                    add_registration=add_registration
                )
                
                st.image(final_image, caption="Thresholded with Guides", use_container_width=True)
                
                if st.button("Print Thresholded Version", key="print_thresholded"):
                    print_image(final_image, printer_info=printer_info)
                    st.success("Thresholded image with guides sent to printer!")
```

## Required Changes

### 1. New Tab Module
Create `tabs/cutting_guides.py` with the above implementation.

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
    "Cutting Guides",  # Add this line
]
```

### 3. Utility Functions
Extend `image_utils.py` with cutting guide utilities:
```python
def add_cutting_guide(image, guide_type="dashed", spacing=15, margin=5):
    """Add cutting guide around image."""
    from PIL import ImageDraw
    
    width, height = image.size
    guide_image = Image.new("RGB", (width + margin * 2, height + margin * 2), (255, 255, 255))
    guide_image.paste(image, (margin, margin))
    
    draw = ImageDraw.Draw(guide_image)
    
    # Define cut line positions
    cut_left = margin
    cut_right = width + margin
    cut_top = margin
    cut_bottom = height + margin
    
    if guide_type == "dashed":
        # Simple dashed implementation
        for x in range(cut_left, cut_right, spacing * 2):
            if x + spacing <= cut_right:
                draw.line([(x, cut_top), (x + spacing, cut_top)], fill=0, width=2)
                draw.line([(x, cut_bottom), (x + spacing, cut_bottom)], fill=0, width=2)
    
    return guide_image