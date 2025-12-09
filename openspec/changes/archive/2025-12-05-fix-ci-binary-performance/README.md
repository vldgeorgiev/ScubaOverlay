# Fix: CI Binary Build Performance and Compatibility

## Summary

This openspec fix addresses two critical issues with the CI-built binaries:

1. **Slow startup performance**: 30s on macOS, 10s on Windows
2. **macOS architecture mismatch**: "Bad CPU type in executable" error on Intel Macs

## Root Causes

- **Slow startup**: PyInstaller `--onefile` mode extracts 150-200MB to temp directory on every run
- **Architecture issue**: GitHub's `macos-latest` runner now uses ARM64, producing Apple Silicon-only binaries

## Solutions

### Performance Fix
- Switch from `--onefile` to `--onedir` mode (eliminates extraction overhead)
- Disable UPX compression in spec file
- Distribute as zip archives containing application directory
- **Result**: 10-30x faster startup (<2 seconds vs 10-30 seconds)

### Architecture Fix
- Split macOS builds: `macos-15` (Intel) + `macos-latest` (Apple Silicon)
- Update asset naming: `macos-intel` and `macos-apple-silicon`
- Provide clear download instructions for each architecture
- **Result**: Both Intel and ARM Macs work natively

## Files Created

- `proposal.md` - Change rationale and impact
- `design.md` - Technical decisions and implementation details
- `tasks.md` - Step-by-step implementation checklist
- `specs/ci-cd/spec.md` - Updated requirements and scenarios

## Implementation Priority

**High Priority** - These are critical user-facing issues that significantly impact user experience and product usability. The macOS Intel incompatibility makes the binary completely unusable for a large segment of users.

## Next Steps

1. Review and approve the fix proposal
2. Implement PyInstaller spec file changes
3. Update GitHub Actions workflow
4. Test builds locally and in CI
5. Create test release to validate fixes
6. Update documentation
7. Deploy to production release

## Trade-offs

**Pros**:
- 10-30x faster startup time
- Full macOS compatibility (Intel + Apple Silicon)
- Better debuggability (directory structure visible)
- More reliable binary execution

**Cons**:
- Users must extract zip instead of running single file
- Slightly larger distribution (directory + zip overhead)
- One additional macOS build job in CI (4 total platforms instead of 3)

The performance and compatibility improvements far outweigh the minor distribution inconvenience.
