# Design: Python Packaging Modernization

## Overview

Migrate from legacy `requirements.txt` to modern `pyproject.toml` (PEP 621) and update to Python 3.13.

## Technical Decisions

### Python Version: 3.13

**Decision**: Set minimum Python version to 3.13 (latest stable as of December 2025)

**Rationale**:
- Python 3.13 includes significant performance improvements (JIT compiler, optimized bytecode)
- Better error messages and debugging experience
- Current project uses modern syntax (e.g., `tuple[int, int]`) compatible with 3.13
- No blocking dependencies on older Python versions

**Alternatives Considered**:
- Python 3.12: More conservative, but misses 3.13 performance gains
- Python 3.11: Current minimum; would miss 2+ years of improvements

**Migration**: Users on 3.11/3.12 must upgrade Python installation

### Build Backend: setuptools

**Decision**: Use setuptools as the build backend in pyproject.toml

**Rationale**:
- Most widely supported and stable build backend
- No complex build requirements (pure Python project)
- Excellent compatibility with pip and virtual environments
- Default choice for simple projects without special needs

**Alternatives Considered**:
- **Poetry**: Full dependency resolver but adds complexity; overkill for simple project
- **PDM**: Modern but less universal support
- **Flit**: Lightweight but limited features for future growth
- **Hatchling**: Modern but setuptools more proven for compatibility

**Configuration**:
```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"
```

### Package Name: scuba-overlay

**Decision**: Use `scuba-overlay` as the package name (lowercase with hyphen)

**Rationale**:
- PyPI convention: lowercase with hyphens
- Python module import remains `main` (entry point)
- Distinguishes package name from module structure
- Reserves name for potential PyPI publishing

**Import Structure**: No changes; modules imported as before (`from parser import ...`)

### CLI Entry Point

**Decision**: Create `scuba-overlay` console script entry point

**Rationale**:
- Enables installation as system command: `scuba-overlay --help`
- Cleaner than requiring `python main.py`
- Standard practice for Python CLI tools
- Maintains backward compatibility (users can still run `python main.py`)

**Configuration**:
```toml
[project.scripts]
scuba-overlay = "main:main"
```

### Dependency Pinning Strategy

**Decision**: Use minimum version constraints without upper bounds

**Rationale**:
- `opencv-python>=4.8.0` - Avoid breaking changes from older versions
- `pillow>=10.0.0` - Security fixes in recent versions
- `pyyaml>=6.0` - Stable API, recent versions safe
- No upper bounds to avoid dependency conflicts

**Reasoning**: This is an application, not a library. Users install specific versions in their environment. Upper bounds would cause conflicts when dependencies update.

### Optional Dependencies

**Decision**: Define `[project.optional-dependencies]` for development tools

**Groups**:
- `dev`: Development tools (not included in this change, reserved for future)

**Rationale**: Prepares structure for adding testing/linting tools without requiring them for end users

### Metadata Completeness

**Decision**: Include full project metadata even without PyPI publishing plans

**Fields**:
- `name`, `version`, `description`, `readme`, `requires-python`
- `license`: MIT (from existing LICENSE file)
- `authors`: From git history or project owner
- `keywords`: ["scuba", "diving", "video", "overlay", "chroma-key"]
- `classifiers`: Python versions, license, topic

**Rationale**:
- Documents project professionally
- Prepares for potential future PyPI distribution
- Standard metadata useful for tools and discoverability

## File Changes

### New Files

**pyproject.toml**:
```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "scuba-overlay"
version = "0.1.0"
description = "Generate chroma key-ready dive computer overlay videos from dive logs"
readme = "Readme.md"
requires-python = ">=3.13"
license = {text = "MIT"}
authors = [
    {name = "Vladimir", email = "your@email.com"}
]
keywords = ["scuba", "diving", "video", "overlay", "chroma-key", "dive-computer"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.13",
    "Topic :: Multimedia :: Video",
]

dependencies = [
    "opencv-python>=4.8.0",
    "pillow>=10.0.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = []  # Reserved for future development tools

[project.scripts]
scuba-overlay = "main:main"

[project.urls]
Homepage = "https://github.com/YOUR_USERNAME/ScubaOverlay"
Repository = "https://github.com/YOUR_USERNAME/ScubaOverlay"
Issues = "https://github.com/YOUR_USERNAME/ScubaOverlay/issues"
```

### Removed Files

- `requirements.txt` - Fully replaced by pyproject.toml dependencies

### Modified Files

- `.gitignore` - Add build artifacts
- `README.md` - Update installation instructions
- `openspec/project.md` - Update Python version and conventions

## Testing Strategy

1. **Clean Environment Test**: Create fresh Python 3.13 venv and install package
2. **Editable Install Test**: Test `pip install -e .` for development workflow
3. **CLI Entry Point Test**: Verify `scuba-overlay --help` works after installation
4. **Functional Tests**: Run existing sample commands to ensure no regression
5. **Build Test**: Run `python -m build` to verify package builds correctly

## Rollback Plan

If issues arise:
1. Revert commit removing `requirements.txt`
2. Users can continue using `pip install -r requirements.txt`
3. pyproject.toml can coexist temporarily for transition period

## Future Enhancements

After this change is stable:
- Add `[project.optional-dependencies.dev]` with pytest, black, ruff
- Consider publishing to PyPI
- Add GitHub Actions workflow for automated builds
- Add version management tooling (bump2version or similar)
