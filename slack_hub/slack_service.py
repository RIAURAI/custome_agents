"""
Slack API service layer — fetches channels, messages, sends replies.
"""
from __future__ import annotations

from integrations.slack_utils import slack_api_get, slack_api_post


def fetch_channels(token: str) -> list[dict]:
    """Fetch all channels the bot/user has access to."""
    data = slack_api_get(token, "conversations.list", {
        "types": "public_channel,private_channel",
        "exclude_archived": "true",
        "limit": "200",
    })
    return data.get("channels", [])


def join_channel(token: str, channel_id: str) -> None:
    """Join a channel so the bot can read messages."""
    try:
        slack_api_post(token, "conversations.join", {"channel": channel_id})
    except Exception:
        pass  # Already in channel or unable to join


def fetch_messages(token: str, channel_id: str, limit: int = 30) -> list[dict]:
    """Fetch recent messages from a channel (auto-joins if needed)."""
    try:
        data = slack_api_get(token, "conversations.history", {
            "channel": channel_id,
            "limit": str(limit),
        })
    except Exception as e:
        if "not_in_channel" in str(e):
            join_channel(token, channel_id)
            data = slack_api_get(token, "conversations.history", {
                "channel": channel_id,
                "limit": str(limit),
            })
        else:
            raise
    return data.get("messages", [])


def fetch_thread_replies(token: str, channel_id: str, thread_ts: str) -> list[dict]:
    """Fetch replies in a thread."""
    data = slack_api_get(token, "conversations.replies", {
        "channel": channel_id,
        "ts": thread_ts,
    })
    return data.get("messages", [])


def send_message(token: str, channel_id: str, text: str, thread_ts: str = "") -> dict:
    """Send a message to a channel (optionally as a thread reply)."""
    payload = {
        "channel": channel_id,
        "text": text,
    }
    if thread_ts:
        payload["thread_ts"] = thread_ts
    return slack_api_post(token, "chat.postMessage", payload)


def get_user_info(token: str, user_id: str) -> dict:
    """Get Slack user profile info."""
    data = slack_api_get(token, "users.info", {"user": user_id})
    return data.get("user", {})


def get_user_name(token: str, user_id: str) -> str:
    """Get display name for a Slack user ID."""
    try:
        user = get_user_info(token, user_id)
        profile = user.get("profile", {})
        return profile.get("display_name") or profile.get("real_name") or user.get("name", user_id)
    except Exception:
        return user_id
