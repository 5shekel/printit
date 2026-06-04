#!/usr/bin/env python3
"""
Test script for cutting guides functionality.
Takes an input image, adds dashed cutting guides, and saves the result.
"""

import sys
import os
from PIL import Image

# Add current directory to path to import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_cutting_guides(input_image_path, output_image_path=None, guide_type="dashed", spacing=15, margin=5):
    """
    Test the cutting guides functionality on an image.
    
    Args:
        input_image_path: Path to input image
        output_image_path: Path to save output image (default: input_image_path with '_with_guides' suffix)
        guide_type: Type of cutting guide ("dashed", "dotted")
        spacing: Spacing between guide marks in pixels
        margin: Distance from image edge to cut line in pixels
    
    Returns:
        Path to saved output image
    """
    try:
        # Import the cutting guide function
        from image_utils import add_cutting_guide
        
        # Load the input image
        print(f"Loading image: {input_image_path}")
        image = Image.open(input_image_path).convert("RGB")
        print(f"  Original size: {image.width}x{image.height}")
        
        # Add cutting guides
        print(f"Adding {guide_type} cutting guides...")
        print(f"  Guide spacing: {spacing}px")
        print(f"  Cut margin: {margin}px")
        
        image_with_guides = add_cutting_guide(
            image, 
            guide_type=guide_type,
            spacing=spacing,
            margin=margin
        )
        
        print(f"  New size with margin: {image_with_guides.width}x{image_with_guides.height}")
        
        # Determine output path
        if output_image_path is None:
            base, ext = os.path.splitext(input_image_path)
            output_image_path = f"{base}_with_guides{ext}"
        
        # Save the result
        print(f"Saving result to: {output_image_path}")
        image_with_guides.save(output_image_path)
        
        print(f"\n✅ Success! Image with cutting guides saved to: {output_image_path}")
        return output_image_path
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the printit directory and image_utils.py is available.")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main function with command line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Add cutting guides to an image')
    parser.add_argument('input_image', help='Path to input image file')
    parser.add_argument('-o', '--output', help='Output image path (default: input_with_guides.ext)')
    parser.add_argument('-t', '--type', default='dashed', choices=['dashed', 'dotted'],
                       help='Type of cutting guide (default: dashed)')
    parser.add_argument('-s', '--spacing', type=int, default=15,
                       help='Spacing between guide marks in pixels (default: 15)')
    parser.add_argument('-m', '--margin', type=int, default=5,
                       help='Distance from edge to cut line in pixels (default: 5)')
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input_image):
        print(f"❌ Error: Input file '{args.input_image}' not found")
        sys.exit(1)
    
    # Run the test
    result = test_cutting_guides(
        input_image_path=args.input_image,
        output_image_path=args.output,
        guide_type=args.type,
        spacing=args.spacing,
        margin=args.margin
    )
    
    if result is None:
        sys.exit(1)

if __name__ == "__main__":
    main()

# Example usage without command line arguments:
def example_usage():
    """
    Example of how to use the cutting guides function programmatically.
    """
    # This is an example - you would need to provide a real image path
    example_image = "example.jpg"  # Replace with actual image path
    
    if os.path.exists(example_image):
        print("Running example...")
        test_cutting_guides(
            input_image_path=example_image,
            guide_type="dashed",
            spacing=15,
            margin=5
        )
    else:
        print(f"Example image '{example_image}' not found.")
        print("To test with your own image:")
        print("  python test_cutting_guides.py your_image.jpg")
        print("\nOr with options:")
        print("  python test_cutting_guides.py your_image.jpg -t dotted -s 20 -m 10")