"""
Platform API abstraction — handles sending messages and marking as read
for each social media platform (WhatsApp, LinkedIn, Facebook, Instagram, Twitter).

Each function dispatches to the correct platform's API.
Requires valid tokens stored in the SocialMediaAccount.
"""
import logging

import requests

from integrations.utils import decrypt_token

logger = logging.getLogger(__name__)

# ── Base URLs ─────────────────────────────────────────────────────────────────
WHATSAPP_API_BASE = "https://graph.facebook.com/v18.0"
FACEBOOK_API_BASE = "https://graph.facebook.com/v18.0"
LINKEDIN_API_BASE = "https://api.linkedin.com/v2"
TWITTER_API_BASE = "https://api.twitter.com/2"


def _get_token(account) -> str:
    """Decrypt and return the access token for an account."""
    if not account.access_token_enc:
        raise ValueError(f"No access token for {account}")
    return decrypt_token(account.access_token_enc)


# ── Send Message ──────────────────────────────────────────────────────────────


def send_message_to_platform(account, recipient_id: str, text: str) -> dict:
    """
    Send a message to a recipient on the given platform.
    Returns the platform API response or raises an exception.
    """
    platform = account.platform

    if platform == "whatsapp":
        return _send_whatsapp_message(account, recipient_id, text)
    elif platform == "facebook":
        return _send_facebook_message(account, recipient_id, text)
    elif platform == "instagram":
        return _send_instagram_message(account, recipient_id, text)
    elif platform == "linkedin":
        return _send_linkedin_message(account, recipient_id, text)
    elif platform == "twitter":
        return _send_twitter_dm(account, recipient_id, text)
    else:
        raise ValueError(f"Unsupported platform: {platform}")


def _send_whatsapp_message(account, recipient_phone: str, text: str) -> dict:
    """Send a WhatsApp message via the Cloud API."""
    token = _get_token(account)
    phone_number_id = account.phone_number_id

    if not phone_number_id:
        raise ValueError("WhatsApp phone_number_id not configured.")

    url = f"{WHATSAPP_API_BASE}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "text",
        "text": {"body": text},
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    logger.info(f"[WhatsApp] Message sent to {recipient_phone}")
    return resp.json()


def _send_facebook_message(account, recipient_id: str, text: str) -> dict:
    """Send a Facebook Messenger message via Page API."""
    token = _get_token(account)
    page_id = account.page_id

    if not page_id:
        raise ValueError("Facebook page_id not configured.")

    url = f"{FACEBOOK_API_BASE}/{page_id}/messages"
    headers = {"Content-Type": "application/json"}
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
        "access_token": token,
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    logger.info(f"[Facebook] Message sent to {recipient_id}")
    return resp.json()


def _send_instagram_message(account, recipient_id: str, text: str) -> dict:
    """Send an Instagram DM via the Messenger API."""
    token = _get_token(account)
    page_id = account.page_id

    if not page_id:
        raise ValueError("Instagram page_id not configured.")

    url = f"{FACEBOOK_API_BASE}/{page_id}/messages"
    headers = {"Content-Type": "application/json"}
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
        "access_token": token,
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    logger.info(f"[Instagram] Message sent to {recipient_id}")
    return resp.json()


def _send_linkedin_message(account, recipient_urn: str, text: str) -> dict:
    """Send a LinkedIn message (requires Messaging API access)."""
    token = _get_token(account)

    url = f"{LINKEDIN_API_BASE}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    payload = {
        "recipients": [recipient_urn],
        "subject": "Message",
        "body": text,
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    logger.info(f"[LinkedIn] Message sent to {recipient_urn}")
    return resp.json()


def _send_twitter_dm(account, recipient_id: str, text: str) -> dict:
    """Send a Twitter/X Direct Message."""
    token = _get_token(account)

    url = f"{TWITTER_API_BASE}/dm_conversations/with/{recipient_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {"text": text}
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    logger.info(f"[Twitter] DM sent to {recipient_id}")
    return resp.json()


# ── Mark as Read ──────────────────────────────────────────────────────────────


def mark_as_read_on_platform(account, message_id: str) -> None:
    """Mark a message as read on the platform (where supported)."""
    platform = account.platform

    if platform == "whatsapp":
        _mark_read_whatsapp(account, message_id)
    elif platform in ("facebook", "instagram"):
        _mark_read_facebook(account, message_id)
    # LinkedIn and Twitter don't have explicit mark-as-read APIs


def _mark_read_whatsapp(account, message_id: str) -> None:
    """Mark WhatsApp message as read."""
    if not message_id:
        return
    token = _get_token(account)
    phone_number_id = account.phone_number_id

    if not phone_number_id:
        return

    url = f"{WHATSAPP_API_BASE}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"[WhatsApp] Mark as read failed: {e}")


def _mark_read_facebook(account, message_id: str) -> None:
    """Mark Facebook/Instagram message as read (sender action)."""
    # Facebook uses Page-scoped IDs; mark read via the Send API
    # This is a no-op for now — FB auto-marks on read receipt
    pass
