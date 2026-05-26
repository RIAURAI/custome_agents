"""
Webhook API views for receiving incoming messages from social media platforms.
These endpoints are called by WhatsApp Cloud API, Facebook, Instagram, LinkedIn, and Twitter webhooks.
"""
import hashlib
import hmac
import json
import logging

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .bot_handler import SocialMediaBotHandler
from .models import SocialMediaAccount

logger = logging.getLogger(__name__)


def _verify_webhook_signature(request, secret: str, platform: str) -> bool:
    """Verify webhook signature from platform."""
    if not secret:
        return True  # Skip verification if no secret configured

    if platform == "whatsapp" or platform == "facebook" or platform == "instagram":
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not signature:
            return False
        expected = "sha256=" + hmac.HMAC(
            secret.encode(), request.body, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected)

    return True


# ── WhatsApp Webhook ──────────────────────────────────────────────────────────


@csrf_exempt
@require_http_methods(["GET", "POST"])
def whatsapp_webhook(request):
    """
    WhatsApp Cloud API webhook endpoint.
    GET: Verification challenge
    POST: Incoming messages
    """
    if request.method == "GET":
        # Webhook verification
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        verify_token = getattr(settings, "WHATSAPP_VERIFY_TOKEN", "")
        if mode == "subscribe" and token == verify_token:
            return HttpResponse(challenge, content_type="text/plain")
        return HttpResponse("Forbidden", status=403)

    # POST: process incoming message
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Parse WhatsApp webhook payload
    entries = body.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            messages = value.get("messages", [])
            metadata = value.get("metadata", {})
            phone_number_id = metadata.get("phone_number_id", "")

            for msg in messages:
                _handle_whatsapp_message(phone_number_id, msg, value.get("contacts", []))

    return JsonResponse({"status": "ok"})


def _handle_whatsapp_message(phone_number_id: str, msg: dict, contacts: list):
    """Process a single WhatsApp incoming message."""
    account = SocialMediaAccount.objects.filter(
        platform="whatsapp",
        phone_number_id=phone_number_id,
        status="active",
    ).first()

    if not account:
        logger.warning(f"No WhatsApp account for phone_number_id: {phone_number_id}")
        return

    sender_phone = msg.get("from", "")
    msg_id = msg.get("id", "")
    msg_type = msg.get("type", "text")
    timestamp_str = msg.get("timestamp", "")

    # Extract text content
    content = ""
    if msg_type == "text":
        content = msg.get("text", {}).get("body", "")
    elif msg_type == "image":
        content = msg.get("image", {}).get("caption", "[Image]")
    elif msg_type == "document":
        content = msg.get("document", {}).get("caption", "[Document]")
    else:
        content = f"[{msg_type}]"

    # Get sender name from contacts
    sender_name = ""
    for contact in contacts:
        if contact.get("wa_id") == sender_phone:
            profile = contact.get("profile", {})
            sender_name = profile.get("name", "")
            break

    # Process through bot handler
    handler = SocialMediaBotHandler(account.company)
    handler.process_incoming_message(account, {
        "sender_id": sender_phone,
        "sender_name": sender_name,
        "content": content,
        "message_type": msg_type,
        "platform_message_id": msg_id,
        "is_group": False,
    })


# ── Facebook / Instagram Webhook ──────────────────────────────────────────────


@csrf_exempt
@require_http_methods(["GET", "POST"])
def facebook_webhook(request):
    """
    Facebook Messenger / Instagram webhook endpoint.
    GET: Verification
    POST: Incoming messages
    """
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        verify_token = getattr(settings, "FACEBOOK_VERIFY_TOKEN", "")
        if mode == "subscribe" and token == verify_token:
            return HttpResponse(challenge, content_type="text/plain")
        return HttpResponse("Forbidden", status=403)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    entries = body.get("entry", [])
    for entry in entries:
        page_id = entry.get("id", "")
        messaging = entry.get("messaging", [])

        for event in messaging:
            if "message" in event:
                _handle_facebook_message(page_id, event)

    return JsonResponse({"status": "ok"})


def _handle_facebook_message(page_id: str, event: dict):
    """Process a single Facebook/Instagram message event."""
    # Try Facebook first, then Instagram
    account = SocialMediaAccount.objects.filter(
        page_id=page_id,
        platform__in=["facebook", "instagram"],
        status="active",
    ).first()

    if not account:
        logger.warning(f"No FB/IG account for page_id: {page_id}")
        return

    sender = event.get("sender", {})
    sender_id = sender.get("id", "")
    message = event.get("message", {})
    msg_id = message.get("mid", "")
    text = message.get("text", "")

    if not text:
        # Attachments, stickers, etc.
        attachments = message.get("attachments", [])
        if attachments:
            text = f"[{attachments[0].get('type', 'attachment')}]"
        else:
            return

    handler = SocialMediaBotHandler(account.company)
    handler.process_incoming_message(account, {
        "sender_id": sender_id,
        "sender_name": "",
        "content": text,
        "message_type": "text",
        "platform_message_id": msg_id,
        "is_group": False,
    })


# ── LinkedIn Webhook ──────────────────────────────────────────────────────────


@csrf_exempt
@require_http_methods(["POST"])
def linkedin_webhook(request):
    """LinkedIn messaging webhook (requires LinkedIn Partner program)."""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # LinkedIn webhook payload varies — this handles messaging events
    event_type = body.get("eventType", "")
    if event_type != "MESSAGING":
        return JsonResponse({"status": "ignored"})

    elements = body.get("elements", [])
    for element in elements:
        msg_event = element.get("event", {})
        message_body = msg_event.get("messageBody", {})
        text = message_body.get("text", "")
        sender_urn = msg_event.get("from", "")

        if not text or not sender_urn:
            continue

        # Find the LinkedIn account
        account = SocialMediaAccount.objects.filter(
            platform="linkedin", status="active"
        ).first()

        if not account:
            continue

        handler = SocialMediaBotHandler(account.company)
        handler.process_incoming_message(account, {
            "sender_id": sender_urn,
            "sender_name": "",
            "content": text,
            "message_type": "text",
            "platform_message_id": element.get("id", ""),
            "is_group": False,
        })

    return JsonResponse({"status": "ok"})


# ── Twitter/X Webhook ─────────────────────────────────────────────────────────


@csrf_exempt
@require_http_methods(["GET", "POST"])
def twitter_webhook(request):
    """Twitter/X Account Activity API webhook."""
    if request.method == "GET":
        # CRC challenge
        crc_token = request.GET.get("crc_token", "")
        consumer_secret = getattr(settings, "TWITTER_CONSUMER_SECRET", "")
        if crc_token and consumer_secret:
            import base64
            sha256_hash = hmac.HMAC(
                consumer_secret.encode(), crc_token.encode(), hashlib.sha256
            ).digest()
            response_token = "sha256=" + base64.b64encode(sha256_hash).decode()
            return JsonResponse({"response_token": response_token})
        return HttpResponse("Forbidden", status=403)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Handle Direct Message events
    dm_events = body.get("direct_message_events", [])
    for event in dm_events:
        if event.get("type") != "message_create":
            continue

        msg_create = event.get("message_create", {})
        sender_id = msg_create.get("sender_id", "")
        target = msg_create.get("target", {})
        recipient_id = target.get("recipient_id", "")
        msg_data = msg_create.get("message_data", {})
        text = msg_data.get("text", "")

        if not text:
            continue

        account = SocialMediaAccount.objects.filter(
            platform="twitter", status="active", account_id=recipient_id
        ).first()

        if not account:
            continue

        # Don't process our own messages
        if sender_id == account.account_id:
            continue

        handler = SocialMediaBotHandler(account.company)
        handler.process_incoming_message(account, {
            "sender_id": sender_id,
            "sender_name": "",
            "content": text,
            "message_type": "text",
            "platform_message_id": event.get("id", ""),
            "is_group": False,
        })

    return JsonResponse({"status": "ok"})


# ── Telegram Webhook ──────────────────────────────────────────────────────────


@csrf_exempt
@require_http_methods(["POST"])
def telegram_webhook(request):
    """
    Telegram Bot API webhook endpoint.
    Receives updates from Telegram when bot gets messages.
    """
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Handle different update types
    message = body.get("message") or body.get("channel_post")
    if not message:
        return JsonResponse({"status": "ignored"})

    chat = message.get("chat", {})
    chat_id = str(chat.get("id", ""))
    chat_type = chat.get("type", "private")  # private, group, supergroup, channel
    sender = message.get("from", {})
    sender_id = str(sender.get("id", ""))
    sender_name = sender.get("first_name", "")
    if sender.get("last_name"):
        sender_name += f" {sender['last_name']}"

    # Extract text
    text = message.get("text", "")
    if not text:
        # Handle other content types
        if message.get("photo"):
            text = message.get("caption", "[Photo]")
        elif message.get("document"):
            text = message.get("caption", "[Document]")
        elif message.get("voice"):
            text = "[Voice message]"
        elif message.get("sticker"):
            text = f"[Sticker: {message['sticker'].get('emoji', '')}]"
        else:
            text = "[Unsupported content]"

    if not text:
        return JsonResponse({"status": "no_content"})

    # Find the Telegram account — match by bot username or chat_id
    account = None
    if chat_type == "private":
        account = SocialMediaAccount.objects.filter(
            platform="telegram", status="active"
        ).first()
    else:
        # Group/channel — try matching by stored chat_id
        account = SocialMediaAccount.objects.filter(
            platform="telegram", status="active", telegram_chat_id=chat_id
        ).first()
        if not account:
            # Fallback: any active telegram account
            account = SocialMediaAccount.objects.filter(
                platform="telegram", status="active"
            ).first()

    if not account:
        logger.warning(f"No Telegram account found for chat_id: {chat_id}")
        return JsonResponse({"status": "no_account"})

    # Skip messages from the bot itself
    bot_id = account.account_id
    if sender_id == bot_id:
        return JsonResponse({"status": "own_message"})

    # Handle bot commands
    if text.startswith("/"):
        command = text.split()[0].split("@")[0]
        if command in ("/start", "/help"):
            _send_telegram_welcome(account, chat_id, command)
            return JsonResponse({"status": "command_handled"})

    # Process through bot handler
    handler = SocialMediaBotHandler(account.company)
    handler.process_incoming_message(account, {
        "sender_id": sender_id,
        "sender_name": sender_name,
        "content": text,
        "message_type": "text",
        "platform_message_id": str(message.get("message_id", "")),
        "is_group": chat_type in ("group", "supergroup"),
        "chat_id": chat_id,
    })

    return JsonResponse({"status": "ok"})


def _send_telegram_welcome(account, chat_id: str, command: str):
    """Send a welcome/help message for /start or /help commands."""
    from integrations.utils import decrypt_token
    import requests as http_requests

    try:
        token = decrypt_token(account.access_token_enc)
    except Exception:
        return

    if command == "/start":
        text = (
            f"👋 Hi! I'm {account.account_name}.\n\n"
            "I'm an AI-powered business assistant. You can:\n"
            "• Ask me questions about our business\n"
            "• Send messages and I'll reply\n"
            "• Use /help to see available commands\n\n"
            "How can I help you today?"
        )
    else:
        text = (
            "📋 *Available Commands:*\n\n"
            "/start - Start conversation\n"
            "/help - Show this help message\n\n"
            "Or simply type your message and I'll respond!"
        )

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    http_requests.post(url, json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }, timeout=10)
