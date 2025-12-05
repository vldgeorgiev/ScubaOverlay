# ci-cd Specification

## Purpose
TBD - created by archiving change add-ci-binary-builds. Update Purpose after archive.
## Requirements
### Requirement: Multi-Platform Binary Builds

The system SHALL automatically build standalone executables for Windows, macOS (Intel), macOS (Apple Silicon), and Linux platforms.

#### Scenario: macOS Intel executable build (Updated)
- **GIVEN** GitHub Actions workflow is triggered
- **WHEN** macOS Intel build job executes using `macos-13` runner
- **THEN** a macOS executable is created for x86_64 architecture
- **AND** the executable includes Python runtime and all dependencies
- **AND** the executable runs natively on Intel Macs without Rosetta
- **AND** binary is packaged as zip archive

#### Scenario: macOS Apple Silicon executable build (New)
- **GIVEN** GitHub Actions workflow is triggered
- **WHEN** macOS Apple Silicon build job executes using `macos-latest` runner
- **THEN** a macOS executable is created for ARM64 architecture
- **AND** the executable includes Python runtime and all dependencies
- **AND** the executable runs natively on Apple Silicon Macs
- **AND** binary is packaged as zip archive

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

The system SHALL implement a GitHub Actions workflow with architecture-specific builds.

#### Scenario: Separate macOS architecture builds
- **GIVEN** workflow is triggered
- **WHEN** macOS build jobs execute
- **THEN** Intel build runs on `macos-13` runner
- **AND** Apple Silicon build runs on `macos-latest` runner
- **AND** both builds produce architecture-specific artifacts
- **AND** builds run in parallel with Windows and Linux builds

### Requirement: Executable Naming Convention

The system SHALL use clear, architecture-specific naming for all binary artifacts.

#### Scenario: Asset naming includes architecture
- **GIVEN** binary builds complete successfully
- **WHEN** artifacts are uploaded to GitHub Release
- **THEN** Windows artifact is named `scuba-overlay-{version}-windows-x64.zip`
- **AND** macOS Intel artifact is named `scuba-overlay-{version}-macos-intel.zip`
- **AND** macOS Apple Silicon artifact is named `scuba-overlay-{version}-macos-apple-silicon.zip`
- **AND** Linux artifact is named `scuba-overlay-{version}-linux-x64.zip`

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

### Requirement: Fast Binary Startup Performance

The system SHALL provide binaries with near-instant startup times across all platforms.

#### Scenario: Windows binary starts quickly
- **GIVEN** a user downloads the Windows binary
- **WHEN** user runs `scuba-overlay.exe --help`
- **THEN** the command completes in less than 2 seconds
- **AND** no extraction or unpacking delay occurs
- **AND** full functionality is immediately available

#### Scenario: macOS binary starts quickly
- **GIVEN** a user downloads the macOS binary
- **WHEN** user runs `./scuba-overlay --help`
- **THEN** the command completes in less than 2 seconds
- **AND** no extraction or unpacking delay occurs
- **AND** performance is consistent across repeated executions

#### Scenario: Linux binary starts quickly
- **GIVEN** a user downloads the Linux binary
- **WHEN** user runs `./scuba-overlay --help`
- **THEN** the command completes in less than 2 seconds
- **AND** no extraction or unpacking delay occurs

### Requirement: Multi-Architecture macOS Support

The system SHALL provide separate native binaries for both Intel and Apple Silicon Macs.

#### Scenario: Intel Mac binary compatibility
- **GIVEN** a user with an Intel-based Mac
- **WHEN** user downloads the macOS Intel binary
- **THEN** the binary runs natively on x86_64 architecture
- **AND** no "Bad CPU type in executable" error occurs
- **AND** no Rosetta 2 emulation is required
- **AND** performance is optimal for Intel hardware

#### Scenario: Apple Silicon Mac binary compatibility
- **GIVEN** a user with an Apple Silicon Mac (M1/M2/M3)
- **WHEN** user downloads the macOS Apple Silicon binary
- **THEN** the binary runs natively on ARM64 architecture
- **AND** no Rosetta 2 emulation is required
- **AND** performance is optimal for Apple Silicon hardware

#### Scenario: Clear architecture identification
- **GIVEN** a user visits the GitHub Releases page
- **WHEN** user views available downloads
- **THEN** macOS Intel and Apple Silicon binaries are clearly distinguished
- **AND** asset names include architecture identifier
- **AND** documentation explains which binary to download

### Requirement: Directory-Based Binary Distribution

The system SHALL distribute binaries as directory bundles packaged in zip archives.

#### Scenario: Windows directory bundle
- **GIVEN** PyInstaller builds with onedir mode
- **WHEN** Windows build completes
- **THEN** output is a directory containing executable and dependencies
- **AND** directory is packaged as a zip archive
- **AND** user extracts zip and runs executable from folder

#### Scenario: macOS directory bundle
- **GIVEN** PyInstaller builds with onedir mode
- **WHEN** macOS build completes
- **THEN** output is a directory containing executable and dependencies
- **AND** directory is packaged as a zip archive
- **AND** bundle structure allows immediate execution without extraction overhead

#### Scenario: Linux directory bundle
- **GIVEN** PyInstaller builds with onedir mode
- **WHEN** Linux build completes
- **THEN** output is a directory containing executable and dependencies
- **AND** directory is packaged as a zip archive
- **AND** executable permissions are preserved

### Requirement: Optimized PyInstaller Configuration

The system SHALL use optimized PyInstaller settings to maximize startup performance.

#### Scenario: UPX compression disabled
- **GIVEN** PyInstaller spec file configuration
- **WHEN** executable is built
- **THEN** UPX compression is disabled (upx=False)
- **AND** no runtime decompression overhead exists
- **AND** startup time is minimized

#### Scenario: Onedir bundling mode
- **GIVEN** PyInstaller spec file configuration
- **WHEN** executable is built
- **THEN** onedir mode is used instead of onefile
- **AND** COLLECT section bundles dependencies in directory
- **AND** no runtime extraction to temporary directory occurs

#### Scenario: Dependencies immediately accessible
- **GIVEN** binary bundle in onedir mode
- **WHEN** application starts
- **THEN** all dependencies are directly accessible from bundle directory
- **AND** no file copying or extraction needed
- **AND** OpenCV, Pillow, NumPy load instantly

