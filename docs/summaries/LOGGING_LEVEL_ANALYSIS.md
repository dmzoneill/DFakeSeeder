# Logging Level Analysis and Conversion Plan

## Overview
This document provides a comprehensive analysis of logger.info usage in the DFakeSeeder codebase and defines clear rules for when to use info vs debug level logging.

## Current Status
- **Total logger.info calls**: 234 across codebase
- **Top files by logger.info count**:
  1. dfakeseeder_tray.py - 26 calls
  2. domain/torrent/seeders/udp_seeder.py - 23 calls
  3. domain/torrent/torrent.py - 19 calls
  4. lib/util/window_manager.py - 13 calls
  5. scripts/launch_tray.py - 10 calls
  6. domain/torrent/shared_async_executor.py - 10 calls
  7. domain/torrent/global_peer_manager.py - 10 calls

## Logging Level Guidelines

### INFO Level - User-Facing Events
Use `logger.info()` for messages that represent important user-facing events and state changes:

1. **Application Lifecycle**
   - Application startup/shutdown
   - Major component initialization (but not detailed steps)
   - Fatal errors or critical warnings

2. **User Actions**
   - Torrent added/removed by user
   - Settings changes initiated by user
   - Manual operations (start/stop seeding, etc.)

3. **Significant State Changes**
   - Tracker connection established/lost
   - DHT mode enabled/disabled
   - Peer connection count thresholds reached
   - Network mode changes (online/offline)

4. **Error Recovery**
   - Automatic failover to backup tracker
   - Recovered from error condition
   - Retry operations (but not every retry attempt)

5. **Summary Statistics**
   - Hourly/daily summary reports
   - Aggregate statistics
   - Performance milestones

### DEBUG Level - Operational Details
Use `logger.debug()` for verbose operational messages and technical details:

1. **Protocol Details**
   - Individual packet sends/receives
   - Transaction IDs, connection IDs
   - Peer IDs, info hashes
   - Packet sizes, buffer sizes

2. **Routine Operations**
   - Every announce request/response
   - Socket connections (unless representing state change)
   - Individual peer listings
   - Periodic updates
   - Timer callbacks

3. **Technical Flow**
   - Function entry/exit (except critical paths)
   - Lock acquisition/release
   - Thread/worker startup
   - Queue operations

4. **Detailed Statistics**
   - Per-torrent upload/download bytes
   - Individual seeder/leecher counts
   - Interval timings
   - Individual peer details

5. **Verbose Protocol Information**
   - BitTorrent message types
   - DHT query/response details
   - Extension protocol negotiations
   - Handshake details

## Conversion Categories

### Category 1: UDP Tracker Protocol (udp_seeder.py)
**Convert to DEBUG**: All detailed protocol operations
- "📡 Connecting to UDP tracker"
- "📁 Torrent: ... (Hash: ...)"
- "🆔 Peer ID: ..."
- "📊 Upload announce - Up: ... bytes"
- "🔌 UDP socket connected"
- "🔢 Transaction ID: ..."
- "📦 Sending UDP packet"
- "📨 Received UDP response"
- "✅ UDP tracker response processed successfully"
- "🌱 Seeders: ..., ⬇️ Leechers: ..."
- "⏱️ Update interval: ..."
- "👥 Found {n} peers"
- "👥 Peer {i}: {ip}:{port}"
- "🔄 Starting UDP peer discovery"

**Keep as INFO**: State changes and error recovery
- "🔄 Switched to backup tracker" (error recovery)
- "🛑 Shutdown requested, aborting" (lifecycle event)

### Category 2: HTTP Tracker Protocol (http_seeder.py)
**Convert to DEBUG**: All detailed protocol operations
- HTTP request/response details
- URL construction
- Header information
- Response parsing details

**Keep as INFO**: State changes
- Tracker unavailable/available
- Failover to backup

### Category 3: Torrent Management (torrent.py)
**Convert to DEBUG**: Operational details
- File parsing details
- Piece calculations
- Worker thread operations
- Periodic updates

**Keep as INFO**: User-visible state
- Torrent added/removed
- Torrent started/stopped
- Critical parsing errors

### Category 4: Peer Management (global_peer_manager.py, peer_server.py)
**Convert to DEBUG**: Connection details
- Individual peer connection attempts
- Handshake details
- Message exchanges
- Connection pool operations

**Keep as INFO**: Connection state changes
- Server started/stopped
- Connection limits reached
- Significant peer events (first peer, all peers disconnected)

### Category 5: DHT Protocol (dht/)
**Convert to DEBUG**: Protocol operations
- DHT query/response details
- Node additions/removals
- Routing table updates
- Individual peer discoveries

**Keep as INFO**: DHT state
- DHT enabled/disabled
- Bootstrap complete
- Major routing table milestones

### Category 6: UI Components (component/)
**Convert to DEBUG**: UI operations
- Widget creation
- Signal connections
- Model updates
- View refreshes

**Keep as INFO**: User actions
- Settings saved
- Profile changes
- Import/export operations

### Category 7: Utility Classes (lib/util/)
**Convert to DEBUG**: Infrastructure operations
- D-Bus connections
- File watching
- Window management details

**Keep as INFO**: Service availability
- D-Bus service registered/lost
- Critical configuration changes

## Implementation Strategy

### Phase 1: Seeder Protocol Classes (High Impact)
1. udp_seeder.py - 23 conversions
2. http_seeder.py - estimated 15 conversions
3. dht_seeder.py - 7 conversions
4. base_seeder.py - 4 conversions

**Expected Result**: Significant noise reduction in protocol-heavy operations

### Phase 2: Torrent Management (Medium Impact)
1. torrent.py - 19 conversions (selective)
2. torrent_peer_manager.py - 6 conversions
3. seeder.py - estimated 10 conversions

**Expected Result**: Cleaner torrent lifecycle logging

### Phase 3: Network Infrastructure (Medium Impact)
1. global_peer_manager.py - 10 conversions (selective)
2. peer_server.py - 6 conversions
3. utp_manager.py - 7 conversions
4. shared_async_executor.py - 10 conversions

**Expected Result**: Less verbose network operation logs

### Phase 4: DHT Protocol (Low-Medium Impact)
1. dht/seeder.py - 8 conversions
2. dht/node.py - 7 conversions
3. dht/peer_discovery.py - 6 conversions

**Expected Result**: Cleaner DHT logs

### Phase 5: UI and Utilities (Low Impact)
1. window_manager.py - 13 conversions (selective)
2. torrent_folder_watcher.py - 6 conversions
3. files_tab.py - 7 conversions
4. Various other component files

**Expected Result**: Less UI operation noise

### Phase 6: Application Entry Points (Low Impact)
1. dfakeseeder_tray.py - 26 conversions (selective)
2. launch_tray.py - 10 conversions (selective)
3. controller.py - 7 conversions (selective)

**Expected Result**: Cleaner application startup logs

## Verification Checklist

After conversions, verify:
- [ ] Application startup shows key milestones at INFO
- [ ] User actions (add/remove torrent) visible at INFO
- [ ] Tracker state changes visible at INFO
- [ ] Error recovery actions visible at INFO
- [ ] Detailed protocol operations at DEBUG only
- [ ] Individual peer operations at DEBUG only
- [ ] Technical details (IDs, sizes, etc.) at DEBUG only
- [ ] No loss of important diagnostic information

## Expected Outcome

**Before**: ~234 INFO messages during typical operation (very noisy)
**After**: ~50-70 INFO messages for important events only
**Improvement**: 70% reduction in INFO noise, better signal-to-noise ratio

## Notes

- Emoji icons don't determine log level - focus on message importance
- When in doubt, prefer DEBUG to reduce noise
- INFO should be readable by non-technical users
- DEBUG can be as verbose as needed for troubleshooting
