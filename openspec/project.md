# Project Context

## Purpose

ScubaOverlay is a cross-platform Python command-line tool that generates chroma key-ready dive computer overlay videos from dive log files. The tool allows divers to composite depth, time, tank pressures, temperature, and decompression stop information directly into their dive footage for post-production video editing.

The project aims to support multiple dive log formats (Subsurface .ssrf and Shearwater XML) and provide flexible, customizable overlays through YAML templates without requiring code changes.

## Tech Stack

- **Python 3.13+** (primary language)
- **OpenCV (cv2)** - video generation and frame manipulation
- **Pillow (PIL)** - image rendering, text drawing, font handling
- **PyYAML** - YAML template configuration parsing
- **XML parsing** (xml.etree.ElementTree) - dive log parsing
- **PEP 621 pyproject.toml** - modern package configuration

## Distribution

- **pip installation**: Standard Python package installation via `pip install .`
- **Standalone binaries**: Cross-platform executables built with PyInstaller (Windows, macOS, Linux)
- **GitHub Releases**: Automated binary builds via GitHub Actions on version tags
- **No Python required**: End users can download and run binaries without Python installation

## Project Conventions

### Code Style

- **Type hints**: Use type annotations extensively (e.g., `Optional[float]`, `List[DiveSample]`, `Dict[str, Any]`)
- **Naming conventions**:
  - Snake_case for functions, variables, and module names
  - PascalCase for class names (e.g., `DiveSample`, `DiveParser`, `SubsurfaceParser`)
  - Private/internal functions prefixed with underscore (e.g., `_build_converter`, `_compile_template`)
  - Constants in UPPER_SNAKE_CASE with `_DEF_` prefix (e.g., `_DEF_M_TO_FT`, `_DEF_BAR_TO_PSI`)
- **Dataclasses**: Use `@dataclass` for data containers (e.g., `DiveSample`)
- **Error handling**: Custom exception hierarchy with descriptive error classes (e.g., `DiveLogError`, `TemplateError`, `NoDiveDataError`)
- **Docstrings**: Class-level docstrings present; function docstrings light or minimal
- **Packaging**: PEP 621 `pyproject.toml` for all project metadata and dependencies

### Architecture Patterns

- **Parser pattern**: Abstract base class (`DiveParser`) with format-specific implementations (`SubsurfaceParser`, `ShearwaterParser`)
  - `ShearwaterParser` accepts optional `date_format` parameter for regional date format overrides
- **Factory pattern**: `get_parser()` dispatches to appropriate parser based on file extension and configuration
- **Separation of concerns**: Clear module boundaries:
  - `parser.py` - dive log parsing and data extraction
  - `template.py` - YAML template loading
  - `overlay.py` - video/image rendering logic
  - `main.py` - CLI entry point and argument handling
  - `font_utils.py` - font fallback and selection
  - `utils.py` - shared utilities
- **Compiled template optimization**: Pre-process templates into `_CompiledTemplate` objects to avoid repeated work during video generation
- **Unit conversion**: Internal canonical units (meters, bar, Celsius) with runtime conversion to imperial units when requested
- **Automated builds**: GitHub Actions workflow for multi-platform binary builds using PyInstaller
- **Matrix builds**: Parallel CI jobs for Windows, macOS, and Linux platforms

### Testing Strategy

- No formal test suite currently in place (no test files found)
- Manual testing via `--test-template` flag for quick layout validation
- Sample dive logs provided in `samples/` directory for integration testing
- `.gitignore` includes pytest-related entries suggesting future test infrastructure
- **CI/CD testing**: Automated binary builds tested on Windows, macOS, and Linux via GitHub Actions

### Git Workflow

- Standard `.gitignore` for Python projects (excludes `__pycache__`, venv, `.pyc`, etc.)
- Ignores macOS `.DS_Store` files
- **Release process**: Version tags (`v*.*.*`) trigger automated binary builds via GitHub Actions
- **Semantic versioning**: Tags follow `vMAJOR.MINOR.PATCH` format
- **GitHub Releases**: Automated release creation with binary artifacts for download

## Domain Context

### Scuba Diving Terminology

- **Dive log**: Electronic record from dive computer containing depth, time, and sensor data sampled throughout a dive
- **NDL** (No Decompression Limit): Maximum time in minutes a diver can stay at current depth without required decompression stops
- **TTS** (Time to Surface): Total time in minutes to safely return to surface including decompression stops
- **Decompression stop**: Mandatory safety stop at specific depth for specified time to off-gas nitrogen
- **Tank pressure**: Breathing gas pressure, typically measured in bar (metric) or PSI (imperial)
- **SAC** (Surface Air Consumption): Rate of gas consumption in liters per minute
- **GTR** (Gas Time Remaining): Estimated time in seconds before running out of breathing gas
- **PPO2** (Partial Pressure of Oxygen): Oxygen pressure in bar; critical for rebreather/CCR diving
- **CNS** (Central Nervous System toxicity): Percentage measure of oxygen toxicity exposure
- **Sensors**: Multiple oxygen sensors (`ppo2_sensors[0]`, `ppo2_sensors[1]`, `ppo2_sensors[2]`) used in closed-circuit rebreather diving

### Dive Log Formats

- **Subsurface (.ssrf)**: XML format from popular open-source dive log software
  - Uses ISO 8601 date format: `YYYY-MM-DD HH:MM:SS`
- **Shearwater (.xml)**: XML format from Shearwater dive computers (Perdix, Teric, etc.)
  - Uses regional date/time formats that vary by dive computer settings
  - Parser automatically uses system locale for date/time parsing
  - Common formats: `M/D/Y h:mm:ss AM/PM` (US), `D/M/Y HH:mm:ss` (EU)
  - Manual override available via `--shearwater-date-format` CLI parameter
- Data stored in metric units internally (meters, bar, Celsius)

### Video Production Context

- **Chroma key**: Technique to composite overlay onto video by replacing specific color (typically bright green `#00FF00`)
- Overlays designed to be composited in video editing software (DaVinci Resolve, Final Cut Pro, Premiere, etc.)
- Frame rate typically 10-30 fps for overlay video
- Overlay resolution independent of final video resolution

## Important Constraints

- **Single dive limitation**: Currently only supports dive logs containing one dive; multiple dives in a file will raise `MultipleDivesError`
- **Python version**: Requires Python 3.13+ (uses modern type hint syntax like `tuple[int, int]` and benefits from performance improvements)
- **Font availability**: Cross-platform font selection with fallback mechanism (Arial → Liberation Sans → DejaVu Sans)
- **Unit system**: Internal data always stored in metric; conversion to imperial only for display
- **Sample interpolation**: Dive computers sample at varying intervals; tool must handle missing/sparse data and forward-fill values
- **Multi-tank support**: Supports multiple tank pressures via indexed fields (`pressure[0]`, `pressure[1]`)
- **Multi-sensor support**: Supports multiple PPO2 sensors via indexed fields (`ppo2_sensors[0]`, `ppo2_sensors[1]`, `ppo2_sensors[2]`)

## External Dependencies

### Runtime Dependencies

- **opencv-python**: Core video encoding/frame generation
- **Pillow**: Image manipulation and text rendering
- **pyyaml**: YAML template parsing
- All dependencies are Python packages installable via pip (no external services or APIs)
- Font files expected to be system-installed (no bundled fonts)

### Build Dependencies

- **PyInstaller**: Creates standalone executables for distribution
- **GitHub Actions**: CI/CD platform for automated builds (Windows, macOS, Linux runners)
- Build dependencies are optional and only needed for creating binary releases

