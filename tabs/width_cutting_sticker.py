"""Width Cutting Sticker tab content."""

import logging
import streamlit as st
import os
from PIL import Image
import io

logger = logging.getLogger("sticker_factory.tabs.width_cutting_sticker")


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


def render(preper_image, print_image, printer_info):
    """Render the Width Cutting Sticker tab."""
    st.subheader(":scissors: Width Cutting Sticker")
    st.write("Upload an image and specify how many equal-width strips to cut it into. Each strip will be printed as a separate sticker.")

    # Check if there's a selected image from history
    if 'selected_image_path' in st.session_state:
        image_path = st.session_state.selected_image_path
        try:
            image_to_process = Image.open(image_path).convert("RGB")
            grayscale_image, dithered_image = preper_image(image_to_process, label_width=printer_info['label_width'])
            
            st.info(f"Image loaded from history: {os.path.basename(image_path)}")
            
            # Create checkboxes for rotation and dithering
            col1, col2 = st.columns(2)
            with col1:
                dither_checkbox = st.checkbox(
                    "Dither - _use for high detail, true by default_", value=True,
                    key="dither_history_width"
                )
            with col2:
                rotate_checkbox = st.checkbox("Rotate - _90 degrees_", key="rotate_history_width")

            # Display image based on checkbox status
            if dither_checkbox:
                st.image(dithered_image, caption="Resized and Dithered Image")
            else:
                st.image(image_to_process, caption="Original Image")

            # Print button
            button_text = "Print "
            if rotate_checkbox:
                button_text += "Rotated "
            if dither_checkbox:
                button_text += "Dithered "
            button_text += "Image"

            if st.button(button_text, key="print_history_width"):
                rotate_value = 90 if rotate_checkbox else 0
                dither_value = dither_checkbox
                print_image(image_to_process, printer_info, rotate=rotate_value, dither=dither_value)
                
            if st.button("Clear Selection"):
                del st.session_state.selected_image_path
                st.rerun()
                
        except Exception as e:
            st.error(f"Error loading image: {str(e)}")
            del st.session_state.selected_image_path
            st.rerun()

    # Allow the user to upload an image or PDF
    uploaded_image = st.file_uploader(
        "Choose an image file or PDF to print", type=["png", "jpg", "gif", "webp", "pdf"],
        key="width_cutting_file_uploader"
    )
    
    # Or fetch from URL
    image_url = st.text_input("Or enter an HTTPS image URL to fetch and print")

    # Process uploaded file or URL
    if uploaded_image is not None:
        image_to_process = None
        original_filename_without_extension = os.path.splitext(uploaded_image.name)[0]
        
        # Handle PDF files
        if uploaded_image.type == "application/pdf":
            try:
                import fitz  # PyMuPDF
                
                st.info("PDF file detected. Converting the first page to an image.")
                dpi_selected = st.selectbox("Select the DPI for the conversion", [72, 92, 150, 300, 600], index=1)
                
                # Open the PDF file
                pdf_document = fitz.open(stream=uploaded_image.read(), filetype="pdf")
                
                # Convert the first page to an image
                page = pdf_document.load_page(0)
                pix = page.get_pixmap(dpi=dpi_selected)
                image_to_process = Image.open(io.BytesIO(pix.tobytes("png")))
                
            except ImportError:
                st.error("PyMuPDF (fitz) is not installed. Install it with: pip install pymupdf")
                st.stop()
            except Exception as e:
                st.error(f"Error converting PDF: {str(e)}")
                st.stop()
        else:
            # Convert the uploaded file to a PIL Image
            image_to_process = Image.open(uploaded_image).convert("RGB")

        if image_to_process:
            # Store the original image in session state for width cutting
            st.session_state.original_image_for_cutting = image_to_process
            
            # Get image dimensions
            image_width = image_to_process.width
            image_height = image_to_process.height
            
            st.success(f"Image loaded: {image_width} × {image_height} pixels")
            
            # Strip cutting input
            st.subheader("Strip Cutting Settings")
            
            col1, col2 = st.columns(2)
            with col1:
                # Number of strips (1 to reasonable max, e.g., min(20, image_width))
                max_strips = min(20, image_width)  # Reasonable maximum
                num_strips = st.slider(
                    "Number of Equal Strips",
                    min_value=1,
                    max_value=max_strips,
                    value=min(3, max_strips),  # Default to 3 or max
                    help=f"Cut image into N equal-width strips (1 to {max_strips})"
                )
            
            with col2:
                # Calculate and show strip width info
                strip_width = image_width // num_strips
                remainder = image_width % num_strips
                actual_strip_width = strip_width + (1 if remainder > 0 else 0)
                st.metric("Strip Width", f"{strip_width} px")
                if remainder > 0:
                    st.caption(f"First {remainder} strips: {actual_strip_width}px")
                    st.caption(f"Remaining strips: {strip_width}px")
                st.metric("Total Strips", f"{num_strips}")
            
            # Show visual indicator of strip cuts
            from image_utils import add_strip_cut_indicators
            indicator_image = add_strip_cut_indicators(image_to_process, num_strips)
            st.image(indicator_image, caption=f"Cut into {num_strips} equal strips", use_container_width=True)
            
            # Process the image for preview
            grayscale_image, dithered_image = preper_image(image_to_process, label_width=printer_info['label_width'])
            
            # Create checkboxes for rotation and dithering (dither default to True) inline
            col1, col2 = st.columns(2)
            with col1:
                dither_checkbox = st.checkbox(
                    "Dither - _use for high detail, true by default_", value=True,
                    key="width_cutting_dither"
                )
            with col2:
                rotate_checkbox = st.checkbox("Rotate - _90 degrees_", key="width_cutting_rotate")

            # Display image based on checkbox status
            try:
                if dither_checkbox:
                    st.image(dithered_image, caption="Resized and Dithered Image")
                else:
                    st.image(image_to_process, caption="Original Image")
            
                # Create 'temp' directory if it doesn't exist
                os.makedirs("temp", exist_ok=True)
                
                # Save original image
                original_image_path = os.path.join(
                    "temp", original_filename_without_extension + "_original.png"
                )
                image_to_process.save(original_image_path, "PNG")
            except ValueError as e:
                logger.error(f"Error displaying image: {str(e)}")
            
            # Print buttons for strips
            st.subheader("Print Strips")
            
            # Create strips
            from image_utils import cut_image_into_strips
            strips = cut_image_into_strips(image_to_process, num_strips)
            
            # Individual strip buttons in columns
            st.write(f"Print individual strips (1 to {num_strips}):")
            
            # Create columns for strip buttons (max 4 per row)
            cols_per_row = 4
            for strip_idx in range(0, num_strips, cols_per_row):
                cols = st.columns(cols_per_row)
                for col_idx, col in enumerate(cols):
                    strip_num = strip_idx + col_idx + 1
                    if strip_num <= num_strips:
                        with col:
                            if st.button(f"Strip {strip_num}", key=f"print_strip_{strip_num}"):
                                try:
                                    strip_image = strips[strip_num - 1]
                                    rotate_value = 90 if rotate_checkbox else 0
                                    dither_value = dither_checkbox
                                    print_image(strip_image, printer_info, rotate=rotate_value, dither=dither_value)
                                    st.success(f"Strip {strip_num} sent to printer!")
                                except Exception as e:
                                    st.error(f"Error printing strip {strip_num}: {str(e)}")
            
            # Print all strips button
            if st.button("Print All Strips", key="print_all_strips"):
                try:
                    rotate_value = 90 if rotate_checkbox else 0
                    dither_value = dither_checkbox
                    
                    for i, strip_image in enumerate(strips, 1):
                        print_image(strip_image, printer_info, rotate=rotate_value, dither=dither_value)
                        st.success(f"Strip {i}/{num_strips} sent to printer!")
                        
                        # Small delay between prints (except after last)
                        if i < num_strips:
                            import time
                            time.sleep(2)
                    
                    st.balloons()
                    st.success(f"All {num_strips} strips printed successfully!")
                    
                except Exception as e:
                    st.error(f"Error printing strips: {str(e)}")
            
            # Print original (uncut) button
            if st.button("Print Original (Uncut)", key="print_original_uncut"):
                rotate_value = 90 if rotate_checkbox else 0
                dither_value = dither_checkbox
                print_image(image_to_process, printer_info, rotate=rotate_value, dither=dither_value)
                st.success("Original (uncut) image sent to printer!")
        
    elif image_url:
        # Try to fetch and process image from URL
        image_to_process = fetch_image_from_url(image_url)
        if image_to_process:
            # Store the original image in session state for width cutting
            st.session_state.original_image_for_cutting = image_to_process
            
            # Get image dimensions
            image_width = image_to_process.width
            image_height = image_to_process.height
            
            st.success(f"Image loaded from URL: {image_width} × {image_height} pixels")
            
            # Strip cutting input for URL image
            st.subheader("Strip Cutting Settings")
            
            col1, col2 = st.columns(2)
            with col1:
                # Number of strips (1 to reasonable max, e.g., min(20, image_width))
                max_strips = min(20, image_width)  # Reasonable maximum
                num_strips = st.slider(
                    "Number of Equal Strips",
                    min_value=1,
                    max_value=max_strips,
                    value=min(3, max_strips),  # Default to 3 or max
                    help=f"Cut image into N equal-width strips (1 to {max_strips})",
                    key="url_num_strips"
                )
            
            with col2:
                # Calculate and show strip width info
                strip_width = image_width // num_strips
                remainder = image_width % num_strips
                actual_strip_width = strip_width + (1 if remainder > 0 else 0)
                st.metric("Strip Width", f"{strip_width} px")
                if remainder > 0:
                    st.caption(f"First {remainder} strips: {actual_strip_width}px")
                    st.caption(f"Remaining strips: {strip_width}px")
                st.metric("Total Strips", f"{num_strips}")
            
            # Show visual indicator of strip cuts
            from image_utils import add_strip_cut_indicators
            indicator_image = add_strip_cut_indicators(image_to_process, num_strips)
            st.image(indicator_image, caption=f"Cut into {num_strips} equal strips", use_container_width=True)
            
            # Process the fetched image
            grayscale_image, dithered_image = preper_image(image_to_process, label_width=printer_info['label_width'])
            
            # Create checkboxes for rotation and dithering
            col1, col2 = st.columns(2)
            with col1:
                dither_checkbox = st.checkbox(
                    "Dither - _use for high detail, true by default_", value=True,
                    key="dither_url_width"
                )
            with col2:
                rotate_checkbox = st.checkbox("Rotate - _90 degrees_", key="rotate_url_width")

            # Display image based on checkbox status
            if dither_checkbox:
                st.image(dithered_image, caption="Resized and Dithered Image")
            else:
                st.image(image_to_process, caption="Original Image")

            # Print buttons for URL image strips
            st.subheader("Print Strips")
            
            # Create strips for URL image
            from image_utils import cut_image_into_strips
            strips = cut_image_into_strips(image_to_process, num_strips)
            
            # Individual strip buttons in columns
            st.write(f"Print individual strips (1 to {num_strips}):")
            
            # Create columns for strip buttons (max 4 per row)
            cols_per_row = 4
            for strip_idx in range(0, num_strips, cols_per_row):
                cols = st.columns(cols_per_row)
                for col_idx, col in enumerate(cols):
                    strip_num = strip_idx + col_idx + 1
                    if strip_num <= num_strips:
                        with col:
                            if st.button(f"Strip {strip_num}", key=f"print_strip_url_{strip_num}"):
                                try:
                                    strip_image = strips[strip_num - 1]
                                    rotate_value = 90 if rotate_checkbox else 0
                                    dither_value = dither_checkbox
                                    print_image(strip_image, printer_info, rotate=rotate_value, dither=dither_value)
                                    st.success(f"Strip {strip_num} sent to printer!")
                                except Exception as e:
                                    st.error(f"Error printing strip {strip_num}: {str(e)}")
            
            # Print all strips button
            if st.button("Print All Strips", key="print_all_strips_url"):
                try:
                    rotate_value = 90 if rotate_checkbox else 0
                    dither_value = dither_checkbox
                    
                    for i, strip_image in enumerate(strips, 1):
                        print_image(strip_image, printer_info, rotate=rotate_value, dither=dither_value)
                        st.success(f"Strip {i}/{num_strips} sent to printer!")
                        
                        # Small delay between prints (except after last)
                        if i < num_strips:
                            import time
                            time.sleep(2)
                    
                    st.balloons()
                    st.success(f"All {num_strips} strips printed successfully!")
                    
                except Exception as e:
                    st.error(f"Error printing strips: {str(e)}")
            
            # Print original (uncut) button
            if st.button("Print Original (Uncut)", key="print_original_uncut_url"):
                rotate_value = 90 if rotate_checkbox else 0
                dither_value = dither_checkbox
                print_image(image_to_process, printer_info, rotate=rotate_value, dither=dither_value)
                st.success("Original (uncut) image sent to printer!")
