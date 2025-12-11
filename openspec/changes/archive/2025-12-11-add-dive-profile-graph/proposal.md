# Proposal: Add Dive Profile Graph Overlay

## Problem

ScubaOverlay currently displays dive computer data as discrete numeric values (depth, time, tank pressure, etc.) on the overlay. While this provides precise real-time information, it lacks visual context about the overall dive progression, depth trends, and dive profile shape.

Divers and video viewers cannot see:
- Where in the dive the current moment is positioned
- Whether the diver is ascending, descending, or at depth
- The overall shape and depth profile of the dive
- How much of the dive has been completed

This limits the educational and entertainment value of dive videos, as viewers must mentally construct the dive profile from changing numbers.

## User Value

This feature enables divers to:

1. **Visualize dive progression** - See a graphical representation of depth over time throughout the dive
2. **Provide spatial context** - Show current position in the dive with a moving indicator dot
3. **Enhance video storytelling** - Viewers can understand dive structure (descents, bottom time, ascents, safety stops)
4. **Create professional presentations** - Add polished graphical overlays for dive training, trip reports, and social media
5. **Customize appearance** - Control graph colors, line thickness, and styling to match branding or visibility needs

### Example Use Case

A dive instructor creating training videos wants to show students:

- The dive profile with depth on Y-axis and time on X-axis
- Current position highlighted with a moving dot
- Custom colors matching their dive school branding
- Graph overlaid alongside (or instead of) numeric dive computer data

**Workflow**:

```bash
# Generate profile graph overlay
scuba-overlay --log dive.ssrf --profile-template profile.yaml --output profile_overlay.mp4

# Generate dive computer overlay (existing functionality)
scuba-overlay --log dive.ssrf --template computer.yaml --output computer_overlay.mp4
```

The instructor then imports both independent overlay videos into their video editing software, positioning and layering them as desired over the dive footage.

## Scope

### In Scope

1. **Profile graph rendering**
   - X-axis: Time (seconds or minutes from dive start)
   - Y-axis: Depth (meters or feet, auto-scaled to dive max depth)
   - Line graph plotting depth samples over time
   - Current position indicator (moving dot on the graph line)
   - Grid lines and axis labels (optional, template-controlled)

2. **Template-based styling**
   - YAML template format similar to existing computer overlay templates
   - Background color (use chroma key color like #00FF00 for transparency)
   - Graph line color, thickness, and style
   - Position indicator (dot) color, size, and shape
   - Axis label fonts, colors, and positioning
   - Grid line color, thickness, and visibility
   - Graph dimensions and positioning within frame

3. **Command-line interface**
   - `--profile-template <path>` - Profile graph template YAML file
   - `--template <path>` - Existing computer overlay template
   - Both flags are mutually exclusive (generate one overlay type per run)
   - Users run the tool twice to generate both overlays separately
   - Users composite overlays in their video editing software

4. **Unit system support**
   - Depth axis respects `--units` flag (metric: meters, imperial: feet)
   - Time axis displays in minutes:seconds format
   - Auto-scaling to fit dive depth range with padding

5. **Segment matching compatibility**
   - Works with `--match-video` for automatic segment extraction
   - Works with `--start` and `--duration` for manual segments
   - Profile graph shows only the segment timeline (not full dive)
   - Position indicator moves relative to segment duration

6. **Documentation**
   - Profile template guide in `docs/profile-template-guide.md`
   - Example profile templates in `templates/` directory
   - README section explaining profile overlay feature
   - Example commands and use cases

### Out of Scope

- **Combined overlay rendering** - Profile and computer overlays are separate videos (users composite in video editor)
- **Multiple data series** - Only depth profile (no temperature, pressure, or NDL graphs)
- **Interactive controls** - Static video overlay only (no clickable timeline)
- **Animated transitions** - No zoom, pan, or fade effects on the graph
- **Advanced graph types** - No bar charts, scatter plots, or 3D visualizations
- **Custom time axis scaling** - Fixed linear time scale (no logarithmic or custom scaling)
- **Multiple profile graphs** - One graph per output video (users run command multiple times for multiple graphs)
- **Real-time rendering** - Pre-rendered video overlay only (no live streaming)
- **Dive statistics overlays** - No max depth, average depth, or dive time annotations beyond graph axes

## Dependencies

### System Dependencies

- None (uses existing OpenCV and Pillow libraries)

### Python Dependencies

- No new external dependencies
- Uses existing libraries:
  - `opencv-python` (cv2) - video frame generation
  - `Pillow` (PIL) - graph rendering, line drawing
  - `numpy` - frame buffer manipulation

### Code Changes

**New files**:

- `src/profile_graph.py` - Profile graph rendering logic
- `docs/profile-template-guide.md` - Profile template documentation
- `templates/profile-simple.yaml` - Simple profile template example
- `templates/profile-technical.yaml` - Technical dive profile template example

**Modified files**:

- `src/main.py` - Add `--profile-template` argument, add mutual exclusion with `--template`
- `README.md` - Add profile overlay feature section and examples

**New template fields**:

Profile template YAML structure (new schema):

```yaml
profile_name: "simple-profile"
width: 800
height: 300
background_color: "#00FF00"  # Use chroma green for transparency, or solid color

graph:
  position: { x: 25, y: 25 }    # Top-left corner of graph area
  width: 750
  height: 250
  
  line:
    color: "#00AAFF"
    thickness: 3
    
  indicator:
    color: "#FF0000"
    size: 12                     # Radius in pixels
    
  axes:
    show_grid: true
    grid_color: "#444444"
    grid_thickness: 1
    
    depth_axis:
      label: "Depth"
      label_font: { name: "Arial", size: 18, color: "#FFFFFF" }
      tick_color: "#FFFFFF"
      
    time_axis:
      label: "Time"
      label_font: { name: "Arial", size: 18, color: "#FFFFFF" }
      tick_color: "#FFFFFF"
```

## Risks and Mitigations

### Risk: Performance degradation with graph rendering

**Mitigation**:

- Pre-render static graph background once during compilation
- Only redraw moving indicator dot per frame
- Reuse existing frame duplication strategy (render once per second, duplicate frames)

### Risk: Graph complexity increases template learning curve

**Mitigation**:

- Provide well-documented example templates
- Keep profile templates separate from computer overlay templates
- Include validation with `--test-template` flag for profile templates
- Clear error messages for invalid template configurations

### Risk: Users expect automatic combined rendering

**Mitigation**:

- Clear documentation that overlays are independent videos
- Example workflows showing video editor compositing
- Explain benefits: more flexibility, simpler implementation, standard video editing workflow

## Success Criteria

1. Users can generate depth profile graph overlays from dive logs
2. Graph displays depth over time with current position indicator
3. Profile templates support customization of colors, sizes, and positioning
4. Profile overlays can be generated standalone or combined with computer overlays
5. Feature works with video segment matching (`--match-video`, `--start`)
6. Documentation includes examples and template guide
7. Performance is comparable to existing overlay generation (no significant slowdown)

## Timeline Estimate

- **Phase 1**: Profile graph rendering core (2-3 days)
- **Phase 2**: Template system integration (1-2 days)
- **Phase 3**: Command-line interface and combined rendering (1 day)
- **Phase 4**: Documentation and examples (1 day)

**Total**: ~5-7 days of development

## Future Enhancements (Not in Scope)

- Multiple data series (temperature, NDL, pressure graphs)
- Animated graph reveal (draw graph progressively as dive progresses)
- Custom axis scaling and zoom levels
- Profile comparison overlays (planned dive vs. actual dive)
- 3D depth profile visualization
- Interactive graph controls (scrubbing, pause markers)
