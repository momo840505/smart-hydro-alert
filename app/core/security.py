"""
Shared admin API key check for device-mutating endpoints.

docs/security_controls.md already documents the requirement this file
implements:

    - Require authentication for dashboard and API access.
    - Disable public write endpoints in production unless protected.

Before this fix, nothing in the codebase actually enforced that -- there
was an unused jwt_secret setting but no dependency checking it anywhere.
This module adds a minimal, real enforcement: a single shared API key
(sent as the `X-API-Key` header) required on the routes that change
device state (register / simulate / reset). Read-only endpoints
(list devices, live status, history, alerts, websocket) stay open, since
locking those down too would need a full login flow this single-operator
project doesn't have a use case for yet.

Why an API key instead of the JWT settings that used to be here: JWT is
built for "many users, each with their own identity, tokens that expire
and get refreshed." This project has one operator and one backend --
there is nothing for a JWT's extra machinery (issuing, expiry, refresh)
to buy you. A single shared secret compared with a timing-safe check is
the honest, minimal-complexity fit. If this project grows into a
multi-user product, THAT is the point to introduce real JWT/OAuth login.
"""

import secrets

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import Settings, get_settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_admin_api_key(
    provided_key: str | None = Security(_api_key_header),
    settings: Settings = Depends(get_settings),
) -> None:
    """FastAPI dependency: raise 401/503 unless a valid admin key is sent.

    In development with no key configured, the check is skipped so local
    demos and the test suite keep working with zero extra setup. In every
    other environment, an unconfigured key is treated as a server
    misconfiguration (503) rather than silently running unprotected --
    the previous bug was exactly this kind of "looks configured, isn't
    actually enforced" gap, so this fails loudly on purpose.
    """
    if not settings.admin_api_key:
        if settings.app_env == "development":
            return
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ADMIN_API_KEY is not configured for this environment.",
        )

    if provided_key is None or not secrets.compare_digest(
        provided_key, settings.admin_api_key
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header.",
        )
