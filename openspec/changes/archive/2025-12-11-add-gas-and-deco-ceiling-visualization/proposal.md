# Proposal: Add Gas Change and Deco Ceiling Visualization

## Overview

Enhance the dive profile overlay to display gas changes and decompression ceiling information, providing critical context for technical diving video overlays. This feature will visualize breathing gas switches and mandatory decompression stops directly on the depth profile graph.

## Motivation

Technical divers frequently switch between multiple breathing gases during a dive (bottom gas, travel gas, deco gases) and must respect decompression ceiling limits during ascent. Current profile overlays show only the depth profile and position indicator, lacking essential information that provides context for technical dive videos:

1. **Gas Changes**: Viewers cannot see when the diver switched gases, which is important for understanding dive strategy and safety margins
2. **Decompression Ceiling**: The mandatory minimum depth (ceiling) is not visualized, making it unclear when and why the diver stops at specific depths during ascent

These visualizations are standard in dive computer displays and dive planning software (as shown in the reference image), making them familiar to technical diving audiences.

## Goals

1. **Visual Gas Change Indicators**: Display markers on the profile graph showing when breathing gas switches occurred, with gas mixture information (e.g., "EAN50" for 50% oxygen nitrox, "18/45" for 18% oxygen / 45% helium trimix)
2. **Decompression Ceiling Overlay**: Render a shaded area or line showing the computer-reported decompression ceiling over time
3. **Template Configuration**: Allow users to customize appearance (colors, sizes, positions) via YAML templates
4. **Data Availability**: Leverage existing parsed data from dive logs (gas change events and stopdepth already parsed but not visualized)

## Non-Goals

1. **Ceiling Calculation**: We will NOT calculate decompression ceilings ourselves - only display ceilings reported by the dive computer in the log file
2. **Planned vs Actual Comparison**: We will NOT show planned profiles or compare against dive plans
3. **Multiple Divers**: Single diver only (consistent with existing limitations)
4. **Gas Management Details**: We will NOT show tank pressures, SAC rates, or gas time remaining on the profile graph (these belong in computer overlay templates)

## Impact

### User-Facing Changes

- **New Template Fields**: Profile templates gain optional `gas_changes` and `deco_ceiling` configuration sections
- **Enhanced Visualizations**: Profile overlays automatically include gas change markers and ceiling overlay when configured and when data is available in dive log
- **Backward Compatibility**: Existing templates without these fields continue to work unchanged (new features are optional)

### Technical Impact

- **Rendering Performance**: Minimal - gas changes are static markers (pre-rendered), ceiling is a filled polygon (one draw call per frame)
- **Parser Changes**: None required - gas change events and stopdepth data are already parsed
- **Template Schema**: Extended with new optional configuration sections

## Open Questions

1. **Gas Label Format**: How should gas mixtures be displayed?
   - Option A: Standard notation (e.g., "EAN50", "21/35" for trimix)
   - Option B: Full text (e.g., "50% O2", "O2:21% He:35%")
   - **Recommendation**: Standard notation (compact, familiar to technical divers)

2. **Multiple Ceiling Representation**: Should we show:
   - Option A: Only the deepest mandatory stop (stopdepth from dive computer)
   - Option B: Full ceiling gradient (if available in dive computer data)
   - **Recommendation**: Start with stopdepth (what's currently available), expand later if needed

3. **Icon vs Text for Gas Changes**: Should gas changes use:
   - Option A: Icon/symbol at the gas change point
   - Option B: Text label with gas mixture
   - Option C: Both (icon + text)
   - **Recommendation**: Both - icon for visual marker, text for identification

## Timeline

1. **Specification** (This proposal): Define requirements and scenarios
2. **Implementation**:
   - Add gas change rendering (markers + labels)
   - Add deco ceiling rendering (shaded area)
   - Update template schema and validation
   - Add template examples
3. **Testing**: Validate with multiple dive log formats (Subsurface, Shearwater) and dive types (recreational, technical, CCR)
4. **Documentation**: Update template guide with new configuration options

## Success Criteria

- [ ] Gas change events from dive logs are rendered as visible markers on profile graph
- [ ] Gas mixture labels are displayed at each gas change point
- [ ] Decompression ceiling is rendered as shaded area or line above which the diver cannot ascend
- [ ] Template configuration allows customization of colors, sizes, and visibility
- [ ] Feature works with both Subsurface (.ssrf) and Shearwater (.xml) dive logs
- [ ] Existing templates without new fields continue to work without errors
- [ ] Performance overhead is negligible (< 5% increase in frame rendering time)
