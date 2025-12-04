# Implementation Tasks

## 1. PyInstaller Configuration

- [x] Add `pyinstaller>=6.0` to `[project.optional-dependencies.build]` in pyproject.toml
- [x] Create PyInstaller spec file for build configuration (if needed for advanced options)
- [x] Test local PyInstaller build on development machine
- [x] Ensure all dependencies (opencv, pillow, pyyaml) are bundled correctly
- [x] Test bundled executable with sample templates and dive logs
- [x] Verify template files, fonts, and resources are included in bundle

## 2. GitHub Actions Workflow

- [x] Create `.github/workflows/build.yml` file
- [x] Configure workflow triggers:
  - [x] Manual workflow dispatch for testing
  - [x] Automatic trigger on push to git tags (e.g., `v*.*.*`)
- [x] Set up Windows build job (runs-on: windows-latest)
  - [x] Install Python 3.13
  - [x] Install dependencies
  - [x] Run PyInstaller
  - [x] Upload Windows `.exe` artifact
- [x] Set up macOS build job (runs-on: macos-latest)
  - [x] Install Python 3.13
  - [x] Install dependencies
  - [x] Run PyInstaller
  - [x] Upload macOS executable artifact
  - [x] Consider universal2 binary or separate Intel/ARM builds
- [x] Set up Linux build job (runs-on: ubuntu-latest)
  - [x] Install Python 3.13
  - [x] Install system dependencies (if needed for opencv)
  - [x] Run PyInstaller
  - [x] Upload Linux executable artifact
- [x] Configure artifact naming: `scuba-overlay-{version}-{platform}`

## 3. Release Automation

- [x] Add GitHub Release creation step to workflow
- [x] Configure release to trigger only on version tags
- [x] Attach all platform binaries to release
- [x] Generate release notes automatically from commits
- [x] Set release title format: `ScubaOverlay v{version}`
- [x] Mark pre-releases appropriately (e.g., beta, rc tags)

## 4. Testing Strategy

- [x] Test manual workflow dispatch before tag-based automation
- [x] Download each platform's binary from workflow artifacts
- [x] Test Windows .exe on Windows machine
- [x] Test macOS binary on Intel and/or Apple Silicon Mac
- [x] Test Linux binary on Ubuntu/Debian system
- [x] Verify all commands work: `--help`, `--test-template`, full video generation
- [x] Test with sample dive logs from different formats (.ssrf, .xml)
- [x] Verify error handling and user-friendly error messages

## 5. Documentation Updates

- [x] Update README.md with "Download" section
  - [x] Add link to GitHub Releases page
  - [x] Provide download instructions for each platform
  - [x] Document how to run the binary (no installation needed)
  - [x] Keep pip installation method documented for developers
- [x] Add section on releases and versioning
- [x] Document the difference between binary and pip install methods
- [x] Add troubleshooting for common binary issues (permissions, security warnings)

## 6. Configuration Updates

- [x] Update `.gitignore`
  - [x] Ignore PyInstaller build directory
  - [x] Ignore `.spec` files (if dynamically generated)
- [ ] Consider adding CHANGELOG.md for release notes

## 7. Optional Enhancements

- [ ] Add code signing for Windows executable (requires certificate)
- [ ] Add notarization for macOS binary (requires Apple Developer account)
- [ ] Create installers (MSI for Windows, DMG for macOS) instead of bare executables
- [ ] Add automated testing workflow separate from build workflow
- [ ] Cache Python dependencies in CI for faster builds

## Notes

- PyInstaller bundles Python interpreter and all dependencies into single executable
- Windows Defender and macOS Gatekeeper may show security warnings for unsigned binaries
- Binary size will be ~100-200MB due to bundled dependencies (opencv, numpy)
- GitHub Actions provides 2000 minutes/month free for public repositories
- Consider using matrix strategy in GitHub Actions to parallelize platform builds
