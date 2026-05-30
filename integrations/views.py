import logging
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
    decrypt_token,
    encrypt_token,
    exchange_code_for_tokens,
    get_auth_url,
    get_scopes_for_integration,
    graph_get,
    _get_company_ms_creds,
)
from companies.middleware import log_activity

logger = logging.getLogger(__name__)


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

    # Build Microsoft feature toggles context
    ms_integration = integrations.get("microsoft")
    enabled_features = []
    if ms_integration and hasattr(ms_integration, "enabled_ms_features"):
        enabled_features = ms_integration.enabled_ms_features or []
    ms_features = []
    for key, info in settings.MS_FEATURE_SCOPES.items():
        ms_features.append({
            "key": key,
            "label": info["label"],
            "icon": info["icon"],
            "description": info["description"],
            "enabled": key in enabled_features,
        })

    return render(request, "integrations/connect.html", {
        "integrations": integrations,
        "is_admin": is_admin,
        "ms_redirect_uri": settings.MS_REDIRECT_URI,
        "calendly_redirect_uri": settings.CALENDLY_REDIRECT_URI,
        "google_redirect_uri": settings.GOOGLE_REDIRECT_URI,
        # Google is truly connected only when token exists and status is active
        "google_truly_connected": (
            "google" in integrations
            and getattr(integrations["google"], "access_token_enc", None)
            and getattr(integrations["google"], "status", "") == "active"
        ),
        "coming_soon": [
            ("onedrive", "bi bi-cloud", "OneDrive"),
        ],
    })


@company_admin_required
def microsoft_save_credentials(request):
    """AJAX endpoint: save Azure App Registration credentials for this company."""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Method not allowed."}, status=405)

    client_id = request.POST.get("client_id", "").strip()
    client_secret = request.POST.get("client_secret", "").strip()
    tenant_id = request.POST.get("tenant_id", "").strip() or "common"

    if not client_id or not client_secret:
        return JsonResponse({"success": False, "error": "Client ID and Client Secret are required."})

    company = request.company
    integration, _ = CompanyIntegration.objects.get_or_create(
        company=company, service="microsoft"
    )
    integration.ms_client_id_enc = encrypt_token(client_id)
    integration.ms_client_secret_enc = encrypt_token(client_secret)
    integration.ms_tenant_id = tenant_id
    # Auto-enable all features — no manual selection required
    integration.enabled_ms_features = list(settings.MS_FEATURE_SCOPES.keys())
    integration.save()

    log_activity(request, "integration_credentials_saved", "microsoft", "Azure App credentials saved")
    return JsonResponse({"success": True})


@company_admin_required
@require_POST
def microsoft_save_features(request):
    """AJAX endpoint: save which Microsoft features this company wants enabled."""
    import json as _json

    try:
        body = _json.loads(request.body)
        features = body.get("features", [])
    except (ValueError, AttributeError):
        features = request.POST.getlist("features")

    # Validate feature keys against settings
    valid_keys = set(settings.MS_FEATURE_SCOPES.keys())
    features = [f for f in features if f in valid_keys]

    if not features:
        return JsonResponse({"success": False, "error": "Please enable at least one feature."})

    company = request.company
    integration, _ = CompanyIntegration.objects.get_or_create(
        company=company, service="microsoft"
    )
    old_features = set(integration.enabled_ms_features or [])
    integration.enabled_ms_features = features
    integration.save()

    # Check if new features were added that require re-authentication
    new_features = set(features) - old_features
    needs_reauth = bool(new_features) and integration.access_token_enc

    log_activity(request, "ms_features_updated", "microsoft", f"Features: {', '.join(features)}")
    return JsonResponse({
        "success": True,
        "features": features,
        "needs_reauth": needs_reauth,
        "message": "Features saved! Re-authenticate to grant new permissions." if needs_reauth else "Features saved!",
    })


@company_admin_required
def microsoft_connect(request):
    """Redirect user to Microsoft OAuth consent screen using per-company creds."""
    company = request.company
    try:
        integration = CompanyIntegration.objects.get(company=company, service="microsoft")
        client_id, client_secret, tenant_id = _get_company_ms_creds(integration)
    except (CompanyIntegration.DoesNotExist, ValueError):
        messages.error(request, "Please save your Azure App credentials first.")
        return redirect("integrations:connect")

    state = secrets.token_urlsafe(16)
    request.session["ms_oauth_state"] = state
    auth_url = get_auth_url(state, client_id, client_secret, tenant_id, integration=integration)
    return redirect(auth_url)


@company_admin_required
def microsoft_callback(request):
    """Handle OAuth callback from Microsoft Identity Platform."""
    logger = logging.getLogger(__name__)

    error = request.GET.get("error")
    if error:
        logger.error("Microsoft OAuth error: %s — %s", error, request.GET.get("error_description", ""))
        messages.error(request, "Microsoft login failed. Please check your Azure App configuration and try again.")
        return redirect("integrations:connect")

    state = request.GET.get("state")
    if state != request.session.pop("ms_oauth_state", None):
        messages.error(request, "Invalid OAuth state. Please try again.")
        return redirect("integrations:connect")

    code = request.GET.get("code")
    if not code:
        messages.error(request, "No authorization code received.")
        return redirect("integrations:connect")

    # Load per-company creds for token exchange
    company = request.company
    try:
        integration = CompanyIntegration.objects.get(company=company, service="microsoft")
        client_id, client_secret, tenant_id = _get_company_ms_creds(integration)
    except (CompanyIntegration.DoesNotExist, ValueError):
        messages.error(request, "Azure App credentials missing. Please re-configure.")
        return redirect("integrations:connect")

    result = exchange_code_for_tokens(code, client_id, client_secret, tenant_id, integration=integration)

    if "error" in result:
        raw_desc = result.get("error_description", result["error"])
        logger.error("Microsoft token exchange failed: %s", raw_desc)

        # Map common Azure AD errors to friendly messages
        error_code = result.get("error", "")
        if "7000215" in raw_desc or "Invalid client secret" in raw_desc:
            friendly = ("Invalid client secret. Make sure you copied the secret "
                        "\"Value\" (not the \"Secret ID\") from Azure portal → "
                        "Certificates & secrets.")
        elif "700016" in raw_desc or "not found in the directory" in raw_desc:
            friendly = "Application (Client) ID not found. Please verify your Client ID in Azure portal."
        elif "7000112" in raw_desc or "disabled" in raw_desc:
            friendly = "Your Azure application is disabled. Please enable it in Azure portal."
        elif "70011" in raw_desc or "redirect" in raw_desc.lower():
            friendly = "Redirect URI mismatch. Verify the redirect URI in your Azure App matches exactly."
        elif error_code == "invalid_grant":
            friendly = "Authorization expired. Please try connecting again."
        else:
            friendly = "Connection failed. Please verify your Azure App credentials and try again."

        messages.error(request, friendly)
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


# ── Google Workspace OAuth (dynamic per-company credentials) ──────────────────

from .google_utils import (
    get_google_auth_url,
    exchange_google_code,
    get_google_user_info,
    _get_company_google_creds,
)


@company_admin_required
@require_POST
def google_save_credentials(request):
    """
    AJAX endpoint: save Google OAuth app credentials (client_id, client_secret)
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
        company=company, service="google"
    )
    integration.google_client_id_enc = encrypt_token(client_id)
    integration.google_client_secret_enc = encrypt_token(client_secret)
    integration.connected_by = request.user
    integration.status = "pending"  # Will be set to 'active' only after OAuth completes
    integration.save()

    # Generate OAuth state and build authorization URL
    state = secrets.token_urlsafe(16)
    request.session["google_oauth_state"] = state
    auth_url = get_google_auth_url(state, client_id)

    log_activity(request, "google_credentials_saved", "google", f"Company: {company.name}")
    return JsonResponse({
        "ok": True,
        "message": "Credentials saved! Redirecting to Google for authorization…",
        "redirect_url": auth_url,
    })


@company_admin_required
def google_connect(request):
    """Redirect user to Google OAuth consent screen using stored credentials."""
    company = request.company
    integration = CompanyIntegration.objects.filter(company=company, service="google").first()

    if not integration or not integration.google_client_id_enc:
        messages.error(request, "Please enter your Google Workspace credentials first.")
        return redirect("integrations:connect")

    from .utils import decrypt_token as _dec
    client_id = _dec(integration.google_client_id_enc)

    state = secrets.token_urlsafe(16)
    request.session["google_oauth_state"] = state
    auth_url = get_google_auth_url(state, client_id)
    return redirect(auth_url)


@company_admin_required
def google_callback(request):
    """Handle OAuth callback from Google."""
    error = request.GET.get("error")
    if error:
        err_desc = request.GET.get("error_description", error)
        logger.error("[Google OAuth] Authorization denied: %s — %s", error, err_desc)
        messages.error(request, f"Google login failed: {err_desc}")
        return redirect("integrations:connect")

    state = request.GET.get("state")
    stored_state = request.session.pop("google_oauth_state", None)
    if state != stored_state:
        logger.error(
            "[Google OAuth] State mismatch — received: %s  stored: %s  (session may have expired)",
            state, stored_state,
        )
        messages.error(request, "Invalid OAuth state. Please try again (session may have expired).")
        return redirect("integrations:connect")

    code = request.GET.get("code")
    if not code:
        logger.error("[Google OAuth] Callback received but no authorization code in params: %s", dict(request.GET))
        messages.error(request, "No authorization code received.")
        return redirect("integrations:connect")

    # Get per-company credentials from DB
    company = request.company
    integration = CompanyIntegration.objects.filter(company=company, service="google").first()
    if not integration or not integration.google_client_id_enc:
        logger.error("[Google OAuth] No credentials found for company %s", company)
        messages.error(request, "Google credentials not found. Please reconfigure.")
        return redirect("integrations:connect")

    try:
        client_id, client_secret = _get_company_google_creds(integration)
    except ValueError as e:
        logger.error("[Google OAuth] Failed to decrypt credentials for company %s: %s", company, e)
        messages.error(request, str(e))
        return redirect("integrations:connect")

    result = exchange_google_code(code, client_id, client_secret)
    logger.info("[Google OAuth] Token exchange response keys: %s", list(result.keys()))

    if "access_token" not in result:
        err_msg = result.get("error_description", result.get("error", "unknown"))
        logger.error(
            "[Google OAuth] Token exchange FAILED for company %s: %s — full response: %s",
            company, err_msg, result,
        )
        messages.error(request, f"Google token exchange failed: {err_msg}")
        return redirect("integrations:connect")

    access_token = result["access_token"]
    refresh_token = result.get("refresh_token", "")
    expires_in = result.get("expires_in", 3600)

    from datetime import datetime as dt, timezone as tz
    expiry = dt.fromtimestamp(dt.now(tz.utc).timestamp() + expires_in, tz=tz.utc)

    # Fetch user's Google profile
    try:
        user_info = get_google_user_info(access_token)
        display_name = user_info.get("name", "")
        email = user_info.get("email", "")
    except Exception as e:
        logger.warning("[Google OAuth] Could not fetch user profile: %s", e)
        display_name, email = "", ""

    integration.access_token_enc = encrypt_token(access_token)
    integration.refresh_token_enc = encrypt_token(refresh_token) if refresh_token else integration.refresh_token_enc
    integration.token_expiry = expiry
    integration.google_account_name = display_name
    integration.google_account_email = email
    integration.connected_by = request.user
    integration.status = "active"
    integration.save()

    logger.info("[Google OAuth] ✓ Connected successfully for company %s — account: %s", company, email)
    messages.success(request, f"Google Workspace connected for {company.name}! ({email})")
    log_activity(request, "integration_connected", "google", f"Account: {email}")
    return redirect("integrations:connect")


@company_admin_required
def google_disconnect(request):
    """Remove stored Google tokens and credentials for this company."""
    CompanyIntegration.objects.filter(company=request.company, service="google").delete()
    log_activity(request, "integration_disconnected", "google")
    messages.info(request, "Google Workspace disconnected.")
    return redirect("integrations:connect")


# ── Discord ───────────────────────────────────────────────────────────────────


@company_admin_required
@require_POST
def discord_save_credentials(request):
    """Save Discord bot credentials manually (token-based connection)."""
    bot_token = request.POST.get("discord_bot_token", "").strip()
    guild_id = request.POST.get("discord_guild_id", "").strip()
    webhook_url = request.POST.get("discord_webhook_url", "").strip()

    if not bot_token:
        messages.error(request, "Discord Bot Token is required.")
        return redirect("integrations:connect")

    # Verify the bot token by calling Discord API
    headers = {"Authorization": f"Bot {bot_token}"}
    try:
        resp = http_requests.get("https://discord.com/api/v10/users/@me", headers=headers, timeout=10)
        if resp.status_code != 200:
            messages.error(request, "Invalid Bot Token — Discord rejected it.")
            return redirect("integrations:connect")
        bot_info = resp.json()
    except Exception:
        messages.error(request, "Could not connect to Discord API.")
        return redirect("integrations:connect")

    # Get guild name if guild_id provided
    guild_name = ""
    if guild_id:
        try:
            resp = http_requests.get(
                f"https://discord.com/api/v10/guilds/{guild_id}",
                headers=headers, timeout=10
            )
            if resp.status_code == 200:
                guild_name = resp.json().get("name", "")
        except Exception:
            pass

    company = request.company
    integration, _ = CompanyIntegration.objects.update_or_create(
        company=company, service="discord",
        defaults={
            "discord_bot_token_enc": encrypt_token(bot_token),
            "discord_guild_id": guild_id,
            "discord_guild_name": guild_name or bot_info.get("username", ""),
            "discord_webhook_url": webhook_url,
            "access_token_enc": encrypt_token(bot_token),
            "connected_by": request.user,
            "status": "active",
        },
    )
    messages.success(request, f"Discord connected! Bot: {bot_info.get('username', 'Bot')}")
    log_activity(request, "integration_connected", "discord", f"Guild: {guild_name or guild_id}")
    return redirect("integrations:connect")


@company_admin_required
@require_POST
def discord_disconnect(request):
    """Disconnect Discord integration."""
    CompanyIntegration.objects.filter(company=request.company, service="discord").delete()
    log_activity(request, "integration_disconnected", "discord")
    messages.info(request, "Discord disconnected.")
    return redirect("integrations:connect")


# ── Jira ──────────────────────────────────────────────────────────────────────


@company_admin_required
@require_POST
def jira_save_credentials(request):
    """Save Jira credentials (API Token + site URL)."""
    site_url = request.POST.get("jira_site_url", "").strip().rstrip("/")
    user_email = request.POST.get("jira_user_email", "").strip()
    api_token = request.POST.get("jira_api_token", "").strip()
    project_key = request.POST.get("jira_project_key", "").strip()

    if not site_url or not user_email or not api_token:
        messages.error(request, "Jira Site URL, Email, and API Token are all required.")
        return redirect("integrations:connect")

    # Verify credentials by calling Jira API
    import base64
    auth_str = base64.b64encode(f"{user_email}:{api_token}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_str}",
        "Content-Type": "application/json",
    }
    try:
        resp = http_requests.get(f"{site_url}/rest/api/3/myself", headers=headers, timeout=10)
        if resp.status_code != 200:
            messages.error(request, "Invalid Jira credentials — authentication failed.")
            return redirect("integrations:connect")
        jira_user = resp.json()
    except Exception:
        messages.error(request, "Could not connect to Jira API. Check site URL.")
        return redirect("integrations:connect")

    company = request.company
    integration, _ = CompanyIntegration.objects.update_or_create(
        company=company, service="jira",
        defaults={
            "jira_site_url": site_url,
            "jira_user_email": user_email,
            "jira_api_token_enc": encrypt_token(api_token),
            "jira_project_key": project_key,
            "access_token_enc": encrypt_token(api_token),
            "connected_by": request.user,
            "status": "active",
        },
    )
    display_name = jira_user.get("displayName", user_email)
    messages.success(request, f"Jira connected! User: {display_name}")
    log_activity(request, "integration_connected", "jira", f"Site: {site_url}")
    return redirect("integrations:connect")


@company_admin_required
@require_POST
def jira_disconnect(request):
    """Disconnect Jira integration."""
    CompanyIntegration.objects.filter(company=request.company, service="jira").delete()
    log_activity(request, "integration_disconnected", "jira")
    messages.info(request, "Jira disconnected.")
    return redirect("integrations:connect")
