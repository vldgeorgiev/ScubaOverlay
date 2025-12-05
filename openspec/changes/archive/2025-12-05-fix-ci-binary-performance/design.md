# Design: Fix CI Binary Build Performance and Compatibility

## Overview

Resolve two critical issues with the current PyInstaller-based binary builds: slow startup times (30s macOS, 10s Windows) and macOS architecture incompatibility preventing execution on Intel Macs.

## Root Cause Analysis

### Slow Startup Issue

**Current Configuration**: PyInstaller `--onefile` mode
- Creates a self-extracting archive
- At runtime, extracts all files to temporary directory
- Runs application from temp location
- Large dependencies (OpenCV ~100MB, NumPy, etc.) cause slow extraction
- Extraction happens on every execution

**Why It's Slow**:
- OpenCV bundle: ~100-150 MB of shared libraries
- Pillow, NumPy, and other dependencies: ~30-50 MB
- Total extraction: 150-200 MB every startup
- macOS has additional security scanning overhead (Gatekeeper)
- Windows Defender real-time scanning adds overhead

### macOS Architecture Issue

**Current Configuration**: `macos-latest` runner (macOS 14 on ARM64)
- GitHub Actions `macos-latest` now runs on Apple Silicon (M1/M2)
- PyInstaller builds native ARM64 binary by default
- Intel Macs (x86_64) cannot run ARM64 binaries
- Error: "Bad CPU type in executable"

**Why It's Broken**:
- No explicit architecture target specified in workflow
- Default build produces ARM64-only binary
- Intel Mac users represent significant portion of user base
- Need separate builds for each architecture

## Technical Decisions

### Decision 1: Switch from --onefile to --onedir

**Decision**: Use PyInstaller `--onedir` mode instead of `--onefile`

**Rationale**:
- **Startup time**: Near-instant (no extraction needed)
- **File structure**: Application bundle in directory, no temporary extraction
- **Debugging**: Easier to inspect contents and dependencies
- **Updates**: Can update individual files if needed
- **Size on disk**: Same total size, just organized in folder

**Trade-offs**:
- **Distribution**: Need to zip the directory for download
- **User experience**: Users extract zip, then run executable inside folder
- **File count**: Multiple files instead of single executable

**Alternative Considered**: Keep `--onefile` with optimization
- UPX compression disabled (can help but not enough)
- Excluding modules (limited impact, still 100+ MB)
- Lazy loading (not supported by PyInstaller for native libraries)
- **Rejected**: Fundamental extraction overhead cannot be eliminated in onefile mode

### Decision 2: Disable UPX Compression

**Decision**: Set `upx=False` in PyInstaller spec file

**Rationale**:
- UPX (Ultimate Packer for Executables) can slow down startup
- Modern systems have fast storage, compression overhead not worth it
- Some antiviruses flag UPX-compressed executables
- Transparent decompression adds CPU overhead on every launch

**Impact**:
- Slightly larger binary size (~10-20% increase)
- Faster startup (no decompression needed)
- Better antivirus compatibility

### Decision 3: Split macOS Builds by Architecture

**Decision**: Create separate builds for Intel (x86_64) and Apple Silicon (arm64)

**Rationale**:
- **Compatibility**: Ensures both architectures work natively
- **Performance**: Native execution faster than Rosetta 2 emulation
- **User clarity**: Clear which binary to download
- **GitHub Actions**: Can specify runner architecture

**Build Strategy**:
- **Intel build**: Use `macos-13` runner (last Intel runner)
- **Apple Silicon build**: Use `macos-latest` (ARM64 runner)
- **Universal binary**: Not pursued initially (requires more complex build, larger size)

**Alternative Considered**: Universal2 binary
- Single binary with both architectures embedded
- Larger size (~2x)
- More complex build process (requires cross-compilation)
- **Deferred**: Can add later if user demand justifies complexity

### Decision 4: Update Asset Naming Convention

**Decision**: Use explicit architecture in asset names

**New Naming**:
- Windows: `scuba-overlay-{version}-windows-x64.zip`
- macOS Intel: `scuba-overlay-{version}-macos-intel.zip`
- macOS Apple Silicon: `scuba-overlay-{version}-macos-apple-silicon.zip`
- Linux: `scuba-overlay-{version}-linux-x64.zip`

**Rationale**:
- Clear which binary to download
- Prevents confusion and support requests
- Standard industry practice (see Chrome, VS Code, etc.)

### Decision 5: Update Packaging Format

**Decision**: Distribute as `.zip` archives containing application directory

**Structure**:
```
scuba-overlay-v0.2.0-macos-intel.zip
└── scuba-overlay/
    ├── scuba-overlay (main executable)
    ├── _internal/
    │   ├── libopencv_*.dylib
    │   ├── numpy/
    │   ├── PIL/
    │   └── ... (other dependencies)
    └── templates/
        ├── perdix-ai-cc-tech.yaml
        ├── perdix-ai-oc-tech.yaml
        └── ... (template files)
```

**User Workflow**:
1. Download zip file
2. Extract to desired location
3. Run `scuba-overlay/scuba-overlay --template templates/perdix-ai-cc-tech.yaml`

**Note**: Templates folder is copied to the root level during CI build (after PyInstaller completes) to ensure users can access it with relative paths like `templates/filename.yaml`.

**Alternative Considered**: Keep single file with documentation warning
- Users still experience 30s startup delay
- **Rejected**: Poor user experience unacceptable

### Decision 6: macOS Gatekeeper Handling

**Decision**: Provide user instructions to remove quarantine attribute instead of code signing

**Rationale**:
- **Simplicity**: No Apple Developer account required ($99/year saved)
- **No CI complexity**: Avoids certificate management, keychain setup, secret rotation
- **User control**: Simple one-line command that users can verify and understand
- **Transparency**: Users explicitly choose to trust the binary
- **Standard practice**: Common approach for open-source CLI tools

**User Instructions**:
After downloading and extracting the macOS binary:
```bash
xattr -dr com.apple.quarantine scuba-overlay
```

This removes the quarantine attribute that macOS applies to downloaded files, preventing Gatekeeper errors.

**Trade-offs**:
- Users must run one extra command after download
- First run may take 30-45 seconds due to Gatekeeper verification (subsequent runs are instant)
- Binary is unsigned (expected for free/open-source tools)

**Alternative Considered**: Apple Developer code signing + notarization
- Requires $99/year Apple Developer membership
- Complex CI setup with certificates and secrets
- Provides seamless user experience (no extra steps)
- **Rejected**: Too complex for current project stage, can add later if needed## Implementation Details

### PyInstaller Spec File Updates

```python
# scuba-overlay.spec
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('templates', 'templates')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],                    # Changed: empty (onedir mode)
    exclude_binaries=True,  # Changed: exclude from EXE
    name='scuba-overlay',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,             # Changed: disable UPX
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(         # Added: COLLECT for onedir
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='scuba-overlay',
)
```

### GitHub Actions Workflow Updates

**Matrix Strategy**:
```yaml
matrix:
  include:
    - os: windows-latest
      artifact_name: scuba-overlay
      asset_name: scuba-overlay-${{ github.ref_name }}-windows-x64
      
    - os: macos-13  # Intel
      artifact_name: scuba-overlay
      asset_name: scuba-overlay-${{ github.ref_name }}-macos-intel
      arch: x86_64
      
    - os: macos-latest  # Apple Silicon
      artifact_name: scuba-overlay
      asset_name: scuba-overlay-${{ github.ref_name }}-macos-apple-silicon
      arch: arm64
      
    - os: ubuntu-latest
      artifact_name: scuba-overlay
      asset_name: scuba-overlay-${{ github.ref_name }}-linux-x64
```

**Build Step Changes**:
```yaml
- name: Build with PyInstaller
  run: |
    pyinstaller scuba-overlay.spec
    
- name: Copy templates to root (Windows)
  if: runner.os == 'Windows'
  shell: bash
  run: |
    cp -r templates dist/scuba-overlay/
    
- name: Copy templates to root (Unix)
  if: runner.os != 'Windows'
  run: |
    cp -r templates dist/scuba-overlay/
    
- name: Sign macOS binary (ad-hoc)
  if: runner.os == 'macOS'
  run: |
    codesign --sign - --force --deep dist/scuba-overlay/scuba-overlay
    codesign --verify --verbose dist/scuba-overlay/scuba-overlay
    
- name: Create release archive
  shell: bash
  run: |
    cd dist
    if [ "${{ runner.os }}" == "Windows" ]; then
      7z a ../${{ matrix.asset_name }}.zip scuba-overlay/
    else
      zip -r ../${{ matrix.asset_name }}.zip scuba-overlay/
    fi
```

**Note**: The templates directory is copied after PyInstaller completes because PyInstaller's onedir mode places data files in the `_internal` subdirectory, but we want templates at the root level for easier user access. Ad-hoc code signing is applied to macOS binaries to reduce Gatekeeper warnings.

### Performance Expectations

**Before (onefile)**:
- macOS: 30 seconds startup
- Windows: 10 seconds startup
- Linux: 5-8 seconds startup

**After (onedir)**:
- macOS: <1 second startup
- Windows: <1 second startup
- Linux: <1 second startup

**Improvement**: 10-30x faster startup across all platforms

### Testing Strategy

**Manual Testing Required**:
1. **macOS Intel**: Test on actual Intel Mac (not Rosetta emulation)
2. **macOS Apple Silicon**: Test on M1/M2/M3 Mac
3. **Windows**: Test startup time with `--help` flag
4. **Linux**: Test on Ubuntu 22.04+

**Test Cases**:
```bash
# Startup time test
time ./scuba-overlay --help

# Full functionality test
./scuba-overlay --test-template templates/perdix-ai-cc-tech.yaml

# Video generation test
./scuba-overlay samples/dive426.ssrf templates/perdix-ai-cc-tech.yaml -o test-output.mp4
```

**Success Criteria**:
- All platforms start in <2 seconds
- macOS Intel binary runs on Intel Mac natively
- macOS Apple Silicon binary runs on ARM Mac natively
- Full functionality preserved (video generation works)
- No regressions in error handling or output quality

## Documentation Updates

### README.md Updates

**Download Section**:
```markdown
## Download

Pre-built binaries are available for Windows, macOS, and Linux:

1. Go to the [Releases](https://github.com/user/ScubaOverlay/releases) page
2. Download the appropriate zip file for your platform:
   - **Windows**: `scuba-overlay-vX.X.X-windows-x64.zip`
   - **macOS (Intel)**: `scuba-overlay-vX.X.X-macos-intel.zip`
   - **macOS (Apple Silicon)**: `scuba-overlay-vX.X.X-macos-apple-silicon.zip`
   - **Linux**: `scuba-overlay-vX.X.X-linux-x64.zip`
3. Extract the zip file to a folder
4. Run the `scuba-overlay` executable inside the extracted folder

**Note**: No Python installation required for pre-built binaries!

### macOS Users
If you see a security warning, right-click the executable and choose "Open" the first time.

### Linux Users
You may need to make the file executable:
```bash
chmod +x scuba-overlay/scuba-overlay
```
```

**Installation Options Section**:
```markdown
## Installation Options

### Option 1: Download Pre-Built Binary (Recommended)
No Python required. Download from [Releases](https://github.com/user/ScubaOverlay/releases).

### Option 2: Install with pip (For Developers)
Requires Python 3.13+:
```bash
git clone https://github.com/user/ScubaOverlay.git
cd ScubaOverlay
pip install .
```
```

## Rollback Plan

If issues arise with onedir builds:
1. Revert `.github/workflows/build.yml` to previous commit
2. Revert `scuba-overlay.spec` to onefile configuration
3. Document slow startup as known limitation
4. Continue investigating alternatives (Nuitka, static linking, etc.)

## Future Enhancements

- **Universal2 binary for macOS**: Single binary supporting both architectures
- **Code signing**: Eliminate security warnings on macOS/Windows
- **Application bundles**: `.app` for macOS, `.AppImage` for Linux
- **Installer packages**: MSI for Windows, DMG for macOS
- **Further optimization**: Profile and optimize import time in Python code
