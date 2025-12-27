# DFakeSeeder Configuration Documentation

## Overview

DFakeSeeder uses a comprehensive JSON configuration system with over 300 settings organized into logical categories. The configuration provides default values for all application behavior, from basic UI settings to advanced BitTorrent protocol parameters.

## Configuration File Locations

- **Default Configuration**: `d_fake_seeder/domain/config/default.json` (300+ lines)
- **User Configuration**: `~/.config/dfakeseeder/settings.json` (auto-created from defaults)
- **Torrent Storage**: `~/.config/dfakeseeder/torrents/`

## Configuration Categories

### 1. Basic Speed Settings
Controls fundamental BitTorrent transfer speeds.
```json
{
  "upload_speed": 50,              // KB/s upload rate
  "download_speed": 500,           // KB/s download rate
  "total_upload_speed": 50,        // Global upload limit
  "total_download_speed": 500,     // Global download limit
  "announce_interval": 1800        // Tracker announce interval (seconds)
}
```text
### 2. BitTorrent Client Simulation
Configures client impersonation for realistic torrent behavior.
```json
{
  "agents": [                      // Available user agent strings
    "Deluge/2.0.3 libtorrent/2.0.5.0,-DE2003-",
    "qBittorrent/4.3.1,-qB4310-",
    "Transmission/3.00,-TR3000-",
    "uTorrent/3.5.5,-UT3550-",
    "Vuze/5.7.6.0,-AZ5760-",
    "BitTorrent/7.10.5,-BT7105-",
    "rTorrent/0.9.6,-RT0960-"
  ],
  "detected_clients": [],          // Auto-detected client list
  "agent": 0,                      // Current agent index
  "peer_id_prefix": "-DE2003-",    // BitTorrent peer ID prefix
  "custom_user_agent": ""          // Override agent string
}
```text
### 3. Network Configuration
Network connectivity and proxy settings.
```json
{
  "proxies": {                     // HTTP proxy configuration
    "http": "",
    "https": ""
  },
  "listening_port": 6881,          // BitTorrent listening port
  "enable_upnp": true,             // UPnP port forwarding
  "network_interface": "0.0.0.0",  // Bind interface
  "peer_server_bind_address": "0.0.0.0",
  "concurrent_http_connections": 2,
  "concurrent_peer_connections": 10,
  "max_incoming_connections": 200,
  "max_outgoing_connections": 50,
  "max_connections_per_torrent": 50,
  "max_upload_slots": 4
}
```text
### 4. Proxy Settings
Advanced proxy configuration for anonymization.
```json
{
  "proxy_type": "none",            // none, http, socks4, socks5
  "proxy_host": "",
  "proxy_port": 8080,
  "proxy_auth": false,
  "proxy_username": "",
  "proxy_password": ""
}
```text
### 5. UI Renderer Configuration
Configures GTK widget renderers for torrent data display.
```json
{
  "cellrenderers": {               // Custom cell renderers
    "progress": "Gtk.ProgressBar"
  },
  "textrenderers": {               // Text formatting functions
    "total_uploaded": "humanbytes",
    "total_downloaded": "humanbytes",
    "session_uploaded": "humanbytes",
    "session_downloaded": "humanbytes",
    "total_size": "humanbytes",
    "announce_interval": "convert_seconds_to_hours_mins_seconds",
    "next_update": "convert_seconds_to_hours_mins_seconds",
    "upload_speed": "add_kb",
    "download_speed": "add_kb",
    "threshold": "add_percent"
  },
  "editwidgets": {                 // Edit widget types
    "active": "Gtk.Switch",
    "announce_interval": "Gtk.SpinButton",
    "download_speed": "Gtk.SpinButton",
    // ... more widget mappings
  }
}
```text
### 6. Application Metadata
Basic application information and branding.
```json
{
  "issues_page": "<<https://github.com/dmzoneill/DFakeSeeder/issues",>>
  "website": "<<https://github.com/dmzoneill/DFakeSeeder/",>>
  "author": "David O Neill",
  "copyright": "Copyright {year}",
  "version": "1.0",
  "logo": "components/images/dfakeseeder.png"
}
```text
### 7. Window and UI Settings
Desktop application behavior and appearance.
```json
{
  "window_width": 1024,
  "window_height": 600,
  "start_minimized": false,
  "minimize_to_tray": false,
  "auto_start": false,
  "theme": "system",
  "remember_window_size": true
}
```text
### 8. BitTorrent Protocol Features
Core BitTorrent protocol configuration.
```json
{
  "enable_dht": true,              // Distributed Hash Table
  "enable_pex": true,              // Peer Exchange
  "enable_lpd": true,              // Local Peer Discovery
  "encryption_mode": "enabled",    // Protocol encryption
  "min_announce_interval": 300,    // Minimum tracker announce
  "scrape_interval": 900           // Tracker scrape interval
}
```text
### 9. Speed Management
Advanced speed control and scheduling.
```json
{
  "global_upload_limit": 0,        // 0 = unlimited
  "global_download_limit": 0,
  "enable_alt_speeds": false,      // Alternative speed limits
  "alt_upload_limit": 50,
  "alt_download_limit": 100,
  "enable_scheduler": false,       // Speed scheduling
  "scheduler_start_hour": 22,
  "scheduler_start_minute": 0,
  "scheduler_end_hour": 6,
  "scheduler_end_minute": 0,
  "scheduler_days": [true, true, true, true, true, true, true]  // Mon-Sun
}
```text
### 10. Web UI Configuration
HTTP interface for remote management.
```json
{
  "enable_webui": false,
  "webui_port": 8080,
  "webui_username": "admin",
  "webui_password": "",
  "webui_https": false,
  "webui_localhost_only": true,
  "webui_auth_enabled": true,
  "webui_session_timeout": 60,
  "webui_csrf_protection": true,
  "webui_clickjacking_protection": true,
  "webui_secure_headers": true
}
```text
### 11. Logging Configuration
Debug and monitoring settings.
```json
{
  "log_level": "INFO",             // DEBUG, INFO, WARNING, ERROR, CRITICAL
  "log_to_file": false,
  "log_to_systemd": true,
  "log_to_console": false,
  "max_log_size": 10,              // MB
  "log_filename": "log.log",
  "log_format": "[%(asctime)s][%(class_name)s][%(levelname)s][%(lineno)d] - %(message)s"
}
```text
### 12. Performance Settings
System performance and caching configuration.
```json
{
  "disk_cache_size": 64,           // MB
  "ui_refresh_rate": 9,            // Updates per second
  "debug_mode": false,
  "validate_settings": true,
  "auto_save": true
}
```text
### 13. Peer Protocol Configuration
Low-level BitTorrent peer communication settings.
```json
{
  "peer_protocol": {
    "handshake_timeout_seconds": 30.0,
    "message_read_timeout_seconds": 60.0,
    "data_read_timeout_seconds": 30.0,
    "connect_timeout_seconds": 10.0,
    "receive_timeout_seconds": 5.0,
    "contact_interval_seconds": 300.0,
    "startup_grace_period_seconds": 60.0,
    "keep_alive_interval_seconds": 120.0,
    "retry_interval_seconds": 30.0,
    "metadata_exchange_interval_seconds": 30.0,
    "connection_duration_seconds": 300.0,
    "peer_server_max_connections": 100,
    "peer_update_interval_seconds": 30.0,
    "stats_update_interval_seconds": 2.0,
    "fake_piece_data_size_kb": 16,
    "connection_rotation_percentage": 0.25
  }
}
```text
### 14. Seeder Configuration
Protocol-specific seeder settings.
```json
{
  "seeders": {
    "port_range_min": 1025,
    "port_range_max": 65000,
    "udp_load_timeout_seconds": 5,
    "udp_upload_timeout_seconds": 4,
    "http_timeout_seconds": 10,
    "transaction_id_min": 0,
    "transaction_id_max": 255,
    "udp_buffer_size_bytes": 2048,
    "fake_peer_id": "-FS0001-1234567890ab",
    "connection_id": "0x41727101980",
    "protocol_string": "BitTorrent protocol",
    "peer_request_count": 200
  }
}
```text
### 15. Seeding Profiles
Predefined behavior profiles for different use cases.
```json
{
  "seeding_profiles": {
    "conservative": {
      "upload_limit": 50,
      "max_connections": 100,
      "announce_interval": 3600
    },
    "balanced": {
      "upload_limit": 200,
      "max_connections": 200,
      "announce_interval": 1800
    },
    "aggressive": {
      "upload_limit": 0,
      "max_connections": 500,
      "announce_interval": 900
    }
  },
  "seeding_profile": "balanced"      // Active profile
}
```text
### 16. Application Identity
GTK application integration settings.
```json
{
  "application": {
    "id": "ie.fio.dfakeseeder",
    "title": "D' Fake Seeder",
    "css_file": "components/ui/css/styles.css",
    "config_directory": "~/.config/dfakeseeder",
    "torrents_directory": "~/.config/dfakeseeder/torrents"
  }
}
```text
### 17. Internationalization
Language and localization settings.
```json
{
  "language": "auto",
  "language_display_names": {
    "en": "English",
    "fr": "Français",
    "de": "Deutsch",
    "es": "Español",
    "it": "Italiano",
    "pl": "Polski",
    "pt": "Português",
    "ru": "Русский",
    "zh": "中文",
    "ja": "日本語",
    "ko": "한국어",
    "ar": "العربية",
    "hi": "हिन्दी",
    "nl": "Nederlands",
    "sv": "Svenska"
  }
}
```text
### 18. UI Behavior Settings
Extensive UI timing and behavior configuration (60+ settings).
```json
{
  "ui_settings": {
    "resize_delay_seconds": 1.0,
    "splash_display_duration_seconds": 2,
    "splash_fade_interval_ms": 75,
    "splash_fade_step": 0.025,
    "splash_image_size_pixels": 100,
    "notification_timeout_min_ms": 2000,
    "notification_timeout_multiplier": 500,
    "random_port_range_min": 49152,
    "random_port_range_max": 65535,
    "async_sleep_interval_seconds": 1.0,
    "error_sleep_interval_seconds": 5.0,
    "connection_timeout_seconds": 10.0,
    "message_receive_timeout_seconds": 5.0,
    "manager_thread_join_timeout_seconds": 5.0,
    "failed_connection_removal_delay_seconds": 60,
    "notebook_flush_delay_divisor": 3,
    "seeder_retry_interval_divisor": 2,
    "peer_protocol_message_receive_timeout_seconds": 0.1,
    "seeder_retry_count": 5,

    // Simulation probability settings
    "speed_variation_min": 0.2,
    "speed_variation_max": 0.8,
    "bitfield_piece_probability": 0.3,
    "metadata_exchange_probability": 0.3,
    "peer_idle_probability": 0.3,
    "seeder_upload_activity_probability": 0.3,
    "peer_idle_chance": 0.3,
    "peer_dropout_probability": 0.1,
    "peer_behavior_analysis_probability": 0.2,
    "peer_status_change_probability": 0.4,

    // Progress distribution settings
    "progress_distribution_start": 0.1,
    "progress_distribution_middle": 0.3,
    "progress_distribution_almost": 0.7,

    // Technical limits and thresholds
    "password_length": 16,
    "log_buffer_max_lines": 1000,
    "port_adjustment_value": 1000,
    "max_piece_request_size_bytes": 32768,
    "fake_piece_count_max": 1000,
    "speed_calculation_multiplier": 1000,
    "connection_cleanup_timeout_seconds": 300,
    "bitfield_size_bytes": 32,

    // Byte formatting thresholds
    "byte_format_threshold_kb": 1024,
    "byte_format_threshold_mb": 1048576,
    "byte_format_threshold_gb": 1073741824,

    // UI spacing and layout
    "ui_margin_small": 1,
    "ui_margin_medium": 8,
    "ui_margin_large": 10,
    "ui_margin_xlarge": 20,
    "ui_column_spacing_small": 10,
    "ui_column_spacing_large": 20,
    "ui_row_spacing": 10,

    // Shutdown and cleanup
    "shutdown_overlay_update_interval_ms": 100,
    "shutdown_overlay_show_details": true,
    "shutdown_overlay_show_timer": true,
    "shutdown_overlay_opacity": 0.95,
    "shutdown_timeout_seconds": 10.0,
    "thread_join_timeout_seconds": 3.0,
    "async_shutdown_timeout_seconds": 2.0,
    "force_shutdown_after_seconds": 15.0,

    // Search and misc
    "byte_conversion_base": 1024.0,
    "search_threshold": 0.7,
    "seeder_semaphore_timeout_seconds": 3.0,
    "max_seeder_retries": 3
  }
}
```text
### 19. Component-Specific Settings
Settings for individual application components.
```json
{
  "connection_manager": {
    "callback_throttle_delay_seconds": 1.0
  },
  "torrent_peer_manager": {
    "stats_update_interval_seconds": 2.0
  },
  "listener": {
    "receive_buffer_size_bytes": 1024,
    "socket_listen_backlog": 5,
    "default_port": 34567
  }
}
```text
### 20. Client Speed Profiles
Performance characteristics for different BitTorrent clients.
```json
{
  "client_speed_profiles": {
    "Deluge": {
      "max_down_kbps": 2048,
      "max_up_kbps": 1024,
      "seed_ratio": 0.3
    },
    "qBittorrent": {
      "max_down_kbps": 1536,
      "max_up_kbps": 768,
      "seed_ratio": 0.25
    },
    "Transmission": {
      "max_down_kbps": 1024,
      "max_up_kbps": 512,
      "seed_ratio": 0.35
    },
    "µTorrent": {
      "max_down_kbps": 2048,
      "max_up_kbps": 256,
      "seed_ratio": 0.2
    }
  }
}
```text
## Configuration Management

### Settings Hierarchy
1. **Default values**: Loaded from `default.json`
2. **User overrides**: Stored in `~/.config/dfakeseeder/settings.json`
3. **Runtime changes**: Modified through UI settings dialog

### Settings Validation
- Type checking for all numeric values
- Range validation for ports, timeouts, and percentages
- String format validation for paths and URLs
- Dependency validation (e.g., proxy settings when proxy is enabled)

### Settings Migration
- Automatic migration of old configuration formats
- Addition of new settings with default values
- Preservation of user customizations during updates

### Performance Considerations
- Settings are cached in memory for fast access
- File watching enables automatic reload of external changes
- Batch updates minimize disk I/O during bulk changes

## Configuration Best Practices

### Security
- Never store passwords in plain text (use empty string as placeholder)
- Enable CSRF and clickjacking protection for Web UI
- Use localhost-only binding for Web UI unless remote access is needed
- Enable authentication for all remote interfaces

### Performance
- Adjust `ui_refresh_rate` based on system performance
- Increase `disk_cache_size` on systems with available RAM
- Tune connection limits based on network capacity
- Use conservative profiles on resource-constrained systems

### Debugging
- Set `log_level` to "DEBUG" for detailed troubleshooting
- Enable `log_to_file` for persistent debugging
- Increase timeout values when diagnosing network issues
- Use `debug_mode` for additional diagnostic output

### Customization
- Create custom seeding profiles for specific use cases
- Adjust simulation probabilities for realistic behavior
- Configure client speed profiles to match target clients
- Customize UI timings for optimal user experience

This configuration system provides fine-grained control over all aspects of DFakeSeeder's behavior, from basic torrent seeding to advanced protocol simulation and UI customization.