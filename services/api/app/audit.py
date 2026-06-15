"""Audit log middleware - captures all mutations with user, timestamp, IP."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger()

# HTTP methods that modify state
MUTATION_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Paths to exclude from audit logging
EXCLUDED_PATHS = {"/health", "/metrics", "/docs", "/openapi.json", "/ws/"}


class AuditLogMiddleware:
    """Captures mutation requests for audit logging."""

    @staticmethod
    async def log_mutation(request: Request, response: Response, duration_ms: float) -> None:
        """Log a mutation request."""
        if request.method not in MUTATION_METHODS:
            return
        path = request.url.path
        if any(path.startswith(ex) for ex in EXCLUDED_PATHS):
            return
        if response.status_code >= 400:
            return  # Don't log failed requests

        # Extract user info from auth header if available
        user_id = None
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                import jwt
                from .config import settings
                payload = jwt.decode(auth_header.split(" ")[1], settings.secret_key, algorithms=[settings.jwt_algorithm])
                user_id = payload.get("sub")
            except Exception:
                pass

        client_ip = request.client.host if request.client else "unknown"
        logger.info(
            "audit_mutation",
            method=request.method,
            path=path,
            status=response.status_code,
            user_id=user_id,
            ip=client_ip,
            duration_ms=round(duration_ms, 2),
            timestamp=datetime.now(UTC).isoformat(),
        )

    @staticmethod
    async def persist_audit(
        session: Any,
        user_id: str | None,
        action: str,
        resource: str,
        details: dict | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Persist an audit log entry to the database."""
        from .models import AuditLog
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            details=details or {},
            ip_address=ip_address,
        )
        session.add(entry)
        await session.flush()
