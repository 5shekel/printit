import streamlit as st
import glob
import os
import re
import time
import hashlib
from brother_ql import labels


# Tabs get imported only when enabled in config.toml


# Import image utilities
from image_utils import (
    preper_image,
    apply_threshold,
    resize_image_to_width,
    add_border,
    apply_histogram_equalization,
    img_concat_v,
)
from printer_utils import (
    print_image,
    get_label_type,
)

# Import configuration
from config import (
    get_enabled_tabs,
    APP_TITLE,
    HISTORY_LIMIT,
)

# Get label type and width
label_type, label_status = get_label_type()
label_width = labels.ALL_LABELS[0].dots_printable[0]
for label in labels.ALL_LABELS:
    if label.identifier == label_type:
        label_width = label.dots_printable[0]
        print(f"Label type {label_type} width: {label_width} dots")
        break

# ============================================================================
# PRINTER DETECTION AND CONFIGURATION
# ============================================================================

def list_saved_images(filter_duplicates=True):
    temp_files = glob.glob(os.path.join("temp", "*.[pj][np][g]*"))
    label_files = glob.glob(os.path.join("labels", "*.[pj][np][g]*"))
    image_files = temp_files + label_files

    valid_images = [
        f for f in image_files 
        if "write_something" not in os.path.basename(f).lower()
    ]

    if not filter_duplicates:
        return sorted(valid_images, key=os.path.getmtime, reverse=True)[:HISTORY_LIMIT]

    unique_images = {}
    for image_path in valid_images:
        try:
            file_size = os.path.getsize(image_path)
            
            if file_size in unique_images:
                existing_time = os.path.getmtime(unique_images[file_size])
                current_time = os.path.getmtime(image_path)
                if current_time > existing_time:
                    unique_images[file_size] = image_path
            else:
                unique_images[file_size] = image_path
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
            continue

    return sorted(unique_images.values(), key=os.path.getmtime, reverse=True)[:HISTORY_LIMIT]

def get_fonts():
    """Return list of fonts with 5x5-Tami.ttf as default, followed by system fonts"""
    fonts = []
    
    default_font = "fonts/5x5-Tami.ttf"
    if os.path.exists(default_font):
        fonts.append(default_font)
    
    try:
        for font_file in os.listdir("fonts/"):
            if font_file.endswith(".ttf") and font_file != "5x5-Tami.ttf":
                fonts.append("fonts/" + font_file)
    except OSError:
        pass
    
    import platform
    system = platform.system()
    
    system_font_dirs = []
    if system == "Windows":
        system_font_dirs = ["C:/Windows/Fonts/", "C:/Windows/System32/Fonts/"]
    elif system == "Darwin":
        system_font_dirs = ["/System/Library/Fonts/", "/Library/Fonts/", f"/Users/{os.environ.get('USER', '')}/Library/Fonts/"]
    elif system == "Linux":
        system_font_dirs = ["/usr/share/fonts/", "/usr/local/share/fonts/", f"/home/{os.environ.get('USER', '')}/.fonts/", f"/home/{os.environ.get('USER', '')}/.local/share/fonts/"]
    
    for font_dir in system_font_dirs:
        if os.path.exists(font_dir):
            try:
                for root, dirs, files in os.walk(font_dir):
                    for file in files:
                        if file.lower().endswith('.ttf'):
                            full_path = os.path.join(root, file)
                            if full_path not in fonts:
                                fonts.append(full_path)
            except (OSError, PermissionError):
                continue
    
    seen = set()
    unique_fonts = []
    for font in fonts:
        if font not in seen:
            seen.add(font)
            unique_fonts.append(font)
    
    return unique_fonts if unique_fonts else ["fonts/5x5-Tami.ttf"]

def safe_filename(text):
    epoch_time = int(time.time())
    return f"{epoch_time}_{hashlib.sha256(text.encode()).hexdigest()}.png"

label_dir = "labels"
os.makedirs(label_dir, exist_ok=True)

def generate_image(prompt, steps):
    payload = {"prompt": prompt, "steps": steps, "width": label_width}

    if TXT2IMG_URL == "http://localhost:7860":
        st.warning("Using default Stable Diffusion URL (http://localhost:7860). Configure txt2img_url in .streamlit/secrets.toml for custom endpoint.")

    try:
        response = requests.post(url=f'{TXT2IMG_URL}/sdapi/v1/txt2img', json=payload)
        response.raise_for_status()

        print("Raw response content:", response.content)

        r = response.json()

        if r["images"]:
            first_image = r["images"][0]
            base64_data = first_image.split("base64,")[1] if "base64," in first_image else first_image
            image = Image.open(io.BytesIO(base64.b64decode(base64_data)))

            png_payload = {"image": "data:image/png;base64," + first_image}
            response2 = requests.post(url=f"{TXT2IMG_URL}/sdapi/v1/png-info", json=png_payload)
            response2.raise_for_status()

            pnginfo = PngImagePlugin.PngInfo()
            info = response2.json().get("info")
            if info:
                pnginfo.add_text("parameters", str(info))
            current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            temp_dir = "temp"
            os.makedirs(temp_dir, exist_ok=True)
            filename = os.path.join(temp_dir, "txt2img_" + current_date + ".png")
            image.save(filename, pnginfo=pnginfo)

            return image
        else:
            print("No images found in the response")
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def preper_image(image, label_width=label_width):
    """Wrapper for image preparation - calls image_utils.preper_image"""
    return prepare_image(image, label_width)


def resize_image_to_width(image, target_width_mm):
    """Wrapper for image resizing - calls image_utils.resize_image_to_width"""
    return resize_image_to_width_util(image, target_width_mm, label_width)


def img_concat_v(im1, im2, image_width=label_width):
    """Wrapper for image concatenation - calls image_utils.img_concat_v"""
    return img_concat_v_util(im1, im2, image_width)


def print_image(image, rotate=0, dither=False):
    """Wrapper for print_image - calls printer_utils.print_image"""
    label_type, _ = get_label_type()
    return print_image_util(image, rotate=rotate, dither=dither, label_type=label_type)


def find_url(string):
    url_pattern = re.compile(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
    urls = re.findall(url_pattern, string)
    return urls

# ============================================================================
# STREAMLIT APP
# ============================================================================

if not os.path.exists(".streamlit/secrets.toml"):
    st.error("⚠️ No secrets.toml file found!")
    st.info("""
    Please set up your `.streamlit/secrets.toml` file:
    1. Copy the example file: `cp .streamlit/secrets.toml.example .streamlit/secrets.toml`
    2. Edit the file with your settings
    
    The app will try to auto-detect your printer's label type, but you can override it in secrets.toml if needed.
    See the example file for all available options and their descriptions.
    """)

st.title(APP_TITLE)
st.subheader(":printer: hard copies of images and text")

# Get enabled tabs from configuration
enabled_tab_names = get_enabled_tabs()

if not enabled_tab_names:
    st.error("❌ No tabs are enabled! Check tabs/__init__.py ENABLED_TABS configuration")
    st.stop()

# Create tabs dynamically
tab_objects = st.tabs(enabled_tab_names)

# Render each enabled tab
for tab_obj, tab_name in zip(tab_objects, enabled_tab_names):
    with tab_obj:
        try:
            if tab_name == "Sticker":
                import tabs.sticker as sticker_module
                sticker_module.render(
                    preper_image=preper_image,
                    print_image=print_image,
                    safe_filename=safe_filename,
                )
            elif tab_name == "Label":
                import tabs.label as label_module
                label_module.render(
                    label_type=label_type,
                    label_width=label_width,
                    get_fonts=get_fonts,
                    find_url=find_url,
                    preper_image=preper_image,
                    print_image=print_image,
                    safe_filename=safe_filename,
                    label_dir=label_dir,
                    img_concat_v=img_concat_v,
                )
            elif tab_name == "Text2image":
                import tabs.text2image as text2image_module
                # For text2image, we need to define submit function
                def submit():
                    st.session_state.prompt = st.session_state.widget
                    st.session_state.widget = ""
                    st.session_state.generated_image = None
                
                if "prompt" not in st.session_state:
                    st.session_state.prompt = ""
                if "generated_image" not in st.session_state:
                    st.session_state.generated_image = None
                
                text2image_module.render(
                    submit_func=submit,
                    generate_image_func=text2image_module.generate_image,
                    preper_image=preper_image,
                    print_image=print_image,
                    label_width=label_width,
                )
            elif tab_name == "Webcam":
                import tabs.webcam as webcam_module
                webcam_module.render(
                    preper_image=preper_image,
                    print_image=print_image,
                    safe_filename=safe_filename,
                    label_dir=label_dir,
                )
            elif tab_name == "Cat":
                import tabs.cat as cat_module
                cat_module.render(
                    preper_image=preper_image,
                    print_image=print_image,
                )
            elif tab_name == "FAQ":
                import tabs.faq as faq_module
                faq_module.render()
            elif tab_name == "Sticker Pro":
                import tabs.sticker_pro as sticker_pro_module    
                sticker_pro_module.render(
                    print_image=print_image,
                    apply_threshold=apply_threshold,
                    add_border=add_border,
                    apply_histogram_equalization=apply_histogram_equalization,
                    resize_image_to_width=resize_image_to_width,
                    preper_image=preper_image,
                    label_width=label_width,
                )
            elif tab_name == "History":
                import tabs.history as history_module
                history_module.render(
                    list_saved_images=list_saved_images,
                    label_dir=label_dir,
                    safe_filename=safe_filename,
                    print_image=print_image,
                    preper_image=preper_image,
                )
            else:
                st.warning(f"Tab '{tab_name}' is not implemented yet")
        except Exception as e:
            st.error(f"Error rendering {tab_name} tab: {str(e)}")
            print(f"Exception in tab {tab_name}: {e}")
            import traceback
            traceback.print_exc()
