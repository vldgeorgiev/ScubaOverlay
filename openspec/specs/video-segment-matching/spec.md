# video-segment-matching Specification

## Purpose
TBD - created by archiving change add-video-segment-matching. Update Purpose after archive.
## Requirements
### Requirement: Video Metadata Extraction

The system SHALL extract start time and duration from video files using OpenCV (cv2.VideoCapture).

#### Scenario: Extract metadata from video file

- **GIVEN** a video file accessible to OpenCV
- **WHEN** user provides `--match-video path/to/video.mp4`
- **THEN** system extracts video duration using cv2.VideoCapture
- **AND** system extracts file creation time from file system
- **AND** both values are used for segment matching

#### Scenario: Handle video file OpenCV cannot read

- **GIVEN** a video file that OpenCV cannot open
- **WHEN** user provides `--match-video path/to/corrupted.mp4`
- **THEN** system reports clear error message
- **AND** error indicates video file cannot be read
- **AND** program exits with non-zero status

#### Scenario: Report error when video file not found

- **GIVEN** a non-existent video file path
- **WHEN** user provides `--match-video path/to/nonexistent.mp4`
- **THEN** system reports clear error message
- **AND** error includes the attempted file path
- **AND** program exits with non-zero status

### Requirement: Timezone Offset Detection

The system SHALL automatically detect and correct timezone offsets between camera and dive computer timestamps.

#### Scenario: Video matches dive log with no offset

- **GIVEN** a video with start time within dive log timeframe
- **WHEN** system performs segment matching
- **THEN** system uses zero timezone offset
- **AND** segment is extracted without time adjustment
- **AND** no offset warning is logged

#### Scenario: Detect +1 hour timezone offset

- **GIVEN** a video with start time 1 hour after dive start
- **AND** video start time (minus 1 hour) falls within dive log timeframe
- **WHEN** system performs timezone detection
- **THEN** system detects +1 hour offset
- **AND** system logs detected offset
- **AND** video start time is adjusted by -1 hour for matching

#### Scenario: Detect -2 hour timezone offset

- **GIVEN** a video with start time 2 hours before dive start
- **AND** video start time (plus 2 hours) falls within dive log timeframe
- **WHEN** system performs timezone detection
- **THEN** system detects -2 hour offset
- **AND** system adjusts video start time by +2 hours
- **AND** segment extraction uses corrected time

#### Scenario: Try offsets up to 10 hours

- **GIVEN** video start time requires 8 hour offset to match dive
- **WHEN** system performs timezone detection
- **THEN** system tries offsets in order: 0, +1, -1, +2, -2, ..., +10, -10
- **AND** system finds 8 hour offset
- **AND** segment matching proceeds with detected offset

#### Scenario: Report error when no offset matches

- **GIVEN** a video with start time more than 10 hours from dive
- **WHEN** system tries all offsets up to ±10 hours
- **THEN** system reports clear error message
- **AND** error includes video start time
- **AND** error includes dive log time range
- **AND** error suggests manual override with --start option
- **AND** program exits with non-zero status

#### Scenario: Choose smallest absolute offset when multiple match

- **GIVEN** a video that could match with both +1h and +3h offsets
- **WHEN** system performs timezone detection
- **THEN** system selects +1 hour offset
- **AND** uses smallest absolute offset for matching

### Requirement: Dive Log Segmentation

The system SHALL extract and process only the portion of dive log samples that match the video time segment.

#### Scenario: Extract mid-dive segment

- **GIVEN** a dive log from 0 to 3600 seconds
- **AND** a video segment from 900 to 1200 seconds (15-20 minutes)
- **WHEN** system performs segment extraction
- **THEN** overlay includes only samples from 900-1200 seconds
- **AND** overlay duration matches video duration (300 seconds)
- **AND** overlay starts with depth/data at 900 seconds into dive

#### Scenario: Include samples before and after segment for interpolation

- **GIVEN** a video segment from 900 to 1200 seconds
- **AND** dive samples at 890, 900, 910, ..., 1190, 1200, 1210 seconds
- **WHEN** system extracts segment samples
- **THEN** sample at 890 seconds is included (before segment)
- **AND** sample at 1210 seconds is included (after segment)
- **AND** smooth interpolation is maintained at segment boundaries

#### Scenario: Handle video starting before dive begins

- **GIVEN** a dive log starting at time T
- **AND** a video starting at time T-30 seconds (before dive start)
- **WHEN** system performs segment extraction
- **THEN** segment is trimmed to dive start time T
- **AND** warning is logged about pre-dive video time
- **AND** overlay starts at dive time 0

#### Scenario: Handle video extending beyond dive end

- **GIVEN** a dive log ending at 3600 seconds
- **AND** a video extending to 3700 seconds (beyond dive end)
- **WHEN** system performs segment extraction
- **THEN** segment is trimmed to dive end time 3600
- **AND** warning is logged about post-dive video time
- **AND** overlay ends at final dive sample

#### Scenario: Reject video segment completely outside dive bounds

- **GIVEN** a dive log from 0 to 3600 seconds
- **AND** a video segment from 4000 to 4300 seconds (after dive ends)
- **WHEN** system performs segment extraction with all timezone offsets
- **THEN** system reports error that segment is outside dive bounds
- **AND** error includes video time range and dive time range
- **AND** program exits with non-zero status

### Requirement: Manual Override Options

The system SHALL support manual specification of segment timing when automatic detection fails.

#### Scenario: Manual segment start time override

- **GIVEN** automatic matching fails or is incorrect
- **WHEN** user provides `--start 300`
- **AND** user provides `--duration 180`
- **THEN** system uses manual start time (300 seconds from dive start)
- **AND** system skips automatic video matching and timezone detection
- **AND** segment extraction uses manual timing

#### Scenario: Require duration with manual start time

- **GIVEN** no video file provided for automatic matching
- **WHEN** user provides `--start 300` without `--duration`
- **THEN** system reports error requiring --duration
- **AND** program exits with non-zero status

#### Scenario: Manual overrides work without video file

- **GIVEN** user wants to extract specific segment without video file
- **WHEN** user provides `--start 600` and `--duration 120`
- **THEN** system extracts segment from 600-720 seconds of dive
- **AND** no video file is required
- **AND** no timezone detection is performed

### Requirement: Command-Line Interface

The system SHALL provide intuitive command-line options for video segment matching.

#### Scenario: Help text includes video segment options

- **GIVEN** scuba-overlay command is available
- **WHEN** user runs `scuba-overlay --help`
- **THEN** help text includes `--match-video` option description
- **AND** help text includes `--start` option description
- **AND** help text includes updated `--duration` option description for segment mode

#### Scenario: Automatic segment matching with video file

- **GIVEN** a dive log and matching video file
- **WHEN** user runs `scuba-overlay --log dive.ssrf --template template.yaml --match-video clip.mp4 --output overlay.mp4`
- **THEN** system automatically extracts video metadata
- **AND** system automatically detects timezone offset (trying ±10 hours)
- **AND** system generates overlay for video segment only
- **AND** output video duration matches input video duration

#### Scenario: Duration flag used for manual segment mode

- **GIVEN** `--start` is provided for manual segment mode
- **WHEN** user provides `--duration 180`
- **THEN** system uses duration value for segment length
- **AND** segment is extracted from start to start+duration
- **AND** no video file metadata is used

### Requirement: Error Messages and Diagnostics

The system SHALL provide detailed diagnostic information when segment matching fails.

#### Scenario: Timezone detection failure diagnostics

- **GIVEN** video segment cannot match dive log with any offset
- **WHEN** timezone detection fails
- **THEN** error message includes video start time with timezone
- **AND** error message includes dive start and end times
- **AND** error message lists all tested timezone offsets
- **AND** error message shows calculated time after each offset
- **AND** error message suggests manual override commands with examples

#### Scenario: Video file read failure diagnostics

- **GIVEN** OpenCV fails to open video file
- **WHEN** video metadata extraction is attempted
- **THEN** error message indicates video cannot be read
- **AND** error message includes the file path
- **AND** error message suggests checking file format and corruption
- **AND** error message suggests manual override with --start and --duration

### Requirement: Documentation

The system SHALL provide comprehensive documentation for video segment matching feature.

#### Scenario: README includes video segment matching section

- **GIVEN** README.md file
- **WHEN** user reads documentation
- **THEN** README includes "Video Segment Matching" section
- **AND** section explains purpose of feature
- **AND** section provides example commands
- **AND** section explains timezone offset detection
- **AND** section documents manual override options

#### Scenario: Detailed guide for video segment matching

- **GIVEN** docs/video-segment-matching.md file exists
- **WHEN** user reads guide
- **THEN** guide explains video metadata extraction using OpenCV
- **AND** guide provides timezone offset examples with diagrams
- **AND** guide documents supported video formats
- **AND** guide includes troubleshooting section
- **AND** guide shows manual override workflow

#### Scenario: Example commands in documentation

- **GIVEN** video segment matching documentation
- **WHEN** user looks for usage examples
- **THEN** documentation includes automatic matching example
- **AND** documentation includes manual start time example
- **AND** documentation includes manual offset example
- **AND** documentation includes troubleshooting examples
- **AND** all examples use realistic file paths and timestamps

