# Continuous Strips & Infinite Width/Height Stickers Feature

## Concept
Print continuous strips by aligning multiple labels, creating effectively infinite dimensions. Users can create timelines, borders, measuring tapes, or any long-form content that spans multiple labels.

## Implementation Approach

### Core Functionality
```python
# tabs/continuous_strip.py
import math
from PIL import Image, ImageDraw
import streamlit as st

def create_continuous_strip(image, strip_direction, label_width, max_labels=10, add_continuation=True):
    """
    Create a continuous strip across multiple labels.
    
    Args:
        image: PIL Image to convert to strip
        strip_direction: "horizontal" or "vertical"
        label_width: Printer label width in pixels
        max_labels: Maximum number of labels to use
        add_continuation: Whether to add continuation marks
    
    Returns:
        List of PIL Images for each label segment
    """
    segments = []
    
    if strip_direction == "horizontal":
        # Horizontal strip - segment by width
        img_width, img_height = image.size
        
        # Calculate how many labels needed
        labels_needed = math.ceil(img_width / label_width)
        labels_needed = min(labels_needed, max_labels)
        
        # Segment width (last segment may be partial)
        segment_width = label_width
        
        for i in range(labels_needed):
            left = i * segment_width
            right = min((i + 1) * segment_width, img_width)
            
            # Extract segment
            segment = image.crop((left, 0, right, img_height))
            
            # Create new segment with consistent width
            new_segment = Image.new("RGB", (label_width, img_height), (255, 255, 255))
            new_segment.paste(segment, (0, 0))
            
            # Add continuation marks if requested
            if add_continuation:
                draw = ImageDraw.Draw(new_segment)
                
                # Add segment number
                draw.text((5, 5), f"Part {i+1}/{labels_needed}", fill=0)
                
                # Add continuation arrows
                if i > 0:  # Not first segment
                    # Left arrow
                    draw.polygon([(10, img_height//2 - 10),
                                 (10, img_height//2 + 10),
                                 (0, img_height//2)], fill=0)
                    draw.text((15, img_height//2 - 15), "←", fill=0)
                
                if i < labels_needed - 1:  # Not last segment
                    # Right arrow
                    draw.polygon([(label_width - 10, img_height//2 - 10),
                                 (label_width - 10, img_height//2 + 10),
                                 (label_width, img_height//2)], fill=0)
                    draw.text((label_width - 25, img_height//2 - 15), "→", fill=0)
            
            segments.append(new_segment)
    
    else:  # vertical
        # Vertical strip - segment by height
        img_width, img_height = image.size
        
        # Calculate segment height (based on label width for vertical orientation)
        # For vertical strips, we rotate the image, so segment height = label_width
        labels_needed = math.ceil(img_height / label_width)
        labels_needed = min(labels_needed, max_labels)
        
        for i in range(labels_needed):
            top = i * label_width
            bottom = min((i + 1) * label_width, img_height)
            
            # Extract segment
            segment = image.crop((0, top, img_width, bottom))
            
            # Create new segment with consistent height
            new_segment = Image.new("RGB", (img_width, label_width), (255, 255, 255))
            new_segment.paste(segment, (0, 0))
            
            # Add continuation marks if requested
            if add_continuation:
                draw = ImageDraw.Draw(new_segment)
                
                # Add segment number
                draw.text((5, 5), f"Part {i+1}/{labels_needed}", fill=0)
                
                # Add continuation arrows
                if i > 0:  # Not first segment
                    # Up arrow
                    draw.polygon([(img_width//2 - 10, 10),
                                 (img_width//2 + 10, 10),
                                 (img_width//2, 0)], fill=0)
                    draw.text((img_width//2 - 15, 15), "↑", fill=0)
                
                if i < labels_needed - 1:  # Not last segment
                    # Down arrow
                    draw.polygon([(img_width//2 - 10, label_width - 10),
                                 (img_width//2 + 10, label_width - 10),
                                 (img_width//2, label_width)], fill=0)
                    draw.text((img_width//2 - 15, label_width - 25), "↓", fill=0)
            
            segments.append(new_segment)
    
    return segments

def render(printer_info, preper_image, print_image):
    """Render the Continuous Strips tab."""
    st.subheader(":straight_ruler: Continuous Strips")
    st.write("Create long strips that span multiple labels")
    
    # Input options
    input_method = st.radio("Input Method", 
                           ["Upload Image", "Create Pattern", "Text Strip"],
                           horizontal=True)
    
    segments = []
    
    if input_method == "Upload Image":
        # Image upload for strip creation
        uploaded_file = st.file_uploader("Choose an image", type=['png', 'jpg', 'jpeg'])
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Original Image", use_container_width=True)
            
            # Strip configuration
            col1, col2, col3 = st.columns(3)
            with col1:
                direction = st.selectbox("Strip Direction", 
                                        ["horizontal", "vertical"],
                                        help="Horizontal for width, vertical for height")
            with col2:
                max_segments = st.slider("Max Labels", 2, 20, 10,
                                        help="Maximum number of labels to use")
            with col3:
                add_marks = st.checkbox("Add Continuation Marks", value=True,
                                       help="Add arrows and part numbers")
            
            # Generate strip
            if st.button("Create Strip Segments", key="create_strip"):
                with st.spinner("Creating strip segments..."):
                    segments = create_continuous_strip(
                        image=image,
                        strip_direction=direction,
                        label_width=printer_info['label_width'],
                        max_labels=max_segments,
                        add_continuation=add_marks
                    )
    
    elif input_method == "Create Pattern":
        # Pattern-based strip creation
        col1, col2 = st.columns(2)
        with col1:
            pattern_type = st.selectbox("Pattern Type",
                                       ["Stripes", "Dots", "Chevron", "Wave", "Barcode"])
            pattern_color = st.color_picker("Pattern Color", "#000000")
        with col2:
            strip_length = st.slider("Strip Length (labels)", 2, 20, 5)
            pattern_size = st.slider("Pattern Size", 10, 100, 30)
        
        # Generate pattern
        if st.button("Generate Pattern Strip", key="generate_pattern"):
            with st.spinner("Creating pattern..."):
                # Create pattern image
                pattern_width = printer_info['label_width'] * strip_length
                pattern_height = 200  # Fixed height for patterns
                
                pattern = Image.new("RGB", (pattern_width, pattern_height), (255, 255, 255))
                draw = ImageDraw.Draw(pattern)
                
                # Convert hex color to RGB
                color_rgb = tuple(int(pattern_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                
                # Draw pattern based on type
                if pattern_type == "Stripes":
                    for x in range(0, pattern_width, pattern_size * 2):
                        draw.rectangle([x, 0, x + pattern_size, pattern_height], fill=color_rgb)
                elif pattern_type == "Dots":
                    for x in range(pattern_size, pattern_width, pattern_size * 2):
                        for y in range(pattern_size, pattern_height, pattern_size * 2):
                            draw.ellipse([x-pattern_size//2, y-pattern_size//2,
                                         x+pattern_size//2, y+pattern_size//2], 
                                        fill=color_rgb)
                # ... other pattern types
                
                segments = create_continuous_strip(
                    image=pattern,
                    strip_direction="horizontal",
                    label_width=printer_info['label_width'],
                    max_labels=strip_length,
                    add_continuation=True
                )
    
    else:  # Text Strip
        # Text-based strip creation
        text = st.text_area("Enter text for strip", "CONTINUOUS STRIP TEXT")
        col1, col2 = st.columns(2)
        with col1:
            font_size = st.slider("Font Size", 20, 100, 40)
            text_spacing = st.slider("Letter Spacing", 0, 50, 10)
        with col2:
            repeat_text = st.checkbox("Repeat Text", value=True)
            strip_length = st.slider("Text Length (labels)", 2, 10, 4)
        
        if st.button("Create Text Strip", key="create_text_strip"):
            with st.spinner("Creating text strip..."):
                # Create text image
                from PIL import ImageFont
                
                # Estimate text width
                char_width = font_size * 0.6
                text_width = int(len(text) * char_width + (len(text) - 1) * text_spacing)
                if repeat_text:
                    text_width *= 2  # Double for repetition
                
                strip_width = printer_info['label_width'] * strip_length
                strip_height = font_size + 40
                
                text_image = Image.new("RGB", (max(text_width, strip_width), strip_height), (255, 255, 255))
                draw = ImageDraw.Draw(text_image)
                
                # Try to load font
                try:
                    font = ImageFont.truetype("fonts/5x5-Tami.ttf", font_size)
                except:
                    font = ImageFont.load_default()
                
                # Draw text
                x_pos = 20
                text_to_draw = text * 2 if repeat_text else text
                for char in text_to_draw:
                    draw.text((x_pos, 20), char, font=font, fill=(0, 0, 0))
                    x_pos += char_width + text_spacing
                
                segments = create_continuous_strip(
                    image=text_image,
                    strip_direction="horizontal",
                    label_width=printer_info['label_width'],
                    max_labels=strip_length,
                    add_continuation=True
                )
    
    # Display and print controls
    if segments:
        st.success(f"Created {len(segments)} strip segments!")
        
        # Display preview
        st.subheader("Strip Preview")
        preview_cols = st.columns(min(3, len(segments)))
        for i, segment in enumerate(segments):
            col_idx = i % 3
            with preview_cols[col_idx]:
                st.image(segment, caption=f"Segment {i+1}/{len(segments)}", width=200)
        
        # Assembly instructions
        with st.expander("Assembly Instructions"):
            st.markdown(f"""
            ### How to assemble your {len(segments)}-segment strip:
            
            1. **Print all segments** in order (use "Print in Sequence" below)
            2. **Align carefully**: Match the continuation arrows
            3. **Join segments**: Overlap or butt-join based on your preference
            4. **Secure**: Use tape on the back for a continuous strip
            
            **Printing tip**: Print segment 1 first, then use it as reference for alignment!
            """)
        
        # Print controls
        st.subheader("Print Controls")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Print in Sequence", key="print_sequence"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, segment in enumerate(segments):
                    status_text.text(f"Printing segment {i+1}/{len(segments)}...")
                    print_image(segment, printer_info=printer_info)
                    progress_bar.progress((i + 1) / len(segments))
                    # Small delay between prints
                    import time
                    time.sleep(0.5)
                
                status_text.text(f"All {len(segments)} segments printed in sequence!")
                st.success("Strip printing complete!")
        
        with col2:
            selected_segment = st.selectbox(
                "Print Specific Segment",
                [f"Segment {i+1}" for i in range(len(segments))],
                key="segment_selector"
            )
            
            if st.button("Print Selected Segment", key="print_selected_segment"):
                seg_num = int(selected_segment.split()[1]) - 1
                print_image(segments[seg_num], printer_info=printer_info)
                st.success(f"{selected_segment} sent to printer!")
```

## Required Changes

### 1. New Tab Module
Create `tabs/continuous_strip.py` with the above implementation.

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
    "Continuous Strip",  # Add this line
]
```

### 3. Utility Functions
Extend `image_utils.py` with strip utilities:
```python
def create_strip_segments(image, segment_width, add_labels=True):
    """Create strip segments from an image."""
    from PIL import ImageDraw
    import math
    
    width, height = image.size
    segments_needed = math.ceil(width / segment_width)
    
    segments = []
    for i in range(segments_needed):
        left = i * segment_width
        right = min((i + 1) * segment_width, width)
        
        segment = image.crop((left, 0, right, height))
        
        # Create consistent width segment
        new_segment = Image.new("RGB", (segment_width, height), (255, 255, 255))
        new_segment.paste(segment, (0, 0))
        
        if add_labels:
            draw = ImageDraw.Draw(new_segment)
            draw.text((5, 5), f"{i+1}/{segments_needed}", fill=0)
        
        segments.append(new_segment)
    
    return segments

def add_continuation_marks(image, position="right", mark_type="arrow"):
    """Add continuation marks to image edges."""
    from PIL import ImageDraw
    
    draw = ImageDraw.Draw(image)
    width, height = image.size
    
    if mark_type == "arrow":
        if position == "right":
            # Right arrow
            draw.polygon([(width - 20, height//2 - 15),
                         (width - 20, height//2 + 15),
                         (width, height//2)], fill=0)
        elif position == "left":
            # Left arrow
            draw.polygon([(20, height//2 - 15),
                         (20, height//2 + 15),
                         (0, height//2)], fill=0)
    
    return image
```

## Integration Points

### Uses Existing Functions
- `preper_image()`: Prepares each segment for printing
- `print_image()`: Queues individual segment print jobs
- Image loading and text rendering from existing tabs

### Sequence Management
- Ordered printing with progress tracking
- Segment numbering for proper assembly
- Visual continuation marks for alignment

### Pattern Generation
- Built-in pattern creation for decorative strips
- Text strip generation for banners and labels
- Custom image segmentation

## Creative Applications

### 1. Timeline Visualizations
- Historical timelines
- Project schedules
- Process flow diagrams

### 2. Continuous Barcodes/QR Codes
- Extra-long barcodes for inventory
- Sequential QR codes for tours
- Scannable story strips

### 3. Border Decorations
- Room borders and trim
- Picture frame decorations
- Bulletin board edges

### 4. Measuring Tools
- Printable rulers and tape measures
- Calibration strips
- Scale references

### 5. Text Banners
- Long messages and quotes
- Event banners
- Warning/instruction strips

## Technical Considerations

### Alignment Precision
- Continuation marks must be accurately placed
- Printer margin consistency affects alignment
- User skill in assembling strips

### Printing Sequence
- Must print in correct order
- Paper feeding consistency
- Segment identification clarity

### Image Quality
- Seamless transitions between segments
- Consistent dithering across segments
- Pattern repetition accuracy

## Testing Strategy

### Unit Tests
- Test segment width calculations
- Verify continuation mark placement
- Check pattern generation accuracy

### Integration Tests
- Test with various image sizes
- Verify sequential printing works
- Check session state for segment storage

### User Testing
- Assembly instruction clarity
- Continuation mark effectiveness
- Print alignment accuracy

## Dependencies
- **Phase 2 Implementation** (Moderate complexity)
- Requires sequence management
- Needs pattern generation logic
- Benefits from progress tracking

## Next Steps
1. Implement basic horizontal segmentation
2. Add vertical strip support
3. Include pattern generation
4. Add text strip creation
5. Implement smart segmentation for important features