"""Outline Stickers tab - Create stickers with outlines around figures using background removal."""

import logging
import streamlit as st
import os
import time
import tempfile
from PIL import Image
import io
import numpy as np
import cv2
from rembg import remove
from dataclasses import dataclass
from typing import Optional, Tuple

logger = logging.getLogger("sticker_factory.tabs.cutting_guides")


@dataclass
class OutlineParams:
    """Parameters for outline generation."""
    expansion_pixels: int = 5
    outline_thickness: int = 2
    outline_color: Tuple[int, int, int] = (0, 255, 0)  # BGR green
    shape: str = 'line'  # 'line' or 'marker'
    shape_spacing: int = 10
    shape_size: int = 3
    should_exclude_border: bool = True
    border_margin: int = 5
    shape_type: str = 'circle'
    marker_color: Optional[Tuple[int, int, int]] = None


def remove_background_in_memory(image_bytes):
    """
    Remove background from image bytes in memory.
    
    Args:
        image_bytes: Bytes of input image
    
    Returns:
        numpy.ndarray: Background-removed image with alpha channel (RGBA)
    """
    # Remove background (rembg automatically uses CPU if no GPU available)
    output_data = remove(image_bytes)
    
    # Convert bytes to numpy array
    nparr = np.frombuffer(output_data, np.uint8)
    bg_removed = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
    
    if bg_removed is None:
        raise ValueError("Failed to decode background-removed image")
    
    return bg_removed


def create_mask_from_alpha(image):
    """
    Create a binary mask from the alpha channel of an RGBA image.
    Returns mask where foreground (non-transparent) is white (255) and background is black (0).
    """
    if len(image.shape) == 2:
        # Grayscale image
        mask = image
    elif image.shape[2] == 4:
        # RGBA image - use alpha channel
        mask = image[:, :, 3]
    elif image.shape[2] == 3:
        # RGB image - convert to grayscale
        mask = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Threshold to create binary mask
        _, mask = cv2.threshold(mask, 1, 255, cv2.THRESH_BINARY)
    else:
        raise ValueError(f"Unsupported image shape: {image.shape}")
    
    # Ensure mask is binary (0 or 255)
    if mask.dtype != np.uint8:
        mask = mask.astype(np.uint8)
    
    return mask


def expand_mask(mask, expansion_pixels=5):
    """
    Expand/dilate a binary mask by specified number of pixels.
    """
    if expansion_pixels <= 0:
        return mask.copy()
    
    # Create kernel for dilation
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, 
                                      (2*expansion_pixels + 1, 2*expansion_pixels + 1))
    
    # Dilate the mask
    expanded_mask = cv2.dilate(mask, kernel, iterations=1)
    
    return expanded_mask


def draw_marker(image, x, y, size, marker_type='circle', angle=0):
    """
    Draw a marker at the specified position.
    """
    if marker_type == 'circle':
        cv2.circle(image, (x, y), size, 255, -1)
    elif marker_type == 'square':
        half = size
        cv2.rectangle(image, (x-half, y-half), (x+half, y+half), 255, -1)
    elif marker_type == 'triangle':
        # Equilateral triangle pointing up
        pts = np.array([
            [x, y - size],  # Top
            [x - size, y + size],  # Bottom left
            [x + size, y + size]   # Bottom right
        ], np.int32)
        cv2.fillPoly(image, [pts], 255)
    elif marker_type == 'diamond':
        # Diamond shape
        pts = np.array([
            [x, y - size],  # Top
            [x + size, y],  # Right
            [x, y + size],  # Bottom
            [x - size, y]   # Left
        ], np.int32)
        cv2.fillPoly(image, [pts], 255)
    elif marker_type == 'star':
        # Simple 5-point star
        pts = []
        for i in range(5):
            angle_rad = np.pi/2 + i * 2*np.pi/5
            # Outer point
            pts.append([x + size * np.cos(angle_rad), y - size * np.sin(angle_rad)])
            # Inner point
            angle_rad += np.pi/5
            pts.append([x + size/2 * np.cos(angle_rad), y - size/2 * np.sin(angle_rad)])
        pts = np.array(pts, np.int32)
        cv2.fillPoly(image, [pts], 255)
    elif marker_type == 'cross':
        # Plus sign
        cv2.line(image, (x-size, y), (x+size, y), 255, 2)
        cv2.line(image, (x, y-size), (x, y+size), 255, 2)
    else:
        # Default to circle
        cv2.circle(image, (x, y), size, 255, -1)


def get_mask_outline(mask, outline_thickness=2, shape='line', shape_spacing=10, shape_size=3, 
                     exclude_border=True, border_margin=5, shape_type='circle'):
    """
    Extract the outline of a binary mask.
    """
    # Find contours in the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Create empty image for outline
    outline = np.zeros_like(mask)
    
    # Get image dimensions
    height, width = mask.shape[:2]
    
    if shape == 'marker':
        # Draw markers along each contour
        for contour in contours:
            # Approximate the contour to reduce points
            epsilon = 0.001 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Flatten the contour points
            points = approx.reshape(-1, 2)
            
            # Draw markers along the contour with specified spacing
            for i in range(len(points)):
                # Calculate distance between consecutive points
                if i < len(points) - 1:
                    p1 = points[i]
                    p2 = points[i + 1]
                else:
                    p1 = points[i]
                    p2 = points[0]  # Close the loop
                
                # Interpolate points along the line segment
                distance = np.linalg.norm(p2 - p1)
                if distance > 0:
                    num_shapes = int(distance / shape_spacing)
                    if num_shapes > 0:
                        for j in range(num_shapes + 1):
                            t = j / max(num_shapes, 1)
                            x = int(p1[0] * (1 - t) + p2[0] * t)
                            y = int(p1[1] * (1 - t) + p2[1] * t)
                            
                            # Check if marker is too close to border
                            if exclude_border:
                                if (x < border_margin or x >= width - border_margin or 
                                    y < border_margin or y >= height - border_margin):
                                    continue
                            
                            draw_marker(outline, x, y, shape_size, shape_type)
    else:
        # Draw solid contour with specified thickness
        cv2.drawContours(outline, contours, -1, 255, outline_thickness)
        
        # If exclude_border is True, remove outline near borders
        if exclude_border:
            border_mask = np.zeros((height, width), dtype=np.uint8)
            border_mask[border_margin:height-border_margin, border_margin:width-border_margin] = 255
            outline = cv2.bitwise_and(outline, border_mask)
    
    return outline


def overlay_outline_on_image(original_image, outline_mask, outline_color=(0, 255, 0), 
                            marker_color=None, shape='line'):
    """
    Overlay outline on original image.
    """
    # Convert outline mask to 3-channel if needed
    if len(original_image.shape) == 3 and original_image.shape[2] == 3:
        result = original_image.copy()
        
        # Use marker color if specified and shape is marker, otherwise use outline color
        color = marker_color if (marker_color is not None and shape == 'marker') else outline_color
        
        # Create colored outline
        colored_outline = np.zeros_like(original_image)
        colored_outline[outline_mask > 0] = color
        
        # Blend outline with original image (simple binary replacement)
        result[outline_mask > 0] = colored_outline[outline_mask > 0]
        
        return result
    else:
        raise ValueError("Original image must be 3-channel BGR")


def fetch_image_from_url(url):
    """Validate and fetch image from URL."""
    if not url.startswith('https://'):
        st.error('Only HTTPS URLs are allowed for security')
        return None
        
    try:
        import requests
        from io import BytesIO
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Verify content type is an image
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            st.error('URL does not point to a valid image')
            return None
            
        return Image.open(BytesIO(response.content)).convert("RGB")
    except Exception as e:
        st.error(f'Error fetching image: {str(e)}')
        return None


def render(printer_info, preper_image, print_image, apply_threshold):
    """Render the Outline Stickers tab."""
    st.subheader(":scissors: Outline Stickers")
    st.write("Create stickers with custom outlines around figures")

    # Image loading logic
    image_to_process = None
    
    # Input selection
    input_method = st.radio("Select Image Source", ["Upload", "URL"], horizontal=True)

    if input_method == "Upload":
        uploaded_file = st.file_uploader("Choose an image", type=["png", "jpg", "jpeg", "webp", "pdf"])
        if uploaded_file:
            if uploaded_file.type == "application/pdf":
                try:
                    import fitz
                    uploaded_file.seek(0)
                    pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                    page = pdf_document.load_page(0)
                    pix = page.get_pixmap(dpi=150)
                    image_to_process = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
                except Exception as e:
                    st.error(f"Error processing PDF: {e}")
            else:
                image_to_process = Image.open(uploaded_file).convert("RGB")

    elif input_method == "URL":
        image_url = st.text_input("Enter HTTPS image URL")
        if image_url:
            image_to_process = fetch_image_from_url(image_url)

    if image_to_process:
        # Configuration UI
        st.sidebar.markdown("### Outline Settings")
        
        expansion = st.sidebar.slider("Expansion (px)", 0, 50, 10, key="cg_expansion")
        shape_type_ui = st.sidebar.selectbox("Outline Style", ["Solid Line", "Markers"], key="cg_outline_style")
        
        params = OutlineParams(expansion_pixels=expansion)
        
        if shape_type_ui == "Solid Line":
            params.shape = "line"
            params.outline_thickness = st.sidebar.slider("Thickness", 1, 20, 2, key="cg_thickness")
        else:
            params.shape = "marker"
            params.shape_type = st.sidebar.selectbox("Marker Type", 
                                                   ['circle', 'square', 'triangle', 'diamond', 'star', 'cross'], key="cg_marker_type")
            params.shape_size = st.sidebar.slider("Marker Size", 1, 30, 5, key="cg_marker_size")
            params.shape_spacing = st.sidebar.slider("Marker Spacing", 5, 100, 20, key="cg_marker_spacing")

        # Color Selection
        def hex_to_bgr(hex_color):
            hex_color = hex_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return (b, g, r)

        color_hex = st.sidebar.color_picker("Outline Color", "#00FF00", key="cg_color")
        params.outline_color = hex_to_bgr(color_hex)

        st.sidebar.markdown("### Advanced")
        params.should_exclude_border = st.sidebar.checkbox("Exclude Border", value=True, key="cg_exclude_border")
        if params.should_exclude_border:
            params.border_margin = st.sidebar.slider("Border Margin", 0, 100, 10, key="cg_border_margin")

        # Processing section
        if st.button("Generate Preview", key="cg_gen_preview"):
            with st.spinner("Removing background and generating outline..."):
                try:
                    # Convert PIL to BGR for OpenCV
                    cv_img = cv2.cvtColor(np.array(image_to_process), cv2.COLOR_RGB2BGR)
                    
                    # 1. Background removal
                    img_bytes = io.BytesIO()
                    image_to_process.save(img_bytes, format='PNG')
                    bg_removed = remove_background_in_memory(img_bytes.getvalue())
                    
                    # Ensure same dimensions
                    bg_removed = cv2.resize(bg_removed, (cv_img.shape[1], cv_img.shape[0]))
                    
                    # 2. Mask creation
                    mask = create_mask_from_alpha(bg_removed)
                    
                    # 3. Expand mask
                    expanded_mask = expand_mask(mask, params.expansion_pixels)
                    
                    # 4. Generate outline
                    outline_mask = get_mask_outline(
                        expanded_mask, 
                        params.outline_thickness, 
                        params.shape, 
                        params.shape_spacing, 
                        params.shape_size, 
                        params.should_exclude_border, 
                        params.border_margin, 
                        params.shape_type
                    )
                    
                    # 5. Overlay
                    result_bgr = overlay_outline_on_image(cv_img, outline_mask, params.outline_color, shape=params.shape)
                    
                    # Convert back to RGB for Streamlit/PIL
                    result_rgb = cv2.cvtColor(result_bgr, cv2.COLOR_BGR2RGB)
                    st.session_state.outline_result = Image.fromarray(result_rgb)
                    
                except Exception as e:
                    st.error(f"Error during processing: {e}")
                    logger.error(f"Outline generation error: {e}", exc_info=True)

        if 'outline_result' in st.session_state:
            result_img = st.session_state.outline_result
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.image(image_to_process, caption="Original", use_container_width=True)
            with col_b:
                st.image(result_img, caption="With Outline", use_container_width=True)

            # Print controls
            st.divider()
            st.subheader("Print Controls")
            
            p_col1, p_col2 = st.columns(2)
            with p_col1:
                dither_opt = st.checkbox("Dither", value=True, key="outline_dither")
                rotate_opt = st.checkbox("Rotate 90", key="outline_rotate")
            
            outline_copies = st.number_input("Copies", min_value=1, max_value=100, value=1, key="outline_copies")
            
            if st.button("Print Outlined Sticker", use_container_width=True, key="outline_print_btn"):
                with st.spinner("Sending to printer..."):
                    rotate_val = 90 if rotate_opt else 0
                    for _ in range(outline_copies):
                        print_image(result_img, printer_info=printer_info, rotate=rotate_val, dither=dither_opt)
                        time.sleep(0.5)
                    st.success("Sent to printer!")
