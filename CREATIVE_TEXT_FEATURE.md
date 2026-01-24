# Multi-line Text Creative Applications Feature

## Concept
Enhance the existing label tab with creative text layouts and effects, allowing users to create visually striking text-based stickers with advanced formatting, effects, and artistic arrangements.

## Implementation Approach

### Core Functionality
```python
# tabs/creative_text.py
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import streamlit as st
import math

def create_text_effects(text, font_path, effect_type, label_width, font_size=40):
    """
    Apply creative effects to multi-line text.
    
    Args:
        text: Multi-line text string
        font_path: Path to font file
        effect_type: "wave", "spiral", "perspective", "gradient", "shadow", "outline"
        label_width: Available width for text
        font_size: Base font size
    
    Returns:
        PIL Image with styled text
    """
    # Load font
    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()
    
    # Calculate text dimensions
    lines = text.split('\n')
    draw_temp = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    
    # Calculate total height needed
    line_heights = []
    for line in lines:
        if line.strip():
            bbox = draw_temp.textbbox((0, 0), line, font=font)
            line_heights.append(bbox[3] - bbox[1])
        else:
            line_heights.append(font_size)
    
    total_height = sum(line_heights) + (len(lines) * 20)  # Add spacing
    total_height = max(total_height, label_width // 2)  # Minimum height
    
    # Create base image
    image = Image.new("RGB", (label_width, total_height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # Apply effects based on type
    if effect_type == "wave":
        # Wave effect - sinusoidal text
        amplitude = 20
        frequency = 0.05
        
        y_start = 40
        for line_idx, line in enumerate(lines):
            if not line.strip():
                y_start += line_heights[line_idx] + 20
                continue
            
            # Calculate wave positions for each character
            chars = list(line)
            char_widths = [draw_temp.textbbox((0, 0), char, font=font)[2] for char in chars]
            total_line_width = sum(char_widths)
            x_start = (label_width - total_line_width) // 2
            
            x_pos = x_start
            for i, char in enumerate(chars):
                # Calculate wave offset
                wave_offset = int(amplitude * math.sin(frequency * x_pos))
                y_pos = y_start + wave_offset
                
                draw.text((x_pos, y_pos), char, font=font, fill=(0, 0, 0))
                x_pos += char_widths[i]
            
            y_start += line_heights[line_idx] + 20 + amplitude
    
    elif effect_type == "spiral":
        # Spiral text arrangement
        center_x = label_width // 2
        center_y = total_height // 2
        radius = min(center_x, center_y) - 40
        angle_step = 360 / len(text.replace('\n', ''))
        
        char_idx = 0
        for line in lines:
            for char in line:
                if char.strip():
                    angle = math.radians(char_idx * angle_step)
                    x = center_x + int(radius * math.cos(angle))
                    y = center_y + int(radius * math.sin(angle))
                    
                    # Rotate character to follow spiral
                    char_image = Image.new("RGB", (font_size, font_size), (255, 255, 255))
                    char_draw = ImageDraw.Draw(char_image)
                    char_draw.text((0, 0), char, font=font, fill=(0, 0, 0))
                    rotated_char = char_image.rotate(-char_idx * angle_step)
                    
                    image.paste(rotated_char, (x - font_size//2, y - font_size//2))
                    char_idx += 1
    
    elif effect_type == "gradient":
        # Gradient color text
        y_pos = 40
        for line_idx, line in enumerate(lines):
            if not line.strip():
                y_pos += line_heights[line_idx] + 20
                continue
            
            bbox = draw_temp.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x_pos = (label_width - text_width) // 2
            
            # Create gradient colors
            colors = [(255, 0, 0), (255, 165, 0), (255, 255, 0), 
                     (0, 255, 0), (0, 0, 255), (75, 0, 130), (238, 130, 238)]
            
            # Draw each character with different color
            chars = list(line)
            for i, char in enumerate(chars):
                color_idx = i % len(colors)
                draw.text((x_pos, y_pos), char, font=font, fill=colors[color_idx])
                char_bbox = draw_temp.textbbox((0, 0), char, font=font)
                x_pos += char_bbox[2] - char_bbox[0]
            
            y_pos += line_heights[line_idx] + 20
    
    elif effect_type == "shadow":
        # Text with shadow effect
        y_pos = 40
        shadow_offset = 3
        
        for line_idx, line in enumerate(lines):
            if not line.strip():
                y_pos += line_heights[line_idx] + 20
                continue
            
            bbox = draw_temp.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x_pos = (label_width - text_width) // 2
            
            # Draw shadow
            draw.text((x_pos + shadow_offset, y_pos + shadow_offset), 
                     line, font=font, fill=(150, 150, 150))
            # Draw main text
            draw.text((x_pos, y_pos), line, font=font, fill=(0, 0, 0))
            
            y_pos += line_heights[line_idx] + 20
    
    else:  # Default - centered text
        y_pos = 40
        for line_idx, line in enumerate(lines):
            if not line.strip():
                y_pos += line_heights[line_idx] + 20
                continue
            
            bbox = draw_temp.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x_pos = (label_width - text_width) // 2
            draw.text((x_pos, y_pos), line, font=font, fill=(0, 0, 0))
            y_pos += line_heights[line_idx] + 20
    
    return image

def render(printer_info, get_fonts, preper_image, print_image):
    """Render the Creative Text tab."""
    st.subheader(":art: Creative Text")
    st.write("Create artistic text layouts with special effects")
    
    # Text input
    text = st.text_area("Enter your text", "CREATIVE\nTEXT\nEFFECTS", height=150)
    
    if text:
        # Get available fonts
        fonts = get_fonts()
        
        # Text configuration
        col1, col2, col3 = st.columns(3)
        with col1:
            # Font selection with display names
            def get_font_display_name(font_path):
                try:
                    font = ImageFont.truetype(font_path, 12)
                    if hasattr(font, 'getname'):
                        name = font.getname()
                        if name and isinstance(name, tuple):
                            return ' '.join(name)
                        return name
                except:
                    pass
                import os
                return os.path.splitext(os.path.basename(font_path))[0]
            
            font_names = [get_font_display_name(f) for f in fonts]
            selected_font_name = st.selectbox("Font", font_names, index=0)
            selected_font = fonts[font_names.index(selected_font_name)]
        
        with col2:
            effect_type = st.selectbox("Text Effect",
                                      ["normal", "wave", "spiral", "gradient", "shadow", "outline"],
                                      help="Special effect to apply to text")
        
        with col3:
            font_size = st.slider("Font Size", 20, 100, 40)
        
        # Advanced options
        with st.expander("Advanced Options"):
            col_a, col_b = st.columns(2)
            with col_a:
                line_spacing = st.slider("Line Spacing", 10, 50, 20)
                text_color = st.color_picker("Text Color", "#000000")
            with col_b:
                bg_color = st.color_picker("Background Color", "#FFFFFF")
                add_border = st.checkbox("Add Border", value=False)
        
        # Generate preview
        if st.button("Generate Creative Text", key="generate_creative_text"):
            with st.spinner("Creating text effect..."):
                # Create text image
                text_image = create_text_effects(
                    text=text,
                    font_path=selected_font,
                    effect_type=effect_type,
                    label_width=printer_info['label_width'],
                    font_size=font_size
                )
                
                # Apply background color if not white
                if bg_color != "#FFFFFF":
                    bg_rgb = tuple(int(bg_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                    bg_image = Image.new("RGB", text_image.size, bg_rgb)
                    # Composite text onto background
                    if text_image.mode == 'RGBA':
                        bg_image.paste(text_image, (0, 0), text_image)
                        text_image = bg_image
                    else:
                        # For RGB, we need to handle differently
                        text_pixels = text_image.load()
                        bg_pixels = bg_image.load()
                        for x in range(text_image.width):
                            for y in range(text_image.height):
                                if text_pixels[x, y] == (255, 255, 255):
                                    text_pixels[x, y] = bg_rgb
                
                # Add border if requested
                if add_border:
                    from PIL import ImageOps
                    text_image = ImageOps.expand(text_image, border=10, fill='black')
                    text_image = ImageOps.expand(text_image, border=2, fill='white')
                
                # Store in session state
                st.session_state.creative_text_image = text_image
                
                # Display preview
                st.image(text_image, caption=f"Text with {effect_type} effect", use_container_width=True)
                
                # Creative usage ideas
                with st.expander("Creative Usage Ideas"):
                    st.markdown(f"""
                    ### Ideas for your {effect_type} text:
                    
                    **{effect_type.capitalize()} Text Applications**:
                    - **Posters & Signs**: Eye-catching displays
                    - **Gift Tags**: Personalized presents
                    - **Bookmarks**: Decorative reading aids
                    - **Labels**: Unique organization system
                    - **Art Projects**: Mixed media compositions
                    
                    **Combination Ideas**:
                    - Use with **Cutting Guides** for shaped text
                    - Combine with **Negative Space** for reverse effects
                    - Layer with **Multi-layer** for 3D text
                    - Add to **Mosaic** as individual tiles
                    """)
    
    # Print controls
    if 'creative_text_image' in st.session_state:
        text_image = st.session_state.creative_text_image
        
        st.subheader("Print Options")
        
        col1, col2 = st.columns(2)
        with col1:
            # Print as-is
            if st.button("Print Creative Text", key="print_creative"):
                print_image(text_image, printer_info=printer_info)
                st.success("Creative text sent to printer!")
        
        with col2:
            # Print with dithering
            if st.button("Print with Dithering", key="print_dithered"):
                grayscale, dithered = preper_image(text_image, printer_info['label_width'])
                print_image(dithered, printer_info=printer_info)
                st.success("Dithered creative text sent to printer!")
        
        # Save template option
        if st.button("Save as Template", key="save_template"):
            import json
            import os
            
            template = {
                "text": text,
                "font": selected_font_name,
                "effect": effect_type,
                "font_size": font_size,
                "colors": {
                    "text": text_color,
                    "background": bg_color
                }
            }
            
            # Save to templates directory
            os.makedirs("templates", exist_ok=True)
            template_name = st.text_input("Template Name", value=f"{effect_type}_{text[:10]}...")
            
            if template_name:
                template_path = f"templates/{template_name}.json"
                with open(template_path, 'w') as f:
                    json.dump(template, f, indent=2)
                st.success(f"Template saved as {template_path}")
```

## Required Changes

### 1. New Tab Module
Create `tabs/creative_text.py` with the above implementation.

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
    "Creative Text",  # Add this line
]
```

### 3. Utility Functions
Extend `image_utils.py` with text effect utilities:
```python
def apply_text_effect(text, font, effect_type, width, height):
    """Apply creative effect to text."""
    from PIL import ImageDraw
    import math
    
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    if effect_type == "wave":
        # Wave effect implementation
        amplitude = 15
        for i, char in enumerate(text):
            x = 20 + i * 30
            y = height // 2 + int(amplitude * math.sin(i * 0.3))
            draw.text((x, y), char, font=font, fill=(0, 0, 0))
    
    return image
```

## Integration Points

### Builds on Existing Label System
- Uses same font loading from `get_fonts()`
- Similar text input and processing
- Compatible with existing printing pipeline

### Enhanced Effects
- Wave, spiral, gradient, shadow effects
- Color customization
- Template saving for reuse

### Creative Applications
- Artistic text for posters and signs
- Decorative labels and tags
- Text-based art projects
- Combination with other features

## Creative Applications

### 1. Poetry & Literature
- Formatted poetry with visual effects
- Quote displays with artistic layouts
- Book excerpts with decorative text

### 2. Signage & Displays
- Event signage with eye-catching text
- Directional signs with creative fonts
- Informational displays with hierarchy

### 3. Educational Materials
- Vocabulary cards with visual aids
- Mnemonic devices with text effects
- Learning aids with color coding

### 4. Personal Expression
- Motivational quotes for workspaces
- Personalized gifts with custom text
- Journaling and scrapbooking elements

## Technical Considerations

### Font Compatibility
- TrueType and OpenType font support
- Fallback to system fonts
- Font size and spacing calculations

### Effect Performance
- Real-time preview generation
- Memory usage for complex effects
- Print quality with dithering

### User Experience
- Intuitive effect selection
- Real-time preview updates
- Template management system

## Testing Strategy

### Unit Tests
- Test text effect algorithms
- Verify font loading and rendering
- Check color conversion accuracy

### Integration Tests
- Test with various text inputs
- Verify printing functionality
- Check session state management

### User Testing
- Effect preview clarity
- Print quality assessment
- Template saving and loading

## Dependencies
- **Phase 1 Implementation** (Easiest)
- Builds on existing label.py foundation
- Uses established font system
- Minimal new dependencies

## Next Steps
1. Implement basic text effects
2. Add color customization
3. Include template system
4. Add more advanced effects
5. Integrate with other features