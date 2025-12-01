"""
Column Translation Utilities

Provides centralized column header translation mappings for all ColumnView components
in the application. This system integrates with the existing TranslationManager to
support runtime language switching for column headers.
"""

# fmt: off
from d_fake_seeder.lib.logger import logger

# fmt: on

# Column translations should integrate with the main TranslationManager
# Get translation function through the model's TranslationManager


class ColumnTranslations:
    """Centralized column translation mapping system"""

    # Class-level cache for translation function
    _translation_function = None

    @staticmethod
    def _fallback_function(x):
        """Fallback function when no translation is available"""
        return x

    @classmethod
    def register_translation_function(cls, translate_func):
        """
        Register the translation function from the main TranslationManager

        This should be called once when the Model/TranslationManager is initialized
        to avoid expensive gc.get_objects() calls.

        Args:
            translate_func: The translation function from TranslationManager
        """
        logger.debug("Translation function registration called", "ColumnTranslations")
        logger.debug(f"New translation function: {translate_func}", "ColumnTranslations")
        logger.debug(
            f"Previous translation function: {cls._translation_function}",
            "ColumnTranslations",
        )
        cls._translation_function = translate_func
        logger.debug("Translation function registered successfully", "ColumnTranslations")

    @classmethod
    def _get_translation_function(cls):
        """Get the registered translation function"""
        return cls._translation_function or cls._fallback_function

    @classmethod
    def get_torrent_column_translations(cls):
        """
        Get column header translations for main torrent list

        Maps model property names to translatable column headers
        """
        # Get translation function from the main TranslationManager through model
        _ = cls._get_translation_function()

        return {
            # Core model properties (from Attributes class)
            "id": _("ID"),
            "name": _("Name"),
            "progress": _("Progress"),
            "total_size": _("Total Size"),
            "session_downloaded": _("Session Downloaded"),
            "session_uploaded": _("Session Uploaded"),
            "total_downloaded": _("Total Downloaded"),
            "total_uploaded": _("Total Uploaded"),
            "upload_speed": _("Upload Speed"),
            "download_speed": _("Download Speed"),
            "seeders": _("Seeders"),
            "leechers": _("Leechers"),
            "announce_interval": _("Announce Interval"),
            "next_update": _("Next Update"),
            "filepath": _("File Path"),
            "threshold": _("Threshold"),
            "small_torrent_limit": _("Small Torrent Limit"),
            "uploading": _("Uploading"),
            "active": _("Active"),
            "download_limit": _("Download Limit"),
            "upload_limit": _("Upload Limit"),
            "sequential_download": _("Sequential Download"),
            "super_seeding": _("Super Seeding"),
            "force_start": _("Force Start"),
            # Legacy/computed columns (may exist in UI)
            "size": _("Size"),  # fallback for total_size
            "downloaded": _("Downloaded"),  # fallback for session_downloaded
            "uploaded": _("Uploaded"),  # fallback for session_uploaded
            "ratio": _("Ratio"),
            # Additional details tab strings
            "created": _("Created"),
            "creation_date": _("Created"),
            "comment": _("Comment"),
            "created_by": _("Created By"),
            "piece_length": _("Piece Length"),
            "pieces": _("Pieces"),
            "piece_count": _("Pieces"),
            "speed_up": _("Up Speed"),  # fallback for upload_speed
            "speed_down": _("Down Speed"),  # fallback for download_speed
            "peers": _("Peers"),
            "seeds": _("Seeds"),  # fallback for seeders
            "eta": _("ETA"),
            "priority": _("Priority"),
            "status": _("Status"),
            "tracker": _("Tracker"),
            "added": _("Added"),
            "completed": _("Completed"),
            "label": _("Label"),
            "availability": _("Availability"),
            "private": _("Private"),
        }

    @classmethod
    def get_states_column_translations(cls):
        """
        Get column header translations for states/trackers view
        """
        _ = cls._get_translation_function()
        return {
            "tracker": _("Tracker"),
            "count": _("Torrents"),
            "status": _("Status"),
        }

    @classmethod
    def get_peer_column_translations(cls):
        """
        Get column header translations for peer details
        """
        _ = cls._get_translation_function()
        return {
            # TorrentPeer model properties
            "address": _("Address"),
            "client": _("Client"),
            "country": _("Country"),
            "progress": _("Progress"),
            "down_speed": _("Down Speed"),
            "up_speed": _("Up Speed"),
            "seed": _("Seed"),
            "peer_id": _("Peer ID"),
            # Legacy/additional properties
            "ip": _("IP Address"),
            "port": _("Port"),
            "flags": _("Flags"),
            "downloaded": _("Downloaded"),
            "uploaded": _("Uploaded"),
            "connection_time": _("Connected"),
        }

    @classmethod
    def get_incoming_connections_column_translations(cls):
        """
        Get column header translations for incoming connections
        """
        _ = cls._get_translation_function()
        return {
            "address": _("Address"),
            "status": _("Status"),
            "client": _("Client"),
            "connection_time": _("Connection Time"),
            "handshake_complete": _("Handshake Complete"),
            "peer_interested": _("Peer Interested"),
            "am_choking": _("Am Choking"),
            "bytes_uploaded": _("Bytes Uploaded"),
            "upload_rate": _("Upload Rate"),
            "requests_received": _("Requests Received"),
            "pieces_sent": _("Pieces Sent"),
            "failure_reason": _("Failure Reason"),
        }

    @classmethod
    def get_outgoing_connections_column_translations(cls):
        """
        Get column header translations for outgoing connections
        """
        _ = cls._get_translation_function()
        return {
            "address": _("Address"),
            "status": _("Status"),
            "client": _("Client"),
            "connection_time": _("Connection Time"),
            "handshake_complete": _("Handshake Complete"),
            "am_interested": _("Am Interested"),
            "peer_choking": _("Peer Choking"),
            "bytes_downloaded": _("Bytes Downloaded"),
            "download_rate": _("Download Rate"),
            "requests_sent": _("Requests Sent"),
            "pieces_received": _("Pieces Received"),
            "failure_reason": _("Failure Reason"),
        }

    @classmethod
    def get_files_column_translations(cls):
        """
        Get column header translations for torrent files view
        """
        _ = cls._get_translation_function()
        return {
            "name": _("Name"),
            "size": _("Size"),
            "progress": _("Progress"),
            "priority": _("Priority"),
            "downloaded": _("Downloaded"),
            "path": _("Path"),
        }

    @classmethod
    def get_trackers_column_translations(cls):
        """
        Get column header translations for torrent trackers view
        """
        _ = cls._get_translation_function()
        return {
            "url": _("URL"),
            "status": _("Status"),
            "tier": _("Tier"),
            "last_announce": _("Last Announce"),
            "next_announce": _("Next Announce"),
            "seeds": _("Seeds"),
            "leechers": _("Leechers"),
            "downloaded": _("Downloaded"),
            "message": _("Message"),
        }

    @staticmethod
    def get_column_title(column_type: str, property_name: str) -> str:
        """
        Get translated column title for a given property

        Args:
            column_type: Type of column view ('torrent', 'states', 'peer', etc.)
            property_name: Model property name

        Returns:
            Translated column title or property name if no translation found
        """
        translation_map = {
            "torrent": ColumnTranslations.get_torrent_column_translations(),
            "states": ColumnTranslations.get_states_column_translations(),
            "peer": ColumnTranslations.get_peer_column_translations(),
            "incoming_connections": ColumnTranslations.get_incoming_connections_column_translations(),
            "outgoing_connections": ColumnTranslations.get_outgoing_connections_column_translations(),
            "files": ColumnTranslations.get_files_column_translations(),
            "trackers": ColumnTranslations.get_trackers_column_translations(),
        }

        mapping = translation_map.get(column_type, {})

        # GObject properties use hyphens, but our mapping uses underscores
        # Try both the original property_name and the underscore version
        property_name_underscore = property_name.replace("-", "_")

        # If we have a specific mapping, use it (try underscore version first)
        if property_name_underscore in mapping:
            return mapping[property_name_underscore]
        elif property_name in mapping:
            return mapping[property_name]

        # Try to translate the property name directly (with underscores)
        _ = ColumnTranslations._get_translation_function()
        translated = _(property_name_underscore)

        # If translation function returned the same string, it means no translation exists
        # Return the property name as-is without modification
        return translated if translated != property_name_underscore else property_name
