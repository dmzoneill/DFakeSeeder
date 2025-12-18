#!/bin/bash
# DFakeSeeder launcher wrapper script
# Installs at /usr/bin/dfakeseeder
# Launches the main application and optionally the tray application

# Function to show usage
show_usage() {
    cat << EOF
D' Fake Seeder - BitTorrent seeding simulator

Usage:
  dfakeseeder [OPTIONS]

Options:
  --with-tray    Launch with system tray icon
  --tray-only    Launch only the system tray (main window hidden)
  --help         Show this help message
  --version      Show version information

Examples:
  dfakeseeder                  # Launch main application
  dfakeseeder --with-tray      # Launch with tray icon
  dfakeseeder --tray-only      # Launch tray only

Environment Variables:
  LOG_LEVEL      Set logging level (DEBUG, INFO, WARNING, ERROR)
  DFS_PATH       Override application path (default: /opt/dfakeseeder)

For more information, visit: https://github.com/dmzoneill/DFakeSeeder
EOF
}

# Set default paths
DFS_PATH="${DFS_PATH:-/opt/dfakeseeder}"
DFS_APP_PATH="${DFS_PATH}/d_fake_seeder"
LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Find pipenv in PATH (could be /usr/bin/pipenv or /usr/local/bin/pipenv)
PIPENV="${PIPENV:-$(command -v pipenv || echo /usr/bin/pipenv)}"

# Check if installation exists
if [ ! -d "$DFS_PATH" ]; then
    echo "Error: DFakeSeeder installation not found at $DFS_PATH" >&2
    exit 1
fi

# Parse command line arguments
WITH_TRAY=false
TRAY_ONLY=false

for arg in "$@"; do
    case "$arg" in
        --with-tray)
            WITH_TRAY=true
            ;;
        --tray-only)
            TRAY_ONLY=true
            WITH_TRAY=true
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        --version|-v)
            cd "$DFS_PATH" || exit 1
            exec "$PYTHON" -c "from d_fake_seeder.domain.app_settings import AppSettings; s = AppSettings(); print(f\"D' Fake Seeder v{s.get('version', '1.0')}\")"
            ;;
        *)
            echo "Unknown option: $arg" >&2
            echo "Use --help for usage information" >&2
            exit 1
            ;;
    esac
done

# Change to application directory
cd "$DFS_APP_PATH" || exit 1

# For RPM installations, all dependencies are installed as system packages
# We can use system Python directly instead of pipenv
PYTHON="${PYTHON:-python3}"

# Launch application based on options
# DFS_PATH needs to point to the directory containing 'components' folder
# For RPM installations, this is the d_fake_seeder directory
if [ "$TRAY_ONLY" = true ]; then
    # Launch only tray application
    exec env LOG_LEVEL="$LOG_LEVEL" DFS_PATH="$DFS_APP_PATH" PYTHONPATH="$DFS_PATH" \
        "$PYTHON" dfakeseeder_tray.py
elif [ "$WITH_TRAY" = true ]; then
    # Launch main app in background, then tray
    env LOG_LEVEL="$LOG_LEVEL" DFS_PATH="$DFS_APP_PATH" PYTHONPATH="$DFS_PATH" \
        "$PYTHON" dfakeseeder.py &

    # Wait a moment for main app to initialize
    sleep 2

    # Launch tray application
    exec env LOG_LEVEL="$LOG_LEVEL" DFS_PATH="$DFS_APP_PATH" PYTHONPATH="$DFS_PATH" \
        "$PYTHON" dfakeseeder_tray.py
else
    # Launch main application only
    exec env LOG_LEVEL="$LOG_LEVEL" DFS_PATH="$DFS_APP_PATH" PYTHONPATH="$DFS_PATH" \
        "$PYTHON" dfakeseeder.py
fi
