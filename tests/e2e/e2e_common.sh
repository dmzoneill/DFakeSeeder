#!/bin/bash
# Shared helpers for the DFakeSeeder end-to-end test scripts (deb, rpm, pypi).
# Source it from a test script:  source "$(dirname "${BASH_SOURCE[0]}")/e2e_common.sh"
# Provides: colours, pass/fail counters, log_* helpers, Xvfb start/stop,
# first-launch config creation, config JSON validation and the summary/exit.

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test tracking
TESTS_PASSED=0
TESTS_FAILED=0

USER_CONFIG=~/.config/dfakeseeder/settings.json

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
	if [[ -n "${XVFB_PID:-}" ]]; then
		log_info "Stopping Xvfb..."
		kill "$XVFB_PID" 2>/dev/null || true
	fi
	pkill -9 Xvfb || true
}

# Stop Xvfb and any leftover app processes (used for the EXIT trap and final cleanup)
cleanup_app() {
	stop_xvfb
	pkill -9 -f dfakeseeder || true
}

# Test: first launch creates the user config
# Usage: check_user_config_creation <title> <command to launch the app>
check_user_config_creation() {
	local title=$1
	local app_command=$2
	log_info "Test: $title"

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
		timeout 15s "$app_command" 2>&1 | head -20 &
	)
	APP_PID=$!

	# Wait for config to be created
	for _ in {1..30}; do
		if [[ -f $USER_CONFIG ]]; then
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

# Test: the user config exists and is valid JSON
# Usage: check_user_config_json <title>
check_user_config_json() {
	log_info "Test: $1"

	# Check if user config exists
	if [[ ! -f $USER_CONFIG ]]; then
		log_error "✗ User config not found"
		TESTS_FAILED=$((TESTS_FAILED + 1))
		return 1
	fi

	# Validate JSON
	if python3 -m json.tool "$USER_CONFIG" >/dev/null 2>&1; then
		log_info "✓ User config is valid JSON"
		TESTS_PASSED=$((TESTS_PASSED + 1))
	else
		log_error "✗ User config is invalid JSON"
		TESTS_FAILED=$((TESTS_FAILED + 1))
		return 1
	fi
}

# Print the pass/fail summary and exit 0 if nothing failed, 1 otherwise
print_summary_and_exit() {
	echo ""
	echo "=========================================="
	echo "TEST SUMMARY"
	echo "=========================================="
	echo ""
	echo "Tests Passed: $TESTS_PASSED"
	echo "Tests Failed: $TESTS_FAILED"
	echo "Total Tests:  $((TESTS_PASSED + TESTS_FAILED))"
	echo ""

	if [[ $TESTS_FAILED -eq 0 ]]; then
		log_info "All tests passed! ✓"
		exit 0
	else
		log_error "Some tests failed! ✗"
		exit 1
	fi
}
