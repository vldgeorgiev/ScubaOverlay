"""Profile graph rendering module for dive depth visualization.

This module generates depth profile graph overlays showing dive depth over time
with a moving position indicator. Graphs are rendered as video overlays for
compositing with dive footage in video editing software.
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from parser import DiveSample
from font_utils import get_font, get_font_name


# Unit conversion constants (metric to imperial)
_M_TO_FT = 3.28084


@dataclass
class _CompiledProfileTemplate:
    """Pre-compiled profile template with static graph background."""
    base_img: Image.Image  # Static background with profile line
    graph_config: Dict[str, Any]  # Graph dimensions, colors, etc.
    frame_size: Tuple[int, int]
    dive_samples: List[DiveSample]  # Cached for position lookup
    max_depth: float  # Cached for coordinate transformations
    total_duration: int  # Total dive/segment duration in seconds


def _time_to_x(time: int, total_duration: int, graph_x: int, graph_width: int) -> int:
    """Convert dive time (seconds) to graph X-coordinate (pixels).

    Args:
        time: Time in seconds from dive/segment start
        total_duration: Total duration in seconds
        graph_x: Graph area X offset in frame
        graph_width: Graph area width in pixels

    Returns:
        X-coordinate in pixels
    """
    if total_duration <= 0:
        return graph_x
    return graph_x + int((time / total_duration) * graph_width)


def _depth_to_y(depth: float, max_depth: float, graph_y: int, graph_height: int) -> int:
    """Convert depth to graph Y-coordinate (pixels, inverted - depth increases downward).

    Args:
        depth: Depth value (meters or feet after conversion)
        max_depth: Maximum depth in dive (with 10% padding applied)
        graph_y: Graph area Y offset in frame
        graph_height: Graph area height in pixels

    Returns:
        Y-coordinate in pixels
    """
    if max_depth <= 0:
        return graph_y
    # Add 10% padding to max depth for visual spacing
    padded_max = max_depth * 1.1
    return graph_y + int((depth / padded_max) * graph_height)


def _render_profile_line(
    draw: ImageDraw.ImageDraw,
    samples: List[DiveSample],
    total_duration: int,
    max_depth: float,
    graph_x: int,
    graph_y: int,
    graph_width: int,
    graph_height: int,
    line_color: Tuple[int, int, int],
    line_thickness: int,
    depth_converter: Optional[callable] = None
) -> None:
    """Draw depth profile line connecting all dive samples.

    Args:
        draw: PIL ImageDraw object
        samples: List of dive samples
        total_duration: Total duration in seconds
        max_depth: Maximum depth (already converted if needed)
        graph_x: Graph area X offset
        graph_y: Graph area Y offset
        graph_width: Graph area width
        graph_height: Graph area height
        line_color: RGB tuple for line color
        line_thickness: Line thickness in pixels
        depth_converter: Optional function to convert depth units
    """
    if not samples:
        return

    # Build list of (x, y) coordinates for all samples
    coordinates = []
    for sample in samples:
        depth = sample.depth
        if depth_converter:
            depth = depth_converter(depth)

        x = _time_to_x(int(sample.time), total_duration, graph_x, graph_width)
        y = _depth_to_y(depth, max_depth, graph_y, graph_height)
        coordinates.append((x, y))

    # Draw line connecting all points
    if len(coordinates) >= 2:
        draw.line(coordinates, fill=line_color, width=line_thickness)
    elif len(coordinates) == 1:
        # Single point - draw small circle
        x, y = coordinates[0]
        r = line_thickness
        draw.ellipse([(x-r, y-r), (x+r, y+r)], fill=line_color)


def _render_position_indicator(
    draw: ImageDraw.ImageDraw,
    current_sample: DiveSample,
    total_duration: int,
    max_depth: float,
    graph_x: int,
    graph_y: int,
    graph_width: int,
    graph_height: int,
    indicator_color: Tuple[int, int, int],
    indicator_size: int,
    depth_converter: Optional[callable] = None
) -> None:
    """Draw position indicator dot at current dive time.

    Args:
        draw: PIL ImageDraw object
        current_sample: Current dive sample
        total_duration: Total duration in seconds
        max_depth: Maximum depth (already converted if needed)
        graph_x: Graph area X offset
        graph_y: Graph area Y offset
        graph_width: Graph area width
        graph_height: Graph area height
        indicator_color: RGB tuple for indicator color
        indicator_size: Indicator radius in pixels
        depth_converter: Optional function to convert depth units
    """
    depth = current_sample.depth
    if depth_converter:
        depth = depth_converter(depth)

    x = _time_to_x(int(current_sample.time), total_duration, graph_x, graph_width)
    y = _depth_to_y(depth, max_depth, graph_y, graph_height)

    # Draw circle
    r = indicator_size
    draw.ellipse([(x-r, y-r), (x+r, y+r)], fill=indicator_color)


def _render_grid(
    draw: ImageDraw.ImageDraw,
    total_duration: int,
    max_depth: float,
    graph_x: int,
    graph_y: int,
    graph_width: int,
    graph_height: int,
    grid_color: Tuple[int, int, int],
    grid_thickness: int,
    time_interval: int,
    depth_interval: float
) -> None:
    """Draw grid lines on the graph.

    Args:
        draw: PIL ImageDraw object
        total_duration: Total duration in seconds
        max_depth: Maximum depth (already converted if needed)
        graph_x: Graph area X offset
        graph_y: Graph area Y offset
        graph_width: Graph area width
        graph_height: Graph area height
        grid_color: RGB tuple for grid color
        grid_thickness: Grid line thickness in pixels
        time_interval: Time interval for vertical grid lines in seconds
        depth_interval: Depth interval for horizontal grid lines
    """
    # Draw vertical grid lines (time intervals)
    if time_interval > 0:
        time = time_interval
        while time < total_duration:
            x = _time_to_x(time, total_duration, graph_x, graph_width)
            draw.line([(x, graph_y), (x, graph_y + graph_height)],
                     fill=grid_color, width=grid_thickness)
            time += time_interval

    # Draw horizontal grid lines (depth intervals)
    if depth_interval > 0:
        padded_max = max_depth * 1.1
        depth = depth_interval
        while depth < padded_max:
            y = _depth_to_y(depth, max_depth, graph_y, graph_height)
            draw.line([(graph_x, y), (graph_x + graph_width, y)],
                     fill=grid_color, width=grid_thickness)
            depth += depth_interval


def _render_axis_labels(
    draw: ImageDraw.ImageDraw,
    total_duration: int,
    max_depth: float,
    graph_x: int,
    graph_y: int,
    graph_width: int,
    graph_height: int,
    axes_config: Dict[str, Any],
    use_imperial: bool
) -> None:
    """Draw axis labels and ticks.

    Args:
        draw: PIL ImageDraw object
        total_duration: Total duration in seconds
        max_depth: Maximum depth (already converted if needed)
        graph_x: Graph area X offset
        graph_y: Graph area Y offset
        graph_width: Graph area width
        graph_height: Graph area height
        axes_config: Axes configuration from template
        use_imperial: Whether using imperial units
    """
    # Depth axis
    if "depth_axis" in axes_config:
        depth_axis = axes_config["depth_axis"]

        # Draw ticks
        if depth_axis.get("show_ticks", False):
            tick_interval = depth_axis.get("tick_interval", 10)
            tick_color = hex_to_rgb(depth_axis.get("tick_color", "#FFFFFF"))
            label_font_config = depth_axis.get("label_font", {})
            font_size = label_font_config.get("size", 14)
            font_color = hex_to_rgb(label_font_config.get("color", "#FFFFFF"))

            try:
                font = get_font(label_font_config.get("name", "Arial"), font_size)
            except:
                font = ImageFont.load_default()

            label_position = depth_axis.get("label_position", "left")
            padded_max = max_depth * 1.1
            depth = 0

            while depth <= padded_max:
                y = _depth_to_y(depth, max_depth, graph_y, graph_height)

                # Draw tick mark
                if label_position == "left":
                    draw.line([(graph_x - 5, y), (graph_x, y)], fill=tick_color, width=1)
                    # Draw label
                    label = f"{int(depth)}"
                    bbox = draw.textbbox((0, 0), label, font=font)
                    text_width = bbox[2] - bbox[0]
                    draw.text((graph_x - 10 - text_width, y - font_size // 2),
                             label, fill=font_color, font=font)
                else:  # right
                    draw.line([(graph_x + graph_width, y), (graph_x + graph_width + 5, y)],
                             fill=tick_color, width=1)
                    draw.text((graph_x + graph_width + 10, y - font_size // 2),
                             f"{int(depth)}", fill=font_color, font=font)

                depth += tick_interval

        # Draw axis label
        if "label" in depth_axis:
            label_text = depth_axis["label"]
            label_font_config = depth_axis.get("label_font", {})
            font_size = label_font_config.get("size", 18)
            font_color = hex_to_rgb(label_font_config.get("color", "#FFFFFF"))

            try:
                font = get_font(label_font_config.get("name", "Arial"), font_size)
            except:
                font = ImageFont.load_default()

            # Position axis label
            label_position = depth_axis.get("label_position", "left")
            if label_position == "left":
                draw.text((5, graph_y - font_size - 5), label_text, fill=font_color, font=font)
            else:
                bbox = draw.textbbox((0, 0), label_text, font=font)
                text_width = bbox[2] - bbox[0]
                draw.text((graph_x + graph_width - text_width - 5, graph_y - font_size - 5),
                         label_text, fill=font_color, font=font)

    # Time axis
    if "time_axis" in axes_config:
        time_axis = axes_config["time_axis"]

        # Draw ticks
        if time_axis.get("show_ticks", False):
            tick_interval = time_axis.get("tick_interval", 60)
            tick_color = hex_to_rgb(time_axis.get("tick_color", "#FFFFFF"))
            tick_format = time_axis.get("tick_format", "mm:ss")
            label_font_config = time_axis.get("label_font", {})
            font_size = label_font_config.get("size", 14)
            font_color = hex_to_rgb(label_font_config.get("color", "#FFFFFF"))

            try:
                font = get_font(label_font_config.get("name", "Arial"), font_size)
            except:
                font = ImageFont.load_default()

            label_position = time_axis.get("label_position", "bottom")
            time = 0

            while time <= total_duration:
                x = _time_to_x(time, total_duration, graph_x, graph_width)

                # Draw tick mark
                if label_position == "bottom":
                    draw.line([(x, graph_y + graph_height), (x, graph_y + graph_height + 5)],
                             fill=tick_color, width=1)
                    # Format time label
                    if tick_format == "mm:ss":
                        minutes = time // 60
                        seconds = time % 60
                        label = f"{minutes:02d}:{seconds:02d}"
                    elif tick_format == "mm":
                        minutes = time // 60
                        label = f"{minutes}"
                    else:  # seconds
                        label = f"{time}"

                    bbox = draw.textbbox((0, 0), label, font=font)
                    text_width = bbox[2] - bbox[0]
                    draw.text((x - text_width // 2, graph_y + graph_height + 8),
                             label, fill=font_color, font=font)
                else:  # top
                    draw.line([(x, graph_y - 5), (x, graph_y)], fill=tick_color, width=1)
                    if tick_format == "mm:ss":
                        minutes = time // 60
                        seconds = time % 60
                        label = f"{minutes:02d}:{seconds:02d}"
                    elif tick_format == "mm":
                        minutes = time // 60
                        label = f"{minutes}"
                    else:  # seconds
                        label = f"{time}"

                    bbox = draw.textbbox((0, 0), label, font=font)
                    text_width = bbox[2] - bbox[0]
                    draw.text((x - text_width // 2, graph_y - font_size - 8),
                             label, fill=font_color, font=font)

                time += tick_interval

        # Draw axis label
        if "label" in time_axis:
            label_text = time_axis["label"]
            label_font_config = time_axis.get("label_font", {})
            font_size = label_font_config.get("size", 18)
            font_color = hex_to_rgb(label_font_config.get("color", "#FFFFFF"))

            try:
                font = get_font(label_font_config.get("name", "Arial"), font_size)
            except:
                font = ImageFont.load_default()

            # Position axis label
            label_position = time_axis.get("label_position", "bottom")
            bbox = draw.textbbox((0, 0), label_text, font=font)
            text_width = bbox[2] - bbox[0]
            x_center = graph_x + graph_width // 2

            if label_position == "bottom":
                draw.text((x_center - text_width // 2, graph_y + graph_height + 35),
                         label_text, fill=font_color, font=font)
            else:
                draw.text((x_center - text_width // 2, 5),
                         label_text, fill=font_color, font=font)


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def compile_profile_template(
    template: Dict[str, Any],
    dive_samples: List[DiveSample],
    frame_size: Tuple[int, int],
    duration: int,
    units_override: Optional[Dict[str, str]] = None,
    time_offset: int = 0
) -> _CompiledProfileTemplate:
    """Pre-compile profile template with static graph background.

    Args:
        template: Profile template dictionary
        dive_samples: List of dive samples to plot
        frame_size: (width, height) of output frame
        duration: Total duration in seconds
        units_override: Optional unit overrides (e.g., {"depth": "ft"})
        time_offset: Time offset for segments

    Returns:
        Compiled profile template with cached static background

    Raises:
        ValueError: If template is invalid or samples are insufficient
    """
    # Validate inputs
    if not dive_samples:
        raise ValueError("Cannot create profile graph: no dive samples provided")

    if len(dive_samples) == 1:
        raise ValueError("Cannot create profile graph: only 1 sample (need at least 2 for a line)")

    if duration <= 0:
        raise ValueError(f"Cannot create profile graph: invalid duration {duration}s")

    # Validate required template fields
    if "graph" not in template:
        raise ValueError("Invalid profile template: missing 'graph' section")

    graph = template.get("graph", {})
    required_fields = ["position", "width", "height", "line", "indicator"]
    missing = [f for f in required_fields if f not in graph]
    if missing:
        raise ValueError(f"Invalid profile template: graph section missing fields: {', '.join(missing)}")

    # Determine units from command line override only
    use_imperial = False
    if units_override:
        use_imperial = units_override.get("depth", "m").lower() in ("ft", "feet")

    # Calculate max depth with unit conversion
    if not dive_samples:
        max_depth = 0.0
    else:
        max_depth = max(s.depth for s in dive_samples)
        if use_imperial:
            max_depth = max_depth * _M_TO_FT

    # Create depth converter if needed
    depth_converter = (lambda d: d * _M_TO_FT) if use_imperial else None

    # Create base image
    bg_color = hex_to_rgb(template.get("background_color", "#00FF00"))
    base_img = Image.new("RGBA", frame_size, bg_color + (255,))
    draw = ImageDraw.Draw(base_img)

    # Extract graph configuration
    graph = template.get("graph", {})
    graph_pos = graph.get("position", {"x": 0, "y": 0})
    graph_x = graph_pos.get("x", 0)
    graph_y = graph_pos.get("y", 0)
    graph_width = graph.get("width", frame_size[0])
    graph_height = graph.get("height", frame_size[1])

    # Extract line configuration
    line_config = graph.get("line", {})
    line_color = hex_to_rgb(line_config.get("color", "#00AAFF"))
    line_thickness = line_config.get("thickness", 3)

    # Render grid if configured
    axes_config = graph.get("axes", {})
    if axes_config.get("show_grid", False):
        grid_interval = axes_config.get("grid_interval", {})
        time_interval = grid_interval.get("time", 60)
        depth_interval = grid_interval.get("depth", 10)
        if use_imperial:
            depth_interval = depth_interval * _M_TO_FT

        grid_color = hex_to_rgb(axes_config.get("grid_color", "#444444"))
        grid_thickness = axes_config.get("grid_thickness", 1)

        _render_grid(
            draw,
            duration,
            max_depth,
            graph_x,
            graph_y,
            graph_width,
            graph_height,
            grid_color,
            grid_thickness,
            time_interval,
            depth_interval
        )

    # Render axis labels and ticks if configured
    if axes_config:
        _render_axis_labels(
            draw,
            duration,
            max_depth,
            graph_x,
            graph_y,
            graph_width,
            graph_height,
            axes_config,
            use_imperial
        )

    # Render static profile line
    _render_profile_line(
        draw,
        dive_samples,
        duration,
        max_depth,
        graph_x,
        graph_y,
        graph_width,
        graph_height,
        line_color,
        line_thickness,
        depth_converter
    )

    # Store configuration for dynamic rendering
    graph_config = {
        "graph_x": graph_x,
        "graph_y": graph_y,
        "graph_width": graph_width,
        "graph_height": graph_height,
        "indicator_color": hex_to_rgb(graph.get("indicator", {}).get("color", "#FF0000")),
        "indicator_size": graph.get("indicator", {}).get("size", 12),
        "depth_converter": depth_converter
    }

    return _CompiledProfileTemplate(
        base_img=base_img,
        graph_config=graph_config,
        frame_size=frame_size,
        dive_samples=dive_samples,
        max_depth=max_depth,
        total_duration=duration
    )


def render_profile_frame(
    compiled: _CompiledProfileTemplate,
    current_time: int
) -> np.ndarray:
    """Render single profile graph frame with position indicator.

    Args:
        compiled: Pre-compiled profile template
        current_time: Current time in seconds from dive/segment start

    Returns:
        Frame as numpy array (RGBA)
    """
    # Copy static background
    img = compiled.base_img.copy()
    draw = ImageDraw.Draw(img)

    # Find current sample (latest sample with time <= current_time)
    current_sample = None
    for sample in compiled.dive_samples:
        if sample.time <= current_time:
            current_sample = sample
        else:
            break

    if current_sample is None and compiled.dive_samples:
        # Use first sample if current_time is before all samples
        current_sample = compiled.dive_samples[0]

    # Render position indicator
    if current_sample:
        _render_position_indicator(
            draw,
            current_sample,
            compiled.total_duration,
            compiled.max_depth,
            compiled.graph_config["graph_x"],
            compiled.graph_config["graph_y"],
            compiled.graph_config["graph_width"],
            compiled.graph_config["graph_height"],
            compiled.graph_config["indicator_color"],
            compiled.graph_config["indicator_size"],
            compiled.graph_config["depth_converter"]
        )

    return np.array(img)


def generate_profile_overlay_video(
    dive_samples: List[DiveSample],
    template: Dict[str, Any],
    output_path: str,
    resolution: Tuple[int, int] = (800, 300),
    duration: Optional[int] = None,
    fps: int = 10,
    units_override: Optional[Dict[str, str]] = None,
    time_offset: int = 0,
    segment_samples: Optional[List[DiveSample]] = None
) -> None:
    """Generate profile overlay video from dive samples and template.

    Args:
        dive_samples: List of ALL dive samples (full dive for rendering complete profile)
        template: Profile template dictionary
        output_path: Output video file path
        resolution: (width, height) of output video
        duration: Duration in seconds for video generation (segment duration)
        fps: Frames per second
        units_override: Optional unit overrides
        time_offset: Time offset for segments (start time of segment in full dive)
        segment_samples: Optional segment samples for position indicator (if None, uses dive_samples)
    """
    # Determine video duration
    if duration is not None:
        total_seconds = int(duration)
    else:
        total_seconds = int(dive_samples[-1].time) + 1 if dive_samples else 0

    # For profile rendering, use full dive duration and all samples
    full_dive_duration = int(dive_samples[-1].time) + 1 if dive_samples else 0

    # Compile template with FULL dive samples and duration for complete profile
    compiled = compile_profile_template(
        template,
        dive_samples,
        resolution,
        full_dive_duration,
        units_override,
        0  # No time offset for rendering full profile
    )

    # Setup video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, resolution)

    print(f"Generating {total_seconds * fps} frames in {total_seconds} seconds...")
    progress_step = max(1, total_seconds // 10)

    # Render frames
    for sec in range(total_seconds):
        # Calculate actual dive time for sample lookup
        dive_time = sec + time_offset

        # Render frame with position indicator at current time
        frame_rgba = render_profile_frame(compiled, dive_time)
        frame_bgr = cv2.cvtColor(frame_rgba, cv2.COLOR_RGBA2BGR)

        # Duplicate frame for FPS
        for _ in range(fps):
            out.write(frame_bgr)

        # Progress reporting
        if (sec + 1) % progress_step == 0 or sec == total_seconds - 1:
            percent = (sec + 1) / total_seconds * 100 if total_seconds else 100
            print(f"Progress: {percent:.1f}% ({sec + 1}/{total_seconds} sec)")

    out.release()


def generate_test_profile_image(
    template: Dict[str, Any],
    output_path: str,
    units_override: Optional[Dict[str, str]] = None
) -> None:
    """Generate test profile graph image with dummy dive data.

    Args:
        template: Profile template dictionary
        output_path: Output image file path
        units_override: Optional unit overrides
    """
    # Create dummy dive profile (descent, bottom time, ascent, safety stop)
    dummy_samples = []

    # Descent: 0-30m over 3 minutes
    for t in range(0, 180, 10):
        depth = (t / 180.0) * 30.0
        dummy_samples.append(DiveSample(time=t, depth=depth))

    # Bottom time: 30m for 20 minutes
    for t in range(180, 1380, 10):
        dummy_samples.append(DiveSample(time=t, depth=30.0))

    # Ascent to 5m: 5 minutes
    for t in range(1380, 1680, 10):
        depth = 30.0 - ((t - 1380) / 300.0) * 25.0
        dummy_samples.append(DiveSample(time=t, depth=depth))

    # Safety stop at 5m: 3 minutes
    for t in range(1680, 1860, 10):
        dummy_samples.append(DiveSample(time=t, depth=5.0))

    # Surface
    for t in range(1860, 1920, 10):
        depth = 5.0 - ((t - 1860) / 60.0) * 5.0
        dummy_samples.append(DiveSample(time=t, depth=max(0, depth)))

    frame_size = (int(template.get("width", 800)), int(template.get("height", 300)))
    duration = 1920  # ~32 minutes

    # Compile template with dummy data
    compiled = compile_profile_template(
        template,
        dummy_samples,
        frame_size,
        duration,
        units_override
    )

    # Render frame at mid-dive (position indicator at ~15 minutes)
    frame_rgba = render_profile_frame(compiled, 900)

    # Save as PNG
    img = Image.fromarray(frame_rgba)
    img.save(output_path)
