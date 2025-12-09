# Design: Video Segment Matching

## Problem Statement

Currently, ScubaOverlay generates overlay videos for entire dive logs. However, divers often record multiple short video clips during a single dive rather than one continuous recording. When compositing these clips, users need overlay videos that match only the specific time segments captured on camera.

Additionally, camera timestamps may be in different timezones than the dive computer, causing misalignment between the video start time and the dive log timeline.

## Requirements

1. **Video metadata extraction**: Read video file metadata to determine start time and duration
2. **Timezone offset detection**: Automatically detect and correct timezone mismatches (±1-5 hours) between camera and dive computer
3. **Dive log segmentation**: Extract and generate overlay for only the portion of the dive log that matches the video segment
4. **Fallback to file creation time**: Use file system creation time when video metadata is unavailable
5. **User override**: Allow manual specification of video start time and offset when automatic detection fails

## Architecture

### Video Metadata Extraction

**Tool**: `cv2` library

**Metadata sources** (in order of preference):
1. Video creation time metadata (`creation_time` tag)
2. File system creation time (`stat.st_birthtime` or `stat.st_ctime`)

**Implementation**: New module `video_metadata.py` with functions:
- `extract_video_metadata(video_path: str) -> VideoMetadata`
- `get_video_duration(video_path: str) -> float`
- `get_video_creation_time(video_path: str) -> datetime`

### Timezone Offset Detection

**Strategy**: Iterative matching with ±1 hour increments

1. Extract video start time from metadata
2. Check if start time falls within dive log timeframe (dive start to dive end)
3. If not, try offsets: +1h, -1h, +2h, -2h, ..., +10h, -10h
4. Use first offset that places video start time within dive timeframe
5. If no offset works, report error with detailed diagnostic information

**Edge cases**:
- Multiple offset candidates: Choose smallest absolute offset
- Video spans dive boundaries: Accept if start time is within dive
- Short dives vs. long offset range: Validate end time is also reasonable

### Dive Log Segmentation

**Approach**: Filter dive samples by time range

1. Convert video start time to seconds from dive start
2. Calculate video end time: `start + duration`
3. Filter `DiveSample` list to only include samples where `start_time <= sample.time <= end_time`
4. Generate overlay video using filtered sample list

**Considerations**:
- Preserve first sample before segment start for smooth interpolation
- Include last sample after segment end for complete data
- Handle videos that start before dive begins (trim to dive start)
- Handle videos that extend beyond dive end (trim to dive end)

### Command-Line Interface

New options for `main.py`:

```
--match-video <path>         # Video file to match against (triggers segment mode)
--start <seconds>            # Manual override: video start time in seconds from dive start
--duration <seconds>         # Manual override: video duration in seconds (overrides existing flag behavior in segment mode)
```

**Behavior**:
- When `--match-video` is provided: automatic segment matching with timezone detection (±10 hours)
- When `--start` is provided: manual segment mode (requires `--duration`)
- Existing `--duration` flag: used for manual segment duration when `--start` provided
- Timezone offset detection tries ±10 hours automatically (not user-configurable)
- Error if segment is outside dive log bounds after offset correction

### Data Flow

```
1. Parse dive log → DiveSample[]
2. If --video-file provided:
   a. Extract video metadata → VideoMetadata
   b. Detect timezone offset → offset_hours
   c. Calculate segment bounds → (start_seconds, end_seconds)
   d. Filter dive samples → DiveSample[] (segment only)
3. Generate overlay from filtered samples
```

## Dependencies

**New Python dependencies**:
- None (uses existing opencv-python for video metadata)

**System dependencies**:
- None (no external tools required)

**New Python stdlib imports**:
- `datetime` (for timestamp handling)
- `os` (for file stat operations)

## Error Handling

New exception classes in `parser.py`:

Error messages should provide:
- Video start time (with timezone if available)
- Dive start and end times
- Tested timezone offsets
- Suggested manual override commands

## Testing Strategy

**Manual testing approach** (no automated tests currently):

1. Test with video files having valid metadata
2. Test with video files missing metadata (use file creation time)
3. Test timezone offsets: +1h, -1h, +5h, -5h
4. Test edge cases: video starts before dive, video ends after dive
5. Test manual overrides: `--video-start`, `--video-duration`, `--timezone-offset`
6. Test error cases: segment completely outside dive bounds

**Sample test data needed**:
- Sample video files with various metadata formats
- Dive logs with known start times
- Documentation of timezone offset scenarios

## Documentation Updates

**README.md additions**:
- New "Video Segment Matching" section
- Example commands for segment mode
- Explanation of timezone offset detection
- Troubleshooting guide for segment matching issues

**docs/ additions**:
- New `video-segment-matching.md` guide
- Detailed timezone offset examples
- OpenCV video metadata extraction details
- Manual override workflow

## Future Enhancements (Out of Scope)

- GPS coordinate matching between video and dive log
- Multiple video segments in single overlay batch
- Automatic video file discovery in directory
- Machine learning for better timezone detection
- Support for GoPro GPMF telemetry data
