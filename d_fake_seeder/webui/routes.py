"""
Web UI API Routes.

Defines the REST API endpoints for the Web UI server.
"""

from typing import Any

from d_fake_seeder.lib.logger import logger

# Try to import aiohttp - it's an optional dependency
try:
    from aiohttp import web

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    web = None


def setup_routes(app: Any) -> None:
    """
    Set up all API routes for the Web UI.

    Args:
        app: aiohttp Application instance.
    """
    if not AIOHTTP_AVAILABLE:
        raise ImportError("aiohttp is required for Web UI")

    # Health check
    app.router.add_get("/api/health", handle_health)

    # Authentication
    app.router.add_post("/api/login", handle_login)
    app.router.add_post("/api/logout", handle_logout)

    # Torrents
    app.router.add_get("/api/torrents", handle_get_torrents)
    app.router.add_get("/api/torrents/{torrent_id}", handle_get_torrent)
    app.router.add_post("/api/torrents/{torrent_id}/start", handle_start_torrent)
    app.router.add_post("/api/torrents/{torrent_id}/stop", handle_stop_torrent)
    app.router.add_delete("/api/torrents/{torrent_id}", handle_delete_torrent)

    # Statistics
    app.router.add_get("/api/stats", handle_get_stats)
    app.router.add_get("/api/stats/speed", handle_get_speed_stats)

    # Settings
    app.router.add_get("/api/settings", handle_get_settings)
    app.router.add_patch("/api/settings", handle_update_settings)

    # Alternative speeds
    app.router.add_get("/api/alt-speed", handle_get_alt_speed)
    app.router.add_post("/api/alt-speed/toggle", handle_toggle_alt_speed)

    # Root serves simple dashboard
    app.router.add_get("/", handle_dashboard)

    logger.debug(
        "WebUI routes configured",
        extra={"class_name": "WebUIRoutes"},
    )


async def handle_health(request: Any) -> Any:
    """Health check endpoint."""
    return web.json_response({"status": "ok", "service": "DFakeSeeder WebUI"})


async def handle_login(request: Any) -> Any:
    """Handle login request."""
    try:
        data = await request.json()
        username = data.get("username", "")
        password = data.get("password", "")

        settings = request.app["settings"]
        expected_username = settings.get("webui.username", "admin")
        expected_password = settings.get("webui.password", "")

        if username == expected_username and password == expected_password:
            # Create session (simplified - in production use proper session management)
            response = web.json_response({"success": True, "username": username})
            return response

        return web.json_response({"success": False, "error": "Invalid credentials"}, status=401)
    except Exception as e:
        logger.error(f"Login error: {e}", extra={"class_name": "WebUIRoutes"})
        return web.json_response({"error": str(e)}, status=500)


async def handle_logout(request: Any) -> Any:
    """Handle logout request."""
    response = web.json_response({"success": True})
    response.del_cookie("session")
    return response


async def handle_get_torrents(request: Any) -> Any:
    """Get list of all torrents."""
    try:
        model = request.app["model"]
        torrents = model.get_torrents() if model else []

        torrent_list = []
        for torrent in torrents:
            torrent_list.append(
                {
                    "id": getattr(torrent, "file_path", ""),
                    "name": getattr(torrent, "name", "Unknown"),
                    "active": getattr(torrent, "active", False),
                    "upload_speed": getattr(torrent, "upload_speed", 0),
                    "download_speed": getattr(torrent, "download_speed", 0),
                    "total_uploaded": getattr(torrent, "total_uploaded", 0),
                    "total_downloaded": getattr(torrent, "total_downloaded", 0),
                    "ratio": getattr(torrent, "ratio", 0.0),
                    "total_size": getattr(torrent, "total_size", 0),
                }
            )

        return web.json_response({"torrents": torrent_list, "count": len(torrent_list)})
    except Exception as e:
        logger.error(f"Error getting torrents: {e}", extra={"class_name": "WebUIRoutes"})
        return web.json_response({"error": str(e)}, status=500)


async def handle_get_torrent(request: Any) -> Any:
    """Get details of a specific torrent."""
    try:
        torrent_id = request.match_info["torrent_id"]
        model = request.app["model"]

        if not model:
            return web.json_response({"error": "Model not available"}, status=500)

        torrents = model.get_torrents()
        for torrent in torrents:
            if getattr(torrent, "file_path", "") == torrent_id:
                return web.json_response(
                    {
                        "id": torrent_id,
                        "name": getattr(torrent, "name", "Unknown"),
                        "active": getattr(torrent, "active", False),
                        "upload_speed": getattr(torrent, "upload_speed", 0),
                        "download_speed": getattr(torrent, "download_speed", 0),
                        "total_uploaded": getattr(torrent, "total_uploaded", 0),
                        "total_downloaded": getattr(torrent, "total_downloaded", 0),
                        "ratio": getattr(torrent, "ratio", 0.0),
                        "total_size": getattr(torrent, "total_size", 0),
                        "info_hash": getattr(torrent, "info_hash", ""),
                        "tracker": getattr(torrent, "tracker", ""),
                    }
                )

        return web.json_response({"error": "Torrent not found"}, status=404)
    except Exception as e:
        logger.error(f"Error getting torrent: {e}", extra={"class_name": "WebUIRoutes"})
        return web.json_response({"error": str(e)}, status=500)


async def handle_start_torrent(request: Any) -> Any:
    """Start a torrent."""
    try:
        torrent_id = request.match_info["torrent_id"]
        model = request.app["model"]

        if not model:
            return web.json_response({"error": "Model not available"}, status=500)

        torrents = model.get_torrents()
        for torrent in torrents:
            if getattr(torrent, "file_path", "") == torrent_id:
                torrent.active = True
                return web.json_response({"success": True})

        return web.json_response({"error": "Torrent not found"}, status=404)
    except Exception as e:
        logger.error(f"Error starting torrent: {e}", extra={"class_name": "WebUIRoutes"})
        return web.json_response({"error": str(e)}, status=500)


async def handle_stop_torrent(request: Any) -> Any:
    """Stop a torrent."""
    try:
        torrent_id = request.match_info["torrent_id"]
        model = request.app["model"]

        if not model:
            return web.json_response({"error": "Model not available"}, status=500)

        torrents = model.get_torrents()
        for torrent in torrents:
            if getattr(torrent, "file_path", "") == torrent_id:
                torrent.active = False
                return web.json_response({"success": True})

        return web.json_response({"error": "Torrent not found"}, status=404)
    except Exception as e:
        logger.error(f"Error stopping torrent: {e}", extra={"class_name": "WebUIRoutes"})
        return web.json_response({"error": str(e)}, status=500)


async def handle_delete_torrent(request: Any) -> Any:
    """Delete a torrent."""
    try:
        torrent_id = request.match_info["torrent_id"]
        model = request.app["model"]

        if not model:
            return web.json_response({"error": "Model not available"}, status=500)

        # Find and remove the torrent
        if hasattr(model, "remove_torrent"):
            model.remove_torrent(torrent_id)
            return web.json_response({"success": True})

        return web.json_response({"error": "Delete not supported"}, status=501)
    except Exception as e:
        logger.error(f"Error deleting torrent: {e}", extra={"class_name": "WebUIRoutes"})
        return web.json_response({"error": str(e)}, status=500)


async def handle_get_stats(request: Any) -> Any:
    """Get overall statistics."""
    try:
        model = request.app["model"]
        torrents = model.get_torrents() if model else []

        total_upload = sum(getattr(t, "total_uploaded", 0) for t in torrents)
        total_download = sum(getattr(t, "total_downloaded", 0) for t in torrents)
        active_count = sum(1 for t in torrents if getattr(t, "active", False))

        return web.json_response(
            {
                "total_torrents": len(torrents),
                "active_torrents": active_count,
                "total_uploaded": total_upload,
                "total_downloaded": total_download,
                "global_ratio": total_upload / total_download if total_download > 0 else 0,
            }
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}", extra={"class_name": "WebUIRoutes"})
        return web.json_response({"error": str(e)}, status=500)


async def handle_get_speed_stats(request: Any) -> Any:
    """Get current speed statistics."""
    try:
        model = request.app["model"]
        torrents = model.get_torrents() if model else []

        upload_speed = sum(getattr(t, "upload_speed", 0) for t in torrents)
        download_speed = sum(getattr(t, "download_speed", 0) for t in torrents)

        settings = request.app["settings"]
        alt_speed_enabled = settings.get("speed.enable_alternative_speeds", False)

        return web.json_response(
            {
                "upload_speed": upload_speed,
                "download_speed": download_speed,
                "alt_speed_enabled": alt_speed_enabled,
            }
        )
    except Exception as e:
        logger.error(f"Error getting speed stats: {e}", extra={"class_name": "WebUIRoutes"})
        return web.json_response({"error": str(e)}, status=500)


async def handle_get_settings(request: Any) -> Any:
    """Get application settings (safe subset)."""
    try:
        settings = request.app["settings"]

        # Return only safe, non-sensitive settings
        safe_settings = {
            "speed": {
                "upload_limit_kbps": settings.get("speed.upload_limit_kbps", 0),
                "download_limit_kbps": settings.get("speed.download_limit_kbps", 0),
                "enable_alternative_speeds": settings.get("speed.enable_alternative_speeds", False),
                "alt_upload_limit_kbps": settings.get("speed.alt_upload_limit_kbps", 50),
                "alt_download_limit_kbps": settings.get("speed.alt_download_limit_kbps", 100),
            },
            "scheduler": {
                "enabled": settings.get("scheduler.enabled", False),
                "start_hour": settings.get("scheduler.start_hour", 22),
                "start_minute": settings.get("scheduler.start_minute", 0),
                "end_hour": settings.get("scheduler.end_hour", 6),
                "end_minute": settings.get("scheduler.end_minute", 0),
            },
        }

        return web.json_response(safe_settings)
    except Exception as e:
        logger.error(f"Error getting settings: {e}", extra={"class_name": "WebUIRoutes"})
        return web.json_response({"error": str(e)}, status=500)


async def handle_update_settings(request: Any) -> Any:
    """Update application settings."""
    try:
        data = await request.json()
        settings = request.app["settings"]

        # Only allow updating specific settings
        allowed_keys = [
            "speed.upload_limit_kbps",
            "speed.download_limit_kbps",
            "speed.enable_alternative_speeds",
            "speed.alt_upload_limit_kbps",
            "speed.alt_download_limit_kbps",
            "scheduler.enabled",
        ]

        updated = []
        for key, value in data.items():
            if key in allowed_keys:
                settings.set(key, value)
                updated.append(key)

        return web.json_response({"success": True, "updated": updated})
    except Exception as e:
        logger.error(f"Error updating settings: {e}", extra={"class_name": "WebUIRoutes"})
        return web.json_response({"error": str(e)}, status=500)


async def handle_get_alt_speed(request: Any) -> Any:
    """Get alternative speed status."""
    try:
        settings = request.app["settings"]
        return web.json_response(
            {
                "enabled": settings.get("speed.enable_alternative_speeds", False),
                "upload_limit": settings.get("speed.alt_upload_limit_kbps", 50),
                "download_limit": settings.get("speed.alt_download_limit_kbps", 100),
            }
        )
    except Exception as e:
        logger.error(f"Error getting alt speed: {e}", extra={"class_name": "WebUIRoutes"})
        return web.json_response({"error": str(e)}, status=500)


async def handle_toggle_alt_speed(request: Any) -> Any:
    """Toggle alternative speed mode."""
    try:
        settings = request.app["settings"]
        current = settings.get("speed.enable_alternative_speeds", False)
        settings.set("speed.enable_alternative_speeds", not current)
        return web.json_response({"enabled": not current})
    except Exception as e:
        logger.error(f"Error toggling alt speed: {e}", extra={"class_name": "WebUIRoutes"})
        return web.json_response({"error": str(e)}, status=500)


async def handle_dashboard(request: Any) -> Any:
    """Serve a simple dashboard HTML page."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DFakeSeeder - Web UI</title>
    <style>
        :root {
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --accent: #e94560;
            --text-primary: #eaeaea;
            --text-secondary: #a0a0a0;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 2rem;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
        h1 { font-size: 1.8rem; }
        h1 span { color: var(--accent); }
        .stats-grid { display: grid; gap: 1rem; margin-bottom: 2rem;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
        .stat-card {
            background: var(--bg-secondary);
            padding: 1.5rem;
            border-radius: 8px;
            border-left: 3px solid var(--accent);
        }
        .stat-card h3 { font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 0.5rem; }
        .stat-card .value { font-size: 1.8rem; font-weight: 600; }
        .torrents-table {
            width: 100%;
            background: var(--bg-secondary);
            border-radius: 8px;
            overflow: hidden;
        }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 1rem; text-align: left; }
        th { background: rgba(233, 69, 96, 0.1); font-weight: 600; }
        tr:hover { background: rgba(255, 255, 255, 0.05); }
        .status-active { color: #4ade80; }
        .status-inactive { color: var(--text-secondary); }
        .alt-speed-btn {
            padding: 0.5rem 1rem;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .alt-speed-btn:hover { opacity: 0.9; }
        .alt-speed-btn.active { background: #4ade80; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>DFake<span>Seeder</span></h1>
            <button id="altSpeedBtn" class="alt-speed-btn" onclick="toggleAltSpeed()">Alt Speed: OFF</button>
        </header>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Torrents</h3>
                <div class="value" id="totalTorrents">-</div>
            </div>
            <div class="stat-card">
                <h3>Active Torrents</h3>
                <div class="value" id="activeTorrents">-</div>
            </div>
            <div class="stat-card">
                <h3>Upload Speed</h3>
                <div class="value" id="uploadSpeed">-</div>
            </div>
            <div class="stat-card">
                <h3>Download Speed</h3>
                <div class="value" id="downloadSpeed">-</div>
            </div>
        </div>

        <div class="torrents-table">
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Status</th>
                        <th>Upload</th>
                        <th>Download</th>
                        <th>Ratio</th>
                    </tr>
                </thead>
                <tbody id="torrentsList"></tbody>
            </table>
        </div>
    </div>

    <script>
        function formatSpeed(kbps) {
            if (kbps >= 1024) return (kbps / 1024).toFixed(1) + ' MB/s';
            return kbps + ' KB/s';
        }

        function formatBytes(bytes) {
            if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(2) + ' GB';
            if (bytes >= 1048576) return (bytes / 1048576).toFixed(2) + ' MB';
            return (bytes / 1024).toFixed(2) + ' KB';
        }

        async function fetchData() {
            try {
                const [statsRes, speedRes, torrentsRes] = await Promise.all([
                    fetch('/api/stats'),
                    fetch('/api/stats/speed'),
                    fetch('/api/torrents')
                ]);

                const stats = await statsRes.json();
                const speed = await speedRes.json();
                const torrents = await torrentsRes.json();

                document.getElementById('totalTorrents').textContent = stats.total_torrents;
                document.getElementById('activeTorrents').textContent = stats.active_torrents;
                document.getElementById('uploadSpeed').textContent = formatSpeed(speed.upload_speed);
                document.getElementById('downloadSpeed').textContent = formatSpeed(speed.download_speed);

                const btn = document.getElementById('altSpeedBtn');
                if (speed.alt_speed_enabled) {
                    btn.textContent = 'Alt Speed: ON';
                    btn.classList.add('active');
                } else {
                    btn.textContent = 'Alt Speed: OFF';
                    btn.classList.remove('active');
                }

                const tbody = document.getElementById('torrentsList');
                tbody.innerHTML = torrents.torrents.map(t => `
                    <tr>
                        <td>${t.name}</td>
                        <td class="${t.active ? 'status-active' : 'status-inactive'}">
                            ${t.active ? 'Active' : 'Inactive'}</td>
                        <td>${formatSpeed(t.upload_speed)}</td>
                        <td>${formatSpeed(t.download_speed)}</td>
                        <td>${t.ratio.toFixed(2)}</td>
                    </tr>
                `).join('');
            } catch (e) {
                console.error('Error fetching data:', e);
            }
        }

        async function toggleAltSpeed() {
            try {
                await fetch('/api/alt-speed/toggle', { method: 'POST' });
                fetchData();
            } catch (e) {
                console.error('Error toggling alt speed:', e);
            }
        }

        fetchData();
        setInterval(fetchData, 5000);
    </script>
</body>
</html>"""
    return web.Response(text=html, content_type="text/html")
