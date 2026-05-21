"""
Slack Socket Mode Bot — listens to all incoming messages and auto-replies using AI.
Method: WebSocket (Socket Mode) — no ngrok, no public URL needed.
Run with: python manage.py run_slack_bot
"""
import logging
import re
from datetime import datetime, timezone

from django.conf import settings
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from integrations.models import CompanyIntegration
from integrations.slack_utils import get_valid_slack_token
from .models import SlackMessage, AutoReplyRule
from .ai_service import classify_message, generate_reply

logger = logging.getLogger(__name__)


def _get_integration_and_token():
    """Return (integration, token) for the first connected Slack company."""
    integration = CompanyIntegration.objects.filter(service="slack", status="active").first()
    if not integration:
        return None, None
    token = get_valid_slack_token(integration)
    return integration, token


def _get_sender_name(client, user_id: str) -> str:
    """Resolve Slack user_id to display name."""
    try:
        info = client.users_info(user=user_id)
        profile = info["user"]["profile"]
        return profile.get("display_name") or profile.get("real_name") or user_id
    except Exception:
        return user_id


def _get_channel_name(client, channel_id: str) -> str:
    """Resolve channel_id to channel name."""
    try:
        info = client.conversations_info(channel=channel_id)
        ch = info["channel"]
        return ch.get("name") or channel_id
    except Exception:
        return channel_id


def _process_message(event: dict, say, client):
    """
    Core logic: receive message → AI analyze → AI reply → save to DB.
    Works for: public channels, private channels, DMs.
    """
    # ── Guard: skip bot messages and system events ──────────────────────────
    if event.get("bot_id") or event.get("subtype"):
        return

    channel_id = event.get("channel", "")
    user_id = event.get("user", "")
    text = event.get("text", "").strip()
    ts = event.get("ts", "")
    thread_ts = event.get("thread_ts", "")
    channel_type = event.get("channel_type", "")  # "channel", "group", "im"
    is_dm = channel_type == "im"

    if not text or not channel_id or not user_id:
        return

    logger.info(f"📨 [{channel_type or 'channel'}] {user_id}: {text[:60]}")

    # ── Find connected user ─────────────────────────────────────────────────
    integration, token = _get_integration_and_token()
    if not integration or not token:
        logger.warning("No Slack integration found.")
        return

    # ── Check auto-reply rule ───────────────────────────────────────────────
    # First: channel-specific rule
    rule = AutoReplyRule.objects.filter(
        company=integration.company, channel_id=channel_id, is_enabled=True
    ).first()
    # Fallback: wildcard rule for all channels/DMs
    if not rule:
        rule = AutoReplyRule.objects.filter(
            company=integration.company, channel_id="*", is_enabled=True
        ).first()
    if not rule:
        return  # No rule, skip silently

    # ── Keyword filter ──────────────────────────────────────────────────────
    if rule.keywords:
        kws = [k.strip().lower() for k in rule.keywords.split(",") if k.strip()]
        if not any(kw in text.lower() for kw in kws):
            return

    # ── Resolve names ───────────────────────────────────────────────────────
    sender_name = _get_sender_name(client, user_id)
    if is_dm:
        channel_display = f"DM with {sender_name}"
    else:
        channel_display = _get_channel_name(client, channel_id)

    # ── AI: classify message ────────────────────────────────────────────────
    try:
        classification = classify_message(text)
        logger.info(f"🧠 {classification['classification'].upper()} — {classification['summary']}")
    except Exception as e:
        logger.error(f"AI classify error: {e}")
        classification = {"classification": "general", "summary": text[:100]}

    # ── AI: generate reply ──────────────────────────────────────────────────
    try:
        reply_text = generate_reply(text, custom_instructions=rule.custom_instructions)
        logger.info(f"💬 Reply: {reply_text[:80]}...")
    except Exception as e:
        logger.error(f"AI reply error: {e}")
        return

    # ── Save to database ────────────────────────────────────────────────────
    msg, _ = SlackMessage.objects.get_or_create(
        company=integration.company,
        channel_id=channel_id,
        timestamp=ts,
        defaults={
            "channel_name": channel_display,
            "sender_id": user_id,
            "sender_name": sender_name,
            "text": text,
            "thread_ts": thread_ts,
            "ai_classification": classification["classification"],
            "ai_summary": classification["summary"],
            "ai_reply": reply_text,
        },
    )

    # ── Send reply to Slack ─────────────────────────────────────────────────
    if rule.auto_send:
        try:
            if is_dm:
                # DMs: reply in the same conversation (no thread)
                say(text=reply_text)
            else:
                # Channels/groups: reply in thread to keep it tidy
                say(text=reply_text, thread_ts=ts)

            msg.is_auto_replied = True
            msg.reply_sent_at = datetime.now(timezone.utc)
            msg.save()
            logger.info(f"✅ Sent auto-reply in {channel_display}")
        except Exception as e:
            logger.error(f"Send reply failed: {e}")
            msg.save()
    else:
        # Draft mode — save reply but don't send it
        msg.save()
        logger.info(f"📝 Draft saved for {channel_display}")


def create_slack_app():
    """Build and configure the Slack Bolt app."""
    _, token = _get_integration_and_token()
    if not token:
        raise RuntimeError("No Slack bot token. Connect Slack in WorkHub first.")

    app = App(token=token)

    # ── Handler: all message types ──────────────────────────────────────────
    @app.event("message")
    def on_message(event, say, client):
        _process_message(event, say, client)

    # ── Handler: DMs specifically (message subtype for im) ───────────────────
    @app.event({"type": "message", "channel_type": "im"})
    def on_dm(event, say, client):
        _process_message(event, say, client)

    # ── Handler: @mentions — always reply ───────────────────────────────────
    @app.event("app_mention")
    def on_mention(event, say, client):
        text = event.get("text", "")
        ts = event.get("ts", "")
        user_id = event.get("user", "")
        clean_text = re.sub(r"<@[A-Z0-9]+>", "", text).strip()

        if not clean_text:
            say(text="Hey! How can I help you? 👋", thread_ts=ts)
            return

        logger.info(f"📣 Mention from {user_id}: {clean_text[:60]}")

        # Also save the mention to DB
        integration, _ = _get_integration_and_token()
        try:
            classification = classify_message(clean_text)
        except Exception:
            classification = {"classification": "general", "summary": clean_text[:100]}

        try:
            reply_text = generate_reply(clean_text)
        except Exception as e:
            logger.error(f"Mention reply failed: {e}")
            say(text="Sorry, I'm having trouble right now.", thread_ts=ts)
            return

        say(text=reply_text, thread_ts=ts)

        if integration:
            sender_name = _get_sender_name(client, user_id)
            channel_id = event.get("channel", "")
            SlackMessage.objects.get_or_create(
                company=integration.company,
                channel_id=channel_id,
                timestamp=ts,
                defaults={
                    "channel_name": _get_channel_name(client, channel_id),
                    "sender_id": user_id,
                    "sender_name": sender_name,
                    "text": clean_text,
                    "ai_classification": classification["classification"],
                    "ai_summary": classification["summary"],
                    "ai_reply": reply_text,
                    "is_auto_replied": True,
                    "reply_sent_at": datetime.now(timezone.utc),
                },
            )

    return app


def run_bot():
    """Start the Socket Mode bot (blocking). Called from thread or management command."""
    app_token = settings.SLACK_APP_TOKEN
    if not app_token:
        raise RuntimeError(
            "SLACK_APP_TOKEN not set in .env. "
            "Get it from Slack App > Basic Information > App-Level Tokens."
        )

    app = create_slack_app()
    handler = SocketModeHandler(app, app_token)

    logger.info("🚀 Slack AI Bot running (Socket Mode — WebSocket)")
    logger.info("   ✓ Channels + DMs handled automatically")
    logger.info("   ✓ AI classifies + replies to every message")
    logger.info("   ✓ History at /slack/history/")

    handler.start()
