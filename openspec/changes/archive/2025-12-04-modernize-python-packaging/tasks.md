# Implementation Tasks

## 1. Create pyproject.toml

- [x] Create `pyproject.toml` with PEP 621 project metadata
- [x] Define project name: `scuba-overlay` (PyPI-friendly)
- [x] Set version: `0.1.0` (initial semantic version)
- [x] Add project description from README
- [x] Specify Python version requirement: `>=3.13`
- [x] List runtime dependencies (opencv-python, pillow, pyyaml)
- [x] Add optional `[dev]` dependencies (pytest, black, ruff, etc. if needed in future)
- [x] Configure `[project.scripts]` entry point for CLI: `scuba-overlay = main:main`
- [x] Add `[build-system]` section using setuptools backend

## 2. Update Documentation

- [x] Update README.md installation section
  - [x] Change Python requirement to 3.13+
  - [x] Replace `pip install -r requirements.txt` with `pip install .`
  - [x] Add editable install option: `pip install -e .` for development
  - [x] Update Windows and macOS/Linux installation instructions
- [x] Update `openspec/project.md`
  - [x] Change Tech Stack: Python 3.11+ → Python 3.13+
  - [x] Add packaging convention: Uses PEP 621 pyproject.toml
  - [x] Update constraints section about Python version

## 3. Update Configuration Files

- [x] Update `.gitignore`
  - [x] Add `dist/` directory
  - [x] Add `*.egg-info` files
  - [x] Add `build/` directory
- [x] Remove `requirements.txt` file (after pyproject.toml is validated)

## 4. Testing and Validation

- [x] Validate pyproject.toml syntax: `python -m build --sdist --wheel .` (requires `build` package)
- [x] Test installation in clean virtual environment with Python 3.13
- [x] Test editable installation: `pip install -e .`
- [x] Verify CLI entry point works: `scuba-overlay --help`
- [x] Test all existing functionality with sample dive logs
- [x] Verify `--test-template` flag still works

## 5. Documentation Updates

- [x] Add migration guide for existing users in README or separate MIGRATION.md
- [x] Document new installation method
- [x] Note Python 3.13 requirement clearly

## Notes

- Keep existing functionality unchanged; this is purely a packaging modernization
- Consider adding package description for future PyPI publishing
- pyproject.toml should be the single source of truth for dependencies
