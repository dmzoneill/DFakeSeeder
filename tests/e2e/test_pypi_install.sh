#!/bin/bash
# End-to-end Python package installation test script
# Tests: pip install, desktop integration, application launch, uninstall

set -e
set -u

# Add user's local bin to PATH for pip-installed commands
export PATH="$HOME/.local/bin:$PATH"

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

# Start Xvfb (virtual X server for headless GUI testing)
start_xvfb() {
    log_info "Starting Xvfb virtual display..."

    # Kill any existing Xvfb on :99
    pkill -9 Xvfb || true
    sleep 1

    # Start Xvfb with software rendering support
    Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
    XVFB_PID=$!
    export DISPLAY=:99

    # Set GTK/GDK environment for headless operation
    export GDK_BACKEND=x11
    export LIBGL_ALWAYS_SOFTWARE=1
    export GALLIUM_DRIVER=llvmpipe
    export MESA_GL_VERSION_OVERRIDE=3.3
    export GTK_A11Y=none
    export NO_AT_BRIDGE=1

    # Disable GTK animations and effects for faster startup
    export GTK_THEME=Adwaita
    export GTK_DEBUG=no-css-cache

    # Wait for X server to be ready
    log_info "Waiting for X server..."
    for i in {1..10}; do
        if xdpyinfo -display :99 >/dev/null 2>&1; then
            log_info "✓ X server ready"
            return 0
        fi
        sleep 1
    done

    log_error "X server failed to start"
    return 1
}

# Stop Xvfb
stop_xvfb() {
    if [ -n "${XVFB_PID:-}" ]; then
        log_info "Stopping Xvfb..."
        kill $XVFB_PID 2>/dev/null || true
    fi
    pkill -9 Xvfb || true
}

# Test: Python module imports
test_python_imports() {
    log_info "Test: Python module imports after installation"

    # Test critical imports
    IMPORTS=(
        "d_fake_seeder.domain.app_settings"
        "d_fake_seeder.lib.logger"
        "d_fake_seeder.controller"
        "d_fake_seeder.model"
        "d_fake_seeder.view"
    )

    for import_path in "${IMPORTS[@]}"; do
        if python3 -c "import $import_path" 2>/dev/null; then
            log_info "✓ Can import: $import_path"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_error "✗ Cannot import: $import_path"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    done
}

# Test: CLI commands available
test_cli_commands() {
    log_info "Test: CLI commands availability"

    COMMANDS=(
        "dfs"
        "dfakeseeder"
        "dfs-tray"
        "dfs-setup"
        "dfs-install-desktop"
        "dfs-uninstall-desktop"
    )

    for cmd in "${COMMANDS[@]}"; do
        if command -v "$cmd" &> /dev/null; then
            log_info "✓ Command available: $cmd"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_error "✗ Command not found: $cmd"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    done
}

# Test: Help command works
test_help_command() {
    log_info "Test: Help command functionality"

    if dfs --help 2>&1 | grep -q "D' Fake Seeder\|Usage"; then
        log_info "✓ Help command works"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "✗ Help command failed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Test: Setup command works
test_setup_command() {
    log_info "Test: Setup command functionality"

    # Run setup in non-interactive mode (won't prompt for desktop integration)
    # Just verify it checks dependencies and prints guidance
    if dfs-setup 2>&1 | grep -q "Setting up D' Fake Seeder\\|SYSTEM DEPENDENCIES\\|LAUNCH INSTRUCTIONS"; then
        log_info "✓ Setup command works and checks dependencies"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "✗ Setup command failed or didn't produce expected output"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Test: Desktop integration installation
test_desktop_integration() {
    log_info "Test: Desktop integration installation"

    # Remove any existing desktop integration
    rm -rf ~/.local/share/applications/dfakeseeder.desktop
    rm -rf ~/.local/share/icons/hicolor/*/apps/dfakeseeder.png

    # Install desktop integration
    if dfs-install-desktop 2>&1; then
        log_info "✓ Desktop integration installation completed"
        TESTS_PASSED=$((TESTS_PASSED + 1))

        # Check if desktop file was created
        if [ -f ~/.local/share/applications/dfakeseeder.desktop ]; then
            log_info "✓ Desktop file created"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_error "✗ Desktop file not created"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi

        # Check if icons were installed
        if ls ~/.local/share/icons/hicolor/*/apps/dfakeseeder.png &> /dev/null; then
            log_info "✓ Icons installed"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_error "✗ Icons not installed"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        log_error "✗ Desktop integration installation failed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Test: User config creation
test_user_config_creation() {
    log_info "Test: User config creation on first launch"

    # Remove existing config
    rm -rf ~/.config/dfakeseeder

    # Start D-Bus session for GTK
    eval $(dbus-launch --sh-syntax)
    export DBUS_SESSION_BUS_ADDRESS

    # Launch app in background with timeout
    log_info "Launching application to trigger config creation..."
    (
        export GDK_BACKEND=x11
        export LIBGL_ALWAYS_SOFTWARE=1
        export GALLIUM_DRIVER=llvmpipe
        export GTK_A11Y=none
        export NO_AT_BRIDGE=1
        timeout 15s dfs 2>&1 | head -20 &
    )
    APP_PID=$!

    # Wait for config to be created
    for i in {1..30}; do
        if [ -f ~/.config/dfakeseeder/settings.json ]; then
            log_info "✓ User config created"
            TESTS_PASSED=$((TESTS_PASSED + 1))

            # Kill app and dbus
            kill $APP_PID 2>/dev/null || true
            kill $DBUS_SESSION_BUS_PID 2>/dev/null || true
            return 0
        fi
        sleep 0.5
    done

    log_error "✗ User config not created"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    kill $APP_PID 2>/dev/null || true
    kill $DBUS_SESSION_BUS_PID 2>/dev/null || true
    return 1
}

# Test: Config validation
test_config_validation() {
    log_info "Test: Config file validation"

    # Check if user config exists
    if [ ! -f ~/.config/dfakeseeder/settings.json ]; then
        log_error "✗ User config not found"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi

    # Validate JSON
    if python3 -m json.tool ~/.config/dfakeseeder/settings.json > /dev/null 2>&1; then
        log_info "✓ User config is valid JSON"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "✗ User config is invalid JSON"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi

    # Check if torrents directory was created (optional - created on demand)
    if [ -d ~/.config/dfakeseeder/torrents ]; then
        log_info "✓ Torrents directory created"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_warning "Torrents directory not created (created on demand when needed)"
        # Not counted as a failure - directory is created when torrents are added
    fi
}

# Test: Application launch
test_app_launch() {
    log_info "Test: Application launch and initialization"

    # Clean any existing processes
    pkill -9 -f dfakeseeder.py || true
    sleep 1

    # Launch app in background with timeout
    log_info "Launching application..."
    (
        export DISPLAY=:99
        export LOG_LEVEL=DEBUG
        timeout 15s dfs > /tmp/pypi-app-launch.log 2>&1
    ) &
    APP_PID=$!

    # Wait for initialization
    sleep 5

    # Check if app successfully initialized (check logs for success markers)
    if [ -f /tmp/pypi-app-launch.log ]; then
        # Check for successful initialization markers
        if grep -q "Full application initialization completed" /tmp/pypi-app-launch.log; then
            log_info "✓ Application initialized successfully"
            TESTS_PASSED=$((TESTS_PASSED + 1))

            # Check for core components starting
            if grep -q "SharedAsyncExecutor started" /tmp/pypi-app-launch.log && \
               grep -q "peer server on port" /tmp/pypi-app-launch.log; then
                log_info "✓ Core components started (peer server, async executor)"
                TESTS_PASSED=$((TESTS_PASSED + 1))
            else
                log_warning "Core components may not have started"
            fi
        else
            log_error "✗ Application failed to initialize"
            log_error "Launch log:"
            cat /tmp/pypi-app-launch.log 2>/dev/null
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        log_error "✗ No launch log found"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    # Clean up
    kill $APP_PID 2>/dev/null || true
    pkill -9 -f dfakeseeder.py || true
}

# Test: Desktop integration uninstallation
test_desktop_uninstall() {
    log_info "Test: Desktop integration uninstallation"

    if dfs-uninstall-desktop 2>&1; then
        log_info "✓ Desktop integration uninstalled"
        TESTS_PASSED=$((TESTS_PASSED + 1))

        # Verify desktop file was removed
        if [ ! -f ~/.local/share/applications/dfakeseeder.desktop ]; then
            log_info "✓ Desktop file removed"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_warning "Desktop file still exists"
        fi

        # Verify icons were removed
        if ! ls ~/.local/share/icons/hicolor/*/apps/dfakeseeder.png &> /dev/null; then
            log_info "✓ Icons removed"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_warning "Some icons still exist"
        fi
    else
        log_error "✗ Desktop integration uninstall failed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Main test execution
main() {
    echo "=========================================="
    echo "Python Package E2E Tests"
    echo "=========================================="
    echo ""

    # Start virtual display
    if ! start_xvfb; then
        log_error "Failed to start Xvfb - cannot continue"
        exit 1
    fi

    # Ensure D-Bus is available
    if ! pgrep -x dbus-daemon > /dev/null; then
        log_info "Starting D-Bus..."
        dbus-daemon --session --fork 2>/dev/null || true
    fi

    # Run tests
    test_python_imports
    test_cli_commands
    test_help_command
    test_setup_command
    test_desktop_integration
    test_user_config_creation || log_warning "Config creation test failed - continuing with other tests"
    test_config_validation
    test_app_launch
    test_desktop_uninstall

    # Cleanup
    stop_xvfb
    pkill -9 -f dfakeseeder || true

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

# Cleanup on exit
trap 'stop_xvfb; pkill -9 -f dfakeseeder || true' EXIT

# Run tests
main "$@"
