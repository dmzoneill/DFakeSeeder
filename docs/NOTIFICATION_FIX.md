# Notification Overlay Fix - 2025-12-08

## Issue

**Error Message:**
```
Error showing notification: Notification overlay creation must be implemented by the using class
```

**Location:** Settings tabs when calling `show_notification()`

## Root Cause

The `NotificationMixin` class provides a `show_notification()` method that displays toast-style notifications to users. This method relies on a `_create_notification_overlay()` method that was designed as an abstract method requiring implementation by each class using the mixin.

However, none of the 10 settings tab classes that use `NotificationMixin` actually implemented this method:
- `AdvancedTab`
- `BitTorrentTab`
- `ConnectionTab`
- `DHTTab`
- `GeneralTab`
- `MultiTrackerTab`
- `PeerProtocolTab`
- `ProtocolExtensionsTab`
- `SimulationTab`
- `SpeedTab`
- `WebUITab`

When any of these tabs called `show_notification()` (which happens frequently for success/error messages), the code would call `_create_notification_overlay()`, which would raise a `NotImplementedError`.

### Call Stack

```python
AdvancedTab.on_log_to_file_changed()
  └─> self.show_notification("File logging enabled", "success")
      └─> overlay = self._create_notification_overlay()
          └─> raise NotImplementedError("Notification overlay creation must be implemented...")
              └─> Exception caught and logged as ERROR
```

## Solution

### Default Implementation

Provided a default implementation of `_create_notification_overlay()` in the `NotificationMixin` that:

1. **Checks for existing overlay:** Returns cached overlay if already created
2. **Finds the settings window:** Uses the `builder` attribute to get `settings_window`
3. **Creates GTK Overlay:** Dynamically creates a `Gtk.Overlay` and wraps the window's existing content
4. **Caches the overlay:** Stores it in `_notification_overlay` attribute for reuse
5. **Graceful fallback:** Returns `None` if window not found

### Updated show_notification()

Modified `show_notification()` to handle cases where overlay creation returns `None`:

```python
# If no overlay available, just log and return
if not overlay:
    logger.trace(f"Notification (no UI): {message} ({notification_type})")
    return
```

This ensures notifications are logged but don't cause errors if the overlay cannot be created.

## Implementation Details

### Before (Abstract Method)

```python
def _create_notification_overlay(self) -> Gtk.Overlay:
    """Create notification overlay if it doesn't exist."""
    # This should be implemented by the class using this mixin
    # to integrate with their specific UI structure
    raise NotImplementedError("Notification overlay creation must be implemented by the using class")
```

### After (Default Implementation)

```python
def _create_notification_overlay(self) -> Gtk.Overlay:
    """
    Create notification overlay if it doesn't exist.

    Default implementation creates a simple overlay attached to the settings window.
    Classes can override this to integrate with their specific UI structure.
    """
    # Check if we already have an overlay stored
    if hasattr(self, "_notification_overlay"):
        return self._notification_overlay

    # Try to get the settings window from builder
    window = None
    if hasattr(self, "builder"):
        window = self.builder.get_object("settings_window")

    if not window:
        # Fallback: return None and show_notification will skip overlay display
        logger.trace("No settings window found, notifications will be skipped")
        return None

    # Create an overlay for the window
    current_child = window.get_child()

    # Create overlay
    overlay = Gtk.Overlay()

    # Remove current child from window and add to overlay
    if current_child:
        window.set_child(None)
        overlay.set_child(current_child)

    # Set overlay as window's child
    window.set_child(overlay)

    # Cache it
    self._notification_overlay = overlay

    logger.trace("Created notification overlay for settings window")
    return overlay
```

## Benefits

1. **No Breaking Changes:** Existing code continues to work without modification
2. **Extensibility:** Classes can still override `_create_notification_overlay()` for custom behavior
3. **Graceful Degradation:** If overlay creation fails, notifications are logged but don't crash
4. **Single Implementation:** DRY principle - one implementation serves all 10 settings tabs
5. **Lazy Creation:** Overlay is only created when first notification is shown

## Testing

The fix was verified by:

1. **Import test:** Confirmed `NotificationMixin` imports without errors
2. **Method availability:** Verified both methods exist on the class
3. **Runtime test:** Ran application and confirmed no more `NotImplementedError`

Expected behavior after fix:
- Notifications show as toast overlays in settings window
- No error messages in logs about missing implementation
- Graceful fallback if window not available

## Future Improvements

Consider these enhancements:

1. **CSS Styling:** Add proper CSS classes for notification appearance:
   - `.notification-info` - Blue info toasts
   - `.notification-success` - Green success toasts
   - `.notification-warning` - Yellow warning toasts
   - `.notification-error` - Red error toasts

2. **Animation:** Add fade-in/fade-out animations for notifications

3. **Positioning:** Make notification position configurable (top/bottom, left/center/right)

4. **Queuing:** Implement notification queue for multiple simultaneous notifications

5. **GTK 4 Native:** Consider using `Adw.ToastOverlay` from libadwaita for modern toast notifications

## Related Files

- `d_fake_seeder/components/component/settings/settings_mixins.py` - NotificationMixin implementation
- `d_fake_seeder/components/component/settings/*_tab.py` - All settings tabs using the mixin
- `d_fake_seeder/components/ui/settings.xml` - Settings window UI definition

## Related Issues

This fix resolves the notification errors seen when:
- Changing log level settings
- Toggling file/console/systemd logging
- Changing language
- Applying seeding profiles
- Any other settings changes that show success/error notifications
