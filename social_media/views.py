from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import SocialMediaAccount, SocialMediaPost, SocialMediaMessage, AutoReplyRule, BotConversationLog


def company_admin_required(view_func):
    """User must be logged in AND be a company owner/admin."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        membership = getattr(request, "membership", None)
        if not membership or not membership.is_admin:
            messages.error(request, "Only company admins can manage social media accounts.")
            return redirect("social_media:dashboard")
        return view_func(request, *args, **kwargs)
    return wrapper


# ─── Dashboard ────────────────────────────────────────────────────────────────


@login_required
def dashboard_view(request):
    """Main social media hub — shows all connected accounts and recent posts."""
    company = getattr(request, "company", None)
    accounts = []
    recent_posts = []
    if company:
        accounts = company.social_accounts.filter(status="active")
        recent_posts = SocialMediaPost.objects.filter(company=company).select_related("account")[:10]

    membership = getattr(request, "membership", None)
    is_admin = membership.is_admin if membership else False

    platform_info = [
        {"key": "whatsapp", "name": "WhatsApp Business", "icon": "bi-whatsapp", "color": "#25D366"},
        {"key": "linkedin", "name": "LinkedIn", "icon": "bi-linkedin", "color": "#0A66C2"},
        {"key": "facebook", "name": "Facebook", "icon": "bi-facebook", "color": "#1877F2"},
        {"key": "instagram", "name": "Instagram", "icon": "bi-instagram", "color": "#E4405F"},
        {"key": "telegram", "name": "Telegram", "icon": "bi-telegram", "color": "#0088CC"},
    ]

    # Only map accounts that are truly connected (active + have a token)
    connected_map = {
        a.platform: a for a in accounts
        if a.access_token_enc
    }

    # Inject account object into platform_info for easy template access
    for info in platform_info:
        info["account"] = connected_map.get(info["key"])

    return render(request, "social_media/social_media_dashboard.html", {
        "accounts": accounts,
        "recent_posts": recent_posts,
        "is_admin": is_admin,
        "platform_info": platform_info,
    })


@login_required
def setup_guide(request):
    """Show setup instructions for all platforms."""
    return render(request, "social_media/setup_guide.html")


# ─── Connect / Disconnect ────────────────────────────────────────────────────


@company_admin_required
def connect_account(request, platform):
    """Connect a social media account — accepts JSON (modal) or form POST."""
    valid_platforms = dict(SocialMediaAccount.PLATFORM_CHOICES)
    if platform not in valid_platforms:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": "Invalid platform."})
        messages.error(request, "Invalid platform.")
        return redirect("social_media:dashboard")

    if request.method == "POST":
        account_name = request.POST.get("account_name", "").strip()
        account_id = request.POST.get("account_id", "").strip()
        access_token = request.POST.get("access_token", "").strip()
        api_key = request.POST.get("api_key", "").strip()
        page_id = request.POST.get("page_id", "").strip()
        phone_number_id = request.POST.get("phone_number_id", "").strip()
        waba_id = request.POST.get("waba_id", "").strip()
        profile_url = request.POST.get("profile_url", "").strip()
        webhook_secret = request.POST.get("webhook_secret", "").strip()
        telegram_chat_id = request.POST.get("telegram_chat_id", "").strip()

        # Permissions
        can_read_messages = request.POST.get("can_read_messages") == "on"
        can_send_messages = request.POST.get("can_send_messages") == "on"
        can_auto_reply = request.POST.get("can_auto_reply") == "on"
        can_post_content = request.POST.get("can_post_content") == "on"

        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if not account_name:
            if is_ajax:
                return JsonResponse({"success": False, "error": "Account name is required."})
            messages.error(request, "Account name is required.")
            return redirect("social_media:dashboard")

        from integrations.utils import encrypt_token

        account, created = SocialMediaAccount.objects.update_or_create(
            company=request.company,
            platform=platform,
            account_id=account_id or account_name,
            defaults={
                "account_name": account_name,
                "profile_url": profile_url,
                "access_token_enc": encrypt_token(access_token) if access_token else None,
                "api_key_enc": encrypt_token(api_key) if api_key else None,
                "page_id": page_id,
                "phone_number_id": phone_number_id,
                "waba_id": waba_id,
                "telegram_chat_id": telegram_chat_id,
                "webhook_secret": webhook_secret,
                "can_read_messages": can_read_messages,
                "can_send_messages": can_send_messages,
                "can_auto_reply": can_auto_reply,
                "can_post_content": can_post_content,
                "status": "active" if access_token else "disconnected",
                "connected_by": request.user,
            },
        )

        action = "connected" if created else "updated"
        if is_ajax:
            return JsonResponse({"success": True, "message": f"{valid_platforms[platform]} {action} successfully!", "action": action})
        messages.success(request, f"{valid_platforms[platform]} account {action} successfully!")
        return redirect("social_media:dashboard")

    # GET — redirect to dashboard (modals handle UI now)
    return redirect("social_media:dashboard")


@company_admin_required
@require_POST
def disconnect_account(request, pk):
    """Disconnect (deactivate) a social media account."""
    account = get_object_or_404(
        SocialMediaAccount, pk=pk, company=request.company
    )
    account.status = "disconnected"
    account.access_token_enc = None
    account.refresh_token_enc = None
    account.save()
    messages.success(request, f"{account.get_platform_display()} disconnected.")
    return redirect("social_media:dashboard")


# ─── Posts ────────────────────────────────────────────────────────────────────


@login_required
def posts_list(request):
    """List all posts for the company."""
    company = getattr(request, "company", None)
    posts = []
    if company:
        posts = SocialMediaPost.objects.filter(company=company).select_related("account", "created_by")
    return render(request, "social_media/posts_list.html", {"posts": posts})


@login_required
def create_post(request):
    """Create a new social media post (draft or publish immediately)."""
    company = getattr(request, "company", None)
    accounts = []
    if company:
        accounts = company.social_accounts.filter(status="active")

    if request.method == "POST":
        account_id = request.POST.get("account")
        content = request.POST.get("content", "").strip()
        media_url = request.POST.get("media_url", "").strip()
        action = request.POST.get("action", "draft")  # draft or publish

        if not content:
            messages.error(request, "Post content cannot be empty.")
            return render(request, "social_media/create_post.html", {"accounts": accounts})

        account = get_object_or_404(SocialMediaAccount, pk=account_id, company=company, status="active")

        post = SocialMediaPost.objects.create(
            company=company,
            account=account,
            content=content,
            media_url=media_url,
            status="draft" if action == "draft" else "published",
            published_at=timezone.now() if action == "publish" else None,
            created_by=request.user,
        )

        if action == "publish":
            # TODO: Call platform API to publish
            messages.success(request, "Post published successfully!")
        else:
            messages.success(request, "Post saved as draft.")

        return redirect("social_media:posts_list")

    return render(request, "social_media/create_post.html", {"accounts": accounts})


@login_required
def post_detail(request, pk):
    """View a single post."""
    company = getattr(request, "company", None)
    post = get_object_or_404(SocialMediaPost, pk=pk, company=company)
    return render(request, "social_media/post_detail.html", {"post": post})


@require_POST
@login_required
def delete_post(request, pk):
    """Delete a draft post."""
    company = getattr(request, "company", None)
    post = get_object_or_404(SocialMediaPost, pk=pk, company=company, status="draft")
    post.delete()
    messages.success(request, "Draft deleted.")
    return redirect("social_media:posts_list")


# ─── Messages (WhatsApp / DMs) ───────────────────────────────────────────────


@login_required
def messages_inbox(request):
    """Show incoming messages from all social media accounts."""
    company = getattr(request, "company", None)
    inbox = []
    if company:
        account_ids = company.social_accounts.filter(status="active").values_list("id", flat=True)
        inbox = SocialMediaMessage.objects.filter(
            account_id__in=account_ids
        ).select_related("account")[:50]
    return render(request, "social_media/messages_inbox.html", {"inbox": inbox})


@login_required
def conversation_view(request, account_id, contact_id):
    """View conversation thread with a specific contact."""
    company = getattr(request, "company", None)
    account = get_object_or_404(SocialMediaAccount, pk=account_id, company=company)
    thread = SocialMediaMessage.objects.filter(
        account=account,
    ).filter(
        models.Q(sender_id=contact_id) | models.Q(recipient_id=contact_id)
    ).order_by("timestamp")

    # Mark as read
    thread.filter(direction="inbound", is_read=False).update(is_read=True)

    if request.method == "POST":
        reply_content = request.POST.get("content", "").strip()
        if reply_content:
            SocialMediaMessage.objects.create(
                account=account,
                direction="outbound",
                sender_id="business",
                recipient_id=contact_id,
                content=reply_content,
                timestamp=timezone.now(),
            )
            # TODO: Send via platform API
            messages.success(request, "Reply sent!")
            return redirect("social_media:conversation", account_id=account_id, contact_id=contact_id)

    return render(request, "social_media/conversation.html", {
        "account": account,
        "contact_id": contact_id,
        "thread": thread,
    })


# ─── AI Bot Configuration ────────────────────────────────────────────────────


@company_admin_required
def bot_settings(request):
    """View and manage AI bot auto-reply rules for all platforms."""
    company = request.company
    rules = AutoReplyRule.objects.filter(company=company).select_related("account")
    accounts = company.social_accounts.filter(status="active")

    return render(request, "social_media/bot_settings.html", {
        "rules": rules,
        "accounts": accounts,
    })


@company_admin_required
def create_bot_rule(request):
    """Create a new auto-reply rule."""
    company = request.company
    accounts = company.social_accounts.filter(status="active")

    if request.method == "POST":
        platform = request.POST.get("platform", "")
        account_id = request.POST.get("account", "")
        is_enabled = request.POST.get("is_enabled") == "on"
        auto_send = request.POST.get("auto_send") == "on"
        keywords = request.POST.get("keywords", "").strip()
        reply_to_dms = request.POST.get("reply_to_dms") == "on"
        reply_to_comments = request.POST.get("reply_to_comments") == "on"
        reply_to_groups = request.POST.get("reply_to_groups") == "on"
        custom_instructions = request.POST.get("custom_instructions", "").strip()
        persona_name = request.POST.get("persona_name", "").strip()

        account = None
        if account_id:
            account = SocialMediaAccount.objects.filter(pk=account_id, company=company).first()

        AutoReplyRule.objects.create(
            company=company,
            account=account,
            platform=platform,
            is_enabled=is_enabled,
            auto_send=auto_send,
            keywords=keywords,
            reply_to_dms=reply_to_dms,
            reply_to_comments=reply_to_comments,
            reply_to_groups=reply_to_groups,
            custom_instructions=custom_instructions,
            persona_name=persona_name,
        )
        messages.success(request, "Auto-reply rule created!")
        return redirect("social_media:bot_settings")

    return render(request, "social_media/create_bot_rule.html", {
        "accounts": accounts,
        "platform_choices": SocialMediaAccount.PLATFORM_CHOICES,
    })


@company_admin_required
def edit_bot_rule(request, pk):
    """Edit an existing auto-reply rule."""
    company = request.company
    rule = get_object_or_404(AutoReplyRule, pk=pk, company=company)
    accounts = company.social_accounts.filter(status="active")

    if request.method == "POST":
        rule.platform = request.POST.get("platform", rule.platform)
        account_id = request.POST.get("account", "")
        rule.account = SocialMediaAccount.objects.filter(pk=account_id, company=company).first() if account_id else None
        rule.is_enabled = request.POST.get("is_enabled") == "on"
        rule.auto_send = request.POST.get("auto_send") == "on"
        rule.keywords = request.POST.get("keywords", "").strip()
        rule.reply_to_dms = request.POST.get("reply_to_dms") == "on"
        rule.reply_to_comments = request.POST.get("reply_to_comments") == "on"
        rule.reply_to_groups = request.POST.get("reply_to_groups") == "on"
        rule.custom_instructions = request.POST.get("custom_instructions", "").strip()
        rule.persona_name = request.POST.get("persona_name", "").strip()
        rule.save()
        messages.success(request, "Rule updated!")
        return redirect("social_media:bot_settings")

    return render(request, "social_media/edit_bot_rule.html", {
        "rule": rule,
        "accounts": accounts,
        "platform_choices": SocialMediaAccount.PLATFORM_CHOICES,
    })


@company_admin_required
@require_POST
def delete_bot_rule(request, pk):
    """Delete an auto-reply rule."""
    rule = get_object_or_404(AutoReplyRule, pk=pk, company=request.company)
    rule.delete()
    messages.success(request, "Rule deleted.")
    return redirect("social_media:bot_settings")


@company_admin_required
@require_POST
def toggle_bot_rule(request, pk):
    """Toggle a rule on/off."""
    rule = get_object_or_404(AutoReplyRule, pk=pk, company=request.company)
    rule.is_enabled = not rule.is_enabled
    rule.save(update_fields=["is_enabled"])
    status = "enabled" if rule.is_enabled else "disabled"
    messages.success(request, f"Rule {status}.")
    return redirect("social_media:bot_settings")


# ─── Bot Analytics ────────────────────────────────────────────────────────────


@login_required
def bot_analytics(request):
    """View AI bot analytics — messages processed, replies sent, classifications."""
    company = getattr(request, "company", None)
    logs = []
    analytics = {}

    if company:
        from .bot_handler import SocialMediaBotHandler
        handler = SocialMediaBotHandler(company)
        analytics = handler.get_analytics(days=7)
        logs = BotConversationLog.objects.filter(
            account__company=company
        ).select_related("account", "message")[:50]

    return render(request, "social_media/bot_analytics.html", {
        "logs": logs,
        "analytics": analytics,
    })


# ─── Connection Testing ──────────────────────────────────────────────────────


@company_admin_required
@require_POST
def test_connection(request, pk):
    """Test if a social media account connection is working."""
    account = get_object_or_404(SocialMediaAccount, pk=pk, company=request.company)

    from integrations.utils import decrypt_token
    import requests as http_requests

    token = None
    if account.access_token_enc:
        try:
            token = decrypt_token(account.access_token_enc)
        except Exception:
            account.status = "error"
            account.last_test_result = "Token decryption failed"
            account.last_tested_at = timezone.now()
            account.save()
            return JsonResponse({"success": False, "error": "Token decryption failed"})

    if not token:
        account.status = "disconnected"
        account.last_test_result = "No access token configured"
        account.last_tested_at = timezone.now()
        account.save()
        return JsonResponse({"success": False, "error": "No access token configured"})

    success = False
    error_msg = ""

    try:
        if account.platform == "whatsapp":
            # Test WhatsApp Business API
            url = f"https://graph.facebook.com/v18.0/{account.phone_number_id or 'me'}"
            resp = http_requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=10)
            success = resp.status_code == 200
            error_msg = resp.json().get("error", {}).get("message", "") if not success else ""

        elif account.platform == "facebook":
            # Test Facebook Graph API
            url = f"https://graph.facebook.com/v18.0/{account.page_id or 'me'}?fields=id,name"
            resp = http_requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=10)
            success = resp.status_code == 200
            error_msg = resp.json().get("error", {}).get("message", "") if not success else ""

        elif account.platform == "instagram":
            # Test Instagram Graph API
            url = f"https://graph.facebook.com/v18.0/{account.page_id or 'me'}?fields=id,username"
            resp = http_requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=10)
            success = resp.status_code == 200
            error_msg = resp.json().get("error", {}).get("message", "") if not success else ""

        elif account.platform == "linkedin":
            # Test LinkedIn API
            url = "https://api.linkedin.com/v2/userinfo"
            resp = http_requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=10)
            success = resp.status_code == 200
            error_msg = "Invalid token or insufficient permissions" if not success else ""

        elif account.platform == "telegram":
            # Test Telegram Bot API
            url = f"https://api.telegram.org/bot{token}/getMe"
            resp = http_requests.get(url, timeout=10)
            data = resp.json()
            success = data.get("ok", False)
            if success:
                bot_info = data.get("result", {})
                account.telegram_bot_username = bot_info.get("username", "")
            else:
                error_msg = data.get("description", "Invalid bot token")

        else:
            error_msg = "Unknown platform"

    except http_requests.Timeout:
        error_msg = "Connection timed out"
    except http_requests.ConnectionError:
        error_msg = "Could not reach platform API"
    except Exception as e:
        error_msg = str(e)[:200]

    # Update account status
    if success:
        account.status = "active"
        account.last_test_result = "Connection successful"
    else:
        account.status = "error"
        account.last_test_result = error_msg or "Connection failed"

    account.last_tested_at = timezone.now()
    account.save()

    return JsonResponse({
        "success": success,
        "status": account.status,
        "message": account.last_test_result,
    })
