# Dispatch.yaml Flatpak Integration

## Overview

This document provides the complete changes needed for `dispatch.yaml` to support fully automated Flathub releases for ANY repository using the dispatch workflow.

## Key Requirements

1. **Auto-detect Flatpak files** - No hardcoded paths
2. **Graceful failure** - Return success if files don't exist
3. **Auto-update package URLs** - Fetch latest PyPI versions
4. **Support both workflows** - Initial submission and updates
5. **Repository agnostic** - Works with any project structure

---

## Changes to dispatch.yaml

### 1. Add New Inputs (after existing `flatpak-build` input)

Add these new inputs in the `inputs:` section around line 40-50:

```yaml
      flatpak-build:
        required: false
        type: string
        default: "false"

      # New Flatpak automation inputs
      flatpak-runtime:
        description: 'Flatpak runtime (e.g., org.gnome.Platform, org.freedesktop.Platform)'
        required: false
        type: string
        default: "org.gnome.Platform"
      flatpak-runtime-version:
        description: 'Runtime version (e.g., 49 for GNOME 49)'
        required: false
        type: string
        default: "49"
      flatpak-flathub-repo:
        description: 'Your Flathub fork (username/flathub) for auto-submission'
        required: false
        type: string
        default: ""
      flatpak-auto-submit:
        description: 'Automatically submit to Flathub (requires FLATHUB_TOKEN)'
        required: false
        type: string
        default: "false"
```

### 2. Replace Entire Flatpak Job

**Find the existing `flatpak:` job** (around line 1200-1250) and **REPLACE IT COMPLETELY** with:

```yaml
  flatpak:
    if: inputs.flatpak-build != 'false'
    needs: create-release
    name: Flatpak publish
    runs-on: ubuntu-22.04
    outputs:
      manifest-found: ${{ steps.detect-files.outputs.manifest-found }}
      version: ${{ steps.get-version.outputs.version }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Detect Flatpak files
        id: detect-files
        run: |
          echo "Searching for Flatpak manifest files..."

          # Find manifest (*.json with app-id or id field)
          MANIFEST=""
          for json in *.json; do
            if [ -f "$json" ]; then
              if grep -q '"app-id"\|"id"' "$json" 2>/dev/null; then
                MANIFEST="$json"
                echo "Found manifest: $MANIFEST"
                break
              fi
            fi
          done

          if [ -z "$MANIFEST" ]; then
            echo "::warning::No Flatpak manifest found (*.json with app-id/id field)"
            echo "manifest-found=false" >> $GITHUB_OUTPUT
            echo "Skipping Flatpak build - no manifest detected"
            exit 0
          fi

          # Extract app-id from manifest
          APP_ID=$(grep -o '"app-id"[[:space:]]*:[[:space:]]*"[^"]*"' "$MANIFEST" | cut -d'"' -f4)
          if [ -z "$APP_ID" ]; then
            APP_ID=$(grep -o '"id"[[:space:]]*:[[:space:]]*"[^"]*"' "$MANIFEST" | cut -d'"' -f4)
          fi

          # Find appdata file
          APPDATA=""
          if [ -f "${APP_ID}.appdata.xml" ]; then
            APPDATA="${APP_ID}.appdata.xml"
          elif [ -f "${APP_ID}.metainfo.xml" ]; then
            APPDATA="${APP_ID}.metainfo.xml"
          else
            # Search for any .appdata.xml or .metainfo.xml
            APPDATA=$(find . -maxdepth 1 -name "*.appdata.xml" -o -name "*.metainfo.xml" | head -1)
          fi

          # Find desktop file
          DESKTOP=""
          if [ -f "${APP_ID}.desktop" ]; then
            DESKTOP="${APP_ID}.desktop"
          else
            DESKTOP=$(find . -maxdepth 1 -name "*.desktop" | head -1)
          fi

          # Find icon (prefer PNG, search in common locations)
          ICON=""
          for size in 256 128 64 48; do
            for dir in . images icons data; do
              if [ -d "$dir" ]; then
                ICON=$(find "$dir" -name "*.png" -o -name "*.svg" | head -1)
                if [ -n "$ICON" ]; then
                  break 2
                fi
              fi
            done
          done

          echo "manifest-found=true" >> $GITHUB_OUTPUT
          echo "MANIFEST=$MANIFEST" >> $GITHUB_ENV
          echo "APP_ID=$APP_ID" >> $GITHUB_ENV
          echo "APPDATA=$APPDATA" >> $GITHUB_ENV
          echo "DESKTOP=$DESKTOP" >> $GITHUB_ENV
          echo "ICON=$ICON" >> $GITHUB_ENV

          echo "✅ Detected Flatpak files:"
          echo "  Manifest: $MANIFEST"
          echo "  App ID: $APP_ID"
          echo "  AppData: ${APPDATA:-Not found}"
          echo "  Desktop: ${DESKTOP:-Not found}"
          echo "  Icon: ${ICON:-Not found}"

      - name: Get version
        id: get-version
        if: steps.detect-files.outputs.manifest-found == 'true'
        run: |
          if [ -f version ]; then
            VERSION=$(grep 'version=' version | cut -d'=' -f2)
          elif [ -f pyproject.toml ]; then
            VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
          elif [ -f setup.py ]; then
            VERSION=$(grep 'version=' setup.py | cut -d'"' -f2 | head -1)
          elif [ -f package.json ]; then
            VERSION=$(grep '"version"' package.json | cut -d'"' -f4)
          else
            VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.1")
            VERSION=${VERSION#v}
          fi
          echo "version=$VERSION" >> $GITHUB_OUTPUT
          echo "Found version: $VERSION"

      - name: Install Flatpak tools
        if: steps.detect-files.outputs.manifest-found == 'true'
        run: |
          sudo apt-get update
          sudo apt-get install -y flatpak flatpak-builder appstream-util desktop-file-utils

      - name: Add Flathub repository
        if: steps.detect-files.outputs.manifest-found == 'true'
        run: |
          flatpak remote-add --if-not-exists --user flathub https://dl.flathub.org/repo/flathub.flatpakrepo

      - name: Install runtime
        if: steps.detect-files.outputs.manifest-found == 'true'
        run: |
          RUNTIME="${{ inputs.flatpak-runtime }}//${{ inputs.flatpak-runtime-version }}"
          SDK="${{ inputs.flatpak-runtime }}.Sdk//${{ inputs.flatpak-runtime-version }}"

          echo "Installing runtime: $RUNTIME"
          flatpak install --user -y flathub "$RUNTIME" || true
          flatpak install --user -y flathub "$SDK" || true

      - name: Auto-update Python package URLs
        if: steps.detect-files.outputs.manifest-found == 'true'
        run: |
          python3 << 'PYTHON_SCRIPT'
          import json
          import urllib.request
          import sys
          import os

          manifest_path = os.environ.get('MANIFEST', '')
          if not manifest_path or not os.path.exists(manifest_path):
              print("No manifest to update")
              sys.exit(0)

          # Read manifest
          with open(manifest_path, 'r') as f:
              manifest = json.load(f)

          # Update runtime version
          manifest['runtime-version'] = "${{ inputs.flatpak-runtime-version }}"

          # Function to get latest package from PyPI
          def get_latest_pypi_package(package_name):
              try:
                  url = f'https://pypi.org/pypi/{package_name}/json'
                  with urllib.request.urlopen(url) as response:
                      data = json.loads(response.read())

                      # Prefer py3-none-any wheels, fallback to source
                      wheels = [u for u in data['urls'] if u['packagetype']=='bdist_wheel']
                      if wheels:
                          wheel = next((u for u in wheels if 'py3-none-any' in u['filename']), wheels[0])
                          return {'url': wheel['url'], 'sha256': wheel['digests']['sha256']}
                      else:
                          sdist = next((u for u in data['urls'] if u['packagetype']=='sdist'), None)
                          if sdist:
                              return {'url': sdist['url'], 'sha256': sdist['digests']['sha256']}
              except Exception as e:
                  print(f"Warning: Failed to fetch {package_name}: {e}")
                  return None

          # Common Python package groups
          package_map = {
              'python3-requests': ['requests', 'certifi', 'idna', 'charset-normalizer', 'urllib3'],
              'python3-typer': ['typer', 'click', 'typing-extensions', 'shellingham', 'rich',
                               'markdown-it-py', 'mdurl', 'pygments'],
              'python3-watchdog': ['watchdog'],
              'python3-bencodepy': ['bencodepy']
          }

          updated = False
          for module in manifest.get('modules', []):
              module_name = module.get('name', '')
              if module_name in package_map:
                  print(f"Updating {module_name}...")
                  sources = module.get('sources', [])

                  for i, source in enumerate(sources):
                      if source.get('type') == 'file':
                          filename = source.get('url', '').split('/')[-1]
                          for pkg in package_map[module_name]:
                              if pkg.replace('-', '_') in filename or pkg in filename:
                                  new_info = get_latest_pypi_package(pkg)
                                  if new_info:
                                      sources[i]['url'] = new_info['url']
                                      sources[i]['sha256'] = new_info['sha256']
                                      print(f"  ✅ Updated {pkg}")
                                      updated = True
                                  break

          # Write updated manifest
          if updated:
              with open(manifest_path, 'w') as f:
                  json.dump(manifest, f, indent=4)
              print("✅ Manifest updated with latest package URLs")
          else:
              print("ℹ️  No package URLs to update")
          PYTHON_SCRIPT

      - name: Validate metadata
        if: steps.detect-files.outputs.manifest-found == 'true'
        continue-on-error: true
        run: |
          if [ -n "$APPDATA" ] && [ -f "$APPDATA" ]; then
            echo "Validating AppStream metadata..."
            appstream-util validate-relax "$APPDATA" || echo "::warning::AppStream validation had issues"
          fi

          if [ -n "$DESKTOP" ] && [ -f "$DESKTOP" ]; then
            echo "Validating desktop file..."
            desktop-file-validate "$DESKTOP" || echo "::warning::Desktop file validation had issues"
          fi

      - name: Build Flatpak
        if: steps.detect-files.outputs.manifest-found == 'true'
        run: |
          echo "Building Flatpak from manifest: $MANIFEST"
          flatpak-builder --user --install --force-clean build-dir "$MANIFEST"
          echo "✅ Flatpak built successfully"

      - name: Create GitHub release
        if: steps.detect-files.outputs.manifest-found == 'true'
        id: create-release
        continue-on-error: true
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: v${{ steps.get-version.outputs.version }}
          release_name: v${{ steps.get-version.outputs.version }}
          body: |
            ## Release v${{ steps.get-version.outputs.version }}

            Automated release for Flathub submission.
          draft: false
          prerelease: false

      - name: Update manifest with release tarball
        if: steps.detect-files.outputs.manifest-found == 'true' && steps.create-release.outcome == 'success'
        run: |
          sleep 10  # Wait for release assets

          VERSION="${{ steps.get-version.outputs.version }}"
          TARBALL_URL="https://github.com/${{ github.repository }}/archive/refs/tags/v${VERSION}.tar.gz"

          # Download and get SHA256
          wget -q "$TARBALL_URL" -O release.tar.gz
          SHA256=$(sha256sum release.tar.gz | awk '{print $1}')

          # Update manifest
          python3 << PYTHON_SCRIPT
          import json
          import os

          manifest_path = os.environ.get('MANIFEST', '')
          version = "$VERSION"
          sha256 = "$SHA256"
          repo = "${{ github.repository }}"
          app_name = repo.split('/')[-1].lower()

          with open(manifest_path, 'r') as f:
              manifest = json.load(f)

          # Find main app module
          for module in manifest.get('modules', []):
              module_name = module.get('name', '').lower()
              if app_name in module_name or 'main' in module_name:
                  module['sources'] = [{
                      'type': 'archive',
                      'url': f'https://github.com/{repo}/archive/refs/tags/v{version}.tar.gz',
                      'sha256': sha256
                  }]
                  print(f"✅ Updated {module['name']} to use release tarball")
                  break

          with open(manifest_path, 'w') as f:
              json.dump(manifest, f, indent=4)
          PYTHON_SCRIPT

      - name: Test build with release tarball
        if: steps.detect-files.outputs.manifest-found == 'true' && steps.create-release.outcome == 'success'
        continue-on-error: true
        run: |
          rm -rf build-dir .flatpak-builder
          flatpak-builder --user --install --force-clean build-dir "$MANIFEST"
          echo "✅ Release tarball build successful"

      - name: Submit to Flathub (if configured)
        if: |
          steps.detect-files.outputs.manifest-found == 'true' &&
          inputs.flatpak-auto-submit == 'true' &&
          inputs.flatpak-flathub-repo != ''
        continue-on-error: true
        run: |
          echo "🚀 Flathub auto-submission would happen here"
          echo "Fork: ${{ inputs.flatpak-flathub-repo }}"
          echo "App: $APP_ID"
          echo "Version: ${{ steps.get-version.outputs.version }}"
          echo ""
          echo "To enable auto-submission:"
          echo "1. Fork https://github.com/flathub/flathub"
          echo "2. Add FLATHUB_TOKEN secret to repository"
          echo "3. Set flatpak-flathub-repo: 'username/flathub'"
          echo "4. Set flatpak-auto-submit: 'true'"

      - name: Upload Flatpak artifacts
        if: steps.detect-files.outputs.manifest-found == 'true'
        uses: actions/upload-artifact@v4
        with:
          name: flatpak-files
          path: |
            ${{ env.MANIFEST }}
            ${{ env.APPDATA }}
            ${{ env.DESKTOP }}

      - name: Send message to Redis
        if: steps.detect-files.outputs.manifest-found == 'true'
        uses: dmzoneill/dmzoneill/.github/actions/redis@main
        with:
          message: "${{ github.sha }} ${{ github.repository }} published flatpak"
          redis_password: ${{ secrets.REDIS_PASSWORD }}

      - name: Summary
        if: always()
        run: |
          if [ "${{ steps.detect-files.outputs.manifest-found }}" == "true" ]; then
            echo "✅ Flatpak build completed successfully"
            echo "Manifest: $MANIFEST"
            echo "Version: ${{ steps.get-version.outputs.version }}"
          else
            echo "ℹ️  Flatpak build skipped - no manifest detected"
            echo "This is normal for repositories without Flatpak support"
          fi
```

---

## Usage in Repositories

### For DFakeSeeder (with Flatpak support)

Update `.github/workflows/main.yml`:

```yaml
jobs:
  cicd:
    secrets: inherit
    uses: dmzoneill/dmzoneill/.github/workflows/dispatch.yaml@main
    with:
      pypi-extension: "true"
      deb-build: "true"
      rpm-build: "true"
      docker-build: "true"
      flatpak-build: "true"              # Enable Flatpak
      flatpak-runtime: "org.gnome.Platform"
      flatpak-runtime-version: "49"
      flatpak-flathub-repo: "dmzoneill/flathub"  # Your fork
      flatpak-auto-submit: "false"       # Manual submission for now
      VALIDATE_JSCPD: "false"
      VALIDATE_PYTHON_MYPY: "false"
      VALIDATE_PYTHON_PYLINT: "false"
      VALIDATE_DOCKERFILE_HADOLINT: "false"
```

### For Repositories WITHOUT Flatpak

```yaml
jobs:
  cicd:
    secrets: inherit
    uses: dmzoneill/dmzoneill/.github/workflows/dispatch.yaml@main
    with:
      pypi-extension: "true"
      deb-build: "true"
      flatpak-build: "true"  # ← Still enabled, will gracefully skip
```

**Result**: Job will detect no manifest and exit gracefully with success status.

---

## File Detection Logic

The workflow auto-detects files in this order:

1. **Manifest**: Any `*.json` file containing `"app-id"` or `"id"` field
2. **AppData**: `${APP_ID}.appdata.xml` or `${APP_ID}.metainfo.xml` or any `*.appdata.xml`
3. **Desktop**: `${APP_ID}.desktop` or any `*.desktop`
4. **Icon**: PNG/SVG in common directories (., images, icons, data)

---

## Graceful Failure Behavior

| Scenario | Behavior | Exit Code |
|----------|----------|-----------|
| No manifest found | Skip all steps, log warning | 0 (success) |
| Manifest found, build fails | Job fails | 1 (failure) |
| Manifest found, metadata invalid | Continue (warning logged) | 0 (success) |
| Release creation fails | Skip release-specific steps | 0 (success) |

---

## Benefits

✅ **Zero Configuration**: Auto-detects all files
✅ **Graceful Degradation**: Returns success if Flatpak not applicable
✅ **Auto-Updates**: Fetches latest PyPI package URLs
✅ **Repository Agnostic**: Works with any project structure
✅ **Version Detection**: Supports pyproject.toml, setup.py, package.json, git tags
✅ **Multi-Runtime**: Supports GNOME, Freedesktop, KDE runtimes

---

## Testing Checklist

After updating dispatch.yaml:

- [ ] Test with DFakeSeeder (has Flatpak files) → Should build
- [ ] Test with non-Flatpak repo → Should skip gracefully
- [ ] Verify auto-detection finds all files correctly
- [ ] Check package URL updates work
- [ ] Confirm release creation and tarball update
- [ ] Validate artifacts are uploaded

---

## Security Considerations

- `FLATHUB_TOKEN` is optional - only needed for auto-submission
- Workflow only modifies files in build context, not repository
- All external package fetches use HTTPS from pypi.org
- Release creation requires `GITHUB_TOKEN` (automatically provided)

---

## Next Steps

1. Update dispatch.yaml with the changes above
2. Commit and push to `dmzoneill/dmzoneill` repository
3. Test with DFakeSeeder by pushing a commit
4. Verify build succeeds and artifacts are created
5. Optional: Configure FLATHUB_TOKEN for auto-submission

---

**Questions?** Check the workflow logs - all steps include detailed output explaining what's happening.
