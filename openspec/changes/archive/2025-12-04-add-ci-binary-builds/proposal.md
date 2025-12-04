# Change: Add GitHub CI Pipeline for Standalone Binary Builds

## Why

Users currently need Python 3.13+ installed to use ScubaOverlay, which creates a barrier to entry for non-technical users. Many divers who want to create video overlays may not have Python installed or be comfortable with command-line Python environments. Providing standalone executables for Windows, macOS, and Linux eliminates this friction and makes the tool accessible to a wider audience.

Additionally, automated CI builds ensure:
- Consistent, reproducible builds across platforms
- Automated testing before releases
- Easy distribution via GitHub Releases
- Version-tagged releases with downloadable artifacts

## What Changes

- **Add GitHub Actions workflow** (`.github/workflows/build.yml`) for multi-platform builds
- **Integrate PyInstaller** to create standalone executables
- **Build for three platforms**:
  - Windows (x64) - `.exe` executable
  - macOS (x64 and ARM64/Apple Silicon) - Universal binary or separate builds
  - Linux (x64) - Executable binary
- **Automated release creation** on git tags
- **Upload build artifacts** to GitHub Releases
- **Add build configuration** for PyInstaller spec file
- **Update documentation** with download and usage instructions for binaries

## Impact

- **Affected specs**: `ci-cd` (new capability)
- **Affected files**:
  - `.github/workflows/build.yml` → new CI workflow
  - `build.spec` or `pyinstaller.spec` → PyInstaller configuration (if needed)
  - `README.md` → add binary download and usage instructions
  - `.gitignore` → add PyInstaller build artifacts (`dist/`, `build/`, `*.spec`)
- **Breaking changes**: None - existing pip installation method remains supported
- **Migration path**: Not applicable - this adds a new distribution method
- **Dependencies added**:
  - `pyinstaller` (dev dependency for building)
  - GitHub Actions runners (Windows, macOS, Ubuntu)
- **Benefits**:
  - Users can download and run without Python installation
  - Single-file executables for easy distribution
  - Automated builds on every release tag
  - Professional distribution method

## Benefits

- Dramatically lowers barrier to entry for non-technical users
- No Python installation required
- Single-file download and run experience
- Cross-platform support with native executables
- Automated quality assurance through CI
- Professional release process with version management
- Easier to share with diving community
