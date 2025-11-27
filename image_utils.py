"""Image processing and conversion utilities for the Sticker Factory."""

from PIL import Image, ImageOps, ImageDraw, ImageFont
import io


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
        print(f"Resizing image from ({width}, {height}) >> {image.size}")

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

    print(f"Image resized from {image.width}x{image.height} to {resized_image.width}x{resized_image.height} pixels.")
    print(f"Target width was {target_width_mm}mm ({target_width_px}px)")
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
