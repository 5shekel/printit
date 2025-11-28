"""Sticker Pro tab content - advanced image masking and processing with PDF support."""

import streamlit as st
import requests
import io
import os
from PIL import Image, ImageOps


def render(print_image, apply_threshold, add_border, apply_histogram_equalization, 
           resize_image_to_width, preper_image, label_width):
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
            mirror_checkbox = st.checkbox("Mirror Mask", value=False, key="sticker_pro_mirror")
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
            
            # Add target width in mm option
            target_width_mm = st.number_input("Target Width (mm)", min_value=0, value=0, key="sticker_pro_width")
            
            # Disable rotation if target width is specified
            rotate_disabled = target_width_mm > 0
            rotate_checkbox = st.checkbox("rotate 90deg", value=False, disabled=rotate_disabled, key="sticker_pro_rotate")
            if rotate_disabled and rotate_checkbox:
                st.info("Rotation disabled when target width is specified")
            
            # Apply target width resizing if specified
            if target_width_mm > 0:
                image = resize_image_to_width(image, target_width_mm)
            
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
                grayscale_image, dithered_image = preper_image(image, label_width=label_width)
                display_image = dithered_image if dither else grayscale_image
            else:  # Threshold
                threshold_percent = st.slider("Threshold (%)", 0, 100, 50, key="sticker_pro_threshold")
                threshold = int(threshold_percent * 255 / 100)
                display_image = apply_threshold(image, threshold)
                grayscale_image = image.convert("L")
            
            # Create a copy for display with border if needed
            preview_image = display_image.copy()
            if border_checkbox:
                preview_image = add_border(preview_image)
        
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
            if print_choice == "Original":
                print_image(grayscale_image, rotate=rotate, dither=dither)
            else:
                print_image(display_image, rotate=rotate, dither=False)
            st.success("Print job sent to printer!")
