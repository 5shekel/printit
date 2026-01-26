"""Image processing and conversion utilities for the Sticker Factory."""

import logging
from PIL import Image, ImageOps

logger = logging.getLogger("sticker_factory.image_utils")


def preper_image(image, label_width):
    """Prepare image by resizing and dithering for thermal printer output."""
    if image.mode == "RGBA":
        background = Image.new("RGBA", image.size, "white")
        image = Image.alpha_composite(background, image)
        image = image.convert("RGB")

    width, height = image.size
    if width != label_width:
        new_height = int((label_width / width) * height)
        image = image.resize((label_width, new_height))
        logger.debug(f"Resizing image from ({width}, {height}) >> {image.size}")

    if image.mode != "L":
        grayscale_image = image.convert("L")
    else:
        grayscale_image = image

    dithered_image = grayscale_image.convert("1", dither=Image.FLOYDSTEINBERG)

    return grayscale_image, dithered_image


def apply_threshold(image, threshold):
    """Apply threshold to convert image to black and white."""
    if image.mode != 'L':
        image = image.convert('L')
    lut = [255 if i > threshold else 0 for i in range(256)]
    return image.point(lut, mode='1')


def resize_image_to_width(image, target_width_mm, label_width, current_dpi=300):
    """Resize image to specific width in millimeters."""
    target_width_inch = target_width_mm / 25.4
    target_width_px = int(target_width_inch * current_dpi)
    current_width = image.width
    scale_factor = target_width_px / current_width
    new_height = int(image.height * scale_factor)
    resized_image = image.resize((target_width_px, new_height), Image.LANCZOS)

    if target_width_px < label_width:
        new_image = Image.new("RGB", (label_width, new_height), (255, 255, 255))
        new_image.paste(resized_image, ((label_width - target_width_px) // 2, 0))
        resized_image = new_image

    logger.debug(f"Image resized from {image.width}x{image.height} to {resized_image.width}x{resized_image.height} pixels.")
    logger.debug(f"Target width was {target_width_mm}mm ({target_width_px}px)")
    return resized_image


def add_border(image, border_width=1):
    """Add a thin black border around the image."""
    if image.mode == '1':
        bordered = Image.new('1', (image.width + 2*border_width, image.height + 2*border_width), 0)
        bordered.paste(image, (border_width, border_width))
        return bordered
    else:
        return ImageOps.expand(image, border=border_width, fill='black')


def apply_levels(image, black_point=0, white_point=255):
    """Apply levels adjustment to an image."""
    if image.mode != 'L':
        image = image.convert('L')
    
    lut = []
    for i in range(256):
        if i <= black_point:
            lut.append(0)
        elif i >= white_point:
            lut.append(255)
        else:
            normalized = (i - black_point) / (white_point - black_point)
            lut.append(int(normalized * 255))
    
    return image.point(lut)


def apply_histogram_equalization(image, black_point=0, white_point=255):
    """Apply histogram equalization with levels adjustment to an image."""
    if image.mode != 'L':
        image = image.convert('L')
    
    leveled = apply_levels(image, black_point, white_point)
    return ImageOps.equalize(leveled)


def img_concat_v(im1, im2, image_width):
    """Vertically concatenate two images."""
    dst = Image.new("RGB", (im1.width, im1.height + image_width))
    dst.paste(im1, (0, 0))
    im2 = im2.resize((image_width, image_width))
    dst.paste(im2, (0, im1.height))
    return dst


def find_figure_bounds(image, background_threshold=240):
    """Find bounding box of main figure in image.
    
    Args:
        image: PIL Image
        background_threshold: RGB value threshold for considering pixel as background (0-255)
    
    Returns:
        Tuple (min_x, min_y, max_x, max_y) or None if no figure found
    """
    if image.mode == 'RGBA':
        # Use alpha channel for transparent images
        alpha = image.getchannel('A')
        width, height = image.size
        
        min_x, min_y = width, height
        max_x, max_y = 0, 0
        
        for y in range(height):
            for x in range(width):
                if alpha.getpixel((x, y)) > 0:  # Non-transparent pixel
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
        
        if min_x < max_x and min_y < max_y:
            return (min_x, min_y, max_x, max_y)
    
    # For RGB images, detect non-background pixels
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    width, height = image.size
    pixels = image.load()
    
    min_x, min_y = width, height
    max_x, max_y = 0, 0
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            # Check if pixel is significantly different from white
            if r < background_threshold or g < background_threshold or b < background_threshold:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
    
    if min_x < max_x and min_y < max_y:
        return (min_x, min_y, max_x, max_y)
    
    return None


def draw_dashed_line(draw, start, end, dash_length=10, gap_length=5, width=2, fill=(0, 0, 0)):
    """Draw dashed line between two points.
    
    Args:
        draw: PIL ImageDraw object
        start: (x1, y1) start point
        end: (x2, y2) end point
        dash_length: Length of each dash in pixels
        gap_length: Length of gap between dashes in pixels
        width: Line width
        fill: Line color
    """
    import math
    
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1
    distance = math.sqrt(dx**2 + dy**2)
    
    if distance == 0:
        return
    
    # Normalize direction
    dx /= distance
    dy /= distance
    
    # Draw dashes
    step = dash_length + gap_length
    for d in range(0, int(distance), step):
        start_d = d
        end_d = min(d + dash_length, distance)
        
        x_start = x1 + dx * start_d
        y_start = y1 + dy * start_d
        x_end = x1 + dx * end_d
        y_end = y1 + dy * end_d
        
        draw.line([(x_start, y_start), (x_end, y_end)], fill=fill, width=width)


def add_cutting_guide(image, guide_type="dashed", spacing=15, margin=5, background_threshold=240):
    """Add cutting guide around the main figure in image.
    
    Args:
        image: PIL Image to add guides to
        guide_type: "dashed", "dotted", "scissors_icon", "perforated"
        spacing: Spacing between guide marks in pixels
        margin: Distance from figure edge to cut line in pixels
        background_threshold: RGB threshold for background detection (0-255)
    
    Returns:
        PIL Image with cutting guides added around the figure
    """
    from PIL import ImageDraw
    
    # Find figure bounds
    bounds = find_figure_bounds(image, background_threshold)
    
    if bounds is None:
        # If no figure detected, use whole image
        bounds = (0, 0, image.width, image.height)
    
    min_x, min_y, max_x, max_y = bounds
    
    # Calculate bounds with margin
    guide_left = max(0, min_x - margin)
    guide_top = max(0, min_y - margin)
    guide_right = min(image.width, max_x + margin)
    guide_bottom = min(image.height, max_y + margin)
    
    # Create new image with white background (same size as original)
    guide_image = Image.new("RGB", image.size, (255, 255, 255))
    guide_image.paste(image)
    
    draw = ImageDraw.Draw(guide_image)
    
    if guide_type == "dashed":
        # Draw dashed rectangle around figure
        dash_length = 10
        gap_length = 5
        
        # Top edge
        draw_dashed_line(draw, 
                        (guide_left, guide_top), 
                        (guide_right, guide_top),
                        dash_length, gap_length, 2, (0, 0, 0))
        
        # Bottom edge
        draw_dashed_line(draw,
                        (guide_left, guide_bottom),
                        (guide_right, guide_bottom),
                        dash_length, gap_length, 2, (0, 0, 0))
        
        # Left edge
        draw_dashed_line(draw,
                        (guide_left, guide_top),
                        (guide_left, guide_bottom),
                        dash_length, gap_length, 2, (0, 0, 0))
        
        # Right edge
        draw_dashed_line(draw,
                        (guide_right, guide_top),
                        (guide_right, guide_bottom),
                        dash_length, gap_length, 2, (0, 0, 0))
    
    elif guide_type == "dotted":
        # Draw dotted rectangle
        for x in range(guide_left, guide_right, spacing):
            if x <= guide_right:
                draw.ellipse([x-2, guide_top-2, x+2, guide_top+2], fill=(0, 0, 0))
                draw.ellipse([x-2, guide_bottom-2, x+2, guide_bottom+2], fill=(0, 0, 0))
        
        for y in range(guide_top, guide_bottom, spacing):
            if y <= guide_bottom:
                draw.ellipse([guide_left-2, y-2, guide_left+2, y+2], fill=(0, 0, 0))
                draw.ellipse([guide_right-2, y-2, guide_right+2, y+2], fill=(0, 0, 0))
    
    return guide_image


def cut_image_width(image, cut_position):
    """Cut an image at a specific width position.
    
    Args:
        image: PIL Image to cut
        cut_position: Pixel position (1 to image.width-1) where to cut
        
    Returns:
        Tuple of (left_image, right_image) - two images split at cut_position
    """
    if cut_position < 1 or cut_position >= image.width:
        raise ValueError(f"cut_position must be between 1 and {image.width-1}")
    
    # Crop left part (0 to cut_position-1)
    left_box = (0, 0, cut_position, image.height)
    left_image = image.crop(left_box)
    
    # Crop right part (cut_position to end)
    right_box = (cut_position, 0, image.width, image.height)
    right_image = image.crop(right_box)
    
    return left_image, right_image


def add_width_cut_indicator(image, cut_position, line_width=3, color=(255, 0, 0)):
    """Add a visual indicator showing where the image will be cut.
    
    Args:
        image: PIL Image to add indicator to
        cut_position: Pixel position where cut will occur
        line_width: Width of the indicator line
        color: Color of the indicator line (RGB tuple)
        
    Returns:
        PIL Image with cut indicator added
    """
    from PIL import ImageDraw
    
    # Create a copy to draw on
    indicator_image = image.copy()
    if indicator_image.mode != 'RGB':
        indicator_image = indicator_image.convert('RGB')
    
    draw = ImageDraw.Draw(indicator_image)
    
    # Draw vertical line at cut position
    draw.line([(cut_position, 0), (cut_position, image.height)], 
              fill=color, width=line_width)
    
    # Add arrow indicators
    arrow_size = 10
    # Top arrow
    draw.polygon([
        (cut_position, arrow_size),
        (cut_position - arrow_size, 0),
        (cut_position + arrow_size, 0)
    ], fill=color)
    
    # Bottom arrow
    draw.polygon([
        (cut_position, image.height - arrow_size),
        (cut_position - arrow_size, image.height),
        (cut_position + arrow_size, image.height)
    ], fill=color)
    
    # Add text label
    try:
        from PIL import ImageFont
        font = ImageFont.load_default()
        text = f"Cut at {cut_position}px"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Position text near the cut line
        text_x = cut_position - text_width // 2
        text_y = image.height // 2 - text_height // 2
        
        # Draw text with background for visibility
        draw.rectangle([text_x-2, text_y-2, text_x+text_width+2, text_y+text_height+2], 
                      fill=(255, 255, 255))
        draw.text((text_x, text_y), text, fill=color, font=font)
    except:
        # If font loading fails, just draw without text
        pass
    
    return indicator_image


def cut_image_into_strips(image, num_strips):
    """Cut an image into N equal-width strips.
    
    Args:
        image: PIL Image to cut
        num_strips: Number of equal-width strips to create (1 to reasonable max)
        
    Returns:
        List of PIL Images - the strips from left to right
    """
    if num_strips < 1:
        raise ValueError(f"num_strips must be at least 1, got {num_strips}")
    
    if num_strips > image.width:
        raise ValueError(f"num_strips ({num_strips}) cannot exceed image width ({image.width})")
    
    image_width = image.width
    image_height = image.height
    
    # Calculate strip width (integer division)
    strip_width = image_width // num_strips
    remainder = image_width % num_strips
    
    strips = []
    current_x = 0
    
    for i in range(num_strips):
        # Distribute remainder pixels among first few strips
        extra_pixel = 1 if i < remainder else 0
        current_strip_width = strip_width + extra_pixel
        
        # Crop strip using same pattern as cut_image_width
        strip_box = (current_x, 0, current_x + current_strip_width, image_height)
        strip_image = image.crop(strip_box)
        strips.append(strip_image)
        
        current_x += current_strip_width
    
    return strips


def add_strip_cut_indicators(image, num_strips, line_width=2, color=(255, 0, 0)):
    """Add visual indicators showing where the image will be cut into strips.
    
    Args:
        image: PIL Image to add indicators to
        num_strips: Number of equal-width strips
        line_width: Width of the indicator lines
        color: Color of the indicator lines (RGB tuple)
        
    Returns:
        PIL Image with strip cut indicators added
    """
    from PIL import ImageDraw
    
    # Create a copy to draw on
    indicator_image = image.copy()
    if indicator_image.mode != 'RGB':
        indicator_image = indicator_image.convert('RGB')
    
    draw = ImageDraw.Draw(indicator_image)
    
    image_width = image.width
    image_height = image.height
    
    # Calculate strip width
    strip_width = image_width // num_strips
    remainder = image_width % num_strips
    
    current_x = 0
    
    # Draw cut lines between strips (skip the first line at x=0)
    for i in range(1, num_strips):
        # Calculate x position for this cut line
        extra_pixel = 1 if (i - 1) < remainder else 0
        current_x += strip_width + extra_pixel
        
        # Draw vertical line using same visual style as add_width_cut_indicator
        draw.line([(current_x, 0), (current_x, image_height)], 
                  fill=color, width=line_width)
        
        # Add arrow indicators (smaller than single cut indicator)
        arrow_size = 8
        # Top arrow
        draw.polygon([
            (current_x, arrow_size),
            (current_x - arrow_size, 0),
            (current_x + arrow_size, 0)
        ], fill=color)
        
        # Bottom arrow
        draw.polygon([
            (current_x, image_height - arrow_size),
            (current_x - arrow_size, image.height),
            (current_x + arrow_size, image.height)
        ], fill=color)
    
    # Add text label
    try:
        from PIL import ImageFont
        font = ImageFont.load_default()
        text = f"Cut into {num_strips} equal strips"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Position text at top center
        text_x = (image_width - text_width) // 2
        text_y = 10
        
        # Draw text with background for visibility
        draw.rectangle([text_x-2, text_y-2, text_x+text_width+2, text_y+text_height+2], 
                      fill=(255, 255, 255))
        draw.text((text_x, text_y), text, fill=color, font=font)
    except:
        # If font loading fails, just draw without text
        pass
    
    return indicator_image
