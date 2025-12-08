"""Printer handling and detection utilities for the Sticker Factory."""

import subprocess
import tempfile
import time
from brother_ql.models import ModelsManager
from brother_ql.backends import backend_factory
from brother_ql import labels
from brother_ql.raster import BrotherQLRaster
from brother_ql.conversion import convert
from brother_ql.backends.helpers import send
import usb.core

import streamlit as st
from job_queue import print_queue
from config import LABEL_TYPE


@dataclass
class PrinterInfo:
    identifier: str
    backend: str
    protocol: str
    vendor_id: str
    product_id: str
    serial_number: str
    name: str = "Brother QL Printer"
    model: str = "QL-570"
    status: str = "unknown"
    label_type: str = "unknown"
    label_size : str = "unknown"
    label_width: int = 0
    label_height: int = 0
    
    def __getitem__(self, item):
        return getattr(self, item)
    
    def __setitem__(self, key, value):
        setattr(self, key, value)


def find_and_parse_printer():
    print("Searching for Brother QL printers...")
    model_manager = ModelsManager()
    
    found_printers = []

    for backend_name in ["pyusb", "linux_kernel"]:
        try:
            print(f"Trying backend: {backend_name}")
            backend = backend_factory(backend_name)
            available_devices = backend["list_available_devices"]()
            print(f"Found {len(available_devices)} devices with {backend_name} backend")
            
            for printer in available_devices:
                print(f"Found device: {printer}")
                identifier = printer["identifier"]
                parts = identifier.split("/")

                if len(parts) < 4:
                    print(f"Skipping device with invalid identifier format: {identifier}")
                    continue

                protocol = parts[0]
                device_info = parts[2]
                serial_number = parts[3]
                
                try:
                    vendor_id, product_id = device_info.split(":")
                except ValueError:
                    print(f"Invalid device info format: {device_info}")
                    continue
                
                try:
                    product_id_int = int(product_id, 16)
                    for m in model_manager.iter_elements():
                        if m.product_id == product_id_int:
                            model = m.identifier
                            break
                    print(f"Matched printer model: {model}")
                except ValueError:
                    print(f"Invalid product ID format: {product_id}")
                    continue

                printer_info = PrinterInfo(
                    identifier=identifier,
                    backend=backend_name,
                    model=model,
                    protocol=protocol,
                    vendor_id=vendor_id,
                    product_id=product_id,
                    serial_number=serial_number,
                )
                found_printers.append(printer_info)            
                get_printer_status(printer_info)
                printer_info['name'] = f"{printer_info['model']} - H{serial_number.split('H')[-1]} - {printer_info['label_size']}"
                print(f"Added printer: {printer_info}")

        except Exception as e:
            print(f"Error with backend {backend_name}: {str(e)}")
            continue    
    return found_printers


def get_printer_status(printer):
    try:
        cmd = f"brother_ql -b pyusb --model {printer['model']} -p {printer['identifier']} status"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if "Phase:" in line:
                printer['status'] = line.split("Phase:")[1].strip()
                print(f"Printer {printer['identifier']} status: {printer['status']}")
            if "Media size:" in line:
                printer['label_size'] = line.split("Media size:")[1].strip()
                size_str = line.split("Media size:")[1].strip().split('x')[0].strip()
                try:
                    media_width_mm = int(size_str)
                    label_sizes = {
                        12: "12", 29: "29", 38: "38", 50: "50", 54: "54", 
                        62: "62", 102: "102", 103: "103", 104: "104"
                    }
                    if media_width_mm in label_sizes:
                        label_type = label_sizes[media_width_mm]
                        printer['label_type'] = label_type
                        printer['label_width'] = get_label_width(label_type)
                        printer['label_height'] = None
                        print(f"Printer {printer['identifier']} label type: {label_type}")
                except ValueError:
                    continue

    except Exception as e:
        #print(f"Error getting status for printer {printer['identifier']}: {str(e)}")
        printer['status'] = str(e)
        printer['label_type'] = "unknown"
        printer['label_size'] = "unknown"
        printer['label_width'] = 0
        printer['label_height'] = 0


def get_printer_label_info():
    """Get label information from printer or use defaults."""
    printer_info = find_and_parse_printer()
    if not printer_info:
        return None, "No printer found"
    
    try:
        cmd = f"brother_ql -b pyusb --model {printer_info['model']} -p {printer_info['identifier']} status"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout:
            status_output = result.stdout
            print(f"Printer status output: {status_output}")
            
            media_width_mm = None
            
            for line in status_output.split('\n'):
                if 'Media size:' in line:
                    try:
                        width_str = line.split(':')[1].split('x')[0].strip()
                        media_width_mm = int(width_str)
                        print(f"Detected media width: {media_width_mm}mm")
                    except ValueError:
                        continue
            
            if media_width_mm is not None:
                label_sizes = {
                    12: "12", 29: "29", 38: "38", 50: "50", 54: "54", 
                    62: "62", 102: "102", 103: "103", 104: "104"
                }
                
                if media_width_mm in label_sizes:
                    label_type = label_sizes[media_width_mm]
                    return label_type, f"Detected {label_type} ({media_width_mm}mm)"
        
        if 'model' in printer_info:
            model_defaults = {
                'QL-500': "62", 'QL-550': "62", 'QL-560': "62", 'QL-570': "62",
                'QL-580N': "62", 'QL-650TD': "62", 'QL-700': "62", 'QL-710W': "62",
                'QL-720NW': "62", 'QL-800': "62", 'QL-810W': "62", 'QL-820NWB': "62",
                'QL-1050': "102", 'QL-1060N': "102",
            }
            if printer_info['model'] in model_defaults:
                return model_defaults[printer_info['model']], f"Using default for {printer_info['model']}"
        
        return "62", "Using safe default width"
        
    except Exception as e:
        print(f"Error getting printer status: {str(e)}")
        return "62", f"Error getting printer status, using default"


def get_label_width(label_type):
    """Get the pixel width of a label type."""
    label_definitions = labels.ALL_LABELS
    for label in label_definitions:
        if label.identifier == label_type:
            width = label.dots_printable[0]
            print(f"Label type {label_type} width: {width} dots")
            return width
    raise ValueError(f"Label type {label_type} not found in label definitions")


def print_image(image, rotate=0, dither=False, label_type="62"):
    """Queue a print job."""
    temp_dir = tempfile.gettempdir()
    import os
    os.makedirs(temp_dir, exist_ok=True)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir=temp_dir) as temp_file:
        temp_file_path = temp_file.name
        image.save(temp_file_path, "PNG")
        print(f"Image saved to: {temp_file_path}")

    printer_info = find_and_parse_printer()
    if not printer_info:
        st.error("No Brother QL printer found. Please check the connection and try again.")
        return False

    print(f"Using label type: {label_type}")

    job_id = print_queue.add_job(
        image,
        rotate=rotate,
        dither=dither,
        printer_info=printer_info,
        temp_file_path=temp_file_path,
        label_type=label_type
    )

    status = print_queue.get_job_status(job_id)
    status_container = st.empty()
    
    while status.status in ["pending", "processing"]:
        status_container.info(f"Print job status: {status.status}")
        time.sleep(0.5)
        status = print_queue.get_job_status(job_id)

    if status.status == "completed":
        status_container.success("Print job completed successfully!")
        return True
    else:
        status_container.error(f"Print job failed: {status.error}")
        return False


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


def get_label_type():
    """Get label type from printer, config, or default."""
    if 'label_type' not in st.session_state:
        st.session_state.label_type = None
        st.session_state.label_status = None
    
    if st.session_state.label_type is not None:
        return st.session_state.label_type, st.session_state.label_status

    detected_label, status_message = get_printer_label_info()
    if detected_label:
        print(f"Using detected label type: {detected_label} - {status_message}")
        st.session_state.label_type = detected_label
        st.session_state.label_status = status_message
        return detected_label, status_message

    if LABEL_TYPE:
        status = "Using configured label_type from config.toml"
        print(f"Using configured label type from config.toml: {LABEL_TYPE}")
        st.session_state.label_type = LABEL_TYPE
        st.session_state.label_status = status
        return LABEL_TYPE, status

    default_type = "62"
    status = "Using default label type 62"
    print("No label type detected or configured, using default 62")
    st.warning("⚠️ No label type detected from printer and none configured in config.toml. Using default label type 62")
    st.session_state.label_type = default_type
    st.session_state.label_status = status
    return default_type, status
