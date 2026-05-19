import json
from datetime import datetime, timezone

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
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


@login_required
def channel_messages_view(request, channel_id):
    """Show messages from a specific channel with tracking."""
    token = _get_slack_token(request)
    if not token:
        return redirect("integrations:connect")

    msgs = []
    channel_name = request.GET.get("name", channel_id)
    error = None

    try:
        raw_messages = fetch_messages(token, channel_id, limit=30)
        # Enrich messages with user names
        user_cache = {}
        for msg in raw_messages:
            if msg.get("type") != "message" or msg.get("subtype"):
                continue
            user_id = msg.get("user", "")
            if user_id not in user_cache:
                user_cache[user_id] = get_user_name(token, user_id)
            msg["sender_name"] = user_cache[user_id]
            msgs.append(msg)
    except Exception as e:
        error = str(e)

    return render(request, "slack_hub/messages.html", {
        "messages": msgs,
        "channel_id": channel_id,
        "channel_name": channel_name,
        "error": error,
    })


@login_required
def track_view(request):
    """Dashboard of all tracked/analyzed messages."""
    tracked = SlackMessage.objects.filter(user=request.user)[:50]
    return render(request, "slack_hub/track.html", {"tracked_messages": tracked})


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

    rules = {r.channel_id: r for r in AutoReplyRule.objects.filter(user=request.user)}

    if request.method == "POST":
        channel_id = request.POST.get("channel_id", "").strip()
        channel_name = request.POST.get("channel_name", "").strip()
        is_enabled = request.POST.get("is_enabled") == "on"
        auto_send = request.POST.get("auto_send") == "on"
        keywords = request.POST.get("keywords", "").strip()
        custom_instructions = request.POST.get("custom_instructions", "").strip()

        if channel_id:
            rule, _ = AutoReplyRule.objects.get_or_create(
                user=request.user, channel_id=channel_id
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
