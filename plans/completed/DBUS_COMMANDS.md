# DFakeSeeder D-Bus Interface - Command Reference

Complete reference for testing the D-Bus interface of the main application.

## Service Information

- **Service Name:** `ie.fio.dfakeseeder`
- **Object Path:** `/ie/fio/dfakeseeder`
- **Interface Name:** `ie.fio.dfakeseeder.Settings`

## Quick Start

### Launch the test suite (Interactive)
```bash
./test_dbus_interface.sh
```text
### Run all tests automatically
```bash
./test_dbus_interface.sh --all
```text
### Run quick health check
```bash
./test_dbus_interface.sh --quick
```text
---

## Individual D-Bus Commands

### 1. Check if Service is Running

```bash
# List all D-Bus services (look for ie.fio.dfakeseeder)
dbus-send --session --print-reply \
  --dest=org.freedesktop.DBus \
  /org/freedesktop/DBus \
  org.freedesktop.DBus.ListNames | grep dfakeseeder
```text
```bash
# Check service owner
busctl --user list | grep dfakeseeder
```text
---

### 2. Introspect the D-Bus Interface

```bash
# View all available methods and signals
gdbus introspect --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder
```text
```bash
# Alternative using dbus-send
dbus-send --session --print-reply \
  --dest=ie.fio.dfakeseeder \
  /ie/fio/dfakeseeder \
  org.freedesktop.DBus.Introspectable.Introspect
```text
---

### 3. Ping Method (Health Check)

```bash
# Simple ping to check if application is responsive
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.Ping

# Expected output: (true,)
```text
---

### 4. GetSettings Method

```bash
# Retrieve all current settings as JSON
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.GetSettings
```text
```bash
# Pretty-print the settings JSON
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.GetSettings | \
  sed "s/^('\(.*\)',)$/\1/" | \
  python3 -m json.tool
```text
```bash
# Save settings to file
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.GetSettings | \
  sed "s/^('\(.*\)',)$/\1/" | \
  python3 -m json.tool > current_settings.json
```text
---

### 5. GetConnectionStatus Method

```bash
# Get D-Bus connection health status
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.GetConnectionStatus
```text
```bash
# Pretty-print connection status
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.GetConnectionStatus | \
  sed "s/^('\(.*\)',)$/\1/" | \
  python3 -m json.tool
```text
**Example Output:**
```json
{
  "connected": true,
  "is_service_owner": true,
  "last_ping": 1696251234.567,
  "message_count": 42,
  "error_count": 0,
  "uptime": 123.45
}
```text
---

### 6. GetDebugInfo Method

```bash
# Get comprehensive debug information
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.GetDebugInfo
```text
```bash
# Pretty-print debug info
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.GetDebugInfo | \
  sed "s/^('\(.*\)',)$/\1/" | \
  python3 -m json.tool
```text
**Example Output:**
```json
{
  "service_name": "ie.fio.dfakeseeder",
  "object_path": "/ie/fio/dfakeseeder",
  "interface_name": "ie.fio.dfakeseeder.Settings",
  "connection_status": { ... },
  "registration_id": 1,
  "app_settings_available": true,
  "settings_count": 150
}
```text
---

### 7. ShowPreferences Method

```bash
# Open preferences/settings dialog in main application
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.ShowPreferences

# Expected output: (true,)
```text
**Description:**
- Opens the preferences/settings dialog in the main application
- Automatically shows the main window if it's hidden
- Returns `true` on success, `false` on failure
- Useful for tray menu integration

---

### 8. ShowAbout Method

```bash
# Open about dialog in main application
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.ShowAbout

# Expected output: (true,)
```text
**Description:**
- Opens the about dialog in the main application
- Automatically shows the main window if it's hidden
- Returns `true` on success, `false` on failure
- Useful for tray menu integration

---

### 9. UpdateSettings Method - Examples

#### Update Single Setting

```bash
# Set upload speed to 100 KB/s
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.UpdateSettings \
  '{"upload_speed": 100}'

# Expected output: (true,)
```text
#### Update Multiple Settings

```bash
# Set both upload and download speeds
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.UpdateSettings \
  '{"upload_speed": 200, "download_speed": 1000}'
```text
#### Update Boolean Settings

```bash
# Hide the main window
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.UpdateSettings \
  '{"window_visible": false}'
```text
```bash
# Show the main window
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.UpdateSettings \
  '{"window_visible": true}'
```text
```bash
# Enable alternative speed mode
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.UpdateSettings \
  '{"alternative_speed_enabled": true}'
```text
#### Update Nested Settings

```bash
# Enable DHT protocol
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.UpdateSettings \
  '{"protocols.dht.enabled": true}'
```text
```bash
# Update peer protocol timeout
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.UpdateSettings \
  '{"peer_protocol.handshake_timeout_seconds": 60.0}'
```text
#### Update String Settings

```bash
# Change seeding profile
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.UpdateSettings \
  '{"seeding_profile": "aggressive"}'
```text
```bash
# Change language
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.UpdateSettings \
  '{"language": "es"}'
```text
---

### 10. Monitor Signals

```bash
# Monitor all signals from the service
gdbus monitor --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder
```text
```bash
# Monitor with filtering (only SettingsChanged signals)
gdbus monitor --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder | \
  grep "SettingsChanged"
```text
```bash
# Monitor in background and trigger a change
gdbus monitor --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder &
MONITOR_PID=$!

# Trigger a settings change
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.UpdateSettings \
  '{"upload_speed": 150}'

# Stop monitoring after a few seconds
sleep 5
kill $MONITOR_PID
```text
---

### 11. Application Control

#### Quit Application

```bash
# ⚠️ WARNING: This will close the application!
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.UpdateSettings \
  '{"application_quit_requested": true}'
```text
---

## Validation Tests

### Test Valid Values

```bash
# Upload speed: 0-10000 KB/s
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.UpdateSettings \
  '{"upload_speed": 500}'

# Should return: (true,)
```text
### Test Invalid Values

```bash
# Upload speed exceeds maximum (should fail validation)
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.UpdateSettings \
  '{"upload_speed": 99999}'

# Should return: (false,)
```text
```bash
# Invalid boolean type (should fail validation)
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.UpdateSettings \
  '{"window_visible": "yes"}'

# Should return: (false,)
```text
```bash
# Invalid seeding profile (should fail validation)
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.UpdateSettings \
  '{"current_seeding_profile": "invalid_profile"}'

# Should return: (false,)
```text
---

## Performance Testing

### Measure Response Time

```bash
# Single ping with timing
time gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.Ping
```text
### Concurrent Requests

```bash
# Run 10 concurrent pings
for i in {1..10}; do
  (gdbus call --session \
    --dest ie.fio.dfakeseeder \
    --object-path /ie/fio/dfakeseeder \
    --method ie.fio.dfakeseeder.Settings.Ping \
    && echo "Request $i completed") &
done
wait
```text
### Stress Test

```bash
# Rapid-fire 100 requests
for i in {1..100}; do
  gdbus call --session \
    --dest ie.fio.dfakeseeder \
    --object-path /ie/fio/dfakeseeder \
    --method ie.fio.dfakeseeder.Settings.Ping \
    >/dev/null 2>&1
done
echo "Completed 100 requests"
```text
---

## Debugging Commands

### Check Journal Logs

```bash
# Follow D-Bus related logs
journalctl --user -f | grep -i dbus
```text
```bash
# Follow DFakeSeeder logs
journalctl --user -f | grep dfakeseeder
```text
```bash
# Show recent D-Bus method calls
journalctl --user -n 100 | grep "D-Bus method call"
```text
### Check D-Bus Session

```bash
# Show D-Bus session address
echo $DBUS_SESSION_BUS_ADDRESS
```text
```bash
# List all session bus names
busctl --user list
```text
```bash
# Show service details
busctl --user status ie.fio.dfakeseeder
```text
### Monitor D-Bus Traffic

```bash
# Monitor all D-Bus traffic (verbose)
dbus-monitor --session "type='method_call',interface='ie.fio.dfakeseeder.Settings'"
```text
```bash
# Monitor only signals
dbus-monitor --session "type='signal',interface='ie.fio.dfakeseeder.Settings'"
```text
---

## Common Use Cases

### 1. Remote Window Control

```bash
# Hide window (minimize to tray)
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.UpdateSettings \
  '{"window_visible": false}'

# Show window
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.UpdateSettings \
  '{"window_visible": true}'
```text
### 2. Change Speed Limits

```bash
# Set conservative speeds
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.UpdateSettings \
  '{"upload_speed": 50, "download_speed": 200}'

# Set aggressive speeds
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.UpdateSettings \
  '{"upload_speed": 1000, "download_speed": 5000}'
```text
### 3. Profile Switching

```bash
# Switch to conservative profile
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.UpdateSettings \
  '{"seeding_profile": "conservative"}'

# Switch to balanced profile
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.UpdateSettings \
  '{"seeding_profile": "balanced"}'

# Switch to aggressive profile
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.UpdateSettings \
  '{"seeding_profile": "aggressive"}'
```text
### 4. Language Switching

```bash
# Switch to English
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.UpdateSettings \
  '{"language": "en"}'

# Switch to Spanish
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.UpdateSettings \
  '{"language": "es"}'

# Switch to French
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.UpdateSettings \
  '{"language": "fr"}'
```text
### 5. UI Control

```bash
# Open preferences dialog
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.ShowPreferences

# Open about dialog
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.ShowAbout
```text
### 6. Health Check Script

```bash
#!/bin/bash
# Quick health check

echo "Checking DFakeSeeder D-Bus service..."

# Ping
if gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.Ping | grep -q "true"; then
  echo "✅ Service is responsive"
else
  echo "❌ Service is not responding"
  exit 1
fi

# Get connection status
echo "Connection status:"
gdbus call --session \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.GetConnectionStatus | \
  sed "s/^('\(.*\)',)$/\1/" | \
  python3 -m json.tool
```text
---

## Error Handling

### Service Not Available

If you get `Error: GDBus.Error:org.freedesktop.DBus.Error.ServiceUnknown`, the application is not running.

**Solution:**
```bash
# Start the application
cd /home/daoneill/src/DFakeSeeder
make run-debug
```text
### Timeout Errors

If commands timeout, increase the timeout:

```bash
# Default timeout is 25 seconds, increase if needed
gdbus call --session \
  --timeout 60 \
  --dest ie.fio.dfakeseeder \
  --object-path /ie/fio/dfakeseeder \
  --method ie.fio.dfakeseeder.Settings.GetSettings
```text
### Invalid JSON

Make sure JSON is properly formatted:

```bash
# ❌ Wrong (single quotes won't work)
gdbus call ... "{'key': 'value'}"

# ✅ Correct (use double quotes for JSON)
gdbus call ... '{"key": "value"}'
```text
---

## Tips and Tricks

1. **Pretty-print JSON output:**
   ```bash
   gdbus call ... | sed "s/^('\(.*\)',)$/\1/" | python3 -m json.tool
   ```

2. **Save output to file:**
   ```bash
   gdbus call ... > output.txt
   ```

3. **Chain multiple settings updates:**
   ```bash
   gdbus call ... '{"upload_speed": 100, "download_speed": 500, "window_visible": true}'
   ```

4. **Monitor logs in real-time:**
   ```bash
   journalctl --user -f | grep -E "(DBusUnifier|WindowManager|AppSettings)"
   ```

5. **Check if specific setting exists:**
   ```bash
   gdbus call --session \
     --dest ie.fio.dfakeseeder \
     --object-path /ie/fio/dfakeseeder \
     --method ie.fio.dfakeseeder.Settings.GetSettings | \
     grep "upload_speed"
   ```

---

## Validated Settings

Settings that have validation in place:

| Setting | Type | Valid Range | Notes |
| --------- | ------ | ------------- | ------- |
| `upload_speed` | int/float | 0-10000 | KB/s |
| `download_speed` | int/float | 0-10000 | KB/s |
| `alternative_upload_speed` | int/float | 0-10000 | KB/s |
| `alternative_download_speed` | int/float | 0-10000 | KB/s |
| `alternative_speed_enabled` | bool | true/false | - |
| `seeding_paused` | bool | true/false | - |
| `window_visible` | bool | true/false | - |
| `close_to_tray` | bool | true/false | - |
| `minimize_to_tray` | bool | true/false | - |
| `application_quit_requested` | bool | true/false | ⚠️ Quits app when true |
| `current_seeding_profile` | string | conservative/balanced/aggressive | - |
| `language` | string | 2+ chars | See language codes |

---

## Support

For issues or questions:
- Check logs: `journalctl --user -f | grep dfakeseeder`
- GitHub Issues: <<https://github.com/dmzoneill/DFakeSeeder/issues>>
- See also: `plans/UNIFIED_DBUS_TRAY_IMPLEMENTATION_PLAN.md`
