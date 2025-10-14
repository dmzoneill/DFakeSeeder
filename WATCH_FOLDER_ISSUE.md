# Watch Folder Feature - Troubleshooting

## Issue
Watch folder is not working when running with system Python.

## Root Cause
The `watchdog` library is required for the watch folder feature but is not available to system Python.

### Evidence from Journal
```
TorrentFolderWatcher[54]: Watchdog library not available - watch folder feature disabled
```

### Dependency Status
- ✅ `watchdog` is in `Pipfile` 
- ✅ `watchdog` is installed in pipenv environment (6.0.0)
- ❌ `watchdog` is NOT available to system Python
- ❌ App is running with system Python (not pipenv)

## Solutions

### Solution 1: Run with Pipenv (RECOMMENDED)
```bash
make run-debug-venv
```

This ensures all dependencies including `watchdog` are available.

### Solution 2: Install Watchdog System-Wide
```bash
# Option A: Using DNF (Fedora/RHEL)
sudo dnf install python3-watchdog

# Option B: Using pip
pip3 install --user watchdog
```

## Verification
After installing watchdog, check the journal for this message:
```
TorrentFolderWatcher: Started watching folder for torrents: /path/to/folder
```

## Implementation Details
The watch folder feature:
1. Scans for existing `*.torrent` files on startup
2. Monitors for new files using watchdog's Observer
3. Automatically copies torrents to `~/.config/dfakeseeder/torrents/`
4. Adds them to the model and UI
5. Integrates with GlobalPeerManager for P2P networking

The feature gracefully degrades when watchdog is unavailable rather than crashing.
