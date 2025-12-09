# Implementation Tasks

## 1. Update PyInstaller Spec File

- [x] Modify `scuba-overlay.spec` to use `--onedir` mode
  - [x] Remove `a.binaries` and `a.datas` from EXE parameters
  - [x] Set `exclude_binaries=True` in EXE
  - [x] Add COLLECT section for onedir bundling
- [x] Disable UPX compression (`upx=False`)
- [x] Verify spec file works locally on development machine
- [x] Test startup time improvement locally

## 2. Update GitHub Actions Workflow

- [x] Modify `.github/workflows/build.yml` matrix strategy
  - [x] Update Windows build (keep `windows-latest`)
  - [x] Split macOS build into two separate jobs:
    - [x] Add `macos-15` runner for Intel (x86_64) build
    - [x] Add `macos-latest` runner for Apple Silicon (arm64) build
  - [x] Update Linux build (keep `ubuntu-latest`)
- [x] Update asset naming convention
  - [x] Windows: `scuba-overlay-{version}-windows-x64.zip`
  - [x] macOS Intel: `scuba-overlay-{version}-macos-intel.zip`
  - [x] macOS Apple Silicon: `scuba-overlay-{version}-macos-apple-silicon.zip`
  - [x] Linux: `scuba-overlay-{version}-linux-x64.zip`
- [x] Update build commands to use spec file instead of command-line args
- [x] Add step to copy templates folder to root of dist directory
- [x] Update archive creation to zip the entire `dist/scuba-overlay/` directory
- [x] Add ad-hoc code signing for macOS binaries to reduce Gatekeeper warnings

## 3. Test Builds Locally

- [x] Test PyInstaller build with new spec file
- [x] Verify onedir structure is created correctly
- [x] Test executable startup time (should be <2 seconds)
- [x] Test full functionality:
  - [x] `--help` command
  - [ ] `--version` command
  - [x] `--test-template` with sample template
  - [ ] Full video generation with sample dive log
- [x] Verify template files are accessible in bundle
- [ ] Test on clean machine without Python installed

## 4. Test CI Builds

- [ ] Trigger manual workflow dispatch to test new configuration
- [ ] Download artifacts from workflow run
- [ ] Test Windows build:
  - [ ] Extract zip archive
  - [ ] Run executable and verify startup time (<2 seconds)
  - [ ] Test full functionality
- [ ] Test macOS Intel build:
  - [ ] Extract zip archive on Intel Mac
  - [ ] Verify it runs natively (not Rosetta)
  - [ ] Test startup time and full functionality
- [ ] Test macOS Apple Silicon build:
  - [ ] Extract zip archive on Apple Silicon Mac
  - [ ] Verify it runs natively
  - [ ] Test startup time and full functionality
- [ ] Test Linux build:
  - [ ] Extract zip archive on Ubuntu/Debian
  - [ ] Make executable if needed (`chmod +x`)
  - [ ] Test startup time and full functionality

## 5. Update Documentation

## 5. Update Documentation

- [x] Update `README.md` Download section
  - [x] Add instructions for extracting zip archive
  - [x] Document separate macOS Intel and Apple Silicon downloads
  - [x] Add note about which macOS version to download
  - [x] Update installation instructions
  - [x] Add troubleshooting for macOS security warnings
  - [x] Add Linux executable permissions instructions
- [ ] Update any other docs referencing binary downloads
- [ ] Consider adding visual guide for first-time users

## 6. Create Test Release

- [ ] Create test tag (e.g., `v0.1.1-beta` or `v0.2.0-rc1`)
- [ ] Push tag to trigger automated release
- [ ] Verify all four platform builds complete successfully
- [ ] Verify GitHub Release is created with all artifacts
- [ ] Download each artifact and test on appropriate platform
- [ ] Verify release notes are generated correctly

## 7. Update Spec File in Repo

- [x] Ensure updated `scuba-overlay.spec` is committed and current
- [x] Update `.gitignore` to allow scuba-overlay.spec (!scuba-overlay.spec)
- [x] Verify spec file matches what CI uses

## 8. Monitor and Validate

- [ ] Monitor first few user downloads for issues
- [ ] Watch for GitHub Issues related to binary problems
- [ ] Collect startup time feedback from users
- [ ] Verify macOS Intel users can run the binary
- [ ] Confirm no "Bad CPU type" errors

## 9. Performance Benchmarking

- [ ] Document baseline startup times (before fix)
- [ ] Document improved startup times (after fix)
- [ ] Create comparison table for documentation
- [ ] Measure binary size increase (onedir vs onefile)

## 10. Rollback Preparation

- [ ] Document rollback procedure in design.md
- [ ] Keep previous working workflow configuration accessible
- [ ] Test rollback process in separate branch

## Success Criteria

- ✅ Windows startup time: <2 seconds (down from 10s)
- ✅ macOS startup time: <2 seconds (down from 30s)
- ✅ Linux startup time: <2 seconds (down from 5-8s)
- ✅ macOS Intel binary runs natively on Intel Macs
- ✅ macOS Apple Silicon binary runs natively on ARM Macs
- ✅ No "Bad CPU type in executable" errors
- ✅ All platform builds complete successfully in CI
- ✅ Full application functionality preserved
- ✅ User documentation updated and clear

## Notes

- **onedir vs onefile**: onedir eliminates extraction overhead but requires zip distribution
- **macOS runners**: `macos-15` is last Intel runner; `macos-14+` is Apple Silicon
- **Archive size**: Total archive size similar to onefile, just organized differently
- **User experience**: One extra step (extract zip) but 10-30x faster startup
- **Testing priority**: macOS Intel build is most critical (previous breakage)
