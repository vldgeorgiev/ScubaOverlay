# Implementation Tasks

## Phase 1: Gas Change Visualization

### Data Layer

- [x] Verify gas change event parsing works for Subsurface format
- [x] Verify gas change event parsing works for Shearwater format
- [x] Add helper function to format gas mixture for display (e.g., "21/35" for trimix, "EAN50" for nitrox)
- [x] Extract gas change events from parsed dive data for rendering

### Rendering Layer

- [x] Implement gas change marker rendering function
  - [x] Draw vertical line at gas change time
  - [x] Position marker icon at appropriate depth
  - [x] Add gas mixture label near marker
- [x] Add gas change rendering to template compilation (static elements)
- [x] Handle edge cases (gas changes at dive start, multiple rapid changes)

### Template Configuration

- [x] Define template schema for gas_changes section
  - [x] Marker style (line, icon, both)
  - [x] Marker color and thickness
  - [x] Label font, size, color
  - [x] Label position (above/below marker)
  - [x] Visibility toggle (show_gas_changes: true/false)
- [x] Add validation for gas_changes configuration
- [x] Define sensible defaults when gas_changes not specified

## Phase 2: Decompression Ceiling Visualization

### Ceiling Data Layer

- [x] Verify stopdepth parsing works for Subsurface format
- [x] Verify stopdepth parsing works for Shearwater format
- [x] Extract ceiling depth timeline from dive samples

### Ceiling Rendering Layer

- [x] Implement ceiling visualization rendering
  - [x] Compute ceiling polygon coordinates from samples
  - [x] Fill ceiling area with semi-transparent color
  - [x] Optional: draw ceiling line at top of shaded area
- [x] Add ceiling rendering to template compilation (static background)
- [x] Handle edge cases (ceiling at 0m, missing ceiling data, ceiling changes)

### Ceiling Template Configuration

- [x] Define template schema for deco_ceiling section
  - [x] Fill color (RGBA for transparency)
  - [x] Border line color and thickness (optional)
  - [x] Visualization style (filled_area, line, both)
  - [x] Visibility toggle (show_deco_ceiling: true/false)
- [x] Add validation for deco_ceiling configuration
- [x] Define sensible defaults when deco_ceiling not specified

## Phase 3: Template Examples and Documentation

### Template Files

- [x] Create example template with gas changes only
- [x] Create example template with deco ceiling only
- [x] Create example template with both features enabled
- [x] Update profile-full.yaml with comprehensive documentation

### Testing

- [x] Test with recreational dive (no gas changes, no ceiling)
- [x] Test with single gas change dive
- [x] Test with multiple gas changes (technical dive)
- [x] Test with decompression dive (ceiling data present)
- [x] Test with CCR dive (multiple gas changes + ceiling)
- [x] Test with Subsurface format
- [x] Test with Shearwater format
- [x] Test backward compatibility (old templates still work)
- [x] Verify performance impact is minimal

### Documentation

- [x] Document gas_changes configuration in profile-template-guide.md
- [x] Document deco_ceiling configuration in profile-template-guide.md
- [x] Add examples with screenshots showing the features
- [x] Update README.md with feature description

## Phase 4: Validation and Polish

- [x] Run openspec validate to ensure spec compliance
- [x] Review all scenarios in spec are implemented
- [x] Check error handling for missing/invalid data
- [x] Verify unit conversions work correctly (imperial units)
- [x] Code review and cleanup

