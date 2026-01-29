#!/usr/bin/env python3
"""
Create outline overlay from images with automatic background removal.
Can either:
1. Use a pre-existing background-removed image (from remove_bg.py)
2. Automatically remove background in memory without saving intermediate files

Processes images to:
1. Remove background (if needed)
2. Create a black mask from the alpha channel
3. Expand the mask
4. Extract the outline (solid or dotted)
5. Overlay outline on original image
"""

import os
import sys
import argparse
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from rembg import remove
from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class OutlineParams:
    """Parameters for outline generation."""
    expansion_pixels: int = 5
    outline_thickness: int = 2
    outline_color: Tuple[int, int, int] = (0, 255, 0)  # BGR green
    shape: str = 'line'  # 'line' or 'marker'
    shape_spacing: int = 10
    shape_size: int = 3
    should_exclude_border: bool = True
    border_margin: int = 5
    shape_type: str = 'circle'
    marker_color: Optional[Tuple[int, int, int]] = None

@dataclass
class ProcessingParams:
    """Parameters for image processing."""
    original_path: str
    bg_removed_path: Optional[str] = None
    output_path: Optional[str] = None
    outline_params: Optional[OutlineParams] = None
    
    def __post_init__(self):
        if self.outline_params is None:
            self.outline_params = OutlineParams()

def load_image(image_path):
    """Load image using OpenCV."""
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")
    return img

def create_mask_from_alpha(image):
    """
    Create a binary mask from the alpha channel of an RGBA image.
    Returns mask where foreground (non-transparent) is white (255) and background is black (0).
    """
    if len(image.shape) == 2:
        # Grayscale image
        mask = image
    elif image.shape[2] == 4:
        # RGBA image - use alpha channel
        mask = image[:, :, 3]
    elif image.shape[2] == 3:
        # RGB image - convert to grayscale
        mask = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Threshold to create binary mask
        _, mask = cv2.threshold(mask, 1, 255, cv2.THRESH_BINARY)
    else:
        raise ValueError(f"Unsupported image shape: {image.shape}")
    
    # Ensure mask is binary (0 or 255)
    if mask.dtype != np.uint8:
        mask = mask.astype(np.uint8)
    
    return mask

def expand_mask(mask, expansion_pixels=5):
    """
    Expand/dilate a binary mask by specified number of pixels.
    
    Args:
        mask: Binary mask (0 or 255)
        expansion_pixels: Number of pixels to expand in all directions
    
    Returns:
        Expanded mask
    """
    if expansion_pixels <= 0:
        return mask.copy()
    
    # Create kernel for dilation
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, 
                                      (2*expansion_pixels + 1, 2*expansion_pixels + 1))
    
    # Dilate the mask
    expanded_mask = cv2.dilate(mask, kernel, iterations=1)
    
    return expanded_mask

def draw_marker(image, x, y, size, marker_type='circle', angle=0):
    """
    Draw a marker at the specified position.
    
    Args:
        image: Image to draw on
        x, y: Center coordinates
        size: Size of marker
        marker_type: Type of marker ('circle', 'square', 'triangle', 'diamond', 'star', 'cross')
        angle: Rotation angle in degrees (for some markers)
    """
    if marker_type == 'circle':
        cv2.circle(image, (x, y), size, 255, -1)
    elif marker_type == 'square':
        half = size
        cv2.rectangle(image, (x-half, y-half), (x+half, y+half), 255, -1)
    elif marker_type == 'triangle':
        # Equilateral triangle pointing up
        pts = np.array([
            [x, y - size],  # Top
            [x - size, y + size],  # Bottom left
            [x + size, y + size]   # Bottom right
        ], np.int32)
        cv2.fillPoly(image, [pts], 255)
    elif marker_type == 'diamond':
        # Diamond shape
        pts = np.array([
            [x, y - size],  # Top
            [x + size, y],  # Right
            [x, y + size],  # Bottom
            [x - size, y]   # Left
        ], np.int32)
        cv2.fillPoly(image, [pts], 255)
    elif marker_type == 'star':
        # Simple 5-point star
        pts = []
        for i in range(5):
            angle_rad = np.pi/2 + i * 2*np.pi/5
            # Outer point
            pts.append([x + size * np.cos(angle_rad), y - size * np.sin(angle_rad)])
            # Inner point
            angle_rad += np.pi/5
            pts.append([x + size/2 * np.cos(angle_rad), y - size/2 * np.sin(angle_rad)])
        pts = np.array(pts, np.int32)
        cv2.fillPoly(image, [pts], 255)
    elif marker_type == 'cross':
        # Plus sign
        cv2.line(image, (x-size, y), (x+size, y), 255, 2)
        cv2.line(image, (x, y-size), (x, y+size), 255, 2)
    else:
        # Default to circle
        cv2.circle(image, (x, y), size, 255, -1)

def _draw_markers_along_contour(contour, outline, shape_spacing, shape_size, 
                               exclude_border, border_margin, shape_type, height, width):
    """Draw markers along a single contour."""
    # Approximate the contour to reduce points
    epsilon = 0.001 * cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, epsilon, True)
    
    # Flatten the contour points
    points = approx.reshape(-1, 2)
    
    # Draw markers along the contour with specified spacing
    for i in range(len(points)):
        # Calculate distance between consecutive points
        if i < len(points) - 1:
            p1 = points[i]
            p2 = points[i + 1]
        else:
            p1 = points[i]
            p2 = points[0]  # Close the loop
        
        # Interpolate points along the line segment
        distance = np.linalg.norm(p2 - p1)
        if distance > 0:
            num_shapes = int(distance / shape_spacing)
            if num_shapes > 0:
                for j in range(num_shapes + 1):
                    t = j / max(num_shapes, 1)
                    x = int(p1[0] * (1 - t) + p2[0] * t)
                    y = int(p1[1] * (1 - t) + p2[1] * t)
                    
                    # Check if marker is too close to border
                    if exclude_border:
                        if (x < border_margin or x >= width - border_margin or 
                            y < border_margin or y >= height - border_margin):
                            continue
                    
                    draw_marker(outline, x, y, shape_size, shape_type)

def _create_border_mask(height, width, border_margin):
    """Create a mask that excludes the border region."""
    border_mask = np.zeros((height, width), dtype=np.uint8)
    border_mask[border_margin:height-border_margin, border_margin:width-border_margin] = 255
    return border_mask

def get_mask_outline(mask, outline_thickness=2, shape='line', shape_spacing=10, shape_size=3, 
                     exclude_border=True, border_margin=5, shape_type='circle'):
    """
    Extract the outline of a binary mask.
    
    Args:
        mask: Binary mask (0 or 255)
        outline_thickness: Thickness of the outline in pixels (for solid lines)
        shape: Type of outline ('line' for solid line, 'marker' for shapes)
        shape_spacing: Distance between shapes in pixels (if shape='marker')
        shape_size: Size of shapes in pixels (if shape='marker')
        exclude_border: Whether to exclude outline near image borders
        border_margin: Distance from border to exclude (in pixels)
        shape_type: Type of marker ('circle', 'square', 'triangle', 'diamond', 'star', 'cross')
    
    Returns:
        Outline mask (white outline on black background)
    """
    # Find contours in the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Create empty image for outline
    outline = np.zeros_like(mask)
    
    # Get image dimensions
    height, width = mask.shape[:2]
    
    if shape == 'marker':
        # Draw markers along each contour
        for contour in contours:
            _draw_markers_along_contour(contour, outline, shape_spacing, shape_size,
                                       exclude_border, border_margin, shape_type, height, width)
    else:
        # Draw solid contour with specified thickness
        cv2.drawContours(outline, contours, -1, 255, outline_thickness)
        
        # If exclude_border is True, remove outline near borders
        if exclude_border:
            border_mask = _create_border_mask(height, width, border_margin)
            outline = cv2.bitwise_and(outline, border_mask)
    
    return outline

def overlay_outline_on_image(original_image, outline_mask, outline_color=(0, 255, 0), 
                            marker_color=None, shape='line'):
    """
    Overlay outline on original image.
    
    Args:
        original_image: Original BGR image
        outline_mask: Binary outline mask (0 or 255)
        outline_color: BGR color for the outline (default: green)
        marker_color: BGR color for markers (if None, uses outline_color)
        shape: Type of outline ('line' or 'marker')
    
    Returns:
        Image with outline overlay
    """
    # Convert outline mask to 3-channel if needed
    if len(original_image.shape) == 3 and original_image.shape[2] == 3:
        result = original_image.copy()
        
        # Use marker color if specified and shape is marker, otherwise use outline color
        color = marker_color if (marker_color is not None and shape == 'marker') else outline_color
        
        # Create colored outline
        colored_outline = np.zeros_like(original_image)
        colored_outline[outline_mask > 0] = color
        
        # Blend outline with original image
        # Simple overlay: where outline exists, use outline color
        result[outline_mask > 0] = colored_outline[outline_mask > 0]
        
        return result
    else:
        raise ValueError("Original image must be 3-channel BGR")

def remove_background_in_memory(image_path):
    """
    Remove background from an image in memory without saving to disk.
    
    Args:
        image_path: Path to input image
    
    Returns:
        numpy.ndarray: Background-removed image with alpha channel (RGBA)
    """
    print(f"Removing background from: {image_path}")
    
    # Read the input image
    with open(image_path, 'rb') as f:
        input_data = f.read()
    
    # Remove background (rembg automatically uses CPU if no GPU available)
    print("Processing background removal...")
    output_data = remove(input_data)
    
    # Convert bytes to numpy array
    nparr = np.frombuffer(output_data, np.uint8)
    bg_removed = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
    
    if bg_removed is None:
        raise ValueError("Failed to decode background-removed image")
    
    print(f"Background removal completed. Image shape: {bg_removed.shape}")
    return bg_removed

def _generate_output_path(input_path, shape, output_path=None):
    """Generate output path if not provided."""
    if output_path is not None:
        return output_path
    
    input_path_obj = Path(input_path)
    suffix = "_marker_outline" if shape == 'marker' else "_outline"
    return str(input_path_obj.parent / f"{input_path_obj.stem}{suffix}_overlay.png")

def _ensure_same_dimensions(image1, image2):
    """Ensure two images have the same dimensions."""
    if image1.shape[:2] != image2.shape[:2]:
        print(f"Resizing image to match dimensions")
        return cv2.resize(image1, (image2.shape[1], image2.shape[0]))
    return image1

def _save_debug_images(output_path, mask, expanded_mask, outline):
    """Save intermediate debug images."""
    debug_dir = Path(output_path).parent / "debug_outline"
    debug_dir.mkdir(exist_ok=True)
    
    cv2.imwrite(str(debug_dir / "1_original_mask.png"), mask)
    cv2.imwrite(str(debug_dir / "2_expanded_mask.png"), expanded_mask)
    cv2.imwrite(str(debug_dir / "3_outline.png"), outline)
    
    print(f"Intermediate debug images saved to: {debug_dir}")

def process_image_with_auto_bg_removal(original_path, output_path=None, 
                  expansion_pixels=5, outline_thickness=2, outline_color=(0, 255, 0),
                  shape='line', shape_spacing=10, shape_size=3, exclude_border=True, 
                  border_margin=5, shape_type='circle', marker_color=None):
    """
    Process image with automatic background removal (no intermediate file saved).
    
    Args:
        original_path: Path to original image
        output_path: Path to save output image
        expansion_pixels: Pixels to expand mask
        outline_thickness: Thickness of outline (for solid lines)
        outline_color: BGR color for outline
        shape: Type of outline ('line' or 'marker')
        shape_spacing: Distance between shapes in pixels (if shape='marker')
        shape_size: Size of shapes in pixels (if shape='marker')
        exclude_border: Whether to exclude outline near image borders
        border_margin: Distance from border to exclude (in pixels)
        shape_type: Type of marker ('circle', 'square', 'triangle', 'diamond', 'star', 'cross')
        marker_color: BGR color for markers (if None, uses outline_color)
    
    Returns:
        Path to saved output image
    """
    print(f"Processing image with automatic background removal: {original_path}")
    
    # Set default output path
    output_path = _generate_output_path(original_path, shape, output_path)
    print(f"Output will be saved to: {output_path}")
    
    # Step 1: Remove background in memory
    bg_removed = remove_background_in_memory(original_path)
    
    # Step 2: Load original image
    print("Loading original image...")
    original = load_image(original_path)
    
    # Ensure images have same dimensions
    bg_removed = _ensure_same_dimensions(bg_removed, original)
    
    # Step 3: Create mask from alpha channel
    print("Creating mask from alpha channel...")
    mask = create_mask_from_alpha(bg_removed)
    
    # Step 4: Expand the mask
    print(f"Expanding mask by {expansion_pixels} pixels...")
    expanded_mask = expand_mask(mask, expansion_pixels)
    
    # Step 5: Get outline of expanded mask
    if shape == 'marker':
        print(f"Extracting {shape_type} markers (size: {shape_size}px, spacing: {shape_spacing}px)...")
    else:
        print(f"Extracting solid outline (thickness: {outline_thickness}px)...")
    
    if exclude_border:
        print(f"Excluding outline within {border_margin}px of image border...")
    
    outline = get_mask_outline(expanded_mask, outline_thickness, shape, shape_spacing, 
                              shape_size, exclude_border, border_margin, shape_type)
    
    # Step 6: Overlay outline on original image
    print("Overlaying outline on original image...")
    result = overlay_outline_on_image(original, outline, outline_color, marker_color, shape)
    
    # Save result
    print(f"Saving result to: {output_path}")
    cv2.imwrite(output_path, result)
    
    # Also save intermediate images for debugging
    _save_debug_images(output_path, mask, expanded_mask, outline)
    
    print(f"Outline overlay saved to: {output_path}")
    
    return output_path

def process_image_with_params(params: ProcessingParams):
    """
    Process image using ProcessingParams object.
    
    Args:
        params: ProcessingParams object containing all processing parameters
    
    Returns:
        Path to saved output image
    """
    outline_params = params.outline_params
    
    print(f"Processing image with parameters:")
    print(f"  Original: {params.original_path}")
    print(f"  BG Removed: {params.bg_removed_path}")
    print(f"  Output: {params.output_path}")
    
    # Load images
    print("Loading images...")
    original = load_image(params.original_path)
    
    if params.bg_removed_path:
        bg_removed = load_image(params.bg_removed_path)
    else:
        # Auto background removal
        print("Removing background automatically...")
        bg_removed = remove_background_in_memory(params.original_path)
    
    # Ensure images have same dimensions
    bg_removed = _ensure_same_dimensions(bg_removed, original)
    
    # Create mask from alpha channel
    print("Creating mask from alpha channel...")
    mask = create_mask_from_alpha(bg_removed)
    
    # Expand the mask
    print(f"Expanding mask by {outline_params.expansion_pixels} pixels...")
    expanded_mask = expand_mask(mask, outline_params.expansion_pixels)
    
    # Get outline of expanded mask
    if outline_params.shape == 'marker':
        print(f"Extracting {outline_params.shape_type} markers (size: {outline_params.shape_size}px, spacing: {outline_params.shape_spacing}px)...")
    else:
        print(f"Extracting solid outline (thickness: {outline_params.outline_thickness}px)...")
    
    if outline_params.should_exclude_border:
        print(f"Excluding outline within {outline_params.border_margin}px of image border...")
    
    outline = get_mask_outline(
        expanded_mask, 
        outline_params.outline_thickness, 
        outline_params.shape, 
        outline_params.shape_spacing, 
        outline_params.shape_size, 
        outline_params.should_exclude_border, 
        outline_params.border_margin, 
        outline_params.shape_type
    )
    
    # Overlay outline on original image
    print("Overlaying outline on original image...")
    result = overlay_outline_on_image(
        original, 
        outline, 
        outline_params.outline_color, 
        outline_params.marker_color, 
        outline_params.shape
    )
    
    # Generate output path if not provided
    if params.output_path is None:
        input_path = params.bg_removed_path if params.bg_removed_path else params.original_path
        params.output_path = _generate_output_path(input_path, outline_params.shape)
    
    # Save result
    print(f"Saving result to: {params.output_path}")
    cv2.imwrite(params.output_path, result)
    
    # Save debug images
    _save_debug_images(params.output_path, mask, expanded_mask, outline)
    
    print(f"Outline overlay saved to: {params.output_path}")
    
    return params.output_path

def process_image(bg_removed_path, original_path=None, output_path=None, 
                  expansion_pixels=5, outline_thickness=2, outline_color=(0, 255, 0),
                  shape='line', shape_spacing=10, shape_size=3, exclude_border=True, 
                  border_margin=5, shape_type='circle', marker_color=None):
    """
    Main processing function (legacy interface).
    
    Args:
        bg_removed_path: Path to background-removed image (from remove_bg.py)
        original_path: Path to original image (default: here2.jpg)
        output_path: Path to save output image
        expansion_pixels: Pixels to expand mask
        outline_thickness: Thickness of outline (for solid lines)
        outline_color: BGR color for outline
        shape: Type of outline ('line' or 'marker')
        shape_spacing: Distance between shapes in pixels (if shape='marker')
        shape_size: Size of shapes in pixels (if shape='marker')
        exclude_border: Whether to exclude outline near image borders
        border_margin: Distance from border to exclude (in pixels)
        shape_type: Type of marker ('circle', 'square', 'triangle', 'diamond', 'star', 'cross')
        marker_color: BGR color for markers (if None, uses outline_color)
    
    Returns:
        Path to saved output image
    """
    # Set default original image
    if original_path is None:
        original_path = "here2.jpg"
    
    # Create parameter objects
    outline_params = OutlineParams(
        expansion_pixels=expansion_pixels,
        outline_thickness=outline_thickness,
        outline_color=outline_color,
        shape=shape,
        shape_spacing=shape_spacing,
        shape_size=shape_size,
        should_exclude_border=exclude_border,
        border_margin=border_margin,
        shape_type=shape_type,
        marker_color=marker_color
    )
    
    processing_params = ProcessingParams(
        original_path=original_path,
        bg_removed_path=bg_removed_path,
        output_path=output_path,
        outline_params=outline_params
    )
    
    return process_image_with_params(processing_params)

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Create outline overlay from images with optional automatic background removal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Basic usage with automatic background removal (green solid line):
    %(prog)s -i here2.jpg
  
  Use pre-existing background-removed image:
    %(prog)s -i here2.jpg -b here2_nobg.png
  
  Custom solid line with different color and thickness:
    %(prog)s -i input.jpg -e 10 -t 3 -c "255,0,0"
  
  Circle markers along the outline:
    %(prog)s -i input.jpg --shape marker --shape-type circle --shape-size 5 --shape-spacing 15
  
  Square markers with custom color:
    %(prog)s -i input.jpg --shape marker --shape-type square --shape-size 4 --shape-spacing 12 --marker-color "0,0,255"
  
  Triangle markers with border exclusion:
    %(prog)s -i input.jpg --shape marker --shape-type triangle --shape-size 6 --shape-spacing 20 --border-margin 10
  
  Diamond markers with large expansion:
    %(prog)s -i input.jpg --shape marker --shape-type diamond -e 15 --shape-size 8 --shape-spacing 25
  
  Star markers with different colors for outline and markers:
    %(prog)s -i input.jpg --shape marker --shape-type star -c "0,255,0" --marker-color "255,0,255" --shape-size 7 --shape-spacing 18
  
  Cross markers with thick lines:
    %(prog)s -i input.jpg --shape marker --shape-type cross --shape-size 5 --shape-spacing 15 -t 2
  
  Include border outlines (default is to exclude):
    %(prog)s -i input.jpg --include-border -e 8 -t 2
  
  Custom output filename:
    %(prog)s -i input.jpg -o custom_output.png -e 5 -t 2
  
  Multiple options combined:
    %(prog)s -i input.jpg --shape marker --shape-type circle --shape-size 4 --shape-spacing 12 -e 8 --border-margin 8 -c "255,128,0"
        """
    )
    
    # Input/output arguments
    parser.add_argument("-i", "--input", default="here2.jpg",
                       help="Input original image (default: here2.jpg)")
    parser.add_argument("-b", "--bg-removed", default=None,
                       help="Optional: Background-removed image. If not provided, background will be removed automatically.")
    parser.add_argument("-o", "--output",
                       help="Output image path (default: auto-generated)")
    
    # Outline style arguments
    parser.add_argument("-e", "--expansion", type=int, default=5,
                       help="Pixels to expand mask (default: 5)")
    parser.add_argument("-t", "--thickness", type=int, default=2,
                       help="Outline thickness for solid lines (default: 2)")
    parser.add_argument("-c", "--color", default="0,255,0",
                       help="Outline color as BGR values (default: 0,255,0 = green)")
    
    # Shape/style arguments
    parser.add_argument("--shape", choices=['line', 'marker'], default='line',
                       help="Outline shape: 'line' for solid line, 'marker' for shapes (default: line)")
    parser.add_argument("--shape-type", choices=['circle', 'square', 'triangle', 'diamond', 'star', 'cross'], 
                       default='circle', help="Type of marker (default: circle)")
    parser.add_argument("--shape-spacing", type=int, default=10,
                       help="Distance between shapes in pixels (default: 10)")
    parser.add_argument("--shape-size", type=int, default=3,
                       help="Size of shapes in pixels (default: 3)")
    
    # Color arguments
    parser.add_argument("--marker-color", default=None,
                       help="BGR color for markers (e.g., '255,0,0' for red). If not set, uses --color")
    
    # Border exclusion argument
    parser.add_argument("--include-border", action="store_true",
                       help="Include outline near image borders (default: exclude)")
    parser.add_argument("--border-margin", type=int, default=5,
                       help="Distance from border to exclude (in pixels, default: 5)")
    
    args = parser.parse_args()
    
    # Parse color argument
    try:
        color_parts = args.color.split(",")
        if len(color_parts) == 3:
            outline_color = (int(color_parts[0]), int(color_parts[1]), int(color_parts[2]))
        else:
            print(f"Warning: Invalid color format '{args.color}'. Using default green.")
            outline_color = (0, 255, 0)
    except ValueError:
        print(f"Warning: Could not parse color '{args.color}'. Using default green.")
        outline_color = (0, 255, 0)
    
    # Check if original image exists
    if not os.path.exists(args.input):
        print(f"Original image '{args.input}' not found.")
        
        # Look for any image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
        image_files = [f for f in os.listdir('.') 
                      if os.path.isfile(f) and Path(f).suffix.lower() in image_extensions]
        
        if image_files:
            print(f"Found image files: {', '.join(image_files)}")
            print("Please specify the correct input image using -i flag.")
        sys.exit(1)
    
    # Parse marker color argument
    marker_color = None
    if args.marker_color:
        try:
            color_parts = args.marker_color.split(",")
            if len(color_parts) == 3:
                marker_color = (int(color_parts[0]), int(color_parts[1]), int(color_parts[2]))
            else:
                print(f"Warning: Invalid marker color format '{args.marker_color}'. Using outline color.")
        except ValueError:
            print(f"Warning: Could not parse marker color '{args.marker_color}'. Using outline color.")
    
    # Determine processing mode
    use_auto_bg_removal = args.bg_removed is None
    
    if use_auto_bg_removal:
        print("="*60)
        print("AUTOMATIC BACKGROUND REMOVAL MODE")
        print("="*60)
        print("No background-removed image provided.")
        print("Background will be removed automatically in memory.")
        print("No intermediate files will be saved.")
        print("="*60)
    else:
        # Check if provided background-removed image exists
        if not os.path.exists(args.bg_removed):
            print(f"Background-removed image '{args.bg_removed}' not found.")
            print("Please run remove_bg.py first or provide the correct path.")
            
            # Look for any *_nobg.png files
            nobg_files = [f for f in os.listdir('.') 
                         if f.endswith('_nobg.png') and os.path.isfile(f)]
            
            if nobg_files:
                print(f"Found potential background-removed images: {', '.join(nobg_files)}")
                args.bg_removed = nobg_files[0]
                print(f"Using: {args.bg_removed}")
                use_auto_bg_removal = False
            else:
                print("No background-removed images found.")
                print("Switching to automatic background removal mode...")
                use_auto_bg_removal = True
    
    # Create outline parameters
    outline_params = OutlineParams(
        expansion_pixels=args.expansion,
        outline_thickness=args.thickness,
        outline_color=outline_color,
        shape=args.shape,
        shape_spacing=args.shape_spacing,
        shape_size=args.shape_size,
        should_exclude_border=not args.include_border,  # Default is to exclude border
        border_margin=args.border_margin,
        shape_type=args.shape_type,
        marker_color=marker_color
    )
    
    # Create processing parameters
    processing_params = ProcessingParams(
        original_path=args.input,
        bg_removed_path=args.bg_removed,
        output_path=args.output,
        outline_params=outline_params
    )
    
    # Process the image
    try:
        output_path = process_image_with_params(processing_params)
        
        print("\n" + "="*60)
        print("Outline creation completed successfully!")
        print(f"Input image: {args.input}")
        if args.bg_removed:
            print(f"Background removed image: {args.bg_removed}")
        print(f"Output: {output_path}")
        print(f"Processing mode: {'Automatic background removal' if use_auto_bg_removal else 'Pre-existing background-removed image'}")
        
        if args.shape == 'marker':
            print(f"Outline style: {args.shape_type} markers (size: {args.shape_size}px, spacing: {args.shape_spacing}px)")
            if marker_color:
                print(f"Marker color: BGR{marker_color}")
            else:
                print(f"Marker color: BGR{outline_color} (same as outline)")
        else:
            print(f"Outline style: Solid line (thickness: {args.thickness}px)")
            print(f"Outline color: BGR{outline_color}")
        
        print(f"Mask expansion: {args.expansion}px")
        print(f"Border exclusion: {'Enabled' if not args.include_border else 'Disabled'}")
        if not args.include_border:
            print(f"Border margin: {args.border_margin}px")
        print("="*60)
        
    except Exception as e:
        print(f"\nError processing image: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
