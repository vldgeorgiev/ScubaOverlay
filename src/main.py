import argparse
from parser import parse_dive_log, DiveLogError, extract_dive_segment
from template import load_template, TemplateError
from overlay import generate_overlay_video, generate_test_template_image
from profile_graph import generate_profile_overlay_video, generate_test_profile_image
from video_metadata import extract_video_metadata, detect_timezone_offset
from video_segment_errors import (
    VideoSegmentError, VideoReadError, VideoMetadataError,
    TimezoneOffsetError, SegmentOutOfBoundsError, EmptySegmentError
)
from datetime import timedelta

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", required=False, help="YAML layout template file for computer overlay")
    parser.add_argument("--profile-template", required=False, help="YAML template file for profile graph overlay")
    parser.add_argument("--log", required=False, help="Dive log file (e.g. .ssrf)")
    parser.add_argument("--output", required=False, default="output_overlay.mp4", help="Output overlay video file (e.g. overlay.mp4)")
    parser.add_argument("--duration", type=int, default=None, help="Duration in seconds. For full dive if not in segment mode, or segment duration with --start")
    parser.add_argument("--fps", type=int, default=10, help="Frames per second for output video")
    parser.add_argument("--test-template", action="store_true", help="Generate a single PNG image with dummy data and exit")
    parser.add_argument("--units", choices=["metric", "imperial"], help="Override all display units (metric or imperial)")
    parser.add_argument("--match-video", help="Video file to match for automatic segment extraction")
    parser.add_argument("--start", type=int, help="Manual segment start time in seconds from dive start")
    args = parser.parse_args()

    # Validate template arguments
    if not args.template and not args.profile_template:
        parser.error("Either --template or --profile-template is required")

    if args.template and args.profile_template:
        parser.error("Cannot use --template and --profile-template together. Generate overlays separately and composite in your video editor.")

    if not args.test_template and not args.log:
        parser.error("--log is required unless --test-template is used")

    if args.start is not None and args.duration is None:
        parser.error("--duration is required when using --start")

    units_override = None
    if args.units:
        if args.units == "metric":
            units_override = {"depth": "m", "pressure": "bar", "temperature": "C"}
        else:  # imperial
            units_override = {"depth": "ft", "pressure": "psi", "temperature": "F"}

    # Test template shortcut
    if args.test_template:
        try:
            if args.profile_template:
                # Test profile template
                template = load_template(args.profile_template)
                print("Generating test profile template image...")
                generate_test_profile_image(template, "test_profile_template.png", units_override=units_override)
                print("✅ Test profile template image saved as test_profile_template.png")
            else:
                # Test computer overlay template
                template = load_template(args.template)
                print("Generating test template image...")
                generate_test_template_image(template, "test_template.png", units_override=units_override)
                print("✅ Test template image saved as test_template.png")
        except TemplateError as e:
            print(f"❌ Error: {e}")
        except Exception as e:
            print(f"❌ Error generating test template: {e}")
            print("   Please check that all dependencies are installed.")
        return

    # Parse dive log
    try:
        dive_data = parse_dive_log(args.log)
        if not dive_data.samples:
            print("❌ No dive data parsed. Exiting.")
            return
    except DiveLogError as e:
        print(f"❌ Error: {e}")
        return
    except Exception as e:
        print(f"❌ Unexpected error while parsing dive log: {e}")
        print("   Please check that the file exists and is a valid dive log.")
        return

    # Determine segment extraction mode
    dive_samples = dive_data.samples  # Default to full dive
    segment_start_offset = None
    segment_duration = None
    time_offset = 0  # Offset for segment rendering

    if args.match_video:
        # Automatic segment matching mode
        try:
            print(f"🔍 Analyzing video: {args.match_video}")
            video_metadata = extract_video_metadata(args.match_video)
            print(f"   Video duration: {video_metadata.duration:.1f}s")
            source_label = "video metadata" if video_metadata.source == "video_metadata" else "file system"
            print(f"   Creation time: {video_metadata.start_time} (from {source_label})")

            print(f"🔍 Detecting timezone offset...")
            timezone_offset = detect_timezone_offset(
                video_metadata.start_time,
                dive_data.start_time,
                dive_data.end_time
            )

            if timezone_offset is None:
                raise TimezoneOffsetError(
                    video_metadata.start_time,
                    dive_data.start_time,
                    dive_data.end_time,
                    max_offset=10,
                    video_duration=video_metadata.duration
                )

            print(f"   Detected offset: {timezone_offset:+d} hours")

            # Calculate segment boundaries
            video_start_utc = video_metadata.start_time + timedelta(hours=timezone_offset)
            segment_start_offset = int((video_start_utc - dive_data.start_time).total_seconds())
            segment_end_offset = segment_start_offset + int(video_metadata.duration)
            segment_duration = int(video_metadata.duration)

            print(f"🔍 Extracting dive segment...")
            print(f"   Segment start: {segment_start_offset}s from dive start")
            print(f"   Segment end: {segment_end_offset}s from dive start")

            dive_samples = extract_dive_segment(
                dive_data,
                segment_start_offset,
                segment_end_offset
            )
            time_offset = segment_start_offset
            print(f"   Extracted {len(dive_samples)} samples")

        except (VideoReadError, VideoMetadataError) as e:
            print(f"❌ Video error: {e}")
            return
        except TimezoneOffsetError as e:
            print(f"❌ {e}")
            return
        except (SegmentOutOfBoundsError, EmptySegmentError) as e:
            print(f"❌ {e}")
            return
        except Exception as e:
            print(f"❌ Unexpected error during segment matching: {e}")
            import traceback
            traceback.print_exc()
            return

    elif args.start is not None:
        # Manual segment mode
        segment_start_offset = args.start
        segment_end_offset = segment_start_offset + args.duration  # Already validated to be present
        segment_duration = args.duration

        try:
            print(f"🔍 Extracting manual dive segment...")
            print(f"   Segment start: {segment_start_offset}s from dive start")
            print(f"   Segment end: {segment_end_offset}s from dive start")

            dive_samples = extract_dive_segment(
                dive_data,
                segment_start_offset,
                segment_end_offset
            )
            time_offset = segment_start_offset
            print(f"   Extracted {len(dive_samples)} samples")

        except (SegmentOutOfBoundsError, EmptySegmentError) as e:
            print(f"❌ {e}")
            return
        except Exception as e:
            print(f"❌ Unexpected error during segment extraction: {e}")
            import traceback
            traceback.print_exc()
            return

    # Load template
    try:
        if args.profile_template:
            template = load_template(args.profile_template)
            template_type = "profile"
        else:
            template = load_template(args.template)
            template_type = "computer"
    except TemplateError as e:
        print(f"❌ Error: {e}")
        return
    except Exception as e:
        print(f"❌ Error loading template: {e}")
        return

    # Determine resolution from template (fallback defaults)
    width = int(template.get("width", 480))
    height = int(template.get("height", 280))
    resolution = (width, height)

    # Duration: use segment duration if in segment mode, otherwise user override or derive from last sample time
    if segment_duration is not None:
        duration = segment_duration
    elif args.duration is not None:
        duration = args.duration
    else:
        duration = int(dive_samples[-1].time) + 1

    overlay_type = "profile graph" if template_type == "profile" else "computer"
    print(f"Generating {overlay_type} overlay video: {args.output}")
    print(f" - Resolution: {resolution[0]}x{resolution[1]}")
    print(f" - Duration: {duration}s (fps={args.fps})")
    if units_override:
        print(f" - Units: {args.units} -> {units_override}")

    try:
        if template_type == "profile":
            # For profile graphs, always render full dive profile even when generating segment video
            full_samples = dive_data.samples
            generate_profile_overlay_video(full_samples, template, args.output, resolution=resolution, duration=duration, fps=args.fps, units_override=units_override, time_offset=time_offset, segment_samples=dive_samples if time_offset > 0 else None)
        else:
            generate_overlay_video(dive_samples, template, args.output, resolution=resolution, duration=duration, fps=args.fps, units_override=units_override, time_offset=time_offset)
        print(f"✅ Done. Overlay video saved to: {args.output}")
    except Exception as e:
        print(f"❌ Error generating overlay video: {e}")
        print("   Please check that all dependencies are installed and the output path is writable.")
        return

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("   Please check your inputs and try again.")
