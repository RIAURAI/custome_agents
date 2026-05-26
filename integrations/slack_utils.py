"""
Slack OAuth helpers and API wrapper functions.
"""
from __future__ import annotations

from urllib.parse import urlencode

from django.conf import settings
import requests

from .utils import encrypt_token, decrypt_token


# ── OAuth helpers ─────────────────────────────────────────────────────────────

def get_slack_auth_url(state: str) -> str:
    """Build the Slack OAuth authorization URL."""
    params = {
        "client_id": settings.SLACK_CLIENT_ID,
        "scope": settings.SLACK_SCOPES,
        "redirect_uri": settings.SLACK_REDIRECT_URI,
        "state": state,
    }
    return f"https://slack.com/oauth/v2/authorize?{urlencode(params)}"


def exchange_slack_code(code: str) -> dict:
    """Exchange authorization code for access token."""
    resp = requests.post(
        "https://slack.com/api/oauth.v2.access",
        data={
            "client_id": settings.SLACK_CLIENT_ID,
            "client_secret": settings.SLACK_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.SLACK_REDIRECT_URI,
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


# ── Slack API wrappers ────────────────────────────────────────────────────────

def slack_api_get(token: str, method: str, params: dict | None = None) -> dict:
    """Call a Slack Web API method (GET)."""
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://slack.com/api/{method}"
    resp = requests.get(url, headers=headers, params=params or {}, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise Exception(f"Slack API error: {data.get('error', 'unknown')}")
    return data


def slack_api_post(token: str, method: str, json_body: dict) -> dict:
    """Call a Slack Web API method (POST with JSON)."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    url = f"https://slack.com/api/{method}"
    resp = requests.post(url, headers=headers, json=json_body, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise Exception(f"Slack API error: {data.get('error', 'unknown')}")
    return data


def get_valid_slack_token(integration) -> str | None:
    """
    Return the decrypted Slack bot access token for the given UserIntegration.
    Slack bot tokens don't expire, so no refresh logic needed.
    """
    if not integration.access_token_enc:
        return None
    return decrypt_token(integration.access_token_enc)


def get_valid_slack_app_token(integration) -> str | None:
    """Return the decrypted Slack app-level token (xapp-…) if stored."""
    if not integration.slack_app_token_enc:
        return None
    return decrypt_token(integration.slack_app_token_enc)


def get_valid_slack_signing_secret(integration) -> str | None:
    """Return the decrypted Slack signing secret for webhook verification."""
    if not integration.slack_signing_secret_enc:
        return None
    return decrypt_token(integration.slack_signing_secret_enc)


def get_valid_slack_user_token(integration) -> str | None:
    """Return the decrypted Slack user OAuth token (xoxp-…) for posting as the user."""
    if not getattr(integration, "slack_user_token_enc", None):
        return None
    return decrypt_token(integration.slack_user_token_enc)
