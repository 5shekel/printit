#!/usr/bin/env python3
"""
Simple test script for width cutting functionality.
Tests the cut_image_width and add_width_cut_indicator functions.
"""

import sys
import os
from PIL import Image, ImageDraw

# Add current directory to path to import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_image(width=300, height=200, output_path="test_width_image.png"):
    """Create a simple test image for testing width cutting."""
    # Create a simple image with gradient and shapes
    image = Image.new("RGB", (width, height), (240, 240, 240))
    draw = ImageDraw.Draw(image)
    
    # Draw a gradient background
    for x in range(width):
        r = int(200 + (55 * x / width))
        g = int(200 + (55 * (width - x) / width))
        b = 200
        draw.line([(x, 0), (x, height)], fill=(r, g, b))
    
    # Draw a centered rectangle
    rect_width = width // 2
    rect_height = height // 2
    rect_x = (width - rect_width) // 2
    rect_y = (height - rect_height) // 2
    draw.rectangle([rect_x, rect_y, rect_x + rect_width, rect_y + rect_height], 
                   fill=(255, 100, 100), outline=(0, 0, 0), width=2)
    
    # Draw grid lines for reference
    for x in range(0, width, 50):
        draw.line([(x, 0), (x, height)], fill=(200, 200, 200), width=1)
    
    for y in range(0, height, 50):
        draw.line([(0, y), (width, y)], fill=(200, 200, 200), width=1)
    
    # Draw width markers
    for x in [0, width//4, width//2, 3*width//4, width-1]:
        draw.line([(x, 0), (x, 10)], fill=(0, 0, 0), width=2)
        draw.text((x-10, 15), str(x), fill=(0, 0, 0))
    
    # Add title
    from PIL import ImageFont
    try:
        font = ImageFont.truetype("fonts/5x5-Tami.ttf", 16)
    except:
        font = ImageFont.load_default()
    
    title = f"Test Image: {width}x{height}"
    draw.text((10, height-30), title, fill=(0, 0, 0), font=font)
    
    # Save the test image
    image.save(output_path)
    print(f"Created test image: {output_path} ({width}x{height})")
    return output_path, image

def test_width_cutting_functions():
    """Test the width cutting functions."""
    print("=== Width Cutting Functions Test ===\n")
    
    # Create a test image if one doesn't exist
    test_image_path = "test_width_image.png"
    if not os.path.exists(test_image_path):
        print("Creating test image...")
        test_image_path, test_image = create_test_image(width=300, height=200)
    else:
        print(f"Loading existing test image: {test_image_path}")
        test_image = Image.open(test_image_path).convert("RGB")
    
    try:
        # Import the width cutting functions
        from image_utils import cut_image_width, add_width_cut_indicator, cut_image_into_strips, add_strip_cut_indicators
        
        image_width = test_image.width
        image_height = test_image.height
        print(f"Test image size: {image_width}x{image_height}")
        
        # Test 1: Single cut at the middle (150px for 300px wide image)
        print("\n--- Test 1: Single Cut at Middle (150px) ---")
        cut_position = image_width // 2  # 150px
        
        left_image, right_image = cut_image_width(test_image, cut_position)
        
        print(f"Cut position: {cut_position}px")
        print(f"Left part size: {left_image.width}x{left_image.height}")
        print(f"Right part size: {right_image.width}x{right_image.height}")
        
        # Save the cut parts
        left_output = "test_left_part.png"
        right_output = "test_right_part.png"
        left_image.save(left_output)
        right_image.save(right_output)
        print(f"Saved left part to: {left_output}")
        print(f"Saved right part to: {right_output}")
        
        # Test 2: Cut into 3 equal strips
        print("\n--- Test 2: Cut into 3 Equal Strips ---")
        num_strips = 3
        
        strips = cut_image_into_strips(test_image, num_strips)
        
        print(f"Number of strips: {num_strips}")
        for i, strip in enumerate(strips, 1):
            print(f"  Strip {i}: {strip.width}x{strip.height}px")
        
        # Save the strips
        strip_outputs = []
        for i, strip in enumerate(strips, 1):
            output_path = f"test_strip_{i}_of_{num_strips}.png"
            strip.save(output_path)
            strip_outputs.append(output_path)
            print(f"Saved strip {i} to: {output_path}")
        
        # Test 3: Cut into 5 equal strips
        print("\n--- Test 3: Cut into 5 Equal Strips ---")
        num_strips2 = 5
        
        strips2 = cut_image_into_strips(test_image, num_strips2)
        
        print(f"Number of strips: {num_strips2}")
        for i, strip in enumerate(strips2, 1):
            print(f"  Strip {i}: {strip.width}x{strip.height}px")
        
        # Save these strips too
        strip_outputs2 = []
        for i, strip in enumerate(strips2, 1):
            output_path = f"test_strip_{i}_of_{num_strips2}.png"
            strip.save(output_path)
            strip_outputs2.append(output_path)
            print(f"Saved strip {i} to: {output_path}")
        
        # Test 4: Visual indicators for single cut
        print("\n--- Test 4: Visual Cut Indicator (Single) ---")
        
        # Create indicator for middle cut
        indicator_image = add_width_cut_indicator(test_image, image_width // 2)
        indicator_output = "test_cut_indicator.png"
        indicator_image.save(indicator_output)
        print(f"Saved cut indicator to: {indicator_output}")
        
        # Test 5: Visual indicators for strip cuts
        print("\n--- Test 5: Visual Strip Cut Indicators ---")
        
        # Create indicator for 3 strips
        strip_indicator_image = add_strip_cut_indicators(test_image, 3)
        strip_indicator_output = "test_strip_indicator_3.png"
        strip_indicator_image.save(strip_indicator_output)
        print(f"Saved 3-strip indicator to: {strip_indicator_output}")
        
        # Create indicator for 5 strips
        strip_indicator_image2 = add_strip_cut_indicators(test_image, 5)
        strip_indicator_output2 = "test_strip_indicator_5.png"
        strip_indicator_image2.save(strip_indicator_output2)
        print(f"Saved 5-strip indicator to: {strip_indicator_output2}")
        
        # Test 6: Edge cases for single cut
        print("\n--- Test 6: Edge Cases (Single Cut) ---")
        
        # Test cut at 1px (minimum valid)
        try:
            left_min, right_min = cut_image_width(test_image, 1)
            print(f"✓ Cut at 1px: Left={left_min.width}x{left_min.height}, Right={right_min.width}x{right_min.height}")
        except Exception as e:
            print(f"✗ Cut at 1px failed: {e}")
        
        # Test cut at width-1 (maximum valid)
        try:
            left_max, right_max = cut_image_width(test_image, image_width - 1)
            print(f"✓ Cut at {image_width-1}px: Left={left_max.width}x{left_max.height}, Right={right_max.width}x{right_max.height}")
        except Exception as e:
            print(f"✗ Cut at {image_width-1}px failed: {e}")
        
        # Test invalid cuts (should raise ValueError)
        print("\n--- Test 7: Invalid Cut Positions (should fail) ---")
        
        invalid_positions = [0, image_width, image_width + 10, -5]
        for pos in invalid_positions:
            try:
                left, right = cut_image_width(test_image, pos)
                print(f"✗ Cut at {pos}px should have failed but didn't!")
            except ValueError as e:
                print(f"✓ Cut at {pos}px correctly failed: {str(e)[:50]}...")
            except Exception as e:
                print(f"✓ Cut at {pos}px failed with unexpected error: {type(e).__name__}")
        
        # Test 8: Edge cases for strip cutting
        print("\n--- Test 8: Edge Cases (Strip Cutting) ---")
        
        # Test 1 strip (should return original image)
        try:
            one_strip = cut_image_into_strips(test_image, 1)
            print(f"✓ 1 strip: Returns list with 1 image of size {one_strip[0].width}x{one_strip[0].height}")
        except Exception as e:
            print(f"✗ 1 strip failed: {e}")
        
        # Test max strips (image width)
        try:
            max_strips = cut_image_into_strips(test_image, image_width)
            print(f"✓ {image_width} strips: Returns {len(max_strips)} strips, each 1px wide")
        except Exception as e:
            print(f"✗ {image_width} strips failed: {e}")
        
        # Test invalid strip counts
        invalid_strip_counts = [0, -1, image_width + 1]
        for count in invalid_strip_counts:
            try:
                strips_invalid = cut_image_into_strips(test_image, count)
                print(f"✗ {count} strips should have failed but didn't!")
            except ValueError as e:
                print(f"✓ {count} strips correctly failed: {str(e)[:50]}...")
            except Exception as e:
                print(f"✓ {count} strips failed with unexpected error: {type(e).__name__}")
        
        print("\n=== Test Summary ===")
        print(f"Original test image: {test_image_path}")
        print("\nSingle cut parts:")
        print(f"1. Middle cut (150px): {left_output}, {right_output}")
        print("\nStrip cuts:")
        print(f"2. 3 equal strips: {', '.join(strip_outputs)}")
        print(f"3. 5 equal strips: {', '.join(strip_outputs2)}")
        print("\nVisual indicators:")
        print(f"4. Single cut indicator: {indicator_output}")
        print(f"5. 3-strip indicator: {strip_indicator_output}")
        print(f"6. 5-strip indicator: {strip_indicator_output2}")
        print("\n✅ All tests completed successfully!")
        print("\nTo view the results, open the PNG files in an image viewer.")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the printit directory and image_utils.py has the width cutting functions.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def quick_test_with_image(image_path, cut_position=None):
    """Quick test with an existing image."""
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return False
    
    try:
        from image_utils import cut_image_width, add_width_cut_indicator
        
        print(f"Processing: {image_path}")
        image = Image.open(image_path).convert("RGB")
        print(f"Image size: {image.width}x{image.height}")
        
        # Determine cut position
        if cut_position is None:
            # Default to middle
            cut_position = image.width // 2
        elif cut_position < 1 or cut_position >= image.width:
            print(f"❌ Invalid cut position: {cut_position}. Must be between 1 and {image.width-1}")
            return False
        
        print(f"Cut position: {cut_position}px")
        
        # Create visual indicator first
        indicator_image = add_width_cut_indicator(image, cut_position)
        
        # Then cut the image
        left_image, right_image = cut_image_width(image, cut_position)
        
        # Save results with appropriate names
        base, ext = os.path.splitext(image_path)
        
        indicator_output = f"{base}_cut_indicator_{cut_position}px{ext}"
        left_output = f"{base}_left_{cut_position}px{ext}"
        right_output = f"{base}_right_{cut_position}px{ext}"
        
        indicator_image.save(indicator_output)
        left_image.save(left_output)
        right_image.save(right_output)
        
        print(f"\n✅ Results saved:")
        print(f"   Cut indicator: {indicator_output}")
        print(f"   Left part: {left_output} ({left_image.width}x{left_image.height})")
        print(f"   Right part: {right_output} ({right_image.width}x{right_image.height})")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        # First argument is image path
        image_path = sys.argv[1]
        
        # Second optional argument is cut position
        cut_position = None
        if len(sys.argv) > 2:
            try:
                cut_position = int(sys.argv[2])
            except ValueError:
                print(f"❌ Invalid cut position: {sys.argv[2]}. Must be an integer.")
                sys.exit(1)
        
        quick_test_with_image(image_path, cut_position)
    else:
        # Run the full test with sample image
        test_width_cutting_functions()