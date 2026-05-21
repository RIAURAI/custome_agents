from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.functional import SimpleLazyObject


def _get_active_membership(request):
    if not request.user.is_authenticated:
        return None
    return (
        request.user.memberships.filter(is_active=True)
        .select_related("company")
        .first()
    )


def _get_company(request):
    membership = request.membership
    return membership.company if membership else None


class CompanyMiddleware:
    """Attaches `request.membership` and `request.company` to every request.

    Phase 1: one company per user, so we pick the user's first active membership.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.membership = SimpleLazyObject(lambda: _get_active_membership(request))
        request.company = SimpleLazyObject(lambda: _get_company(request))
        return self.get_response(request)


def company_context(request):
    """Expose membership/company and platform access flags in all templates."""
    membership = getattr(request, "membership", None)
    is_superuser = getattr(request, "user", None) and request.user.is_authenticated and request.user.is_superuser
    ctx = {
        "current_company": getattr(request, "company", None),
        "current_membership": membership,
    }
    # Superusers get full access to everything
    if is_superuser:
        ctx["has_ms_access"] = True
        ctx["has_slack_access"] = True
    elif membership:
        ctx["has_ms_access"] = bool(has_platform_access(request, "microsoft"))
        ctx["has_slack_access"] = bool(has_platform_access(request, "slack"))
    else:
        ctx["has_ms_access"] = False
        ctx["has_slack_access"] = False
    return ctx


# ── Permission helpers ────────────────────────────────────────────────────────

def has_platform_access(request, service, min_permission="view"):
    """Check if the current user has at least `min_permission` on the given service.

    Admins/owners always have full access.
    Returns the PlatformAccess object if granted, True for admins, or None.
    """
    from companies.models import PlatformAccess

    membership = getattr(request, "membership", None)
    if not membership:
        return None

    # Admins always have full access
    if membership.is_admin:
        return True

    perm_levels = ["view", "reply", "manage"]
    min_index = perm_levels.index(min_permission) if min_permission in perm_levels else 0

    access = PlatformAccess.objects.filter(
        membership=membership,
        integration__service=service,
        integration__status="active",
    ).first()

    if not access:
        return None

    access_index = perm_levels.index(access.permission) if access.permission in perm_levels else -1
    return access if access_index >= min_index else None


def platform_access_required(service, min_permission="view"):
    """Decorator: user must have at least `min_permission` on the given platform."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not has_platform_access(request, service, min_permission):
                messages.error(request, f"You don't have access to {service}. Contact your admin.")
                return redirect("dashboard:home")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# ── Activity logging ──────────────────────────────────────────────────────────

def log_activity(request, action, platform="", detail=""):
    """Log a user action to the ActivityLog.

    Can be called from any view. Gracefully no-ops if there's no company context.
    """
    from companies.models import ActivityLog

    company = getattr(request, "company", None)
    if not company:
        return None

    ip = _get_client_ip(request)
    return ActivityLog.objects.create(
        company=company,
        user=request.user if request.user.is_authenticated else None,
        action=action,
        platform=platform,
        detail=detail[:500],
        ip_address=ip,
    )


def _get_client_ip(request):
    """Extract client IP from request, respecting X-Forwarded-For."""
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
