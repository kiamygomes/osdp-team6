"""OAuth helper functions for Jira Cloud (Auth0) flows."""

from __future__ import annotations

from urllib.parse import urlencode

import httpx

from .config import settings
from .storage import Token, get_tokens, is_expired, update_access, upsert_tokens

AUTH_BASE = "https://auth.atlassian.com"
TOKEN_URL = f"{AUTH_BASE}/oauth/token"
SCOPE = "read:jira-user read:jira-work write:jira-work offline_access"
AUDIENCE = "api.atlassian.com"


def build_authorize_url(state: str) -> str:
    """Build the browser URL to start OAuth authorization."""
    params = {
        "audience": AUDIENCE,
        "client_id": settings.oauth_client_id,
        "scope": SCOPE,
        "redirect_uri": settings.oauth_redirect_uri,
        "response_type": "code",
        "prompt": "consent",
        "state": state,
    }
    return f"{AUTH_BASE}/authorize?{urlencode(params)}"


async def exchange_code_for_tokens(user_id: str, code: str) -> tuple[str, str, int]:
    """Exchange authorization code for access/refresh tokens."""
    data = {
        "grant_type": "authorization_code",
        "client_id": settings.oauth_client_id,
        "client_secret": settings.oauth_client_secret,
        "code": code,
        "redirect_uri": settings.oauth_redirect_uri,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(TOKEN_URL, json=data)
        r.raise_for_status()
        payload = r.json()
    access = payload["access_token"]
    refresh = payload["refresh_token"]
    expires_in = int(payload.get("expires_in", 3600))
    upsert_tokens(user_id, access, refresh, expires_in)
    return access, refresh, expires_in


async def refresh_access_token(user_id: str) -> str:
    """Use refresh token to obtain a new access token."""
    tok: Token | None = get_tokens(user_id)
    if not tok:
        msg = "No tokens for user; authenticate first (/auth/login)."
        raise RuntimeError(msg)
    data = {
        "grant_type": "refresh_token",
        "client_id": settings.oauth_client_id,
        "client_secret": settings.oauth_client_secret,
        "refresh_token": tok.refresh_token,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(TOKEN_URL, json=data)
        r.raise_for_status()
        payload = r.json()
    access = payload["access_token"]
    expires_in = int(payload.get("expires_in", 3600))
    update_access(user_id, access, expires_in)
    return access


async def get_valid_access_token(user_id: str) -> str:
    """Return a non-expired access token, refreshing if needed."""
    # Allow test users to bypass OAuth
    if user_id.startswith("test-"):
        return "test-access-token"

    tok = get_tokens(user_id)
    if not tok:
        msg = "User has no token; complete OAuth."
        raise RuntimeError(msg)
    if is_expired(tok):
        return await refresh_access_token(user_id)
    return tok.access_token
