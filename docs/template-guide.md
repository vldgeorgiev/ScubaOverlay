# Template System Guide

The ScubaOverlay template system allows you to create custom dive overlay layouts using YAML configuration files. Templates define the visual layout, fonts, colors, and data fields to display on your dive overlays.

## Template Structure

### Basic Template Properties

```yaml
template_name: my-template-name    # Template identifier
width: 750                        # Frame width in pixels
height: 600                       # Frame height in pixels
background_color: "#3c3c3c"       # Hex color for background
background_image: "path/to/bg.png" # Optional background image
chroma_color: "#00FF00"           # Color used for transparent areas
```

### Background Options

- **Solid Color**: Use only `background_color` for a simple colored background
- **Image**: Use `background_image` to display an image scaled to fit the template size
- **Transparent Overlay**: Use `background_image` with `chroma_color` - transparent areas in the PNG become the chroma key color

### Font Defaults

Define default fonts that apply to all items unless overridden:

```yaml
default_label_font:
  path: "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
  size: 20
  color: "#00BAEF"

default_data_font:
  path: "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
  size: 42
  color: "#FFFFFF"
```

### Unit System in Templates

Templates can specify default units, but some oof them can be overridden via command-line:

```yaml
units:
  depth: "m"        # Template default depth units (m -> ft)
  pressure: "bar"    # Template default pressure units (bar -> psi)  
  temperature: "C"   # Template default temperature units (C -> F)
```

**Command-line Override:**

- `--units metric` forces all units to metric (m, bar, C). This is the default.
- `--units imperial` forces all units to imperial (ft, psi, F)

## Item Types

### 1. Text Items (Static)

Display static text that doesn't change during the dive:

```yaml
- type: text
  text: "DIVE COMPUTER"
  position: { x: 100, y: 50 }
  font:
    path: "/System/Library/Fonts/Helvetica.ttc"
    size: 24
    color: "#FFFFFF"
```

**Properties:**

- `type: text` - Required for static text
- `text` - The text to display
- `position` - X,Y coordinates for text placement
- `font` - Optional font override (uses `default_label_font` if not specified)

### 2. Data Items (Dynamic)

Display dive data that changes throughout the dive:

```yaml
- type: data
  field: depth
  label: "DEPTH"
  label_position: { x: 180, y: 200 }
  data_position: { x: 180, y: 220 }
  unit: "m"
  precision: 1
  fallback: "N/A"
  label_font:
    size: 18
    color: "#00BAEF"
  data_font:
    size: 36
    color: "#FFFFFF"
```

**Properties:**

- `type: data` - Required for data fields
- `field` - The dive data field to display (see Available Fields below)
- `label` - Optional static label text
- `label_position` - X,Y coordinates for the label
- `data_position` - X,Y coordinates for the data value
- `unit` - Optional unit suffix (can be overridden by unit system)
- `precision` - Number of decimal places for numeric values
- `fallback` - Text to show when data is unavailable
- `label_font` - Font settings for the label
- `data_font` - Font settings for the data value

### 3. Computed Items

Create custom displays by combining multiple data fields:

```yaml
- type: data
  compute: "{fractionO2:02%}/{fractionHe:02%}"
  label: "GAS"
  label_position: { x: 300, y: 350 }
  data_position: { x: 300, y: 370 }
  fallback: "21/00"
```

**Compute Expression Syntax:**

- `{field}` - Simple field substitution
- `{field:02%}` - Percentage with 2 digits (0.21 → "21")
- `{field:1f}` - Float with 1 decimal place
- `{field:0f}` - Integer (no decimal places)

**Examples:**

- `"{fractionO2:02%}/{fractionHe:02%}"` → "32/05" (Trimix)
- `"{depth:1f}m @ {time}"` → "30.5m @ 45:30"
- `"{pressure[0]:0f} bar"` → "200 bar"

## Available Data Fields

### Core Dive Data

- `time` - Dive time (formatted as MM:SS)
- `depth` - Current depth in meters
- `temperature` - Water temperature in Celsius

### Decompression Info

- `ndl` - No Decompression Limit in minutes
- `tts` - Time to Surface in minutes
- `stop_depth` - Decompression stop depth in meters
- `stop_time` - Decompression stop time in minutes

### Gas Information

- `fractionO2` - Oxygen fraction (0.21 for air)
- `fractionHe` - Helium fraction (0.0 for air, >0 for trimix)

### Tank Data

- `pressure[0]` - Tank 1 pressure in bar
- `pressure[1]` - Tank 2 pressure in bar
- `pressure[2]` - Tank 3 pressure in bar
- `pressure[3]` - Tank 4 pressure in bar

### Consumption Data

- `sac` - Surface Air Consumption in L/min
- `gtr` - Gas Time Remaining in minutes

## Font Override Examples

### System Fonts (macOS)

```yaml
font:
  path: "/System/Library/Fonts/Helvetica.ttc"
  size: 24
  color: "#FFFFFF"
```

### Custom Fonts

```yaml
font:
  path: "./fonts/MyCustomFont.ttf"
  size: 28
  color: "#00BAEF"
```

### Font Properties

- `path` - Full path to font file (.ttf, .ttc, .otf)
- `size` - Font size in pixels
- `color` - Hex color code (e.g., "#FFFFFF" for white)

## Complete Example Template

```yaml
template_name: example-template
width: 800
height: 600
background_color: "#2c2c2c"
background_image: "templates/background.png"
chroma_color: "#00FF00"

default_label_font:
  path: "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
  size: 18
  color: "#00BAEF"

default_data_font:
  path: "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
  size: 36
  color: "#FFFFFF"

units:
  depth: "m"
  pressure: "bar"
  temperature: "C"

items:
  # Static title
  - type: text
    text: "DIVE COMPUTER"
    position: { x: 400, y: 50 }
    font:
      size: 24
      color: "#FFFFFF"

  # Depth with custom precision
  - type: data
    field: depth
    label: "DEPTH"
    label_position: { x: 100, y: 150 }
    data_position: { x: 100, y: 180 }
    precision: 1
    unit: "m"

  # Time display
  - type: data
    field: time
    label: "TIME"
    label_position: { x: 250, y: 150 }
    data_position: { x: 250, y: 180 }

  # Gas mixture display
  - type: data
    compute: "{fractionO2:02%}/{fractionHe:02%}"
    label: "GAS"
    label_position: { x: 400, y: 150 }
    data_position: { x: 400, y: 180 }
    fallback: "21/00"

  # Tank pressure
  - type: data
    field: pressure[0]
    label: "TANK 1"
    label_position: { x: 100, y: 250 }
    data_position: { x: 100, y: 280 }
    unit: "bar"
    precision: 0

  # Temperature
  - type: data
    field: temperature
    label: "TEMP"
    label_position: { x: 250, y: 250 }
    data_position: { x: 250, y: 280 }
    precision: 1
    unit: "°F"
```

## Tips and Best Practices

1. **Test Templates**: Use `--test-template` to preview your template with dummy data
2. **Color Codes**: Always use 6-digit hex codes with # prefix
3. **Positioning**: Plan your layout and test it with `--test-template`, readjust poosition and repeat
4. **Fallback Values**: Provide meaningful fallbacks for optional data fields

## Supported Formats

- **Fonts**: TrueType (.ttf), OpenType (.otf), TrueType Collection (.ttc)
