#!/bin/bash
# End-to-end Python package installation test script
# Tests: pip install, desktop integration, application launch, uninstall

set -e
set -u

# Add user's local bin to PATH for pip-installed commands
export PATH="$HOME/.local/bin:$PATH"

# shellcheck source=SCRIPTDIR/e2e_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/e2e_common.sh"

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
		if command -v "$cmd" &>/dev/null; then
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
		if [[ -f ~/.local/share/applications/dfakeseeder.desktop ]]; then
			log_info "✓ Desktop file created"
			TESTS_PASSED=$((TESTS_PASSED + 1))
		else
			log_error "✗ Desktop file not created"
			TESTS_FAILED=$((TESTS_FAILED + 1))
		fi

		# Check if icons were installed
		if ls ~/.local/share/icons/hicolor/*/apps/dfakeseeder.png &>/dev/null; then
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
	check_user_config_creation "User config creation on first launch" dfs
}

# Test: Config validation
test_config_validation() {
	check_user_config_json "Config file validation" || return 1

	# Check if torrents directory was created (optional - created on demand)
	if [[ -d ~/.config/dfakeseeder/torrents ]]; then
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
		timeout 15s dfs >/tmp/pypi-app-launch.log 2>&1
	) &
	APP_PID=$!

	# Wait for initialization
	sleep 5

	# Check if app successfully initialized (check logs for success markers)
	if [[ -f /tmp/pypi-app-launch.log ]]; then
		# Check for successful initialization markers
		if grep -q "Full application initialization completed" /tmp/pypi-app-launch.log; then
			log_info "✓ Application initialized successfully"
			TESTS_PASSED=$((TESTS_PASSED + 1))

			# Check for core components starting
			if grep -q "SharedAsyncExecutor started" /tmp/pypi-app-launch.log &&
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
		if [[ ! -f ~/.local/share/applications/dfakeseeder.desktop ]]; then
			log_info "✓ Desktop file removed"
			TESTS_PASSED=$((TESTS_PASSED + 1))
		else
			log_warning "Desktop file still exists"
		fi

		# Verify icons were removed
		if ! ls ~/.local/share/icons/hicolor/*/apps/dfakeseeder.png &>/dev/null; then
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
	if ! pgrep -x dbus-daemon >/dev/null; then
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
	cleanup_app

	print_summary_and_exit
}

# Cleanup on exit
trap cleanup_app EXIT

# Run tests
main "$@"
