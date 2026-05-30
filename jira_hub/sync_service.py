"""
Sync Jira projects and issues into the local database.
"""
import logging
from datetime import datetime, timezone

from integrations.models import CompanyIntegration
from .jira_service import JiraClient, JiraAPIError
from .models import JiraProject, JiraIssue, JiraComment, JiraSyncLog

logger = logging.getLogger(__name__)


def _parse_dt(val):
    """Parse Jira datetime string (ISO 8601) to timezone-aware datetime."""
    if not val:
        return None
    try:
        return datetime.fromisoformat(val.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _status_category_key(status_field):
    """Extract statusCategory.key from a Jira status dict."""
    cat = status_field.get("statusCategory", {}) if status_field else {}
    return cat.get("key", "undefined").lower()


def sync_projects(company, client=None):
    """Sync all Jira projects for a company. Returns count synced."""
    integration = CompanyIntegration.objects.filter(
        company=company, service="jira", status="active",
    ).first()
    if not integration:
        return 0

    if client is None:
        client = JiraClient(integration)

    projects = client.list_projects()
    count = 0
    for p in projects:
        lead = p.get("lead", {})
        avatar = p.get("avatarUrls", {})
        JiraProject.objects.update_or_create(
            company=company,
            project_id=str(p["id"]),
            defaults={
                "key": p["key"],
                "name": p["name"],
                "project_type": p.get("projectTypeKey", ""),
                "lead_display_name": lead.get("displayName", ""),
                "avatar_url": avatar.get("48x48", ""),
                "last_synced_at": datetime.now(timezone.utc),
            },
        )
        count += 1
    return count


def sync_issues(company, project_key=None, client=None, max_pages=10):
    """Sync Jira issues for a company. Returns count synced."""
    integration = CompanyIntegration.objects.filter(
        company=company, service="jira", status="active",
    ).first()
    if not integration:
        return 0

    if client is None:
        client = JiraClient(integration)

    jql_parts = []
    if project_key:
        jql_parts.append(f'project = "{project_key}"')
    jql = " AND ".join(jql_parts) + " ORDER BY updated DESC" if jql_parts else "ORDER BY updated DESC"

    total_synced = 0
    start_at = 0

    for _ in range(max_pages):
        result = client.search_issues(jql=jql, start_at=start_at, max_results=50)
        issues = result.get("issues", [])
        if not issues:
            break

        for raw in issues:
            fields = raw.get("fields", {})
            proj_field = fields.get("project", {})

            # Link to local JiraProject if it exists
            local_project = JiraProject.objects.filter(
                company=company, project_id=str(proj_field.get("id", "")),
            ).first()

            status_field = fields.get("status", {})
            assignee = fields.get("assignee") or {}
            reporter = fields.get("reporter") or {}
            priority = fields.get("priority") or {}
            desc = fields.get("description", "")
            if isinstance(desc, dict):
                desc = JiraClient.adf_to_text(desc)

            JiraIssue.objects.update_or_create(
                company=company,
                issue_id=str(raw["id"]),
                defaults={
                    "project": local_project,
                    "issue_key": raw["key"],
                    "summary": (fields.get("summary") or "")[:500],
                    "description": desc or "",
                    "issue_type": (fields.get("issuetype") or {}).get("name", ""),
                    "status": status_field.get("name", ""),
                    "status_category": _status_category_key(status_field),
                    "priority": priority.get("name", ""),
                    "labels": fields.get("labels", []),
                    "assignee_display_name": assignee.get("displayName", ""),
                    "reporter_display_name": reporter.get("displayName", ""),
                    "created_at_jira": _parse_dt(fields.get("created")),
                    "updated_at_jira": _parse_dt(fields.get("updated")),
                    "due_date": fields.get("duedate"),
                },
            )
            total_synced += 1

        start_at += len(issues)
        if start_at >= result.get("total", 0):
            break

    return total_synced


def sync_comments(company, issue_key, client=None):
    """Sync comments for a single issue."""
    integration = CompanyIntegration.objects.filter(
        company=company, service="jira", status="active",
    ).first()
    if not integration:
        return 0

    if client is None:
        client = JiraClient(integration)

    issue = JiraIssue.objects.filter(company=company, issue_key=issue_key).first()
    if not issue:
        return 0

    raw_comments = client.get_comments(issue_key)
    count = 0
    for c in raw_comments:
        body = c.get("body", "")
        if isinstance(body, dict):
            body = JiraClient.adf_to_text(body)
        author = c.get("author", {})
        JiraComment.objects.update_or_create(
            issue=issue,
            comment_id=str(c["id"]),
            defaults={
                "author_display_name": author.get("displayName", "Unknown"),
                "body": body,
                "created_at_jira": _parse_dt(c.get("created")),
            },
        )
        count += 1
    return count


def sync_single_issue(company, issue_key, client=None):
    """Sync a single issue by key (used by webhook handler). Returns the JiraIssue or None."""
    integration = CompanyIntegration.objects.filter(
        company=company, service="jira", status="active",
    ).first()
    if not integration:
        return None

    if client is None:
        client = JiraClient(integration)

    try:
        raw = client.get_issue(issue_key)
    except JiraAPIError as exc:
        if exc.status_code == 404:
            # Issue was deleted — remove local copy
            JiraIssue.objects.filter(company=company, issue_key=issue_key).delete()
            logger.info("Deleted local issue %s (no longer in Jira)", issue_key)
            return None
        raise

    fields = raw.get("fields", {})
    proj_field = fields.get("project", {})

    local_project = JiraProject.objects.filter(
        company=company, project_id=str(proj_field.get("id", "")),
    ).first()

    status_field = fields.get("status", {})
    assignee = fields.get("assignee") or {}
    reporter = fields.get("reporter") or {}
    priority = fields.get("priority") or {}
    desc = fields.get("description", "")
    if isinstance(desc, dict):
        desc = JiraClient.adf_to_text(desc)

    issue, _ = JiraIssue.objects.update_or_create(
        company=company,
        issue_id=str(raw["id"]),
        defaults={
            "project": local_project,
            "issue_key": raw["key"],
            "summary": (fields.get("summary") or "")[:500],
            "description": desc or "",
            "issue_type": (fields.get("issuetype") or {}).get("name", ""),
            "status": status_field.get("name", ""),
            "status_category": _status_category_key(status_field),
            "priority": priority.get("name", ""),
            "labels": fields.get("labels", []),
            "assignee_display_name": assignee.get("displayName", ""),
            "reporter_display_name": reporter.get("displayName", ""),
            "created_at_jira": _parse_dt(fields.get("created")),
            "updated_at_jira": _parse_dt(fields.get("updated")),
            "due_date": fields.get("duedate"),
        },
    )
    return issue


def full_sync(company):
    """Run a full sync (projects + issues) and log it."""
    sync_log = JiraSyncLog.objects.create(company=company, status="running")
    try:
        integration = CompanyIntegration.objects.filter(
            company=company, service="jira", status="active",
        ).first()
        if not integration:
            sync_log.status = "error"
            sync_log.error_message = "No active Jira integration found."
            sync_log.finished_at = datetime.now(timezone.utc)
            sync_log.save()
            return sync_log

        client = JiraClient(integration)
        p_count = sync_projects(company, client=client)
        i_count = sync_issues(company, client=client)
        sync_log.projects_synced = p_count
        sync_log.issues_synced = i_count
        sync_log.status = "success"
    except JiraAPIError as exc:
        sync_log.status = "error"
        sync_log.error_message = str(exc)
        logger.exception("Jira sync failed for company=%s", company.slug)
    except Exception as exc:
        sync_log.status = "error"
        sync_log.error_message = str(exc)
        logger.exception("Unexpected error during Jira sync for company=%s", company.slug)
    finally:
        sync_log.finished_at = datetime.now(timezone.utc)
        sync_log.save()
    return sync_log
