import secrets
from datetime import datetime, timezone
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

import requests as http_requests

from .models import CompanyIntegration, UserIntegration
from .utils import (
    encrypt_token,
    exchange_code_for_tokens,
    get_auth_url,
    graph_get,
)
from companies.middleware import log_activity


def company_admin_required(view_func):
    """Decorator: user must be logged in AND be a company owner/admin."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        membership = getattr(request, "membership", None)
        if not membership or not membership.is_admin:
            messages.error(request, "Only company admins can manage integrations.")
            return redirect("integrations:connect")
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
def connect_view(request):
    """Show all integration cards with connect / disconnect status."""
    company = getattr(request, "company", None)
    integrations = {}
    if company:
        integrations = {
            i.service: i for i in company.integrations.all()
        }
    # Fallback: show UserIntegration if no CompanyIntegration exists for Slack
    if "slack" not in integrations:
        user_slack = UserIntegration.objects.filter(
            user=request.user, service="slack"
        ).first()
        if user_slack and user_slack.access_token_enc:
            integrations["slack"] = user_slack
    membership = getattr(request, "membership", None)
    is_admin = membership.is_admin if membership else False
    return render(request, "integrations/connect.html", {
        "integrations": integrations,
        "is_admin": is_admin,
        "calendly_redirect_uri": settings.CALENDLY_REDIRECT_URI,
        "coming_soon": [
            ("onedrive", "bi bi-cloud", "OneDrive"),
            ("chatgpt", "bi bi-robot", "ChatGPT Pro"),
        ],
    })


@company_admin_required
def microsoft_connect(request):
    """Redirect user to Microsoft OAuth consent screen."""
    state = secrets.token_urlsafe(16)
    request.session["ms_oauth_state"] = state
    auth_url = get_auth_url(state)
    return redirect(auth_url)


@company_admin_required
def microsoft_callback(request):
    """Handle OAuth callback from Microsoft Identity Platform."""
    error = request.GET.get("error")
    if error:
        messages.error(request, f"Microsoft login failed: {request.GET.get('error_description', error)}")
        return redirect("integrations:connect")

    state = request.GET.get("state")
    if state != request.session.pop("ms_oauth_state", None):
        messages.error(request, "Invalid OAuth state. Please try again.")
        return redirect("integrations:connect")

    code = request.GET.get("code")
    if not code:
        messages.error(request, "No authorization code received.")
        return redirect("integrations:connect")

    result = exchange_code_for_tokens(code)

    if "error" in result:
        messages.error(request, f"Token exchange failed: {result.get('error_description', result['error'])}")
        return redirect("integrations:connect")

    access_token = result["access_token"]
    refresh_token = result.get("refresh_token", "")
    expires_in = result.get("expires_in", 3600)
    expiry = datetime.fromtimestamp(
        datetime.now(timezone.utc).timestamp() + expires_in,
        tz=timezone.utc,
    )

    # Fetch user's Microsoft profile
    try:
        me = graph_get(access_token, "/me")
        display_name = me.get("displayName", "")
        email = me.get("mail") or me.get("userPrincipalName", "")
    except Exception:
        display_name, email = "", ""

    company = request.company
    integration, _ = CompanyIntegration.objects.get_or_create(
        company=company, service="microsoft"
    )
    integration.access_token_enc = encrypt_token(access_token)
    integration.refresh_token_enc = encrypt_token(refresh_token) if refresh_token else integration.refresh_token_enc
    integration.token_expiry = expiry
    integration.ms_account_name = display_name
    integration.ms_account_email = email
    integration.connected_by = request.user
    integration.status = "active"
    integration.save()

    messages.success(request, f"Microsoft account connected for {company.name}! ({email})")
    log_activity(request, "integration_connected", "microsoft", f"Account: {email}")
    return redirect("integrations:connect")


@company_admin_required
def microsoft_disconnect(request):
    """Remove stored Microsoft tokens for this company."""
    CompanyIntegration.objects.filter(company=request.company, service="microsoft").delete()
    log_activity(request, "integration_disconnected", "microsoft")
    messages.info(request, "Microsoft account disconnected.")
    return redirect("integrations:connect")


# ── Slack OAuth ───────────────────────────────────────────────────────────────

from .slack_utils import get_slack_auth_url, exchange_slack_code


@company_admin_required
def slack_connect(request):
    """Redirect user to Slack OAuth consent screen."""
    state = secrets.token_urlsafe(16)
    request.session["slack_oauth_state"] = state
    auth_url = get_slack_auth_url(state)
    return redirect(auth_url)


@company_admin_required
def slack_callback(request):
    """Handle OAuth callback from Slack."""
    error = request.GET.get("error")
    if error:
        messages.error(request, f"Slack login failed: {error}")
        return redirect("integrations:connect")

    state = request.GET.get("state")
    if state != request.session.pop("slack_oauth_state", None):
        messages.error(request, "Invalid OAuth state. Please try again.")
        return redirect("integrations:connect")

    code = request.GET.get("code")
    if not code:
        messages.error(request, "No authorization code received.")
        return redirect("integrations:connect")

    result = exchange_slack_code(code)

    if not result.get("ok"):
        messages.error(request, f"Slack token exchange failed: {result.get('error', 'unknown')}")
        return redirect("integrations:connect")

    access_token = result.get("access_token", "")
    team = result.get("team", {})
    authed_user = result.get("authed_user", {})

    company = request.company
    integration, _ = CompanyIntegration.objects.get_or_create(
        company=company, service="slack"
    )
    integration.access_token_enc = encrypt_token(access_token)
    integration.slack_team_id = team.get("id", "")
    integration.slack_team_name = team.get("name", "")
    integration.slack_user_id = authed_user.get("id", "")
    integration.connected_by = request.user
    integration.status = "active"
    integration.save()

    messages.success(request, f"Slack connected for {company.name}! Workspace: {team.get('name', 'Unknown')}")
    log_activity(request, "integration_connected", "slack", f"Workspace: {team.get('name', '')}")
    return redirect("integrations:connect")


@login_required
@require_POST
def slack_disconnect(request):
    """Remove stored Slack tokens for this company and user."""
    company = getattr(request, "company", None)
    if company:
        CompanyIntegration.objects.filter(company=company, service="slack").delete()
    # Also remove UserIntegration
    UserIntegration.objects.filter(user=request.user, service="slack").delete()
    log_activity(request, "integration_disconnected", "slack")
    messages.info(request, "Slack account disconnected.")
    return redirect("integrations:connect")


# ── Slack Manual Connect (dynamic credentials per user) ───────────────────────

@login_required
@require_POST
def slack_manual_connect(request):
    """
    Accept a Bot Token (and optional App Token) entered by the user,
    validate them against Slack's auth.test API, then encrypt and save
    per-user.  Returns JSON so the page can update without a full reload.
    """
    bot_token = request.POST.get("bot_token", "").strip()
    app_token = request.POST.get("app_token", "").strip()

    if not bot_token:
        return JsonResponse({"ok": False, "error": "Bot token is required."}, status=400)

    # Basic format check — bot tokens start with xoxb-
    if not bot_token.startswith("xoxb-"):
        return JsonResponse(
            {"ok": False, "error": "Invalid bot token format. Bot tokens must start with xoxb-"},
            status=400,
        )

    if app_token and not app_token.startswith("xapp-"):
        return JsonResponse(
            {"ok": False, "error": "Invalid app token format. App tokens must start with xapp-"},
            status=400,
        )

    signing_secret = request.POST.get("signing_secret", "").strip()
    # Signing secret is a 32-char hex string — no specific prefix, just validate length
    if signing_secret and len(signing_secret) < 16:
        return JsonResponse(
            {"ok": False, "error": "Signing secret looks too short. Copy it exactly from Basic Information."},
            status=400,
        )

    user_token = request.POST.get("user_token", "").strip()
    if user_token and not user_token.startswith("xoxp-"):
        return JsonResponse(
            {"ok": False, "error": "Invalid user token format. User OAuth tokens start with xoxp-"},
            status=400,
        )

    # Validate bot token with Slack
    try:
        resp = http_requests.post(
            "https://slack.com/api/auth.test",
            headers={"Authorization": f"Bearer {bot_token}"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        return JsonResponse({"ok": False, "error": f"Could not reach Slack API: {exc}"}, status=502)

    if not data.get("ok"):
        slack_err = data.get("error", "unknown")
        friendly = {
            "invalid_auth": "The bot token is invalid. Please check and try again.",
            "account_inactive": "This Slack account is inactive.",
            "token_revoked": "This token has been revoked.",
            "not_allowed_token_type": "Wrong token type — please use a Bot Token (xoxb-…).",
        }.get(slack_err, f"Slack rejected the token: {slack_err}")
        return JsonResponse({"ok": False, "error": friendly}, status=400)

    # Persist encrypted credentials — per-user (legacy) + per-company (primary)

    # Save to UserIntegration (per-user, backwards-compatible)
    user_integ, _ = UserIntegration.objects.get_or_create(
        user=request.user, service="slack"
    )
    user_integ.access_token_enc = encrypt_token(bot_token)
    user_integ.slack_team_id = data.get("team_id", "")
    user_integ.slack_team_name = data.get("team", "")
    user_integ.slack_user_id = data.get("user_id", "")
    user_integ.slack_bot_user_id = data.get("bot_id", "")
    if app_token:
        user_integ.slack_app_token_enc = encrypt_token(app_token)
    if signing_secret:
        user_integ.slack_signing_secret_enc = encrypt_token(signing_secret)
    if user_token:
        user_integ.slack_user_token_enc = encrypt_token(user_token)
    user_integ.save()

    # Save to CompanyIntegration (company-level — used by Slack pages & bot)
    company = getattr(request, "company", None)
    if company:
        company_integ, _ = CompanyIntegration.objects.get_or_create(
            company=company, service="slack"
        )
        company_integ.access_token_enc = encrypt_token(bot_token)
        company_integ.slack_team_id = data.get("team_id", "")
        company_integ.slack_team_name = data.get("team", "")
        company_integ.slack_user_id = data.get("user_id", "")
        company_integ.slack_bot_user_id = data.get("bot_id", "")
        if app_token:
            company_integ.slack_app_token_enc = encrypt_token(app_token)
        if signing_secret:
            company_integ.slack_signing_secret_enc = encrypt_token(signing_secret)
        if user_token:
            company_integ.slack_user_token_enc = encrypt_token(user_token)
        company_integ.connected_by = request.user
        company_integ.status = "active"
        company_integ.save()

    # Auto-start bot in background thread if app_token provided
    if app_token:
        import threading
        def _auto_start():
            try:
                from slack_hub.bot_service import run_bot
                run_bot()
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Bot auto-start failed: {e}")
        t = threading.Thread(target=_auto_start, daemon=True, name="slack-bot-connect")
        t.start()

    return JsonResponse({
        "ok": True,
        "team_name": data.get("team", ""),
        "team_id": data.get("team_id", ""),
        "user_id": data.get("user_id", ""),
        "connected_at": user_integ.connected_at.strftime("%b %-d, %Y"),
    })


# ── Calendly OAuth (dynamic per-company credentials) ─────────────────────────

from .calendly_utils import (
    get_calendly_auth_url,
    exchange_calendly_code,
    calendly_api_get,
    _get_company_calendly_creds,
)


@company_admin_required
@require_POST
def calendly_save_credentials(request):
    """
    AJAX endpoint: save Calendly OAuth app credentials (client_id, client_secret)
    for this company, then return a redirect URL to start OAuth.
    """
    client_id = request.POST.get("client_id", "").strip()
    client_secret = request.POST.get("client_secret", "").strip()

    if not client_id:
        return JsonResponse({"ok": False, "error": "Client ID is required."}, status=400)
    if not client_secret:
        return JsonResponse({"ok": False, "error": "Client Secret is required."}, status=400)

    company = request.company
    integration, _ = CompanyIntegration.objects.get_or_create(
        company=company, service="calendly"
    )
    integration.calendly_client_id_enc = encrypt_token(client_id)
    integration.calendly_client_secret_enc = encrypt_token(client_secret)
    integration.connected_by = request.user
    integration.save()

    # Generate OAuth state and build authorization URL
    state = secrets.token_urlsafe(16)
    request.session["calendly_oauth_state"] = state
    auth_url = get_calendly_auth_url(state, client_id)

    log_activity(request, "calendly_credentials_saved", "calendly", f"Company: {company.name}")
    return JsonResponse({
        "ok": True,
        "message": "Credentials saved! Redirecting to Calendly for authorization…",
        "redirect_url": auth_url,
    })


@company_admin_required
def calendly_connect(request):
    """Redirect user to Calendly OAuth consent screen using stored credentials."""
    company = request.company
    integration = CompanyIntegration.objects.filter(company=company, service="calendly").first()

    if not integration or not integration.calendly_client_id_enc:
        messages.error(request, "Please enter your Calendly credentials first.")
        return redirect("integrations:connect")

    from .utils import decrypt_token as _dec
    client_id = _dec(integration.calendly_client_id_enc)

    state = secrets.token_urlsafe(16)
    request.session["calendly_oauth_state"] = state
    auth_url = get_calendly_auth_url(state, client_id)
    return redirect(auth_url)


@company_admin_required
def calendly_callback(request):
    """Handle OAuth callback from Calendly."""
    error = request.GET.get("error")
    if error:
        messages.error(request, f"Calendly login failed: {request.GET.get('error_description', error)}")
        return redirect("integrations:connect")

    state = request.GET.get("state")
    if state != request.session.pop("calendly_oauth_state", None):
        messages.error(request, "Invalid OAuth state. Please try again.")
        return redirect("integrations:connect")

    code = request.GET.get("code")
    if not code:
        messages.error(request, "No authorization code received.")
        return redirect("integrations:connect")

    # Get per-company credentials from DB
    company = request.company
    integration = CompanyIntegration.objects.filter(company=company, service="calendly").first()
    if not integration or not integration.calendly_client_id_enc:
        messages.error(request, "Calendly credentials not found. Please reconfigure.")
        return redirect("integrations:connect")

    try:
        client_id, client_secret = _get_company_calendly_creds(integration)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("integrations:connect")

    result = exchange_calendly_code(code, client_id, client_secret)

    if "access_token" not in result:
        err_msg = result.get("error_description", result.get("error", "unknown"))
        messages.error(request, f"Calendly token exchange failed: {err_msg}")
        return redirect("integrations:connect")

    access_token = result["access_token"]
    refresh_token = result.get("refresh_token", "")
    expires_in = result.get("expires_in", 7200)

    from datetime import datetime as dt, timezone as tz
    expiry = dt.fromtimestamp(dt.now(tz.utc).timestamp() + expires_in, tz=tz.utc)

    # Fetch current user info from Calendly API
    try:
        user_info = calendly_api_get(access_token, "/users/me")
        resource = user_info.get("resource", {})
        user_uri = resource.get("uri", "")
        org_uri = resource.get("current_organization", "")
        user_name = resource.get("name", "")
    except Exception:
        user_uri, org_uri, user_name = "", "", ""

    integration.access_token_enc = encrypt_token(access_token)
    integration.refresh_token_enc = encrypt_token(refresh_token) if refresh_token else integration.refresh_token_enc
    integration.token_expiry = expiry
    integration.calendly_user_uri = user_uri
    integration.calendly_organization_uri = org_uri
    integration.connected_by = request.user
    integration.status = "active"
    integration.save()

    messages.success(request, f"Calendly connected for {company.name}! ({user_name})")
    log_activity(request, "integration_connected", "calendly", f"User: {user_name}")
    return redirect("integrations:connect")


@company_admin_required
def calendly_disconnect(request):
    """Remove stored Calendly tokens and credentials for this company."""
    CompanyIntegration.objects.filter(company=request.company, service="calendly").delete()
    log_activity(request, "integration_disconnected", "calendly")
    messages.info(request, "Calendly account disconnected.")
    return redirect("integrations:connect")
