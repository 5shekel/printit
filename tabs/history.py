"""History tab content - gallery of saved images."""

import streamlit as st
import os
from PIL import Image
from datetime import datetime


def render(list_saved_images, label_dir, print_image, preper_image):
    """Render the History tab."""
    st.subheader("Gallery of Labels and Stickers")
    
    # Initialize session state variables if they don't exist
    if 'saved_images_list' not in st.session_state:
        st.session_state.saved_images_list = list_saved_images()
    if 'page_number' not in st.session_state:
        st.session_state.page_number = 0
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    if 'filter_duplicates' not in st.session_state:
        st.session_state.filter_duplicates = True
    
    # Get pagination settings from secrets with defaults
    items_per_page = st.secrets.get("items_per_page", 5)  # Default to 3x3 grid
    
    # Search, filter, and refresh controls
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        search_query = st.text_input("Search filenames", value=st.session_state.search_query, key="history_search")
    with col2:
        filter_duplicates = st.checkbox("Filter duplicates", value=st.session_state.filter_duplicates, key="history_filter")
        st.session_state.filter_duplicates = filter_duplicates
    with col3:
        if st.button("Refresh Gallery", key="history_refresh"):
            st.session_state.saved_images_list = list_saved_images(filter_duplicates)
            st.session_state.page_number = 0
            st.rerun()
    
    # Update image list if filter setting changed
    if filter_duplicates != st.session_state.filter_duplicates:
        st.session_state.saved_images_list = list_saved_images(filter_duplicates)
        st.session_state.page_number = 0
        st.rerun()
    
    # Filter images based on search query
    filtered_images = [
        img for img in st.session_state.saved_images_list 
        if search_query.lower() in os.path.basename(img).lower()
    ]
    
    # Pagination
    total_pages = max((len(filtered_images) - 1) // items_per_page + 1, 1)
    
    # Pagination controls
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("Previous", disabled=st.session_state.page_number <= 0, key="history_prev"):
            st.session_state.page_number -= 1
            st.rerun()
    with col2:
        st.write(f"Page {st.session_state.page_number + 1} of {total_pages}")
    with col3:
        if st.button("Next", disabled=st.session_state.page_number >= total_pages - 1, key="history_next"):
            st.session_state.page_number += 1
            st.rerun()
    
    # Calculate start and end indices for current page
    start_idx = st.session_state.page_number * items_per_page
    end_idx = min(start_idx + items_per_page, len(filtered_images))
    
    # Display current page images
    cols_per_row = 3
    current_page_images = filtered_images[start_idx:end_idx]
    
    # Show total count of filtered images
    if len(filtered_images) > 0:
        st.caption(f"Showing {len(current_page_images)} of {len(filtered_images)} images")
        
        # Display images in grid
        for i in range(0, len(current_page_images), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                idx = i + j
                if idx < len(current_page_images):
                    with cols[j]:
                        image_path = current_page_images[idx]
                        try:
                            image = Image.open(image_path)
                            st.image(image, width='stretch')
                            
                            filename = os.path.basename(image_path)
                            modified_time = datetime.fromtimestamp(
                                os.path.getmtime(image_path)
                            ).strftime("%Y-%m-%d %H:%M")
                            st.caption(f"{filename}\n{modified_time}")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Print", key=f"print_history_{idx}_{st.session_state.page_number}"):
                                    image_to_print = Image.open(image_path).convert("RGB")
                                    grayscale_image, dithered_image = preper_image(image_to_print)
                                    print_image(grayscale_image, dither=True)
                            with col2:
                                if st.button("Send to Sticker", key=f"send_to_sticker_{idx}_{st.session_state.page_number}"):
                                    st.session_state.selected_image_path = image_path
                                    st.rerun()
                        except Exception as e:
                            st.error(f"Error loading image: {str(e)}")
    else:
        st.info("No images in history yet. Print some images to see them here!")
