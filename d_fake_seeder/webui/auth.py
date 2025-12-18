"""
Web UI Authentication Handler.

Provides authentication middleware and utilities for the Web UI server.
"""

import base64
import secrets
import time
from typing import Any, Callable, Dict, Optional, Set

from d_fake_seeder.lib.logger import logger

# Try to import aiohttp - it's an optional dependency
try:
    from aiohttp import web

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    web = None


class SessionStore:
    """Simple in-memory session store."""

    def __init__(self, timeout_minutes: int = 60) -> None:
        """
        Initialize the session store.

        Args:
            timeout_minutes: Session timeout in minutes.
        """
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.timeout_seconds = timeout_minutes * 60

    def create_session(self, username: str) -> str:
        """
        Create a new session.

        Args:
            username: The authenticated username.

        Returns:
            Session token.
        """
        token = secrets.token_urlsafe(32)
        self.sessions[token] = {
            "username": username,
            "created_at": time.time(),
            "last_access": time.time(),
        }
        return token

    def validate_session(self, token: str) -> Optional[str]:
        """
        Validate a session token.

        Args:
            token: Session token to validate.

        Returns:
            Username if valid, None otherwise.
        """
        session = self.sessions.get(token)
        if not session:
            return None

        # Check if session has expired
        if time.time() - session["last_access"] > self.timeout_seconds:
            self.destroy_session(token)
            return None

        # Update last access time
        session["last_access"] = time.time()
        username: str = session["username"]
        return username

    def destroy_session(self, token: str) -> None:
        """
        Destroy a session.

        Args:
            token: Session token to destroy.
        """
        self.sessions.pop(token, None)

    def cleanup_expired(self) -> None:
        """Remove all expired sessions."""
        current_time = time.time()
        expired = [
            token
            for token, session in self.sessions.items()
            if current_time - session["last_access"] > self.timeout_seconds
        ]
        for token in expired:
            del self.sessions[token]


class FailedLoginTracker:
    """Track failed login attempts for rate limiting."""

    def __init__(self, max_failures: int = 5, ban_duration: int = 300) -> None:
        """
        Initialize the failed login tracker.

        Args:
            max_failures: Maximum failed attempts before ban.
            ban_duration: Ban duration in seconds.
        """
        self.max_failures = max_failures
        self.ban_duration = ban_duration
        self.failed_attempts: Dict[str, list] = {}
        self.banned_ips: Dict[str, float] = {}

    def record_failure(self, ip: str) -> bool:
        """
        Record a failed login attempt.

        Args:
            ip: Client IP address.

        Returns:
            True if IP is now banned.
        """
        current_time = time.time()

        # Clean old attempts
        if ip in self.failed_attempts:
            self.failed_attempts[ip] = [t for t in self.failed_attempts[ip] if current_time - t < self.ban_duration]

        # Add new attempt
        if ip not in self.failed_attempts:
            self.failed_attempts[ip] = []
        self.failed_attempts[ip].append(current_time)

        # Check if should ban
        if len(self.failed_attempts[ip]) >= self.max_failures:
            self.banned_ips[ip] = current_time
            return True

        return False

    def is_banned(self, ip: str) -> bool:
        """
        Check if an IP is banned.

        Args:
            ip: Client IP address.

        Returns:
            True if banned.
        """
        if ip not in self.banned_ips:
            return False

        # Check if ban has expired
        if time.time() - self.banned_ips[ip] > self.ban_duration:
            del self.banned_ips[ip]
            self.failed_attempts.pop(ip, None)
            return False

        return True

    def clear_failures(self, ip: str) -> None:
        """Clear failed attempts for an IP after successful login."""
        self.failed_attempts.pop(ip, None)


def create_auth_middleware(settings: Any) -> Any:
    """
    Create authentication middleware for aiohttp.

    Args:
        settings: AppSettings instance.

    Returns:
        Middleware function.
    """
    if not AIOHTTP_AVAILABLE:
        raise ImportError("aiohttp is required for Web UI")

    timeout_minutes = settings.get("webui.session_timeout_minutes", 60)
    max_failures = settings.get("webui.ban_after_failures", 5)

    session_store = SessionStore(timeout_minutes)
    login_tracker = FailedLoginTracker(max_failures)

    # Public routes that don't require authentication
    public_routes: Set[str] = {"/api/login", "/api/health", "/"}

    @web.middleware
    async def auth_middleware(request: web.Request, handler: Callable) -> web.Response:
        """Authentication middleware."""
        # Check if auth is enabled
        if not settings.get("webui.auth_enabled", True):
            return await handler(request)

        # Allow public routes
        if request.path in public_routes:
            return await handler(request)

        # Check for banned IP
        client_ip = request.remote or "unknown"
        if login_tracker.is_banned(client_ip):
            logger.warning(
                f"WebUI: Banned IP attempted access: {client_ip}",
                extra={"class_name": "AuthMiddleware"},
            )
            return web.json_response(
                {"error": "Too many failed attempts. Try again later."},
                status=429,
            )

        # Check for session token in cookie or header
        token = request.cookies.get("session") or request.headers.get("X-Session-Token")

        if token:
            username = session_store.validate_session(token)
            if username:
                request["username"] = username
                return await handler(request)

        # Check for Basic Auth
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Basic "):
            try:
                credentials = base64.b64decode(auth_header[6:]).decode("utf-8")
                username, password = credentials.split(":", 1)

                expected_username = settings.get("webui.username", "admin")
                expected_password = settings.get("webui.password", "")

                if username == expected_username and password == expected_password:
                    login_tracker.clear_failures(client_ip)
                    request["username"] = username
                    return await handler(request)
                else:
                    if login_tracker.record_failure(client_ip):
                        logger.warning(
                            f"WebUI: IP banned due to failed logins: {client_ip}",
                            extra={"class_name": "AuthMiddleware"},
                        )
            except Exception:
                pass

        # No valid authentication
        return web.json_response(
            {"error": "Authentication required"},
            status=401,
            headers={"WWW-Authenticate": 'Basic realm="DFakeSeeder"'},
        )

    return auth_middleware


def create_security_middleware(settings: Any) -> Any:
    """
    Create security headers middleware.

    Args:
        settings: AppSettings instance.

    Returns:
        Middleware function.
    """
    if not AIOHTTP_AVAILABLE:
        raise ImportError("aiohttp is required for Web UI")

    @web.middleware
    async def security_middleware(request: web.Request, handler: Callable) -> web.Response:
        """Add security headers to responses."""
        response = await handler(request)

        # Add security headers if enabled
        if settings.get("webui.secure_headers", True):
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Clickjacking protection
        if settings.get("webui.clickjacking_protection", True):
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"

        return response

    return security_middleware
