"""Sticker Pro tab content - advanced image masking and processing with PDF support."""

import streamlit as st
import requests
import io
import os
from PIL import Image, ImageOps, ImageDraw, ImageFont


def make_meme_text(image, top_text, bottom_text, font_size=20, outline_width=3):
    """Add Impact-style meme text to top and bottom of image."""
    if not top_text and not bottom_text:
        return image
    
    # Create a copy to draw on
    meme_image = image.copy()
    draw = ImageDraw.Draw(meme_image)
    
    # Use provided font size
    font_path = None
    
    # Try common Impact font locations
    potential_paths = [
        "fonts/Impact.ttf",
        "C:/Windows/Fonts/impact.ttf",
        "/System/Library/Fonts/Impact.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    
    for path in potential_paths:
        if os.path.exists(path):
            font_path = path
            break
    
    try:
        if font_path:
            font = ImageFont.truetype(font_path, font_size)
        else:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    
    # Text color: white with black outline (classic meme style)
    text_color = "white"
    outline_color = "black"
    
    def draw_text_with_outline(draw, text, position, font, text_color, outline_color, outline_width):
        """Draw text with outline effect."""
        x, y = position
        # Get text bounding box for proper centering
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center text 
        x = x - text_width // 2
        y = y - text_height // 2
        
        # Draw outline
        for adj_x in range(-outline_width, outline_width + 1):
            for adj_y in range(-outline_width, outline_width + 1):
                if adj_x != 0 or adj_y != 0:
                    draw.text((x + adj_x, y + adj_y), text, font=font, fill=outline_color)
        # Draw main text
        draw.text((x, y), text, font=font, fill=text_color)
    
    # Draw top text
    if top_text:
        top_y = int(meme_image.height * 0.10)
        center_x = meme_image.width // 2
        draw_text_with_outline(draw, top_text.upper(), (center_x, top_y), font, text_color, outline_color, outline_width)
    
    # Draw bottom text
    if bottom_text:
        bottom_y = int(meme_image.height * 0.85)
        center_x = meme_image.width // 2
        draw_text_with_outline(draw, bottom_text.upper(), (center_x, bottom_y), font, text_color, outline_color, outline_width)
    
    return meme_image


def render(print_image,printer_info, apply_threshold, add_border, apply_histogram_equalization, 
           resize_image_to_width, preper_image, label_dir):
    """Render the Sticker Pro tab."""
    st.subheader(":printer: a sticker for pros")
    
    # Allow file upload or URL input
    uploaded_file = st.file_uploader(
        "Choose an image or PDF for processing...", 
        type=["jpg", "jpeg", "png", "gif", "webp", "bmp", "pdf"],
        key="sticker_pro_uploader"
    )
    image_url = st.text_input("Or enter an HTTPS image URL to fetch and process", key="sticker_pro_url")
    
    # Initialize image variable
    image = None
    
    try:
        if uploaded_file is not None:
            # Handle PDF files
            if uploaded_file.type == "application/pdf":
                try:
                    import fitz  # PyMuPDF
                    
                    st.info("PDF file detected. Converting the first page to an image.")
                    dpi_selected = st.selectbox("Select the DPI for the conversion", [72, 92, 150, 300, 600], index=1, key="sticker_pro_pdf_dpi")
                    
                    # Open the PDF file
                    pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                    
                    # Convert the first page to an image
                    page = pdf_document.load_page(0)
                    pix = page.get_pixmap(dpi=dpi_selected)
                    image = Image.open(io.BytesIO(pix.tobytes("png")))
                    
                except ImportError:
                    st.error("PyMuPDF (fitz) is not installed. Install it with: pip install pymupdf")
                    st.stop()
                except Exception as e:
                    st.error(f"Error converting PDF: {str(e)}")
                    st.stop()
            else:
                # Process regular image file
                image = Image.open(uploaded_file)
        elif image_url:
            # Validate and fetch image from URL
            if not image_url.startswith('https://'):
                st.error('Only HTTPS URLs are allowed for security')
            else:
                try:
                    response = requests.get(image_url, timeout=10)
                    response.raise_for_status()
                    
                    # Verify content type is an image
                    content_type = response.headers.get('content-type', '')
                    if not content_type.startswith('image/'):
                        st.error('URL does not point to a valid image')
                    else:
                        image = Image.open(io.BytesIO(response.content))
                except requests.exceptions.RequestException as e:
                    st.error(f'Error fetching image: {str(e)}')
                except Exception as e:
                    st.error(f'Error processing image: {str(e)}')
    except Exception as e:
        st.error(f'Error loading image: {str(e)}')
        st.info("Please try another image or format")
    
    if image is not None:
        if image.mode == "RGBA":
            # Handle transparency
            background = Image.new("RGBA", image.size, "white")
            image = Image.alpha_composite(background, image)
        image = image.convert("RGB")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            print_choice = st.radio("Choose which image to print/save:", ("Original", "Threshold"), key="sticker_pro_choice")
            
            st.text("General options:")
            mirror_checkbox = st.checkbox("Mirror Image", value=False, key="sticker_pro_mirror")
            invert_checkbox = st.checkbox("Invert Image", value=False, key="sticker_pro_invert")
            border_checkbox = st.checkbox(
                "Show border in preview", 
                value=True, 
                key="sticker_pro_border",
                help="Adds a border in the preview to help visualize boundaries (not printed)"
            )
            equalize_checkbox = st.checkbox(
                "Apply Histogram Equalization", 
                value=False, 
                key="sticker_pro_equalize",
                help="Enhance image contrast"
            )
            meme_checkbox = st.checkbox(
                "Make it a meme!", 
                value=False, 
                key="sticker_pro_meme",
                help="Adds Impact font style text at top and bottom of image"
            )
        
            
            # Add target width in mm option
            target_width_mm = st.number_input("Target Width (mm)", min_value=0, value=0, key="sticker_pro_width")
            
            # Disable rotation if target width is specified
            rotate_disabled = target_width_mm > 0
            rotate_checkbox = st.checkbox("rotate 90deg", value=False, disabled=rotate_disabled, key="sticker_pro_rotate")
            if rotate_disabled and rotate_checkbox:
                st.info("Rotation disabled when target width is specified")
            
            # Apply target width resizing if specified
            if target_width_mm > 0:
                image = resize_image_to_width(image, target_width_mm, printer_info['label_width'])
            
            if mirror_checkbox:
                image = ImageOps.mirror(image)
            
            if invert_checkbox:
                image = ImageOps.invert(image)
            
            black_point = 0
            white_point = 255
            if equalize_checkbox:
                st.text("Levels Adjustment:")
                col_levels1, col_levels2 = st.columns(2)
                with col_levels1:
                    black_point = st.slider("Black Point", 0, 255, 0, key="sticker_pro_black_point")
                with col_levels2:
                    white_point = st.slider("White Point", 0, 255, 255, key="sticker_pro_white_point")
            
            # Apply histogram equalization if selected
            if equalize_checkbox:
                image = apply_histogram_equalization(image, black_point, white_point)
            
            # Process image based on choice
            dither = False
            grayscale_image = None
            dithered_image = None
            if print_choice == "Original":
                dither = st.checkbox("Dither - approximate grey tones with dithering", value=True, key="sticker_pro_dither")
                grayscale_image, dithered_image = preper_image(image, label_width=printer_info['label_width'])
                display_image = dithered_image if dither else grayscale_image
            else:  # Threshold
                threshold_percent = st.slider("Threshold (%)", 0, 100, 50, key="sticker_pro_threshold")
                threshold = int(threshold_percent * 255 / 100)
                display_image = apply_threshold(image, threshold)
                grayscale_image = image.convert("L")
            
            # Get meme text if checkbox is enabled
            meme_top_text = ""
            meme_bottom_text = ""
            if meme_checkbox:
                meme_top_text = st.text_input("Top Text", key="sticker_pro_meme_top")
                meme_bottom_text = st.text_input("Bottom Text", key="sticker_pro_meme_bottom")
                meme_font_size = st.slider("Meme Font Size", 10, 100, 20, key="sticker_pro_meme_font_size_final")
                meme_outline_width = st.slider("Meme Outline Width", 1, 10, 3, key="sticker_pro_meme_outline_width")

            # Create a copy for display with border if needed
            preview_image = display_image.copy()
            if border_checkbox:
                preview_image = add_border(preview_image)

            if meme_checkbox and (meme_top_text or meme_bottom_text):
                print(type(meme_outline_width))
                print(type(meme_font_size))
                preview_image = make_meme_text(preview_image, meme_top_text, meme_bottom_text, meme_font_size, meme_outline_width)
        
        with col2:
            st.image(preview_image, caption="Preview", width='stretch')
        
        print_button_label = f"Print {print_choice} Image"
        if print_choice == "Original" and dither:
            print_button_label += ", Dithering"
        if rotate_checkbox and not rotate_disabled:
            print_button_label += ", Rotated 90°"
        if mirror_checkbox:
            print_button_label += ", Mirrored"
        if invert_checkbox:
            print_button_label += ", Inverted"
        if target_width_mm > 0:
            print_button_label += f", Width: {target_width_mm}mm"
        
        if st.button(print_button_label, key="sticker_pro_print"):
            rotate = 90 if (rotate_checkbox and not rotate_disabled) else 0
            
            # Apply meme text to the image being printed if enabled
            print_display_image = display_image.copy()
            if meme_checkbox and (meme_top_text or meme_bottom_text):
                print_display_image = make_meme_text(print_display_image, meme_top_text, meme_bottom_text, meme_font_size, meme_outline_width)
            
            if print_choice == "Original":
                print_image(print_display_image, printer_info, rotate=rotate, dither=dither)
            else:
                print_image(print_display_image, printer_info, rotate=rotate, dither=False)
            st.success("Print job sent to printer!")
