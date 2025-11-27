"""Text2image tab content."""

import streamlit as st


def submit(st_session_state):
    """Handle prompt submission."""
    st_session_state.prompt = st_session_state.widget
    st_session_state.widget = ""
    st_session_state.generated_image = None


def render(submit_func, generate_image, preper_image, print_image):
    """Render the Text2image tab."""
    st.subheader(":printer: image from text")
    st.write("using tami stable diffusion bot")

    st.text_input("Enter a prompt", key="widget", on_change=submit_func)
    prompt = st.session_state.prompt

    if prompt and st.session_state.generated_image is None:
        st.write("Generating image from prompt: " + prompt)
        generated_image = generate_image(prompt, 30)
        st.session_state.generated_image = generated_image

    if st.session_state.generated_image:
        generated_image = st.session_state.generated_image
        grayscale_image, dithered_image = preper_image(generated_image)

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
