# Change: Modernize Python Packaging with pyproject.toml

## Why

The project currently uses Python 3.11+ with a legacy `requirements.txt` file for dependency management. Modern Python projects (PEP 517/518/621) use `pyproject.toml` as the standard configuration file, which provides:
- Single source of truth for project metadata, dependencies, and build configuration
- Better integration with modern Python tooling (pip, poetry, PDM, uv)
- Support for optional dependencies and development tools
- Standardized package metadata for potential distribution on PyPI

Additionally, updating to the latest stable Python version (3.13 as of December 2025) ensures access to the newest performance improvements and language features.

## What Changes

- **Update minimum Python version** from 3.11 to 3.13
- **Replace `requirements.txt`** with `pyproject.toml` using PEP 621 standard
- **Define project metadata** (name, version, description, author, license)
- **Specify dependencies** with version constraints
- **Add optional dependency groups** (e.g., `[dev]` for development tools)
- **Update documentation** (README.md, installation instructions)
- **Update project.md** to reflect new packaging conventions

## Impact

- **Affected specs**: `packaging` (new capability)
- **Affected files**:
  - `requirements.txt` → removed, replaced by `pyproject.toml`
  - `README.md` → update installation instructions
  - `openspec/project.md` → update tech stack and conventions
  - `.gitignore` → add `dist/`, `*.egg-info`, `build/` entries
- **Breaking changes**: Users must have Python 3.13+ installed
- **Migration path**: 
  - Existing Python 3.11/3.12 users must upgrade to Python 3.13+
  - Installation command changes from `pip install -r requirements.txt` to `pip install -e .` (editable mode) or `pip install .`
- **Backward compatibility**: No runtime API changes; purely packaging-related

## Benefits

- Aligns with modern Python packaging standards (PEP 621)
- Easier maintenance with centralized configuration
- Better tooling support for dependency management
- Prepares project for potential PyPI distribution
- Access to Python 3.13 performance improvements and features
