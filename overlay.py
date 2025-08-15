import cv2
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from typing import Dict, Any, List, Optional, Callable
from parser import DiveSample

# Simple font cache to avoid reloading fonts repeatedly
_FONT_CACHE: Dict[tuple[str, int], ImageFont.FreeTypeFont] = {}

# Canonical source units from parser (Subsurface): meters, bar, Celsius
_SOURCE_UNITS = {
    "depth": "m",
    "pressure": "bar",
    "temperature": "C",
}

# Conversion helpers (only metric->imperial currently needed)
_DEF_M_TO_FT = 3.28084
_DEF_BAR_TO_PSI = 14.5037738

# Only keep one-way (metric -> imperial) numeric converters; temperature handled separately
_DEF_CONVERTERS = {
    ("depth", "m", "ft"): lambda v: v * _DEF_M_TO_FT,
    ("pressure", "bar", "psi"): lambda v: v * _DEF_BAR_TO_PSI,
}

def _build_converter(quantity: str, src_unit: str, target_unit: str) -> Optional[Callable[[Any], Any]]:
    # Internal data always metric (m, bar, C). Only build converter if target is imperial.
    if not target_unit:
        return None
    target = target_unit.lower()
    if quantity == "temperature":
        if src_unit.lower() == "c" and target in ("f", "°f", "fahrenheit"):
            return lambda v: ((v * 9/5) + 32) if isinstance(v, (int, float)) else v
        return None
    key = (quantity, src_unit, target)
    fn = _DEF_CONVERTERS.get(key)
    return (lambda v: fn(v) if isinstance(v, (int, float)) else v) if fn else None

# Pre-compiled template for faster rendering
class _CompiledTemplate:
    def __init__(self, base_img: Image.Image, data_items: List[Dict[str, Any]], frame_size: tuple[int, int], units_map: Dict[str, str]):
        self.base_img = base_img
        self.data_items = data_items
        self.frame_size = frame_size
        self.units_map = units_map  # e.g. {"depth": "ft", "pressure": "psi", "temperature": "F"}
        self.has_converters = any(it.get("_convert") for it in data_items)


def _compile_template(template: Dict[str, Any], frame_size: tuple[int, int], units_override: Optional[Dict[str, str]] = None) -> _CompiledTemplate:
    # Background handling: either solid color or a transparent PNG mapped onto a chroma key color.
    background_image_path = template.get("background_image")
    chroma_rgb = hex_to_rgb(template.get("chroma_color", "#00FF00")) # default green

    if background_image_path:
        # Start with chroma base so fully transparent pixels become the chroma key.
        base = Image.new("RGBA", frame_size, chroma_rgb + (255,))
        try:
            fg = Image.open(background_image_path).convert("RGBA")
            if fg.size != frame_size:
                # Resize preserving aspect ratio by letterboxing/padding to avoid distortion.
                fg_ratio = fg.width / fg.height
                frame_ratio = frame_size[0] / frame_size[1]
                if abs(fg_ratio - frame_ratio) < 0.01:
                    fg_resized = fg.resize(frame_size, Image.Resampling.LANCZOS)
                elif fg_ratio > frame_ratio:
                    # Wider than frame: fit width
                    new_w = frame_size[0]
                    new_h = int(new_w / fg_ratio)
                    fg_resized = fg.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    pad_y = (frame_size[1] - new_h) // 2
                    tmp = Image.new("RGBA", frame_size, chroma_rgb + (255,))
                    tmp.paste(fg_resized, (0, pad_y), fg_resized)
                    fg = tmp
                else:
                    # Taller than frame: fit height
                    new_h = frame_size[1]
                    new_w = int(new_h * fg_ratio)
                    fg_resized = fg.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    pad_x = (frame_size[0] - new_w) // 2
                    tmp = Image.new("RGBA", frame_size, chroma_rgb + (255,))
                    tmp.paste(fg_resized, (pad_x, 0), fg_resized)
                    fg = tmp

            # Overlay PNG onto chroma base, preserving alpha
            base.paste(fg, (0, 0), fg)
        except Exception:
            # If background image loading fails, fall back to solid color
            bg_color = hex_to_rgb(template.get("background_color", "#000000"))
            base = Image.new("RGBA", frame_size, bg_color + (255,))
    else:
        bg_color = hex_to_rgb(template.get("background_color", "#000000"))
        base = Image.new("RGBA", frame_size, bg_color + (255,))

    draw = ImageDraw.Draw(base)

    default_label_font = template.get("default_label_font", {})
    default_data_font = template.get("default_data_font", {})

    fallback_path = default_label_font.get("path") or default_data_font.get("path") or "/System/Library/Fonts/Supplemental/Arial.ttf"

    data_items: List[Dict[str, Any]] = []

    for item in template.get("items", []):
        item_type = item.get("type", "data")  # Default to "data" for backward compatibility

        if item_type == "text":
            # Static text item
            text = item.get("text", "")
            pos = item.get("position", {"x": 0, "y": 0})
            x, y = pos.get("x", 0), pos.get("y", 0)

            # Use label font as default for text items
            font_size = item.get("font", {}).get("size", default_label_font.get("size", 22))
            font_path = item.get("font", {}).get("path", default_label_font.get("path", fallback_path))
            font_color = hex_to_rgb(item.get("font", {}).get("color", default_label_font.get("color", "#FFFFFF")))

            font = _get_font(font_path, font_size)
            draw.text((x, y), text, font=font, fill=font_color)

        elif item_type == "data":
            # Data field item
            field = item.get("field")
            compute_expr = item.get("compute")

            if not field and not compute_expr:
                continue  # Skip items without field or compute expression

            unit = item.get("unit", "")
            label = item.get("label", "")
            fallback_value = item.get("fallback", "N/A")

            # Draw label (static) onto base
            label_pos = item.get("label_position", {"x": 0, "y": 0})
            label_x, label_y = label_pos.get("x", 0), label_pos.get("y", 0)
            label_font_size = item.get("label_font", {}).get("size", default_label_font.get("size", 22))
            label_font_path = item.get("label_font", {}).get("path", default_label_font.get("path", fallback_path))
            label_font = _get_font(label_font_path, label_font_size)
            label_color = hex_to_rgb(item.get("label_font", {}).get("color", default_label_font.get("color", "#FFFFFF")))

            if label:
                draw.text((label_x, label_y), label, font=label_font, fill=label_color)

            # Prepare data (dynamic) rendering info
            data_pos = item.get("data_position")
            if not data_pos:
                continue  # Skip if no data position specified

            data_x, data_y = data_pos.get("x", 0), data_pos.get("y", 0)
            data_font_size = item.get("data_font", {}).get("size", default_data_font.get("size", 22))
            data_font_path = item.get("data_font", {}).get("path", default_data_font.get("path", fallback_path))
            data_font = _get_font(data_font_path, data_font_size)
            data_color = hex_to_rgb(item.get("data_color", item.get("data_font", {}).get("color", default_data_font.get("color", "#FFFFFF"))))
            precision = item.get("precision")

            data_items.append({
                "field": field,
                "compute": compute_expr,
                "unit": unit,
                "x": data_x,
                "y": data_y,
                "font": data_font,
                "color": data_color,
                "fallback": fallback_value,
                "precision": precision,
            })

    units_map = template.get("units", {}).copy()
    if units_override:
        units_map.update({k: v for k, v in units_override.items() if v})

    # Precompute converters & final unit labels
    for it in data_items:
        field_name = it["field"]

        # Skip unit conversion for computed fields
        if field_name is None:
            it["_convert"] = None
            it["_final_unit"] = it.get("unit", "")
            continue

        if field_name.startswith("pressure["):
            quantity = "pressure"
        elif field_name in ("depth", "stop_depth"):
            quantity = "depth"
        elif field_name == "temperature":
            quantity = "temperature"
        else:
            quantity = None
        it["_convert"] = None
        it["_final_unit"] = it.get("unit", "")
        if quantity:
            src = _SOURCE_UNITS.get(quantity)
            target = units_map.get(quantity)
            if src and target:
                conv = _build_converter(quantity, src, target)
                if conv:
                    it["_convert"] = conv
                    if it["_final_unit"].strip():  # only replace label if original had one
                        it["_final_unit"] = target

    return _CompiledTemplate(base, data_items, frame_size, units_map)


def _render_dynamic_frame(data: DiveSample, compiled: _CompiledTemplate) -> np.ndarray:
    img = compiled.base_img.copy()
    draw = ImageDraw.Draw(img)
    draw_text = draw.text  # local binding
    for it in compiled.data_items:
        # Check if this is a computed field or regular field
        if it.get("compute"):
            value = evaluate_compute_expression(it["compute"], data)
        else:
            value = extract_value_from_data(it["field"], data)

        if value is None:
            value = it["fallback"]
        conv = it.get("_convert")
        if conv:
            try:
                value = conv(value)
            except Exception:
                pass
        precision = it.get("precision")
        if precision is not None:
            try:
                if isinstance(value, (int, float)) and not (isinstance(value, int) and precision == 0):
                    value = f"{float(value):.{precision}f}"
                elif not isinstance(value, (int, float)):
                    value = f"{float(value):.{precision}f}"
            except Exception:
                pass
        unit = it.get("_final_unit", "")
        display = f"{value} {unit}".strip()
        draw_text((it["x"], it["y"]), display, font=it["font"], fill=it["color"])
    return np.array(img)


def extract_value_from_data(field: str, data: DiveSample):
    # time formatting (required field, should never be None)
    if field == "time":
        t = data.time
        minutes = int(t) // 60
        seconds = int(t) % 60
        return f"{minutes}:{seconds:02d}"

    # pressure[i] - handle optional pressure list
    if field.startswith("pressure["):
        try:
            index = int(field[9:-1])
            pressures = data.pressure
            if pressures is None or index >= len(pressures):
                return None
            return pressures[index]
        except Exception:
            return None

    # Handle all other fields - use getattr with None default for optional fields
    value = getattr(data, field, None)
    return value


def evaluate_compute_expression(compute_expr: str, data: DiveSample) -> Optional[str]:
    """
    Evaluate a simple compute expression using template substitution.

    Supported syntax:
    - {field} - Simple field substitution
    - {field:02%} - Field as percentage with 2 digits (fractionO2 -> "21")
    - {field:1f} - Field with 1 decimal place
    - {field:0f} - Field as integer

    Example: "{fractionO2:02%}/{fractionHe:02%}" -> "32/05"
    """
    import re

    # Find all field references like {field} or {field:format}
    pattern = r'\{([^}:]+)(?::([^}]+))?\}'
    matches = re.findall(pattern, compute_expr)

    result = compute_expr
    for field_name, format_spec in matches:
        # Get the field value
        field_value = getattr(data, field_name, None)

        if field_value is None:
            return None  # If any required field is missing, return None

        # Apply formatting
        if format_spec:
            if format_spec.endswith('%'):
                # Percentage formatting (fraction to percentage)
                digits = format_spec[:-1]
                try:
                    precision = int(digits) if digits else 2
                    formatted_value = f"{round(field_value * 100):0{precision}d}"
                except (ValueError, TypeError):
                    formatted_value = str(field_value)
            elif 'f' in format_spec:
                # Float formatting
                try:
                    formatted_value = f"{field_value:{format_spec}}"
                except (ValueError, TypeError):
                    formatted_value = str(field_value)
            else:
                # Default formatting
                formatted_value = f"{field_value:{format_spec}}"
        else:
            # No formatting specified
            formatted_value = str(field_value)

        # Replace in the result string
        old_pattern = '{' + field_name + (':' + format_spec if format_spec else '') + '}'
        result = result.replace(old_pattern, formatted_value)

    return result


def generate_overlay_video(dive_samples: List[DiveSample], template: Dict[str, Any], output_path: str, resolution=(480, 280), duration=None, fps=30, units_override: Optional[Dict[str, str]] = None):
    fourcc_func = getattr(cv2, "VideoWriter_fourcc", None)
    fourcc = fourcc_func(*'mp4v') if fourcc_func else 0
    out = cv2.VideoWriter(output_path, fourcc, fps, resolution)

    compiled = _compile_template(template, resolution, units_override)

    # Determine total seconds to render, then duplicate frames per second
    if duration is not None:
        total_seconds = int(duration)
    else:
        total_seconds = int(dive_samples[-1].time) + 1 if dive_samples else 0

    # Pointer to current sample for O(1) lookup per second
    idx = 0

    print(f"Generating {total_seconds * fps} frames in {total_seconds} seconds (rendering once/second)...")
    progress_step = max(1, total_seconds // 10)

    for sec in range(total_seconds):
        # Advance sample pointer to latest sample <= current second
        while idx + 1 < len(dive_samples) and dive_samples[idx + 1].time <= sec:
            idx += 1
        sample = dive_samples[idx] if dive_samples else None
        if sample is None:
            break

        frame_rgba = _render_dynamic_frame(sample, compiled)
        frame_bgr = cv2.cvtColor(frame_rgba, cv2.COLOR_RGBA2BGR)

        for _ in range(fps):
            out.write(frame_bgr)

        if (sec + 1) % progress_step == 0 or sec == total_seconds - 1:
            percent = (sec + 1) / total_seconds * 100 if total_seconds else 100
            print(f"Progress: {percent:.1f}% ({sec + 1}/{total_seconds} sec)")

    out.release()


def generate_test_template_image(template: Dict[str, Any], output_path: str, units_override: Optional[Dict[str, str]] = None):
    frame_size = (int(template.get("width", 0)), int(template.get("height", 0)))

    dummy_data = DiveSample(
        depth=30.0,
        time=8000,  # 8000 seconds = 2 hours, 13 minutes, 20 seconds
        ndl=15,
        tts=10,
        temperature=22.5,
        pressure=[200.15, 180.4, 150.50, 120.95],
        stop_depth=6.0,
        stop_time=3,
        fractionO2=0.21,
        fractionHe=0.29,
    )

    compiled = _compile_template(template, frame_size, units_override)
    img_array = _render_dynamic_frame(dummy_data, compiled)
    img = Image.fromarray(img_array)
    img.save(output_path)

def _get_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    key = (path, size)
    font = _FONT_CACHE.get(key)
    if font is None:
        font = ImageFont.truetype(path, size)
        _FONT_CACHE[key] = font
    return font

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
