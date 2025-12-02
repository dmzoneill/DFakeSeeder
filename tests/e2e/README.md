# End-to-End Testing for RPM Packaging

Comprehensive automated testing framework for RPM installation, application launch, and desktop integration.

## Overview

This E2E testing system provides **fully automated** testing for:
- ✅ RPM package build and validation
- ✅ Installation in clean Fedora containers
- ✅ File placement and permissions
- ✅ System configuration
- ✅ Application launch (with GUI testing via Xvfb)
- ✅ Desktop integration
- ✅ Configuration system
- ✅ Uninstallation and cleanup

## Quick Start

### Run All E2E Tests

```bash
# From project root
make test-e2e
```text
This will:
1. Build the RPM package
2. Create a Docker/Podman test container
3. Run installation tests
4. Run application launch tests
5. Run uninstall tests
6. Generate test report

### Run Specific Test Suites

```bash
# Run only installation tests
make test-e2e-install

# Run only launch tests
make test-e2e-launch

# Run only uninstall tests
make test-e2e-uninstall

# Fast mode (skip build, use existing RPM)
make test-e2e-fast
```text
## Test Architecture

### Components

```text
tests/e2e/
├── Dockerfile.fedora              # Test container definition
├── test_rpm_installation.sh       # Installation and file verification tests
├── test_rpm_launch.sh             # Application launch and GUI tests
├── run_e2e_tests.sh               # Main test orchestrator
└── README.md                      # This file
```text
### Test Flow

```mermaid
graph TD
    A[Build RPM] --> B[Create Test Container]
    B --> C[Run Installation Tests]
    C --> D[Verify Files & Config]
    D --> E[Run Launch Tests]
    E --> F[Start Xvfb Virtual Display]
    F --> G[Launch Application]
    G --> H[Verify Processes]
    H --> I[Run Uninstall Tests]
    I --> J[Generate Report]
```text
## Test Details

### 1. Installation Tests (`test_rpm_installation.sh`)

**Tests Performed** (40+ individual tests):

#### RPM File Validation
- RPM file exists and is readable
- RPM structure is valid
- Package metadata is correct

#### File Installation
- Application directory: `/opt/dfakeseeder/`
- Main application: `/opt/dfakeseeder/dfakeseeder.py`
- Tray application: `/opt/dfakeseeder/dfakeseeder_tray.py`
- All subdirectories (config, components, lib, domain, locale)

#### System Files
- System config: `/etc/dfakeseeder/default.json`
- Wrapper script: `/usr/bin/dfakeseeder` (executable)
- Desktop file: `/usr/share/applications/dfakeseeder.desktop`
- Icons: `/usr/share/icons/hicolor/*/apps/dfakeseeder.png` (all sizes)

#### Permissions
- Config files are readable
- Wrapper script is executable
- Application files have correct permissions

#### System Integration
- Command is in PATH
- Desktop file validation
- Icon cache updates

#### Configuration
- JSON validation
- Required fields present
- Structure verification

#### Dependencies
- Python modules (requests, watchdog, bencodepy, gi)
- System libraries (GTK4, GObject)

**Example Output:**
```text
==========================================
RPM Installation End-to-End Tests
==========================================

[INFO] ✓ RPM file is readable
[INFO] ✓ RPM file structure is valid
[INFO] ✓ Application directory installed
[INFO] ✓ System default config installed
[INFO] ✓ Wrapper script is executable
...

========================================
TEST SUMMARY
========================================

Tests Passed: 42
Tests Failed: 0
Total Tests:  42

[INFO] All tests passed! ✓
```text
### 2. Launch Tests (`test_rpm_launch.sh`)

**Tests Performed** (15+ individual tests):

#### GUI Environment Setup
- Start Xvfb virtual X server (`:99`)
- D-Bus session initialization
- X server readiness verification

#### User Config Creation
- First-run config initialization
- Config copied from `/etc/dfakeseeder/default.json`
- `~/.config/dfakeseeder/settings.json` created
- `~/.config/dfakeseeder/torrents/` directory created
- JSON validation of user config

#### Application Launch
- Main application process starts
- Process management (PID tracking)
- Log output verification
- GTK initialization detection

#### Python Module Imports
- Import all critical modules
- Verify PYTHONPATH setup
- Module dependency resolution

#### Desktop Integration
- Desktop file validation
- Exec path verification
- Desktop actions present

#### Tray Application
- Tray process launch
- Process lifecycle management

**Example Output:**
```text
==========================================
Application Launch End-to-End Tests
==========================================

[INFO] Starting Xvfb virtual display...
[INFO] ✓ X server ready
[INFO] ✓ User config created
[INFO] ✓ Config is valid JSON
[INFO] ✓ Application process started (PID: 12345)
[INFO] ✓ Can import: d_fake_seeder.domain.app_settings
...

========================================
TEST SUMMARY
========================================

Tests Passed: 16
Tests Failed: 0
Total Tests:  16

[INFO] All tests passed! ✓
```text
### 3. Uninstall Tests

**Tests Performed:**
- Package removal via `dnf remove` or `rpm -e`
- Verify package not in RPM database
- Clean uninstallation (no errors)

## Container Environment

### Dockerfile.fedora

Provides a clean Fedora environment with:
- Python 3.11+
- GTK4 and GObject Introspection
- Xvfb for headless GUI testing
- D-Bus for application messaging
- Desktop utilities (desktop-file-utils, gtk-update-icon-cache)

### Non-root Testing

Tests run as user `tester` (not root) to simulate real-world installation:
- `sudo` used for RPM installation
- User directories in `/home/tester/`
- Proper permission testing

## Running Tests Locally

### Prerequisites

```bash
# Install container engine (choose one)
sudo dnf install podman  # Recommended
# or
sudo dnf install docker

# Make scripts executable
chmod +x tests/e2e/*.sh
```text
### Manual Test Execution

```bash
# 1. Build RPM first
make rpm

# 2. Run full E2E suite
make test-e2e

# 3. Or run individual test suites
make test-e2e-install
make test-e2e-launch
make test-e2e-uninstall
```text
### Advanced Usage

```bash
# Run with custom options
tests/e2e/run_e2e_tests.sh --skip-build   # Use existing RPM
tests/e2e/run_e2e_tests.sh --skip-image   # Use existing container
tests/e2e/run_e2e_tests.sh --test install  # Run only installation tests
tests/e2e/run_e2e_tests.sh --cleanup      # Clean artifacts after tests
```text
### Direct Container Testing

```bash
# Build test container
cd tests/e2e
podman build -t dfakeseeder-e2e-test:latest -f Dockerfile.fedora .

# Run installation tests manually
podman run --rm \
  -v $(pwd)/../../rpmbuild/RPMS:/rpms:ro \
  -v $(pwd):/workspace/tests:ro \
  dfakeseeder-e2e-test:latest \
  /bin/bash /workspace/tests/test_rpm_installation.sh

# Run launch tests manually
podman run --rm --privileged \
  -v $(pwd)/../../rpmbuild/RPMS:/rpms:ro \
  -v $(pwd):/workspace/tests:ro \
  -e DISPLAY=:99 \
  dfakeseeder-e2e-test:latest \
  /bin/bash -c "
    RPM_FILE=\$(find /rpms -name 'dfakeseeder-*.rpm' | head -1)
    sudo rpm -ivh \"\$RPM_FILE\"
    /bin/bash /workspace/tests/test_rpm_launch.sh
  "
```text
## CI/CD Integration

### GitHub Actions

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main`
- Manual workflow dispatch

See `.github/workflows/rpm-e2e-tests.yml` for configuration.

#### Matrix Testing

Tests run against multiple Fedora versions:
- Fedora Latest
- Fedora 39
- Fedora 38

#### Artifacts

GitHub Actions uploads:
- Test results and logs
- Built RPM packages
- Test reports

### Local CI Simulation

```bash
# Simulate GitHub Actions locally
act push --workflows .github/workflows/rpm-e2e-tests.yml
```text
## Test Reports

### Locations

```text
rpmbuild/test-artifacts/
├── e2e-test-report.txt          # Summary report
├── installation-test.log        # Installation test output
├── launch-test.log              # Launch test output
└── uninstall-test.log           # Uninstall test output
```text
### Report Format

```text
DFakeSeeder E2E Test Report
===========================
Date: 2024-11-27 12:00:00
Container Engine: podman
Test Image: dfakeseeder-e2e-test:latest
RPM File: dfakeseeder-0.0.46-1.fc43.noarch.rpm

Test Results:
-------------
✓ Installation Tests: PASSED (42 tests)
✓ Launch Tests: PASSED (16 tests)
✓ Uninstall Tests: PASSED (3 tests)

Full details available in test-artifacts directory
```text
## Troubleshooting

### Common Issues

#### 1. Container Build Fails

**Problem**: Docker/Podman build errors

**Solution**:
```bash
# Update base image
podman pull fedora:latest

# Rebuild without cache
cd tests/e2e
podman build --no-cache -t dfakeseeder-e2e-test:latest -f Dockerfile.fedora .
```text
#### 2. RPM Not Found

**Problem**: Tests can't find RPM file

**Solution**:
```bash
# Ensure RPM is built
make rpm

# Check RPM location
find rpmbuild/RPMS -name "*.rpm"

# Verify RPM path is correct
ls -la rpmbuild/RPMS/noarch/dfakeseeder-*.rpm
```text
#### 3. Xvfb Fails to Start

**Problem**: Virtual display errors

**Solution**:
```bash
# Run with more privileges
podman run --privileged ...

# Or install additional X11 dependencies in Dockerfile
```text
#### 4. GUI Tests Fail in Headless

**Problem**: GTK application won't start

**Solution**:
- This is expected in some environments
- Check logs for actual errors vs expected behavior
- Tray tests may fail gracefully (this is acceptable)

#### 5. Permission Denied

**Problem**: Cannot execute test scripts

**Solution**:
```bash
chmod +x tests/e2e/*.sh
```text
## Best Practices

### For Developers

1. **Run E2E tests before committing** packaging changes
   ```bash
   make test-e2e
   ```

2. **Test on multiple Fedora versions** using matrix
   ```bash
   # Build for Fedora 39
   podman build --build-arg FEDORA_VERSION=39 -t test:f39 -f tests/e2e/Dockerfile.fedora .
   ```

3. **Keep tests fast** by using `--skip-build` when iterating
   ```bash
   make test-e2e-fast
   ```

4. **Review test logs** when failures occur
   ```bash
   cat rpmbuild/test-artifacts/*.log
   ```

### For CI/CD

1. **Cache test images** to speed up builds
2. **Upload artifacts** for debugging
3. **Run tests in parallel** when possible
4. **Set reasonable timeouts** (tests should complete in < 10 minutes)

## Test Coverage

### What's Tested ✅

- RPM package structure and metadata
- File installation to correct locations
- File permissions and ownership
- System configuration files
- User configuration creation
- CLI wrapper script functionality
- Desktop file integration
- Icon installation (system and user)
- Python module imports
- Application process lifecycle
- GUI initialization (with Xvfb)
- Config fallback logic (system → user)
- Package removal and cleanup

### What's Not Tested ⚠️

- Real GUI interaction (Xvfb limitations)
- Actual torrent seeding (integration test)
- Network connectivity
- Long-running process stability
- Multi-user scenarios
- Upgrade scenarios (future enhancement)

## Future Enhancements

- [ ] Multi-distro testing (CentOS, AlmaLinux, Rocky)
- [ ] Upgrade testing (old version → new version)
- [ ] Performance benchmarks
- [ ] Memory leak detection
- [ ] Network simulation for torrent testing
- [ ] Real GUI testing with VNC
- [ ] Multi-user installation scenarios
- [ ] SELinux context testing

## Resources

- [RPM Packaging Guide](https://rpm-packaging-guide.github.io/)
- [Docker Testing Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [GTK Testing](https://docs.gtk.org/gtk4/running.html)
- [Xvfb Documentation](https://www.x.org/releases/X11R7.6/doc/man/man1/Xvfb.1.xhtml)

## Support

For issues with E2E tests:
- Check logs in `rpmbuild/test-artifacts/`
- Review test script output
- Verify container engine is working: `podman run hello-world`
- GitHub Issues: <<https://github.com/dmzoneill/DFakeSeeder/issues>>

---

**Last Updated**: 2024-11-27
**Test Framework Version**: 1.0
