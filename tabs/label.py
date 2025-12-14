"""Label tab content - extracted from main file for modularity."""

# This tab requires many helper functions from the main file
# Import and use from printit.py context

def render(printer_info, get_fonts, find_url, preper_image, print_image, label_dir, img_concat_v):
    """Render the Label tab - implementation from main printit.py."""
    import streamlit as st
    import os
    import qrcode
    from PIL import Image, ImageDraw, ImageFont
    
    st.subheader(":printer: a label")

    label_type = printer_info["label_type"]
    label_width = printer_info["label_width"]
    # Helper functions
    def calculate_actual_image_height_with_empty_lines(text, font, line_spacing=10):
        draw = ImageDraw.Draw(Image.new("RGB", (1, 1), color="white"))
        total_height = 0
        ascent, descent = font.getmetrics()
        font_height = ascent + descent

        for line in text.split("\n"):
            if line.strip():
                bbox = draw.textbbox((0, 0), line, font=font)
                text_height = max(bbox[3] - bbox[1], font_height)
            else:
                text_height = font_height
            total_height += text_height + line_spacing

        padding = 20
        return total_height + (padding * 2)

    def calculate_max_font_size(width, text, font_path, start_size=10, end_size=200, step=1):
        try:
            draw = ImageDraw.Draw(Image.new("RGB", (1, 1), color="white"))
            max_font_size = start_size

            for size in range(start_size, end_size, step):
                try:
                    font = ImageFont.truetype(font_path, size)
                except OSError:
                    return 50
                adjusted_lines = [line for line in text.split("\n")]
                max_text_width = max([draw.textbbox((0, 0), line, font=font)[2] for line in adjusted_lines if line.strip()])

                if max_text_width <= width:
                    max_font_size = size
                else:
                    break

            return max_font_size
        except Exception as e:
            print(f"Error in calculate_max_font_size: {e}")
            return 50

    text = st.text_area("Enter your text to print", "write something", height=200)
    
    if text:
        urls = find_url(text)
        if urls:
            st.success("Found URLs: we might automate the QR code TODO")
            for url in urls:
                st.write(url)

        fonts = get_fonts()
        alignment = "center"
        
        if "selected_font" not in st.session_state:
            st.session_state.selected_font = fonts[0]
        
        if st.session_state.selected_font not in fonts:
            st.session_state.selected_font = fonts[0]
        
        font = st.session_state.selected_font

        try:
            test_font = ImageFont.truetype(font, 12)
        except OSError:
            working_font = None
            system_fonts = [
                "C:/Windows/Fonts/arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/System/Library/Fonts/Helvetica.ttf",
            ]
            
            for sys_font in system_fonts:
                try:
                    ImageFont.truetype(sys_font, 12)
                    working_font = sys_font
                    break
                except OSError:
                    continue
            
            if working_font:
                font = working_font
                st.warning(f"Custom fonts not available, using system font: {working_font}")
            else:
                try:
                    test_default = ImageFont.load_default()
                    font = None
                    st.warning("No TrueType or OpenType fonts available, using PIL default font")
                except Exception:
                    st.error("Unable to load any fonts. Please check your system font installation.")
                    st.stop()

        try:
            chars_per_line = max(len(line) for line in text.split('\n'))
            if chars_per_line == 0:
                chars_per_line = 1
            
            if label_type == "62":
                base_font_size = 60
                base_width = 696
            elif label_type == "102":
                base_font_size = 107
                base_width = 1164
            else:
                base_font_size = 60
                base_width = 696
            
            width_scale = label_width / base_width
            scaled_base_size = int(base_font_size * width_scale)
            base_text_length = 14
            text_scale = base_text_length / chars_per_line
            font_size = int(scaled_base_size * text_scale)
            font_size = max(font_size, 20)
            
            max_size = font_size
        except Exception as e:
            max_size = 60
            font_size = max_size
            print(f"Error calculating font size: {e}")

        fontstuff = st.checkbox("font settings", value=False)
        col1, col2 = st.columns(2)
        if fontstuff:
            with col1:
                # Create a mapping of font names (from metadata) to paths
                def get_font_display_name(font_path):
                    """Extract the actual font name from TTF file or use filename as fallback"""
                    try:
                        font = ImageFont.truetype(font_path, 12)
                        # Try to get the font name from the font object
                        if hasattr(font, 'getname'):
                            name = font.getname()
                            if name:
                                # Join tuple elements with space (e.g., ('Guatemala', 'Italic') -> 'Guatemala Italic')
                                if isinstance(name, tuple):
                                    return ' '.join(name)
                                return name
                        # Fallback to filename without extension
                        return os.path.splitext(os.path.basename(font_path))[0]
                    except Exception:
                        # Fallback to filename without extension
                        return os.path.splitext(os.path.basename(font_path))[0]
                
                font_display_names = [get_font_display_name(f) for f in fonts]
                font_name_to_path = {name: path for name, path in zip(font_display_names, fonts)}
                
                current_font_name = get_font_display_name(st.session_state.selected_font)
                
                selected_font_name = st.selectbox(
                    "Choose your font",
                    list(font_name_to_path.keys()),
                    index=list(font_name_to_path.keys()).index(current_font_name) if current_font_name in font_name_to_path else 0,
                    key="font_selector"
                )
                selected_font = font_name_to_path[selected_font_name]
                if selected_font != st.session_state.selected_font:
                    st.session_state.selected_font = selected_font
                font = selected_font

            with col2:
                alignment_options = ["left", "center", "right"]
                alignment = st.selectbox("Choose text alignment", alignment_options, index=1)
            
            try:
                if font == "fonts/5x5-Tami.ttf":
                    chars_per_line = max(len(line) for line in text.split('\n'))
                    if chars_per_line == 0:
                        chars_per_line = 1
                    if label_type == "62":
                        font_size = 60
                    elif label_type == "102":
                        font_size = 107
                    else:
                        base_width = 696
                        width_scale = label_width / base_width
                        font_size = int(60 * width_scale)
                    max_size = font_size
                else:
                    max_size = calculate_max_font_size(label_width, text, font)
            except Exception as e:
                print(f"Error calculating font size for {font}: {e}")
            font_size = st.slider("Font Size", 20, max_size + 50, max_size, help="Supports both TTF and OTF fonts")

        try:
            if font is None:
                fnt = ImageFont.load_default()
            else:
                try:
                    fnt = ImageFont.truetype(font, font_size)
                except (OSError, TypeError):
                    # Fallback if font loading fails (TTF or OTF)
                    fnt = ImageFont.load_default()
                    st.warning(f"Font {font} not found, using default font.")
        except Exception as e:
            try:
                fnt = ImageFont.load_default()
                st.warning(f"Error loading font {font}: {e}")
            except Exception as load_e:
                st.error(f"Error loading font: {load_e}")
        
        line_spacing = 20
        new_image_height = calculate_actual_image_height_with_empty_lines(text, fnt, line_spacing)
        padding = 20
        img = Image.new("RGB", (label_width, new_image_height), color="white")
        d = ImageDraw.Draw(img)
        y = padding

        for line in text.split("\n"):
            text_width = 0
            ascent, descent = fnt.getmetrics()
            font_height = ascent + descent

            if line.strip():
                bbox = d.textbbox((0, y), line, font=fnt)
                text_width = bbox[2] - bbox[0]
                text_height = max(bbox[3] - bbox[1], font_height)
            else:
                text_height = font_height

            if alignment == "center":
                x = (label_width - text_width) // 2
            elif alignment == "right":
                x = label_width - text_width
            else:
                x = 0

            d.text((x, y), line, font=fnt, fill=(0, 0, 0))
            y += text_height + line_spacing

        qr = qrcode.QRCode(border=0)
        qrurl = st.text_input("add a QRcode to your sticker")
        
        if qrurl:
            qr.add_data(qrurl)
            qr.make(fit=True)
            imgqr = qr.make_image(fill_color="black", back_color="white")

            if imgqr and img:
                imgqr = img_concat_v(img, imgqr)
                st.image(imgqr, width='stretch')
                if st.button("Print sticker+qr", key="print_sticker_qr"):
                    print_image(imgqr)
            elif imgqr and not (img):
                if st.button("Print sticker", key="print_qr_only"):
                    print_image(imgqr)

        if text and not (qrurl):
            st.image(img, width='stretch')
            if st.button("Print sticker", key="print_text_only"):
                print_image(img,printer_info=printer_info)
                st.success("sticker sent to printer")
        
        st.markdown("""
            * label will automaticly resize to fit the longest line, so use linebreaks.
            * on pc `ctrl+enter` will submit, on mobile click outside the `text_area` to process.
        """)