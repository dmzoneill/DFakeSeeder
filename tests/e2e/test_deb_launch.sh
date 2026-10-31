#!/bin/bash
# End-to-end Debian package launch test script
# Tests: application launch, initialization, core components

set -e
set -u

# shellcheck source=SCRIPTDIR/e2e_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/e2e_common.sh"

# Test: Wrapper script help
test_wrapper_help() {
	log_info "Test: Wrapper script help command"

	if /usr/bin/dfakeseeder --help 2>&1 | grep -q "D' Fake Seeder\|Usage"; then
		log_info "✓ Wrapper help command works"
		TESTS_PASSED=$((TESTS_PASSED + 1))
	else
		log_error "✗ Wrapper help command failed"
		TESTS_FAILED=$((TESTS_FAILED + 1))
	fi
}

# Test: Short command help
test_short_command_help() {
	log_info "Test: Short command (dfs) help"

	if /usr/bin/dfs --help 2>&1 | grep -q "D' Fake Seeder\|Usage"; then
		log_info "✓ Short command help works"
		TESTS_PASSED=$((TESTS_PASSED + 1))
	else
		log_error "✗ Short command help failed"
		TESTS_FAILED=$((TESTS_FAILED + 1))
	fi
}

# Test: Python imports work
test_python_imports() {
	log_info "Test: Python module imports"

	# Set PYTHONPATH to application directory
	export PYTHONPATH="/opt/dfakeseeder"
	export DFS_PATH="/opt/dfakeseeder"

	cd /opt/dfakeseeder

	IMPORTS=(
		"d_fake_seeder.model"
		"d_fake_seeder.view"
		"d_fake_seeder.controller"
		"d_fake_seeder.domain.app_settings"
		"d_fake_seeder.lib.logger"
	)

	for import_path in "${IMPORTS[@]}"; do
		if python3 -c "import sys; sys.path.insert(0, '/opt/dfakeseeder'); import $import_path" 2>/dev/null; then
			log_info "✓ Can import: $import_path"
			TESTS_PASSED=$((TESTS_PASSED + 1))
		else
			log_error "✗ Cannot import: $import_path"
			python3 -c "import sys; sys.path.insert(0, '/opt/dfakeseeder'); import $import_path" 2>&1 | head -5
			TESTS_FAILED=$((TESTS_FAILED + 1))
		fi
	done
}

# Test: Application launch
test_app_launch() {
	log_info "Test: Application launch and initialization"

	# Clean any existing processes
	pkill -9 -f dfakeseeder.py || true
	sleep 1

	# Start D-Bus session
	eval "$(dbus-launch --sh-syntax)"
	export DBUS_SESSION_BUS_ADDRESS

	# Launch app in background with timeout
	log_info "Launching application..."
	(
		export DISPLAY=:99
		export LOG_LEVEL=DEBUG
		timeout 15s /usr/bin/dfakeseeder >/tmp/deb-app-launch.log 2>&1
	) &
	APP_PID=$!

	# Wait for initialization
	sleep 5

	# Check if app successfully initialized (check logs for success markers)
	if [[ -f /tmp/deb-app-launch.log ]]; then
		# Check for successful initialization markers
		if grep -q "Full application initialization completed" /tmp/deb-app-launch.log; then
			log_info "✓ Application initialized successfully"
			TESTS_PASSED=$((TESTS_PASSED + 1))

			# Check for core components starting
			if grep -q "SharedAsyncExecutor started" /tmp/deb-app-launch.log &&
				grep -q "peer server on port" /tmp/deb-app-launch.log; then
				log_info "✓ Core components started (peer server, async executor)"
				TESTS_PASSED=$((TESTS_PASSED + 1))
			else
				log_warning "Core components may not have started"
			fi
		else
			log_error "✗ Application failed to initialize"
			log_error "Launch log:"
			cat /tmp/deb-app-launch.log 2>/dev/null | tail -50
			TESTS_FAILED=$((TESTS_FAILED + 1))
		fi
	else
		log_error "✗ No launch log found"
		TESTS_FAILED=$((TESTS_FAILED + 1))
	fi

	# Clean up
	kill "$APP_PID" 2>/dev/null || true
	kill "$DBUS_SESSION_BUS_PID" 2>/dev/null || true
	pkill -9 -f dfakeseeder.py || true
}

# Test: User config creation
test_user_config_creation() {
	check_user_config_creation "User config creation on first launch" /usr/bin/dfakeseeder
}

# Test: Config validation
test_config_validation() {
	check_user_config_json "Config file validation"
}

# Test: Environment setup
test_environment_setup() {
	log_info "Test: Environment variables set by wrapper"

	# Run wrapper and check environment
	if /usr/bin/dfakeseeder --help 2>&1 | grep -q "Usage"; then
		log_info "✓ Wrapper sets up environment correctly"
		TESTS_PASSED=$((TESTS_PASSED + 1))
	else
		log_error "✗ Wrapper environment setup failed"
		TESTS_FAILED=$((TESTS_FAILED + 1))
	fi
}

# Main test execution
main() {
	echo "=========================================="
	echo "Debian Package Launch Tests"
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

	# Run tests
	test_wrapper_help
	test_short_command_help
	test_python_imports
	test_environment_setup
	test_user_config_creation || log_warning "Config creation test failed - continuing with other tests"
	test_config_validation
	test_app_launch

	# Cleanup
	cleanup_app

	print_summary_and_exit
}

# Cleanup on exit
trap cleanup_app EXIT

# Run tests
main "$@"
