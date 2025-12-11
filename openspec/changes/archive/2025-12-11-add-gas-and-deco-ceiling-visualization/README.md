# Add Gas Change and Deco Ceiling Visualization

**Status**: Proposed (Awaiting Approval)

**Change ID**: `add-gas-and-deco-ceiling-visualization`

## Summary

Enhance the dive profile overlay to display:

1. **Gas change markers**: Visual indicators showing when the diver switched breathing gases, with gas mixture labels (e.g., "EAN50", "18/45")
2. **Decompression ceiling**: Shaded area showing the computer-reported minimum depth (ceiling) above which the diver cannot ascend without violating decompression limits

These features are essential for technical diving video overlays, providing context for gas management and decompression obligations visible in the reference image.

## Key Features

- **Gas Change Visualization**
  - Vertical markers at gas change events
  - Gas mixture labels in standard notation
  - Configurable colors, thickness, label fonts
  - Optional visibility toggle

- **Decompression Ceiling Visualization**
  - Filled area or line showing ceiling depth
  - Semi-transparent overlay
  - Configurable fill color, border style
  - Optional visibility toggle

- **Performance Optimized**
  - Static elements pre-rendered during template compilation
  - Minimal per-frame overhead (< 5%)

- **Backward Compatible**
  - Existing templates work unchanged
  - Features are opt-in via template configuration

## Files

- `proposal.md`: Full feature proposal with motivation and goals
- `tasks.md`: Implementation checklist
- `specs/dive-profile-overlay/spec.md`: Requirements and scenarios (delta)

## Validation

```bash
openspec validate add-gas-and-deco-ceiling-visualization --strict
```

✅ Change is valid

## Next Steps

1. Review and approve this proposal
2. Implement per tasks.md checklist
3. Test with sample dive logs (recreational, technical, CCR)
4. Archive change after deployment
