#!/usr/bin/env python3
"""
Simple test script for cutting guides functionality.
Creates a test image, adds cutting guides, and saves it.
"""

import sys
import os
from PIL import Image, ImageDraw

# Add current directory to path to import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_image(width=200, height=150, output_path="test_image.png"):
    """Create a simple test image for testing cutting guides."""
    # Create a simple image with some shapes
    image = Image.new("RGB", (width, height), (240, 240, 240))
    draw = ImageDraw.Draw(image)
    
    # Draw a rectangle
    draw.rectangle([20, 20, width-20, height-20], outline=(0, 0, 0), width=2)
    
    # Draw some text
    from PIL import ImageFont
    try:
        font = ImageFont.truetype("fonts/5x5-Tami.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    draw.text((width//2 - 40, height//2 - 10), "TEST", fill=(0, 0, 0), font=font)
    
    # Save the test image
    image.save(output_path)
    print(f"Created test image: {output_path} ({width}x{height})")
    return output_path

def test_with_sample_image():
    """Test cutting guides with a sample image."""
    print("=== Cutting Guides Test ===\n")
    
    # Create a test image if one doesn't exist
    test_image_path = "test_image.png"
    if not os.path.exists(test_image_path):
        print("Creating test image...")
        test_image_path = create_test_image()
    
    try:
        # Import the cutting guide function
        from image_utils import add_cutting_guide
        
        # Load the test image
        print(f"\nLoading test image: {test_image_path}")
        image = Image.open(test_image_path).convert("RGB")
        print(f"Original size: {image.width}x{image.height}")
        
        # Test 1: Dashed lines
        print("\n--- Test 1: Dashed Cutting Guides ---")
        dashed_image = add_cutting_guide(
            image, 
            guide_type="dashed",
            spacing=15,
            margin=5
        )
        dashed_output = "test_dashed_guides.png"
        dashed_image.save(dashed_output)
        print(f"Saved to: {dashed_output}")
        print(f"New size: {dashed_image.width}x{dashed_image.height}")
        
        # Test 2: Dotted lines
        print("\n--- Test 2: Dotted Cutting Guides ---")
        dotted_image = add_cutting_guide(
            image,
            guide_type="dotted",
            spacing=20,
            margin=8
        )
        dotted_output = "test_dotted_guides.png"
        dotted_image.save(dotted_output)
        print(f"Saved to: {dotted_output}")
        print(f"New size: {dotted_image.width}x{dotted_image.height}")
        
        # Test 3: Different parameters
        print("\n--- Test 3: Custom Parameters ---")
        custom_image = add_cutting_guide(
            image,
            guide_type="dashed",
            spacing=10,
            margin=15
        )
        custom_output = "test_custom_guides.png"
        custom_image.save(custom_output)
        print(f"Saved to: {custom_output}")
        print(f"New size: {custom_image.width}x{custom_image.height}")
        
        print("\n=== Test Summary ===")
        print(f"1. Dashed guides: {dashed_output}")
        print(f"2. Dotted guides: {dotted_output}")
        print(f"3. Custom guides: {custom_output}")
        print("\n✅ All tests completed successfully!")
        print("\nTo view the results, open the PNG files in an image viewer.")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the printit directory.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def quick_test_existing_image(image_path):
    """Quick test with an existing image."""
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return False
    
    try:
        from image_utils import add_cutting_guide
        
        print(f"Processing: {image_path}")
        image = Image.open(image_path).convert("RGB")
        
        # Add dashed guides
        result = add_cutting_guide(image, guide_type="dashed", spacing=15, margin=5)
        
        # Save with suffix
        base, ext = os.path.splitext(image_path)
        output_path = f"{base}_with_dashed_guides{ext}"
        result.save(output_path)
        
        print(f"✅ Saved to: {output_path}")
        print(f"   Original: {image.width}x{image.height}")
        print(f"   With guides: {result.width}x{result.height}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    # Check if an image path was provided as command line argument
    if len(sys.argv) > 1:
        # Test with provided image
        image_path = sys.argv[1]
        quick_test_existing_image(image_path)
    else:
        # Run the full test with sample image
        test_with_sample_image()