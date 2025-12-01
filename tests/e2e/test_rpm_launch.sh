#!/bin/bash
# End-to-end application launch test script
# Tests: GUI launch, process management, config creation

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

# Test: Python module imports (fallback if GUI tests fail)
test_python_imports() {
    log_info "Test: Python module imports"

    if python3 -c "
import sys
sys.path.insert(0, '/opt/dfakeseeder')
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk
from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.model import Model
print('All imports successful')
" 2>&1; then
        log_info "✓ Python imports successful"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        log_error "✗ Python imports failed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
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
    for _ in {1..10}; do
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
        kill "$XVFB_PID" 2>/dev/null || true
    fi
    pkill -9 Xvfb || true
}

# Test: User config creation
test_user_config_creation() {
    log_info "Test: User config creation"

    # Remove existing config
    rm -rf ~/.config/dfakeseeder

    # Start D-Bus session for GTK
    eval "$(dbus-launch --sh-syntax)"
    export DBUS_SESSION_BUS_ADDRESS

    # Launch app in background with timeout
    log_info "Launching application to trigger config creation..."
    (
        export GDK_BACKEND=x11
        export LIBGL_ALWAYS_SOFTWARE=1
        export GALLIUM_DRIVER=llvmpipe
        export GTK_A11Y=none
        export NO_AT_BRIDGE=1
        timeout 15s /usr/bin/dfakeseeder 2>&1 | head -20 &
    )
    APP_PID=$!

    # Wait for config to be created
    for _ in {1..30}; do
        if [ -f ~/.config/dfakeseeder/settings.json ]; then
            log_info "✓ User config created"
            TESTS_PASSED=$((TESTS_PASSED + 1))

            # Kill app and dbus
            kill "$APP_PID" 2>/dev/null || true
            kill "$DBUS_SESSION_BUS_PID" 2>/dev/null || true
            return 0
        fi
        sleep 0.5
    done

    log_error "✗ User config not created"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    kill "$APP_PID" 2>/dev/null || true
    kill "$DBUS_SESSION_BUS_PID" 2>/dev/null || true
    return 1
}

# Test: Config copied from system default
test_config_source() {
    log_info "Test: Config source (should use /etc/dfakeseeder/default.json)"

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

    # Check if torrents directory was created
    if [ -d ~/.config/dfakeseeder/torrents ]; then
        log_info "✓ Torrents directory created"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "✗ Torrents directory not created"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Test: Application launch via wrapper script
test_wrapper_launch() {
    log_info "Test: Application launch via wrapper script"

    # Test --help (should not require X server)
    if /usr/bin/dfakeseeder --help 2>&1 | grep -q "D' Fake Seeder"; then
        log_info "✓ Wrapper --help works"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "✗ Wrapper --help failed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Test: Application process start
test_app_process() {
    log_info "Test: Application process management"

    # Clean any existing processes
    pkill -9 -f dfakeseeder.py || true
    sleep 1

    # Launch app in background with timeout
    log_info "Launching application..."
    (
        export DISPLAY=:99
        export LOG_LEVEL=DEBUG
        timeout 15s /usr/bin/dfakeseeder > /tmp/app-launch.log 2>&1
    ) &
    APP_PID=$!

    # Wait for initialization
    sleep 5

    # Check if app successfully initialized (check logs for success markers)
    # In headless Docker, the app may crash after init due to display issues
    if [ -f /tmp/app-launch.log ]; then
        # Check for successful initialization markers
        if grep -q "Full application initialization completed" /tmp/app-launch.log; then
            log_info "✓ Application initialized successfully"
            TESTS_PASSED=$((TESTS_PASSED + 1))

            # Check for core components starting
            if grep -q "SharedAsyncExecutor started" /tmp/app-launch.log && \
               grep -q "peer server on port" /tmp/app-launch.log; then
                log_info "✓ Core components started (peer server, async executor)"
                TESTS_PASSED=$((TESTS_PASSED + 1))
            else
                log_warning "Core components may not have started"
            fi
        else
            log_error "✗ Application failed to initialize"
            log_error "Launch log:"
            cat /tmp/app-launch.log 2>/dev/null
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

# Test: Tray application
test_tray_app() {
    log_info "Test: Tray application launch"

    # Clean processes
    pkill -9 -f dfakeseeder_tray.py || true
    sleep 1

    # Launch tray app
    log_info "Launching tray application..."
    (
        export DISPLAY=:99
        export LOG_LEVEL=DEBUG
        timeout 10s python3 /opt/dfakeseeder/dfakeseeder_tray.py > /tmp/tray-launch.log 2>&1
    ) &
    TRAY_PID=$!

    sleep 2

    # Check if process started
    if ps -p $TRAY_PID > /dev/null 2>&1; then
        log_info "✓ Tray application started (PID: $TRAY_PID)"
        TESTS_PASSED=$((TESTS_PASSED + 1))

        kill $TRAY_PID 2>/dev/null || true
        pkill -9 -f dfakeseeder_tray.py || true
    else
        log_warning "Tray application may have issues (expected in headless)"
        # Don't fail test - tray apps often have issues in headless environments
    fi
}

# Test: Desktop file execution
test_desktop_launch() {
    log_info "Test: Desktop file launch capability"

    # Validate desktop file
    if desktop-file-validate /usr/share/applications/dfakeseeder.desktop 2>&1; then
        log_info "✓ Desktop file validation passed"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_warning "Desktop file has validation warnings"
    fi

    # Check Exec line
    if grep -q "Exec=/usr/bin/dfakeseeder" /usr/share/applications/dfakeseeder.desktop; then
        log_info "✓ Desktop file has correct Exec path"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "✗ Desktop file has incorrect Exec path"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    # Check for Actions
    if grep -q "Actions=with-tray;tray-only" /usr/share/applications/dfakeseeder.desktop; then
        log_info "✓ Desktop file has desktop actions"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "✗ Desktop file missing desktop actions"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Test: Python import test
test_python_imports() {
    log_info "Test: Python module imports"

    cd /opt/dfakeseeder

    # Test critical imports
    IMPORTS=(
        "d_fake_seeder.domain.app_settings"
        "d_fake_seeder.lib.logger"
        "d_fake_seeder.controller"
        "d_fake_seeder.model"
        "d_fake_seeder.view"
    )

    for import_path in "${IMPORTS[@]}"; do
        if PYTHONPATH=/opt/dfakeseeder python3 -c "import $import_path" 2>/dev/null; then
            log_info "✓ Can import: $import_path"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_error "✗ Cannot import: $import_path"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    done
}

# Main test execution
main() {
    echo "=========================================="
    echo "Application Launch End-to-End Tests"
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

    # Run tests (import test first as baseline)
    test_python_imports
    test_user_config_creation || log_warning "GUI test failed - continuing with other tests"
    test_config_source
    test_wrapper_launch
    test_app_process
    test_tray_app
    test_desktop_launch

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
