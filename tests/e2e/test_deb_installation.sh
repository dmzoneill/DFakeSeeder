#!/bin/bash
# End-to-end Debian package installation test script
# Tests: dpkg install, package contents, dependencies

set -e
set -u

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test tracking
TESTS_PASSED=0
TESTS_FAILED=0

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Test: DEB package file exists
test_deb_file_exists() {
    log_info "Test: DEB package file exists"

    DEB_FILE=$(find /debs -name "dfakeseeder*.deb" | head -1)
    if [ -n "$DEB_FILE" ] && [ -f "$DEB_FILE" ]; then
        log_info "✓ DEB package found: $DEB_FILE"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        export DEB_FILE
    else
        log_error "✗ DEB package not found in /debs"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        exit 1
    fi
}

# Test: DEB package info
test_deb_package_info() {
    log_info "Test: DEB package metadata"

    if dpkg -I "$DEB_FILE" | grep -q "Package: dfakeseeder"; then
        log_info "✓ Package name correct"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "✗ Package name incorrect"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    if dpkg -I "$DEB_FILE" | grep -q "Version:"; then
        log_info "✓ Package version present"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "✗ Package version missing"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    if dpkg -I "$DEB_FILE" | grep -q "Architecture: all"; then
        log_info "✓ Architecture correct (all)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "✗ Architecture incorrect"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Test: DEB package contents
test_deb_contents() {
    log_info "Test: DEB package contents"

    REQUIRED_PATHS=(
        "opt/dfakeseeder/dfakeseeder.py"
        "opt/dfakeseeder/dfakeseeder_tray.py"
        "opt/dfakeseeder/model.py"
        "opt/dfakeseeder/view.py"
        "opt/dfakeseeder/controller.py"
        "opt/dfakeseeder/config/"
        "opt/dfakeseeder/lib/"
        "opt/dfakeseeder/domain/"
        "opt/dfakeseeder/components/"
        "usr/bin/dfakeseeder"
        "usr/bin/dfs"
        "usr/share/applications/dfakeseeder.desktop"
    )

    for path in "${REQUIRED_PATHS[@]}"; do
        if dpkg -c "$DEB_FILE" | grep -q "$path"; then
            log_info "✓ Contains: $path"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_error "✗ Missing: $path"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    done
}

# Test: Install DEB package
test_deb_install() {
    log_info "Test: DEB package installation"

    # Install dependencies first (apt will handle this but we test it explicitly)
    apt-get update -qq

    if dpkg -i "$DEB_FILE" 2>&1; then
        log_info "✓ DEB package installed successfully"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_warning "Initial install failed, trying with apt-get -f install"
        # Install missing dependencies
        apt-get install -f -y

        if dpkg -i "$DEB_FILE"; then
            log_info "✓ DEB package installed after dependency resolution"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_error "✗ DEB package installation failed"
            TESTS_FAILED=$((TESTS_FAILED + 1))
            return 1
        fi
    fi
}

# Test: Verify installed files
test_installed_files() {
    log_info "Test: Verify installed files exist"

    INSTALLED_FILES=(
        "/opt/dfakeseeder/dfakeseeder.py"
        "/opt/dfakeseeder/dfakeseeder_tray.py"
        "/opt/dfakeseeder/model.py"
        "/opt/dfakeseeder/view.py"
        "/opt/dfakeseeder/controller.py"
        "/opt/dfakeseeder/config"
        "/opt/dfakeseeder/lib"
        "/opt/dfakeseeder/domain"
        "/opt/dfakeseeder/components"
        "/usr/bin/dfakeseeder"
        "/usr/bin/dfs"
        "/usr/share/applications/dfakeseeder.desktop"
    )

    for file in "${INSTALLED_FILES[@]}"; do
        if [ -e "$file" ]; then
            log_info "✓ Installed: $file"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_error "✗ Not found: $file"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    done
}

# Test: Wrapper script is executable
test_wrapper_executable() {
    log_info "Test: Wrapper scripts are executable"

    if [ -x /usr/bin/dfakeseeder ]; then
        log_info "✓ /usr/bin/dfakeseeder is executable"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "✗ /usr/bin/dfakeseeder is not executable"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    if [ -x /usr/bin/dfs ]; then
        log_info "✓ /usr/bin/dfs is executable"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "✗ /usr/bin/dfs is not executable"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Test: Desktop file validation
test_desktop_file() {
    log_info "Test: Desktop file validation"

    DESKTOP_FILE="/usr/share/applications/dfakeseeder.desktop"

    if [ -f "$DESKTOP_FILE" ]; then
        log_info "✓ Desktop file exists"
        TESTS_PASSED=$((TESTS_PASSED + 1))

        # Check desktop file uses wrapper
        if grep -q "Exec=/usr/bin/dfakeseeder" "$DESKTOP_FILE"; then
            log_info "✓ Desktop file uses wrapper script"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_error "✗ Desktop file doesn't use wrapper script"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi

        # Validate desktop file with desktop-file-validate if available
        if command -v desktop-file-validate &> /dev/null; then
            if desktop-file-validate "$DESKTOP_FILE" 2>/dev/null; then
                log_info "✓ Desktop file is valid"
                TESTS_PASSED=$((TESTS_PASSED + 1))
            else
                log_warning "Desktop file validation warnings (non-critical)"
            fi
        fi
    else
        log_error "✗ Desktop file not found"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Test: Python dependencies installed
test_python_dependencies() {
    log_info "Test: Python dependencies from pip"

    # Check bencodepy
    if python3 -c "import bencodepy" 2>/dev/null; then
        log_info "✓ bencodepy is installed"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "✗ bencodepy not found (postinst may have failed)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    # Check typer
    if python3 -c "import typer" 2>/dev/null; then
        log_info "✓ typer is installed"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "✗ typer not found (postinst may have failed)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Test: System dependencies installed
test_system_dependencies() {
    log_info "Test: System dependencies"

    REQUIRED_PACKAGES=(
        "python3"
        "python3-pip"
        "python3-gi"
        "gir1.2-gtk-4.0"
        "libadwaita-1-0"
        "gir1.2-adw-1"
        "python3-requests"
        "python3-urllib3"
        "python3-watchdog"
    )

    for pkg in "${REQUIRED_PACKAGES[@]}"; do
        if dpkg -l | grep -q "^ii.*$pkg"; then
            log_info "✓ Package installed: $pkg"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_error "✗ Package missing: $pkg"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    done
}

# Test: Package can be queried
test_package_query() {
    log_info "Test: Package query with dpkg"

    if dpkg -l dfakeseeder | grep -q "^ii"; then
        log_info "✓ Package is installed and registered"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "✗ Package not properly registered"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    # List installed files
    if dpkg -L dfakeseeder > /tmp/deb-files.txt; then
        FILE_COUNT=$(wc -l < /tmp/deb-files.txt)
        log_info "✓ Package owns $FILE_COUNT files"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "✗ Cannot list package files"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Test: Uninstall package
test_uninstall() {
    log_info "Test: Package uninstallation"

    if dpkg -r dfakeseeder; then
        log_info "✓ Package uninstalled successfully"
        TESTS_PASSED=$((TESTS_PASSED + 1))

        # Verify key files removed
        if [ ! -f /usr/bin/dfakeseeder ]; then
            log_info "✓ Wrapper script removed"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_error "✗ Wrapper script still exists"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi

        if [ ! -f /usr/share/applications/dfakeseeder.desktop ]; then
            log_info "✓ Desktop file removed"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_error "✗ Desktop file still exists"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        log_error "✗ Package uninstallation failed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Main test execution
main() {
    echo "=========================================="
    echo "Debian Package Installation Tests"
    echo "=========================================="
    echo ""

    # Run tests
    test_deb_file_exists
    test_deb_package_info
    test_deb_contents
    test_deb_install
    test_installed_files
    test_wrapper_executable
    test_desktop_file
    test_python_dependencies
    test_system_dependencies
    test_package_query
    test_uninstall

    # Summary
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
        exit 0
    else
        log_error "Some tests failed! ✗"
        exit 1
    fi
}

# Run tests
main "$@"
