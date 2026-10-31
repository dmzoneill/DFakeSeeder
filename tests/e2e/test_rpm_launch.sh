#!/bin/bash
# End-to-end application launch test script
# Tests: GUI launch, process management, config creation

set -e
set -u

# shellcheck source=SCRIPTDIR/e2e_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/e2e_common.sh"

# Test: User config creation
test_user_config_creation() {
	check_user_config_creation "User config creation" /usr/bin/dfakeseeder
}

# Test: Config copied from system default
test_config_source() {
	check_user_config_json "Config source (should use /etc/dfakeseeder/default.json)" || return 1

	# Check if torrents directory was created
	if [[ -d ~/.config/dfakeseeder/torrents ]]; then
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
	export DISPLAY=:99
	export LOG_LEVEL=DEBUG
	(
		timeout 15s /usr/bin/dfakeseeder >/tmp/app-launch.log 2>&1
	) &
	APP_PID=$!

	# Wait for initialization
	sleep 5

	# Check if app successfully initialized (check logs for success markers)
	# In headless Docker, the app may crash after init due to display issues
	if [[ -f /tmp/app-launch.log ]]; then
		# Check for successful initialization markers
		if grep -q "Full application initialization completed" /tmp/app-launch.log; then
			log_info "✓ Application initialized successfully"
			TESTS_PASSED=$((TESTS_PASSED + 1))

			# Check for core components starting
			if grep -q "SharedAsyncExecutor started" /tmp/app-launch.log &&
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
	export DISPLAY=:99
	export LOG_LEVEL=DEBUG
	(
		timeout 10s python3 /opt/dfakeseeder/dfakeseeder_tray.py >/tmp/tray-launch.log 2>&1
	) &
	TRAY_PID=$!

	sleep 2

	# Check if process started
	if ps -p "$TRAY_PID" >/dev/null 2>&1; then
		log_info "✓ Tray application started (PID: $TRAY_PID)"
		TESTS_PASSED=$((TESTS_PASSED + 1))

		kill "$TRAY_PID" 2>/dev/null || true
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
	if ! pgrep -x dbus-daemon >/dev/null; then
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
	cleanup_app

	print_summary_and_exit
}

# Cleanup on exit
trap cleanup_app EXIT

# Run tests
main "$@"
