"""Bound HTTP bodies before parsing, and protect the local browser boundary."""

from __future__ import annotations

import asyncio
import ipaddress
from urllib.parse import urlsplit

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class LocalRequestLimits:
    def __init__(
        self,
        app: ASGIApp,
        max_bytes: int = 200_000,
        max_active: int = 4,
        body_timeout: float = 10,
        allowed_hosts: tuple[str, ...] = (),
        path_limits: dict[str, int] | None = None,
    ):
        self.app = app
        self.max_bytes = max_bytes
        self.path_limits = dict(path_limits or {})
        self.max_active = max_active
        self.body_timeout = body_timeout
        self.allowed_hosts = frozenset(allowed_hosts)
        self.active = 0

    def _host_allowed(self, host: str) -> bool:
        try:
            parsed = urlsplit("http://" + host)
            name = parsed.hostname or ""
            _ = parsed.port  # Reject malformed ports before allowing localhost.
            if parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
                return False
            if name in self.allowed_hosts or name == "localhost":
                return True
            return ipaddress.ip_address(name).is_loopback
        except ValueError:
            return False

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = {key.lower(): value.decode("latin-1") for key, value in scope["headers"]}

        async def reject(code: int, message: str) -> None:
            await JSONResponse(
                {"detail": message}, status_code=code, headers={"Retry-After": "2"} if code == 429 else None
            )(scope, receive, send)

        host = headers.get(b"host", "")
        if not self._host_allowed(host):
            await reject(400, "Host is not allowed. Use the local address printed by the server.")
            return
        origin = headers.get(b"origin")
        if origin is not None and origin != f"{scope.get('scheme', 'http')}://{host}":
            await reject(403, "Cross-origin requests to the local studio are not allowed.")
            return
        if scope["method"] not in ("POST", "PUT", "PATCH"):
            await self.app(scope, receive, send)
            return
        if self.active >= self.max_active:
            await reject(429, "The local studio is busy. Wait for an export to finish and try again.")
            return
        limit = self.path_limits.get(scope.get("path", ""), self.max_bytes)
        length = headers.get(b"content-length")
        if length is not None and (
            not length.isascii() or not length.isdigit() or len(length) > 12 or int(length) > limit
        ):
            await reject(413, f"Request is too large or has an invalid length. Limit: {limit} bytes.")
            return
        self.active += 1
        try:
            body = bytearray()
            deadline = asyncio.get_running_loop().time() + self.body_timeout
            while True:
                remaining = deadline - asyncio.get_running_loop().time()
                try:
                    message = await asyncio.wait_for(receive(), timeout=max(remaining, 0))
                except asyncio.TimeoutError:
                    await reject(408, "Request body timed out. Your local edits have not been changed.")
                    return
                if message["type"] == "http.disconnect":
                    return
                chunk = message.get("body", b"")
                if len(body) + len(chunk) > limit:
                    await reject(413, f"Request is too large. Limit: {limit} bytes.")
                    return
                body.extend(chunk)
                if not message.get("more_body", False):
                    break
            if length is not None and int(length) != len(body):
                await reject(400, "Request body length does not match Content-Length.")
                return
            delivered = False

            async def buffered_receive():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": bytes(body), "more_body": False}
                return await receive()

            await self.app(scope, buffered_receive, send)
        finally:
            self.active -= 1
