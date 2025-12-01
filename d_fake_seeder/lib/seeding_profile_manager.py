"""
Seeding Profile Manager for DFakeSeeder

This module provides centralized management of seeding profiles, allowing users
to quickly switch between different seeding behaviors and configurations.

Profiles supported:
- Conservative: Low bandwidth, privacy-focused
- Balanced: Moderate settings for general use (default)
- Aggressive: High performance, maximum sharing
- Custom: User-defined settings
"""

# fmt: off
from typing import Any, Dict

from d_fake_seeder.lib.logger import logger

# fmt: on


class SeedingProfileManager:
    """
    Manages seeding profiles for DFakeSeeder application.

    Handles loading, applying, and validating seeding profiles that control
    torrent behavior, bandwidth usage, and protocol participation.
    """

    # Profile names mapped to their internal identifiers
    PROFILE_NAMES = {"conservative": 0, "balanced": 1, "aggressive": 2, "custom": 3}

    # Dropdown index to profile name mapping
    PROFILE_INDEX_MAP = {0: "conservative", 1: "balanced", 2: "aggressive", 3: "custom"}

    def __init__(self, app_settings):
        """
        Initialize the profile manager.

        Args:
            app_settings: AppSettings instance for reading/writing configuration
        """
        self.app_settings = app_settings
        self.logger = logger
        self.current_profile = self._load_current_profile()
        self.logger.debug(
            "SeedingProfileManager initialized",
            extra={"class_name": self.__class__.__name__},
        )

    def _load_current_profile(self) -> str:
        """Load the currently active profile from settings."""
        try:
            current = self.app_settings.get("seeding_profile", "balanced")
            self.logger.debug(
                f"Loaded current profile: {current}",
                extra={"class_name": self.__class__.__name__},
            )
            return current
        except Exception as e:
            self.logger.error(
                f"Error loading current profile: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return "balanced"

    def get_predefined_profiles(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all predefined seeding profiles with their complete configurations.

        Returns:
            Dictionary of profile configurations
        """
        return {
            "conservative": {
                "upload_limit": 50,  # KB/s - Limited upload speed
                "download_limit": 500,  # KB/s - Moderate download
                "max_connections": 100,  # Lower connection count
                "announce_interval": 3600,  # 1 hour - Less frequent announces
                "concurrent_uploads": 4,  # Fewer simultaneous uploads
                "share_ratio_target": 1.5,  # Conservative sharing goal
                "idle_probability": 0.6,  # Often appears idle
                "speed_variance": 0.3,  # Low speed fluctuation
                "burst_probability": 0.1,  # Rare speed bursts
                "throttle_mode": "strict",  # Strict bandwidth adherence
                "dht_enabled": False,  # Privacy-focused
                "pex_enabled": False,  # Privacy-focused
                "client_behavior": "conservative",
                "description": "Low bandwidth usage, privacy-focused seeding",
            },
            "balanced": {
                "upload_limit": 200,  # KB/s - Moderate upload speed
                "download_limit": 1000,  # KB/s - Good download speed
                "max_connections": 200,  # Balanced connection count
                "announce_interval": 1800,  # 30 minutes - Regular announces
                "concurrent_uploads": 8,  # Moderate uploads
                "share_ratio_target": 2.0,  # Standard sharing goal
                "idle_probability": 0.3,  # Sometimes idle
                "speed_variance": 0.5,  # Moderate speed variation
                "burst_probability": 0.3,  # Occasional speed bursts
                "throttle_mode": "adaptive",  # Smart bandwidth management
                "dht_enabled": True,  # Standard protocol participation
                "pex_enabled": True,  # Standard peer exchange
                "client_behavior": "balanced",
                "description": "Balanced settings for general use",
            },
            "aggressive": {
                "upload_limit": 0,  # Unlimited upload speed
                "download_limit": 0,  # Unlimited download speed
                "max_connections": 500,  # Maximum connections
                "announce_interval": 900,  # 15 minutes - Frequent announces
                "concurrent_uploads": 16,  # High simultaneous uploads
                "share_ratio_target": 3.0,  # High sharing goal
                "idle_probability": 0.1,  # Rarely idle
                "speed_variance": 0.8,  # High speed variation
                "burst_probability": 0.6,  # Frequent speed bursts
                "throttle_mode": "unrestricted",  # No bandwidth limits
                "dht_enabled": True,  # Full protocol participation
                "pex_enabled": True,  # Active peer discovery
                "client_behavior": "aggressive",
                "description": "Maximum performance and sharing",
            },
        }

    def get_profile_settings(self, profile_name: str) -> Dict[str, Any]:
        """
        Get complete settings for a specific profile.

        Args:
            profile_name: Name of the profile ('conservative', 'balanced', 'aggressive', 'custom')

        Returns:
            Dictionary containing all profile settings
        """
        try:
            predefined_profiles = self.get_predefined_profiles()

            if profile_name == "custom":
                # Load custom profile from app_settings or use balanced as template
                custom_settings = self.app_settings.get(
                    "custom_seeding_profile", predefined_profiles["balanced"].copy()
                )
                custom_settings["description"] = "User-defined custom settings"
                return custom_settings
            elif profile_name in predefined_profiles:
                return predefined_profiles[profile_name]
            else:
                self.logger.warning(
                    f"Unknown profile '{profile_name}', using balanced",
                    extra={"class_name": self.__class__.__name__},
                )
                return predefined_profiles["balanced"]

        except Exception as e:
            self.logger.error(
                f"Error getting profile settings for '{profile_name}': {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return self.get_predefined_profiles()["balanced"]

    def apply_profile(self, profile_name: str) -> bool:
        """
        Apply a seeding profile to the application settings.

        Args:
            profile_name: Name of the profile to apply

        Returns:
            True if profile was successfully applied, False otherwise
        """
        try:
            self.logger.info(
                f"Applying seeding profile: {profile_name}",
                extra={"class_name": self.__class__.__name__},
            )

            # Get profile settings
            profile_settings = self.get_profile_settings(profile_name)

            if not self.validate_profile(profile_settings):
                self.logger.error(
                    f"Profile '{profile_name}' failed validation",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            # Apply settings to app_settings
            self._apply_profile_settings(profile_settings)

            # Update current profile
            self.app_settings.set("seeding_profile", profile_name)
            self.current_profile = profile_name

            self.logger.info(
                f"Successfully applied seeding profile: {profile_name}",
                extra={"class_name": self.__class__.__name__},
            )
            return True

        except Exception as e:
            self.logger.error(
                f"Error applying profile '{profile_name}': {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    def _apply_profile_settings(self, profile_settings: Dict[str, Any]) -> None:
        """
        Apply profile settings to app_settings.

        Args:
            profile_settings: Dictionary of settings to apply
        """
        # Map profile settings to app_settings keys
        setting_mappings = {
            "upload_limit": "upload_speed",
            "download_limit": "download_speed",
            "max_connections": "concurrent_peer_connections",
            "announce_interval": "announce_interval",
            "concurrent_uploads": "max_upload_slots",
            "dht_enabled": "protocols.dht.enabled",
            "pex_enabled": "protocols.pex.enabled",
        }

        # Apply mapped settings
        for profile_key, settings_key in setting_mappings.items():
            if profile_key in profile_settings:
                value = profile_settings[profile_key]
                self.app_settings.set(settings_key, value)
                self.logger.debug(
                    f"Applied {settings_key} = {value}",
                    extra={"class_name": self.__class__.__name__},
                )

        # Store profile-specific settings
        profile_specific_keys = [
            "share_ratio_target",
            "idle_probability",
            "speed_variance",
            "burst_probability",
            "throttle_mode",
            "client_behavior",
        ]

        for key in profile_specific_keys:
            if key in profile_settings:
                self.app_settings.set(f"profile_settings.{key}", profile_settings[key])

    def validate_profile(self, profile_settings: Dict[str, Any]) -> bool:
        """
        Validate profile settings are within acceptable ranges.

        Args:
            profile_settings: Dictionary of settings to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            validations = [
                # Speed limits (0 = unlimited, otherwise positive)
                (
                    "upload_limit",
                    lambda x: x == 0 or (isinstance(x, (int, float)) and x > 0),
                ),
                (
                    "download_limit",
                    lambda x: x == 0 or (isinstance(x, (int, float)) and x > 0),
                ),
                # Connection limits (positive integers)
                ("max_connections", lambda x: isinstance(x, int) and 1 <= x <= 1000),
                ("concurrent_uploads", lambda x: isinstance(x, int) and 1 <= x <= 50),
                # Intervals (positive seconds)
                (
                    "announce_interval",
                    lambda x: isinstance(x, (int, float)) and 300 <= x <= 7200,
                ),
                # Probability values (0.0 to 1.0)
                (
                    "idle_probability",
                    lambda x: isinstance(x, (int, float)) and 0.0 <= x <= 1.0,
                ),
                (
                    "speed_variance",
                    lambda x: isinstance(x, (int, float)) and 0.0 <= x <= 1.0,
                ),
                (
                    "burst_probability",
                    lambda x: isinstance(x, (int, float)) and 0.0 <= x <= 1.0,
                ),
                ("share_ratio_target", lambda x: isinstance(x, (int, float)) and x > 0),
                # Boolean values
                ("dht_enabled", lambda x: isinstance(x, bool)),
                ("pex_enabled", lambda x: isinstance(x, bool)),
            ]

            for setting_name, validator in validations:
                if setting_name in profile_settings:
                    value = profile_settings[setting_name]
                    if not validator(value):
                        self.logger.error(
                            f"Invalid value for {setting_name}: {value}",
                            extra={"class_name": self.__class__.__name__},
                        )
                        return False

            return True

        except Exception as e:
            self.logger.error(
                f"Error validating profile: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    def get_current_profile(self) -> str:
        """Get the name of the currently active profile."""
        return self.current_profile

    def get_profile_dropdown_index(self, profile_name: str) -> int:
        """
        Get dropdown index for a profile name.

        Args:
            profile_name: Name of the profile

        Returns:
            Dropdown index (0-3)
        """
        return self.PROFILE_NAMES.get(profile_name, 1)  # Default to balanced

    def get_profile_from_dropdown_index(self, index: int) -> str:
        """
        Get profile name from dropdown index.

        Args:
            index: Dropdown index (0-3)

        Returns:
            Profile name
        """
        return self.PROFILE_INDEX_MAP.get(index, "balanced")  # Default to balanced

    def create_custom_profile(self, base_template: str = "balanced") -> Dict[str, Any]:
        """
        Create a new custom profile based on an existing template.

        Args:
            base_template: Profile to use as starting template

        Returns:
            Custom profile settings dictionary
        """
        try:
            template_settings = self.get_profile_settings(base_template)
            custom_settings = template_settings.copy()
            custom_settings["description"] = f"Custom profile based on {base_template}"
            custom_settings["base_template"] = base_template

            # Save as custom profile
            self.app_settings.set("custom_seeding_profile", custom_settings)

            self.logger.info(
                f"Created custom profile from {base_template} template",
                extra={"class_name": self.__class__.__name__},
            )
            return custom_settings

        except Exception as e:
            self.logger.error(
                f"Error creating custom profile: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return self.get_predefined_profiles()["balanced"]

    def get_profile_summary(self, profile_name: str) -> str:
        """
        Get a human-readable summary of a profile's key characteristics.

        Args:
            profile_name: Name of the profile

        Returns:
            Summary string describing the profile
        """
        try:
            settings = self.get_profile_settings(profile_name)

            upload = settings.get("upload_limit", 0)
            upload_str = "Unlimited" if upload == 0 else f"{upload} KB/s"

            connections = settings.get("max_connections", 0)
            interval = settings.get("announce_interval", 1800) // 60  # Convert to minutes

            return f"Upload: {upload_str}, Connections: {connections}, Announces: {interval}min"

        except Exception as e:
            self.logger.error(
                f"Error generating profile summary for '{profile_name}': {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return "Profile summary unavailable"
