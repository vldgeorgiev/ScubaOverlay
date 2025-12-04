# ci-cd Specification

## Purpose
TBD - created by archiving change add-ci-binary-builds. Update Purpose after archive.
## Requirements
### Requirement: Multi-Platform Binary Builds

The system SHALL automatically build standalone executables for Windows, macOS, and Linux platforms.

#### Scenario: Windows executable build
- **GIVEN** GitHub Actions workflow is triggered
- **WHEN** Windows build job executes
- **THEN** a single `.exe` file is created for Windows x64
- **AND** the executable includes Python runtime and all dependencies
- **AND** the executable runs without Python installation

#### Scenario: macOS executable build
- **GIVEN** GitHub Actions workflow is triggered
- **WHEN** macOS build job executes
- **THEN** a macOS executable is created for x64 architecture
- **AND** the executable includes Python runtime and all dependencies
- **AND** the executable runs on both Intel and ARM Macs

#### Scenario: Linux executable build
- **GIVEN** GitHub Actions workflow is triggered
- **WHEN** Linux build job executes
- **THEN** a Linux executable is created for x64 architecture
- **AND** the executable includes Python runtime and all dependencies
- **AND** the executable runs on Ubuntu 22.04+ and compatible distributions

### Requirement: Automated Release Creation

The system SHALL automatically create GitHub Releases with binary attachments when version tags are pushed.

#### Scenario: Tag-triggered release
- **GIVEN** a developer pushes a git tag matching `v*.*.*` pattern
- **WHEN** GitHub Actions workflow completes successfully
- **THEN** a GitHub Release is created with the tag version
- **AND** all platform binaries are attached to the release
- **AND** release notes are auto-generated from commits

#### Scenario: Manual build without release
- **GIVEN** a developer triggers workflow manually via workflow_dispatch
- **WHEN** builds complete successfully
- **THEN** artifacts are available for download from workflow run
- **AND** no GitHub Release is created
- **AND** binaries can be tested before official release

### Requirement: PyInstaller Integration

The system SHALL use PyInstaller to bundle the application into standalone executables.

#### Scenario: Dependencies bundled correctly
- **GIVEN** PyInstaller build process runs
- **WHEN** executable is created
- **THEN** opencv-python is bundled and functional
- **AND** pillow is bundled and functional
- **AND** pyyaml is bundled and functional
- **AND** all Python standard library dependencies are included

#### Scenario: Data files included
- **GIVEN** application uses template files and resources
- **WHEN** PyInstaller bundles the application
- **THEN** template YAML files are included in the bundle
- **AND** template PNG images are included in the bundle
- **AND** application can locate and load these files at runtime

#### Scenario: Single-file executable
- **GIVEN** PyInstaller runs with `--onefile` option
- **WHEN** build completes
- **THEN** output is a single executable file (not a directory)
- **AND** all dependencies are embedded in the single file
- **AND** no external DLLs or libraries are required

### Requirement: GitHub Actions Workflow

The system SHALL implement a GitHub Actions workflow for automated builds and releases.

#### Scenario: Workflow configuration exists
- **GIVEN** the repository root
- **WHEN** user inspects `.github/workflows/` directory
- **THEN** a `build.yml` (or similar) workflow file exists
- **AND** workflow defines jobs for Windows, macOS, and Linux builds
- **AND** workflow includes release job for tagged commits

#### Scenario: Parallel platform builds
- **GIVEN** workflow is triggered
- **WHEN** build jobs execute
- **THEN** Windows, macOS, and Linux builds run in parallel
- **AND** matrix strategy is used to avoid duplication
- **AND** total build time is minimized

#### Scenario: Build artifacts uploaded
- **GIVEN** a build job completes successfully
- **WHEN** artifact upload step executes
- **THEN** executable is uploaded with platform-specific naming
- **AND** artifact is available for download for 90 days
- **AND** artifact name includes version and platform identifier

### Requirement: Executable Naming Convention

The system SHALL use consistent naming for executable files across platforms.

#### Scenario: Version in filename
- **GIVEN** a release build for version `v0.1.0`
- **WHEN** executables are created
- **THEN** Windows binary is named `scuba-overlay-v0.1.0-windows-x64.exe`
- **AND** macOS binary is named `scuba-overlay-v0.1.0-macos-x64`
- **AND** Linux binary is named `scuba-overlay-v0.1.0-linux-x64`

#### Scenario: Platform identifier in filename
- **GIVEN** executables for different platforms
- **WHEN** user views release assets
- **THEN** each filename clearly indicates target platform
- **AND** architecture (x64) is specified
- **AND** naming prevents confusion between platforms

### Requirement: Binary Functionality

The system SHALL ensure standalone binaries provide full application functionality without Python installation.

#### Scenario: Help command works
- **GIVEN** a user downloads and runs a platform binary
- **WHEN** user executes `./scuba-overlay --help` (or `.exe --help`)
- **THEN** help text is displayed
- **AND** all command-line options are shown
- **AND** no Python installation is required

#### Scenario: Template testing works
- **GIVEN** a user has a template YAML file
- **WHEN** user runs `./scuba-overlay --template path/to/template.yaml --test-template`
- **THEN** test PNG image is generated
- **AND** all template rendering functions correctly
- **AND** no Python installation is required

#### Scenario: Video generation works
- **GIVEN** a user has a dive log and template
- **WHEN** user runs full video generation command
- **THEN** overlay video is created successfully
- **AND** all dive log parsing functions correctly
- **AND** video encoding with OpenCV works
- **AND** no Python installation is required

### Requirement: Build Configuration

The system SHALL include PyInstaller build configuration in the project.

#### Scenario: PyInstaller in dev dependencies
- **GIVEN** pyproject.toml file
- **WHEN** user inspects `[project.optional-dependencies]`
- **THEN** a `build` group includes `pyinstaller>=6.0`
- **AND** developers can install with `pip install .[build]`

#### Scenario: Gitignore updated for build artifacts
- **GIVEN** .gitignore file
- **WHEN** PyInstaller builds run locally
- **THEN** `build/` directory is ignored
- **AND** `dist/` directory is ignored (if used for binaries separate from pip dist)
- **AND** `*.spec` files are ignored (if auto-generated)

### Requirement: Documentation for Binary Users

The system SHALL provide documentation for downloading and using standalone binaries.

#### Scenario: Download instructions in README
- **GIVEN** README.md file
- **WHEN** user reads installation section
- **THEN** binary download option is documented
- **AND** link to GitHub Releases page is provided
- **AND** instructions for each platform are clear

#### Scenario: Binary usage documented
- **GIVEN** a user downloads a binary
- **WHEN** user reads README documentation
- **THEN** how to run the binary is explained
- **AND** no Python installation mentioned as requirement
- **AND** permission/security warnings are documented (macOS Gatekeeper, Windows SmartScreen)

#### Scenario: Troubleshooting security warnings
- **GIVEN** binaries are unsigned
- **WHEN** users encounter platform security warnings
- **THEN** README documents how to bypass Windows SmartScreen
- **AND** README documents how to allow macOS unsigned binaries
- **AND** README documents Linux executable permissions

### Requirement: Build Reproducibility

The system SHALL ensure consistent and reproducible builds across runs.

#### Scenario: Python version pinned
- **GIVEN** GitHub Actions workflow
- **WHEN** Python setup step runs
- **THEN** Python 3.13 is specified explicitly
- **AND** same version is used across all platform builds
- **AND** builds are consistent across workflow runs

#### Scenario: Dependency versions locked
- **GIVEN** build environment
- **WHEN** dependencies are installed
- **THEN** pyproject.toml dependency constraints are respected
- **AND** pip installs consistent versions
- **AND** build output is reproducible

### Requirement: Build Performance

The system SHALL optimize build times using caching and parallelization.

#### Scenario: Dependency caching
- **GIVEN** GitHub Actions workflow with caching enabled
- **WHEN** workflow runs after initial run
- **THEN** Python dependencies are restored from cache
- **AND** build time is reduced by 50% or more
- **AND** cache hit is logged in workflow output

#### Scenario: Parallel builds
- **GIVEN** three platform builds needed
- **WHEN** workflow executes
- **THEN** all platform jobs run simultaneously
- **AND** total workflow time is close to single longest job
- **AND** workflow completes in under 20 minutes

