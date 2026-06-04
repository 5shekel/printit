# Multi-layer Stickers Feature

## Concept
Create layered stickers with registration marks for precise alignment, potentially with transparent layers. Users can build complex 3D compositions, color separations, interactive flip books, and educational models using multiple printed layers.

## Implementation Approach

### Core Functionality
The multilayer feature requires a project management system with:
1. Layer management (add, remove, reorder, adjust properties)
2. Registration marks for alignment
3. Preview of assembled composition
4. Individual print sheets generation
5. Project saving/loading

### Key Components

**MultiLayerProject Class** (in `tabs/multilayer.py`):
- Manages layers with properties (image, name, offset, opacity)
- Generates print sheets with registration marks
- Creates assembled previews
- Handles project serialization

**Streamlit UI**:
- Layer management interface
- Real-time preview
- Print controls
- Project save/load functionality

## Required Changes

### 1. New Tab Module
Create `tabs/multilayer.py` with comprehensive layer management.

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
    "Isometric Cube",
    "Mosaic",
    "Continuous Strip",
    "Cutting Guides",
    "Creative Text",
    "Negative Space",
    "Multi-layer",  # Add this line
]
```

### 3. Utility Functions
Extend `image_utils.py` with multilayer utilities:
```python
def composite_layers(layers, background_color=(255, 255, 255)):
    """Composite multiple layers into single image."""
    from PIL import Image
    
    if not layers:
        return None
    
    # Calculate maximum dimensions
    max_width = 0
    max_height = 0
    for layer in layers:
        img = layer["image"]
        width = img.width + layer.get("offset_x", 0)
        height = img.height + layer.get("offset_y", 0)
        max_width = max(max_width, width)
        max_height = max(max_height, height)
    
    # Create composite
    composite = Image.new("RGBA", (max_width, max_height), (*background_color, 255))
    
    for layer in layers:
        layer_img = layer["image"]
        offset_x = layer.get("offset_x", 0)
        offset_y = layer.get("offset_y", 0)
        opacity = layer.get("opacity", 1.0)
        
        # Apply opacity if needed
        if opacity < 1.0 and layer_img.mode == 'RGBA':
            # Adjust alpha channel
            alpha_layer = layer_img.copy()
            alpha_data = alpha_layer.getdata()
            new_data = []
            for item in alpha_data:
                if len(item) == 4:
                    r, g, b, a = item
                    new_a = int(a * opacity)
                    new_data.append((r, g, b, new_a))
                else:
                    new_data.append(item)
            alpha_layer.putdata(new_data)
            layer_img = alpha_layer
        
        # Composite layer
        composite.alpha_composite(
            layer_img.convert("RGBA") if layer_img.mode != 'RGBA' else layer_img,
            dest=(offset_x, offset_y)
        )
    
    return composite

def add_registration_marks(image, mark_type="crosshair", margin=30):
    """Add registration marks to image."""
    from PIL import ImageDraw
    
    draw = ImageDraw.Draw(image)
    width, height = image.size
    
    if mark_type == "crosshair":
        mark_size = 10
        # Top-left
        draw.line([(margin, margin - mark_size), (margin, margin + mark_size)], fill=0)
        draw.line([(margin - mark_size, margin), (margin + mark_size, margin)], fill=0)
        # Top-right
        draw.line([(width - margin, margin - mark_size), (width - margin, margin + mark_size)], fill=0)
        draw.line([(width - margin - mark_size, margin), (width - margin + mark_size, margin)], fill=0)
        # Bottom-left
        draw.line([(margin, height - margin - mark_size), (margin, height - margin + mark_size)], fill=0)
        draw.line([(margin - mark_size, height - margin), (margin + mark_size, height - margin)], fill=0)
        # Bottom-right
        draw.line([(width - margin, height - margin - mark_size), (width - margin, height - margin + mark_size)], fill=0)
        draw.line([(width - margin - mark_size, height - margin), (width - margin + mark_size, height - margin)], fill=0)
    
    return image
```

## Integration Points

### Uses Existing Functions
- `preper_image()`: For preparing individual layers
- `print_image()`: For printing individual sheets
- Image loading from uploaded files
- Font system for text layers

### Project Management
- Session state for project persistence
- JSON serialization for saving/loading
- Layer reordering and property adjustment

### Registration System
- Consistent marks across all layers
- Alignment guides for assembly
- Layer identification labels

## Creative Applications

### 1. 3D Compositions
- Layered shadow boxes
- Depth effects with spacing
- Pop-up card elements
- Diorama components

### 2. Color Separation
- Screen printing color layers
- CMYK color separation
- Spot color applications
- Metallic/foil layer preparation

### 3. Interactive Elements
- Flip books and animations
- Reveal layers (lift flaps)
- Moving parts with pivots
- Educational models with layers

### 4. Mixed Media Art
- Paper and transparency combinations
- Textured layer additions
- Found object integration
- Collage element organization

### 5. Educational Tools
- Anatomy layer models
- Geological cross-sections
- Historical timeline layers
- Scientific process diagrams

## Technical Considerations

### Registration Precision
- Consistent mark placement across layers
- Printer alignment considerations
- Material thickness compensation
- Assembly guidance system

### Layer Management
- Memory usage with many layers
- Real-time preview performance
- Undo/redo functionality
- Layer grouping and organization

### Printing Workflow
- Batch printing of all layers
- Individual layer reprinting
- Print order optimization
- Material type variations

## Testing Strategy

### Unit Tests
- Test layer compositing algorithms
- Verify registration mark placement
- Check project serialization/deserialization

### Integration Tests
- Test with various layer combinations
- Verify printing functionality
- Check session state persistence

### User Testing
- Assembly instruction clarity
- Registration mark effectiveness
- Layer management usability

## Dependencies
- **Phase 3 Implementation** (Most complex)
- Requires project management system
- Needs registration mark system
- Benefits from advanced UI components

## Next Steps
1. Implement basic layer management
2. Add registration mark system
3. Create project save/load functionality
4. Integrate with other tabs for layer sources
5. Add advanced features like layer groups and effects

## Example Workflow
1. User creates new multilayer project
2. Adds layers from various sources (upload, text, other tabs)
3. Adjusts layer positions and properties
4. Previews assembled composition
5. Generates print sheets with registration marks
6. Prints all layers
7. Assembles using registration marks for alignment
8. Saves project for future modifications

This feature enables complex sticker projects that go beyond single-layer printing, opening up possibilities for advanced papercraft, educational models, and artistic compositions.