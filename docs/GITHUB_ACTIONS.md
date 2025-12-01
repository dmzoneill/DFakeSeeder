# GitHub Actions CI/CD

This document describes the GitHub Actions workflows used for continuous integration and testing of DFakeSeeder.

## Workflows Overview

### 1. Main CI/CD Workflow (`.github/workflows/main.yml`)

**Triggers:**
- Push to `main` branch
- Pull requests to `main` branch

**Purpose:**
- Uses a reusable workflow for standard CI/CD tasks
- Builds PyPI packages, Debian packages, RPM packages, and Docker images
- Runs basic code validation and linting

**Configuration:**
```yaml
pypi-extension: "true"
deb-build: "true"
rpm-build: "true"
docker-build: "true"
```

### 2. RPM End-to-End Tests (`.github/workflows/rpm-e2e-tests.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` branch
- Manual workflow dispatch

**Test Matrix:**
- Fedora versions: `latest`, `39`, `38`

**Test Steps:**
1. **Build Phase**
   - Checkout code
   - Set up Python 3.11
   - Install system dependencies (rpm, rpmlint, xmllint, GTK4)
   - Build UI components
   - Run linting
   - Build RPM package

2. **Validation Phase**
   - List RPM contents
   - Validate with rpmlint
   - Build E2E test Docker container

3. **Testing Phase**
   - Run installation tests in Docker
   - Run launch tests with Xvfb (headless GTK)
   - Generate test reports

4. **Artifacts**
   - RPM packages (30 days retention)
   - Test artifacts (7 days retention)
   - Test summary report

**PyPI Compatibility Test:**
- Basic import testing
- CLI entry point verification
- Uploads PyPI packages as artifacts

### 3. PyPI End-to-End Tests (`.github/workflows/pypi-e2e-tests.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` branch
- Manual workflow dispatch

**Test Matrix:**
- **Fedora Tests**: Fedora `latest`, `42`, `41`
- **Ubuntu Tests**: Ubuntu `22.04`, `24.04`

#### Job 1: Fedora E2E Tests (`pypi-e2e-tests`)

**Test Steps:**
1. **Build Phase**
   - Checkout code
   - Set up Python 3.11
   - Install build dependencies
   - Build UI components
   - Build Python wheel and sdist packages

2. **Validation Phase**
   - Verify package contents (setup_helper, post_install, desktop files)
   - Build E2E test Docker container for each Fedora version

3. **Testing Phase (in Docker)**
   - Install package with pip
   - Run comprehensive E2E test suite:
     - Python module imports (5 tests)
     - CLI commands availability (6 tests)
     - Help command functionality (1 test)
     - Setup command functionality (1 test)
     - Desktop integration installation (3 tests)
     - User config creation (1 test)
     - Config validation (1 test)
     - Application launch and initialization (2 tests)
     - Desktop integration uninstallation (3 tests)
   - **Total: 23+ tests per Fedora version**

4. **Artifacts**
   - Test logs and reports
   - PyPI packages (wheel + sdist)
   - 7-day retention for test artifacts
   - 30-day retention for packages

#### Job 2: Ubuntu E2E Tests (`pypi-ubuntu-e2e-tests`)

**Test Steps:**
1. **Environment Setup**
   - Install GTK4, LibAdwaita, PyGObject on Ubuntu
   - Install Xvfb for headless testing

2. **Package Tests**
   - Build and install PyPI package
   - Test Python imports
   - Test all CLI commands:
     - `dfs`, `dfakeseeder`
     - `dfs-setup`
     - `dfs-install-desktop`, `dfs-uninstall-desktop`

3. **Functional Tests**
   - Test `dfs-setup` dependency checking
   - Test desktop integration install/uninstall
   - Test headless application launch

4. **Artifacts**
   - Setup and launch output logs
   - 7-day retention

#### Job 3: Test Summary (`test-summary`)

**Depends on:** Both Fedora and Ubuntu test jobs

**Runs:** Always (even if tests fail)

**Actions:**
1. Downloads all test artifacts
2. Generates comprehensive test summary report
3. Lists all test results by OS version
4. Creates markdown summary with:
   - Test execution metadata
   - Results per OS version
   - Artifact listing

5. **PR Comments**
   - Automatically comments test results on pull requests
   - Provides immediate feedback to contributors

## Test Coverage

### What's Tested

#### RPM E2E Tests
- ✅ RPM package building and structure
- ✅ RPM installation on Fedora
- ✅ System-level file installation
- ✅ Wrapper script functionality
- ✅ Application launch in Docker/headless environment
- ✅ Core component initialization

#### PyPI E2E Tests (Fedora)
- ✅ Python package building (wheel + sdist)
- ✅ Package contents verification
- ✅ pip installation process
- ✅ Python module imports
- ✅ All CLI command entry points
- ✅ `dfs-setup` automated setup process
- ✅ System dependency checking
- ✅ Desktop integration installation
- ✅ User configuration creation
- ✅ Application launch and initialization
- ✅ Desktop integration uninstallation
- ✅ Package uninstallation

#### PyPI E2E Tests (Ubuntu)
- ✅ Cross-distribution compatibility
- ✅ GTK4 environment on Debian/Ubuntu
- ✅ Package installation on Ubuntu LTS versions
- ✅ Command-line interface functionality
- ✅ Desktop integration on Ubuntu

### What's Not Tested (Limitations)

- ❌ Real desktop environment interactions (headless only)
- ❌ System tray functionality (requires running desktop)
- ❌ User interface interactions (no UI automation)
- ❌ Multi-user scenarios
- ❌ Network interactions with real trackers
- ❌ Long-running seeding scenarios

## Manual Workflow Triggering

All E2E test workflows can be triggered manually via GitHub Actions UI:

1. Go to **Actions** tab in GitHub repository
2. Select the workflow (RPM or PyPI E2E Tests)
3. Click **Run workflow**
4. Select branch
5. Click **Run workflow** button

This is useful for:
- Testing before merging
- Debugging test failures
- Validating fixes
- Testing on different OS versions

## Artifacts

### Available Artifacts

**RPM E2E Tests:**
- `dfakeseeder-rpm-fedora-{version}` (30 days)
  - Built RPM packages
- `e2e-test-artifacts-fedora-{version}` (7 days)
  - Test logs and output

**PyPI E2E Tests:**
- `dfakeseeder-pypi-package-fedora-{version}` (30 days)
  - Wheel and sdist packages
- `pypi-e2e-test-artifacts-fedora-{version}` (7 days)
  - Test logs and reports
- `pypi-ubuntu-test-artifacts-{version}` (7 days)
  - Ubuntu test output
- `pypi-e2e-test-summary` (30 days)
  - Comprehensive test summary

### Downloading Artifacts

1. Go to **Actions** tab
2. Select a workflow run
3. Scroll down to **Artifacts** section
4. Click artifact name to download

## CI/CD Best Practices

### When Tests Run

**Automatically:**
- Every push to `main` or `develop`
- Every pull request to `main`

**Benefits:**
- Early detection of breakage
- Ensures all branches are tested
- Validates PRs before merge
- Builds packages for testing

### Test Failure Handling

**Strategy:**
```yaml
fail-fast: false
```

This ensures all OS versions are tested even if one fails, providing comprehensive results.

**Continuation:**
```yaml
continue-on-error: true
```

Used for non-critical steps like linting to prevent blocking builds on warnings.

## Local Testing

Before pushing changes, you can run tests locally:

### RPM E2E Tests
```bash
# Build and test RPM
make rpm
make test-e2e-rpm
```

### PyPI E2E Tests
```bash
# Build and test PyPI package
make pypi-build
make test-e2e-pypi
```

This provides faster feedback than waiting for CI/CD.

## Debugging Failed Tests

### Check Workflow Logs

1. Go to failed workflow run
2. Expand failed step
3. Review error output

### Download Test Artifacts

1. Download test artifacts from failed run
2. Check test logs for detailed errors:
   - `pypi-e2e-test-fedora-{version}.log`
   - `setup-output.txt`
   - `launch-output.txt`

### Common Issues

**Missing Dependencies:**
- Check `dfs-setup` output in logs
- Verify Dockerfile has all required packages

**Test Timeouts:**
- Application may be slow to start in Docker
- Increase timeout values if needed

**Import Errors:**
- Check MANIFEST.in includes all files
- Verify setup.py package_data is correct

**Docker Issues:**
- Ensure Dockerfile builds successfully
- Check for permission issues with volumes

## Adding New Tests

### To RPM E2E Tests

1. Edit `tests/e2e/test_rpm_installation.sh` or `test_rpm_launch.sh`
2. Add test function
3. Call function in main test sequence
4. Test locally with `make test-e2e-rpm`
5. Commit and push

### To PyPI E2E Tests

1. Edit `tests/e2e/test_pypi_install.sh`
2. Add test function
3. Call function in main test sequence
4. Test locally with `make test-e2e-pypi`
5. Commit and push

## Monitoring Test Results

### GitHub Checks

All PR commits show test status:
- ✅ Green checkmark: All tests passed
- ❌ Red X: Tests failed
- 🟡 Yellow circle: Tests in progress

### Status Badge

Add to README.md:
```markdown
![RPM E2E Tests](https://github.com/dmzoneill/DFakeSeeder/workflows/RPM%20End-to-End%20Tests/badge.svg)
![PyPI E2E Tests](https://github.com/dmzoneill/DFakeSeeder/workflows/PyPI%20End-to-End%20Tests/badge.svg)
```

## Future Enhancements

Potential improvements to CI/CD:

- [ ] Add macOS PyPI testing
- [ ] Add Windows PyPI testing (if GTK4 support improves)
- [ ] Add UI automation testing with dogtail
- [ ] Add performance benchmarking
- [ ] Add security scanning (Snyk, SAST)
- [ ] Add code coverage reporting
- [ ] Add automatic version bumping
- [ ] Add automatic PyPI publishing on release
- [ ] Add nightly builds for testing development changes

## Related Documentation

- [PACKAGING.md](PACKAGING.md) - Package building documentation
- [PYPI_INSTALLATION.md](PYPI_INSTALLATION.md) - PyPI installation guide
- [../tests/e2e/README.md](../tests/e2e/README.md) - E2E test documentation (if exists)
