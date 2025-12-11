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


def _format_gas_mixture(fraction_o2: Optional[float], fraction_he: Optional[float]) -> str:
    """Format gas mixture for display using standard diving notation.

    Args:
        fraction_o2: Fraction of oxygen (0.0-1.0)
        fraction_he: Fraction of helium (0.0-1.0)

    Returns:
        Formatted gas string (e.g., "AIR", "EAN50", "18/45")
    """
    if fraction_o2 is None:
        return "Unknown"

    o2_percent = int(round(fraction_o2 * 100))
    he_percent = int(round(fraction_he * 100)) if fraction_he else 0

    # Air (21% O2, no He)
    if o2_percent == 21 and he_percent == 0:
        return "AIR"

    # Nitrox (>21% O2, no He)
    if he_percent == 0:
        return f"EAN{o2_percent}"

    # Trimix (with helium)
    return f"{o2_percent}/{he_percent}"


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
        indicator_size: Radius of indicator in pixels
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


def _render_gas_changes(
    draw: ImageDraw.ImageDraw,
    samples: List[DiveSample],
    total_duration: int,
    max_depth: float,
    graph_x: int,
    graph_y: int,
    graph_width: int,
    graph_height: int,
    gas_config: Dict[str, Any],
    depth_converter: Optional[callable] = None
) -> None:
    """Render gas change markers and labels on the profile graph.

    Args:
        draw: PIL ImageDraw object
        samples: List of dive samples
        total_duration: Total duration in seconds
        max_depth: Maximum depth
        graph_x: Graph area X offset
        graph_y: Graph area Y offset
        graph_width: Graph area width
        graph_height: Graph area height
        gas_config: Gas changes configuration from template
        depth_converter: Optional function to convert depth units
    """
    if not gas_config.get("show", False):
        return

    # Extract gas change events (where fractionO2/He change)
    gas_changes = []
    prev_o2 = None
    prev_he = None

    for sample in samples:
        if sample.fractionO2 is not None:
            # Check if gas changed
            if prev_o2 != sample.fractionO2 or prev_he != sample.fractionHe:
                gas_changes.append({
                    "time": sample.time,
                    "depth": sample.depth,
                    "o2": sample.fractionO2,
                    "he": sample.fractionHe
                })
                prev_o2 = sample.fractionO2
                prev_he = sample.fractionHe

    if not gas_changes:
        return

    # Extract configuration
    marker_config = gas_config.get("marker", {})
    marker_color = hex_to_rgb(marker_config.get("color", "#FFFFFF"))
    marker_size = marker_config.get("size", 12)
    marker_icon = marker_config.get("icon", "▼")  # Default: down-pointing triangle

    show_labels = gas_config.get("show_labels", True)
    label_font_config = gas_config.get("label_font", {})
    label_color = hex_to_rgb(label_font_config.get("color", "#FFFF00"))
    label_size = label_font_config.get("size", 14)
    label_position = gas_config.get("label_position", "above")

    try:
        font = get_font(label_font_config.get("name", "Arial"), label_size)
    except:
        font = ImageFont.load_default()

    # Prepare icon font for markers
    try:
        icon_font = get_font(marker_config.get("font", "Arial"), marker_size)
    except:
        icon_font = ImageFont.load_default()

    # Render each gas change
    for gc in gas_changes:
        time_sec = int(gc["time"])
        depth = gc["depth"]
        if depth_converter:
            depth = depth_converter(depth)

        x = _time_to_x(time_sec, total_duration, graph_x, graph_width)
        y_depth = _depth_to_y(depth, max_depth, graph_y, graph_height)

        # Draw icon marker at the depth where gas change occurred
        icon_bbox = draw.textbbox((0, 0), marker_icon, font=icon_font)
        icon_width = icon_bbox[2] - icon_bbox[0]
        icon_height = icon_bbox[3] - icon_bbox[1]
        icon_x = x - icon_width // 2
        icon_y = y_depth - icon_height // 2
        draw.text((icon_x, icon_y), marker_icon, fill=marker_color, font=icon_font)

        # Draw label if enabled
        if show_labels:
            gas_label = _format_gas_mixture(gc["o2"], gc["he"])

            # Get text size for positioning
            bbox = draw.textbbox((0, 0), gas_label, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Position label relative to the icon
            if label_position == "above":
                label_y = icon_y - text_height - 5
            else:  # below
                label_y = icon_y + icon_height + 5

            label_x = x - text_width // 2

            # Draw label
            draw.text((label_x, label_y), gas_label, fill=label_color, font=font)


def _render_deco_ceiling(
    draw: ImageDraw.ImageDraw,
    samples: List[DiveSample],
    total_duration: int,
    max_depth: float,
    graph_x: int,
    graph_y: int,
    graph_width: int,
    graph_height: int,
    ceiling_config: Dict[str, Any],
    depth_converter: Optional[callable] = None
) -> None:
    """Render decompression ceiling as filled area or line.

    Args:
        draw: PIL ImageDraw object
        samples: List of dive samples
        total_duration: Total duration in seconds
        max_depth: Maximum depth
        graph_x: Graph area X offset
        graph_y: Graph area Y offset
        graph_width: Graph area width
        graph_height: Graph area height
        ceiling_config: Deco ceiling configuration from template
        depth_converter: Optional function to convert depth units
    """
    if not ceiling_config.get("show", False):
        return

    # Extract ceiling depths from samples
    ceiling_points = []
    has_nonzero_ceiling = False

    for sample in samples:
        ceiling_depth = sample.stop_depth if sample.stop_depth else 0.0

        # Track if there's any actual ceiling (non-zero depth)
        if ceiling_depth > 0:
            has_nonzero_ceiling = True

        # Convert depth if needed
        if depth_converter:
            ceiling_depth = depth_converter(ceiling_depth)

        time_sec = int(sample.time)
        x = _time_to_x(time_sec, total_duration, graph_x, graph_width)
        y = _depth_to_y(ceiling_depth, max_depth, graph_y, graph_height)

        ceiling_points.append((x, y))

    # Don't render if no ceiling points or all ceilings are at 0 (surface)
    if not ceiling_points or not has_nonzero_ceiling:
        return

    # Get rendering style
    style = ceiling_config.get("style", "filled")

    # Render filled area
    if style in ("filled", "both"):
        fill_color_hex = ceiling_config.get("fill_color", "#FF000030")

        # Parse RGBA hex color
        if len(fill_color_hex) == 9:  # #RRGGBBAA
            r = int(fill_color_hex[1:3], 16)
            g = int(fill_color_hex[3:5], 16)
            b = int(fill_color_hex[5:7], 16)
            a = int(fill_color_hex[7:9], 16)
            fill_color = (r, g, b, a)
        else:  # #RRGGBB - default to 50% opacity
            fill_color = hex_to_rgb(fill_color_hex) + (128,)

        # Build polygon segments only where ceiling is below surface
        # Split into separate polygons where ceiling depth > 0
        current_segment = []

        for i, (x, y) in enumerate(ceiling_points):
            if y > graph_y:  # Ceiling is below surface (has depth)
                if not current_segment:
                    # Start new segment - add surface point at this x
                    current_segment.append((x, graph_y))
                current_segment.append((x, y))
            else:
                # Ceiling at surface - close current segment if exists
                if current_segment:
                    # Add surface point at previous x and close
                    prev_x = ceiling_points[i-1][0] if i > 0 else x
                    current_segment.append((prev_x, graph_y))
                    # Draw this segment
                    if len(current_segment) >= 3:
                        draw.polygon(current_segment, fill=fill_color)
                    current_segment = []

        # Close final segment if exists
        if current_segment:
            last_x = ceiling_points[-1][0]
            current_segment.append((last_x, graph_y))
            if len(current_segment) >= 3:
                draw.polygon(current_segment, fill=fill_color)

    # Render border line
    if style in ("line", "both"):
        border_config = ceiling_config.get("border", {})
        border_color = hex_to_rgb(border_config.get("color", "#FF0000"))
        border_thickness = border_config.get("thickness", 2)

        # Draw line connecting ceiling points (only if there's variation from surface)
        # Filter out points that are at the surface to avoid drawing a line at y=0
        non_surface_points = [(x, y) for x, y in ceiling_points if y != graph_y]

        if len(non_surface_points) > 1:
            draw.line(non_surface_points, fill=border_color, width=border_thickness)


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

            padded_max = max_depth * 1.1
            depth = 0

            while depth <= padded_max:
                y = _depth_to_y(depth, max_depth, graph_y, graph_height)

                # Draw tick mark on left side
                draw.line([(graph_x - 5, y), (graph_x, y)], fill=tick_color, width=1)
                # Draw label
                label = f"{int(depth)}"
                bbox = draw.textbbox((0, 0), label, font=font)
                text_width = bbox[2] - bbox[0]
                draw.text((graph_x - 10 - text_width, y - font_size // 2),
                         label, fill=font_color, font=font)

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

            # Create a temporary image for rotated text
            bbox = draw.textbbox((0, 0), label_text, font=font)
            text_width = int(bbox[2] - bbox[0])
            text_height = int(bbox[3] - bbox[1])

            # Create image for text
            text_img = Image.new('RGBA', (text_width + 10, text_height + 10), (0, 0, 0, 0))
            text_draw = ImageDraw.Draw(text_img)
            text_draw.text((5, 5), label_text, fill=font_color, font=font)

            # Rotate 90 degrees counter-clockwise
            rotated = text_img.rotate(90, expand=True)

            # Place to the left of the graph, centered vertically
            # Position it further left to avoid overlapping with tick labels
            y_center = graph_y + graph_height // 2
            paste_y = y_center - rotated.height // 2
            # Position: move further left - rotated.width gives us space for the rotated text
            paste_x = max(2, graph_x - 55 - rotated.width)
            # Paste the rotated text onto the main image
            draw._image.paste(rotated, (paste_x, paste_y), rotated)

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

            time = 0

            while time <= total_duration:
                x = _time_to_x(time, total_duration, graph_x, graph_width)

                # Draw tick mark on bottom
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

            # Position axis label at bottom center
            bbox = draw.textbbox((0, 0), label_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x_center = graph_x + graph_width // 2

            # Position below ticks with less spacing
            draw.text((x_center - text_width // 2, graph_y + graph_height + 25),
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

    # Render decompression ceiling if configured (before profile line)
    deco_ceiling_config = graph.get("deco_ceiling", {})
    if deco_ceiling_config.get("show", False):
        _render_deco_ceiling(
            draw,
            dive_samples,
            duration,
            max_depth,
            graph_x,
            graph_y,
            graph_width,
            graph_height,
            deco_ceiling_config,
            depth_converter
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

    # Render gas changes if configured (after profile line)
    gas_changes_config = graph.get("gas_changes", {})
    if gas_changes_config.get("show", False):
        _render_gas_changes(
            draw,
            dive_samples,
            duration,
            max_depth,
            graph_x,
            graph_y,
            graph_width,
            graph_height,
            gas_changes_config,
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

    # Descent: 0-30m over 3 minutes (on air)
    for t in range(0, 180, 10):
        depth = (t / 180.0) * 30.0
        dummy_samples.append(DiveSample(
            time=t,
            depth=depth,
            fractionO2=0.21,  # Air
            fractionHe=0.0,
            stop_depth=0.0
        ))

    # Bottom time: 30m for 20 minutes (still on air)
    for t in range(180, 1380, 10):
        dummy_samples.append(DiveSample(
            time=t,
            depth=30.0,
            fractionO2=0.21,
            fractionHe=0.0,
            stop_depth=0.0
        ))

    # Gas change to EAN50 at start of ascent
    # Ascent to 20m: 2 minutes
    for t in range(1380, 1500, 10):
        depth = 30.0 - ((t - 1380) / 120.0) * 10.0
        ceiling = max(0, 20.0 - (t - 1380) / 120.0 * 15.0)  # Ceiling from 20m to 5m
        dummy_samples.append(DiveSample(
            time=t,
            depth=depth,
            fractionO2=0.50,  # EAN50
            fractionHe=0.0,
            stop_depth=ceiling
        ))

    # Continue ascent to 5m: 3 minutes with deco obligation
    for t in range(1500, 1680, 10):
        depth = 20.0 - ((t - 1500) / 180.0) * 15.0
        ceiling = max(0, 5.0)  # Ceiling at 5m
        dummy_samples.append(DiveSample(
            time=t,
            depth=depth,
            fractionO2=0.50,
            fractionHe=0.0,
            stop_depth=ceiling
        ))

    # Safety/deco stop at 5m: 3 minutes
    for t in range(1680, 1860, 10):
        ceiling = max(0, 5.0 - ((t - 1680) / 180.0) * 5.0)  # Ceiling decreases to 0
        dummy_samples.append(DiveSample(
            time=t,
            depth=5.0,
            fractionO2=0.50,
            fractionHe=0.0,
            stop_depth=ceiling
        ))

    # Surface
    for t in range(1860, 1920, 10):
        depth = 5.0 - ((t - 1860) / 60.0) * 5.0
        dummy_samples.append(DiveSample(
            time=t,
            depth=max(0, depth),
            fractionO2=0.50,
            fractionHe=0.0,
            stop_depth=0.0
        ))

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
