# Design: GitHub CI Pipeline for Standalone Binaries

## Overview

Implement automated build pipeline using GitHub Actions and PyInstaller to create standalone executables for Windows, macOS, and Linux platforms, eliminating the need for users to install Python.

## Technical Decisions

### Build Tool: PyInstaller

**Decision**: Use PyInstaller for creating standalone executables

**Rationale**:
- Most mature and widely-used Python packaging tool for executables
- Excellent cross-platform support (Windows, macOS, Linux)
- Handles complex dependencies like OpenCV, Pillow, NumPy automatically
- Single-file or single-directory bundle options
- Active development and good community support
- Works well with Python 3.13

**Alternatives Considered**:
- **py2exe**: Windows-only, not suitable for multi-platform
- **cx_Freeze**: Less mature dependency detection than PyInstaller
- **Nuitka**: Compiles to C, more complex, slower builds, potential compatibility issues
- **PyOxidizer**: Modern but newer, less proven for complex dependencies like OpenCV

**Configuration Approach**: Start with command-line PyInstaller, add `.spec` file only if needed for advanced customization

### CI Platform: GitHub Actions

**Decision**: Use GitHub Actions for CI/CD pipeline

**Rationale**:
- Native integration with GitHub repository
- Free for public repositories (2000 minutes/month)
- Built-in support for Windows, macOS, and Linux runners
- Matrix builds for parallel execution across platforms
- Easy artifact uploads and GitHub Releases integration
- YAML-based configuration

**Alternatives Considered**:
- **Travis CI**: Less generous free tier, declining popularity
- **CircleCI**: Good but GitHub Actions more integrated
- **AppVeyor**: Windows-focused, less suitable for multi-platform

### Platform Strategy

**Decision**: Build for three platforms with specific configurations

**Windows (x64)**:
- Runner: `windows-latest` (Windows Server)
- Output: `scuba-overlay.exe` single executable
- Bundling: `--onefile` for single .exe
- Considerations: Windows Defender SmartScreen warnings for unsigned binaries

**macOS (Universal)**:
- Runner: `macos-latest` (currently macOS 14)
- Output: `scuba-overlay` executable
- Strategy: Start with x86_64 build (works on both Intel and ARM via Rosetta)
- Future: Consider universal2 binary or separate ARM64 builds
- Considerations: Gatekeeper warnings for non-notarized binaries

**Linux (x64)**:
- Runner: `ubuntu-latest` (Ubuntu 22.04)
- Output: `scuba-overlay` executable
- Bundling: `--onefile` for single binary
- Considerations: Dependency on glibc version (Ubuntu 22.04 = glibc 2.35)

### Workflow Triggers

**Decision**: Support both manual and tag-based automated releases

**Triggers**:
1. **workflow_dispatch**: Manual trigger for testing builds
2. **push tags `v*`**: Automatic release builds on version tags (e.g., `v0.1.0`, `v1.2.3`)

**Rationale**:
- Manual dispatch allows testing before creating official releases
- Tag-based automation ensures consistent release process
- Semantic versioning pattern (`v*.*.*`) is industry standard

### Release Strategy

**Decision**: Automated GitHub Releases with attached binaries

**Process**:
1. Developer creates and pushes git tag: `git tag v0.1.0 && git push origin v0.1.0`
2. GitHub Actions workflow triggers automatically
3. Builds run in parallel for all three platforms
4. Successful builds upload artifacts
5. Release job creates GitHub Release with all binaries attached

**Naming Convention**:
- Windows: `scuba-overlay-v{version}-windows-x64.exe`
- macOS: `scuba-overlay-v{version}-macos-x64`
- Linux: `scuba-overlay-v{version}-linux-x64`

**Release Notes**: Auto-generated from commits between tags

### PyInstaller Configuration

**Decision**: Minimal configuration, add spec file only if needed

**Initial Approach**: Command-line PyInstaller without .spec file
```bash
pyinstaller --onefile --name scuba-overlay main.py
```

**Spec File (if needed for customization)**:
- Include data files (templates/*.yaml, templates/*.png)
- Hidden imports (if PyInstaller misses any)
- Exclude unnecessary modules to reduce size
- Icon file for executable

**Bundle Mode**:
- `--onefile`: Single executable (easier distribution)
- Alternative: `--onedir` if single file has issues (creates folder)

### Dependency Handling

**Decision**: Let PyInstaller auto-detect dependencies, add hidden imports if needed

**Expected Bundled Dependencies**:
- Python 3.13 runtime
- opencv-python (cv2)
- pillow (PIL)
- pyyaml
- numpy (opencv dependency)
- All standard library modules

**Data Files**:
- Template files from `templates/` directory (may need explicit inclusion)
- Background images (PNG files)

**Size Estimate**: 100-200 MB per executable (due to OpenCV, NumPy)

### Security and Code Signing

**Decision**: Start without code signing, document warnings, add later if needed

**Windows**:
- Unsigned .exe will trigger SmartScreen warning
- Users must click "More info" → "Run anyway"
- Code signing requires EV certificate (~$300-500/year)
- Document workaround in README

**macOS**:
- Unsigned binary will show "unidentified developer" warning
- Users must right-click → Open (or use `xattr -d com.apple.quarantine`)
- Notarization requires Apple Developer account ($99/year)
- Document workaround in README

**Linux**:
- No signing infrastructure typically needed
- Mark executable with `chmod +x` (document in README)

**Future Enhancement**: Add code signing when project gains sponsorship/funding

### Testing Strategy

**Decision**: Manual testing of binaries, automated testing in future

**Testing Process**:
1. Trigger workflow manually via workflow_dispatch
2. Download artifacts from workflow run
3. Test each platform binary:
   - Basic functionality: `--help`, `--version`
   - Template test: `--test-template`
   - Full video generation with sample logs
   - Error handling and user messages
4. Verify no Python installation needed
5. Test on clean machines without Python

**Future**: Add automated end-to-end tests in separate workflow

### Build Optimization

**Decision**: Use GitHub Actions caching for faster builds

**Caching Strategy**:
- Cache Python dependencies (pip cache)
- Cache PyInstaller build cache
- Estimated speedup: 2-3 minutes per platform

**Build Time Estimates**:
- Fresh build: ~10-15 minutes per platform
- Cached build: ~5-8 minutes per platform
- Total (3 platforms in parallel): ~10-15 minutes

## File Structure

```
.github/
  workflows/
    build.yml          # Main build and release workflow

# Optional, create only if needed:
pyinstaller.spec       # Custom PyInstaller configuration
.pyinstaller-cache/    # PyInstaller cache (gitignored)
```

## PyInstaller Command Examples

**Minimal (start here)**:
```bash
pyinstaller --onefile --name scuba-overlay main.py
```

**With data files (if templates not auto-detected)**:
```bash
pyinstaller --onefile --name scuba-overlay \
  --add-data "templates:templates" \
  main.py
```

**With icon (nice touch)**:
```bash
pyinstaller --onefile --name scuba-overlay \
  --icon=icon.ico \
  --add-data "templates:templates" \
  main.py
```

## GitHub Actions Workflow Structure

```yaml
name: Build Binaries

on:
  workflow_dispatch:  # Manual trigger
  push:
    tags:
      - 'v*'          # Trigger on version tags

jobs:
  build:
    strategy:
      matrix:
        os: [windows-latest, macos-latest, ubuntu-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          pip install .
          pip install pyinstaller
      - name: Build with PyInstaller
        run: pyinstaller --onefile --name scuba-overlay main.py
      - name: Upload artifact
        uses: actions/upload-artifact@v4

  release:
    needs: build
    if: startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
      - name: Create Release
        uses: softprops/action-gh-release@v1
```

## Rollback Plan

If binary distribution has issues:
1. Binaries are optional - pip install method remains primary
2. Remove problematic platform from build matrix
3. Disable auto-release, keep manual workflow_dispatch
4. Document known issues in README

## Future Enhancements

After initial implementation:
1. Add code signing for Windows and macOS
2. Create installers (MSI, DMG) instead of bare executables
3. Add automated E2E testing in CI
4. Optimize binary size (exclude unused modules)
5. Add update mechanism for auto-updating binaries
6. Create portable versions (no installation needed)
7. Add Windows ARM64 and macOS ARM64 native builds
