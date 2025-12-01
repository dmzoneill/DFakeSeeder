# fmt: off
import random
import struct
import threading
from typing import Any, Dict
from urllib.parse import urlparse

import d_fake_seeder.lib.util.helpers as helpers
from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.constants import (
    BitTorrentProtocolConstants,
    CalculationConstants,
    NetworkConstants,
)

# fmt: on


class BaseSeeder:
    _tracker_semaphore = None
    peer_clients: Dict[str, Any] = {}

    @classmethod
    def get_tracker_semaphore(cls):
        """Lazy-load the tracker semaphore to avoid initialization issues"""
        if cls._tracker_semaphore is None:
            cls._tracker_semaphore = threading.Semaphore(AppSettings.get_instance().concurrent_http_connections)
        return cls._tracker_semaphore

    # Common functionality goes here
    def __init__(self, torrent):
        logger.debug("Startup", extra={"class_name": self.__class__.__name__})

        # subscribe to settings changed
        self.settings = AppSettings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)

        self.torrent = torrent
        self.tracker_url = ""
        self.peer_id = self.settings.agents[self.settings.agent].split(",")[1] + helpers.random_id(12)
        self.download_key = helpers.random_id(12)

        # Use configured port range
        seeders_config = getattr(self.settings, "seeders", {})
        port_min = seeders_config.get("port_range_min", NetworkConstants.PORT_RANGE_MIN)
        port_max = seeders_config.get("port_range_max", NetworkConstants.PORT_RANGE_MAX)
        self.port = random.randint(port_min, port_max)
        self.info = {}
        self.active = False

        # Shutdown flag for graceful termination
        self.shutdown_requested = False

        # Track if this is the first announce (for event=started)
        self.first_announce = True

        # Load configurable probability values
        ui_settings = getattr(self.settings, "ui_settings", {})
        self.seeder_upload_activity_probability = ui_settings.get("seeder_upload_activity_probability", 0.3)
        self.peer_idle_chance = ui_settings.get("peer_idle_chance", 0.3)
        self.progress_distribution_start = ui_settings.get("progress_distribution_start", 0.1)
        self.progress_distribution_middle = ui_settings.get("progress_distribution_middle", 0.3)
        self.progress_distribution_almost = ui_settings.get("progress_distribution_almost", 0.7)
        self.peer_behavior_analysis_probability = ui_settings.get("peer_behavior_analysis_probability", 0.2)
        self.peer_status_change_probability = ui_settings.get("peer_status_change_probability", 0.4)
        self.peer_dropout_probability = ui_settings.get("peer_dropout_probability", 0.1)

        # Enhanced peer storage
        self.peer_data = {}  # Store detailed peer information

        # Load client speed profiles from settings
        self.client_speed_profiles = self._load_client_speed_profiles()

        self.tracker_url = self.torrent.announce
        self.parsed_url = urlparse(self.tracker_url)
        self.tracker_scheme = self.parsed_url.scheme
        if hasattr(self.torrent, "announce_list"):
            self.tracker_urls = [
                url for url in self.torrent.announce_list if urlparse(url).scheme == self.tracker_scheme
            ]
        self.tracker_hostname = self.parsed_url.hostname
        self.tracker_port = self.parsed_url.port

    def _load_client_speed_profiles(self):
        """Load client speed profiles from settings with conversion to bytes/s"""
        # Get client speed profiles from settings
        profiles_config = getattr(self.settings, "client_speed_profiles", {})

        # Convert KB/s values to bytes/s and add missing fields
        converted_profiles = {}
        for client_name, profile in profiles_config.items():
            converted_profiles[client_name] = {
                "max_down": profile.get("max_down_kbps", CalculationConstants.BYTES_PER_KB)
                * CalculationConstants.KB_TO_BYTES_MULTIPLIER,  # Convert KB/s to bytes/s
                "max_up": profile.get("max_up_kbps", 512)
                * CalculationConstants.KB_TO_BYTES_MULTIPLIER,  # Convert KB/s to bytes/s
                "seed_ratio": profile.get("seed_ratio", 0.25),  # Keep as-is
            }

        return converted_profiles

    def _apply_announce_jitter(self, interval: float) -> float:
        """
        Apply random jitter to announce interval to prevent request storms.

        Adds ±10% randomization to the interval to stagger announces across torrents.
        This prevents all torrents from announcing simultaneously and overwhelming trackers.

        Args:
            interval: Base announce interval in seconds

        Returns:
            Interval with random jitter applied
        """
        jitter_percent = CalculationConstants.ANNOUNCE_JITTER_PERCENT  # ±10% jitter
        jitter = (
            interval
            * jitter_percent
            * (
                random.random() * CalculationConstants.JITTER_RANGE_MULTIPLIER
                + CalculationConstants.JITTER_OFFSET_ADJUSTMENT
            )
        )  # Random value between -10% and +10%
        jittered_interval = interval + jitter

        logger.debug(
            f"Applied jitter to interval: {interval:.1f}s -> {jittered_interval:.1f}s (jitter: {jitter:+.1f}s)",
            self.__class__.__name__,
        )

        return jittered_interval

    def set_random_announce_url(self):
        if hasattr(self.torrent, "announce_list") and self.torrent.announce_list:
            same_schema_urls = [
                url for url in self.torrent.announce_list if urlparse(url).scheme == self.tracker_scheme
            ]
            if same_schema_urls:
                random_url = random.choice(same_schema_urls)
                self.tracker_url = random_url
                self.parsed_url = urlparse(self.tracker_url)
                self.tracker_scheme = self.parsed_url.scheme
                self.tracker_hostname = self.parsed_url.hostname
                self.tracker_port = self.parsed_url.port
        else:
            self.tracker_url = self.torrent.announce
            self.parsed_url = urlparse(self.tracker_url)
            self.tracker_scheme = self.parsed_url.scheme
            self.tracker_hostname = self.parsed_url.hostname
            self.tracker_port = self.parsed_url.port

    @staticmethod
    def recreate_semaphore(obj):
        logger.debug(
            "Seeder recreate_semaphore",
            extra={"class_name": obj.__class__.__name__},
        )
        current_count = BaseSeeder.get_tracker_semaphore()._value

        if obj.settings.concurrent_http_connections == current_count:
            return

        # Acquire all available permits from the current semaphore
        BaseSeeder.get_tracker_semaphore().acquire(current_count)

        # Create a new semaphore with the desired count
        new_semaphore = threading.Semaphore(obj.settings.concurrent_http_connections)

        # Release the acquired permits on the new semaphore
        new_semaphore.release(current_count)

        # Update the class variable with the new semaphore
        BaseSeeder._tracker_semaphore = new_semaphore

    def handle_exception(self, e, message):
        logger.debug(
            f"{message}: {str(e)}",
            extra={"class_name": self.__class__.__name__},
        )
        self.get_tracker_semaphore().release()

    def request_shutdown(self):
        """Signal this seeder to shutdown gracefully"""
        logger.info(
            "Seeder shutdown requested",
            extra={"class_name": self.__class__.__name__},
        )
        self.shutdown_requested = True

    def handle_settings_changed(self, source, key, value):
        logger.debug(
            "Seeder settings changed",
            extra={"class_name": self.__class__.__name__},
        )
        if key == "concurrent_http_connections":
            BaseSeeder.recreate_semaphore(self)

    def generate_transaction_id(self):
        seeders_config = getattr(self.settings, "seeders", {})
        transaction_id_min = seeders_config.get("transaction_id_min", 0)
        transaction_id_max = seeders_config.get("transaction_id_max", 255)
        return random.randint(transaction_id_min, transaction_id_max)

    def __str__(self):
        logger.debug("Seeder __get__", extra={"class_name": self.__class__.__name__})
        result = "Peer ID: %s\n" % self.peer_id
        result += "Key: %s\n" % self.download_key
        result += "Port: %d\n" % self.port
        result += "Update tracker interval: %ds" % self.update_interval
        return result

    def identify_client_from_peer_id(self, peer_id):
        """Identify BitTorrent client from peer ID with comprehensive patterns"""
        if not peer_id or len(peer_id) < 8:
            return "Unknown"

        # Convert bytes to string if needed
        if isinstance(peer_id, bytes):
            try:
                peer_id = peer_id.decode("utf-8", errors="ignore")
            except UnicodeDecodeError:
                return "Unknown"

        peer_id_upper = peer_id.upper()
        peer_id_lower = peer_id.lower()

        # Azureus-style encoding (-XX####-) - most common format
        if peer_id.startswith("-") and len(peer_id) >= 8:
            client_id = peer_id[1:3]
            version = peer_id[3:7] if len(peer_id) >= 7 else "????"

            client_map = {
                # Popular clients
                "DE": "Deluge",
                "QB": "qBittorrent",
                "TR": "Transmission",
                "UT": "µTorrent",
                "AZ": "Vuze",
                "BT": "BitTorrent",
                "RT": "rTorrent",
                "LT": "libtorrent",
                "BI": "BiglyBT",
                "TL": "Tribler",
                # Additional clients
                "AB": "BitTyrant",
                "AG": "Ares",
                "AR": "Arctic",
                "AT": "Artemis",
                "AV": "Avicora",
                "BB": "BitBuddy",
                "BC": "BitComet",
                "BF": "Bitflu",
                "BG": "BTG",
                "bk": "BitKitten",
                "BP": "BitTorrent Pro",
                "BR": "BitRocket",
                "BS": "BTSlave",
                "BW": "BitWombat",
                "BX": "Bittorrent X",
                "CD": "Enhanced CTorrent",
                "CT": "CTorrent",
                "EB": "EBit",
                "ES": "Electric Sheep",
                "FC": "FileCroc",
                "FT": "FoxTorrent",
                "GS": "GSTorrent",
                "HL": "Halite",
                "HN": "Hydranode",
                "KG": "KGet",
                "KT": "KTorrent",
                "LC": "LeechCraft",
                "LH": "LH-ABC",
                "LP": "Lphant",
                "LT": "libtorrent",
                "lt": "libTorrent",
                "LW": "LimeWire",
                "MO": "MonoTorrent",
                "MP": "MooPolice",
                "MR": "Miro",
                "MT": "MoonlightTorrent",
                "NX": "Net Transport",
                "OS": "OneSwarm",
                "OT": "OmegaTorrent",
                "PC": "CacheLogic",
                "PT": "Popcorn Time",
                "qB": "qBittorrent",
                "QD": "QQDownload",
                "RS": "Rufus",
                "RV": "Retriever",
                "RZ": "RezTorrent",
                "SB": "Swiftbit",
                "SD": "Thunder",
                "SN": "ShareNET",
                "SS": "SwarmScope",
                "ST": "SymTorrent",
                "st": "sharktorrent",
                "SZ": "Shareaza",
                "TN": "TorrentDotNET",
                "TO": "TopoTorrent",
                "TS": "Torrentstorm",
                "TT": "TuoTu",
                "UL": "uLeecher",
                "UM": "µTorrent Mac",
                "UT": "µTorrent",
                "VZ": "Vuze",
                "WD": "WebTorrent Desktop",
                "WT": "BitLet",
                "WW": "WebTorrent",
                "XL": "Xunlei",
                "XT": "XanTorrent",
                "XX": "Xtorrent",
                "ZT": "ZipTorrent",
            }

            client_name = client_map.get(client_id, f"Unknown ({client_id})")
            # Add version info for known clients
            if client_id in client_map:
                try:
                    # Parse version from format like "4300" -> "4.3.0"
                    if version.isdigit() and len(version) >= 4:
                        v_major = int(version[0])
                        v_minor = int(version[1])
                        v_patch = int(version[2:4])
                        client_name += f" {v_major}.{v_minor}.{v_patch}"
                except (ValueError, IndexError):
                    pass
            return client_name

        # Shadow-style encoding (single letter clients)
        first_char = peer_id[0] if peer_id else ""
        if first_char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            client_map = {
                "A": "ABC",
                "B": "BitTornado",
                "C": "Ctorrent",
                "E": "Enhanced CTorrent",
                "G": "GNU Torrent",
                "M": "Mainline",
                "O": "Opera",
                "Q": "Queen Bee",
                "R": "Tribler",
                "S": "Shadow",
                "T": "BitTornado",
                "U": "UPnP NAT Bit Torrent",
            }
            return client_map.get(first_char, f"Unknown ({first_char})")

        # Check for specific patterns and signatures
        checks = [
            # BitComet patterns
            ("exbc", "BitComet"),
            ("FUTB", "BitComet"),
            ("xUTB", "BitComet"),
            # BitTorrent patterns
            ("MBRV", "BitTorrent"),
            ("AZMP", "Vuze"),
            ("LIME", "LimeWire"),
            ("PEER", "BitTorrent SDK"),
            ("BTPD", "BT Protocol Daemon"),
            ("XBT", "XBT"),
            ("Mbrv", "BitTorrent"),
            ("Plus", "Plus!"),
            ("turb", "Turbo"),
            ("pimp", "Pimp"),
            ("dane", "Deluge"),
            # Mainline patterns
            (b"\x00\x00\x00\x00".decode("latin-1"), "Mainline"),
            # Opera patterns
            ("OP", "Opera"),
            ("op", "Opera"),
            # Tixati
            ("TIX", "Tixati"),
            # WebTorrent patterns
            ("WebT", "WebTorrent"),
            ("-WW", "WebTorrent"),
        ]

        for pattern, client_name in checks:
            if pattern in peer_id:
                return client_name

        # Special handling for numeric patterns
        if peer_id.startswith("M"):
            # Mainline client
            return "BitTorrent (Mainline)"
        elif peer_id_upper.startswith("AZUREUS"):
            return "Azureus"
        elif peer_id_lower.startswith("bitcomet"):
            return "BitComet"
        elif peer_id.startswith("\x00\x00\x00\x00"):
            return "Generic Client"

        # Try to extract readable ASCII for unknown clients
        readable_part = ""
        for char in peer_id[:8]:
            if (
                BitTorrentProtocolConstants.PRINTABLE_ASCII_MIN
                <= ord(char)
                <= BitTorrentProtocolConstants.PRINTABLE_ASCII_MAX
            ):  # Printable ASCII
                readable_part += char
            else:
                readable_part += "?"

        if len(readable_part) > 2 and readable_part.count("?") < len(readable_part) / 2:
            return f"Unknown ({readable_part})"

        return "Unknown"

    @property
    def peers(self):
        logger.debug("Seeder get peers", extra={"class_name": self.__class__.__name__})
        result = []
        if b"peers" not in self.info:
            logger.debug(
                "😲 No peers data available from tracker response",
                extra={"class_name": self.__class__.__name__},
            )
            return result

        # Clear existing data
        BaseSeeder.peer_clients.clear()
        self.peer_data.clear()

        peers = self.info[b"peers"]
        logger.debug(
            f"🔍 Processing peers data: {type(peers)}",
            extra={"class_name": self.__class__.__name__},
        )

        # Handle compact peer format (6 bytes per peer: 4 for IP, 2 for port)
        if isinstance(peers, bytes):
            if len(peers) == 0:
                # If no real peers, add some fake ones for demonstration
                logger.debug(
                    "🎭 No real peers found, generating demo peers for testing",
                    extra={"class_name": self.__class__.__name__},
                )
                fake_peers = [
                    (
                        "185.125.190.58",
                        51413,
                        "-DE2100-abc123456789",
                    ),  # Deluge 2.1.0 (Germany)
                    (
                        "91.219.215.227",
                        6881,
                        "-qB4510-def123456789",
                    ),  # qBittorrent 4.5.1 (Netherlands)
                    (
                        "195.154.173.208",
                        8999,
                        "-TR4000-ghi123456789",
                    ),  # Transmission 4.0.0 (France)
                    (
                        "173.252.95.24",
                        51413,
                        "-UT3630-jkl123456789",
                    ),  # µTorrent 3.6.3 (USA)
                    (
                        "46.229.165.133",
                        9091,
                        "-LT2000-mno123456789",
                    ),  # libtorrent 2.0.0 (Romania)
                    (
                        "51.75.144.43",
                        8080,
                        "-AZ5750-pqr123456789",
                    ),  # Vuze 5.7.5 (Canada)
                    (
                        "94.23.173.157",
                        6969,
                        "-RT1000-stu123456789",
                    ),  # rTorrent 1.0.0 (Poland)
                    (
                        "213.186.33.5",
                        52847,
                        "-BI1630-vwx123456789",
                    ),  # BiglyBT 1.6.3 (Germany)
                ]

                for ip, port, peer_id in fake_peers:
                    peer_address = f"{ip}:{port}"
                    result.append(peer_address)
                    logger.debug(
                        f"🤖 Added demo peer: {peer_address} ({peer_id})",
                        extra={"class_name": self.__class__.__name__},
                    )

                    # Create comprehensive peer data
                    peer_data = self.create_peer_data(ip, port, peer_id.encode())
                    self.peer_data[peer_address] = peer_data
                    BaseSeeder.peer_clients[peer_address] = peer_data["client"]
            else:
                peer_count = len(peers) // 6
                logger.debug(
                    f"🗂 Parsing compact peer data ({len(peers)} bytes = {peer_count})",
                    extra={"class_name": self.__class__.__name__},
                )
                for i in range(0, len(peers), 6):
                    if i + 6 <= len(peers):
                        ip_bytes = peers[i : i + 4]  # noqa: E203
                        ip = ".".join(str(x) for x in ip_bytes)
                        port_bytes = peers[i + 4 : i + 6]  # noqa: E203
                        port = struct.unpack(">H", port_bytes)[0]
                        peer_address = f"{ip}:{port}"
                        result.append(peer_address)
                        logger.debug(
                            f"👥 Found peer: {peer_address}",
                            extra={"class_name": self.__class__.__name__},
                        )

                        # Create comprehensive peer data
                        peer_data = self.create_peer_data(ip, port)
                        self.peer_data[peer_address] = peer_data
                        BaseSeeder.peer_clients[peer_address] = peer_data["client"]

        # Handle list format - could be dictionary format or UDP tuple format
        elif isinstance(peers, list):
            if len(peers) > 0:
                # Check if this is UDP tuple format [(ip, port), ...] or HTTP dict format
                first_peer = peers[0]
                if isinstance(first_peer, tuple) and len(first_peer) == 2:
                    # UDP tuple format: [(ip, port), ...]
                    logger.debug(
                        f"🗃 Parsing UDP tuple peer data ({len(peers)} peer entries)",
                        extra={"class_name": self.__class__.__name__},
                    )
                    for i, (ip, port) in enumerate(peers):
                        peer_address = f"{ip}:{port}"
                        result.append(peer_address)

                        logger.debug(
                            f"👥 UDP Peer {i+1}: {peer_address}",
                            extra={"class_name": self.__class__.__name__},
                        )

                        # Create comprehensive peer data (no peer_id available in UDP)
                        peer_data = self.create_peer_data(ip, port)
                        self.peer_data[peer_address] = peer_data
                        BaseSeeder.peer_clients[peer_address] = peer_data["client"]

                elif isinstance(first_peer, dict):
                    # HTTP dictionary format
                    logger.debug(
                        f"🗃 Parsing HTTP dictionary peer data ({len(peers)} entries)",
                        extra={"class_name": self.__class__.__name__},
                    )
                    for i, peer_dict in enumerate(peers):
                        # Handle both byte keys and string keys
                        ip_key = b"ip" if b"ip" in peer_dict else "ip"
                        port_key = b"port" if b"port" in peer_dict else "port"
                        peer_id_key = b"peer id" if b"peer id" in peer_dict else "peer id"

                        ip = peer_dict.get(ip_key, b"")
                        if isinstance(ip, bytes):
                            ip = ip.decode("utf-8", errors="ignore")

                        port = peer_dict.get(port_key, 0)
                        peer_id = peer_dict.get(peer_id_key, b"")

                        if ip and port:
                            peer_address = f"{ip}:{port}"
                            result.append(peer_address)

                            # Log detailed peer info
                            client_name = self.identify_client_from_peer_id(peer_id) if peer_id else "Unknown"

                            # Add detected client to settings
                            if client_name and client_name != "Unknown":
                                self.settings.add_detected_client(client_name)

                            logger.debug(
                                f"👥 HTTP Peer {i+1}: {peer_address} ({client_name})",
                                extra={"class_name": self.__class__.__name__},
                            )
                            if peer_id:
                                peer_id_str = (
                                    peer_id.decode("utf-8", errors="ignore")
                                    if isinstance(peer_id, bytes)
                                    else str(peer_id)
                                )
                                truncated = "..." if len(peer_id_str) > 20 else ""
                                logger.debug(
                                    f"🆔 Peer ID: {peer_id_str[:20]}{truncated}",
                                    extra={"class_name": self.__class__.__name__},
                                )

                            # Create comprehensive peer data with peer ID
                            peer_data = self.create_peer_data(ip, port, peer_id)
                            self.peer_data[peer_address] = peer_data
                            BaseSeeder.peer_clients[peer_address] = peer_data["client"]
                else:
                    logger.warning(
                        f"❓ Unknown peer list format: {type(first_peer)}",
                        extra={"class_name": self.__class__.__name__},
                    )

        else:
            logger.warning(
                f"❓ Unknown peers data format: {type(peers)}",
                extra={"class_name": self.__class__.__name__},
            )

        logger.debug(
            f"✅ Processed {len(result)} total peers",
            extra={"class_name": self.__class__.__name__},
        )
        return result

    def get_peer_data(self, peer_address):
        """Get comprehensive peer data for a specific peer"""
        return self.peer_data.get(peer_address, {})

    def guess_client_from_ip(self, ip):
        """Fallback method to guess client when peer ID is not available"""
        # This is a basic fallback - in reality we can't determine client from IP
        # We could potentially use other heuristics like port numbers, etc.
        return "Unknown Client"

    def get_country_from_ip(self, ip):
        """Get country code from IP address with enhanced detection"""
        # Check for private/local IP ranges first
        if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172.16."):
            return "LAN"
        elif ip.startswith("127."):
            return "LO"

        # Enhanced IP-to-country mapping for common IP ranges
        # This is a simplified lookup - in production you'd use MaxMind GeoIP2 or similar
        ip_parts = ip.split(".")
        if len(ip_parts) != 4:
            return "??"

        try:
            first_octet = int(ip_parts[0])
            second_octet = int(ip_parts[1])

            # Common country IP ranges (simplified for demo)
            country_ranges = {
                # Germany (185.x.x.x, 213.x.x.x)
                (185, 125): "DE",
                (185, 189): "DE",
                (213, 186): "DE",
                # Netherlands (91.x.x.x)
                (91, 219): "NL",
                (91, 208): "NL",
                # France (195.x.x.x)
                (195, 154): "FR",
                (195, 132): "FR",
                # USA (173.x.x.x, 198.x.x.x)
                (173, 252): "US",
                (198, 51): "US",
                (208, 67): "US",
                # Romania (46.x.x.x)
                (46, 229): "RO",
                (46, 151): "RO",
                # Canada (51.x.x.x)
                (51, 75): "CA",
                (51, 222): "CA",
                # Poland (94.x.x.x)
                (94, 23): "PL",
                (94, 152): "PL",
                # UK (81.x.x.x, 86.x.x.x)
                (81, 174): "GB",
                (86, 146): "GB",
                # Russia (95.x.x.x)
                (95, 154): "RU",
                (95, 216): "RU",
                # Japan (210.x.x.x)
                (210, 188): "JP",
                (210, 196): "JP",
                # China (114.x.x.x, 223.x.x.x)
                (114, 114): "CN",
                (223, 5): "CN",
                # Brazil (200.x.x.x)
                (200, 147): "BR",
                (200, 98): "BR",
            }

            country = country_ranges.get((first_octet, second_octet))
            if country:
                return country

            # Fallback to continent-based detection for common ranges
            if 1 <= first_octet <= 126:
                # Americas, parts of Asia-Pacific
                if 173 <= first_octet <= 208:
                    return "US"  # Likely USA
                elif 200 <= first_octet <= 223:
                    return "??-SA"  # South America or Asia
            elif 128 <= first_octet <= 191:
                # Europe, Middle East, parts of Africa
                if 185 <= first_octet <= 195:
                    return "??-EU"  # Likely Europe
                elif 41 <= first_octet <= 105:
                    return "??-AF"  # Africa
            elif 192 <= first_octet <= 223:
                # Asia-Pacific
                if 210 <= first_octet <= 223:
                    return "??-AP"  # Asia-Pacific

        except ValueError:
            pass

        return "??"

    def create_peer_data(self, ip, port, peer_id=None, client_name=None):
        """Create comprehensive peer data structure"""
        address = f"{ip}:{port}"

        if not client_name:
            client_name = self.identify_client_from_peer_id(peer_id) if peer_id else self.guess_client_from_ip(ip)

        # Add detected client to settings
        if client_name and client_name != "Unknown" and "?" not in client_name:
            self.settings.add_detected_client(client_name)

        country = self.get_country_from_ip(ip)

        # Enhanced realistic peer data simulation
        # Create more realistic progress and speed patterns based on client type

        # Use configurable client speed profiles
        client_behaviors = self.client_speed_profiles

        # Extract base client name for behavior lookup
        base_client = client_name.split()[0] if client_name and " " in client_name else client_name
        behavior = client_behaviors.get(
            base_client,
            client_behaviors.get(
                "default",
                {"max_down": 1024 * 1024, "max_up": 512 * 1024, "seed_ratio": 0.25},
            ),
        )

        # Generate realistic progress (more peers at high completion)
        if random.random() < behavior["seed_ratio"]:
            # This peer is a seeder
            progress = 1.0
            down_speed = 0.0  # Seeders don't download
            up_speed = (
                random.uniform(0, behavior["max_up"])
                if random.random() > self.seeder_upload_activity_probability
                else 0.0
            )
        else:
            # This peer is a leecher with realistic progress distribution
            # More peers tend to be at higher completion percentages
            progress_rand = random.random()
            if progress_rand < self.progress_distribution_start:
                progress = random.uniform(0.0, 0.1)  # Configurable % just started
            elif progress_rand < self.progress_distribution_middle:
                progress = random.uniform(0.1, 0.5)  # Configurable % in middle
            elif progress_rand < self.progress_distribution_almost:
                progress = random.uniform(0.5, 0.9)  # Configurable % almost done
            else:
                progress = random.uniform(0.9, 0.99)  # Remaining % nearly complete

            # Download/upload speeds based on progress and client behavior
            if progress < 0.1:
                # Just started - lower speeds
                down_speed = random.uniform(0, behavior["max_down"] * 0.3)
                up_speed = random.uniform(0, behavior["max_up"] * 0.1)
            elif progress < 0.5:
                # Mid download - peak speeds
                down_speed = random.uniform(behavior["max_down"] * 0.2, behavior["max_down"])
                up_speed = random.uniform(0, behavior["max_up"] * 0.5)
            else:
                # Nearly complete - slower download, more upload
                down_speed = random.uniform(0, behavior["max_down"] * 0.6)
                up_speed = random.uniform(0, behavior["max_up"] * 0.8)

            # Sometimes peers are idle (configurable chance)
            if random.random() < self.peer_idle_chance:
                down_speed = 0.0
                up_speed = 0.0

        is_seed = progress >= 1.0

        # Log peer analysis
        logger.debug(
            f"🔍 Analyzing peer {address}: {client_name}, {country}, Seed={is_seed}",
            extra={"class_name": self.__class__.__name__},
        )
        if progress > 0:
            down_kb = down_speed / 1024
            up_kb = up_speed / 1024
            progress_pct = progress * 100
            logger.debug(
                f"📈 Stats: {progress_pct:.1f}%, D:{down_kb:.1f} KB/s, U:{up_kb:.1f} KB/s",
                extra={"class_name": self.__class__.__name__},
            )

        peer_data = {
            "address": address,
            "client": client_name,
            "country": country,
            "progress": progress,
            "down_speed": down_speed,
            "up_speed": up_speed,
            "seed": is_seed,
            "peer_id": (
                peer_id.decode("utf-8", errors="ignore")
                if isinstance(peer_id, bytes)
                else str(peer_id) if peer_id else ""
            ),
        }

        return peer_data

    # TODO: UNUSED METHOD - Consider removing or integrating into active code path
    # def update_peer_speeds(self):
    #     """Update transfer speeds for existing peers to simulate activity"""
    #     logger.debug(
    #         f"🔄 Updating speeds for {len(self.peer_data)} peers",
    #         extra={"class_name": self.__class__.__name__},
    #     )
    #
    #     for peer_address, peer_data in self.peer_data.items():
    #         client_name = peer_data.get("client", "Unknown")
    #         progress = peer_data.get("progress", 0.0)
    #         is_seed = peer_data.get("seed", False)
    #
    #         # Get client behavior patterns from configured profiles
    #         base_client = client_name.split()[0] if " " in client_name else client_name
    #         behavior = self.client_speed_profiles.get(
    #             base_client,
    #             self.client_speed_profiles.get("default", {"max_down": 1024 * 1024, "max_up": 512 * 1024}),
    #         )
    #
    #         # Update speeds with some randomness to simulate network fluctuations
    #         if is_seed:
    #             # Seeders only upload
    #             current_up = peer_data.get("up_speed", 0.0)
    #             # Fluctuate by ±30% or go idle (configurable % of the time)
    #             if random.random() < self.peer_behavior_analysis_probability:
    #                 new_up_speed = 0.0  # Go idle
    #             else:
    #                 fluctuation = random.uniform(0.7, 1.3)
    #                 max_up = behavior["max_up"]
    #                 new_up_speed = min(max_up, max(0, current_up * fluctuation))
    #
    #             peer_data["down_speed"] = 0.0
    #             peer_data["up_speed"] = new_up_speed
    #         else:
    #             # Leechers can download and upload
    #             current_down = peer_data.get("down_speed", 0.0)
    #             current_up = peer_data.get("up_speed", 0.0)
    #
    #             # Configurable chance to be idle vs active
    #             if random.random() < self.peer_status_change_probability:
    #                 new_down_speed = 0.0
    #                 new_up_speed = 0.0
    #             else:
    #                 # Adjust speeds based on progress
    #                 if progress < 0.1:
    #                     speed_factor = random.uniform(0.1, 0.4)
    #                 elif progress < 0.5:
    #                     speed_factor = random.uniform(0.5, 1.0)
    #                 else:
    #                     speed_factor = random.uniform(0.3, 0.8)
    #
    #                 fluctuation = random.uniform(0.6, 1.4)
    #                 new_down_speed = min(
    #                     behavior["max_down"] * speed_factor,
    #                     max(0, current_down * fluctuation),
    #                 )
    #                 new_up_speed = min(
    #                     behavior["max_up"] * speed_factor * 0.3,
    #                     max(0, current_up * fluctuation),
    #                 )
    #
    #             peer_data["down_speed"] = new_down_speed
    #             peer_data["up_speed"] = new_up_speed
    #
    #             # Occasionally update progress for leechers (very slow progress)
    #             if not is_seed and random.random() < self.peer_dropout_probability:
    #                 progress_increment = random.uniform(0.001, 0.01)  # 0.1-1% progress
    #                 new_progress = min(0.99, progress + progress_increment)
    #                 peer_data["progress"] = new_progress
    #
    #                 # Check if became a seeder
    #                 if new_progress >= 1.0:
    #                     peer_data["progress"] = 1.0
    #                     peer_data["seed"] = True
    #                     peer_data["down_speed"] = 0.0

    @property
    def clients(self):
        logger.debug("Seeder get clients", extra={"class_name": self.__class__.__name__})
        return BaseSeeder.peer_clients

    @property
    def seeders(self):
        logger.debug("Seeder get seeders", extra={"class_name": self.__class__.__name__})
        return self.info[b"complete"] if b"complete" in self.info else 0

    @property
    def tracker(self):
        logger.debug("Seeder get tracker", extra={"class_name": self.__class__.__name__})
        return self.tracker_url

    @property
    def leechers(self):
        logger.debug("Seeder get leechers", extra={"class_name": self.__class__.__name__})
        return self.info[b"incomplete"] if b"incomplete" in self.info else 0
