# Implementation Tasks

## Task Checklist

### Phase 1: Profile Graph Core Rendering

- [x] Create profile_graph.py module
- [x] Implement coordinate transformation functions
- [x] Implement depth profile line rendering
- [x] Implement position indicator rendering
- [x] Add _CompiledProfileTemplate dataclass

### Phase 2: Template System Integration

- [x] Implement profile template loading
- [x] Implement compile_profile_template function
- [x] Implement render_profile_frame function

### Phase 3: Video Generation

- [x] Implement generate_profile_overlay_video function
- [x] Add --profile-template argument to main.py
- [x] Implement profile-only overlay generation in main.py

### Phase 4: Segment Matching Integration

- [x] Support profile overlay with --match-video
- [x] Support profile overlay with --start and --duration

### Phase 5: Testing and Documentation

- [x] Implement --test-template for profile templates
- [x] Create example profile templates
- [x] Write profile template documentation
- [x] Update README with profile overlay feature
- [x] Manual testing with sample dive logs

### Phase 6: Polish and Edge Cases

- [x] Add error handling for invalid profile templates
- [x] Handle edge case: single sample dive
- [x] Handle edge case: very short segments
- [x] Optimize memory usage for large dives

---

## Phase 1: Profile Graph Core Rendering (Foundation)

### Task 1.1: Create profile_graph.py module

**Description**: Create new module with imports and module docstring for profile graph rendering.

**Deliverable**: `src/profile_graph.py` with imports for PIL, numpy, cv2, typing

**Validation**: File exists and imports successfully

**Dependencies**: None

---

### Task 1.2: Implement coordinate transformation functions

**Description**: Write helper functions to map dive time/depth to graph pixel coordinates.

**Deliverable**: Functions in `profile_graph.py`:

- `_time_to_x(time: int, total_duration: int, graph_x: int, graph_width: int) -> int`
- `_depth_to_y(depth: float, max_depth: float, graph_y: int, graph_height: int) -> int`

**Validation**: Unit tests or manual verification with sample values

**Dependencies**: Task 1.1

**Implementation notes**:

- Time to X: Linear mapping `x = graph_x + (time / total_duration) * graph_width`
- Depth to Y: Inverted mapping `y = graph_y + (depth / (max_depth * 1.1)) * graph_height`
- 10% padding on max depth for visual spacing

---

### Task 1.3: Implement depth profile line rendering

**Description**: Draw depth profile line connecting all dive samples.

**Deliverable**: `_render_profile_line()` function using `ImageDraw.line()`

**Validation**: Generates image with visible depth profile line from sample data

**Dependencies**: Task 1.2

**Implementation notes**:

- Convert all samples to (x, y) coordinates using transformation functions
- Use `ImageDraw.line()` with list of coordinates
- Line color and thickness from template
- Straight line segments (no curve smoothing)

---

### Task 1.4: Implement position indicator rendering

**Description**: Draw circular position indicator dot at current dive time.

**Deliverable**: `_render_position_indicator()` function using `ImageDraw.ellipse()`

**Validation**: Generates image with circular dot at correct position on profile line

**Dependencies**: Task 1.2

**Implementation notes**:

- Find current sample: `sample = dive_samples[idx]` where `sample.time <= current_time`
- Convert sample to (x, y) coordinates
- Draw circle: `ImageDraw.ellipse([(x-r, y-r), (x+r, y+r)], fill=color)` where `r = indicator_size`
- Color and size from template

---

### Task 1.5: Add _CompiledProfileTemplate dataclass

**Description**: Create compiled template structure to cache static graph elements.

**Deliverable**: `_CompiledProfileTemplate` dataclass in `profile_graph.py`

**Validation**: Can instantiate and access fields

**Dependencies**: Task 1.1

**Implementation notes**:

```python
@dataclass
class _CompiledProfileTemplate:
    base_img: Image.Image  # Static background with profile line
    graph_config: Dict[str, Any]  # Graph dimensions, colors, etc.
    frame_size: Tuple[int, int]
    units_map: Dict[str, str]
    dive_samples: List[DiveSample]  # Cached for position lookup
    max_depth: float  # Cached for coordinate transformations
```

---

## Phase 2: Template System Integration

### Task 2.1: Implement profile template loading

**Description**: Add function to load and validate profile template YAML.

**Deliverable**: `load_profile_template()` function in `template.py` (or reuse `load_template()`)

**Validation**: Successfully loads valid profile template, raises TemplateError on invalid template

**Dependencies**: None

**Implementation notes**:

- Validate required fields: `width`, `height`, `graph.position`, `graph.width`, `graph.height`, `graph.line`, `graph.indicator`
- Provide defaults for optional fields: `background_color`, `chroma_color`, `axes`, `grid`
- Similar structure to existing `load_template()` function

---

### Task 2.2: Implement compile_profile_template function

**Description**: Pre-compile profile template into _CompiledProfileTemplate with static graph rendered.

**Deliverable**: `compile_profile_template()` function in `profile_graph.py`

**Validation**: Returns _CompiledProfileTemplate with cached background image containing profile line

**Dependencies**: Tasks 1.3, 1.5, 2.1

**Implementation notes**:

- Create base image with background color or chroma color
- Calculate max depth from samples: `max_depth = max(s.depth for s in dive_samples)`
- Apply unit conversion to depth if imperial units requested
- Render complete profile line onto base image
- Cache base image in compiled template
- Store graph configuration for position indicator rendering

---

### Task 2.3: Implement render_profile_frame function

**Description**: Render single profile graph frame with position indicator at current time.

**Deliverable**: `render_profile_frame()` function in `profile_graph.py`

**Validation**: Generates frame with profile line and position indicator at correct location

**Dependencies**: Tasks 1.4, 2.2

**Implementation notes**:

- Copy cached base image from compiled template
- Find current sample by time: advance pointer while `samples[idx+1].time <= current_time`
- Render position indicator at current sample coordinates
- Return numpy array for video frame

---

## Phase 3: Video Generation

### Task 3.1: Implement generate_profile_overlay_video function

**Description**: Generate complete profile overlay video file from dive samples and template.

**Deliverable**: `generate_profile_overlay_video()` function in `profile_graph.py`

**Validation**: Generates playable MP4 video with profile graph and moving position indicator

**Dependencies**: Tasks 2.2, 2.3

**Implementation notes**:

- Similar structure to existing `generate_overlay_video()` in `overlay.py`
- Use cv2.VideoWriter with MP4V codec
- Compile template once at start
- Loop through seconds, render frame, duplicate for FPS
- Progress reporting every 10% of total duration
- Handle time_offset for segment mode

---

### Task 3.2: Add --profile-template argument to main.py

**Description**: Add command-line argument parsing for profile template option with mutual exclusion.

**Deliverable**: Modified `main.py` with `--profile-template` argument

**Validation**: Argument is recognized, mutually exclusive with `--template`, help text is correct

**Dependencies**: None

**Implementation notes**:

- Add `parser.add_argument("--profile-template", help="YAML profile graph template file")`
- Add validation: exactly one of `--template` or `--profile-template` must be provided
- Error if both provided: "Cannot use --template and --profile-template together"
- Error if `--profile-template` provided without `--log` (unless `--test-template`)

---

### Task 3.3: Implement profile-only overlay generation in main.py

**Description**: Orchestrate profile overlay generation when only `--profile-template` provided.

**Deliverable**: Modified `main.py` with profile overlay generation logic

**Validation**: Can generate profile-only overlay video with command:
`scuba-overlay --log dive.ssrf --profile-template profile.yaml --output profile.mp4`

**Dependencies**: Tasks 3.1, 3.2

**Implementation notes**:

- Check if `args.profile_template` and not `args.template`
- Load profile template
- Determine resolution from profile template
- Call `generate_profile_overlay_video()`
- Print success message with output path

---

## Phase 4: Segment Matching Integration

### Task 4.1: Support profile overlay with --match-video

**Description**: Ensure profile overlay works with automatic video segment matching.

**Deliverable**: Profile overlay correctly renders for video segments

**Validation**: Profile graph shows only segment timeline when using `--match-video`

**Dependencies**: Task 3.1

**Implementation notes**:

- Pass segment-filtered `dive_samples` to profile rendering
- Pass `time_offset` to profile rendering for correct time axis
- Graph X-axis spans segment duration (not full dive duration)
- Auto-scale Y-axis to max depth within segment

---

### Task 4.2: Support profile overlay with --start and --duration

**Description**: Ensure profile overlay works with manual segment specification.

**Deliverable**: Profile overlay correctly renders for manual segments

**Validation**: Profile graph shows correct segment with `--start 300 --duration 180`

**Dependencies**: Task 3.1

**Implementation notes**:

- Reuse existing segment extraction logic in `main.py`
- Profile rendering receives segment samples and time offset
- Same behavior as `--match-video` (segment-based timeline)

---

## Phase 5: Testing and Documentation

### Task 5.1: Implement --test-template for profile templates

**Description**: Add support for generating test profile graph image without full dive log.

**Deliverable**: Modified `main.py` to support `--test-template` with `--profile-template`

**Validation**: Command `scuba-overlay --profile-template profile.yaml --test-template` generates test PNG

**Dependencies**: Task 2.3

**Implementation notes**:

- Generate dummy dive samples: simulated descent, bottom time, ascent
- Example: 0m → 30m descent over 3 min → 30m for 20 min → 5m ascent → 5m safety stop → surface
- Render single frame with position indicator at mid-dive
- Save as `test_profile_template.png`

---

### Task 5.2: Create example profile templates

**Description**: Create sample profile templates demonstrating different styles.

**Deliverable**: Template files in `templates/` directory:

- `templates/profile-simple.yaml` - Minimal profile graph (no grid, simple colors)
- `templates/profile-technical.yaml` - Technical profile with grid, axis labels, detailed styling

**Validation**: Both templates load successfully and generate valid overlays

**Dependencies**: Task 2.1

---

### Task 5.3: Write profile template documentation

**Description**: Create comprehensive guide for profile template format and usage.

**Deliverable**: `docs/profile-template-guide.md`

**Validation**: Document includes:

- Template schema explanation
- All template fields with descriptions
- Example templates with annotations
- Coordinate system explanation
- Common customization examples

**Dependencies**: Task 6.2

---

### Task 5.4: Update README with profile overlay feature

**Description**: Add profile overlay section to main README.

**Deliverable**: Modified `README.md` with profile overlay examples and usage

**Validation**: README includes:

- Feature introduction
- Example commands (profile-only, combined)
- Link to profile template guide
- Screenshot or example output

**Dependencies**: Task 6.3

---

### Task 5.5: Manual testing with sample dive logs

**Description**: Test profile overlay generation with various dive profiles.

**Deliverable**: Verified functionality with sample dive logs

**Validation**: Successfully generate profile overlays for:

- Shallow dive (5m max depth)
- Medium recreational dive (30m max depth)
- Deep technical dive (60m+ max depth)
- Short segment (2-minute video clip)

**Dependencies**: Tasks 3.3, 4.1

**Test cases**:

1. Profile overlay: `scuba-overlay --log sample-logs/dive426.ssrf --profile-template templates/profile-simple.yaml --output test_profile.mp4`
2. Computer overlay: `scuba-overlay --log sample-logs/dive426.ssrf --template templates/perdix-ai-cc-tech.yaml --output test_computer.mp4`
3. Segment profile: `scuba-overlay --log sample-logs/match-video.ssrf --match-video sample-video.mp4 --profile-template templates/profile-simple.yaml --output test_segment_profile.mp4`
4. Imperial units: `scuba-overlay --log sample-logs/dive426.ssrf --profile-template templates/profile-simple.yaml --units imperial --output test_imperial.mp4`
5. Test template: `scuba-overlay --profile-template templates/profile-technical.yaml --test-template`

---

## Phase 6: Polish and Edge Cases

### Task 6.1: Add error handling for invalid profile templates

**Description**: Ensure clear error messages for common template mistakes.

**Deliverable**: Comprehensive error handling in template loading and compilation

**Validation**: Clear error messages for:

- Missing required fields
- Invalid color hex codes
- Graph dimensions exceeding frame size
- Negative or zero dimensions

**Dependencies**: Task 2.1

---

### Task 6.2: Handle edge case: single sample dive

**Description**: Ensure profile rendering works with minimal dive data.

**Deliverable**: Profile graph renders single point when only one sample exists

**Validation**: No crash or error when dive has 1-2 samples

**Dependencies**: Task 1.3

**Implementation notes**:

- Single sample: Render as single dot (no line)
- Two samples: Render as single line segment

---

### Task 6.3: Handle edge case: very short segments

**Description**: Ensure profile graph renders correctly for sub-minute segments.

**Deliverable**: Profile graph works with segments < 60 seconds

**Validation**: Generate profile overlay for 10-second segment without layout issues

**Dependencies**: Task 5.1

**Implementation notes**:

- Time axis may be compressed but still functional
- Grid intervals may need adjustment (document in template guide)

---

### Task 6.4: Optimize memory usage for large dives

**Description**: Ensure profile rendering doesn't consume excessive memory for long dives.

**Deliverable**: Efficient memory usage for dives with 10,000+ samples

**Validation**: Profile overlay generation completes without memory errors for 3-hour dive

**Dependencies**: Task 3.1

**Implementation notes**:

- Profile line rendering is O(n) but single-pass
- Static background cached once (RGBA image)
- Monitor memory usage during testing

---

## Summary

**Total tasks**: 24 tasks across 6 phases

**Estimated effort**:

- Phase 1 (Core): 1 day
- Phase 2 (Templates): 1 day
- Phase 3 (Video Gen): 0.5 days
- Phase 4 (Segments): 0.5 days
- Phase 5 (Docs/Tests): 1.5 days
- Phase 6 (Polish): 0.5 days

**Total**: ~5 days

**Critical path**: Phase 1 → Phase 2 → Phase 3 → Phase 5 (for standalone profile overlay)

**Parallel work**: Phase 4 (segments) can be done in parallel with Phase 5 (documentation) after Phase 3

**First deliverable**: Profile-only overlay (Phases 1-3, ~2.5 days)
