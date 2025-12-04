# packaging Specification

## Purpose
TBD - created by archiving change modernize-python-packaging. Update Purpose after archive.
## Requirements
### Requirement: Python 3.13 Minimum Version

The system SHALL require Python 3.13 or higher for installation and execution.

#### Scenario: Install on Python 3.13+
- **GIVEN** a system with Python 3.13 or higher installed
- **WHEN** user installs the package with `pip install .`
- **THEN** installation succeeds without version errors

#### Scenario: Reject installation on Python 3.12 or lower
- **GIVEN** a system with Python 3.12 or lower
- **WHEN** user attempts to install with `pip install .`
- **THEN** pip reports version incompatibility error
- **AND** installation is blocked

### Requirement: PEP 621 Project Configuration

The system SHALL use `pyproject.toml` following PEP 621 specification for all project metadata and dependencies.

#### Scenario: Valid pyproject.toml structure
- **GIVEN** the project root directory
- **WHEN** user inspects `pyproject.toml`
- **THEN** file contains `[project]` table with name, version, description
- **AND** file contains `[build-system]` table with setuptools backend
- **AND** file contains `dependencies` list with opencv-python, pillow, pyyaml

#### Scenario: Build package from pyproject.toml
- **GIVEN** a Python 3.13+ environment with build tools
- **WHEN** user runs `python -m build`
- **THEN** source distribution (.tar.gz) is created in `dist/`
- **AND** wheel distribution (.whl) is created in `dist/`
- **AND** no errors occur during build

### Requirement: Standard Package Installation

The system SHALL support standard pip installation using pyproject.toml without requiring requirements.txt.

#### Scenario: Standard installation
- **GIVEN** a clean Python 3.13+ virtual environment
- **WHEN** user runs `pip install .` from project root
- **THEN** package installs with all dependencies
- **AND** `scuba-overlay` command becomes available
- **AND** no requirements.txt file is needed

#### Scenario: Editable installation for development
- **GIVEN** a Python 3.13+ development environment
- **WHEN** user runs `pip install -e .` from project root
- **THEN** package installs in editable mode
- **AND** code changes are immediately reflected without reinstall
- **AND** all dependencies are installed

### Requirement: CLI Entry Point

The system SHALL provide a `scuba-overlay` command-line entry point that invokes the main function.

#### Scenario: Run via entry point
- **GIVEN** package is installed via pip
- **WHEN** user runs `scuba-overlay --help` in terminal
- **THEN** help text displays showing available arguments
- **AND** command functions identically to `python main.py --help`

#### Scenario: Entry point accepts arguments
- **GIVEN** package is installed and sample files exist
- **WHEN** user runs `scuba-overlay --template templates/perdix-ai-oc-tech.yaml --test-template`
- **THEN** test template image is generated
- **AND** output matches `python main.py` execution

### Requirement: Dependency Specification

The system SHALL declare runtime dependencies with minimum version constraints in pyproject.toml.

#### Scenario: Runtime dependencies defined
- **GIVEN** pyproject.toml file
- **WHEN** user inspects `[project] dependencies` section
- **THEN** opencv-python is listed with minimum version
- **AND** pillow is listed with minimum version
- **AND** pyyaml is listed with minimum version
- **AND** no upper version bounds are specified

#### Scenario: Dependencies install automatically
- **GIVEN** a clean Python environment without opencv, pillow, or pyyaml
- **WHEN** user runs `pip install .`
- **THEN** all three dependencies are automatically installed
- **AND** package functions correctly

### Requirement: Project Metadata

The system SHALL include complete project metadata for discoverability and potential distribution.

#### Scenario: Essential metadata present
- **GIVEN** pyproject.toml file
- **WHEN** user inspects `[project]` section
- **THEN** name field is set to "scuba-overlay"
- **AND** version field is defined (semantic versioning)
- **AND** description field describes the project purpose
- **AND** readme field points to "Readme.md"
- **AND** license field specifies GPL-3.0-or-later
- **AND** requires-python field specifies ">=3.13"

#### Scenario: PyPI classifiers included
- **GIVEN** pyproject.toml file
- **WHEN** user inspects `[project] classifiers`
- **THEN** Python version classifiers include 3.13
- **AND** Topic classifiers include Multimedia/Video
- **AND** Development Status is appropriate

### Requirement: Build System Configuration

The system SHALL use setuptools as the build backend with modern configuration.

#### Scenario: Build system specified
- **GIVEN** pyproject.toml file
- **WHEN** user inspects `[build-system]` section
- **THEN** requires includes setuptools version 68 or higher
- **AND** requires includes wheel
- **AND** build-backend is set to "setuptools.build_meta"

#### Scenario: Compatible with build tools
- **GIVEN** Python 3.13+ environment
- **WHEN** user installs `build` package and runs `python -m build`
- **THEN** build succeeds without warnings
- **AND** both sdist and wheel are produced

### Requirement: No requirements.txt File

The system SHALL NOT include a requirements.txt file; all dependencies SHALL be managed through pyproject.toml.

#### Scenario: requirements.txt removed
- **GIVEN** the project root directory
- **WHEN** user lists files
- **THEN** requirements.txt file does not exist
- **AND** pyproject.toml file exists

#### Scenario: Documentation updated
- **GIVEN** README.md file
- **WHEN** user reads installation instructions
- **THEN** instructions use `pip install .` command
- **AND** no reference to requirements.txt exists
- **AND** Python 3.13+ requirement is clearly stated

### Requirement: Optional Build Dependencies

The system SHALL support optional dependency groups for development and build tooling.

#### Scenario: Build dependencies group
- **GIVEN** pyproject.toml file
- **WHEN** user inspects `[project.optional-dependencies]`
- **THEN** a `build` group exists for build tooling
- **AND** developers can install with `pip install .[build]`

#### Scenario: Dev dependencies group
- **GIVEN** pyproject.toml file
- **WHEN** user inspects `[project.optional-dependencies]`
- **THEN** a `dev` group exists (may be empty initially)
- **AND** structure supports future testing/linting tools

### Requirement: Updated Documentation

The system SHALL provide updated installation documentation reflecting the new packaging approach.

#### Scenario: README installation section updated
- **GIVEN** README.md file
- **WHEN** user reads Requirements section
- **THEN** Python 3.13+ is specified as minimum version
- **AND** installation command is `pip install .` (not requirements.txt)
- **AND** editable installation option is documented

#### Scenario: Project conventions documented
- **GIVEN** openspec/project.md file
- **WHEN** user reads Tech Stack section
- **THEN** Python 3.13+ is listed (not 3.11+)
- **AND** pyproject.toml is mentioned in conventions
- **AND** PEP 621 compliance is noted

