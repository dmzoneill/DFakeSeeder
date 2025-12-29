# fmt: off
# isort: skip_file
"""
HTTP Handler for the inbuilt BitTorrent tracker.

Implements BEP 3 (HTTP Tracker Protocol) and BEP 23 (Compact Peer Lists).
"""

from http.server import BaseHTTPRequestHandler
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

from d_fake_seeder.domain.torrent import bencoding
from d_fake_seeder.lib.logger import logger

# fmt: on


class TrackerHTTPHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for BitTorrent tracker requests.

    Handles /announce and /scrape endpoints.
    """

    # Reference to tracker server (set by TrackerServer)
    tracker_server: Any = None

    # pylint: disable=arguments-differ
    def log_message(self, _format: str, *args: Any) -> None:
        """Override to use our logger instead of stderr."""
        if self.tracker_server and self.tracker_server.log_announces:
            logger.trace(
                f"Tracker HTTP: {_format % args}",
                extra={"class_name": self.__class__.__name__},
            )

    def do_GET(self) -> None:  # pylint: disable=invalid-name
        """Handle GET requests (announce and scrape). Method name required by BaseHTTPRequestHandler."""
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/announce":
            self._handle_announce(parsed.query)
        elif path == "/scrape":
            self._handle_scrape(parsed.query)
        else:
            self._send_error("Invalid request path")

    def _parse_announce_params(self, query: str) -> Optional[Dict[str, Any]]:  # pylint: disable=too-many-locals
        """
        Parse announce request parameters.

        Required: info_hash, peer_id, port, uploaded, downloaded, left
        Optional: event, compact, numwant, ip
        """
        try:
            params = parse_qs(query, keep_blank_values=True)

            # Extract required parameters
            info_hash = params.get("info_hash", [None])[0]
            peer_id = params.get("peer_id", [None])[0]
            port = params.get("port", [None])[0]
            uploaded = params.get("uploaded", [None])[0]
            downloaded = params.get("downloaded", [None])[0]
            left = params.get("left", [None])[0]

            # Validate required params
            if not all([info_hash, peer_id, port, uploaded, downloaded, left]):
                return None

            # URL-decode info_hash and peer_id (they come as raw bytes)
            # The parse_qs decodes them, but they may be URL-encoded bytes
            info_hash_bytes: bytes
            peer_id_bytes: bytes
            if isinstance(info_hash, str):
                info_hash_bytes = info_hash.encode("latin-1")
            else:
                info_hash_bytes = info_hash if info_hash else b""
            if isinstance(peer_id, str):
                peer_id_bytes = peer_id.encode("latin-1")
            else:
                peer_id_bytes = peer_id if peer_id else b""

            # Get optional parameters
            event = params.get("event", [""])[0]
            compact = params.get("compact", ["1"])[0] == "1"
            numwant = int(params.get("numwant", ["50"])[0])
            ip = params.get("ip", [None])[0]

            # Use client IP if not provided
            if not ip:
                ip = self.client_address[0]

            # Convert values with proper type safety
            port_int = int(port) if port else 0
            uploaded_int = int(uploaded) if uploaded else 0
            downloaded_int = int(downloaded) if downloaded else 0
            left_int = int(left) if left else 0

            return {
                "info_hash": info_hash_bytes,
                "peer_id": peer_id_bytes,
                "ip": ip,
                "port": port_int,
                "uploaded": uploaded_int,
                "downloaded": downloaded_int,
                "left": left_int,
                "event": event,
                "compact": compact,
                "numwant": min(numwant, 200),  # Cap at 200
            }
        except (ValueError, TypeError, KeyError) as e:
            logger.warning(
                f"Failed to parse announce params: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return None

    def _handle_announce(self, query: str) -> None:
        """Handle /announce request."""
        if not self.tracker_server:
            self._send_error("Tracker not initialized")
            return

        # Check security (IP filter and rate limit)
        client_ip = self.client_address[0]
        allowed, reason = self.tracker_server.security.check_request(client_ip)
        if not allowed:
            self._send_error(reason or "Request blocked")
            return

        params = self._parse_announce_params(query)
        if not params:
            self._send_error("Missing or invalid parameters")
            return

        info_hash = params["info_hash"]
        peer_id = params["peer_id"]
        event = params["event"]

        # Check if torrent is allowed (private mode)
        if not self.tracker_server.torrent_registry.is_allowed(info_hash, self.tracker_server.private_mode):
            self._send_error("Torrent not registered")
            return

        # Handle event
        if event == "stopped":
            # Remove peer
            self.tracker_server.peer_database.remove_peer(info_hash, peer_id)
        else:
            # Add or update peer
            self.tracker_server.peer_database.add_or_update_peer(
                info_hash=info_hash,
                peer_id=peer_id,
                ip=params["ip"],
                port=params["port"],
                uploaded=params["uploaded"],
                downloaded=params["downloaded"],
                left=params["left"],
                is_internal=False,
            )

            # Register torrent if not in private mode
            if not self.tracker_server.private_mode:
                self.tracker_server.torrent_registry.register_torrent(
                    info_hash=info_hash,
                    is_internal=False,
                )

            # Update torrent stats
            self.tracker_server.torrent_registry.update_announce(
                info_hash=info_hash,
                uploaded=params["uploaded"],
                downloaded=params["downloaded"],
                completed=(event == "completed"),
            )

        # Get peers to return
        compact_peers, dict_peers = self.tracker_server.peer_database.get_peers(
            info_hash=info_hash,
            max_peers=params["numwant"],
            exclude_peer_id=peer_id,
            compact=params["compact"],
        )

        # Get stats
        stats = self.tracker_server.peer_database.get_stats(info_hash)

        # Build response
        response: Dict[bytes, Any] = {
            b"interval": self.tracker_server.announce_interval,
            b"min interval": self.tracker_server.announce_interval // 2,
            b"complete": stats["complete"],
            b"incomplete": stats["incomplete"],
        }

        if params["compact"]:
            response[b"peers"] = compact_peers
        else:
            response[b"peers"] = dict_peers

        self._send_bencoded_response(response)

        logger.trace(
            f"Announce: {params['ip']}:{params['port']} for " f"{info_hash.hex()[:16]} event={event or 'periodic'}",
            extra={"class_name": self.__class__.__name__},
        )

    def _handle_scrape(self, query: str) -> None:
        """Handle /scrape request."""
        if not self.tracker_server:
            self._send_error("Tracker not initialized")
            return

        if not self.tracker_server.enable_scrape:
            self._send_error("Scrape disabled")
            return

        try:
            params = parse_qs(query, keep_blank_values=True)
            info_hashes = params.get("info_hash", [])

            # If no specific hashes, return all (if allowed)
            if not info_hashes:
                info_hashes = [h.decode("latin-1") for h in self.tracker_server.peer_database.get_all_info_hashes()]

            files: Dict[bytes, Dict[bytes, int]] = {}

            for ih in info_hashes:
                if isinstance(ih, str):
                    ih_bytes = ih.encode("latin-1")
                else:
                    ih_bytes = ih

                stats = self.tracker_server.peer_database.get_stats(ih_bytes)
                torrent = self.tracker_server.torrent_registry.get_torrent(ih_bytes)

                files[ih_bytes] = {
                    b"complete": stats["complete"],
                    b"incomplete": stats["incomplete"],
                    b"downloaded": torrent.times_completed if torrent else 0,
                }

            response = {b"files": files}
            self._send_bencoded_response(response)

            logger.trace(
                f"Scrape: {len(files)} torrents",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning(
                f"Scrape error: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            self._send_error("Scrape failed")

    def _send_bencoded_response(self, data: Dict[bytes, Any]) -> None:
        """Send a bencoded response."""
        try:
            encoded = bencoding.encode(data)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                f"Failed to send response: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )
            self._send_error("Internal error")

    def _send_error(self, message: str) -> None:
        """Send a tracker error response."""
        response = {b"failure reason": message.encode()}
        try:
            encoded = bencoding.encode(response)
            self.send_response(200)  # Tracker errors use 200 OK
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
        except Exception:  # pylint: disable=broad-exception-caught
            self.send_response(500)
            self.end_headers()
