"""Cat tab content."""

import streamlit as st
import requests
from io import BytesIO
from PIL import Image


def render(preper_image,printer_info, print_image):
    """Render the Dog tab."""
    st.subheader(":printer: a doggo")
    st.caption("from the fine folks at https://thedogapi.com/")
    
    # Initialize session state for dog image if not exists
    if 'dog_image' not in st.session_state:
        st.session_state.dog_image = None
        st.session_state.dog_dithered = None
    
    # Check if Dog API key exists and is valid
    # dog_api_key = st.secrets.get("dog_api_key", "")
    
    # if not dog_api_key or dog_api_key == "ask me":
    #     st.warning("⚠️ Dog API key is not configured")
    #     st.info("Add your dog_api_key to .streamlit/secrets.toml")
    if True:
        if st.button("Fetch dog"):
            try:
                # Get dog image URL
                response = requests.get(
                    "https://api.thedogapi.com/v1/images/search",
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
                st.session_state.dog_image = grayscale_image
                st.session_state.dog_dithered = dithered_image
                
            except Exception as e:
                st.error(f"Error fetching dog: {str(e)}")
            
        # Show image and print button if we have a dog
        if st.session_state.dog_dithered is not None:
            st.image(st.session_state.dog_dithered, caption="Dog!")
            if st.button("Print Dog", key="print_dog"):
                print_image(st.session_state.dog_image, printer_info, dither=True)
                st.success("Dog sent to printer!")