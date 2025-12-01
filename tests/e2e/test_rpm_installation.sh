#!/bin/bash
# End-to-end RPM installation test script
# Tests: RPM installation, file placement, dependencies

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0
TEST_RESULTS=()

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Test assertion functions
assert_success() {
    local description="$1"
    shift

    if "$@"; then
        log_info "✓ $description"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        TEST_RESULTS+=("PASS: $description")
        return 0
    else
        log_error "✗ $description"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        TEST_RESULTS+=("FAIL: $description")
        return 1
    fi
}

assert_file_exists() {
    local file="$1"
    local description="$2"

    if [ -f "$file" ]; then
        log_info "✓ $description: $file exists"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        TEST_RESULTS+=("PASS: $description")
        return 0
    else
        log_error "✗ $description: $file not found"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        TEST_RESULTS+=("FAIL: $description")
        return 1
    fi
}

assert_dir_exists() {
    local dir="$1"
    local description="$2"

    if [ -d "$dir" ]; then
        log_info "✓ $description: $dir exists"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        TEST_RESULTS+=("PASS: $description")
        return 0
    else
        log_error "✗ $description: $dir not found"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        TEST_RESULTS+=("FAIL: $description")
        return 1
    fi
}

assert_command_exists() {
    local cmd="$1"
    local description="$2"

    if command -v "$cmd" &> /dev/null; then
        log_info "✓ $description: $cmd found"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        TEST_RESULTS+=("PASS: $description")
        return 0
    else
        log_error "✗ $description: $cmd not found"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        TEST_RESULTS+=("FAIL: $description")
        return 1
    fi
}

# Print test header
print_header() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
    echo ""
}

# Print test summary
print_summary() {
    echo ""
    echo "=========================================="
    echo "TEST SUMMARY"
    echo "=========================================="
    echo ""
    echo "Tests Passed: $TESTS_PASSED"
    echo "Tests Failed: $TESTS_FAILED"
    echo "Total Tests:  $((TESTS_PASSED + TESTS_FAILED))"
    echo ""

    if [ $TESTS_FAILED -eq 0 ]; then
        log_info "All tests passed! ✓"
        return 0
    else
        log_error "Some tests failed! ✗"
        echo ""
        echo "Failed tests:"
        for result in "${TEST_RESULTS[@]}"; do
            case "$result" in
                FAIL:*)
                    echo "  - ${result#FAIL: }"
                    ;;
            esac
        done
        return 1
    fi
}

# Main test execution
main() {
    print_header "RPM Installation End-to-End Tests"

    # Find RPM file
    log_info "Searching for RPM file..."
    RPM_FILE=$(find /rpms -name "dfakeseeder-*.rpm" 2>/dev/null | head -1)

    if [ -z "$RPM_FILE" ]; then
        log_error "No RPM file found in /rpms directory"
        exit 1
    fi

    log_info "Found RPM: $RPM_FILE"

    # Test 1: RPM file validation
    print_header "Test 1: RPM File Validation"

    assert_success "RPM file is readable" test -r "$RPM_FILE"

    # Check RPM extension (using case statement for POSIX compatibility)
    case "$RPM_FILE" in
        *.rpm)
            log_info "✓ RPM file has .rpm extension"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            ;;
        *)
            log_error "✗ RPM file has .rpm extension"
            TESTS_FAILED=$((TESTS_FAILED + 1))
            ;;
    esac

    # Validate RPM structure
    log_info "Validating RPM structure..."
    if rpm -qp "$RPM_FILE" &> /dev/null; then
        log_info "✓ RPM file structure is valid"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "✗ RPM file structure is invalid"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        exit 1
    fi

    # Show RPM info
    log_info "RPM Package Information:"
    rpm -qip "$RPM_FILE" 2>/dev/null || true

    # Test 2: RPM Installation
    print_header "Test 2: RPM Installation"

    log_info "Installing RPM..."
    if sudo rpm -ivh "$RPM_FILE" 2>&1 | tee /tmp/rpm-install.log; then
        log_info "✓ RPM installation completed"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "✗ RPM installation failed"
        cat /tmp/rpm-install.log
        TESTS_FAILED=$((TESTS_FAILED + 1))
        exit 1
    fi

    # Test 3: Installed Files Verification
    print_header "Test 3: Installed Files Verification"

    # Application files
    assert_dir_exists "/opt/dfakeseeder" "Application directory installed"
    assert_dir_exists "/opt/dfakeseeder/d_fake_seeder" "D' Fake Seeder package directory installed"
    assert_file_exists "/opt/dfakeseeder/d_fake_seeder/dfakeseeder.py" "Main application file installed"
    assert_file_exists "/opt/dfakeseeder/d_fake_seeder/dfakeseeder_tray.py" "Tray application file installed"

    # Application subdirectories
    assert_dir_exists "/opt/dfakeseeder/d_fake_seeder/config" "Config directory installed"
    assert_dir_exists "/opt/dfakeseeder/d_fake_seeder/components" "Components directory installed"
    assert_dir_exists "/opt/dfakeseeder/d_fake_seeder/lib" "Lib directory installed"
    assert_dir_exists "/opt/dfakeseeder/d_fake_seeder/domain" "Domain directory installed"
    assert_dir_exists "/opt/dfakeseeder/d_fake_seeder/components/locale" "Locale directory installed"

    # System configuration
    assert_dir_exists "/etc/dfakeseeder" "System config directory created"
    assert_file_exists "/etc/dfakeseeder/default.json" "System default config installed"

    # Wrapper script
    assert_file_exists "/usr/bin/dfakeseeder" "Wrapper script installed"
    assert_success "Wrapper script is executable" test -x "/usr/bin/dfakeseeder"

    # Desktop integration
    assert_file_exists "/usr/share/applications/dfakeseeder.desktop" "Desktop file installed"

    # Icons (check a few key sizes)
    assert_file_exists "/usr/share/icons/hicolor/48x48/apps/dfakeseeder.png" "Icon 48x48 installed"
    assert_file_exists "/usr/share/icons/hicolor/128x128/apps/dfakeseeder.png" "Icon 128x128 installed"
    assert_file_exists "/usr/share/icons/hicolor/256x256/apps/dfakeseeder.png" "Icon 256x256 installed"

    # Test 4: File Permissions
    print_header "Test 4: File Permissions"

    assert_success "Config is readable" test -r "/etc/dfakeseeder/default.json"
    assert_success "Wrapper script is executable" test -x "/usr/bin/dfakeseeder"
    assert_success "Application is readable" test -r "/opt/dfakeseeder/d_fake_seeder/dfakeseeder.py"

    # Test 5: System Integration
    print_header "Test 5: System Integration"

    # Check if command is in PATH
    assert_command_exists "dfakeseeder" "dfakeseeder command in PATH"

    # Validate desktop file
    if desktop-file-validate /usr/share/applications/dfakeseeder.desktop 2>&1; then
        log_info "✓ Desktop file is valid"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_warning "Desktop file validation warnings (may be acceptable)"
    fi

    # Test 6: Configuration System
    print_header "Test 6: Configuration System"

    # Validate system config JSON
    if python3 -m json.tool /etc/dfakeseeder/default.json > /dev/null 2>&1; then
        log_info "✓ System config is valid JSON"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "✗ System config is invalid JSON"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    # Check for required config fields
    log_info "Checking config structure..."
    CONFIG_FIELDS=("upload_speed" "download_speed" "torrents" "agents" "peer_protocol")
    for field in "${CONFIG_FIELDS[@]}"; do
        if grep -q "\"$field\"" /etc/dfakeseeder/default.json; then
            log_info "✓ Config contains '$field' field"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_error "✗ Config missing '$field' field"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    done

    # Test 7: Wrapper Script Functionality
    print_header "Test 7: Wrapper Script Functionality"

    # Test --help option
    if /usr/bin/dfakeseeder --help 2>&1 | grep -q "D' Fake Seeder"; then
        log_info "✓ Wrapper script --help works"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_warning "Wrapper script --help output unexpected"
    fi

    # Test 8: RPM Query
    print_header "Test 8: RPM Query"

    # Check package is installed
    if rpm -q dfakeseeder &> /dev/null; then
        log_info "✓ Package is registered in RPM database"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "✗ Package not found in RPM database"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    # List all installed files
    log_info "Installed files count: $(rpm -ql dfakeseeder | wc -l)"

    # Test 9: Dependencies
    print_header "Test 9: Dependencies"

    log_info "Checking Python dependencies..."
    PYTHON_DEPS=("requests" "watchdog" "bencodepy" "gi")
    for dep in "${PYTHON_DEPS[@]}"; do
        if python3 -c "import $dep" 2>/dev/null; then
            log_info "✓ Python module '$dep' available"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_error "✗ Python module '$dep' not available"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    done

    # Print final summary
    print_summary
}

# Run tests
main "$@"
