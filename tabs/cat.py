"""Cat tab content."""

import streamlit as st
import requests
from io import BytesIO
from PIL import Image


def render(preper_image,printer_info, print_image):
    """Render the Cat tab."""
    st.subheader(":printer: a cat")
    st.caption("from the fine folks at https://thecatapi.com/")
    
    # Initialize session state for cat image if not exists
    if 'cat_image' not in st.session_state:
        st.session_state.cat_image = None
        st.session_state.cat_dithered = None
    
    # Check if Cat API key exists and is valid
    # cat_api_key = st.secrets.get("cat_api_key", "")
    
    # if not cat_api_key or cat_api_key == "ask me":
    #     st.warning("⚠️ Cat API key is not configured")
    #     st.info("Add your cat_api_key to .streamlit/secrets.toml")
    if True:
        if st.button("Fetch cat"):
            try:
                # Get cat image URL
                response = requests.get(
                    "https://api.thecatapi.com/v1/images/search",
                    # headers={
                    #     "x-api-key": cat_api_key
                    #     }
                )
                response.raise_for_status()
                image_url = response.json()[0]["url"]
                
                print(f"Fetched cat image URL: {image_url}")
                # Download and process image
                img = Image.open(BytesIO(requests.get(image_url).content)).convert('RGB')
                grayscale_image, dithered_image = preper_image(img, label_width=printer_info['label_width'])
                
                # Store in session state
                st.session_state.cat_image = grayscale_image
                st.session_state.cat_dithered = dithered_image
                
            except Exception as e:
                st.error(f"Error fetching cat: {str(e)}")
            
        # Show image and print button if we have a cat
        if st.session_state.cat_dithered is not None:
            st.image(st.session_state.cat_dithered, printer_info=printer_info, caption="Cat!")
            if st.button("Print Cat", key="print_cat"):
                print_image(st.session_state.cat_image, printer_info, dither=True)
                st.success("Cat sent to printer!")
