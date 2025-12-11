# dive-profile-overlay Specification (Delta)

## ADDED Requirements

### Requirement: Gas Change Visualization

The system SHALL render gas change events on the profile graph showing when the diver switched breathing gases.

#### Scenario: Render gas change markers on profile

- **GIVEN** a dive log with 3 gas changes at times 0s, 1200s, and 2400s
- **AND** profile template with `gas_changes.show: true`
- **WHEN** profile overlay is generated
- **THEN** system draws icon markers at X-coordinates for 0s, 1200s, and 2400s
- **AND** markers are positioned at the depth where gas change occurred
- **AND** marker color and size match template specification

#### Scenario: Display gas mixture labels at gas changes

- **GIVEN** a dive with gas change to EAN50 (50% oxygen) at 1200s
- **AND** profile template with `gas_changes.show_labels: true`
- **WHEN** profile overlay is generated
- **THEN** system displays "EAN50" label near the 1200s marker
- **AND** label is positioned above or below marker per template `label_position`
- **AND** label font, size, and color match template specification

#### Scenario: Format trimix gas labels

- **GIVEN** a dive with gas change to trimix (18% O2, 45% He) at 600s
- **WHEN** profile overlay is generated
- **THEN** system displays label as "18/45" (oxygen/helium percentages)
- **AND** nitrogen percentage is implied (not shown)
- **AND** label format follows standard diving notation

#### Scenario: Format nitrox gas labels

- **GIVEN** a dive with gas change to nitrox (50% O2) at 1800s
- **WHEN** profile overlay is generated
- **THEN** system displays label as "EAN50" (Enriched Air Nitrox)
- **AND** label format follows standard diving notation

#### Scenario: Format air gas labels

- **GIVEN** a dive with gas change to air (21% O2) at 0s
- **WHEN** profile overlay is generated
- **THEN** system displays label as "AIR" or "21/0"
- **AND** label clearly indicates standard air mixture
- **AND** label format follows standard diving notation

#### Scenario: Hide gas changes when disabled

- **GIVEN** a dive log with gas change events
- **AND** profile template with `gas_changes.show: false` OR no gas_changes section
- **WHEN** profile overlay is generated
- **THEN** no gas change markers or labels are rendered
- **AND** profile graph appears as if feature is not present

#### Scenario: Handle dive with no gas changes

- **GIVEN** a recreational dive with single gas (air) throughout
- **AND** profile template with `gas_changes.show: true`
- **WHEN** profile overlay is generated
- **THEN** no gas change markers are rendered (no events to display)
- **AND** no errors or warnings are generated
- **AND** profile graph renders normally

#### Scenario: Handle multiple rapid gas changes

- **GIVEN** a dive with 3 gas changes within 60 seconds (60s, 90s, 120s)
- **AND** profile template with `gas_changes.show: true`
- **WHEN** profile overlay is generated
- **THEN** all 3 markers are rendered at correct X-coordinates
- **AND** labels do not overlap (positioned to avoid collision)
- **AND** all gas changes are clearly visible

#### Scenario: Gas change markers in imperial units

- **GIVEN** a dive with gas change at depth 18 meters
- **AND** user provides `--units imperial`
- **AND** profile template with `gas_changes.show: true`
- **WHEN** profile overlay is generated
- **THEN** marker is positioned at correct Y-coordinate for 59.06 feet (18m converted)
- **AND** gas mixture label is unaffected by unit choice (always percentage)

### Requirement: Decompression Ceiling Visualization

The system SHALL render the dive computer's reported decompression ceiling as a shaded area on the profile graph.

#### Scenario: Render ceiling as filled area

- **GIVEN** a decompression dive with ceiling ranging from 0m to 12m over time
- **AND** profile template with `deco_ceiling.style: "filled"`
- **WHEN** profile overlay is generated
- **THEN** system draws filled polygon from surface (0m) to ceiling depth line
- **AND** polygon fill color matches template `fill_color` specification
- **AND** ceiling area is semi-transparent (alpha channel respected)
- **AND** ceiling clearly shows forbidden ascent zone

#### Scenario: Render ceiling as line only

- **GIVEN** a decompression dive with ceiling data
- **AND** profile template with `deco_ceiling.style: "line"`
- **WHEN** profile overlay is generated
- **THEN** system draws line along ceiling depth over time
- **AND** no filled area is rendered
- **AND** line color and thickness match template specification

#### Scenario: Render ceiling with both fill and line

- **GIVEN** a decompression dive with ceiling data
- **AND** profile template with `deco_ceiling.style: "both"`
- **WHEN** profile overlay is generated
- **THEN** system draws filled polygon for ceiling area
- **AND** system draws border line at ceiling depth
- **AND** fill and line colors/styles are independently configurable

#### Scenario: Hide ceiling when disabled

- **GIVEN** a decompression dive with ceiling data
- **AND** profile template with `deco_ceiling.show: false` OR no deco_ceiling section
- **WHEN** profile overlay is generated
- **THEN** no ceiling visualization is rendered
- **AND** profile graph appears as if feature is not present

#### Scenario: Handle dive with no ceiling (recreational)

- **GIVEN** a recreational no-decompression dive (NDL dive)
- **AND** all samples have `stopdepth: 0` or `stopdepth: None`
- **AND** profile template with `deco_ceiling.show: true`
- **WHEN** profile overlay is generated
- **THEN** no ceiling area is rendered (ceiling is 0m = surface)
- **AND** no errors or warnings are generated
- **AND** profile graph renders normally

#### Scenario: Ceiling transitions smoothly

- **GIVEN** a dive with ceiling starting at 0m, increasing to 18m, then decreasing back to 0m
- **AND** profile template with `deco_ceiling.show: true`
- **WHEN** profile overlay is generated
- **THEN** ceiling polygon connects sample points with straight segments
- **AND** ceiling area expands and contracts smoothly over time
- **AND** no gaps or artifacts appear at ceiling transitions

#### Scenario: Ceiling respects graph boundaries

- **GIVEN** a dive with ceiling data
- **AND** profile template defining graph area (x, y, width, height)
- **WHEN** profile overlay is generated
- **THEN** ceiling polygon is clipped to graph boundaries
- **AND** ceiling does not extend beyond graph area
- **AND** ceiling fills from surface (top) to ceiling depth within graph

#### Scenario: Ceiling in imperial units

- **GIVEN** a dive with ceiling at 9 meters
- **AND** user provides `--units imperial`
- **AND** profile template with `deco_ceiling.show: true`
- **WHEN** profile overlay is generated
- **THEN** ceiling polygon is positioned at correct Y-coordinate for 29.53 feet (9m converted)
- **AND** ceiling depth auto-scales with imperial depth axis

#### Scenario: Ceiling with missing data points

- **GIVEN** a dive where stopdepth is only reported every 30 seconds (sparse samples)
- **AND** profile template with `deco_ceiling.show: true`
- **WHEN** profile overlay is generated
- **THEN** system connects available ceiling points with straight segments
- **AND** no interpolation between samples (accurate to dive computer data)
- **AND** ceiling visualization reflects actual reported data

### Requirement: Combined Gas and Ceiling Visualization

The system SHALL render both gas changes and decompression ceiling when both are enabled and present in dive data.

#### Scenario: Render gas changes above ceiling area

- **GIVEN** a technical dive with both gas changes and decompression ceiling
- **AND** profile template with `gas_changes.show: true` and `deco_ceiling.show: true`
- **WHEN** profile overlay is generated
- **THEN** ceiling area is rendered on static background layer
- **AND** gas change markers are rendered on top of ceiling area
- **AND** gas change labels are clearly visible (not obscured by ceiling)
- **AND** both features are visually distinct and readable

#### Scenario: Gas change during deco stop

- **GIVEN** a dive with gas change at 1800s while at 6m deco stop
- **AND** ceiling depth is 6m at time of gas change
- **AND** profile template with both features enabled
- **WHEN** profile overlay is generated
- **THEN** gas change marker is drawn at correct X-coordinate (1800s)
- **AND** marker extends from graph bottom to depth profile (6m)
- **AND** marker passes through ceiling area
- **AND** gas mixture label is positioned clearly (e.g., above ceiling area)

#### Scenario: Visual layering order

- **GIVEN** a profile with ceiling, depth profile line, gas changes, and position indicator
- **WHEN** frame is rendered
- **THEN** rendering order is (bottom to top):
  1. Background color
  2. Grid lines (if enabled)
  3. Decompression ceiling (filled area)
  4. Depth profile line
  5. Gas change markers and labels
  6. Position indicator dot
- **AND** layering ensures all elements are visible and clear

### Requirement: Template Configuration for Gas and Ceiling

The system SHALL support YAML template configuration for gas change and ceiling visualization appearance.

#### Scenario: Configure gas change marker appearance

- **GIVEN** a profile template specifying:
  ```yaml
  gas_changes:
    show: true
    marker:
      color: "#FFA500"  # Orange
      size: 12
      icon: "▼"  # Down-pointing triangle
  ```
- **WHEN** template is loaded
- **THEN** gas change markers are rendered in orange color
- **AND** marker icon size is 12 pixels
- **AND** marker uses the specified icon glyph

#### Scenario: Configure gas change label appearance

- **GIVEN** a profile template specifying:
  ```yaml
  gas_changes:
    show: true
    show_labels: true
    label_font: { name: "Arial", size: 14, color: "#FFFFFF" }
    label_position: "above"  # or "below"
  ```
- **WHEN** template is loaded
- **THEN** gas labels use Arial font at 14px size
- **AND** labels are white color (#FFFFFF)
- **AND** labels are positioned above the marker icon
- **AND** labels use standard diving notation (e.g., "EAN50", "18/45")

#### Scenario: Configure ceiling fill appearance

- **GIVEN** a profile template specifying:
  ```yaml
  deco_ceiling:
    show: true
    style: "filled"
    fill_color: "#FF000040"  # Red with 25% opacity (RGBA)
  ```
- **WHEN** template is loaded
- **THEN** ceiling area is rendered with red fill color
- **AND** ceiling has 25% opacity (75% transparent)
- **AND** underlying profile line is visible through ceiling

#### Scenario: Configure ceiling border line

- **GIVEN** a profile template specifying:
  ```yaml
  deco_ceiling:
    show: true
    style: "both"
    fill_color: "#80000030"
    border:
      color: "#FF0000"
      thickness: 2
  ```
- **WHEN** template is loaded
- **THEN** ceiling area is filled with dark red (30% opacity)
- **AND** ceiling border line is drawn in bright red (#FF0000)
- **AND** border line thickness is 2 pixels
- **AND** border line traces the top of the ceiling area

#### Scenario: Default values when configuration omitted

- **GIVEN** a profile template with `gas_changes: { show: true }` (minimal config)
- **WHEN** template is loaded
- **THEN** system uses sensible defaults:
  - marker color: white or contrasting color
  - marker thickness: 2 pixels
  - show_labels: true
  - label_font: Arial, 12px, white
  - label_position: "above"
  - labels use standard diving notation
- **AND** gas changes render successfully without errors

#### Scenario: Backward compatibility with old templates

- **GIVEN** an existing profile template without gas_changes or deco_ceiling sections
- **WHEN** template is loaded and used
- **THEN** neither gas changes nor ceiling are rendered
- **AND** profile overlay renders exactly as before (no behavior change)
- **AND** no errors or warnings are generated

### Requirement: Performance Optimization for Static Elements

The system SHALL pre-render gas changes and ceiling as static elements during template compilation.

#### Scenario: Pre-render gas changes during compilation

- **GIVEN** a dive with 4 gas changes
- **WHEN** profile template is compiled
- **THEN** all gas change markers and labels are rendered once to static background
- **AND** gas change elements are cached with depth profile line
- **AND** no per-frame rendering of gas changes occurs

#### Scenario: Pre-render ceiling during compilation

- **GIVEN** a decompression dive with ceiling data
- **WHEN** profile template is compiled
- **THEN** ceiling polygon is computed and rendered once to static background
- **AND** ceiling area is cached with depth profile line
- **AND** no per-frame rendering of ceiling occurs

#### Scenario: Frame rendering remains fast

- **GIVEN** a compiled profile template with gas changes and ceiling enabled
- **WHEN** each video frame is generated
- **THEN** system copies cached static background (with ceiling, profile, grid, gas changes)
- **AND** system draws only position indicator dot (dynamic element)
- **AND** frame rendering time is not significantly increased vs. simple profile
- **AND** performance overhead is < 5% compared to profile without features
