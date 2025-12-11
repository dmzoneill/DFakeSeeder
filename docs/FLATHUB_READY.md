# Flathub Submission - Ready to Publish

**Status**: ✅ All automated steps completed - Ready for GitHub release and Flathub submission

**Date**: 2025-12-11

## What We Completed

### 1. ✅ Flatpak Build Tools Installation
- Installed `flatpak-builder` and dependencies
- Installed GNOME 49 Platform and SDK (latest stable, non-EOL)
- Configured Flathub repository

### 2. ✅ Package Dependencies Updated
Updated all Python package URLs to current versions:
- requests 2.32.5
- certifi 2025.11.12
- idna 3.11
- charset-normalizer 3.4.4
- urllib3 2.6.1
- typer 0.20.0
- click 8.3.1
- typing-extensions 4.15.0
- shellingham 1.5.4
- rich 14.2.0
- markdown-it-py 4.0.0
- mdurl 0.1.2
- pygments 2.19.2
- watchdog 6.0.0
- bencodepy 0.9.5

### 3. ✅ Runtime Updated to GNOME 49
- Changed from GNOME 47 (end-of-life) to GNOME 49 (latest stable)
- File: `ie.fio.dfakeseeder.json` line 4
- Tested and confirmed working

### 4. ✅ Metadata Validation
- **AppStream metadata**: ✅ Validated with no errors
- **Desktop file**: ✅ Validated with no warnings
- Fixed category specification (removed "Utility" main category)

### 5. ✅ Local Flatpak Build
- Successfully built from source
- Successfully installed locally
- Installed as: `ie.fio.dfakeseeder` version 0.0.52

## What You Need to Do

### Step 1: Create GitHub Release

**This is the ONLY blocking step before Flathub submission.**

1. Commit the updated files:
```bash
cd /home/daoneill/src/DFakeSeeder

# Stage the updated Flatpak files
git add ie.fio.dfakeseeder.json
git add ie.fio.dfakeseeder.appdata.xml
git add ie.fio.dfakeseeder.desktop

# Commit
git commit -m "chore(flatpak): update to GNOME 49 runtime and current package URLs

- Update runtime from GNOME 47 (EOL) to GNOME 49 (latest stable)
- Update all Python package URLs to current versions
- Fix desktop file categories (remove duplicate main category)
- Validate all metadata files

All Flatpak prerequisites completed and tested locally."

# Push to GitHub
git push origin main
```

2. Create a git tag for the release:
```bash
git tag -a v0.0.52 -m "Release version 0.0.52 - Flathub ready"
git push origin v0.0.52
```

3. Create the GitHub release:
   - Go to: https://github.com/dmzoneill/DFakeSeeder/releases/new
   - Tag: `v0.0.52`
   - Title: `v0.0.52 - Flathub Release`
   - Description: See suggested text below
   - Click "Publish release"

**Suggested Release Description:**
```markdown
## D' Fake Seeder v0.0.52 - Flathub Release

This release includes Flatpak packaging and is ready for Flathub submission.

### Features
- Multi-Torrent Support with individual configuration
- Full HTTP and UDP tracker compatibility (BEP-003)
- Advanced P2P implementation with connection management
- Real-time monitoring and performance metrics
- System tray integration with D-Bus IPC
- 21 language support with runtime switching
- GTK4 modern user interface

### Flatpak Support
- GNOME 49 runtime (latest stable)
- Complete desktop integration
- Validated AppStream metadata
- Tested and working locally

### Installation

#### From PyPI
```bash
pip install d-fake-seeder
```

#### From Flatpak (after Flathub approval)
```bash
flatpak install flathub ie.fio.dfakeseeder
```

### Changes in This Release
- Updated Flatpak manifest to GNOME 49 runtime
- Updated all Python package dependencies
- Validated and optimized metadata files
- Ready for Flathub submission
```

### Step 2: Get Release Tarball SHA256

After creating the GitHub release, get the tarball SHA256:

```bash
cd /home/daoneill/src/DFakeSeeder
wget https://github.com/dmzoneill/DFakeSeeder/archive/refs/tags/v0.0.52.tar.gz
sha256sum v0.0.52.tar.gz
```

**Save this SHA256 hash** - you'll need it for the next step.

### Step 3: Update Manifest for Release Tarball

Edit `ie.fio.dfakeseeder.json` and replace the `dfakeseeder` module sources (lines 147-151):

**Current:**
```json
"sources": [
    {
        "type": "dir",
        "path": "."
    }
]
```

**Change to:**
```json
"sources": [
    {
        "type": "archive",
        "url": "https://github.com/dmzoneill/DFakeSeeder/archive/refs/tags/v0.0.52.tar.gz",
        "sha256": "YOUR_SHA256_FROM_STEP2_HERE"
    }
]
```

### Step 4: Test Build with Release Tarball

```bash
cd /home/daoneill/src/DFakeSeeder
flatpak-builder --user --install --force-clean build-dir ie.fio.dfakeseeder.json
flatpak run ie.fio.dfakeseeder
```

Verify everything works correctly with the tarball source.

### Step 5: Submit to Flathub

Follow the instructions in `docs/FLATHUB_SUBMISSION.md`:

```bash
# Fork flathub/flathub on GitHub (if not already done)
# Clone your fork
git clone https://github.com/YOUR_USERNAME/flathub.git
cd flathub
git checkout new-pr

# Create app directory
mkdir -p ie.fio.dfakeseeder
cd ie.fio.dfakeseeder

# Copy files
cp ~/src/DFakeSeeder/ie.fio.dfakeseeder.json .
cp ~/src/DFakeSeeder/ie.fio.dfakeseeder.appdata.xml .
cp ~/src/DFakeSeeder/ie.fio.dfakeseeder.desktop .

# Test build from Flathub fork location
cd ..
flatpak-builder --user --install --force-clean build-dir ie.fio.dfakeseeder/ie.fio.dfakeseeder.json

# If successful, commit and push
git add ie.fio.dfakeseeder/
git commit -m "Add ie.fio.dfakeseeder"
git push origin new-pr

# Create PR on GitHub targeting flathub/flathub:new-pr
```

## Files Ready for Submission

All files are ready and validated:

- ✅ `ie.fio.dfakeseeder.json` - Flatpak manifest (GNOME 49, current package URLs)
- ✅ `ie.fio.dfakeseeder.appdata.xml` - AppStream metadata (validated)
- ✅ `ie.fio.dfakeseeder.desktop` - Desktop file (validated, no warnings)
- ✅ Icon: `d_fake_seeder/components/images/dfakeseeder.png` (256x256)

## Testing Checklist

After Flathub submission, verify:

- [ ] Application launches without errors
- [ ] GUI displays correctly
- [ ] Network connectivity works (tracker communication)
- [ ] File operations work (loading torrents)
- [ ] Configuration saves properly
- [ ] Desktop notifications appear
- [ ] All 21 languages are available
- [ ] Settings persistence across restarts

## Support Resources

- **Flathub Submission Guide**: `docs/FLATHUB_SUBMISSION.md` (comprehensive guide)
- **Flathub Discourse**: https://discourse.flathub.org/
- **Flatpak Documentation**: https://docs.flatpak.org/
- **AppStream Specification**: https://www.freedesktop.org/software/appstream/docs/

## Timeline

1. **Now**: Create GitHub release (Step 1)
2. **~5 minutes**: Get SHA256 and update manifest (Steps 2-3)
3. **~5 minutes**: Test build with tarball (Step 4)
4. **~10 minutes**: Submit to Flathub (Step 5)
5. **1-2 weeks**: Wait for Flathub review (volunteers, response times vary)
6. **Upon approval**: Your app appears on Flathub within 24 hours

## What Happens After Submission

1. Automated checks run (manifest validation, AppStream validation, build test)
2. Volunteer reviewers examine your submission
3. Reviewers may request changes or ask questions
4. Once approved, you get a dedicated repository: `flathub/ie.fio.dfakeseeder`
5. You can publish updates by pushing to that repository

## Common Review Comments to Expect

- ✅ We've already addressed most common issues:
  - Using stable release tarball (you'll do in Step 3)
  - Correct permissions (already optimized)
  - Valid AppStream metadata (already validated)
  - Proper icon size (256x256 provided)
  - Non-EOL runtime (GNOME 49)

Reviewers are helpful and the process is straightforward!

---

**Ready to proceed?** Start with Step 1 (Create GitHub Release)!
