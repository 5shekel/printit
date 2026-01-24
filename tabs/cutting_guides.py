"""Cutting Guides tab content."""

import logging
import streamlit as st
import os
from PIL import Image, ImageDraw, ImageFont
import io

logger = logging.getLogger("sticker_factory.tabs.cutting_guides")


def add_cutting_guides(image, guide_type="dashed", guide_spacing=15, cut_margin=5, add_registration=True):
    """
    Add cutting guides around the main figure in image.
    
    Args:
        image: PIL Image to add guides to
        guide_type: "dashed", "dotted", "scissors_icon", "perforated"
        guide_spacing: Spacing between guide marks in pixels
        cut_margin: Distance from figure edge to cut line in pixels
        add_registration: Whether to add registration marks
    
    Returns:
        PIL Image with cutting guides added around the figure
    """
    # Import the improved cutting guide function from image_utils
    from image_utils import add_cutting_guide
    
    # Use the improved function which detects the figure first
    result = add_cutting_guide(
        image=image,
        guide_type=guide_type,
        spacing=guide_spacing,
        margin=cut_margin,
        background_threshold=240
    )
    
    # Add registration marks if requested (on top of the result)
    if add_registration:
        from PIL import ImageDraw
        
        draw = ImageDraw.Draw(result)
        mark_size = 8
        
        # Find figure bounds to place registration marks correctly
        from image_utils import find_figure_bounds
        bounds = find_figure_bounds(image, background_threshold=240)
        
        if bounds is None:
            bounds = (0, 0, image.width, image.height)
        
        min_x, min_y, max_x, max_y = bounds
        
        # Calculate positions with margin
        guide_left = max(0, min_x - cut_margin)
        guide_top = max(0, min_y - cut_margin)
        guide_right = min(image.width, max_x + cut_margin)
        guide_bottom = min(image.height, max_y + cut_margin)
        
        # Corner registration marks (crosshairs)
        # Top-left
        draw.line([(guide_left - mark_size, guide_top), (guide_left + mark_size, guide_top)], fill=0, width=1)
        draw.line([(guide_left, guide_top - mark_size), (guide_left, guide_top + mark_size)], fill=0, width=1)
        
        # Top-right
        draw.line([(guide_right - mark_size, guide_top), (guide_right + mark_size, guide_top)], fill=0, width=1)
        draw.line([(guide_right, guide_top - mark_size), (guide_right, guide_top + mark_size)], fill=0, width=1)
        
        # Bottom-left
        draw.line([(guide_left - mark_size, guide_bottom), (guide_left + mark_size, guide_bottom)], fill=0, width=1)
        draw.line([(guide_left, guide_bottom - mark_size), (guide_left, guide_bottom + mark_size)], fill=0, width=1)
        
        # Bottom-right
        draw.line([(guide_right - mark_size, guide_bottom), (guide_right + mark_size, guide_bottom)], fill=0, width=1)
        draw.line([(guide_right, guide_bottom - mark_size), (guide_right, guide_bottom + mark_size)], fill=0, width=1)
    
    return result


def render(printer_info, preper_image, print_image, apply_threshold):
    """Render the Cutting Guides tab."""
    st.subheader(":scissors: Cutting Guides")
    st.write("Add cutting lines and registration marks for craft projects")
    
    # Input options
    input_method = st.radio("Create from", 
                           ["Upload Image", "Use Label Text", "Create Shape"],
                           horizontal=True)
    
    if input_method == "Upload Image":
        # Image upload
        uploaded_file = st.file_uploader("Choose an image", type=['png', 'jpg', 'jpeg'])
        
        if uploaded_file:
            image = Image.open(uploaded_file).convert("RGB")
            st.image(image, caption="Original Image", use_container_width=True)
            
            # Store original for processing
            st.session_state.original_image = image
    
    elif input_method == "Use Label Text":
        # Use existing label functionality
        st.info("Enter text to create a label with cutting guides")
        
        text = st.text_area("Label Text", "CUT ME OUT!")
        
        if st.button("Create Text Label", key="create_text_label"):
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
            elif shape_type == "Triangle":
                draw.polygon([(shape_width//2, 10), 
                             (10, shape_height-10), 
                             (shape_width-10, shape_height-10)], 
                            fill=fill_rgb, outline=outline_rgb, width=3)
            elif shape_type == "Star":
                # Simple star shape
                points = []
                for i in range(5):
                    angle = 4 * 3.14159 * i / 5
                    x = shape_width//2 + shape_width//3 * 0.5 * (1 if i % 2 == 0 else 0.5) * (-1 if i % 2 == 0 else 1) * (1 if i < 2.5 else -1)
                    y = shape_height//2 + shape_height//3 * 0.5 * (1 if i % 2 == 0 else 0.5) * (-1 if i % 2 == 0 else 1) * (1 if i < 2.5 else -1)
                    points.append((x, y))
                draw.polygon(points, fill=fill_rgb, outline=outline_rgb, width=3)
            else:  # Heart
                # Simple heart shape
                draw.ellipse([10, 10, shape_width//2, shape_height//2], fill=fill_rgb, outline=outline_rgb)
                draw.ellipse([shape_width//2, 10, shape_width-10, shape_height//2], fill=fill_rgb, outline=outline_rgb)
                draw.polygon([(10, shape_height//3), 
                             (shape_width-10, shape_height//3),
                             (shape_width//2, shape_height-10)], 
                            fill=fill_rgb, outline=outline_rgb, width=3)
            
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
                # Prepare image for printing (resize + dither)
                grayscale, dithered = preper_image(result_image, printer_info['label_width'])
                print_image(dithered, printer_info=printer_info)
                st.success("Image with cutting guides sent to printer!")
        
        with col2:
            # Print without guides (original)
            if st.button("Print Original (No Guides)", key="print_original"):
                # Prepare original image for printing
                grayscale, dithered = preper_image(st.session_state.original_image, printer_info['label_width'])
                print_image(dithered, printer_info=printer_info)
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
                    grayscale, dithered = preper_image(final_image, printer_info['label_width'])
                    print_image(dithered, printer_info=printer_info)
                    st.success("Thresholded image with guides sent to printer!")
