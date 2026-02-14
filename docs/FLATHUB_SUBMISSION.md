# Flathub Submission Guide for D' Fake Seeder

This guide documents the complete process for submitting D' Fake Seeder to Flathub.

## Overview

Flathub is the central repository for Flatpak applications. This guide covers preparing, testing, and submitting the application for publication.

## Prerequisites

### Required Tools

```bash
# Fedora/RHEL
sudo dnf install flatpak flatpak-builder appstream

# Debian/Ubuntu
sudo apt install flatpak flatpak-builder appstream-util

# Add Flathub repository
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
```

### Required Knowledge

- Basic Git operations (fork, clone, commit, push, pull request)
- Understanding of Flatpak concepts (runtime, SDK, finish-args)
- Familiarity with AppStream metadata format

## Files Created for Flathub

### 1. Flatpak Manifest: `ie.fio.dfakeseeder.flatpak.json`

**Location**: `/home/daoneill/src/DFakeSeeder/ie.fio.dfakeseeder.flatpak.json`

**Purpose**: Defines how to build the Flatpak package

**Key Components**:
- **Runtime**: `org.gnome.Platform` version 47 (GTK4/LibAdwaita support)
- **SDK**: `org.gnome.Sdk` version 47
- **Finish Args**: Permissions for network, GUI, filesystem access
- **Modules**: All Python dependencies (requests, typer, bencodepy, watchdog)

**Permissions Explained**:
- `--share=ipc`: Required for GTK4 applications
- `--socket=fallback-x11` / `--socket=wayland`: GUI display support
- `--share=network`: Network access for torrent tracker communication
- `--filesystem=xdg-download`: Access to Downloads folder for torrent files
- `--filesystem=xdg-config/dfakeseeder:create`: Configuration storage
- `--talk-name=org.freedesktop.Notifications`: Desktop notifications
- `--talk-name=org.gtk.vfs.*`: Virtual filesystem support

### 2. AppStream Metadata: `ie.fio.dfakeseeder.appdata.xml`

**Location**: `/home/daoneill/src/DFakeSeeder/ie.fio.dfakeseeder.appdata.xml`

**Purpose**: Provides application information for software centers

**Contents**:
- Application description and features
- Screenshots with captions
- Release notes and version history
- Project URLs (homepage, bug tracker, documentation)
- Content ratings (OARS)
- Categories and keywords

**Validation**:
```bash
appstream-util validate-relax ie.fio.dfakeseeder.appdata.xml
```

### 3. Desktop File: `ie.fio.dfakeseeder.desktop`

**Location**: `/home/daoneill/src/DFakeSeeder/ie.fio.dfakeseeder.desktop`

**Purpose**: Defines application launcher for desktop environments

**Key Fields**:
- `Exec=dfakeseeder`: Command to launch
- `Icon=ie.fio.dfakeseeder`: Application icon
- `StartupWMClass=ie.fio.dfakeseeder`: Window manager class for proper taskbar grouping
- `Categories=Network;P2P;Utility;`: Application menu categories

**Validation**:
```bash
desktop-file-validate ie.fio.dfakeseeder.desktop
```

## Local Testing

### Build the Flatpak Locally

```bash
# Clean any previous builds
rm -rf build-dir .flatpak-builder

# Build and install locally
flatpak-builder --user --install --force-clean build-dir ie.fio.dfakeseeder.flatpak.json

# Run the application
flatpak run ie.fio.dfakeseeder

# Check logs if issues occur
journalctl --user -f -u flatpak-session@*
```

### Testing Checklist

- [ ] Application launches without errors
- [ ] GUI displays correctly
- [ ] Network connectivity works (tracker communication)
- [ ] File operations work (loading torrents from Downloads)
- [ ] Configuration saves properly
- [ ] Desktop notifications appear
- [ ] System tray integration functions
- [ ] All 21 languages are available
- [ ] Settings persistence across restarts

### Debugging Build Issues

```bash
# Build with verbose output
flatpak-builder --verbose build-dir ie.fio.dfakeseeder.flatpak.json

# Build without installing to inspect files
flatpak-builder build-dir ie.fio.dfakeseeder.flatpak.json
ls -R build-dir/

# Enter build environment for debugging
flatpak-builder --run build-dir ie.fio.dfakeseeder.flatpak.json bash
```

## Flathub Submission Process

### Step 1: Fork Flathub Repository

1. Visit: https://github.com/flathub/flathub
2. Click "Fork" to create your fork
3. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/flathub.git
   cd flathub
   git checkout new-pr
   ```

### Step 2: Create Application Directory

```bash
# Create directory for your application
mkdir ie.fio.dfakeseeder
cd ie.fio.dfakeseeder

# Copy the manifest
cp /home/daoneill/src/DFakeSeeder/ie.fio.dfakeseeder.flatpak.json .

# Copy metadata files
cp /home/daoneill/src/DFakeSeeder/ie.fio.dfakeseeder.appdata.xml .
cp /home/daoneill/src/DFakeSeeder/ie.fio.dfakeseeder.desktop .

# Copy icon
mkdir -p icons
cp /home/daoneill/src/DFakeSeeder/d_fake_seeder/components/images/dfakeseeder.png icons/ie.fio.dfakeseeder.png
```

### Step 3: Update Manifest for Flathub

**IMPORTANT**: The manifest must reference a **stable release**, not a git branch tip.

Update the `dfakeseeder` module sources in `ie.fio.dfakeseeder.flatpak.json`:

```json
{
  "name": "dfakeseeder",
  "buildsystem": "simple",
  "build-commands": [
    "pip3 install --verbose --no-deps --no-build-isolation --prefix=${FLATPAK_DEST} .",
    "install -Dm644 d_fake_seeder/components/images/dfakeseeder.png ${FLATPAK_DEST}/share/icons/hicolor/256x256/apps/ie.fio.dfakeseeder.png",
    "install -Dm644 ie.fio.dfakeseeder.desktop ${FLATPAK_DEST}/share/applications/ie.fio.dfakeseeder.desktop",
    "install -Dm644 ie.fio.dfakeseeder.appdata.xml ${FLATPAK_DEST}/share/metainfo/ie.fio.dfakeseeder.appdata.xml"
  ],
  "sources": [
    {
      "type": "archive",
      "url": "https://github.com/dmzoneill/DFakeSeeder/archive/refs/tags/v0.0.52.tar.gz",
      "sha256": "YOUR_TARBALL_SHA256_HERE"
    }
  ]
}
```

To get the SHA256:
```bash
wget https://github.com/dmzoneill/DFakeSeeder/archive/refs/tags/v0.0.52.tar.gz
sha256sum v0.0.52.tar.gz
```

### Step 4: Test Flathub Build

```bash
# Build from your Flathub fork directory
cd ~/flathub/ie.fio.dfakeseeder
flatpak-builder --user --install --force-clean build-dir ie.fio.dfakeseeder.flatpak.json

# Test the application
flatpak run ie.fio.dfakeseeder
```

### Step 5: Create Pull Request

```bash
# Add files
git add ie.fio.dfakeseeder/

# Commit with descriptive message
git commit -m "Add ie.fio.dfakeseeder"

# Push to your fork
git push origin new-pr

# Create pull request on GitHub
```

**Pull Request Details**:
- **Base repository**: `flathub/flathub`
- **Base branch**: `new-pr`
- **Title**: "Add ie.fio.dfakeseeder"
- **Description**: Brief description of the application and any special notes

### Step 6: Review Process

**What to Expect**:
1. Automated checks run (manifest validation, appstream validation, build test)
2. Volunteer reviewers examine your submission
3. Reviewers may request changes or ask questions
4. Response times vary (reviewers are volunteers)

**Common Review Comments**:
- Missing or incorrect AppStream metadata
- Insufficient permissions or too many permissions
- Icon size/format issues
- Missing screenshots
- License compliance questions
- Build reproducibility concerns

**Responding to Feedback**:
```bash
# Make requested changes to files
# Commit and push updates
git add .
git commit -m "Address review feedback: <description>"
git push origin new-pr
```

The pull request will automatically update with your changes.

### Step 7: Approval and Publication

**After Approval**:
1. Your PR is merged
2. Flathub creates a dedicated repository: `flathub/ie.fio.dfakeseeder`
3. You're granted collaborator access to this repository
4. The application appears on Flathub within 24 hours
5. You can publish updates by pushing to your dedicated repository

## Post-Publication Maintenance

### Publishing Updates

After your app is on Flathub, you have a dedicated repository:

```bash
# Clone your app's Flathub repository
git clone https://github.com/flathub/ie.fio.dfakeseeder.git
cd ie.fio.dfakeseeder

# Update manifest with new version
# Edit ie.fio.dfakeseeder.flatpak.json:
# - Update tarball URL to new release tag
# - Update SHA256 hash
# - Update appdata.xml with new release notes

# Test the build
flatpak-builder --user --install --force-clean build-dir ie.fio.dfakeseeder.flatpak.json

# Commit and push
git add ie.fio.dfakeseeder.flatpak.json ie.fio.dfakeseeder.appdata.xml
git commit -m "Update to version X.Y.Z"
git push origin master
```

Flathub automatically builds and publishes updates when you push to master.

### Update Checklist

- [ ] Create GitHub release with version tag
- [ ] Update version in `ie.fio.dfakeseeder.appdata.xml` releases section
- [ ] Update tarball URL and SHA256 in manifest
- [ ] Test build locally
- [ ] Push to Flathub repository
- [ ] Verify build succeeds on Flathub
- [ ] Check application updates on user systems

## Flathub Requirements Summary

### Application Requirements

- ✅ **Valid License**: Open source license (MIT)
- ✅ **Redistributable**: All components can be redistributed
- ✅ **Unique App ID**: Reverse DNS format `ie.fio.dfakeseeder`
- ✅ **Stable Releases**: Use release tags, not branch tips
- ✅ **AppStream Metadata**: Complete metadata with screenshots
- ✅ **Desktop Integration**: Valid desktop file
- ✅ **Icon**: Provided in appropriate sizes (256x256)

### Metadata Requirements

- ✅ **Application Name**: Clear, unique name
- ✅ **Summary**: One-line description
- ✅ **Description**: Detailed multi-paragraph description
- ✅ **Screenshots**: At least one screenshot with caption
- ✅ **Project URLs**: Homepage, bug tracker
- ✅ **Content Rating**: OARS content rating
- ✅ **Release Information**: Version history with dates

### Technical Requirements

- ✅ **Build from Source**: Manifest builds from source tarballs
- ✅ **Reproducible Builds**: Deterministic build process
- ✅ **Minimal Permissions**: Only necessary finish-args
- ✅ **No Bundled Dependencies**: Use Flathub shared modules where possible
- ✅ **Runtime Version**: Current stable runtime

## Troubleshooting

### Build Fails

**Issue**: Python dependencies fail to install
**Solution**: Ensure all wheel URLs and SHA256s are correct. Check network connectivity.

**Issue**: AppStream validation fails
**Solution**: Run `appstream-util validate-relax` and fix reported issues.

**Issue**: Desktop file invalid
**Solution**: Run `desktop-file-validate` and address warnings/errors.

### Runtime Issues

**Issue**: Application doesn't launch
**Solution**: Check `journalctl --user -f` for errors. Verify permissions in finish-args.

**Issue**: Network doesn't work
**Solution**: Ensure `--share=network` is in finish-args.

**Issue**: Configuration not saved
**Solution**: Verify `--filesystem=xdg-config/dfakeseeder:create` permission.

### Review Process Issues

**Issue**: Long wait for review
**Solution**: Be patient. Reviewers are volunteers. Ping politely after 1-2 weeks.

**Issue**: Requested changes unclear
**Solution**: Ask for clarification in PR comments. Reviewers are helpful.

## Resources

### Official Documentation

- **Flathub Submission Guide**: https://docs.flathub.org/docs/for-app-authors/submission
- **Flatpak Documentation**: https://docs.flatpak.org/
- **AppStream Specification**: https://www.freedesktop.org/software/appstream/docs/

### Community Resources

- **Flathub Discourse**: https://discourse.flathub.org/
- **Flatpak Chat**: https://matrix.to/#/#flatpak:matrix.org
- **Flathub GitHub**: https://github.com/flathub/flathub

### D' Fake Seeder Resources

- **GitHub Repository**: https://github.com/dmzoneill/DFakeSeeder
- **Issue Tracker**: https://github.com/dmzoneill/DFakeSeeder/issues
- **PyPI Package**: https://pypi.org/project/d-fake-seeder/

## Quick Reference Commands

```bash
# Validate metadata
appstream-util validate-relax ie.fio.dfakeseeder.appdata.xml
desktop-file-validate ie.fio.dfakeseeder.desktop

# Build locally
flatpak-builder --user --install --force-clean build-dir ie.fio.dfakeseeder.flatpak.json

# Run application
flatpak run ie.fio.dfakeseeder

# Check logs
journalctl --user -f -u flatpak-session@*

# Clean build
rm -rf build-dir .flatpak-builder

# Get SHA256 of tarball
wget https://github.com/dmzoneill/DFakeSeeder/archive/refs/tags/v0.0.52.tar.gz
sha256sum v0.0.52.tar.gz
```

## Next Steps

1. **Create a GitHub Release**: Tag version `v0.0.52` if not already done
2. **Get Tarball SHA256**: Download and hash the release tarball
3. **Update Manifest**: Replace source type from `dir` to `archive` with URL and SHA256
4. **Local Test**: Build and test with the updated manifest
5. **Fork Flathub**: Create your fork of the Flathub repository
6. **Submit PR**: Create pull request against `new-pr` branch
7. **Respond to Reviews**: Address any feedback from reviewers
8. **Celebrate**: Once approved, your app is on Flathub!

---

**Last Updated**: 2024-12-03
**Flatpak Runtime**: org.gnome.Platform 47
**Application Version**: 0.0.52
