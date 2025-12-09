"""Exception classes for video segment matching errors.

These exceptions provide detailed diagnostic information for troubleshooting
video segment matching issues, including timezone offset detection failures,
video metadata problems, and segment boundary issues.
"""

from datetime import datetime
from typing import Optional


class VideoSegmentError(Exception):
    """Base exception for video segment matching errors."""
    pass


class VideoMetadataError(VideoSegmentError):
    """Raised when video metadata cannot be extracted.

    Attributes:
        video_path: Path to the video file
        details: Additional error details
    """
    def __init__(self, video_path: str, details: str = ""):
        self.video_path = video_path
        self.details = details
        message = f"Cannot extract metadata from video: {video_path}"
        if details:
            message += f"\n   Details: {details}"
        super().__init__(message)


class VideoReadError(VideoSegmentError):
    """Raised when video file cannot be opened or read.

    Attributes:
        video_path: Path to the video file
        reason: Reason for read failure
    """
    def __init__(self, video_path: str, reason: str = ""):
        self.video_path = video_path
        self.reason = reason
        message = f"Cannot read video file: {video_path}"
        if reason:
            message += f"\n   Reason: {reason}"
        super().__init__(message)


class TimezoneOffsetError(VideoSegmentError):
    """Raised when timezone offset cannot be determined within range.

    Provides detailed diagnostics including tested offsets and manual override suggestions.

    Attributes:
        video_time: Video creation time in UTC
        dive_start: Dive start time in UTC
        dive_end: Dive end time in UTC
        max_offset: Maximum offset hours tested
        video_duration: Video duration in seconds
    """
    def __init__(
        self,
        video_time: datetime,
        dive_start: datetime,
        dive_end: datetime,
        max_offset: int = 10,
        video_duration: Optional[float] = None
    ):
        self.video_time = video_time
        self.dive_start = dive_start
        self.dive_end = dive_end
        self.max_offset = max_offset
        self.video_duration = video_duration

        dive_duration = (dive_end - dive_start).total_seconds()

        message = (
            f"Cannot detect timezone offset between video and dive log\n\n"
            f"Video Information:\n"
            f"   Creation time: {video_time}\n"
        )

        if video_duration:
            message += f"   Duration: {video_duration:.1f}s\n"

        message += (
            f"\nDive Information:\n"
            f"   Start time: {dive_start}\n"
            f"   End time: {dive_end}\n"
            f"   Duration: {dive_duration:.0f}s\n"
            f"\nDiagnostics:\n"
            f"   Tested timezone offsets: ±{max_offset} hours\n"
            f"   No offset places video start within dive timeframe\n"
        )

        # Calculate time difference for suggestions
        time_diff = (video_time - dive_start).total_seconds() / 3600

        message += (
            f"\nPossible causes:\n"
            f"   - Video is from a different dive (time difference: {time_diff:+.1f} hours)\n"
            f"   - Timezone offset exceeds ±{max_offset} hours\n"
            f"   - Camera or dive computer clock is incorrect\n"
            f"\nManual override options:\n"
        )

        # Suggest manual start time based on time difference
        manual_start = int((video_time - dive_start).total_seconds())
        if manual_start < 0:
            message += f"   --start 0 --duration {int(video_duration) if video_duration else '<seconds>'}\n"
        else:
            message += f"   --start {manual_start} --duration {int(video_duration) if video_duration else '<seconds>'}\n"

        super().__init__(message)


class SegmentOutOfBoundsError(VideoSegmentError):
    """Raised when video segment falls outside dive log timeframe.

    Attributes:
        segment_start: Segment start in seconds from dive start
        segment_end: Segment end in seconds from dive start
        dive_duration: Total dive duration in seconds
    """
    def __init__(self, segment_start: int, segment_end: int, dive_duration: int):
        self.segment_start = segment_start
        self.segment_end = segment_end
        self.dive_duration = dive_duration

        message = (
            f"Video segment is outside dive log bounds\n\n"
            f"Segment:\n"
            f"   Start: {segment_start}s\n"
            f"   End: {segment_end}s\n"
            f"\nDive:\n"
            f"   Duration: {dive_duration}s\n"
            f"   Valid range: 0s to {dive_duration}s\n"
            f"\nPossible causes:\n"
        )

        if segment_start < 0:
            message += f"   - Segment starts {abs(segment_start)}s before dive begins\n"
        if segment_end > dive_duration:
            message += f"   - Segment ends {segment_end - dive_duration}s after dive ends\n"

        message += (
            f"\nSuggestions:\n"
            f"   - Check video file timestamp is correct\n"
            f"   - Verify dive log covers the correct dive\n"
            f"   - Try manual segment specification with --start and --duration\n"
        )

        super().__init__(message)


class EmptySegmentError(VideoSegmentError):
    """Raised when segment extraction results in no samples.

    Attributes:
        segment_start: Segment start in seconds from dive start
        segment_end: Segment end in seconds from dive start
        sample_count: Number of samples in original dive log
    """
    def __init__(self, segment_start: int, segment_end: int, sample_count: int):
        self.segment_start = segment_start
        self.segment_end = segment_end
        self.sample_count = sample_count

        message = (
            f"Segment extraction resulted in no samples\n\n"
            f"Segment:\n"
            f"   Start: {segment_start}s\n"
            f"   End: {segment_end}s\n"
            f"   Duration: {segment_end - segment_start}s\n"
            f"\nDive log:\n"
            f"   Total samples: {sample_count}\n"
            f"\nPossible causes:\n"
            f"   - Segment is in a gap between dive samples\n"
            f"   - Segment boundaries are incorrect\n"
            f"   - Dive log sampling rate is too low\n"
            f"\nSuggestions:\n"
            f"   - Verify segment times are within dive duration\n"
            f"   - Check dive log file contains sufficient samples\n"
        )

        super().__init__(message)
