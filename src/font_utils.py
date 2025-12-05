#!/usr/bin/env python3
"""
Font utility to list and test available fonts using SimPIL-Font.
"""

from simpilfont import Font as SimPILFont
from PIL import ImageFont
from typing import Dict, Any, Union
import argparse
import json

# Simple font cache to avoid reloading fonts repeatedly
_FONT_CACHE: Dict[tuple[str, int], Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]] = {}

# Global SimPIL-Font instance
_FONT_MANAGER = SimPILFont()


def get_font_name(font_config: Dict[str, Any], default_font: Dict[str, Any]) -> str:
    """
    Get font name from font configuration.
    Uses cross-platform font names only.
    """
    return font_config.get("name") or default_font.get("name") or "Arial"


def get_font(font_name: str, size: int) -> Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]:
    """
    Get font using SimPIL-Font for cross-platform support.

    Args:
        font_name: Font name (e.g., "Arial Bold", "Helvetica")
        size: Font size in pixels
    """
    key = (font_name, size)
    font = _FONT_CACHE.get(key)
    if font is None:
        try:
            # Use SimPIL-Font to find and load the font
            font = _FONT_MANAGER(font_name, size).font
        except Exception:
            # Fallback: try common alternatives
            fallback_names = ["Arial", "Arial Bold", "Helvetica", "DejaVu Sans"]
            for fallback_name in fallback_names:
                try:
                    font = _FONT_MANAGER(fallback_name, size).font
                    break
                except Exception:
                    continue
            else:
                # Ultimate fallback to PIL default
                font = ImageFont.load_default()
        _FONT_CACHE[key] = font
    return font

def list_fonts():
    """List all available font families on the system."""
    print("Generating font list (this may take a moment)...")

    font_manager = SimPILFont()

    # Export all fonts to fonts.json to get the complete list
    font_manager.export()

    # Read the generated fonts.json file
    try:
        with open('fonts.json', 'r') as f:
            fonts_data = json.load(f)

        print("\nAvailable fonts on this system:")
        print("-" * 50)

        all_fonts = set()
        for encoding, font_list in fonts_data.items():
            if font_list:  # Only process non-empty lists
                print(f"\n{encoding.upper()} encoding fonts:")
                for font_entry in font_list:
                    # Extract family name and style
                    parts = font_entry.split()
                    if len(parts) >= 2:
                        family_name = ' '.join(parts[:-1])
                        style = parts[-1]
                        all_fonts.add(family_name)
                        print(f"  {family_name} ({style})")
                    else:
                        all_fonts.add(font_entry)
                        print(f"  {font_entry}")

        print(f"\nTotal: {len(all_fonts)} unique font families available")

        # Cleanup
        import os
        try:
            os.remove('fonts.json')
        except:
            pass

    except FileNotFoundError:
        print("Error: Could not generate font list")

def find_font(font_name):
    """Find and test a specific font."""
    try:
        font_manager = SimPILFont()
        font_obj = font_manager(font_name, 20)  # Test with size 20
        print(f"✅ Font '{font_name}' found successfully!")
        print(f"   Family: {font_obj.family}")
        print(f"   Style: {font_obj.style}")
        print(f"   Path: {font_obj.path}")
        print(f"   Available styles: {', '.join(font_obj.styles)}")
    except Exception as e:
        print(f"❌ Font '{font_name}' not found: {e}")

def test_common_fonts():
    """Test common cross-platform fonts."""
    common_fonts = [
        "Arial", "Arial Bold", "Arial Black",
        "Times", "Times New Roman", "Times Bold",
        "Courier", "Courier New", "Courier Bold",
        "Helvetica", "Helvetica Bold"
    ]

    print("Testing common cross-platform fonts:")
    print("-" * 50)

    for font_name in common_fonts:
        try:
            font_manager = SimPILFont()
            font_obj = font_manager(font_name, 20)
            print(f"✅ {font_name:<20} → {font_obj.family} {font_obj.style}")
        except Exception:
            print(f"❌ {font_name:<20} → Not found")

def main():
    parser = argparse.ArgumentParser(description="Font utility for ScubaOverlay using SimPIL-Font")
    parser.add_argument("--list", action="store_true", help="List all available fonts")
    parser.add_argument("--find", metavar="FONT_NAME", help="Find and test specific font")
    parser.add_argument("--test-common", action="store_true", help="Test common cross-platform fonts")

    args = parser.parse_args()

    if args.list:
        list_fonts()
    elif args.find:
        find_font(args.find)
    elif args.test_common:
        test_common_fonts()
    else:
        print("Font utility for ScubaOverlay")
        print("Usage:")
        print("  --list              List all available fonts")
        print("  --find FONT_NAME    Find and test specific font")
        print("  --test-common       Test common cross-platform fonts")
        print("\nExamples:")
        print("  python font_utils.py --find 'Arial Bold'")
        print("  python font_utils.py --test-common")

if __name__ == "__main__":
    main()
