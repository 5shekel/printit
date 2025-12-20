import streamlit as st
import glob
import os
import re
import time
import hashlib
import logging
from pathlib import Path
from brother_ql import labels

# Initialize logging configuration (must be done first!)
import logging_config
logger = logging.getLogger("sticker_factory.printit")

# Import centralized config (loads once at startup)
from config_manager import (
    APP_TITLE,
    PRIVACY_MODE,
    HISTORY_LIMIT,
    TABS_CONFIG,
)

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
    find_and_parse_printer,
    print_image,
    # get_label_type
)

def get_enabled_tabs():
    """Return list of enabled tab names from config, excluding History if privacy_mode is true."""
    # Get the enabled tabs list directly from config (preserves order)
    enabled = TABS_CONFIG.get("enabled", [
        "Label",
        "Sticker",
        "Sticker Pro",
        "Text2image",
        "Webcam",
        "Cat",
        "Dog",
        "History",
        "FAQ",
    ])
    
    # Filter out History if privacy_mode is enabled
    if PRIVACY_MODE:
        logger.info("Privacy mode is ENABLED, filtering out History tab")
        if "History" in enabled:
            enabled = [tab for tab in enabled if tab != "History"]
    else:
        logger.info("Privacy mode is DISABLED, History tab should be visible")
    return enabled


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
            logger.error(f"Error processing {image_path}: {e}")
            continue

    return sorted(unique_images.values(), key=os.path.getmtime, reverse=True)[:HISTORY_LIMIT]

def get_fonts():
    """Return list of fonts with 5x5-Tami.ttf as default, followed by system fonts (TTF and OTF)"""
    fonts = []
    
    default_font = "fonts/5x5-Tami.ttf"
    if os.path.exists(default_font):
        fonts.append(default_font)
    
    try:
        for font_file in os.listdir("fonts/"):
            if (font_file.endswith(".ttf") or font_file.endswith(".otf")) and font_file != "5x5-Tami.ttf":
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

label_dir = "labels"
os.makedirs(label_dir, exist_ok=True)

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

st.title(f":rainbow[**{APP_TITLE}**]")
st.subheader(":primary[:printer: hard copies of images and text]")


st.sidebar.title(":primary[Settings]")

printers = find_and_parse_printer()

# check printer statuses 
available_printers = []
for p in printers:
    logger.debug(f"\tPrinter: {p['name']}, Status: {p['status']}")
    if p['status'] == 'Waiting to receive':
        if p['label_type'] != 'unknown':
            available_printers.append(p['name'])

st.sidebar.subheader(":primary[Printer Selection]")
printer = st.sidebar.radio("**Available Printer**", available_printers)
selected_printer = next((p for p in printers if p["name"] == printer), None)

if not selected_printer:
    st.error("❌ No available printers detected! Check connections, power and paper.")
    
    st.sidebar.subheader("Detected Printers")
    for p in printers:
        status_color = "green" if p['status'] == 'Waiting to receive' else "red"
        label_color = "green" if p['label_type'] != 'unknown' else "red"
        st.sidebar.markdown(f":primary[**{p['name']}**]\n- Label Size: :{label_color}[{p['label_size']}]\n- Status:  :{status_color}[{p['status']}]")
    #st.stop()   

else:
    # st.sidebar.markdown(f"- *Serial Number:* {selected_printer['serial_number']}\n- *Label Size:* {selected_printer['label_size']}\n - *Status:* {selected_printer['status']}")
    label_type = selected_printer['label_type']
    label_width = selected_printer['label_width']

    st.sidebar.subheader(":primary[Detected Printers]")
    for p in printers: 
        status_color = "green" if p['status'] == 'Waiting to receive' else "red"
        label_color = "green" if p['label_type'] != 'unknown' else "red"
        if p.name == selected_printer['name']:
            st.sidebar.markdown(f":green[**{p['name']}**]\n- Label Size: :{label_color}[{p['label_size']}]\n- Status:  :{status_color}[{p['status']}]")
        else:     
            st.sidebar.markdown(f":primary[**{p['name']}**]\n- Label Size: :{label_color}[{p['label_size']}]\n- Status:  :{status_color}[{p['status']}]")



    # Get enabled tabs from configuration
    enabled_tab_names = get_enabled_tabs()
    logger.debug(f"Enabled tabs: {enabled_tab_names}")

    if not enabled_tab_names:
        st.error("❌ No tabs are enabled! Check config.toml ENABLED_TABS configuration")
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
                        printer_info=selected_printer,
                        preper_image=preper_image,
                        print_image=print_image,
                    )
                elif tab_name == "Label":
                    import tabs.label as label_module
                    label_module.render(
                        printer_info=selected_printer,
                        get_fonts=get_fonts,
                        find_url=find_url,
                        preper_image=preper_image,
                        print_image=print_image,
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
                        printer_info=selected_printer,
                    )
                elif tab_name == "Webcam":
                    import tabs.webcam as webcam_module
                    webcam_module.render(
                        printer_info=selected_printer,
                        preper_image=preper_image,
                        print_image=print_image,
                    )
                elif tab_name == "Cat":
                    import tabs.cat as cat_module
                    cat_module.render(
                        printer_info=selected_printer,
                        preper_image=preper_image,
                        print_image=print_image,
                    )
                elif tab_name == "Dog":
                    import tabs.dog as dog_module
                    dog_module.render(
                        printer_info=selected_printer,
                        preper_image=preper_image,
                        print_image=print_image,
                    )

                elif tab_name == "Sticker Pro":
                    import tabs.sticker_pro as sticker_pro_module    
                    sticker_pro_module.render(
                        print_image=print_image,
                        apply_threshold=apply_threshold,
                        add_border=add_border,
                        apply_histogram_equalization=apply_histogram_equalization,
                        resize_image_to_width=resize_image_to_width,
                        preper_image=preper_image,
                        printer_info=selected_printer,
                    )
                elif tab_name == "History":
                    import tabs.history as history_module
                    history_module.render(
                        list_saved_images=list_saved_images,
                        print_image=print_image,
                        preper_image=preper_image,
                    )
                elif tab_name == "FAQ":
                    import tabs.faq as faq_module
                    faq_module.render()
                else:
                    st.warning(f"Tab '{tab_name}' is not implemented yet")
            except Exception as e:
                st.error(f"Error rendering {tab_name} tab: {str(e)}")
                logger.error(f"Exception in tab {tab_name}: {e}", exc_info=True)
