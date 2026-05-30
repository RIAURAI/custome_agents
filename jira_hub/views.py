import logging
import secrets

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from integrations.models import CompanyIntegration
from companies.middleware import log_activity

from .models import JiraProject, JiraIssue, JiraComment
from .jira_service import JiraClient, JiraAPIError
from .sync_service import full_sync, sync_comments

logger = logging.getLogger(__name__)


def _get_jira_integration(request):
    """Return active Jira CompanyIntegration or None."""
    company = getattr(request, "company", None)
    if not company:
        return None
    return CompanyIntegration.objects.filter(
        company=company, service="jira", status="active",
    ).first()


def _jira_required(view_func):
    """Decorator: redirect to integrations page if Jira not connected."""
    from functools import wraps

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        integration = _get_jira_integration(request)
        if not integration:
            messages.warning(request, "Please connect your Jira account first.")
            return redirect("integrations:connect")
        request.jira_integration = integration
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Dashboard ─────────────────────────────────────────────────────────────────

@_jira_required
def dashboard_view(request):
    company = request.company
    integration = request.jira_integration

    total_issues = JiraIssue.objects.filter(company=company).count()
    by_status = (
        JiraIssue.objects.filter(company=company)
        .values("status_category")
        .annotate(count=Count("id"))
    )
    status_counts = {s["status_category"]: s["count"] for s in by_status}

    recent_issues = JiraIssue.objects.filter(company=company)[:10]
    projects = JiraProject.objects.filter(company=company)

    return render(request, "jira_hub/dashboard.html", {
        "integration": integration,
        "total_issues": total_issues,
        "open_count": status_counts.get("new", 0) + status_counts.get("indeterminate", 0),
        "done_count": status_counts.get("done", 0),
        "in_progress_count": status_counts.get("indeterminate", 0),
        "todo_count": status_counts.get("new", 0),
        "recent_issues": recent_issues,
        "projects": projects,
        "project_count": projects.count(),
    })


# ── Projects ──────────────────────────────────────────────────────────────────

@_jira_required
def projects_view(request):
    projects = JiraProject.objects.filter(company=request.company).annotate(
        issue_count=Count("issues"),
    )
    return render(request, "jira_hub/projects.html", {
        "projects": projects,
    })


@_jira_required
def project_detail_view(request, key):
    project = get_object_or_404(JiraProject, company=request.company, key=key)
    issues = project.issues.all()

    status_filter = request.GET.get("status", "")
    if status_filter:
        issues = issues.filter(status_category=status_filter)

    return render(request, "jira_hub/project_detail.html", {
        "project": project,
        "issues": issues[:100],
        "status_filter": status_filter,
    })


# ── Issues ────────────────────────────────────────────────────────────────────

@_jira_required
def issues_view(request):
    issues = JiraIssue.objects.filter(company=request.company)

    status_filter = request.GET.get("status", "")
    priority_filter = request.GET.get("priority", "")
    search_q = request.GET.get("q", "").strip()
    project_filter = request.GET.get("project", "")

    if status_filter:
        issues = issues.filter(status_category=status_filter)
    if priority_filter:
        issues = issues.filter(priority__iexact=priority_filter)
    if search_q:
        issues = issues.filter(
            Q(summary__icontains=search_q) | Q(issue_key__icontains=search_q)
        )
    if project_filter:
        issues = issues.filter(project__key=project_filter)

    projects = JiraProject.objects.filter(company=request.company)
    priorities = (
        JiraIssue.objects.filter(company=request.company)
        .values_list("priority", flat=True)
        .distinct()
        .order_by("priority")
    )

    return render(request, "jira_hub/issues.html", {
        "issues": issues[:200],
        "status_filter": status_filter,
        "priority_filter": priority_filter,
        "search_q": search_q,
        "project_filter": project_filter,
        "projects": projects,
        "priorities": [p for p in priorities if p],
    })


@_jira_required
def issue_detail_view(request, key):
    issue = get_object_or_404(JiraIssue, company=request.company, issue_key=key)

    # Sync comments on demand
    try:
        sync_comments(request.company, key)
    except Exception:
        logger.warning("Could not sync comments for %s", key)

    comments = issue.comments.all()

    # Fetch available transitions
    transitions = []
    try:
        client = JiraClient(request.jira_integration)
        transitions = client.list_transitions(key)
    except Exception:
        logger.warning("Could not fetch transitions for %s", key)

    return render(request, "jira_hub/issue_detail.html", {
        "issue": issue,
        "comments": comments,
        "transitions": transitions,
        "integration": request.jira_integration,
    })


@_jira_required
@require_POST
def create_issue_view(request):
    project_key = request.POST.get("project_key", "").strip()
    summary = request.POST.get("summary", "").strip()
    description = request.POST.get("description", "").strip()
    issue_type = request.POST.get("issue_type", "Task").strip()

    if not project_key or not summary:
        messages.error(request, "Project and summary are required.")
        return redirect("jira_hub:issues")

    try:
        client = JiraClient(request.jira_integration)
        result = client.create_issue(project_key, summary, description, issue_type)
        new_key = result.get("key", "")
        messages.success(request, f"Issue {new_key} created successfully!")
        log_activity(request, "jira_issue_created", "jira", f"Issue: {new_key}")

        # Trigger a quick sync to pull the new issue into local DB
        from .sync_service import sync_issues
        sync_issues(request.company, project_key=project_key, client=client, max_pages=1)

        return redirect("jira_hub:issues")
    except JiraAPIError as exc:
        messages.error(request, f"Failed to create issue: {exc.message[:200]}")
        return redirect("jira_hub:issues")


@_jira_required
@require_POST
def add_comment_view(request, key):
    body = request.POST.get("body", "").strip()
    if not body:
        messages.error(request, "Comment body is required.")
        return redirect("jira_hub:issue_detail", key=key)

    try:
        client = JiraClient(request.jira_integration)
        client.add_comment(key, body)
        messages.success(request, "Comment added.")
        sync_comments(request.company, key)
    except JiraAPIError as exc:
        messages.error(request, f"Failed to add comment: {exc.message[:200]}")

    return redirect("jira_hub:issue_detail", key=key)


@_jira_required
@require_POST
def transition_view(request, key):
    transition_id = request.POST.get("transition_id", "")
    if not transition_id:
        messages.error(request, "No transition selected.")
        return redirect("jira_hub:issue_detail", key=key)

    try:
        client = JiraClient(request.jira_integration)
        client.transition_issue(key, transition_id)
        messages.success(request, f"Issue {key} transitioned successfully.")
        log_activity(request, "jira_issue_transitioned", "jira", f"Issue: {key}")

        # Re-sync this issue to update local status
        from .sync_service import sync_issues
        sync_issues(request.company, client=client, max_pages=1)
    except JiraAPIError as exc:
        messages.error(request, f"Transition failed: {exc.message[:200]}")

    return redirect("jira_hub:issue_detail", key=key)


# ── Sync ──────────────────────────────────────────────────────────────────────

@_jira_required
@require_POST
def sync_now_view(request):
    sync_log = full_sync(request.company)
    if sync_log.status == "success":
        messages.success(
            request,
            f"Sync complete! {sync_log.projects_synced} projects, {sync_log.issues_synced} issues."
        )
    else:
        messages.error(request, f"Sync failed: {sync_log.error_message[:200]}")
    log_activity(request, "jira_sync", "jira", f"Status: {sync_log.status}")
    return redirect("jira_hub:dashboard")


# ── Webhooks ──────────────────────────────────────────────────────────────────

@_jira_required
@require_POST
def register_webhook_view(request):
    """Register a Jira webhook for real-time updates."""
    integration = request.jira_integration
    company = request.company

    # Generate a secret if not already set
    if not integration.jira_webhook_secret:
        integration.jira_webhook_secret = secrets.token_hex(32)
        integration.save(update_fields=["jira_webhook_secret"])

    # Build the webhook callback URL
    webhook_url = request.build_absolute_uri(
        f"/jira/webhook/{company.slug}/{integration.jira_webhook_secret}/"
    )

    try:
        client = JiraClient(integration)

        # Delete existing webhook first if one is registered
        if integration.jira_webhook_id:
            try:
                client.delete_webhook(integration.jira_webhook_id)
            except JiraAPIError:
                pass  # Old webhook may already be gone

        result = client.register_webhook(webhook_url)
        webhook_id = str(result.get("self", "").split("/")[-1]) if result.get("self") else ""
        if not webhook_id:
            webhook_id = str(result.get("id", ""))

        integration.jira_webhook_id = webhook_id
        integration.save(update_fields=["jira_webhook_id"])

        messages.success(request, "Jira webhook registered! You'll get real-time updates now.")
        log_activity(request, "jira_webhook_registered", "jira", f"Webhook ID: {webhook_id}")
    except JiraAPIError as exc:
        messages.error(request, f"Failed to register webhook: {exc.message[:200]}")

    return redirect("integrations:connect")


@_jira_required
@require_POST
def deregister_webhook_view(request):
    """Remove the registered Jira webhook."""
    integration = request.jira_integration

    if integration.jira_webhook_id:
        try:
            client = JiraClient(integration)
            client.delete_webhook(integration.jira_webhook_id)
        except JiraAPIError:
            pass  # Best-effort cleanup

    integration.jira_webhook_id = ""
    integration.jira_webhook_secret = ""
    integration.save(update_fields=["jira_webhook_id", "jira_webhook_secret"])

    messages.success(request, "Jira webhook removed.")
    log_activity(request, "jira_webhook_deregistered", "jira", "")
    return redirect("integrations:connect")
