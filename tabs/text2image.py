"""Text2image tab content."""

import logging
import streamlit as st
import requests
import io
import base64
import os
import tomllib
from pathlib import Path
from PIL import Image, PngImagePlugin
from datetime import datetime

logger = logging.getLogger("sticker_factory.tabs.text2image")

# Load configuration directly from config.toml
def _load_config():
    """Load config.toml from the workspace root."""
    config_path = Path(__file__).parent.parent / "config.toml"
    try:
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    except (FileNotFoundError, Exception):
        return {}

_CONFIG = _load_config()
TXT2IMG_URL = _CONFIG.get("txt2img", {}).get("url", "http://localhost:7860")


def generate_image(prompt, steps, label_width):
    """Generate image from text prompt using Stable Diffusion API."""
    payload = {"prompt": prompt, "steps": steps, "width": label_width}

    if TXT2IMG_URL == "http://localhost:7860":
        st.warning("Using default Stable Diffusion URL (http://localhost:7860). Configure txt2img_url in config.toml for custom endpoint.")

    try:
        response = requests.post(url=f'{TXT2IMG_URL}/sdapi/v1/txt2img', json=payload)
        response.raise_for_status()

        logger.debug("Raw response content: %s", response.content)

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
            logger.warning("No images found in the response")
            return None

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return None


def submit(st_session_state):
    """Handle prompt submission."""
    st_session_state.prompt = st_session_state.widget
    st_session_state.widget = ""
    st_session_state.generated_image = None


def render(submit_func, generate_image_func, preper_image, print_image, printer_info):
    """Render the Text2image tab."""
    st.subheader(":printer: image from text")
    st.write("using tami stable diffusion bot")

    st.text_input("Enter a prompt", key="widget", on_change=submit_func)
    prompt = st.session_state.prompt

    if prompt and st.session_state.generated_image is None:
        st.write("Generating image from prompt: " + prompt)
        generated_image = generate_image_func(prompt, 30, printer_info['label_width'])
        st.session_state.generated_image = generated_image

    if st.session_state.generated_image:
        generated_image = st.session_state.generated_image
        grayscale_image, dithered_image = preper_image(generated_image, label_width=printer_info['label_width'])

        col1, col2 = st.columns(2)
        with col1:
            st.image(grayscale_image, caption="Original Image")
        with col2:
            st.image(dithered_image, caption="Resized and Dithered Image")

        col3, col4 = st.columns(2)
        with col3:
            if st.button("Print Original Image", key="print_original_t2i"):
                print_image(grayscale_image)
                st.success("Original image sent to printer!")
        with col4:
            if st.button("Print Dithered Image", key="print_dithered_t2i"):
                print_image(grayscale_image, dither=True)
                st.success("Dithered image sent to printer!")

    st.session_state.last_prompt = prompt
