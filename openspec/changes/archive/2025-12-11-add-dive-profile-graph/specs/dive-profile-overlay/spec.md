# dive-profile-overlay Specification Delta

## ADDED Requirements

### Requirement: Profile Graph Rendering

The system SHALL render depth profile graphs as line plots with time on X-axis and depth on Y-axis.

#### Scenario: Render basic depth profile graph

- **GIVEN** a dive log with depth samples over time
- **WHEN** user provides `--profile-template profile.yaml`
- **THEN** system generates video with line graph plotting depth vs. time
- **AND** X-axis represents time from dive start to dive end
- **AND** Y-axis represents depth with 0 at top (surface) increasing downward
- **AND** line connects consecutive depth samples with straight segments
- **AND** graph dimensions match template specification

#### Scenario: Auto-scale depth axis to dive max depth

- **GIVEN** a dive with maximum depth of 32.5 meters
- **WHEN** profile overlay is generated
- **THEN** Y-axis scales to accommodate max depth plus 10% padding
- **AND** Y-axis range is 0 to approximately 35.75 meters (32.5 * 1.1)
- **AND** graph uses full vertical space efficiently

#### Scenario: Render depth in imperial units

- **GIVEN** user provides `--units imperial`
- **WHEN** profile overlay is generated
- **THEN** depth values are converted to feet before plotting
- **AND** Y-axis labels display feet (ft)
- **AND** graph scaling accounts for feet scale (not meters)

#### Scenario: Handle shallow dives

- **GIVEN** a dive with maximum depth of 3 meters
- **WHEN** profile overlay is generated
- **THEN** Y-axis scales to 3.3 meters (with 10% padding)
- **AND** graph renders without division-by-zero errors
- **AND** depth profile is clearly visible

#### Scenario: Handle deep technical dives

- **GIVEN** a dive with maximum depth of 85 meters
- **WHEN** profile overlay is generated
- **THEN** Y-axis scales to 93.5 meters (with 10% padding)
- **AND** graph renders without overflow or scaling issues
- **AND** depth profile fits within graph area

### Requirement: Position Indicator

The system SHALL display a moving position indicator on the profile graph showing the current moment in the dive.

#### Scenario: Render position indicator as circular dot

- **GIVEN** a profile graph at dive time T seconds
- **WHEN** frame is rendered for time T
- **THEN** system draws a circular dot on the graph line
- **AND** dot X-coordinate corresponds to time T on time axis
- **AND** dot Y-coordinate corresponds to depth at time T
- **AND** dot size and color match template specification

#### Scenario: Move position indicator as dive progresses

- **GIVEN** a 10-minute dive profile overlay at 10 fps
- **WHEN** video plays from start to end
- **THEN** position indicator moves left-to-right along graph line
- **AND** indicator position accurately reflects current dive time
- **AND** indicator moves smoothly (updates once per second minimum)

#### Scenario: Position indicator snaps to nearest sample

- **GIVEN** dive samples at 2-second intervals (Subsurface standard)
- **WHEN** video frame is rendered at time T
- **THEN** position indicator snaps to sample with `sample.time <= T`
- **AND** no interpolation between samples (accurate to dive computer data)

### Requirement: Profile Template System

The system SHALL support YAML templates for customizing profile graph appearance and layout.

#### Scenario: Load profile template with graph dimensions

- **GIVEN** a profile template specifying `width: 1920`, `height: 400`
- **WHEN** template is loaded
- **THEN** output video frame size is 1920x400 pixels
- **AND** graph is positioned within frame per template
- **AND** frame size is independent of computer overlay template (if any)

#### Scenario: Customize graph line appearance

- **GIVEN** a profile template specifying:
  - `line.color: "#00AAFF"`
  - `line.thickness: 5`
- **WHEN** profile overlay is generated
- **THEN** depth profile line is rendered in color #00AAFF (blue)
- **AND** line thickness is 5 pixels
- **AND** line style is solid (no dashes or patterns)

#### Scenario: Customize position indicator appearance

- **GIVEN** a profile template specifying:
  - `indicator.color: "#FF0000"`
  - `indicator.size: 15`
- **WHEN** profile overlay is generated
- **THEN** position indicator dot is rendered in color #FF0000 (red)
- **AND** dot radius is 15 pixels
- **AND** dot is circular shape

#### Scenario: Use chroma key background for compositing

- **GIVEN** a profile template specifying:
  - `background_color: "#00FF00"`
- **WHEN** profile overlay is generated
- **THEN** background is rendered in chroma key color #00FF00 (green)
- **AND** profile graph elements are rendered on top of chroma background
- **AND** video can be composited onto dive footage using green screen

#### Scenario: Use solid color background

- **GIVEN** a profile template specifying `background_color: "#1a1a1a"`
- **WHEN** profile overlay is generated
- **THEN** background is rendered as solid color #1a1a1a (dark gray)
- **AND** overlay is opaque

#### Scenario: Position graph within frame

- **GIVEN** a profile template specifying:
  - `graph.position: { x: 100, y: 50 }`
  - `graph.width: 1700`
  - `graph.height: 300`
- **WHEN** profile overlay is generated
- **THEN** graph area starts at pixel coordinates (100, 50)
- **AND** graph area is 1700 pixels wide by 300 pixels tall
- **AND** graph elements stay within defined area

#### Scenario: Minimal template with defaults

- **GIVEN** a profile template specifying only:
  - `width`, `height`
  - `graph.position`, `graph.width`, `graph.height`
  - `graph.line.color`, `graph.line.thickness`
  - `graph.indicator.color`, `graph.indicator.size`
- **WHEN** template is loaded
- **THEN** all unspecified fields use reasonable defaults
- **AND** graph renders successfully without errors
- **AND** no grid lines or axis labels are shown (minimal mode)

### Requirement: Command-Line Interface for Profile Overlays

The system SHALL accept `--profile-template` argument to generate profile graph overlays.

#### Scenario: Generate profile overlay only

- **GIVEN** user runs command:
  ```
  scuba-overlay --log dive.ssrf --profile-template profile.yaml --output profile.mp4
  ```
- **WHEN** command executes
- **THEN** system generates profile graph overlay video
- **AND** output video contains only profile graph (no computer data overlay)
- **AND** video is saved to `profile.mp4`

#### Scenario: Error when both templates provided

- **GIVEN** user runs command:
  ```
  scuba-overlay --log dive.ssrf --template computer.yaml --profile-template profile.yaml --output output.mp4
  ```
- **WHEN** command executes
- **THEN** system reports error that templates are mutually exclusive
- **AND** error message suggests running command twice for separate overlays
- **AND** program exits with non-zero status

#### Scenario: Error when no template provided

- **GIVEN** user runs command:
  ```
  scuba-overlay --log dive.ssrf --output output.mp4
  ```
- **WHEN** command executes
- **THEN** system reports error requiring at least one template
- **AND** error message suggests using `--template` or `--profile-template`
- **AND** program exits with non-zero status

#### Scenario: Error when profile template provided without dive log

- **GIVEN** user runs command:
  ```
  scuba-overlay --profile-template profile.yaml --output output.mp4
  ```
- **WHEN** command executes
- **THEN** system reports error requiring `--log` argument
- **AND** error message indicates dive data is needed for profile graph
- **AND** program exits with non-zero status

### Requirement: Profile Overlay with Video Segment Matching

The system SHALL generate profile graphs for dive segments when using `--match-video` or `--start` options.

#### Scenario: Profile graph for video segment

- **GIVEN** a 40-minute dive log
- **AND** user provides `--match-video clip.mp4` for 3-minute clip at 15-18 minutes into dive
- **WHEN** profile overlay with `--profile-template` is generated
- **THEN** profile graph shows only 15:00 to 18:00 segment of dive
- **AND** X-axis spans 3 minutes (180 seconds)
- **AND** position indicator moves from left to right over 3 minutes
- **AND** depth samples outside segment are not shown on graph

#### Scenario: Profile graph for manual segment

- **GIVEN** user provides `--start 600 --duration 120` (10-12 minutes into dive)
- **WHEN** profile overlay with `--profile-template` is generated
- **THEN** profile graph shows only 600-720 second segment
- **AND** X-axis spans 120 seconds (2 minutes)
- **AND** graph auto-scales to max depth within segment (not full dive)

### Requirement: Performance Optimization for Profile Rendering

The system SHALL pre-render static graph elements once and update only the position indicator per frame.

#### Scenario: Pre-render static graph during template compilation

- **GIVEN** a profile template and dive samples
- **WHEN** template is compiled
- **THEN** system renders complete depth profile line once
- **AND** static background (grid, axes, profile line) is cached
- **AND** cached background is reused for every frame

#### Scenario: Fast frame rendering with position indicator

- **GIVEN** a pre-compiled profile template
- **WHEN** each video frame is generated
- **THEN** system copies cached static background
- **AND** system draws only position indicator dot (small circle)
- **AND** frame rendering is fast (comparable to computer overlay rendering)
- **AND** no full graph redraw occurs per frame

### Requirement: Test Template for Profile Validation

The system SHALL support `--test-template` flag for profile templates to generate sample output.

#### Scenario: Generate test profile graph image

- **GIVEN** user runs command:
  ```
  scuba-overlay --profile-template profile.yaml --test-template
  ```
- **WHEN** command executes
- **THEN** system generates single PNG image `test_profile_template.png`
- **AND** image shows dummy profile graph (simulated dive profile)
- **AND** position indicator is shown at mid-dive position
- **AND** user can validate template layout and colors without full dive log
