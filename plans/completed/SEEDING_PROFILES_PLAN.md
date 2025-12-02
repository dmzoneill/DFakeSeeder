# Seeding Profiles Implementation Plan

## Overview

DFakeSeeder will implement a comprehensive seeding profiles system that allows users to quickly switch between different seeding behaviors. The system provides three predefined profiles (Conservative, Balanced, Aggressive) plus a Custom profile for advanced users.

## Current State

✅ **Already Implemented:**
- Basic profile configuration in `domain/config/default.json`
- UI dropdown in General settings (`ui/settings/general.xml`)
- Profile structure in simulation_tab.py
- Translation strings for profile names

⚠️ **Needs Implementation:**
- Profile selection handler in GeneralTab
- Real-time profile application to settings
- Profile manager class for centralized logic
- Enhanced profile parameters and validation

## Profile Definitions

### Conservative Profile 🐌
**Target User:** Casual seeders, limited bandwidth, privacy-focused
```json
{
  "upload_limit": 50,              // KB/s - Limited upload speed
  "download_limit": 500,           // KB/s - Moderate download
  "max_connections": 100,          // Lower connection count
  "announce_interval": 3600,       // 1 hour - Less frequent announces
  "concurrent_uploads": 4,         // Fewer simultaneous uploads
  "share_ratio_target": 1.5,       // Conservative sharing goal
  "idle_probability": 0.6,         // Often appears idle
  "speed_variance": 0.3,           // Low speed fluctuation
  "burst_probability": 0.1,        // Rare speed bursts
  "throttle_mode": "strict",       // Strict bandwidth adherence
  "dht_enabled": false,            // Privacy-focused
  "pex_enabled": false,            // Privacy-focused
  "client_behavior": "conservative"
}
```text
### Balanced Profile ⚖️ (Default)
**Target User:** Regular seeders, moderate bandwidth, balanced approach
```json
{
  "upload_limit": 200,             // KB/s - Moderate upload speed
  "download_limit": 1000,          // KB/s - Good download speed
  "max_connections": 200,          // Balanced connection count
  "announce_interval": 1800,       // 30 minutes - Regular announces
  "concurrent_uploads": 8,         // Moderate uploads
  "share_ratio_target": 2.0,       // Standard sharing goal
  "idle_probability": 0.3,         // Sometimes idle
  "speed_variance": 0.5,           // Moderate speed variation
  "burst_probability": 0.3,        // Occasional speed bursts
  "throttle_mode": "adaptive",     // Smart bandwidth management
  "dht_enabled": true,             // Standard protocol participation
  "pex_enabled": true,             // Standard peer exchange
  "client_behavior": "balanced"
}
```text
### Aggressive Profile 🚀
**Target User:** Power seeders, high bandwidth, maximum sharing
```json
{
  "upload_limit": 0,               // Unlimited upload speed
  "download_limit": 0,             // Unlimited download speed
  "max_connections": 500,          // Maximum connections
  "announce_interval": 900,        // 15 minutes - Frequent announces
  "concurrent_uploads": 16,        // High simultaneous uploads
  "share_ratio_target": 3.0,       // High sharing goal
  "idle_probability": 0.1,         // Rarely idle
  "speed_variance": 0.8,           // High speed variation
  "burst_probability": 0.6,        // Frequent speed bursts
  "throttle_mode": "unrestricted", // No bandwidth limits
  "dht_enabled": true,             // Full protocol participation
  "pex_enabled": true,             // Active peer discovery
  "client_behavior": "aggressive"
}
```text
### Custom Profile 🔧
**Target User:** Advanced users wanting fine-grained control
- Inherits from selected base template (default: balanced)
- All parameters individually editable
- Saved per-user with validation
- Can be reset to base template

## Implementation Architecture

### 1. Profile Manager (`lib/seeding_profile_manager.py`)
Central class managing all profile operations:
- Load predefined and custom profiles
- Apply profiles to application settings
- Validate profile parameters
- Handle profile switching and persistence

### 2. Settings Integration (`general_tab.py`)
Enhanced GeneralTab with profile functionality:
- Profile dropdown handler
- Real-time application of profile changes
- Profile preview and validation
- User notifications for profile changes

### 3. Application Integration
Profiles affect multiple components:
- **Torrent Management**: Speed limits, connection counts, announce intervals
- **Peer Protocol**: DHT, PEX, connection behavior
- **Network Management**: Bandwidth allocation, protocol aggressiveness
- **UI Components**: Settings tabs reflect profile values

## Technical Implementation

### Phase 1: Core Functionality
1. **Profile Manager Class**
   - Create `SeedingProfileManager` class
   - Implement profile loading and application logic
   - Add profile validation and error handling

2. **GeneralTab Integration**
   - Add profile dropdown signal handler
   - Implement immediate profile application
   - Add profile change notifications

3. **Settings Synchronization**
   - Ensure profile changes update all relevant settings
   - Handle bidirectional updates (profile→settings, settings→profile)
   - Maintain consistency across application restart

### Phase 2: Enhanced Features
1. **Profile Preview Panel**
   - Show current profile parameters
   - Real-time preview of changes
   - Profile comparison functionality

2. **Custom Profile Editor**
   - Editable parameter controls
   - Template selection and reset
   - Save/load custom profiles

3. **Advanced Integration**
   - Per-torrent profile overrides
   - Scheduled profile switching
   - Performance analytics per profile

## File Structure Changes

### New Files
- `d_fake_seeder/lib/seeding_profile_manager.py` - Core profile management
- `d_fake_seeder/components/component/settings/profiles_tab.py` - Dedicated profiles tab (Phase 2)

### Modified Files
- `d_fake_seeder/components/component/settings/general_tab.py` - Add profile dropdown handler
- `d_fake_seeder/domain/config/default.json` - Enhanced profile definitions
- `d_fake_seeder/domain/torrent/torrent.py` - Apply profile settings to torrents
- `d_fake_seeder/ui/settings/general.xml` - Enhanced profile UI (Phase 2)

## Profile Application Flow

```text
1. User Selection
   ↓
2. Profile Validation
   ↓
3. Settings Update (app_settings.seeding_profile = "name")
   ↓
4. Profile Manager Application
   ↓
5. Component Notifications
   ↓
6. Real-time Effect on Active Torrents
   ↓
7. Settings Persistence
```text
## Parameter Mapping

| Profile Parameter | App Setting Location | Component Effect |
| ------------------ | --------------------- | ------------------ |
| `upload_limit` | `upload_speed` | Global upload speed limit |
| `download_limit` | `download_speed` | Global download speed limit |
| `max_connections` | `concurrent_peer_connections` | Peer connection manager |
| `announce_interval` | `announce_interval` | Tracker communication |
| `concurrent_uploads` | `max_upload_slots` | Upload slot allocation |
| `dht_enabled` | `protocols.dht.enabled` | DHT participation |
| `pex_enabled` | `protocols.pex.enabled` | Peer exchange |

## Success Criteria

### Functional Requirements
- ✅ Users can select from 4 profile options
- ✅ Profile changes apply immediately to active torrents
- ✅ Profile selection persists across application restarts
- ✅ Custom profiles can be created and modified
- ✅ Profile parameters validate within acceptable ranges

### User Experience Requirements
- ✅ Profile changes show immediate visual feedback
- ✅ Profile descriptions clearly explain behavior differences
- ✅ Profile switching is accessible from main settings
- ✅ Error messages guide users for invalid custom settings

### Technical Requirements
- ✅ Profile changes don't require application restart
- ✅ Profile system integrates cleanly with existing settings
- ✅ Profile application is atomic (all settings update together)
- ✅ Profile system supports future extensibility

## Testing Strategy

### Unit Tests
- Profile manager profile loading/saving
- Settings validation and range checking
- Profile application logic

### Integration Tests
- End-to-end profile switching workflow
- Settings persistence across restarts
- Torrent behavior changes with profile switching

### User Acceptance Tests
- Profile switching from UI responds immediately
- Torrent speeds/behavior match selected profile
- Custom profile creation and modification works correctly

## Future Enhancements

### Advanced Features
- **Profile Scheduling**: Automatic profile switching based on time/day
- **Smart Profiles**: Auto-suggest profiles based on swarm analysis
- **Profile Sharing**: Import/export profile configurations
- **Performance Analytics**: Track effectiveness of different profiles

### Integration Opportunities
- **Torrent-Specific Overrides**: Per-torrent profile customization
- **Bandwidth Monitoring**: Real-time bandwidth usage per profile
- **Swarm Analysis**: Adapt profile behavior based on peer characteristics
- **Community Profiles**: Share optimized profiles for specific tracker types

This plan provides a roadmap for implementing comprehensive seeding profiles that enhance DFakeSeeder's usability while maintaining its sophisticated BitTorrent simulation capabilities.