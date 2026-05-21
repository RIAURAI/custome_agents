import secrets
from datetime import datetime, timezone
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import CompanyIntegration
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
    membership = getattr(request, "membership", None)
    is_admin = membership.is_admin if membership else False
    return render(request, "integrations/connect.html", {
        "integrations": integrations,
        "is_admin": is_admin,
        "coming_soon": [
            ("calendly", "bi bi-calendar-event", "Calendly"),
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


@company_admin_required
def slack_disconnect(request):
    """Remove stored Slack tokens for this company."""
    CompanyIntegration.objects.filter(company=request.company, service="slack").delete()
    log_activity(request, "integration_disconnected", "slack")
    messages.info(request, "Slack account disconnected.")
    return redirect("integrations:connect")
