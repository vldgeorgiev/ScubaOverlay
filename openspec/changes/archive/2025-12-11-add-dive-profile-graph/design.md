# Design: Dive Profile Graph Overlay

## Problem Statement

ScubaOverlay currently displays dive computer data as discrete numeric values. Users cannot see the overall dive profile shape, current position in the dive, or depth trends over time. Adding a graphical depth profile with a moving position indicator provides visual context that enhances video storytelling and educational value.

## Requirements

1. **Graph rendering**: Plot depth (Y-axis) over time (X-axis) as a line graph
2. **Position indicator**: Moving dot on the graph line showing current dive moment
3. **Template-based styling**: YAML template control over colors, line thickness, dot size, positioning
4. **Independent rendering**: Generate profile overlay as separate video from computer overlay
5. **Segment compatibility**: Work with video segment matching (`--match-video`, `--start`)
6. **Unit system support**: Respect `--units` flag for depth axis (meters vs. feet)

## Architecture

### Graph Rendering Strategy

**Approach**: Pre-render static graph elements, update only position indicator per frame

**Components**:

1. **Static background layer**:
   - Grid lines (optional)
   - Axis labels and ticks
   - Complete depth profile line (entire dive or segment)
   - Rendered once during template compilation

2. **Dynamic foreground layer**:
   - Position indicator dot
   - Redrawn each frame based on current dive time
   - Composite onto static background

**Performance optimization**:
- Static graph line drawn once using `ImageDraw.line()` with depth sample coordinates
- Position indicator is small circle overlay (fast to render)
- Leverage existing frame duplication (render once per second, duplicate for FPS)

### Data Processing

**Coordinate transformation**:

1. **Time to X-axis**: Linear mapping from dive seconds to pixel X-coordinate
   - `x = graph_x_offset + (sample.time / total_duration) * graph_width`
   - For segments: use segment duration, not full dive duration

2. **Depth to Y-axis**: Inverted linear mapping (depth increases downward)
   - Find max depth in samples: `max_depth = max(sample.depth for sample in samples)`
   - Add padding: `y_scale = graph_height / (max_depth * 1.1)`  # 10% padding
   - `y = graph_y_offset + (sample.depth * y_scale)`

3. **Unit conversion**: Apply depth unit conversion before Y-axis mapping
   - Metric: depth in meters (no conversion)
   - Imperial: depth in feet (multiply by 3.28084)

**Sample interpolation**:
- Connect dive samples with straight line segments
- No curve smoothing (keeps profile accurate to dive computer data)
- Position indicator snaps to nearest sample (no interpolation between samples)

### Template System Extension

**New template type**: Profile template (separate from computer overlay template)

**Profile template schema**:

```yaml
profile_name: "simple-profile"
width: 800                     # Frame dimensions
height: 300
background_color: "#00FF00"    # Use chroma green for transparency, or any solid color

graph:
  position: { x: 25, y: 25 }   # Graph area position in frame
  width: 750                    # Graph area dimensions
  height: 250
  
  line:
    color: "#00AAFF"            # Depth profile line color
    thickness: 3                # Line thickness in pixels
    
  indicator:
    color: "#FF0000"            # Position dot color
    size: 12                    # Dot radius in pixels
    shape: "circle"             # Future: "circle", "square", "diamond"
    
  axes:
    show_grid: true             # Optional grid lines
    grid_color: "#444444"
    grid_thickness: 1
    grid_interval: { time: 60, depth: 10 }  # Grid every 60s, 10m
    
    depth_axis:
      label: "Depth (m)"
      label_font: { name: "Arial", size: 18, color: "#FFFFFF" }
      label_position: "left"    # "left" or "right"
      show_ticks: true
      tick_interval: 10         # Tick every 10m (or ft if imperial)
      tick_color: "#FFFFFF"
      
    time_axis:
      label: "Time"
      label_font: { name: "Arial", size: 18, color: "#FFFFFF" }
      label_position: "bottom"  # "top" or "bottom"
      show_ticks: true
      tick_interval: 60         # Tick every 60 seconds
      tick_format: "mm:ss"      # "mm:ss" or "seconds"
      tick_color: "#FFFFFF"
```

**Minimal template example**:

```yaml
profile_name: "minimal"
width: 800
height: 300
background_color: "#00FF00"  # Chroma green for transparency

graph:
  position: { x: 50, y: 50 }
  width: 700
  height: 200
  line: { color: "#00AAFF", thickness: 3 }
  indicator: { color: "#FF0000", size: 10 }
```

All other fields use defaults.

### Command-Line Interface

**New argument**:
- `--profile-template <path>` - YAML file for profile graph template

**Usage modes**:

1. **Profile overlay only**:
   ```bash
   scuba-overlay --log dive.ssrf --profile-template profile.yaml --output profile.mp4
   ```
   Generates profile graph overlay (no computer data overlay).

2. **Computer overlay only** (existing behavior):
   ```bash
   scuba-overlay --log dive.ssrf --template computer.yaml --output computer.mp4
   ```
   Generates computer data overlay (no profile graph).

**Error conditions**:

- `--profile-template` provided without `--log`: Error (need dive data)
- Both `--template` and `--profile-template` provided: Error (mutually exclusive)
- Neither `--template` nor `--profile-template` provided: Error (need at least one template)

### Module Structure

**Approach**: Composite both overlays into single frame

**Options**:

1. **Option A: Independent overlays** (Recommended)
   - Each template defines its own frame size and positioning
   - Profile template creates profile overlay in its own coordinate space
   - Computer template creates computer overlay in its own coordinate space
   - User manually ensures templates don't overlap (responsibility of template designer)
   - Simpler implementation, more flexible

2. **Option B: Nested composition**
   - Profile graph as template item type in computer overlay template
   - Add `type: profile_graph` item to existing template schema
   - More complex, less flexible

**Selected approach**: **Option A** (Independent overlays)

**Implementation**:
- If only `--template`: render computer overlay (existing logic)
- If only `--profile-template`: render profile overlay (new logic)
- If both: 
  - Determine combined frame size: `max(computer.width, profile.width)` x `max(computer.height, profile.height)`
  - Render computer overlay at position (0, 0)
  - Render profile overlay at position (0, 0)
  - Composite using alpha blending
  - Write combined frame to video

### Module Structure

**New module**: `src/profile_graph.py`

**Functions**:

```python
def compile_profile_template(
    template: Dict[str, Any],
    frame_size: Tuple[int, int],
    units_override: Optional[Dict[str, str]] = None
) -> _CompiledProfileTemplate:
    """Pre-compile profile template for fast rendering."""
    pass

def render_profile_graph(
    samples: List[DiveSample],
    compiled: _CompiledProfileTemplate,
    current_time: int
) -> np.ndarray:
    """Render profile graph with position indicator at current_time."""
    pass

def generate_profile_overlay_video(
    dive_samples: List[DiveSample],
    template: Dict[str, Any],
    output_path: str,
    resolution: Tuple[int, int],
    duration: int,
    fps: int,
    units_override: Optional[Dict[str, str]] = None,
    time_offset: int = 0
) -> None:
    """Generate standalone profile overlay video."""
    pass
```

**Modified files**:

- `src/main.py`:
  - Add `--profile-template` argument
  - Make `--template` and `--profile-template` mutually exclusive
  - Route to profile rendering when `--profile-template` is used
  - Validate template compatibility

- `src/template.py`:
  - Add `load_profile_template()` function (or reuse `load_template()`)
  - Validate profile template schema

### Data Flow

**Profile overlay**:

```
1. Parse dive log → DiveSample[]
2. Load profile template → Dict
3. Compile profile template → _CompiledProfileTemplate
4. For each second in duration:
   a. Find current sample
   b. Render profile graph with indicator at current time
   c. Write frame to video (duplicate for FPS)
```

**Computer overlay** (existing):

```
1. Parse dive log → DiveSample[]
2. Load computer template → Dict
3. Compile computer template → _CompiledTemplate
4. For each second in duration:
   a. Find current sample
   b. Render computer overlay
   c. Write frame to video (duplicate for FPS)
```

## Technical Decisions

### Decision 1: Pre-render vs. Render-per-frame

**Options**:
- A) Render entire graph line every frame
- B) Pre-render static graph, update only position indicator per frame

**Choice**: **B** (Pre-render static graph)

**Rationale**:
- Massive performance gain (render graph once vs. thousands of times)
- Graph line doesn't change during dive (static)
- Position indicator is fast to render (small circle)
- Matches existing optimization strategy (compile templates once)

### Decision 2: Separate vs. Combined Templates

**Options**:
- A) Profile graph as item in computer overlay template
- B) Separate profile template, composited with computer template

**Choice**: **B** (Separate templates)

**Rationale**:
- Simpler implementation (reuse existing template compilation logic)
- More flexible (can use profile alone or combined)
- Easier to maintain (separation of concerns)
- Users can mix and match templates

### Decision 3: Grid Lines and Axes

**Options**:
- A) Always render grid and axes
- B) Template-controlled (optional)
- C) Never render (minimal graph only)

**Choice**: **B** (Template-controlled)

**Rationale**:
- Maximum flexibility for users
- Some users want minimal clean graph
- Others want detailed technical graph with grid
- Default templates can demonstrate both approaches

### Decision 4: Coordinate Scaling

**Options**:
- A) Fixed depth scale (0-40m always)
- B) Auto-scale to max depth + padding
- C) Template-specified scale range

**Choice**: **B** (Auto-scale to max depth)

**Rationale**:
- Adapts to any dive depth (shallow or deep)
- Maximizes use of vertical space
- No template tuning needed per dive
- 10% padding prevents indicator from touching top edge

## Edge Cases

### Shallow Dives
- Max depth < 5m: Still render with 10% padding (scale to ~5.5m)
- Avoid division by zero: Always ensure `max_depth > 0`

### Deep Dives
- Max depth > 100m: Auto-scale works (e.g., scale to 110m)
- Consider larger grid intervals for readability

### Short Segments
- Duration < 60s: Time axis ticks may overlap (template designer responsibility)
- Suggest tick interval adjustment in documentation

### Missing Data
- No samples: Skip profile rendering, show error
- Single sample: Render as single point (no line)

### Unit Conversion
- Always convert depth before coordinate mapping
- Grid intervals in template are in display units (m or ft after conversion)

## Performance Considerations

- **Graph line complexity**: O(n) where n = number of samples (~3000 for 50-minute dive)
- **Position indicator**: O(1) per frame (simple circle draw)
- **Frame duplication**: Leverage existing 1 render/second strategy
- **Memory**: Static graph cached in compiled template (~2-8 MB for 1920x1080 RGBA)

**Expected performance**: Comparable to existing overlay generation (~10-20 seconds for 30-minute dive at 30 FPS)

## Testing Strategy

1. **Template validation**: Add `--test-template` support for profile templates
2. **Sample dives**: Test with shallow (5m), medium (30m), and deep (60m) dives
3. **Segment matching**: Verify position indicator moves correctly in segmented overlays
4. **Unit conversion**: Test metric and imperial unit display
5. **Combined rendering**: Verify computer + profile compositing works correctly

## Future Enhancements (Not in Scope)

- Multiple data series (temperature, NDL, pressure on same graph)
- Animated graph reveal (draw line progressively)
- Custom axis scaling (manual min/max depth range)
- Curve smoothing (spline interpolation between samples)
- 3D depth profile visualization
- Multiple profile graphs in single overlay (multi-panel layout)
