"""
Token encryption/decryption helpers + MSAL flow helpers.
"""
from __future__ import annotations
import base64
from datetime import datetime, timezone

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
import msal
import requests


# ── Fernet helpers ────────────────────────────────────────────────────────────

def _get_fernet() -> Fernet:
    key = settings.FERNET_KEY
    if not key:
        raise RuntimeError("FERNET_KEY is not set in settings / .env")
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def encrypt_token(token: str) -> bytes:
    """Encrypt a plain-text token string → bytes."""
    return _get_fernet().encrypt(token.encode())


def decrypt_token(data: bytes | memoryview) -> str:
    """Decrypt bytes back to a plain-text token string."""
    if isinstance(data, memoryview):
        data = bytes(data)
    return _get_fernet().decrypt(data).decode()


# ── MSAL helpers ──────────────────────────────────────────────────────────────

def build_msal_app() -> msal.ConfidentialClientApplication:
    return msal.ConfidentialClientApplication(
        client_id=settings.MS_CLIENT_ID,
        client_credential=settings.MS_CLIENT_SECRET,
        authority=settings.MS_AUTHORITY,
    )


def get_auth_url(state: str) -> str:
    app = build_msal_app()
    return app.get_authorization_request_url(
        scopes=settings.MS_SCOPES,
        state=state,
        redirect_uri=settings.MS_REDIRECT_URI,
    )


def exchange_code_for_tokens(code: str) -> dict:
    """Exchange authorization code for access + refresh tokens."""
    app = build_msal_app()
    result = app.acquire_token_by_authorization_code(
        code=code,
        scopes=settings.MS_SCOPES,
        redirect_uri=settings.MS_REDIRECT_URI,
    )
    return result


def get_valid_access_token(integration) -> str | None:
    """
    Return a valid access token for the given UserIntegration.
    Refreshes automatically if expired.
    """
    if not integration.access_token_enc:
        return None

    now = datetime.now(timezone.utc)
    if integration.token_expiry and now < integration.token_expiry:
        return decrypt_token(integration.access_token_enc)

    # Token expired — try refresh
    if not integration.refresh_token_enc:
        return None

    refresh_token = decrypt_token(integration.refresh_token_enc)
    app = build_msal_app()
    result = app.acquire_token_by_refresh_token(
        refresh_token=refresh_token,
        scopes=settings.MS_SCOPES,
    )
    if "access_token" not in result:
        return None

    # Persist refreshed tokens
    integration.access_token_enc = encrypt_token(result["access_token"])
    if "refresh_token" in result:
        integration.refresh_token_enc = encrypt_token(result["refresh_token"])
    expiry_secs = result.get("expires_in", 3600)
    integration.token_expiry = datetime.fromtimestamp(
        datetime.now(timezone.utc).timestamp() + expiry_secs,
        tz=timezone.utc,
    )
    integration.save()
    return result["access_token"]


def graph_get(access_token: str, endpoint: str, params: dict | None = None) -> dict:
    """Make an authenticated GET request to Microsoft Graph API."""
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    url = f"https://graph.microsoft.com/v1.0{endpoint}"
    resp = requests.get(url, headers=headers, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def graph_post(access_token: str, endpoint: str, json_body: dict) -> dict:
    """Make an authenticated POST request to Microsoft Graph API."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    url = f"https://graph.microsoft.com/v1.0{endpoint}"
    resp = requests.post(url, headers=headers, json=json_body, timeout=15)
    resp.raise_for_status()
    return resp.json() if resp.content else {}
