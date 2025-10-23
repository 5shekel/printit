from brother_ql.raster import BrotherQLRaster
from brother_ql.conversion import convert
from brother_ql.backends.helpers import send
import usb.core
import streamlit as st

def process_print_job(image, printer_info, temp_file_path, rotate=0, dither=False, label_type="102", debug=False):
    """
    Process a single print job.
    Returns (success, error_message)
    """
    # Get debug flag from secrets if not explicitly passed
    if not debug and 'debug' in st.secrets:
        debug = st.secrets['debug']

    try:
        # Prepare the image for printing
        qlr = BrotherQLRaster(printer_info["model"])
        
        # Debug print before conversion
        if debug:
            print(f"Starting print job with label_type: {label_type}")
        
        instructions = convert(
            qlr=qlr,
            images=[temp_file_path],
            label=label_type,
            rotate=rotate,
            threshold=70,
            dither=dither,
            compress=True,
            red=False,
            dpi_600=False,
            hq=False,
            cut=True,
        )

        # Debug logging
        if debug:
            print(f"""
            Print parameters:
            - Label type: {label_type}
            - Rotate: {rotate}
            - Dither: {dither}
            - Model: {printer_info['model']}
            - Backend: {printer_info['backend']}
            - Identifier: {printer_info['identifier']}
            """)

        # Try to print using Python API
        success = send(
            instructions=instructions,
            printer_identifier=printer_info["identifier"],
            backend_identifier="pyusb"
        )
        
        if not success:
            return False, "Failed to print using Python API"

        return True, None

    except usb.core.USBError as e:
        # Treat timeout errors as successful since they often occur after print completion
        if e.errno == 110:  # Operation timed out
            if debug:
                print("USB timeout occurred - this is normal and the print likely completed")
            return True, "Print completed (timeout is normal)"
        error_msg = f"USBError encountered: {e}"
        if debug:
            print(error_msg)
        return False, error_msg

    except Exception as e:
        error_msg = f"Unexpected error during printing: {str(e)}"
        if debug:
            print(error_msg)
        return False, error_msg
