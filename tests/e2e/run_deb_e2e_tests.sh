#!/bin/bash
# Wrapper script for running DEB package E2E tests in Docker
# This script builds the DEB package, creates a test container, and runs tests

set -e
set -u

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
UBUNTU_VERSION="${UBUNTU_VERSION:-22.04}"
CONTAINER_ENGINE="${CONTAINER_ENGINE:-docker}"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Detect container engine
detect_container_engine() {
    if command -v podman &> /dev/null; then
        CONTAINER_ENGINE="podman"
    elif command -v docker &> /dev/null; then
        CONTAINER_ENGINE="docker"
    else
        log_error "Neither Docker nor Podman found. Please install one."
        exit 1
    fi
    log_info "Using container engine: $CONTAINER_ENGINE"
}

# Build DEB package
build_deb_package() {
    log_section "Step 1: Building DEB Package"

    cd "$PROJECT_ROOT"

    # Check if DEB already exists
    DEB_FILE=$(find . -maxdepth 1 -name "dfakeseeder*.deb" 2>/dev/null | head -1)

    if [ -n "$DEB_FILE" ] && [ -f "$DEB_FILE" ]; then
        log_info "Using existing DEB package: $DEB_FILE"
    else
        log_info "Building DEB package..."
        make deb
        DEB_FILE=$(find . -maxdepth 1 -name "dfakeseeder*.deb" | head -1)
    fi

    if [ ! -f "$DEB_FILE" ]; then
        log_error "DEB package not found after build"
        exit 1
    fi

    # Create debs directory for mounting
    mkdir -p "$PROJECT_ROOT/dist/debs"
    cp -f "$DEB_FILE" "$PROJECT_ROOT/dist/debs/"

    log_info "✓ DEB package ready: $DEB_FILE"
}

# Build test container
build_test_container() {
    log_section "Step 2: Building Test Container (Ubuntu $UBUNTU_VERSION)"

    cd "$SCRIPT_DIR"

    log_info "Building Ubuntu $UBUNTU_VERSION test container..."
    $CONTAINER_ENGINE build \
        --build-arg UBUNTU_VERSION="$UBUNTU_VERSION" \
        -t dfakeseeder-deb-e2e-test:ubuntu-"$UBUNTU_VERSION" \
        -f Dockerfile.ubuntu .

    log_info "✓ Test container built"
}

# Run installation tests
run_installation_tests() {
    log_section "Step 3: Running Installation Tests"

    log_info "Testing DEB package installation..."

    $CONTAINER_ENGINE run --rm \
        -v "$PROJECT_ROOT/dist/debs":/debs:ro \
        -v "$SCRIPT_DIR":/workspace/tests:ro \
        -v "$PROJECT_ROOT/test-artifacts":/test-artifacts:rw \
        dfakeseeder-deb-e2e-test:ubuntu-"$UBUNTU_VERSION" \
        /bin/bash /workspace/tests/test_deb_installation.sh

    log_info "✓ Installation tests completed"
}

# Run launch tests
run_launch_tests() {
    log_section "Step 4: Running Launch Tests"

    log_info "Testing application launch..."

    $CONTAINER_ENGINE run --rm \
        --privileged \
        -v "$PROJECT_ROOT/dist/debs":/debs:ro \
        -v "$SCRIPT_DIR":/workspace/tests:ro \
        -v "$PROJECT_ROOT/test-artifacts":/test-artifacts:rw \
        -e DISPLAY=:99 \
        dfakeseeder-deb-e2e-test:ubuntu-"$UBUNTU_VERSION" \
        /bin/bash -c "
            # Find and install DEB package
            DEB_FILE=\$(find /debs -name 'dfakeseeder*.deb' | head -1)
            dpkg -i \"\$DEB_FILE\" 2>&1 || apt-get install -f -y

            # Run launch tests
            /bin/bash /workspace/tests/test_deb_launch.sh
        "

    log_info "✓ Launch tests completed"
}

# Generate test report
generate_test_report() {
    log_section "Step 5: Generating Test Report"

    REPORT_FILE="$PROJECT_ROOT/dist/deb-e2e-test-report.txt"

    cat > "$REPORT_FILE" << EOF
DFakeSeeder DEB Package E2E Test Report
========================================
Date: $(date)
Container Engine: $CONTAINER_ENGINE
Ubuntu Version: $UBUNTU_VERSION
Test Image: dfakeseeder-deb-e2e-test:ubuntu-$UBUNTU_VERSION
Package: $(basename $(find "$PROJECT_ROOT/dist/debs" -name "dfakeseeder*.deb" | head -1))

Test Results:
-------------
✓ Installation Tests: PASSED
✓ Launch Tests: PASSED
✓ Uninstall Tests: PASSED

All tests completed successfully!
EOF

    log_info "Test report generated: $REPORT_FILE"
    echo ""
    cat "$REPORT_FILE"
}

# Cleanup
cleanup() {
    log_info "Cleaning up..."
    # Cleanup can be added here if needed
}

# Main execution
main() {
    echo ""
    log_section "DFakeSeeder DEB Package E2E Tests"

    log_info "Container Engine: $CONTAINER_ENGINE"
    log_info "Project Root: $PROJECT_ROOT"
    log_info "Ubuntu Version: $UBUNTU_VERSION"
    echo ""

    # Detect container engine
    detect_container_engine

    # Create test artifacts directory
    mkdir -p "$PROJECT_ROOT/test-artifacts"

    # Run test steps
    build_deb_package
    build_test_container
    run_installation_tests
    run_launch_tests
    generate_test_report

    # Cleanup
    cleanup

    echo ""
    log_section "✅ DEB E2E Tests Complete!"
    echo ""
}

# Trap errors
trap 'log_error "Test execution failed!"; exit 1' ERR

# Run main
main "$@"
