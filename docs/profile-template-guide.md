# Profile Template Guide

## Overview

Profile templates control the appearance and layout of dive profile graph overlays. A profile graph shows depth over time with a moving position indicator, providing visual context for dive progression.

## Template Structure

### Basic Properties

```yaml
profile_name: "my-profile"     # Template identifier
width: 800                     # Frame width in pixels
height: 300                    # Frame height in pixels
background_color: "#00FF00"    # Background color (hex)
```

### Background Options

- **Chroma Key (Transparent)**: Use `background_color: "#00FF00"` (bright green) for compositing in video editing software
- **Solid Color**: Use any hex color for an opaque background (e.g., `"#1a1a1a"` for dark gray)

## Graph Configuration

### Position and Dimensions

```yaml
graph:
  position: { x: 25, y: 25 }   # Top-left corner of graph area
  width: 750                    # Graph area width in pixels
  height: 250                   # Graph area height in pixels
```

The graph area is where the depth profile line and position indicator are rendered. Position it within the frame dimensions defined above.

### Profile Line

```yaml
graph:
  line:
    color: "#00AAFF"           # Line color (hex)
    thickness: 3                # Line thickness in pixels
```

The profile line connects all depth samples from the dive log, showing the dive's depth progression over time.

### Position Indicator

```yaml
graph:
  indicator:
    color: "#FF0000"           # Indicator dot color (hex)
    size: 12                    # Indicator radius in pixels
```

The position indicator is a circular dot that moves along the profile line, showing the current moment in the dive video.

### Grid Lines (Optional)

```yaml
graph:
  axes:
    show_grid: true
    grid_color: "#444444"      # Grid line color (hex)
    grid_thickness: 1           # Grid line thickness in pixels
    grid_interval:
      time: 60                  # Vertical grid every 60 seconds
      depth: 10                 # Horizontal grid every 10m (or ft if imperial)
```

Grid lines help visualize time and depth intervals on the graph. The depth interval automatically converts for imperial units.

### Axis Labels and Ticks (Optional)

```yaml
graph:
  axes:
    depth_axis:
      label: "Depth (m)"
      label_font:
        name: "Arial"
        size: 18
        color: "#FFFFFF"
      label_position: "left"    # "left" or "right"
      show_ticks: true
      tick_interval: 10         # Tick every 10m (or ft if imperial)
      tick_color: "#FFFFFF"
    
    time_axis:
      label: "Time"
      label_font:
        name: "Arial"
        size: 18
        color: "#FFFFFF"
      label_position: "bottom"  # "top" or "bottom"
      show_ticks: true
      tick_interval: 60         # Tick every 60 seconds
      tick_format: "mm:ss"      # "mm:ss" or "seconds"
      tick_color: "#FFFFFF"
```

Axis labels and tick marks provide reference points for reading the graph. Ticks are drawn with numeric labels at regular intervals.

## Complete Template Examples

### Minimal Template (Chroma Key)

```yaml
profile_name: "minimal-chroma"
width: 800
height: 300
background_color: "#00FF00"    # Chroma green

graph:
  position: { x: 25, y: 25 }
  width: 750
  height: 250
  
  line:
    color: "#00AAFF"
    thickness: 3
    
  indicator:
    color: "#FF0000"
    size: 10
```

### Professional Template (Opaque)

```yaml
profile_name: "professional"
width: 800
height: 300
background_color: "#1a1a1a"    # Dark gray

graph:
  position: { x: 50, y: 40 }
  width: 700
  height: 220
  
  line:
    color: "#00D4FF"
    thickness: 4
    
  indicator:
    color: "#FF4500"
    size: 12
```

### Full Featured Template (With Grid and Axes)

```yaml
profile_name: "full-featured"
width: 800
height: 300
background_color: "#1a1a1a"

graph:
  position: { x: 50, y: 40 }
  width: 700
  height: 220
  
  line:
    color: "#00D4FF"
    thickness: 4
    
  indicator:
    color: "#FF4500"
    size: 12
  
  axes:
    show_grid: true
    grid_color: "#444444"
    grid_thickness: 1
    grid_interval: { time: 60, depth: 10 }
    
    depth_axis:
      label: "Depth (m)"
      label_font: { name: "Arial", size: 18, color: "#FFFFFF" }
      label_position: "left"
      show_ticks: true
      tick_interval: 10
      tick_color: "#FFFFFF"
      
    time_axis:
      label: "Time"
      label_font: { name: "Arial", size: 18, color: "#FFFFFF" }
      label_position: "bottom"
      show_ticks: true
      tick_interval: 60
      tick_format: "mm:ss"
      tick_color: "#FFFFFF"
```

## Usage

### Generate Profile Overlay

```bash
scuba-overlay --log dive.ssrf --profile-template profile.yaml --output profile.mp4
```

### Test Template Layout

```bash
scuba-overlay --profile-template profile.yaml --test-template
```

This generates `test_profile_template.png` with dummy dive data to preview the layout.

### Unit System

The profile graph respects the `--units` flag:

```bash
# Metric (meters)
scuba-overlay --log dive.ssrf --profile-template profile.yaml --output profile.mp4

# Imperial (feet)
scuba-overlay --log dive.ssrf --profile-template profile.yaml --output profile.mp4 --units imperial
```

The depth axis automatically converts between meters and feet based on the units setting.

### Video Segments

Profile overlays work with video segment matching:

```bash
# Automatic segment matching
scuba-overlay --log dive.ssrf --profile-template profile.yaml --match-video clip.mp4 --output profile.mp4

# Manual segment
scuba-overlay --log dive.ssrf --profile-template profile.yaml --start 300 --duration 180 --output profile.mp4
```

The profile graph shows only the segment timeline, not the full dive.

## Coordinate System

### X-Axis (Time)
- Left edge: Dive/segment start (0 seconds)
- Right edge: Dive/segment end
- Linear time scale

### Y-Axis (Depth)
- Top edge: Surface (0 depth)
- Bottom edge: Maximum dive depth + 10% padding
- Auto-scales to dive depth range

### Position Indicator
- Snaps to nearest dive sample (no interpolation)
- Moves left-to-right as dive progresses

## Design Tips

### Frame Dimensions
- **800x300**: Good default for horizontal overlay
- **400x600**: Vertical orientation for side placement
- **1920x400**: Full HD width for bottom overlay

### Colors
- **High Contrast**: Use bright colors on dark backgrounds or vice versa
- **Chroma Key**: Bright green (#00FF00) is standard for transparency
- **Safety**: Avoid pure black (#000000) for chroma key (may cause issues)

### Graph Sizing
- Leave 20-50px margins around graph area for clean appearance
- Ensure graph dimensions fit within frame dimensions
- Larger graph area = more readable depth profile

### Line Thickness
- **2-3px**: Minimal, clean look
- **4-5px**: Bold, high visibility
- **6+px**: Very prominent (may look thick on small graphs)

### Indicator Size
- **8-10px**: Subtle indicator
- **12-15px**: Standard visibility
- **16+px**: Large, very visible (may obscure line at close depths)

## Troubleshooting

### Indicator Not Visible
- Check that `indicator.color` contrasts with `line.color`
- Increase `indicator.size` to make it more prominent
- Ensure indicator is drawn on top (it should be by default)

### Graph Looks Squashed
- Increase `graph.height` for more vertical space
- Check that `position.y + height` doesn't exceed frame `height`

### Line Too Thin/Thick
- Adjust `line.thickness` (typical range: 2-5 pixels)
- Test with `--test-template` to preview

### Background Not Transparent in Video Editor
- Verify `background_color` is exactly `"#00FF00"`
- Check video editor chroma key settings (tolerance, spill suppression)
- Some editors prefer #00FF00, others prefer #00B140 (try both)

## Compositing in Video Editors

1. **Generate separate overlays**:
   ```bash
   scuba-overlay --log dive.ssrf --template computer.yaml --output computer.mp4
   scuba-overlay --log dive.ssrf --profile-template profile.yaml --output profile.mp4
   ```

2. **Import into video editor** (DaVinci Resolve, Final Cut Pro, Premiere, etc.)

3. **Layer order** (bottom to top):
   - Dive footage
   - Profile overlay (chroma keyed)
   - Computer overlay (chroma keyed)

4. **Apply chroma key** to overlays using green (#00FF00) as key color

5. **Position and scale** overlays as desired within the frame

This workflow gives you maximum flexibility to adjust positioning, opacity, and blending modes in your editor.
