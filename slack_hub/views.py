import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timezone

from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from integrations.models import UserIntegration
from integrations.slack_utils import get_valid_slack_token

from .models import SlackMessage, AutoReplyRule
from .slack_service import (
    fetch_channels,
    fetch_messages,
    get_user_name,
    send_message,
)
from .ai_service import classify_message, generate_reply, summarize_channel

logger = logging.getLogger(__name__)


def _get_slack_token(request):
    """Get valid Slack token or return None with message."""
    integration = UserIntegration.objects.filter(
        user=request.user, service="slack"
    ).first()
    if not integration:
        messages.warning(request, "Please connect your Slack account first.")
        return None
    token = get_valid_slack_token(integration)
    if not token:
        messages.error(request, "Slack token invalid. Please reconnect.")
        return None
    return token


def _verify_slack_signature(request):
    """Verify the request is genuinely from Slack using signing secret."""
    signing_secret = django_settings.SLACK_SIGNING_SECRET
    if not signing_secret:
        return False

    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")

    if not timestamp or not signature:
        return False

    try:
        if abs(time.time() - int(timestamp)) > 300:
            return False
    except (ValueError, TypeError):
        return False

    sig_basestring = f"v0:{timestamp}:{request.body.decode('utf-8')}"
    my_signature = "v0=" + hmac.new(
        signing_secret.encode("utf-8"),
        sig_basestring.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(my_signature, signature)


# ── Slack Events API Webhook ──────────────────────────────────────────────────

@csrf_exempt
def slack_events_webhook(request):
    """
    POST /slack/events/
    Receives all Slack Events API payloads.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Handle Slack URL verification challenge
    if payload.get("type") == "url_verification":
        return JsonResponse({"challenge": payload.get("challenge", "")})

    # Verify request signature
    if not _verify_slack_signature(request):
        logger.warning("Slack event with invalid signature rejected.")
        return JsonResponse({"error": "Invalid signature"}, status=403)

    # Handle event callbacks
    if payload.get("type") == "event_callback":
        event = payload.get("event", {})
        team_id = payload.get("team_id", "")
        try:
            _handle_slack_event(event, team_id)
        except Exception as e:
            logger.error(f"Error handling Slack event: {e}")

    return JsonResponse({"ok": True})


def _handle_slack_event(event: dict, team_id: str):
    """
    Process incoming Slack message:
    1. Verify it's a real user message (not bot)
    2. Find connected user in our system
    3. Check auto-reply rules
    4. AI analyze + generate reply
    5. Send reply to Slack
    6. Save to DB
    """
    if event.get("type") != "message":
        return
    if event.get("subtype"):
        return
    if event.get("bot_id"):  # Avoid infinite loops!
        return

    channel_id = event.get("channel", "")
    user_id = event.get("user", "")
    text = event.get("text", "").strip()
    ts = event.get("ts", "")
    thread_ts = event.get("thread_ts", "")

    if not text or not channel_id:
        return

    # Find user with this Slack workspace connected
    integration = UserIntegration.objects.filter(
        service="slack", slack_team_id=team_id
    ).first()
    if not integration:
        integration = UserIntegration.objects.filter(service="slack").first()
    if not integration:
        return

    token = get_valid_slack_token(integration)
    if not token:
        return

    # Check auto-reply rules for this channel
    rule = AutoReplyRule.objects.filter(
        user=integration.user, channel_id=channel_id, is_enabled=True
    ).first()
    if not rule:
        # Check for global rule (channel_id="*" means all channels)
        rule = AutoReplyRule.objects.filter(
            user=integration.user, channel_id="*", is_enabled=True
        ).first()
    if not rule:
        return

    # Check keywords filter
    if rule.keywords:
        keywords = [k.strip().lower() for k in rule.keywords.split(",") if k.strip()]
        if not any(kw in text.lower() for kw in keywords):
            return

    # Get sender name
    try:
        sender_name = get_user_name(token, user_id)
    except Exception:
        sender_name = user_id

    # AI: Classify message
    try:
        classification_result = classify_message(text)
    except Exception:
        classification_result = {"classification": "general", "summary": text[:100]}

    # AI: Generate reply
    try:
        reply_text = generate_reply(text, custom_instructions=rule.custom_instructions)
    except Exception as e:
        logger.error(f"AI reply generation failed: {e}")
        return

    # Save to DB
    msg, _ = SlackMessage.objects.get_or_create(
        user=integration.user,
        channel_id=channel_id,
        timestamp=ts,
        defaults={
            "channel_name": rule.channel_name or channel_id,
            "sender_id": user_id,
            "sender_name": sender_name,
            "text": text,
            "thread_ts": thread_ts,
            "ai_classification": classification_result["classification"],
            "ai_summary": classification_result["summary"],
            "ai_reply": reply_text,
        },
    )

    # Send reply to Slack if auto_send is enabled
    if rule.auto_send:
        try:
            send_message(token, channel_id, reply_text, thread_ts=ts)
            msg.is_auto_replied = True
            msg.reply_sent_at = datetime.now(timezone.utc)
            msg.save()
        except Exception as e:
            logger.error(f"Failed to send auto-reply: {e}")
    else:
        msg.save()


# ── Page Views ────────────────────────────────────────────────────────────────


@login_required
def channels_view(request):
    """List all Slack channels."""
    token = _get_slack_token(request)
    channels = []
    error = None
    slack_connected = UserIntegration.objects.filter(
        user=request.user, service="slack"
    ).exists()

    if token:
        try:
            channels = fetch_channels(token)
        except Exception as e:
            error = str(e)

    return render(request, "slack_hub/channels.html", {
        "channels": channels,
        "error": error,
        "slack_connected": slack_connected,
    })


def _clean_slack_text(text, user_cache, token, get_user_name_fn):
    """Convert Slack mrkdwn to plain readable text."""
    import re
    if not text:
        return ""
    # <@USERID> -> @Name
    def replace_mention(m):
        uid = m.group(1)
        if uid not in user_cache:
            user_cache[uid] = get_user_name_fn(token, uid)
        return "@" + user_cache[uid]
    text = re.sub(r"<@([A-Z0-9]+)>", replace_mention, text)
    # <#CHANNELID|channel-name> -> #channel-name
    text = re.sub(r"<#[A-Z0-9]+\|([^>]+)>", r"#\1", text)
    # <!subteam^ID|@handle> -> @handle
    text = re.sub(r"<!subteam\^[^|>]+\|([^>]+)>", r"\1", text)
    # <!here>, <!channel>, <!everyone>
    text = re.sub(r"<!here>", "@here", text)
    text = re.sub(r"<!channel>", "@channel", text)
    text = re.sub(r"<!everyone>", "@everyone", text)
    # <http://url|display text> -> display text
    text = re.sub(r"<https?://[^|>]+\|([^>]+)>", r"\1", text)
    # bare <http://url> -> url
    text = re.sub(r"<(https?://[^>]+)>", r"\1", text)
    # Skip messages that are pure JSON (bot block payloads with no readable text)
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return ""
    if stripped.startswith("[") and stripped.endswith("]"):
        return ""
    return text


@login_required
def channel_messages_view(request, channel_id):
    """
    Show messages from a specific Slack channel.

    Steps:
      1. Get a valid Slack token for the logged-in user.
      2. Fetch the last 50 raw messages from the Slack API.
      3. Filter out non-message events (bot subtypes, etc.).
      4. Resolve each sender's display name (with a local cache to avoid repeated API calls).
      5. Convert the raw Unix timestamp to a human-readable format.
      6. Clean mrkdwn / special tokens from the message text.
      7. If the cleaned text is empty, fall back to extracting plain text from Slack Block Kit blocks.
      8. Skip messages that still have no displayable text.
      9. Render the processed message list to the template.
    """
    import datetime

    # Step 1 – Retrieve a valid Slack OAuth token; redirect to connect page if missing.
    token = _get_slack_token(request)
    if not token:
        return redirect("integrations:connect")

    msgs = []
    channel_name = request.GET.get("name", channel_id)
    error = None

    try:
        # Step 2 – Fetch the latest 50 messages from the requested channel.
        raw_messages = fetch_messages(token, channel_id, limit=50)

        # Local cache: { slack_user_id -> display_name } to avoid redundant API calls.
        user_cache = {}

        for msg in raw_messages:
            # Step 3 – Skip anything that isn't a plain user message.
            if msg.get("type") != "message" or msg.get("subtype"):
                continue

            # Step 4 – Resolve sender display name.
            user_id = msg.get("user", "")
            if user_id not in user_cache:
                user_cache[user_id] = get_user_name(token, user_id)
            msg["sender_name"] = user_cache[user_id]

            # Step 5 – Format the Unix timestamp into a readable string.
            try:
                ts_float = float(msg.get("ts", 0))
                msg["ts_display"] = datetime.datetime.fromtimestamp(ts_float).strftime("%b %d, %H:%M")
            except Exception:
                msg["ts_display"] = msg.get("ts", "")

            # Step 6 – Convert Slack mrkdwn / mention tokens to plain text.
            clean = _clean_slack_text(msg.get("text", ""), user_cache, token, get_user_name)

            # Step 7 – If mrkdwn text was empty, extract plain text from Block Kit blocks.
            if not clean and msg.get("blocks"):
                parts = []
                for block in msg["blocks"]:
                    for elem in block.get("elements", []):
                        for e in elem.get("elements", [elem]):
                            if e.get("type") == "text":
                                parts.append(e.get("text", ""))
                            elif e.get("type") == "user":
                                uid = e.get("user_id", "")
                                if uid not in user_cache:
                                    user_cache[uid] = get_user_name(token, uid)
                                parts.append("@" + user_cache[uid])
                clean = " ".join(parts).strip()

            msg["text"] = clean

            # Step 8 – Drop messages that have no displayable text after all processing.
            if not msg["text"]:
                continue

            msgs.append(msg)

    except Exception as e:
        error = str(e)

    # Step 9 – Render the processed messages to the template.
    return render(request, "slack_hub/messages.html", {
        "messages": msgs,
        "channel_id": channel_id,
        "channel_name": channel_name,
        "error": error,
    })


@login_required
def track_view(request):
    """Dashboard of all tracked/analyzed messages."""
    company = getattr(request, "company", None)
    if company:
        tracked = SlackMessage.objects.filter(company=company).order_by("-tracked_at")[:100]
    else:
        tracked = SlackMessage.objects.filter(company__members=request.user).order_by("-tracked_at")[:100]

    tracked_list = list(tracked)
    total = len(tracked_list)
    replied = sum(1 for m in tracked_list if m.is_auto_replied)
    pending = sum(1 for m in tracked_list if m.ai_reply and not m.is_auto_replied)
    dm_count = sum(1 for m in tracked_list if m.channel_name.startswith("DM"))
    channel_count = total - dm_count

    stats = {
        "total": total,
        "analyzed": sum(1 for m in tracked_list if m.ai_classification),
        "replied": replied,
        "pending": pending,
        "dm_count": dm_count,
        "channel_count": channel_count,
    }

    return render(request, "slack_hub/track.html", {
        "tracked_messages": tracked_list,
        "stats": stats,
    })


@login_required
@require_POST
def sync_messages_view(request):
    """
    Pull recent messages from all Slack channels via API and store in DB.
    This allows tracking even if the Socket Mode bot missed events.
    """
    token = _get_slack_token(request)
    if not token:
        return JsonResponse({"ok": False, "error": "Slack not connected."}, status=400)

    company = getattr(request, "company", None)
    if not company:
        return JsonResponse({"ok": False, "error": "No company context."}, status=400)

    try:
        channels = fetch_channels(token)
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"Failed to fetch channels: {e}"}, status=500)

    synced = 0
    skipped = 0
    errors = []

    for ch in channels[:20]:  # Limit to 20 channels to avoid rate limits
        ch_id = ch.get("id", "")
        ch_name = ch.get("name", ch_id)

        try:
            msgs = fetch_messages(token, ch_id, limit=20)
        except Exception as e:
            errors.append(f"#{ch_name}: {e}")
            continue

        for msg in msgs:
            # Skip bot messages and system messages
            if msg.get("bot_id") or msg.get("subtype"):
                continue

            msg_text = msg.get("text", "").strip()
            msg_ts = msg.get("ts", "")
            msg_user = msg.get("user", "")
            thread_ts = msg.get("thread_ts", "")

            if not msg_text or not msg_ts or not msg_user:
                continue

            # Check if already tracked
            exists = SlackMessage.objects.filter(
                company=company, channel_id=ch_id, timestamp=msg_ts
            ).exists()
            if exists:
                skipped += 1
                continue

            # Resolve sender name
            try:
                sender_name = get_user_name(token, msg_user)
            except Exception:
                sender_name = msg_user

            # Save to DB
            SlackMessage.objects.create(
                company=company,
                channel_id=ch_id,
                channel_name=ch_name,
                sender_id=msg_user,
                sender_name=sender_name,
                text=msg_text,
                timestamp=msg_ts,
                thread_ts=thread_ts,
                ai_classification="",
                ai_summary="",
                ai_reply="",
            )
            synced += 1

    return JsonResponse({
        "ok": True,
        "synced": synced,
        "skipped": skipped,
        "channels_scanned": min(len(channels), 20),
        "errors": errors[:5],
    })


@login_required
def auto_reply_settings_view(request):
    """Configure auto-reply rules per channel."""
    token = _get_slack_token(request)
    channels = []
    if token:
        try:
            channels = fetch_channels(token)
        except Exception:
            pass

    rules = {r.channel_id: r for r in AutoReplyRule.objects.filter(company=request.company)}

    if request.method == "POST":
        channel_id = request.POST.get("channel_id", "").strip()
        channel_name = request.POST.get("channel_name", "").strip()
        is_enabled = request.POST.get("is_enabled") == "on"
        auto_send = request.POST.get("auto_send") == "on"
        keywords = request.POST.get("keywords", "").strip()
        custom_instructions = request.POST.get("custom_instructions", "").strip()

        if channel_id:
            rule, _ = AutoReplyRule.objects.get_or_create(
                company=request.company, channel_id=channel_id
            )
            rule.channel_name = channel_name
            rule.is_enabled = is_enabled
            rule.auto_send = auto_send
            rule.keywords = keywords
            rule.custom_instructions = custom_instructions
            rule.save()
            messages.success(request, f"Auto-reply rule updated for #{channel_name}.")
            return redirect("slack_hub:settings")

    return render(request, "slack_hub/settings.html", {
        "channels": channels,
        "rules": rules,
    })


@login_required
def auto_reply_history_view(request):
    """Show all auto-replied and pending messages."""
    tracked = SlackMessage.objects.filter(company=request.company).order_by("-tracked_at")[:100]
    stats = {
        "total": tracked.count(),
        "replied": sum(1 for m in tracked if m.is_auto_replied),
        "pending": sum(1 for m in tracked if m.ai_reply and not m.is_auto_replied),
    }
    return render(request, "slack_hub/auto_reply_history.html", {
        "messages": tracked,
        "stats": stats,
    })


@login_required
@require_POST
def ai_analyze_view(request):
    """
    POST /slack/ai/analyze/
    Body: {"text": "...", "channel_id": "...", "channel_name": "...", "sender_id": "...", "sender_name": "...", "ts": "..."}
    Classifies message and stores in DB.
    """
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    text = payload.get("text", "").strip()
    if not text:
        return JsonResponse({"error": "No text provided."}, status=400)

    # AI classify
    try:
        result = classify_message(text)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    # Store tracked message
    msg, created = SlackMessage.objects.get_or_create(
        user=request.user,
        channel_id=payload.get("channel_id", ""),
        timestamp=payload.get("ts", ""),
        defaults={
            "channel_name": payload.get("channel_name", ""),
            "sender_id": payload.get("sender_id", ""),
            "sender_name": payload.get("sender_name", ""),
            "text": text,
            "ai_classification": result["classification"],
            "ai_summary": result["summary"],
        },
    )
    if not created:
        msg.ai_classification = result["classification"]
        msg.ai_summary = result["summary"]
        msg.save()

    return JsonResponse({
        "classification": result["classification"],
        "summary": result["summary"],
        "tracked": True,
    })


@login_required
@require_POST
def ai_reply_view(request):
    """
    POST /slack/ai/reply/
    Body: {"text": "...", "channel_id": "...", "ts": "...", "send": true/false}
    Generates AI reply and optionally sends it to Slack.
    """
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    text = payload.get("text", "").strip()
    channel_id = payload.get("channel_id", "")
    ts = payload.get("ts", "")
    should_send = payload.get("send", False)

    if not text:
        return JsonResponse({"error": "No text provided."}, status=400)

    # Check for custom instructions from auto-reply rule
    custom_instructions = ""
    rule = AutoReplyRule.objects.filter(
        user=request.user, channel_id=channel_id
    ).first()
    if rule:
        custom_instructions = rule.custom_instructions

    # Generate AI reply
    try:
        reply_text = generate_reply(text, custom_instructions=custom_instructions)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    sent = False
    if should_send and channel_id:
        token = _get_slack_token(request)
        if token:
            try:
                send_message(token, channel_id, reply_text, thread_ts=ts)
                sent = True
                # Update tracked message
                SlackMessage.objects.filter(
                    user=request.user, channel_id=channel_id, timestamp=ts
                ).update(
                    ai_reply=reply_text,
                    is_auto_replied=True,
                    reply_sent_at=datetime.now(timezone.utc),
                )
            except Exception as e:
                return JsonResponse({"error": f"Reply generated but send failed: {e}", "reply": reply_text}, status=500)
        else:
            return JsonResponse({"error": "Slack not connected.", "reply": reply_text}, status=403)

    return JsonResponse({
        "reply": reply_text,
        "sent": sent,
    })


@login_required
@require_POST
def ai_summarize_channel_view(request):
    """
    POST /slack/ai/summarize/
    Body: {"channel_id": "..."}
    Summarizes recent channel activity.
    """
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    channel_id = payload.get("channel_id", "")
    if not channel_id:
        return JsonResponse({"error": "No channel_id provided."}, status=400)

    token = _get_slack_token(request)
    if not token:
        return JsonResponse({"error": "Slack not connected."}, status=403)

    try:
        raw_messages = fetch_messages(token, channel_id, limit=20)
        # Enrich with names
        user_cache = {}
        enriched = []
        for msg in raw_messages:
            if msg.get("type") != "message" or msg.get("subtype"):
                continue
            user_id = msg.get("user", "")
            if user_id not in user_cache:
                user_cache[user_id] = get_user_name(token, user_id)
            enriched.append({
                "sender_name": user_cache[user_id],
                "text": msg.get("text", ""),
            })

        summary = summarize_channel(enriched)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"summary": summary})
