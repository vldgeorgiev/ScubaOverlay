# Proposal: Add Video Segment Matching

## Problem

ScubaOverlay currently generates overlay videos for entire dive logs. However, divers commonly record multiple short video clips during a single dive rather than one continuous recording. When compositing these clips in post-production, users need overlay videos that match only the specific time segments captured on camera.

Additionally, camera timestamps are often in different timezones than dive computer timestamps, causing misalignment between video start times and dive log data. Users must manually calculate offsets and extract segments, which is error-prone and time-consuming.

## User Value

This feature enables divers to:

1. **Generate accurate overlays for video clips** - Create overlay videos that match the exact timing and duration of camera footage
2. **Avoid manual time calculations** - Automatic timezone offset detection eliminates manual offset calculation
3. **Streamline post-production workflow** - Generate multiple overlays for multiple clips from a single dive
4. **Handle real-world camera scenarios** - Support videos with varying metadata quality and timezone settings

### Example Use Case

A diver records three video clips during a 40-minute dive:
- Clip 1: 5:23 into dive, 2 minutes duration
- Clip 2: 18:45 into dive, 3 minutes duration  
- Clip 3: 32:10 into dive, 90 seconds duration

Camera timezone is UTC-8, dive computer is UTC-7 (1 hour difference).

**Current workflow**:
1. Manually calculate timezone offset
2. Manually determine each clip's position in dive timeline
3. Manually extract dive log segments
4. Generate three overlay videos with complex time calculations

**New workflow**:
```bash
scuba-overlay --log dive.ssrf --template template.yaml --match-video clip1.mp4 --output overlay1.mp4
scuba-overlay --log dive.ssrf --template template.yaml --match-video clip2.mp4 --output overlay2.mp4
scuba-overlay --log dive.ssrf --template template.yaml --match-video clip3.mp4 --output overlay3.mp4
```

System automatically handles timezone detection and segment extraction for each clip.

## Scope

### In Scope

1. **Video metadata extraction**
   - Read video duration using OpenCV (cv2.VideoCapture)
   - Read file creation time from file system
   - Support common video formats that OpenCV can read (MP4, AVI, MOV, etc.)

2. **Automatic timezone offset detection**
   - Try timezone offsets from 0 to ±10 hours in 1-hour increments
   - Select offset that places video start time within dive log timeframe
   - Choose smallest absolute offset when multiple offsets match
   - Report detailed diagnostics when no offset matches
   - Not user-configurable (fixed at ±10 hours for simplicity)

3. **Dive log segment extraction**
   - Filter dive samples to match video time segment
   - Include boundary samples for smooth interpolation
   - Handle edge cases (video starts before dive, extends after dive)
   - Generate overlay video with segment duration

4. **Command-line interface**
   - `--match-video <path>` - Automatic segment matching mode
   - `--start <seconds>` - Manual start time in seconds from dive start
   - `--duration <seconds>` - Manual duration override (reuses existing flag)
   - Timezone offset detection: automatic ±10 hours (not configurable)

5. **Documentation**
   - README section explaining feature and usage
   - Detailed guide in `docs/video-segment-matching.md`
   - Example commands and troubleshooting tips
   - Timezone offset explanation and examples

### Out of Scope

- **Multiple video batch processing** - Process one video at a time (users run command multiple times)
- **GPS coordinate matching** - No geographic data matching between video and dive log
- **GoPro GPMF telemetry** - No specialized GoPro metadata support
- **Machine learning offset detection** - Simple iterative search only
- **Video file discovery** - Users must specify video file path explicitly
- **Subsecond timestamp precision** - Work at 1-second granularity (matching dive log sample rate)
- **Graphical user interface** - Command-line interface only

## Dependencies

### System Dependencies

- None (uses existing OpenCV library)

### Python Dependencies

- No new external dependencies (uses existing opencv-python)
- New stdlib modules: `datetime`, `os` (all standard library)

### Code Changes

**New files**:
- `src/video_metadata.py` - Video metadata extraction logic

**Modified files**:
- `src/main.py` - Add command-line options and segment mode logic
- `src/parser.py` - Add segment extraction function and new exception classes
- `src/overlay.py` - Handle segment-based sample lists (no changes likely needed)
- `README.md` - Add Video Segment Matching section
- `docs/video-segment-matching.md` - New detailed guide

## Implementation Phases

### Phase 1: Video Metadata Extraction (Foundation)

Implement video metadata extraction using OpenCV for duration and file system for creation time.

**Deliverable**: `video_metadata.py` module with functions to extract start time and duration

**Validation**: Command successfully extracts and displays metadata from test videos

### Phase 2: Timezone Offset Detection (Core Algorithm)

Implement iterative timezone offset detection algorithm.

**Deliverable**: Offset detection function that tries ±5 hour range

**Validation**: Correct offset detected for videos with known timezone differences

### Phase 3: Dive Log Segmentation (Core Feature)

Implement dive sample filtering and segment extraction.

**Deliverable**: Function to filter dive samples by time range with boundary handling

**Validation**: Segmented overlays match video clip timing exactly

### Phase 4: CLI Integration (User Interface)

Add command-line options and integrate segment mode into main.py.

**Deliverable**: Working `--match-video` option with automatic segment matching

**Validation**: End-to-end workflow generates correct overlay for video clip

### Phase 5: Manual Overrides (Flexibility)

Implement manual override options for edge cases.

**Deliverable**: `--start` and `--duration` options for manual segment specification

**Validation**: Manual overrides work correctly and bypass automatic detection

### Phase 6: Documentation (User Enablement)

Write comprehensive documentation with examples and troubleshooting.

**Deliverable**: Updated README and new video-segment-matching.md guide

**Validation**: Documentation provides clear guidance for common scenarios

## Risks and Mitigations

### Risk: Unsupported video formats

**Mitigation**: OpenCV supports most common formats. Clear error message for unsupported formats. Document supported formats in README. Provide manual override options.

### Risk: Video file read failures

**Mitigation**: Handle OpenCV read errors gracefully. Use file creation time from OS. Provide clear error messages. Document known format limitations.

### Risk: Ambiguous timezone offset detection

**Mitigation**: Choose smallest absolute offset. Provide manual override options. Log detailed diagnostics.

### Risk: Dive computer clock drift

**Mitigation**: Timezone offset detection allows ±5 hour range. Manual offset override available. Document clock synchronization best practices.

### Risk: Video spanning multiple dives

**Mitigation**: Current single-dive limitation already documented. Segment extraction validates bounds within single dive.

## Success Criteria

1. **Automatic matching works for common scenarios** - Users can generate segment overlays without manual time calculations in 80%+ of cases
2. **Timezone offset detection is robust** - Correctly detects offsets within ±5 hour range with appropriate error messages
3. **Documentation is clear** - Users can understand and use feature from README examples alone
4. **Error messages are actionable** - Failed matching provides specific diagnostics and manual override suggestions
5. **Performance is acceptable** - Metadata extraction adds <2 seconds to overlay generation time

## Related Changes

None - This is a new capability with no dependencies on other changes.

## Alternatives Considered

### Alternative 1: GPS-based matching

Use GPS coordinates from video and dive log to match timing.

**Rejected**: Requires GPS data in both video and dive log. Not universally available. More complex implementation.

### Alternative 2: Machine learning timezone detection

Use ML model to predict timezone based on dive location and video metadata.

**Rejected**: Overkill for simple offset problem. Adds heavy dependencies. Simple iterative search is sufficient.

### Alternative 3: Batch video processing

Process multiple videos in single command invocation.

**Rejected**: Adds complexity to CLI and error handling. Users can easily run command multiple times. Can be added later if needed.

### Alternative 4: Interactive offset selection

Present user with offset options and ask for selection.

**Rejected**: Breaks automation. CLI tool should be scriptable. Manual override flags provide flexibility without breaking automation.

## Questions for Stakeholders

1. **Timezone offset range**: Is ±5 hours sufficient, or should we support larger ranges (e.g., ±12 hours)? Should be up to 10h
2. **Metadata format support**: Are there specific video formats or metadata standards we should prioritize? No
3. **Batch processing**: Is processing one video at a time acceptable, or is batch processing critical for initial release? One at a time is ok.
4. **Documentation depth**: Should we provide video tutorials or examples in addition to written documentation? Not yet
5. **File creation time reliability**: Is file system creation time reliable enough as fallback, or should we require video metadata? Video metadata first, then file creation as fallback
