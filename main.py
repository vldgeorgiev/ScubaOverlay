import argparse
from parser import parse_dive_log
from template import load_template
from overlay import generate_overlay_video, generate_test_template_image

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", required=True, help="YAML layout template file")
    parser.add_argument("--log", required=False, help="Dive log file (e.g. .ssrf)")
    parser.add_argument("--output", required=False, default="output_overlay.mp4", help="Output overlay video file (e.g. overlay.mp4)")
    parser.add_argument("--duration", type=int, default=None, help="Override duration (seconds). If omitted, derived from dive log last sample time.")
    parser.add_argument("--fps", type=int, default=10, help="Frames per second for output video")
    parser.add_argument("--test-template", action="store_true", help="Generate a single PNG image with dummy data and exit")
    parser.add_argument("--units", choices=["metric", "imperial"], help="Override all display units (metric or imperial)")
    args = parser.parse_args()

    if not args.test_template and not args.log:
        parser.error("--log is required unless --test-template is used")

    units_override = None
    if args.units:
        if args.units == "metric":
            units_override = {"depth": "m", "pressure": "bar", "temperature": "C"}
        else:  # imperial
            units_override = {"depth": "ft", "pressure": "psi", "temperature": "F"}

    # Test template shortcut
    if args.test_template:
        template = load_template(args.template)
        print("Generating test template image...")
        generate_test_template_image(template, "test_template.png", units_override=units_override)
        print("✅ Test template image saved as test_template.png")
        return

    # Parse dive log
    dive_data = parse_dive_log(args.log)
    if not dive_data:
        print("No dive data parsed. Exiting.")
        return

    # Load template
    template = load_template(args.template)

    # Determine resolution from template (fallback defaults)
    width = int(template.get("width", 480))
    height = int(template.get("height", 280))
    resolution = (width, height)

    # Duration: user override or derive from last sample time
    duration = args.duration if args.duration is not None else int(dive_data[-1]["time"]) + 1

    print(f"Generating overlay video: {args.output}")
    print(f" - Resolution: {resolution[0]}x{resolution[1]}")
    print(f" - Duration: {duration}s (fps={args.fps})")
    if units_override:
        print(f" - Units: {args.units} -> {units_override}")
    generate_overlay_video(dive_data, template, args.output, resolution=resolution, duration=duration, fps=args.fps, units_override=units_override)
    print(f"✅ Done. Overlay video saved to: {args.output}")

if __name__ == "__main__":
    main()
