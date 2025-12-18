"""FAQ tab content."""

import streamlit as st
from PIL import Image


def render():
    """Render the FAQ tab."""
    st.subheader("FAQ:")
    st.markdown(
        """
        - *dithering* is suggested (sometimes inforced) if source is not lineart as grayscale and color look bad at thermal printer
        - switching tabs doesn't re-detect printers, refreshing the page and buttons will do it
        - to save the generated images on the host, set `privacy_mode = false` in `config.toml`
        - to disable printer sleep mode:
            1. Discover the printer with `brother_ql discover`, it returns something like `Found compatible printer QL-600 at: usb://0x04f9:0x20c0/000H2G258173` were `usb://0x04f9:0x20c0/000H2G258173` is the printer id
            2. Set the `power-off-delay` to 0: `brother_ql -p <PRINTER ID> configure set power-off-delay 0`. You can check the set value `brother_ql -p <PRINTER ID> configure get power-off-delay`
        - [Repo](https://github.com/5shekel/printit)

        PRINT ALOT is the best!
        """
    )
    st.image(Image.open("assets/station_sm.jpg"), caption="TAMI printshop", width='stretch')
