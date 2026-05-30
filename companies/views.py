from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.functions import TruncDate, TruncHour, ExtractHour
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from integrations.models import CompanyIntegration

from .models import Company, Invitation, Membership, PlatformAccess, ActivityLog
from companies.middleware import log_activity


def _require_admin(request):
    """Return membership if user is company admin, else None."""
    membership = getattr(request, "membership", None)
    if membership and membership.is_admin:
        return membership
    return None


# ── Team Management ───────────────────────────────────────────────────────────

@login_required
def team_view(request):
    """Show company members, pending invites, and platform access grid."""
    membership = _require_admin(request)
    if not membership:
        messages.error(request, "Only company admins can manage the team.")
        return redirect("dashboard:home")

    company = request.company
    members = Membership.objects.filter(company=company, is_active=True).select_related("user")
    pending_invites = Invitation.objects.filter(company=company, status=Invitation.Status.PENDING)
    integrations = CompanyIntegration.objects.filter(company=company, status="active")

    # Build access grid: {membership_id: {integration_id: PlatformAccess}}
    access_grid = {}
    all_access = PlatformAccess.objects.filter(
        membership__company=company
    ).select_related("membership", "integration")
    for pa in all_access:
        access_grid.setdefault(pa.membership_id, {})[pa.integration_id] = pa

    return render(request, "companies/team.html", {
        "company": company,
        "members": members,
        "pending_invites": pending_invites,
        "integrations": integrations,
        "access_grid": access_grid,
        "role_choices": Membership.Role.choices,
        "permission_choices": PlatformAccess.Permission.choices,
    })


@login_required
def invite_member(request):
    """Send an invitation to join the company."""
    membership = _require_admin(request)
    if not membership:
        messages.error(request, "Only company admins can invite members.")
        return redirect("dashboard:home")

    if request.method != "POST":
        return redirect("companies:team")

    email = request.POST.get("email", "").strip().lower()
    role = request.POST.get("role", Membership.Role.MEMBER)

    if not email:
        messages.error(request, "Email is required.")
        return redirect("companies:team")

    if role not in dict(Membership.Role.choices):
        role = Membership.Role.MEMBER

    # Don't allow inviting existing members
    company = request.company
    if Membership.objects.filter(company=company, user__email=email, is_active=True).exists():
        messages.warning(request, f"{email} is already a member of {company.name}.")
        return redirect("companies:team")

    # Don't allow duplicate pending invites
    if Invitation.objects.filter(company=company, email=email, status=Invitation.Status.PENDING).exists():
        messages.warning(request, f"A pending invite already exists for {email}.")
        return redirect("companies:team")

    invitation = Invitation.objects.create(
        company=company,
        email=email,
        role=role,
        invited_by=request.user,
        expires_at=timezone.now() + timezone.timedelta(days=7),
    )

    # Build invite link (in production, send via email)
    invite_url = request.build_absolute_uri(f"/company/join/{invitation.token}/")
    messages.success(
        request,
        f"Invitation sent to {email}! Share this link: {invite_url}",
    )
    log_activity(request, "invite_sent", "", f"Invited {email} as {role}")
    return redirect("companies:team")


@login_required
def revoke_invite(request, token):
    """Revoke a pending invitation."""
    membership = _require_admin(request)
    if not membership:
        messages.error(request, "Only company admins can revoke invitations.")
        return redirect("dashboard:home")

    invitation = get_object_or_404(
        Invitation, token=token, company=request.company, status=Invitation.Status.PENDING
    )
    invitation.status = Invitation.Status.REVOKED
    invitation.save()
    messages.info(request, f"Invitation to {invitation.email} has been revoked.")
    return redirect("companies:team")


def accept_invite(request, token):
    """Accept an invitation — register or log in, then join the company."""
    invitation = get_object_or_404(Invitation, token=token)

    if not invitation.is_valid:
        if invitation.is_expired:
            invitation.status = Invitation.Status.EXPIRED
            invitation.save()
        return render(request, "companies/invite_invalid.html", {
            "reason": "expired" if invitation.is_expired else invitation.status,
        })

    # If user is already logged in and email matches
    if request.user.is_authenticated:
        if request.user.email.lower() == invitation.email:
            return _finalize_invite(request, invitation, request.user)
        # Different email — show a notice
        return render(request, "companies/invite_accept.html", {
            "invitation": invitation,
            "email_mismatch": True,
        })

    if request.method == "POST":
        # Simple registration inline
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()

        errors = []
        if not username:
            errors.append("Username is required.")
        if not password or len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if User.objects.filter(username=username).exists():
            errors.append("That username is already taken.")

        if errors:
            return render(request, "companies/invite_accept.html", {
                "invitation": invitation,
                "errors": errors,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
            })

        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=invitation.email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            return _finalize_invite(request, invitation, user)

    return render(request, "companies/invite_accept.html", {
        "invitation": invitation,
    })


def _finalize_invite(request, invitation, user):
    """Create membership from invitation and log user in."""
    from django.contrib.auth import login

    with transaction.atomic():
        membership, created = Membership.objects.get_or_create(
            user=user,
            company=invitation.company,
            defaults={
                "role": invitation.role,
                "invited_at": invitation.created_at,
            },
        )
        if not created:
            messages.info(request, f"You're already a member of {invitation.company.name}.")
        else:
            messages.success(
                request,
                f"Welcome to {invitation.company.name}! You've joined as {invitation.get_role_display()}.",
            )
        invitation.status = Invitation.Status.ACCEPTED
        invitation.save()

    login(request, user)
    # Log after login so request.company is available via middleware on next request
    # We log directly since we have the company from invitation
    from companies.models import ActivityLog
    ActivityLog.objects.create(
        company=invitation.company,
        user=user,
        action="invite_accepted",
        detail=f"Joined as {invitation.get_role_display()}",
    )
    return redirect("dashboard:home")


# ── Access Control ────────────────────────────────────────────────────────────

@login_required
def manage_access(request, membership_id):
    """Grant or update platform access for a member."""
    admin_membership = _require_admin(request)
    if not admin_membership:
        messages.error(request, "Only company admins can manage access.")
        return redirect("dashboard:home")

    target = get_object_or_404(
        Membership, id=membership_id, company=request.company, is_active=True
    )

    if request.method != "POST":
        return redirect("companies:team")

    company = request.company
    integrations = CompanyIntegration.objects.filter(company=company, status="active")

    for integration in integrations:
        perm_key = f"perm_{integration.id}"
        perm_value = request.POST.get(perm_key, "")

        if perm_value and perm_value in dict(PlatformAccess.Permission.choices):
            PlatformAccess.objects.update_or_create(
                membership=target,
                integration=integration,
                defaults={
                    "permission": perm_value,
                    "granted_by": request.user,
                },
            )
        elif not perm_value:
            # Remove access if unchecked
            PlatformAccess.objects.filter(
                membership=target, integration=integration
            ).delete()

    messages.success(request, f"Access updated for {target.user.get_full_name() or target.user.username}.")
    log_activity(request, "access_updated", "", f"Updated access for {target.user.username}")
    return redirect("companies:team")


@login_required
def remove_member(request, membership_id):
    """Deactivate a member from the company."""
    admin_membership = _require_admin(request)
    if not admin_membership:
        messages.error(request, "Only company admins can remove members.")
        return redirect("dashboard:home")

    target = get_object_or_404(
        Membership, id=membership_id, company=request.company, is_active=True
    )

    # Can't remove yourself or the owner
    if target.user == request.user:
        messages.error(request, "You cannot remove yourself.")
        return redirect("companies:team")
    if target.is_owner:
        messages.error(request, "The company owner cannot be removed.")
        return redirect("companies:team")

    target.is_active = False
    target.save()
    # Also revoke all platform access
    PlatformAccess.objects.filter(membership=target).delete()

    messages.info(request, f"{target.user.get_full_name() or target.user.username} has been removed.")
    log_activity(request, "member_removed", "", f"Removed {target.user.username}")
    return redirect("companies:team")


# ── Activity Log ──────────────────────────────────────────────────────────────

@login_required
def activity_log_view(request):
    """Show company activity log (admin only)."""
    membership = _require_admin(request)
    if not membership:
        messages.error(request, "Only company admins can view the activity log.")
        return redirect("dashboard:home")

    company = request.company
    logs = ActivityLog.objects.filter(company=company).select_related("user")

    # Filters
    user_filter = request.GET.get("user", "")
    platform_filter = request.GET.get("platform", "")
    action_filter = request.GET.get("action", "")

    if user_filter:
        logs = logs.filter(user_id=user_filter)
    if platform_filter:
        logs = logs.filter(platform=platform_filter)
    if action_filter:
        logs = logs.filter(action=action_filter)

    logs = logs[:200]

    # Get filter options
    members = Membership.objects.filter(company=company, is_active=True).select_related("user")
    action_choices = ActivityLog.Action.choices

    return render(request, "companies/activity_log.html", {
        "logs": logs,
        "members": members,
        "action_choices": action_choices,
        "current_user_filter": user_filter,
        "current_platform_filter": platform_filter,
        "current_action_filter": action_filter,
    })


# ── Admin Dashboard ───────────────────────────────────────────────────────────

@login_required
def admin_dashboard_view(request):
    """Admin dashboard with team activity stats and usage analytics."""
    membership = _require_admin(request)
    if not membership:
        messages.error(request, "Only company admins can view the admin dashboard.")
        return redirect("dashboard:home")

    company = request.company
    now = timezone.now()
    last_7 = now - timezone.timedelta(days=7)
    last_30 = now - timezone.timedelta(days=30)

    # ── Summary cards ──
    total_members = Membership.objects.filter(company=company, is_active=True).count()
    active_integrations = CompanyIntegration.objects.filter(company=company, status="active").count()
    actions_7d = ActivityLog.objects.filter(company=company, created_at__gte=last_7).count()
    actions_30d = ActivityLog.objects.filter(company=company, created_at__gte=last_30).count()

    # ── Activity by day (last 30 days) ──
    daily_activity = list(
        ActivityLog.objects.filter(company=company, created_at__gte=last_30)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    # Convert dates to strings for JSON
    for d in daily_activity:
        d["day"] = d["day"].isoformat()

    # ── Activity by platform (last 30 days) ──
    platform_activity = list(
        ActivityLog.objects.filter(company=company, created_at__gte=last_30)
        .exclude(platform="")
        .values("platform")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # ── Activity by hour of day (last 30 days) — for heatmap ──
    hourly_activity = list(
        ActivityLog.objects.filter(company=company, created_at__gte=last_30)
        .annotate(hour=ExtractHour("created_at"))
        .values("hour")
        .annotate(count=Count("id"))
        .order_by("hour")
    )

    # ── Daily activity per platform (stacked) ──
    daily_by_platform = list(
        ActivityLog.objects.filter(company=company, created_at__gte=last_30)
        .exclude(platform="")
        .annotate(day=TruncDate("created_at"))
        .values("day", "platform")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    for d in daily_by_platform:
        d["day"] = d["day"].isoformat()

    # ── 7-day vs previous 7-day comparison ──
    prev_7 = last_7 - timezone.timedelta(days=7)
    actions_prev_7d = ActivityLog.objects.filter(company=company, created_at__gte=prev_7, created_at__lt=last_7).count()

    # ── Top actions (last 30 days) ──
    top_actions = list(
        ActivityLog.objects.filter(company=company, created_at__gte=last_30)
        .values("action")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )
    # Map action keys to labels
    action_labels = dict(ActivityLog.Action.choices)
    for a in top_actions:
        a["label"] = action_labels.get(a["action"], a["action"])

    # ── Per-user activity (last 30 days) ──
    user_activity = list(
        ActivityLog.objects.filter(company=company, created_at__gte=last_30, user__isnull=False)
        .values("user__username", "user__first_name", "user__last_name")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )
    for u in user_activity:
        name = f"{u['user__first_name']} {u['user__last_name']}".strip()
        u["display_name"] = name or u["user__username"]

    # ── Integration health ──
    integrations_status = list(
        CompanyIntegration.objects.filter(company=company)
        .values("service", "status", "connected_at", "updated_at")
    )
    for i in integrations_status:
        i["connected_at"] = i["connected_at"].isoformat() if i["connected_at"] else ""
        i["updated_at"] = i["updated_at"].isoformat() if i["updated_at"] else ""

    # ── Recent activity (last 10) ──
    recent_logs = ActivityLog.objects.filter(company=company).select_related("user")[:10]

    import json
    return render(request, "companies/admin_dashboard.html", {
        "total_members": total_members,
        "active_integrations": active_integrations,
        "actions_7d": actions_7d,
        "actions_30d": actions_30d,
        "actions_prev_7d": actions_prev_7d,
        "daily_activity_json": json.dumps(daily_activity),
        "platform_activity_json": json.dumps(platform_activity),
        "hourly_activity_json": json.dumps(hourly_activity),
        "daily_by_platform_json": json.dumps(daily_by_platform),
        "top_actions": top_actions,
        "user_activity": user_activity,
        "integrations_status": integrations_status,
        "recent_logs": recent_logs,
    })
