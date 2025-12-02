#!/bin/bash
# Main E2E test runner for RPM packaging
# Builds RPM, creates Docker container, runs all tests

set -e
set -u

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEST_IMAGE="dfakeseeder-e2e-test:latest"
CONTAINER_ENGINE="${CONTAINER_ENGINE:-podman}"  # Use podman by default, fallback to docker

# Detect container engine
detect_container_engine() {
    if command -v podman &> /dev/null; then
        CONTAINER_ENGINE="podman"
    elif command -v docker &> /dev/null; then
        CONTAINER_ENGINE="docker"
    else
        echo -e "${RED}Error: Neither podman nor docker found${NC}"
        exit 1
    fi
    echo -e "${GREEN}Using container engine: $CONTAINER_ENGINE${NC}"
}

# Logging
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_step() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Cleanup function
# shellcheck disable=SC2329  # Function is invoked indirectly via trap
cleanup() {
    log_info "Cleaning up..."

    # Stop any running containers
    $CONTAINER_ENGINE ps -a | grep dfakeseeder-e2e | awk '{print $1}' | xargs -r "$CONTAINER_ENGINE" rm -f || true

    # Remove test artifacts if requested
    if [ "${CLEANUP_ARTIFACTS:-false}" = "true" ]; then
        log_info "Removing test artifacts..."
        rm -rf "$PROJECT_ROOT/rpmbuild/test-artifacts" || true
    fi
}

# Trap cleanup on exit
trap cleanup EXIT

# Step 1: Build RPM
build_rpm() {
    log_step "Step 1: Building RPM"

    cd "$PROJECT_ROOT"

    # Build RPM using Make
    if make rpm; then
        log_info "✓ RPM build successful"
    else
        log_error "✗ RPM build failed"
        exit 1
    fi

    # Find RPM file
    RPM_FILE=$(find "$PROJECT_ROOT/rpmbuild/RPMS" -name "dfakeseeder-*.rpm" 2>/dev/null | head -1)

    if [ -z "$RPM_FILE" ]; then
        log_error "No RPM file found after build"
        exit 1
    fi

    log_info "RPM file: $RPM_FILE"
    export RPM_FILE
}

# Step 2: Build Docker test image
build_test_image() {
    log_step "Step 2: Building Test Container Image"

    cd "$SCRIPT_DIR"

    # For docker, use buildx plugin directly (docker CLI is broken on this system)
    # For podman, use build directly
    if [ "$CONTAINER_ENGINE" = "docker" ]; then
        if /usr/libexec/docker/cli-plugins/docker-buildx build -t "$TEST_IMAGE" -f Dockerfile.fedora .; then
            log_info "✓ Test image built successfully"
        else
            log_error "✗ Test image build failed"
            exit 1
        fi
    else
        if $CONTAINER_ENGINE build -t "$TEST_IMAGE" -f Dockerfile.fedora .; then
            log_info "✓ Test image built successfully"
        else
            log_error "✗ Test image build failed"
            exit 1
        fi
    fi
}

# Step 3: Run installation tests
run_installation_tests() {
    log_step "Step 3: Running Installation Tests"

    # Create artifacts directory
    mkdir -p "$PROJECT_ROOT/rpmbuild/test-artifacts"

    # Run tests in container
    $CONTAINER_ENGINE run --rm \
        --name dfakeseeder-e2e-install \
        -v "$PROJECT_ROOT/rpmbuild/RPMS:/rpms:ro" \
        -v "$SCRIPT_DIR:/workspace/tests:ro" \
        -v "$PROJECT_ROOT/rpmbuild/test-artifacts:/test-artifacts:rw" \
        "$TEST_IMAGE" \
        /bin/bash /workspace/tests/test_rpm_installation.sh

    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        log_info "✓ Installation tests passed"
        return 0
    else
        log_error "✗ Installation tests failed"
        return 1
    fi
}

# Step 4: Run launch tests
run_launch_tests() {
    log_step "Step 4: Running Application Launch Tests"

    # Run tests in container with X11 support
    $CONTAINER_ENGINE run --rm \
        --name dfakeseeder-e2e-launch \
        --privileged \
        -v "$PROJECT_ROOT/rpmbuild/RPMS:/rpms:ro" \
        -v "$SCRIPT_DIR:/workspace/tests:ro" \
        -v "$PROJECT_ROOT/rpmbuild/test-artifacts:/test-artifacts:rw" \
        -e DISPLAY=:99 \
        "$TEST_IMAGE" \
        /bin/bash -c "
            # Install RPM first
            RPM_FILE=\$(find /rpms -name 'dfakeseeder-*.rpm' | head -1)
            if [ -n \"\$RPM_FILE\" ]; then
                sudo rpm -ivh \"\$RPM_FILE\" || exit 1
            else
                echo 'No RPM file found'
                exit 1
            fi

            # Run launch tests
            /bin/bash /workspace/tests/test_rpm_launch.sh
        "

    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        log_info "✓ Launch tests passed"
        return 0
    else
        log_error "✗ Launch tests failed"
        return 1
    fi
}

# Step 5: Run uninstallation tests
run_uninstall_tests() {
    log_step "Step 5: Running Uninstallation Tests"

    $CONTAINER_ENGINE run --rm \
        --name dfakeseeder-e2e-uninstall \
        -v "$PROJECT_ROOT/rpmbuild/RPMS:/rpms:ro" \
        "$TEST_IMAGE" \
        /bin/bash -c "
            # Install RPM
            RPM_FILE=\$(find /rpms -name 'dfakeseeder-*.rpm' | head -1)
            sudo rpm -ivh \"\$RPM_FILE\" || exit 1

            # Verify installation
            if ! rpm -q dfakeseeder; then
                echo 'Package not installed'
                exit 1
            fi

            # Uninstall
            sudo dnf remove -y dfakeseeder || sudo rpm -e dfakeseeder || exit 1

            # Verify removal
            if rpm -q dfakeseeder 2>/dev/null; then
                echo 'Package still installed after removal'
                exit 1
            fi

            echo '✓ Uninstallation successful'
            exit 0
        "

    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        log_info "✓ Uninstall tests passed"
        return 0
    else
        log_error "✗ Uninstall tests failed"
        return 1
    fi
}

# Generate test report
generate_report() {
    log_step "Generating Test Report"

    local report_file="$PROJECT_ROOT/rpmbuild/test-artifacts/e2e-test-report.txt"

    cat > "$report_file" << EOF
DFakeSeeder E2E Test Report
===========================
Date: $(date)
Container Engine: $CONTAINER_ENGINE
Test Image: $TEST_IMAGE
RPM File: $(basename "$RPM_FILE")

Test Results:
-------------
EOF

    if [ "${INSTALL_TESTS_PASSED:-false}" = "true" ]; then
        echo "✓ Installation Tests: PASSED" >> "$report_file"
    else
        echo "✗ Installation Tests: FAILED" >> "$report_file"
    fi

    if [ "${LAUNCH_TESTS_PASSED:-false}" = "true" ]; then
        echo "✓ Launch Tests: PASSED" >> "$report_file"
    else
        echo "✗ Launch Tests: FAILED" >> "$report_file"
    fi

    if [ "${UNINSTALL_TESTS_PASSED:-false}" = "true" ]; then
        echo "✓ Uninstall Tests: PASSED" >> "$report_file"
    else
        echo "✗ Uninstall Tests: FAILED" >> "$report_file"
    fi

    echo "" >> "$report_file"
    echo "Full details available in test-artifacts directory" >> "$report_file"

    cat "$report_file"
    log_info "Report saved to: $report_file"
}

# Main execution
main() {
    log_step "DFakeSeeder RPM End-to-End Testing"

    # Detect container engine
    detect_container_engine

    # Parse arguments
    SKIP_BUILD=false
    SKIP_IMAGE=false
    TESTS_TO_RUN="all"

    while [ $# -gt 0 ]; do
        case "$1" in
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --skip-image)
                SKIP_IMAGE=true
                shift
                ;;
            --test)
                TESTS_TO_RUN="$2"
                shift 2
                ;;
            --cleanup)
                CLEANUP_ARTIFACTS=true
                shift
                ;;
            *)
                echo "Unknown option: $1"
                echo "Usage: $0 [--skip-build] [--skip-image] [--test install|launch|uninstall|all] [--cleanup]"
                exit 1
                ;;
        esac
    done

    # Build RPM if not skipped
    if [ "$SKIP_BUILD" = "false" ]; then
        build_rpm
    else
        log_warning "Skipping RPM build"
        RPM_FILE=$(find "$PROJECT_ROOT/rpmbuild/RPMS" -name "dfakeseeder-*.rpm" 2>/dev/null | head -1)
        if [ -z "$RPM_FILE" ]; then
            log_error "No RPM file found and build skipped"
            exit 1
        fi
    fi

    # Build test image if not skipped
    if [ "$SKIP_IMAGE" = "false" ]; then
        build_test_image
    else
        log_warning "Skipping test image build"
    fi

    # Run tests based on selection
    INSTALL_TESTS_PASSED=false
    LAUNCH_TESTS_PASSED=false
    UNINSTALL_TESTS_PASSED=false

    if [ "$TESTS_TO_RUN" = "all" ] || [ "$TESTS_TO_RUN" = "install" ]; then
        if run_installation_tests; then
            INSTALL_TESTS_PASSED=true
        fi
    fi

    if [ "$TESTS_TO_RUN" = "all" ] || [ "$TESTS_TO_RUN" = "launch" ]; then
        if run_launch_tests; then
            LAUNCH_TESTS_PASSED=true
        fi
    fi

    if [ "$TESTS_TO_RUN" = "all" ] || [ "$TESTS_TO_RUN" = "uninstall" ]; then
        if run_uninstall_tests; then
            UNINSTALL_TESTS_PASSED=true
        fi
    fi

    # Generate report
    generate_report

    # Final summary
    log_step "Final Summary"

    local all_passed=true

    if [ "$TESTS_TO_RUN" = "all" ] || [ "$TESTS_TO_RUN" = "install" ]; then
        [ "$INSTALL_TESTS_PASSED" = "true" ] || all_passed=false
    fi

    if [ "$TESTS_TO_RUN" = "all" ] || [ "$TESTS_TO_RUN" = "launch" ]; then
        [ "$LAUNCH_TESTS_PASSED" = "true" ] || all_passed=false
    fi

    if [ "$TESTS_TO_RUN" = "all" ] || [ "$TESTS_TO_RUN" = "uninstall" ]; then
        [ "$UNINSTALL_TESTS_PASSED" = "true" ] || all_passed=false
    fi

    if [ "$all_passed" = "true" ]; then
        log_info "✓✓✓ ALL E2E TESTS PASSED ✓✓✓"
        exit 0
    else
        log_error "✗✗✗ SOME E2E TESTS FAILED ✗✗✗"
        exit 1
    fi
}

# Run main
main "$@"
