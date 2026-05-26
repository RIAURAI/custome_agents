"""
Calendly OAuth 2.0 helpers — authorization URL, token exchange, API calls.
Credentials are stored per-company in the database (not .env).
"""
from __future__ import annotations

from urllib.parse import urlencode

from django.conf import settings
import requests

from .utils import decrypt_token, encrypt_token


# ── URLs (constant, same for all companies) ───────────────────────────────────
CALENDLY_AUTH_BASE_URL = getattr(settings, "CALENDLY_AUTH_BASE_URL", "https://auth.calendly.com/oauth/authorize")
CALENDLY_TOKEN_URL = getattr(settings, "CALENDLY_TOKEN_URL", "https://auth.calendly.com/oauth/token")
CALENDLY_API_BASE_URL = getattr(settings, "CALENDLY_API_BASE_URL", "https://api.calendly.com")
CALENDLY_REDIRECT_URI = getattr(settings, "CALENDLY_REDIRECT_URI", "http://localhost:8000/integrations/calendly/callback/")


def _get_company_calendly_creds(integration) -> tuple[str, str]:
    """Extract decrypted client_id and client_secret from a CompanyIntegration."""
    if not integration.calendly_client_id_enc or not integration.calendly_client_secret_enc:
        raise ValueError("Calendly OAuth credentials not configured for this company.")
    client_id = decrypt_token(integration.calendly_client_id_enc)
    client_secret = decrypt_token(integration.calendly_client_secret_enc)
    return client_id, client_secret


def get_calendly_auth_url(state: str, client_id: str) -> str:
    """Build the Calendly OAuth authorization URL using the company's client_id."""
    params = {
        "client_id": client_id,
        "redirect_uri": CALENDLY_REDIRECT_URI,
        "response_type": "code",
        "state": state,
    }
    return f"{CALENDLY_AUTH_BASE_URL}?{urlencode(params)}"


def exchange_calendly_code(code: str, client_id: str, client_secret: str) -> dict:
    """Exchange authorization code for access + refresh tokens."""
    resp = requests.post(
        CALENDLY_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": CALENDLY_REDIRECT_URI,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    return resp.json()


def refresh_calendly_token(refresh_token: str, client_id: str, client_secret: str) -> dict:
    """Use a refresh token to get a new access token."""
    resp = requests.post(
        CALENDLY_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    return resp.json()


def get_valid_calendly_token(integration) -> str | None:
    """Return a valid Calendly access token, refreshing if expired using per-company creds."""
    from datetime import datetime, timezone as tz

    if not integration.access_token_enc:
        return None

    now = datetime.now(tz.utc)
    if integration.token_expiry and now < integration.token_expiry:
        return decrypt_token(integration.access_token_enc)

    # Token expired — try refresh
    if not integration.refresh_token_enc:
        return None

    try:
        client_id, client_secret = _get_company_calendly_creds(integration)
    except ValueError:
        return None

    refresh_tok = decrypt_token(integration.refresh_token_enc)
    result = refresh_calendly_token(refresh_tok, client_id, client_secret)

    if "access_token" not in result:
        integration.status = "expired"
        integration.save()
        return None

    # Persist refreshed tokens
    integration.access_token_enc = encrypt_token(result["access_token"])
    if "refresh_token" in result:
        integration.refresh_token_enc = encrypt_token(result["refresh_token"])
    expiry_secs = result.get("expires_in", 7200)
    integration.token_expiry = datetime.fromtimestamp(
        now.timestamp() + expiry_secs, tz=tz.utc
    )
    integration.status = "active"
    integration.save()
    return result["access_token"]


def calendly_api_get(access_token: str, endpoint: str, params: dict | None = None) -> dict:
    """Authenticated GET request to Calendly API."""
    url = f"{CALENDLY_API_BASE_URL}{endpoint}"
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        params=params,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def calendly_api_post(access_token: str, endpoint: str, payload: dict) -> dict:
    """Authenticated POST request to Calendly API."""
    url = f"{CALENDLY_API_BASE_URL}{endpoint}"
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()
