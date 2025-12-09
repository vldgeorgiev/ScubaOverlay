# Video Segment Matching Guide

This guide explains how to generate overlay videos for specific segments of your dive that match your camera footage, rather than creating overlays for entire dives.

---

## Table of Contents

1. [Overview](#overview)
2. [How It Works](#how-it-works)
3. [Automatic Segment Matching](#automatic-segment-matching)
4. [Manual Segment Mode](#manual-segment-mode)
5. [Timezone Offset Detection](#timezone-offset-detection)
6. [Video Metadata Requirements](#video-metadata-requirements)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Usage](#advanced-usage)

---

## Overview

### Why Use Segment Matching?

Divers often record multiple short video clips during a single dive rather than one continuous recording. When compositing these clips with dive computer overlays, you need:

- **Time-accurate overlays** showing the correct dive time and depth for each clip
- **Automatic matching** to avoid manual calculations
- **Timezone handling** since cameras and dive computers may be set to different time zones

### Key Features

- ✅ **Automatic detection** of which dive segment matches your video
- ✅ **Timezone offset correction** (tries ±10 hours automatically)
- ✅ **Actual dive times** preserved (overlay shows real dive time, not reset to 0)
- ✅ **Multiple clips** from same dive handled independently
- ✅ **Manual override** when automatic detection isn't possible

---

## How It Works

### Architecture

```
Video File (footage.mp4)
    ↓
Extract Metadata (duration, creation time)
    ↓
Detect Timezone Offset (0, ±1h, ±2h, ... ±10h)
    ↓
Calculate Segment Bounds (start, end in dive time)
    ↓
Extract Matching Dive Samples
    ↓
Generate Overlay Video (with actual dive times)
```

### Key Concepts

**Video Creation Time**: The timestamp when the camera recorded the video. Extracted from:
1. **Preferred**: Video file metadata (encoded by camera)
2. **Fallback**: File system creation time (less reliable, changes when copying)

**Timezone Offset**: Hour difference between camera time and dive computer time.
- Example: Camera in EST (-5 UTC), dive computer in UTC → offset is -5 hours

**Segment Bounds**: The start and end times (in seconds from dive start) that match the video duration.

**Time Preservation**: Unlike full dive overlays, segment overlays show actual dive times (e.g., "10:42" means 10 minutes 42 seconds into the dive), not reset to "00:00".

---

## Automatic Segment Matching

### Basic Usage

```bash
scuba-overlay --template templates/perdix-ai-oc-tech.yaml \
  --log samples/dive446.ssrf \
  --match-video footage.mp4 \
  --output overlay.mp4
```

### What Happens

1. **Video Analysis**:
   ```
   🔍 Analyzing video: footage.mp4
      Video duration: 45.2s
      Creation time: 2025-12-07 14:33:38+00:00 (from video metadata)
   ```

2. **Timezone Detection**:
   ```
   🔍 Detecting timezone offset...
      Detected offset: +2 hours
   ```

3. **Segment Extraction**:
   ```
   🔍 Extracting dive segment...
      Segment start: 638s from dive start
      Segment end: 683s from dive start
      Extracted 10 samples
   ```

4. **Overlay Generation**:
   - Creates 45-second overlay video
   - Dive time starts at 10:38 (638 seconds)
   - Depth, pressure, etc. match exact dive conditions at that time

### Requirements

- Video file must exist and be readable by OpenCV/pymediainfo
- Dive log must cover the time when video was recorded
- Video start time must fall within dive duration (after timezone correction)

---

## Manual Segment Mode

### When to Use

- Video file has no metadata or incorrect timestamps
- Timezone offset exceeds ±10 hours
- You want precise control over segment boundaries
- Testing specific dive segments

### Basic Usage

```bash
scuba-overlay --template templates/perdix-ai-oc-tech.yaml \
  --log samples/dive446.ssrf \
  --start 600 \
  --duration 30 \
  --output overlay.mp4
```

**Parameters**:
- `--start`: Start time in seconds from dive start (e.g., 600 = 10 minutes into dive)
- `--duration`: Length of segment in seconds (e.g., 30 = 30-second clip)

### Example Workflow

1. **Find segment times** from your video editing timeline:
   - Note when your clip starts in the dive (e.g., 10:00 minutes)
   - Note clip duration (e.g., 0:45 seconds)

2. **Convert to seconds**:
   - Start: 10:00 × 60 = 600 seconds
   - Duration: 45 seconds

3. **Generate overlay**:
   ```bash
   scuba-overlay --template template.yaml --log dive.ssrf \
     --start 600 --duration 45 --output overlay.mp4
   ```

---

## Timezone Offset Detection

### How Detection Works

The tool tries timezone offsets in this order until one places the video start time within the dive:

```
0h → +1h → -1h → +2h → -2h → +3h → -3h → ... → +10h → -10h
```

### Example Scenarios

**Scenario 1: Camera and dive computer in same timezone**
- Offset: 0 hours (detected immediately)

**Scenario 2: Camera in EST, dive computer in UTC**
- EST is UTC-5
- Offset: -5 hours (detected on 9th attempt)

**Scenario 3: Camera ahead by 2 hours**
- Offset: +2 hours (detected on 3rd attempt)

### Detection Failure

If no offset within ±10 hours works:

```
❌ Cannot detect timezone offset between video and dive log

Video Information:
   Creation time: 2025-12-01 12:00:00+00:00
   Duration: 120.0s

Dive Information:
   Start time: 2025-12-07 12:00:00+00:00
   End time: 2025-12-07 13:00:00+00:00
   Duration: 3600s

Diagnostics:
   Tested timezone offsets: ±10 hours
   No offset places video start within dive timeframe

Possible causes:
   - Video is from a different dive (time difference: -144.0 hours)
   - Timezone offset exceeds ±10 hours
   - Camera or dive computer clock is incorrect

Manual override options:
   --start 0 --duration 120
```

**Solutions**:
- Use manual mode with `--start` and `--duration`
- Check if video and dive log are from the same dive
- Verify camera and dive computer clocks are reasonably accurate

---

## Video Metadata Requirements

### Supported Formats

Depends on OpenCV/pymediainfo support on your system. Commonly supported:

- **MP4** (H.264, H.265)
- **AVI** (various codecs)
- **MOV** (QuickTime)
- **MKV** (Matroska)
- **WEBM**

### Metadata Extraction

**Method 1: Video Metadata (Preferred)**
- Uses `pymediainfo` library
- Reads `encoded_date`, `tagged_date`, or `recorded_date` from video file
- Most accurate (preserves original camera timestamp)

**Method 2: File System (Fallback)**
- Uses file creation time from OS
- Less reliable (changes when copying, moving, or editing files)
- Platform-specific:
  - macOS: `st_birthtime`
  - Windows/Linux: `st_ctime`

### Best Practices

✅ **Do**:
- Use original video files directly from camera
- Keep video files with original timestamps
- Set camera clock before diving

❌ **Avoid**:
- Editing videos before using segment matching (may strip metadata)
- Copying videos through cloud services (may change file timestamps)
- Using significantly incorrect camera clocks (>10 hours off)

---

## Troubleshooting

### Error: "Cannot read video file"

**Symptoms**:
```
❌ Video error: Cannot read video file: footage.mp4
   Reason: File does not exist. Check the file path.
```

**Solutions**:
1. Verify file path is correct
2. Check file permissions
3. Try absolute path instead of relative
4. Ensure video codec is supported by OpenCV

---

### Error: "Could not detect timezone offset"

**Symptoms**:
```
❌ Cannot detect timezone offset between video and dive log
```

**Causes**:
- Video from different dive than log
- Timezone offset > 10 hours
- Camera or dive computer clock significantly wrong

**Solutions**:

1. **Verify same dive**: Check dive date and approximate times match

2. **Use manual mode**:
   ```bash
   scuba-overlay --template template.yaml --log dive.ssrf \
     --start 600 --duration 45 --output overlay.mp4
   ```

3. **Check clocks**: Ensure camera and dive computer times are within ±10 hours

---

### Error: "Video segment is outside dive log bounds"

**Symptoms**:
```
❌ Video segment is outside dive log bounds

Segment:
   Start: 10000s
   End: 10045s

Dive:
   Duration: 3645s
   Valid range: 0s to 3645s
```

**Causes**:
- `--start` value too large (beyond dive end)
- Video timestamp doesn't match dive log time
- Wrong dive log file

**Solutions**:

1. **Check segment bounds**:
   - Dive is 3645s (60 minutes, 45 seconds)
   - Start time must be < 3645s

2. **Verify dive log**: Ensure log file matches the dive when video was recorded

3. **Adjust start time**:
   ```bash
   scuba-overlay --template template.yaml --log dive.ssrf \
     --start 600 --duration 45 --output overlay.mp4
   ```

---

### Warning: "Segment extends beyond dive end"

**Symptoms**:
```
⚠️  Warning: Segment extends beyond dive end (3670s > 3645s)
   Segment will be trimmed to dive duration
```

**Cause**: Video recording continued after dive computer stopped logging (e.g., at surface)

**Behavior**: 
- Not an error, just a warning
- Overlay will be generated for the portion that overlaps with dive
- Segment automatically trimmed to dive duration

**Action**: No action needed unless this is unexpected

---

### Error: "Segment extraction resulted in no samples"

**Symptoms**:
```
❌ Segment extraction resulted in no samples
```

**Causes**:
- Segment falls in gap between dive samples
- Very short segment with low sample rate dive log
- Incorrect segment boundaries

**Solutions**:

1. **Check dive log sample rate**: Ensure log has sufficient samples
2. **Verify segment times**: Make sure start/end times are valid
3. **Try longer segment**: Increase duration to include more samples

---

## Advanced Usage

### Multiple Clips from Same Dive

Process each clip independently:

```bash
# Clip 1 (early in dive)
scuba-overlay --template template.yaml --log dive.ssrf \
  --match-video clip1.mp4 --output overlay1.mp4

# Clip 2 (middle of dive)
scuba-overlay --template template.yaml --log dive.ssrf \
  --match-video clip2.mp4 --output overlay2.mp4

# Clip 3 (end of dive)
scuba-overlay --template template.yaml --log dive.ssrf \
  --match-video clip3.mp4 --output overlay3.mp4
```

Each overlay will show correct dive times for its respective clip.

---

### Batch Processing

Use shell scripting for multiple videos:

**Bash/macOS/Linux**:
```bash
#!/bin/bash
for video in footage/*.mp4; do
  output="overlays/$(basename "$video" .mp4)_overlay.mp4"
  scuba-overlay --template template.yaml \
    --log dive.ssrf \
    --match-video "$video" \
    --output "$output"
done
```

**PowerShell/Windows**:
```powershell
Get-ChildItem footage/*.mp4 | ForEach-Object {
  $output = "overlays/$($_.BaseName)_overlay.mp4"
  scuba-overlay --template template.yaml `
    --log dive.ssrf `
    --match-video $_.FullName `
    --output $output
}
```

---

### Testing Segment Extraction

Preview segment without generating video:

```bash
# Add --test-template flag (not yet implemented)
# For now, generate short video to verify segment

scuba-overlay --template template.yaml --log dive.ssrf \
  --start 600 --duration 5 --fps 1 --output test.mp4
```

Quick check creates 5-second overlay at 1 fps (only 5 frames).

---

### Debugging

Add verbose output by running with Python directly:

```bash
python -u src/main.py --template template.yaml \
  --log dive.ssrf \
  --match-video footage.mp4 \
  --output overlay.mp4 2>&1 | tee segment-debug.log
```

This captures all output including:
- Video metadata extraction
- Timezone offset detection attempts
- Segment boundary calculations
- Sample extraction details

---

## Summary

**Automatic Mode** - When video has good metadata:
```bash
scuba-overlay --template template.yaml --log dive.ssrf \
  --match-video footage.mp4 --output overlay.mp4
```

**Manual Mode** - When you know exact times:
```bash
scuba-overlay --template template.yaml --log dive.ssrf \
  --start 600 --duration 45 --output overlay.mp4
```

**Key Points**:
- Original video files give best results
- Timezone detection is automatic (±10 hours)
- Actual dive times are preserved in overlay
- Manual mode always works when automatic fails
- Multiple clips from same dive are handled independently

For additional help, see the main [README](../Readme.md) or open an issue on GitHub.
