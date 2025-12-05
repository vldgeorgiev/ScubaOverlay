# ci-cd Specification Updates

## ADDED Requirements

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

## MODIFIED Requirements

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

### Requirement: Executable Naming Convention

The system SHALL use clear, architecture-specific naming for all binary artifacts.

#### Scenario: Asset naming includes architecture
- **GIVEN** binary builds complete successfully
- **WHEN** artifacts are uploaded to GitHub Release
- **THEN** Windows artifact is named `scuba-overlay-{version}-windows-x64.zip`
- **AND** macOS Intel artifact is named `scuba-overlay-{version}-macos-intel.zip`
- **AND** macOS Apple Silicon artifact is named `scuba-overlay-{version}-macos-apple-silicon.zip`
- **AND** Linux artifact is named `scuba-overlay-{version}-linux-x64.zip`

### Requirement: GitHub Actions Workflow

The system SHALL implement a GitHub Actions workflow with architecture-specific builds.

#### Scenario: Separate macOS architecture builds
- **GIVEN** workflow is triggered
- **WHEN** macOS build jobs execute
- **THEN** Intel build runs on `macos-13` runner
- **AND** Apple Silicon build runs on `macos-latest` runner
- **AND** both builds produce architecture-specific artifacts
- **AND** builds run in parallel with Windows and Linux builds

## Performance Benchmarks

### Before Optimization (onefile mode)
- Windows startup: ~10 seconds
- macOS startup: ~30 seconds
- Linux startup: ~5-8 seconds

### After Optimization (onedir mode)
- Windows startup: <2 seconds (5-10x improvement)
- macOS startup: <2 seconds (15-30x improvement)
- Linux startup: <2 seconds (3-5x improvement)

## Rationale

The switch from onefile to onedir mode eliminates the runtime extraction overhead that was causing slow startup times. While this requires distributing binaries as zip archives instead of single executables, the dramatic performance improvement (10-30x faster) significantly outweighs the minor inconvenience of extracting a zip file.

The architecture-specific macOS builds ensure proper compatibility across both Intel and Apple Silicon Macs, preventing the "Bad CPU type" error that made the previous binary unusable on Intel Macs.
