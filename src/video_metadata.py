"""Video metadata extraction for dive log segment matching.

This module provides functions to extract video duration and creation time
from video files using OpenCV (cv2) and file system metadata. Used to match
video clips to specific segments of dive logs with automatic timezone offset detection.
"""

import cv2
import os
import platform
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from typing import Optional, Iterator
from video_segment_errors import VideoReadError, VideoMetadataError

try:
    from pymediainfo import MediaInfo
    PYMEDIAINFO_AVAILABLE = True
except ImportError:
    PYMEDIAINFO_AVAILABLE = False


@dataclass
class VideoMetadata:
    """Video file metadata for segment matching.

    Attributes:
        start_time: Video creation time in UTC
        duration: Video duration in seconds
        source: Source of metadata ("file_creation")
    """
    start_time: datetime  # UTC
    duration: float  # seconds
    source: str  # "file_creation"


def generate_timezone_offsets() -> Iterator[int]:
    """Generate timezone offsets in order: 0, +1, -1, +2, -2, ..., +10, -10.

    Yields:
        Integer hour offsets to try for timezone matching
    """
    yield 0
    for i in range(1, 11):
        yield i
        yield -i


def detect_timezone_offset(
    video_time: datetime,
    dive_start: datetime,
    dive_end: datetime
) -> Optional[int]:
    """Detect timezone offset that places video within dive timeframe.

    Args:
        video_time: Video creation time (UTC)
        dive_start: Dive start time (UTC)
        dive_end: Dive end time (UTC)

    Returns:
        Hour offset if found, None if no offset within ±10 hours works
    """
    for offset_hours in generate_timezone_offsets():
        adjusted_time = video_time + timedelta(hours=offset_hours)

        if dive_start <= adjusted_time <= dive_end:
            return offset_hours

    return None


def get_video_duration(video_path: str) -> float:
    """Extract video duration using OpenCV.

    Args:
        video_path: Path to video file

    Returns:
        Video duration in seconds

    Raises:
        VideoReadError: If video cannot be opened or duration cannot be determined
    """
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise VideoReadError(video_path, "OpenCV cannot open the video file. Check file format and codec support.")

    try:
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        fps = cap.get(cv2.CAP_PROP_FPS)

        if fps <= 0 or frame_count < 0:
            raise VideoReadError(
                video_path,
                f"Invalid video properties detected (fps={fps:.2f}, frames={frame_count:.0f}). "
                f"Video file may be corrupted or have an unsupported format."
            )

        duration = frame_count / fps
        return duration
    finally:
        cap.release()


def get_video_creation_time_from_metadata(video_path: str) -> Optional[datetime]:
    """Extract video creation time from video metadata tags.

    Tries to extract creation_time from video file metadata using pymediainfo.
    Falls back to None if metadata is not available or pymediainfo is not installed.

    Args:
        video_path: Path to video file

    Returns:
        Creation time as datetime in UTC, or None if not available
    """
    if not PYMEDIAINFO_AVAILABLE:
        return None

    try:
        media_info = MediaInfo.parse(video_path)

        # Try to find creation time in general track
        for track in media_info.tracks:
            if track.track_type == "General":
                # Try various attribute names
                creation_time_str = None
                for attr in ['encoded_date', 'tagged_date', 'recorded_date', 'file_creation_date']:
                    value = getattr(track, attr, None)
                    if value:
                        creation_time_str = value
                        break

                if not creation_time_str:
                    continue

                # Parse the timestamp
                try:
                    # pymediainfo often returns timestamps like "2025-12-07 14:33:38 UTC"
                    # or ISO format "2025-12-07T14:33:38Z"
                    time_str = creation_time_str

                    # Remove "UTC " prefix if present
                    if time_str.startswith("UTC "):
                        time_str = time_str[4:]

                    # Remove " UTC" suffix if present
                    if time_str.endswith(" UTC"):
                        time_str = time_str[:-4]

                    # Try ISO 8601 format first
                    if 'T' in time_str:
                        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                        return dt.astimezone(timezone.utc)

                    # Try space-separated format
                    try:
                        dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                        return dt.replace(tzinfo=timezone.utc)
                    except ValueError:
                        pass

                    # Try other common formats
                    for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y/%m/%d %H:%M:%S']:
                        try:
                            dt = datetime.strptime(time_str, fmt)
                            return dt.replace(tzinfo=timezone.utc)
                        except ValueError:
                            continue

                except (ValueError, AttributeError):
                    continue

        return None

    except Exception:
        # pymediainfo failed
        return None


def get_file_creation_time(file_path: str) -> datetime:
    """Get file creation time from file system.

    Args:
        file_path: Path to file

    Returns:
        File creation time as datetime in UTC
    """
    stat_info = os.stat(file_path)

    # Platform-specific birth time handling
    system = platform.system()
    if system == "Darwin":  # macOS
        timestamp = stat_info.st_birthtime
    else:  # Windows, Linux
        timestamp = stat_info.st_ctime

    # Convert to UTC datetime
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt


def extract_video_metadata(video_path: str) -> VideoMetadata:
    """Extract complete video metadata for segment matching.

    Tries to extract creation time from video metadata first,
    then falls back to file system creation time.

    Args:
        video_path: Path to video file

    Returns:
        VideoMetadata object with duration and creation time

    Raises:
        VideoReadError: If video file cannot be opened or read
        VideoMetadataError: If metadata extraction fails completely
    """
    if not os.path.exists(video_path):
        raise VideoReadError(video_path, "File does not exist. Check the file path.")

    try:
        duration = get_video_duration(video_path)
    except VideoReadError:
        raise
    except Exception as e:
        raise VideoReadError(video_path, f"Unexpected error reading video: {e}")

    # Try video metadata first
    creation_time = get_video_creation_time_from_metadata(video_path)
    source = "video_metadata"

    # Fallback to file system
    if creation_time is None:
        try:
            creation_time = get_file_creation_time(video_path)
            source = "file_creation"
        except Exception as e:
            raise VideoMetadataError(
                video_path,
                f"Cannot extract creation time from video metadata or file system: {e}"
            )

    return VideoMetadata(
        start_time=creation_time,
        duration=duration,
        source=source
    )