# E2E Testing Quick Start Guide

**One command. Fully automated. 60+ tests.**

## Quick Start

### Run All Tests
```bash
make test-e2e
```

That's it! This will:
- ✅ Build RPM
- ✅ Create test container
- ✅ Run 60+ automated tests
- ✅ Generate test report

**Time: ~10 minutes**

## Common Commands

```bash
# Full test suite
make test-e2e                    # Everything

# Specific tests
make test-e2e-install            # Only installation tests (42 tests)
make test-e2e-launch             # Only launch tests (16 tests)
make test-e2e-uninstall          # Only uninstall tests (3 tests)

# Fast iteration
make test-e2e-fast               # Skip build, use existing RPM

# Maintenance
make test-e2e-build-image        # Rebuild test container
make clean-e2e                   # Clean test artifacts
```

## What Gets Tested

### Installation (42 tests)
- RPM file validation
- File installation (40+ files checked)
- Permissions
- System integration
- Configuration
- Dependencies

### Launch (16 tests)
- Config creation
- Application startup
- Python imports
- Desktop integration
- GUI initialization (headless)

### Uninstall (3 tests)
- Package removal
- Database cleanup
- Verification

## Test Output

```
========================================
RPM Installation End-to-End Tests
========================================

[INFO] ✓ RPM file is readable
[INFO] ✓ RPM file structure is valid
[INFO] ✓ Application directory installed
[INFO] ✓ Main application file installed
[INFO] ✓ System default config installed
[INFO] ✓ Wrapper script installed
[INFO] ✓ Wrapper script is executable
[INFO] ✓ Desktop file installed
[INFO] ✓ Icon 48x48 installed
...

========================================
TEST SUMMARY
========================================

Tests Passed: 42
Tests Failed: 0
Total Tests:  42

[INFO] All tests passed! ✓
```

## Prerequisites

```bash
# Install container engine (choose one)
sudo dnf install podman  # Recommended
# or
sudo dnf install docker
```

## Troubleshooting

### Tests Fail

**Check logs:**
```bash
cat rpmbuild/test-artifacts/*.log
```

**Run specific test:**
```bash
make test-e2e-install  # Just installation
```

**Debug container:**
```bash
podman run -it dfakeseeder-e2e-test:latest /bin/bash
```

### RPM Not Found

```bash
# Build RPM first
make rpm

# Verify location
ls -la rpmbuild/RPMS/noarch/dfakeseeder-*.rpm
```

### Container Engine Not Found

```bash
# Install podman
sudo dnf install podman

# Or docker
sudo dnf install docker
sudo systemctl start docker
```

## Advanced Usage

### Custom Test Execution

```bash
# Run with options
tests/e2e/run_e2e_tests.sh --skip-build   # Use existing RPM
tests/e2e/run_e2e_tests.sh --test install # Only installation
tests/e2e/run_e2e_tests.sh --cleanup      # Clean after
```

### Manual Container Testing

```bash
# Build container
cd tests/e2e
podman build -t dfakeseeder-e2e-test:latest -f Dockerfile.fedora .

# Run tests
podman run --rm \
  -v $(pwd)/../../rpmbuild/RPMS:/rpms:ro \
  -v $(pwd):/workspace/tests:ro \
  dfakeseeder-e2e-test:latest \
  /bin/bash /workspace/tests/test_rpm_installation.sh
```

## CI/CD Integration

### GitHub Actions

Tests run automatically on:
- Push to main/develop
- Pull requests
- Manual trigger

**Matrix**: Fedora latest, 39, 38

**Artifacts**: RPMs, test reports, logs

## Test Reports

**Location**: `rpmbuild/test-artifacts/e2e-test-report.txt`

```
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
```

## Documentation

- **Full Guide**: `tests/e2e/README.md` (500+ lines)
- **Summary**: `E2E_TESTING_SUMMARY.md`
- **This Guide**: `E2E_TESTING_QUICK_START.md`

## Key Features

✅ **Fully Automated** - One command
✅ **Fast** - ~10 minutes total
✅ **Comprehensive** - 60+ tests
✅ **CI/CD Ready** - GitHub Actions
✅ **Isolated** - Clean containers
✅ **Reproducible** - 100% consistent

## Development Workflow

```bash
# 1. Make packaging changes
vim dfakeseeder.spec

# 2. Run E2E tests
make test-e2e

# 3. If tests pass, commit
git add .
git commit -m "Update packaging"

# 4. CI runs tests automatically
git push
```

## Best Practices

✅ Run `make test-e2e` before committing
✅ Use `make test-e2e-fast` for iteration
✅ Check logs when tests fail
✅ Keep container image updated

## Need Help?

- **Logs**: `rpmbuild/test-artifacts/*.log`
- **Docs**: `tests/e2e/README.md`
- **Issues**: https://github.com/dmzoneill/DFakeSeeder/issues

---

**Version**: 1.0
**Last Updated**: 2024-11-27
