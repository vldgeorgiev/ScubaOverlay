# Implementation Tasks

## Phase 1: Video Metadata Extraction (Foundation)

### Task 1.1: Create video_metadata.py module

**Description**: Create new module with OpenCV wrapper functions for video metadata extraction.

**Deliverable**: `src/video_metadata.py` with module docstring and imports

**Validation**: File exists and imports successfully

**Dependencies**: None

---

### Task 1.2: Implement OpenCV video duration extraction

**Description**: Write function to use cv2.VideoCapture to extract video duration (frame count / FPS).

**Deliverable**: `get_video_duration(video_path: str) -> float` function

**Validation**: Successfully extracts duration from MP4 test video with known length

**Dependencies**: Task 1.1

**Implementation notes**:
- Use `cv2.VideoCapture(video_path)` to open video
- Get frame count: `cap.get(cv2.CAP_PROP_FRAME_COUNT)`
- Get FPS: `cap.get(cv2.CAP_PROP_FPS)`
- Calculate duration: `frame_count / fps`
- Handle errors gracefully (file not found, unsupported format)

---

### Task 1.3: Implement file creation time fallback

**Description**: Add fallback to file system creation time when video metadata unavailable.

**Deliverable**: `get_file_creation_time(file_path: str) -> datetime` function

**Validation**: Correctly retrieves file creation time on macOS, Windows, Linux

**Dependencies**: Task 1.1

**Implementation notes**:
- Use `os.stat()` with platform-specific birth time handling
- macOS: `st_birthtime`, Linux: `st_ctime`, Windows: `st_ctime`
- Return datetime object in UTC

---

### Task 1.4: Add VideoMetadata dataclass

**Description**: Create dataclass to hold video metadata (start time, duration, source).

**Deliverable**: `VideoMetadata` dataclass with type hints

**Validation**: Can instantiate and access fields

**Dependencies**: Task 1.1

**Implementation notes**:
```python
@dataclass
class VideoMetadata:
    start_time: datetime  # UTC
    duration: float  # seconds
    source: str  # "metadata" or "file_creation"
```

---

### Task 1.5: Add video metadata exception classes

**Description**: Add exception classes for video metadata errors.

**Deliverable**: `VideoMetadataError`, `VideoReadError` in parser.py

**Validation**: Can raise and catch exceptions

**Dependencies**: None (add to existing parser.py)

---

## Phase 2: Timezone Offset Detection (Core Algorithm)

### Task 2.1: Implement timezone offset iterator

**Description**: Function to generate timezone offsets in order: 0, +1, -1, +2, -2, ..., +10, -10.

**Deliverable**: `generate_timezone_offsets() -> Iterator[int]` function (fixed at 10 hours)

**Validation**: Generates correct sequence up to ±10 hours

**Dependencies**: None (add to video_metadata.py or parser.py)

---

### Task 2.2: Add dive time boundary extraction

**Description**: Function to extract dive start time and duration from dive samples.

**Deliverable**: `get_dive_time_bounds(dive_samples: List[DiveSample]) -> tuple[datetime, datetime]`

**Validation**: Returns correct start and end times for test dive log

**Dependencies**: None (add to parser.py)

**Implementation notes**:
- Need to add `dive_start_time: datetime` field to dive log metadata
- May require parser changes to extract dive date/time from XML

---

### Task 2.3: Implement timezone offset detection algorithm

**Description**: Core algorithm to find timezone offset that places video in dive timeframe (±10 hours).

**Deliverable**: `detect_timezone_offset(video_time: datetime, dive_start: datetime, dive_end: datetime) -> Optional[int]`

**Validation**: Returns correct offset for known test cases (+1h, -2h, +8h, no offset)

**Dependencies**: Tasks 2.1, 2.2

**Implementation notes**:
- Try each offset from generator
- Check if `video_time + offset` falls within `[dive_start, dive_end]`
- Return first matching offset
- Return None if no offset works

---

### Task 2.4: Add timezone offset exception classes

**Description**: Exception classes for timezone offset errors.

**Deliverable**: `TimezoneOffsetError`, `SegmentOutOfBoundsError` in parser.py

**Validation**: Can raise and catch exceptions

**Dependencies**: None (add to parser.py)

---

## Phase 3: Dive Log Segmentation (Core Feature)

### Task 3.1: Parse dive start timestamp from logs

**Description**: Extend parsers to extract dive start date/time from Subsurface and Shearwater logs.

**Deliverable**: Updated `SubsurfaceParser` and `ShearwaterParser` with start time extraction

**Validation**: Parsers return dive start time for sample logs

**Dependencies**: None (modify existing parser.py)

**Implementation notes**:
- Subsurface: `<dive date="..." time="...">`
- Shearwater: `<Dive>` element date attributes
- Store as datetime in UTC

---

### Task 3.2: Update parse_dive_log return type

**Description**: Return both dive samples and dive metadata (start time, end time).

**Deliverable**: `DiveData` dataclass with samples and metadata

**Validation**: Existing tests still pass with new return type

**Dependencies**: Task 3.1

**Implementation notes**:
```python
@dataclass
class DiveData:
    samples: List[DiveSample]
    start_time: datetime
    end_time: datetime
```

---

### Task 3.3: Implement dive log segment extraction

**Description**: Filter dive samples to match video time segment with boundary samples.

**Deliverable**: `extract_dive_segment(dive_data: DiveData, segment_start: int, segment_end: int) -> List[DiveSample]`

**Validation**: Returns correct samples for mid-dive segment, handles edge cases

**Dependencies**: Task 3.2

**Implementation notes**:
- Include sample before segment_start for interpolation
- Include sample after segment_end for interpolation
- Handle segment_start < 0 (trim to 0)
- Handle segment_end > dive duration (trim to dive end)

---

## Phase 4: CLI Integration (User Interface)

### Task 4.1: Add video segment command-line arguments

**Description**: Add `--match-video`, `--start` to argparse. Reuse existing `--duration` for segment mode.

**Deliverable**: Updated argument parser in main.py

**Validation**: `--help` shows new options with descriptions

**Dependencies**: None

---

### Task 4.2: Implement automatic segment mode logic

**Description**: When `--match-video` provided, extract metadata, detect offset (±10h), extract segment.

**Deliverable**: Segment mode workflow in main.py

**Validation**: Generates correct overlay for video clip automatically

**Dependencies**: Tasks 1.2-1.4, 2.3, 3.3

**Implementation notes**:
- Extract video metadata
- Detect timezone offset
- Calculate segment start/end in dive timeline
- Extract segment samples
- Pass to overlay generation

---

### Task 4.3: Implement manual override handling

**Description**: Support `--start` and `--duration` for manual segment specification (in seconds).

**Deliverable**: Manual override logic in main.py

**Validation**: Manual overrides bypass automatic detection

**Dependencies**: Task 4.1

**Implementation notes**:
- `--start` expects seconds from dive start (integer)
- Require `--duration` when using `--start`
- Skip video file processing entirely when using manual mode
- Log when manual mode is used

---

### Task 4.5: Add segment mode validation

**Description**: Validate that segment (from video or manual) falls within dive bounds.

**Deliverable**: Validation logic with clear error messages

**Validation**: Rejects segments outside dive, provides diagnostic output

**Dependencies**: Tasks 2.3, 3.3, 4.2, 4.3

---

## Phase 5: Error Handling and Diagnostics

### Task 5.1: Implement detailed timezone offset error messages

**Description**: When offset detection fails (tried ±10 hours), show video time, dive times, tested offsets.

**Deliverable**: Formatted error message with diagnostic details and manual override suggestion

**Validation**: Error message includes all diagnostic information

**Dependencies**: Task 2.3

---

### Task 5.2: Implement video read error diagnostics

**Description**: When OpenCV cannot read video file, show clear error and suggestions.

**Deliverable**: Formatted error message for video read failures

**Validation**: Error message guides user to check file format and try manual override

**Dependencies**: Task 1.2

---

### Task 5.3: Add segment extraction warnings

**Description**: Warn when video extends before dive start or after dive end.

**Deliverable**: Warning messages for boundary cases

**Validation**: Warnings appear for edge cases but overlay still generates

**Dependencies**: Task 3.3

---

## Phase 6: Documentation (User Enablement)

### Task 6.1: Add Video Segment Matching section to README

**Description**: Write README section with overview, example commands, basic usage.

**Deliverable**: Updated README.md with new section after "Command Reference"

**Validation**: Section includes automatic and manual examples

**Dependencies**: Phase 4 complete

**Content outline**:
- Feature overview
- Basic automatic usage example
- Manual override example
- Timezone offset explanation
- Link to detailed guide

---

### Task 6.2: Create video-segment-matching.md guide

**Description**: Comprehensive guide in docs/ with detailed explanations and troubleshooting.

**Deliverable**: `docs/video-segment-matching.md` file

**Validation**: Guide covers all scenarios from spec

**Dependencies**: Phase 4 complete

**Content outline**:
- How it works (architecture overview)
- Video metadata requirements
- Timezone offset detection explained
- Manual override workflows
- Troubleshooting common issues
- Supported video formats and OpenCV compatibility
- Example commands for various scenarios

---

### Task 6.3: Update command reference in README

**Description**: Add new command-line options to Command Reference section.

**Deliverable**: Updated README.md command reference

**Validation**: All new options documented with examples

**Dependencies**: Task 4.1

---

### Task 6.4: Document supported video formats

**Description**: Document which video formats are supported by OpenCV for segment matching.

**Deliverable**: Updated README.md with supported formats list

**Validation**: Supported formats clearly documented

**Dependencies**: None

---

## Phase 7: Testing and Validation

### Task 7.1: Create test video files

**Description**: Generate or find test video files in common formats (MP4, AVI, MOV).

**Deliverable**: Test videos in sample-logs/ with documented durations and creation times

**Validation**: Videos can be read by OpenCV and have known timestamps

**Dependencies**: None

**Test cases needed**:
- MP4 video with known duration
- AVI video with known duration
- Videos at various timezone offsets (+1h, -2h, +5h)

---

### Task 7.2: Manual end-to-end testing

**Description**: Test full workflow with sample dive logs and test videos.

**Deliverable**: Test results document or checklist

**Validation**: All scenarios from spec work correctly

**Dependencies**: All implementation phases complete

**Test scenarios**:
- Automatic matching with no offset
- Automatic matching with +1h offset
- Automatic matching with -2h offset
- Automatic matching with +8h offset
- Manual segment with --start and --duration
- Video before dive start (boundary case)
- Video after dive end (boundary case)
- Video completely outside dive (error case)
- Unsupported video format (error case)
- Invalid/corrupted video file (error case)

---

### Task 7.3: Documentation review and validation

**Description**: Review all documentation for accuracy and completeness.

**Deliverable**: Documentation validated against implementation

**Validation**: No discrepancies between docs and implementation

**Dependencies**: Phase 6 complete

---

## Task Dependencies Summary

**Can parallelize**:
- Phase 1 and Phase 2 are mostly independent
- Documentation (Phase 6) can start once CLI is designed (Phase 4)

**Sequential dependencies**:
- Phase 3 depends on Phase 2 (need offset detection for segmentation)
- Phase 4 depends on Phases 1-3 (CLI integrates all components)
- Phase 5 depends on Phases 2-4 (error handling for implemented features)
- Phase 7 depends on all phases (testing complete implementation)

**Critical path**: Tasks 1.2 → 2.3 → 3.3 → 4.2 → 7.2

**Estimated effort**: 15-20 tasks, approximately 2-3 days for experienced developer
