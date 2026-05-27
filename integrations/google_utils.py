"""
Google Workspace OAuth 2.0 helpers — authorization URL, token exchange, API calls.
Credentials are stored per-company in the database (similar to Calendly pattern).
"""
from __future__ import annotations

from urllib.parse import urlencode

from django.conf import settings
import requests

from .utils import decrypt_token, encrypt_token


# ── URLs (constant, same for all companies) ───────────────────────────────────
GOOGLE_AUTH_BASE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_REDIRECT_URI = getattr(
    settings, "GOOGLE_REDIRECT_URI",
    "http://localhost:8000/integrations/google/callback/",
)

# Scopes for full Google Workspace (Gmail · Calendar · Meet · Drive · Docs · Sheets · Forms)
GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    # Gmail — read, send, modify labels / drafts
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    # Calendar
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
    # Google Meet
    "https://www.googleapis.com/auth/meetings.space.created",
    "https://www.googleapis.com/auth/meetings.space.readonly",
    # Drive — full access to all files (images, PDFs, videos, etc.)
    "https://www.googleapis.com/auth/drive",
    # Docs
    "https://www.googleapis.com/auth/documents",
    # Sheets
    "https://www.googleapis.com/auth/spreadsheets",
    # Forms — create/manage forms + read responses
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
]


def _get_company_google_creds(integration) -> tuple[str, str]:
    """Extract decrypted client_id and client_secret from a CompanyIntegration."""
    if not integration.google_client_id_enc or not integration.google_client_secret_enc:
        raise ValueError("Google OAuth credentials not configured for this company.")
    client_id = decrypt_token(integration.google_client_id_enc)
    client_secret = decrypt_token(integration.google_client_secret_enc)
    return client_id, client_secret


def get_google_auth_url(state: str, client_id: str) -> str:
    """Build the Google OAuth authorization URL using the company's client_id."""
    params = {
        "client_id": client_id,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{GOOGLE_AUTH_BASE_URL}?{urlencode(params)}"


def exchange_google_code(code: str, client_id: str, client_secret: str) -> dict:
    """Exchange authorization code for access + refresh tokens."""
    resp = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=15,
    )
    return resp.json()


def refresh_google_token(refresh_token: str, client_id: str, client_secret: str) -> dict:
    """Refresh an expired access token using the refresh token."""
    resp = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=15,
    )
    return resp.json()


def get_google_user_info(access_token: str) -> dict:
    """Fetch the authenticated user's profile information."""
    resp = requests.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def google_api_get(access_token: str, url: str, params: dict | None = None) -> dict:
    """Make an authenticated GET request to a Google API endpoint."""
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    resp = requests.get(url, headers=headers, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def google_api_post(access_token: str, url: str, json_body: dict) -> dict:
    """Make an authenticated POST request to a Google API endpoint."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    resp = requests.post(url, headers=headers, json=json_body, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_valid_google_access_token(integration) -> str | None:
    """
    Return a valid access token for a Google CompanyIntegration.
    Refreshes automatically if expired.
    """
    from datetime import datetime, timezone

    if not integration.access_token_enc:
        return None

    now = datetime.now(timezone.utc)
    if integration.token_expiry and now < integration.token_expiry:
        return decrypt_token(integration.access_token_enc)

    # Token expired — try refresh
    if not integration.refresh_token_enc:
        return None

    refresh_token = decrypt_token(integration.refresh_token_enc)

    try:
        client_id, client_secret = _get_company_google_creds(integration)
    except ValueError:
        return None

    result = refresh_google_token(refresh_token, client_id, client_secret)
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
    integration.status = "active"
    integration.save()
    return result["access_token"]


# ── Gmail API Helpers ─────────────────────────────────────────────────────────

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


def gmail_list_messages(access_token: str, max_results: int = 25, query: str = "") -> list[dict]:
    """Fetch a list of messages from Gmail inbox."""
    params = {"maxResults": max_results}
    if query:
        params["q"] = query
    resp = requests.get(
        f"{GMAIL_API_BASE}/messages",
        headers={"Authorization": f"Bearer {access_token}"},
        params=params,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    message_ids = data.get("messages", [])

    # Fetch metadata for each message
    messages = []
    for msg_ref in message_ids[:max_results]:
        msg = gmail_get_message(access_token, msg_ref["id"], fmt="metadata")
        if msg:
            messages.append(msg)
    return messages


def gmail_get_message(access_token: str, message_id: str, fmt: str = "full") -> dict | None:
    """Fetch a single message by ID. fmt: 'full', 'metadata', 'minimal'."""
    resp = requests.get(
        f"{GMAIL_API_BASE}/messages/{message_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"format": fmt},
        timeout=15,
    )
    if resp.status_code != 200:
        return None
    return resp.json()


def gmail_send_message(access_token: str, raw_message: str) -> dict:
    """Send an email. raw_message is base64url-encoded RFC 2822 message."""
    resp = requests.post(
        f"{GMAIL_API_BASE}/messages/send",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={"raw": raw_message},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def gmail_modify_message(access_token: str, message_id: str, remove_labels: list = None, add_labels: list = None) -> dict:
    """Modify labels on a message (e.g., mark as read by removing UNREAD)."""
    body = {}
    if remove_labels:
        body["removeLabelIds"] = remove_labels
    if add_labels:
        body["addLabelIds"] = add_labels
    resp = requests.post(
        f"{GMAIL_API_BASE}/messages/{message_id}/modify",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


# ── Google Calendar API Helpers ───────────────────────────────────────────────

CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"


def calendar_list_events(access_token: str, days: int = 7, max_results: int = 20) -> list[dict]:
    """Fetch upcoming calendar events for the next N days."""
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)
    time_max = now + timedelta(days=days)

    resp = requests.get(
        f"{CALENDAR_API_BASE}/calendars/primary/events",
        headers={"Authorization": f"Bearer {access_token}"},
        params={
            "timeMin": now.isoformat(),
            "timeMax": time_max.isoformat(),
            "maxResults": max_results,
            "singleEvents": "true",
            "orderBy": "startTime",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("items", [])


# ── Gmail extras ─────────────────────────────────────────────────────────────

def gmail_list_labels(access_token: str) -> list[dict]:
    """Fetch all Gmail labels for the authenticated user."""
    resp = requests.get(
        f"{GMAIL_API_BASE}/labels",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("labels", [])


def gmail_get_unread_count(access_token: str) -> int:
    """Return total unread message count in the inbox."""
    resp = requests.get(
        f"{GMAIL_API_BASE}/labels/INBOX",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("messagesUnread", 0)


def gmail_create_draft(access_token: str, raw_message: str) -> dict:
    """Save an email as a Gmail draft. raw_message is base64url-encoded RFC 2822."""
    resp = requests.post(
        f"{GMAIL_API_BASE}/drafts",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={"message": {"raw": raw_message}},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


# ── Google Calendar extras ────────────────────────────────────────────────────

def calendar_create_event(access_token: str, event_body: dict) -> dict:
    """Create a new event in the primary calendar."""
    resp = requests.post(
        f"{CALENDAR_API_BASE}/calendars/primary/events",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json=event_body,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def calendar_delete_event(access_token: str, event_id: str) -> None:
    """Delete (cancel) an event from the primary calendar."""
    resp = requests.delete(
        f"{CALENDAR_API_BASE}/calendars/primary/events/{event_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    resp.raise_for_status()


def calendar_get_event(access_token: str, event_id: str) -> dict:
    """Fetch a single calendar event by ID."""
    resp = requests.get(
        f"{CALENDAR_API_BASE}/calendars/primary/events/{event_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


# ── Google Meet API Helpers ───────────────────────────────────────────────────

MEET_API_BASE = "https://meet.googleapis.com/v2"


def meet_create_space(access_token: str) -> dict:
    """Create a new Google Meet meeting space."""
    resp = requests.post(
        f"{MEET_API_BASE}/spaces",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()
