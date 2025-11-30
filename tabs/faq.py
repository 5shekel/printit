"""FAQ tab content."""

import streamlit as st
from PIL import Image


def render():
    """Render the FAQ tab."""
    st.subheader("FAQ:")
    st.markdown(
        """
        *dithering* is suggested (sometimes inforced) if source is not lineart as grayscale and color look bad at thermal printer

        all uploaded images, generated labels, and webcam snapshots are saved

        app [code](https://github.com/5shekel/printit)

        PRINT ALOT is the best!
        """
    )
    st.image(Image.open("assets/station_sm.jpg"), caption="TAMI printshop", width='stretch')
