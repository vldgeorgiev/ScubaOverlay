# Change: Fix CI Binary Build Performance and Compatibility Issues

## Why

The current binary builds have two critical issues that significantly impact user experience:

1. **Slow startup performance**: Binaries take 30 seconds to start on macOS and 10 seconds on Windows, even with just the `--help` flag. This creates a poor user experience and makes the tool feel unresponsive.

2. **macOS architecture mismatch**: The macOS binary built on GitHub Actions cannot run on macOS AMD64 (Intel) systems, failing with "Bad CPU type in executable" error. This makes the macOS binary unusable for a large portion of Mac users still on Intel machines.

These issues undermine the primary goal of providing easy-to-use standalone binaries and need immediate resolution.

## What Changes

### Performance Fix
- **Switch PyInstaller bundling mode** from `--onefile` to `--onedir` to eliminate extraction overhead
- **Update packaging** to use `.zip` archives containing the application directory
- **Add startup optimization flags** to PyInstaller configuration
- **Update spec file** to disable UPX compression (can cause startup delays)

### macOS Architecture Fix
- **Split macOS builds** into separate Intel (x86_64) and Apple Silicon (arm64) binaries
- **Update GitHub Actions workflow** to use explicit architecture targets
- **Add proper asset naming** to distinguish between architectures
- **Apply ad-hoc code signing** to reduce Gatekeeper warnings (free, no Apple Developer account needed)
- **Consider universal2 binary** as future enhancement (requires more complex build process)

## Impact

- **Affected specs**: `ci-cd` (binary build requirements)
- **Affected files**:
  - `.github/workflows/build.yml` → update build strategy for both platforms
  - `scuba-overlay.spec` → add optimization flags and onedir configuration
  - Asset naming scheme changes (e.g., `macos-intel` vs `macos-apple-silicon`)
- **Breaking changes**: None for end users, but binary distribution format changes from single file to zip archive
- **Migration path**: Update documentation to explain archive extraction
- **Benefits**:
  - **30x faster startup on macOS** (30s → ~1s)
  - **10x faster startup on Windows** (10s → ~1s)
  - **macOS Intel compatibility** restored
  - **Better user experience** overall
  - **More maintainable** build process

## Benefits

- Near-instant startup time for all platforms
- Full macOS compatibility (both Intel and Apple Silicon)
- More reliable binary execution
- Improved user satisfaction
- Proper architecture support for Mac users
- Easier debugging (onedir preserves file structure)
