# Change: Add Video Segment Matching

**Status**: Proposal  
**Change ID**: `add-video-segment-matching`  
**Created**: 2025-12-05

## Overview

Enable ScubaOverlay to generate overlay videos for specific segments of a dive that match camera video clips, with automatic timezone offset detection. This allows divers who record multiple short videos during a single dive to create accurate overlays for each clip without manual time calculations.

## Quick Summary

**Problem**: Divers record multiple video clips during a dive, but ScubaOverlay only generates overlays for entire dives. Camera and dive computer may have different timezone settings.

**Solution**:

- Extract video duration using OpenCV (cv2.VideoCapture)
- Read file creation time from file system
- Automatically detect timezone offset (±10 hours)
- Extract matching dive log segment
- Generate overlay for video segment only

**User Value**: Streamlined workflow for multi-clip dive videos with automatic timezone handling.

## Documents

- **[proposal.md](./proposal.md)** - Detailed proposal with user value, scope, and success criteria
- **[design.md](./design.md)** - Architecture and implementation design
- **[tasks.md](./tasks.md)** - Ordered implementation tasks with dependencies
- **[specs/video-segment-matching/spec.md](./specs/video-segment-matching/spec.md)** - Requirements and scenarios

## Key Command-Line Options

```bash
# Automatic segment matching
scuba-overlay --log dive.ssrf --template template.yaml --match-video clip.mp4 --output overlay.mp4

# Manual segment specification
scuba-overlay --log dive.ssrf --template template.yaml \
  --start 300 \
  --duration 180 \
  --output overlay.mp4
```

## Implementation Phases

1. **Video Metadata Extraction** - OpenCV duration extraction and file system timestamps
2. **Timezone Offset Detection** - Iterative offset search algorithm (±5 hours)
3. **Dive Log Segmentation** - Sample filtering and boundary handling
4. **CLI Integration** - Command-line options and segment mode workflow
5. **Manual Overrides** - User-specified timing when automatic detection fails
6. **Documentation** - README updates and detailed guide

## Validation Status

✅ Validated with `openspec validate add-video-segment-matching --strict`

## Next Steps

1. Review proposal with stakeholders
2. Answer questions in proposal.md (timezone range, metadata priorities, etc.)
3. Approve proposal
4. Begin implementation starting with Phase 1 (video metadata extraction)

## Related Specs

- **video-segment-matching** (NEW) - Video segment matching requirements
