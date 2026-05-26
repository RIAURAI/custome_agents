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

def build_msal_app(
    client_id: str | None = None,
    client_secret: str | None = None,
    tenant_id: str | None = None,
) -> msal.ConfidentialClientApplication:
    """Build MSAL app using per-company creds, falling back to settings."""
    return msal.ConfidentialClientApplication(
        client_id=client_id or settings.MS_CLIENT_ID,
        client_credential=client_secret or settings.MS_CLIENT_SECRET,
        authority=f"https://login.microsoftonline.com/{tenant_id or settings.MS_TENANT_ID}",
    )


def _get_company_ms_creds(integration) -> tuple[str, str, str]:
    """Extract decrypted client_id, client_secret, and tenant_id from CompanyIntegration."""
    if not integration.ms_client_id_enc or not integration.ms_client_secret_enc:
        raise ValueError("Microsoft Azure App credentials not configured for this company.")
    client_id = decrypt_token(integration.ms_client_id_enc)
    client_secret = decrypt_token(integration.ms_client_secret_enc)
    tenant_id = integration.ms_tenant_id or "common"
    return client_id, client_secret, tenant_id


def get_scopes_for_integration(integration=None) -> list[str]:
    """Build OAuth scopes from a CompanyIntegration's enabled features, or defaults."""
    if integration is not None:
        return integration.get_ms_scopes()
    # Fallback: base + default features
    scopes = list(settings.MS_BASE_SCOPES)
    for feat in settings.MS_DEFAULT_FEATURES:
        feat_info = settings.MS_FEATURE_SCOPES.get(feat)
        if feat_info:
            scopes.extend(feat_info["scopes"])
    return list(dict.fromkeys(scopes))


def get_auth_url(state: str, client_id: str | None = None, client_secret: str | None = None, tenant_id: str | None = None, integration=None) -> str:
    app = build_msal_app(client_id, client_secret, tenant_id)
    scopes = get_scopes_for_integration(integration)
    return app.get_authorization_request_url(
        scopes=scopes,
        state=state,
        redirect_uri=settings.MS_REDIRECT_URI,
    )


def exchange_code_for_tokens(code: str, client_id: str | None = None, client_secret: str | None = None, tenant_id: str | None = None, integration=None) -> dict:
    """Exchange authorization code for access + refresh tokens."""
    app = build_msal_app(client_id, client_secret, tenant_id)
    scopes = get_scopes_for_integration(integration)
    result = app.acquire_token_by_authorization_code(
        code=code,
        scopes=scopes,
        redirect_uri=settings.MS_REDIRECT_URI,
    )
    return result


def get_valid_access_token(integration) -> str | None:
    """
    Return a valid access token for the given CompanyIntegration.
    Uses per-company credentials if available, falls back to global settings.
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

    # Use per-company creds if available
    try:
        client_id, client_secret, tenant_id = _get_company_ms_creds(integration)
    except ValueError:
        client_id, client_secret, tenant_id = None, None, None

    app = build_msal_app(client_id, client_secret, tenant_id)
    scopes = get_scopes_for_integration(integration)
    result = app.acquire_token_by_refresh_token(
        refresh_token=refresh_token,
        scopes=scopes,
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


import logging as _logging

_logger = _logging.getLogger(__name__)


def friendly_graph_error(exc: Exception) -> str:
    """Convert a Graph API exception into a safe, user-friendly message."""
    raw = str(exc)
    _logger.error("Microsoft Graph API error: %s", raw)

    if "401" in raw:
        return "Microsoft session expired. Please reconnect your account."
    if "403" in raw:
        return ("Access denied by Microsoft. Your Azure App may be missing the "
                "required API permissions. Check API permissions in Azure portal "
                "and grant admin consent.")
    if "404" in raw:
        return "The requested item was not found. It may have been deleted."
    if "429" in raw:
        return "Too many requests. Please wait a moment and try again."
    if "500" in raw or "502" in raw or "503" in raw:
        return "Microsoft services are temporarily unavailable. Please try again later."
    return "Something went wrong while contacting Microsoft. Please try again."


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


def graph_patch(access_token: str, endpoint: str, json_body: dict) -> dict:
    """Make an authenticated PATCH request to Microsoft Graph API."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    url = f"https://graph.microsoft.com/v1.0{endpoint}"
    resp = requests.patch(url, headers=headers, json=json_body, timeout=15)
    resp.raise_for_status()
    return resp.json() if resp.content else {}


# ── Company integration helpers ───────────────────────────────────────────────

def get_company_integration(request, service: str):
    """
    Return the CompanyIntegration for the current company + service, or None.
    """
    from integrations.models import CompanyIntegration
    company = getattr(request, "company", None)
    if not company:
        return None
    return CompanyIntegration.objects.filter(company=company, service=service).first()


def get_company_ms_token(request) -> str | None:
    """Get a valid Microsoft access token for the current company."""
    integration = get_company_integration(request, "microsoft")
    if not integration:
        return None
    return get_valid_access_token(integration)


def get_company_slack_token(request) -> str | None:
    """Get a valid Slack token for the current company."""
    integration = get_company_integration(request, "slack")
    if not integration:
        return None
    if not integration.access_token_enc:
        return None
    return decrypt_token(integration.access_token_enc)
