# Isometric 3D Sticker Half Cube Feature

## Concept
Create stickers that appear as 3D half-cubes when assembled, with isometric projection. Users can print multiple faces that assemble into a 3D cube structure.

## Implementation Approach

### Core Functionality
```python
# tabs/isometric_cube.py
import math
from PIL import Image, ImageDraw
import streamlit as st

def create_isometric_cube_faces(label_width, cube_size_mm, shading_intensity=0.3):
    """
    Generate 3 faces of a half-cube in isometric projection.
    
    Args:
        label_width: Printer label width in pixels
        cube_size_mm: Desired cube size in millimeters
        shading_intensity: 0.0 to 1.0 for 3D shading effect
    
    Returns:
        List of PIL Images: [front_face, top_face, side_face]
    """
    # Convert mm to pixels (assuming 300 DPI)
    cube_size_px = int((cube_size_mm / 25.4) * 300)
    
    # Isometric projection angles (30 degrees)
    angle_rad = math.radians(30)
    cos_angle = math.cos(angle_rad)
    sin_angle = math.sin(angle_rad)
    
    # Calculate face dimensions
    face_width = cube_size_px
    face_height = cube_size_px
    
    faces = []
    face_names = ["front", "top", "side"]
    
    for i, face_name in enumerate(face_names):
        # Create blank face
        face = Image.new("L", (face_width, face_height), 255)
        draw = ImageDraw.Draw(face)
        
        # Apply isometric transformation
        if face_name == "front":
            # Front face - no transformation
            points = [(0, 0), (face_width, 0), (face_width, face_height), (0, face_height)]
        elif face_name == "top":
            # Top face - sheared horizontally
            points = [
                (0, 0),
                (int(face_width * cos_angle), int(-face_height * sin_angle)),
                (int(face_width * cos_angle), int(face_height - face_height * sin_angle)),
                (0, face_height)
            ]
        else:  # side
            # Side face - sheared vertically
            points = [
                (0, 0),
                (face_width, 0),
                (int(face_width + face_width * sin_angle), int(face_height * cos_angle)),
                (int(face_width * sin_angle), int(face_height * cos_angle))
            ]
        
        # Draw face with shading
        shade_value = int(255 * (1 - shading_intensity * i/2))
        draw.polygon(points, fill=shade_value, outline=0)
        
        # Add alignment marks
        draw.rectangle([5, 5, 10, 10], fill=0)  # Top-left corner
        draw.rectangle([face_width-10, 5, face_width-5, 10], fill=0)  # Top-right
        
        faces.append(face)
    
    return faces

def render(printer_info, preper_image, print_image):
    """Render the Isometric Cube tab."""
    st.subheader(":triangular_ruler: Isometric 3D Cube")
    st.write("Create 3D cube faces with isometric projection")
    
    # Cube size selection
    col1, col2 = st.columns(2)
    with col1:
        cube_size = st.slider("Cube Size (mm)", 20, 100, 50, 
                             help="Size of each cube face in millimeters")
    with col2:
        shading = st.slider("Shading Intensity", 0.0, 1.0, 0.3, 0.1,
                           help="3D shading effect intensity")
    
    # Generate preview
    if st.button("Generate Cube Faces", key="generate_cube"):
        with st.spinner("Creating isometric cube faces..."):
            faces = create_isometric_cube_faces(
                label_width=printer_info['label_width'],
                cube_size_mm=cube_size,
                shading_intensity=shading
            )
            
            # Store in session state
            st.session_state.cube_faces = faces
            
            # Display preview
            st.success(f"Generated {len(faces)} cube faces!")
            
            # Show assembly instructions
            with st.expander("Assembly Instructions"):
                st.markdown("""
                1. Print all three faces
                2. Cut along the edges
                3. Fold along the dashed lines (if added)
                4. Assemble into a half-cube shape
                5. Use glue or tape to secure
                """)
    
    # Print controls
    if 'cube_faces' in st.session_state:
        faces = st.session_state.cube_faces
        face_names = ["Front Face", "Top Face", "Side Face"]
        
        st.subheader("Print Controls")
        
        # Individual face printing
        for i, (face, name) in enumerate(zip(faces, face_names)):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.image(face, caption=name, width=200)
            with col2:
                if st.button(f"Print {name}", key=f"print_face_{i}"):
                    print_image(face, printer_info=printer_info)
                    st.success(f"{name} sent to printer!")
        
        # Batch printing option
        if st.button("Print All Faces", key="print_all_faces"):
            for i, face in enumerate(faces):
                print_image(face, printer_info=printer_info)
            st.success("All cube faces sent to printer queue!")
```

## Required Changes

### 1. New Tab Module
Create `tabs/isometric_cube.py` with the above implementation.

### 2. Configuration Update
Add to `config.toml`:
```toml
[tabs]
enabled = [
    "Label",
    "Sticker", 
    "Sticker Pro",
    "Text2image",
    "Webcam",
    "Dog",
    "Cat",
    "History",
    "FAQ",
    "Isometric Cube",  # Add this line
]
```

### 3. Utility Functions
Extend `image_utils.py` with isometric helper functions:
```python
def apply_isometric_transform(image, angle_degrees=30, axis='x'):
    """Apply isometric transformation to an image."""
    from PIL import Image
    import math
    
    angle_rad = math.radians(angle_degrees)
    
    if axis == 'x':
        # Shear horizontally
        shear_factor = math.tan(angle_rad)
        return image.transform(
            image.size,
            Image.AFFINE,
            (1, shear_factor, 0, 0, 1, 0),
            Image.BICUBIC
        )
    else:  # 'y'
        # Shear vertically
        shear_factor = math.tan(angle_rad)
        return image.transform(
            image.size,
            Image.AFFINE,
            (1, 0, 0, shear_factor, 1, 0),
            Image.BICUBIC
        )
```

## Integration Points

### Uses Existing Functions
- `preper_image()`: For dithering cube faces before printing
- `print_image()`: To queue print jobs
- Printer info from `printer_info` parameter

### Session State
- Stores generated cube faces in `st.session_state.cube_faces`
- Maintains user settings between interactions

### UI Consistency
- Follows same layout patterns as other tabs
- Uses Streamlit components consistently
- Provides clear feedback and instructions

## Creative Applications

### 1. Architectural Models
- Create miniature building blocks
- Design geometric sculptures
- Educational geometry tools

### 2. Package Design
- Prototype 3D packaging
- Create gift box templates
- Product mockups

### 3. Educational Tools
- Geometry teaching aids
- Spatial reasoning exercises
- 3D puzzle components

### 4. Art Projects
- Abstract 3D compositions
- Modular sculpture elements
- Optical illusion art

## Technical Considerations

### Printer Limitations
- Label width limits maximum cube size
- Dithering affects shading quality
- Alignment marks help with assembly

### Image Processing
- Isometric projection requires coordinate math
- Shading enhances 3D perception
- Anti-aliasing improves edge quality

### User Experience
- Real-time preview of cube faces
- Clear assembly instructions
- Batch printing option for convenience

## Testing Strategy

### Unit Tests
- Test isometric projection calculations
- Verify face dimensions are correct
- Check shading values are within range

### Integration Tests
- Test tab renders without errors
- Verify print functionality works
- Check session state management

### User Testing
- Assembly instructions clarity
- Print quality of alignment marks
- Ease of cube assembly

## Dependencies
- **Phase 3 Implementation** (Most complex)
- Requires 3D projection mathematics
- Needs careful alignment mark design
- Benefits from advanced shading options

## Next Steps
1. Implement basic isometric projection
2. Add shading options for 3D effect
3. Include fold lines for assembly
4. Add texture mapping for realistic faces
5. Support for different cube types (not just half-cube)