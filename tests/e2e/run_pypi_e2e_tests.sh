#!/bin/bash
# Wrapper script for running Python package E2E tests
# Builds the package, installs it in Docker, and runs tests

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Determine container engine
if command -v podman &> /dev/null; then
    CONTAINER_ENGINE="podman"
elif command -v docker &> /dev/null; then
    CONTAINER_ENGINE="docker"
else
    echo -e "${RED}[ERROR]${NC} Neither podman nor docker found"
    exit 1
fi

# Configuration
TEST_IMAGE="dfakeseeder-e2e-test:latest"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DIST_DIR="$PROJECT_ROOT/dist"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Build Python package
build_package() {
    log_section "Step 1: Building Python Package"

    cd "$PROJECT_ROOT"

    # Clean previous builds
    rm -rf dist/ build/ *.egg-info

    log_info "Building wheel and sdist..."
    python3 setup.py sdist bdist_wheel

    if [ -d "$DIST_DIR" ] && [ "$(ls -A $DIST_DIR/*.whl 2>/dev/null)" ]; then
        log_info "✓ Package built successfully"
        ls -lh "$DIST_DIR"
    else
        log_error "✗ Package build failed"
        exit 1
    fi
}

# Build test image if needed
build_test_image() {
    log_section "Step 2: Checking Test Container Image"

    cd "$SCRIPT_DIR"

    # Check if image exists
    if $CONTAINER_ENGINE images | grep -q "$TEST_IMAGE"; then
        log_info "Test image exists: $TEST_IMAGE"
    else
        log_info "Building test image..."
        # For docker, use buildx plugin directly (docker CLI is broken on this system)
        # For podman, use build directly
        if [ "$CONTAINER_ENGINE" = "docker" ]; then
            if /usr/libexec/docker/cli-plugins/docker-buildx build -t "$TEST_IMAGE" -f Dockerfile.fedora .; then
                log_info "✓ Test image built successfully"
            else
                log_error "✗ Failed to build test image"
                exit 1
            fi
        else
            if $CONTAINER_ENGINE build -t "$TEST_IMAGE" -f Dockerfile.fedora .; then
                log_info "✓ Test image built successfully"
            else
                log_error "✗ Failed to build test image"
                exit 1
            fi
        fi
    fi
}

# Run installation tests
run_installation_tests() {
    log_section "Step 3: Running Installation Tests"

    log_info "Installing package from wheel in container..."

    # Find the wheel file
    WHEEL_FILE=$(ls "$DIST_DIR"/*.whl | head -1)
    WHEEL_NAME=$(basename "$WHEEL_FILE")

    $CONTAINER_ENGINE run --rm \
        -v "$DIST_DIR:/packages:ro" \
        "$TEST_IMAGE" \
        bash -c "
            set -e
            echo '=== Installing package ==='
            pip3 install --no-cache-dir /packages/$WHEEL_NAME

            echo ''
            echo '=== Verifying installation ==='
            pip3 show d-fake-seeder

            echo ''
            echo '=== Checking CLI commands ==='
            command -v dfs && echo '✓ dfs command available'
            command -v dfakeseeder && echo '✓ dfakeseeder command available'
            command -v dfs-install-desktop && echo '✓ dfs-install-desktop command available'

            echo ''
            echo '=== Testing imports ==='
            python3 -c 'import d_fake_seeder; print(\"✓ Package imports successfully\")'
        "

    if [ $? -eq 0 ]; then
        log_info "✓ Installation tests passed"
    else
        log_error "✗ Installation tests failed"
        exit 1
    fi
}

# Run application launch tests
run_launch_tests() {
    log_section "Step 4: Running Application Launch Tests"

    WHEEL_FILE=$(ls "$DIST_DIR"/*.whl | head -1)
    WHEEL_NAME=$(basename "$WHEEL_FILE")

    # Run the test script inside the container
    $CONTAINER_ENGINE run --rm \
        -v "$DIST_DIR:/packages:ro" \
        -v "$SCRIPT_DIR/test_pypi_install.sh:/test_pypi_install.sh:ro" \
        "$TEST_IMAGE" \
        bash -c "
            set -e
            # Install the package
            pip3 install --no-cache-dir /packages/$WHEEL_NAME

            # Run the E2E test script
            bash /test_pypi_install.sh
        "

    if [ $? -eq 0 ]; then
        log_info "✓ Launch tests passed"
    else
        log_error "✗ Launch tests failed"
        exit 1
    fi
}

# Run uninstallation tests
run_uninstall_tests() {
    log_section "Step 5: Running Uninstallation Tests"

    WHEEL_FILE=$(ls "$DIST_DIR"/*.whl | head -1)
    WHEEL_NAME=$(basename "$WHEEL_FILE")

    $CONTAINER_ENGINE run --rm \
        -v "$DIST_DIR:/packages:ro" \
        "$TEST_IMAGE" \
        bash -c "
            set -e
            # Install the package
            pip3 install --no-cache-dir /packages/$WHEEL_NAME

            echo '=== Installed files before uninstall ==='
            pip3 show -f d-fake-seeder | head -20

            echo ''
            echo '=== Uninstalling package ==='
            pip3 uninstall -y d-fake-seeder

            echo ''
            echo '=== Verifying uninstall ==='
            if pip3 show d-fake-seeder 2>&1 | grep -q 'not found\|WARNING'; then
                echo '✓ Package uninstalled successfully'
                exit 0
            else
                echo '✗ Package still found after uninstall'
                exit 1
            fi
        "

    if [ $? -eq 0 ]; then
        log_info "✓ Uninstall tests passed"
    else
        log_error "✗ Uninstall tests failed"
        exit 1
    fi
}

# Generate test report
generate_report() {
    log_section "Generating Test Report"

    cat > "$DIST_DIR/pypi-e2e-test-report.txt" << EOF
DFakeSeeder PyPI Package E2E Test Report
========================================
Date: $(date)
Container Engine: $CONTAINER_ENGINE
Test Image: $TEST_IMAGE
Package: $(ls "$DIST_DIR"/*.whl | head -1 | xargs basename)

Test Results:
-------------
✓ Installation Tests: PASSED
✓ Launch Tests: PASSED
✓ Uninstall Tests: PASSED

All tests completed successfully!
EOF

    log_info "Report saved to: $DIST_DIR/pypi-e2e-test-report.txt"
}

# Main execution
main() {
    echo "=========================================="
    echo "DFakeSeeder PyPI Package E2E Tests"
    echo "=========================================="
    echo ""
    echo "Container Engine: $CONTAINER_ENGINE"
    echo "Project Root: $PROJECT_ROOT"
    echo ""

    # Run test phases
    build_package
    build_test_image
    run_installation_tests
    run_launch_tests
    run_uninstall_tests
    generate_report

    # Final summary
    log_section "Final Summary"
    log_info "✓✓✓ ALL PYPI E2E TESTS PASSED ✓✓✓"
    log_info "Cleaning up..."
}

# Run main
main "$@"
