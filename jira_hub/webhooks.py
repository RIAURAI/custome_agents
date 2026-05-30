"""
Jira Cloud webhook handler.
Receives issue/comment events and syncs the affected issue locally.
"""
import hashlib
import hmac
import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from companies.models import Company
from integrations.models import CompanyIntegration
from .sync_service import sync_single_issue, sync_comments
from .models import JiraIssue

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def jira_webhook(request, company_slug, secret):
    """
    POST /jira/webhook/<company_slug>/<secret>/
    Inbound Jira Cloud webhook — validates the per-company secret in the URL,
    then syncs the affected issue.
    """
    # Look up company
    try:
        company = Company.objects.get(slug=company_slug)
    except Company.DoesNotExist:
        return JsonResponse({"error": "unknown company"}, status=404)

    # Validate secret
    integration = CompanyIntegration.objects.filter(
        company=company, service="jira", status="active",
    ).first()
    if not integration or not integration.jira_webhook_secret:
        return JsonResponse({"error": "webhooks not configured"}, status=403)

    if not hmac.compare_digest(secret, integration.jira_webhook_secret):
        logger.warning("Jira webhook: invalid secret for company=%s", company_slug)
        return JsonResponse({"error": "invalid secret"}, status=403)

    # Parse payload
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "invalid JSON"}, status=400)

    event_type = payload.get("webhookEvent", "")
    issue_data = payload.get("issue")
    comment_data = payload.get("comment")

    logger.info("Jira webhook event=%s for company=%s", event_type, company_slug)

    # Handle issue events
    if event_type in ("jira:issue_created", "jira:issue_updated"):
        if issue_data:
            issue_key = issue_data.get("key")
            if issue_key:
                try:
                    sync_single_issue(company, issue_key)
                except Exception:
                    logger.exception("Webhook: failed to sync issue %s", issue_key)

    elif event_type == "jira:issue_deleted":
        if issue_data:
            issue_key = issue_data.get("key")
            if issue_key:
                deleted = JiraIssue.objects.filter(
                    company=company, issue_key=issue_key,
                ).delete()
                logger.info("Webhook: deleted local issue %s (%s rows)", issue_key, deleted[0])

    # Handle comment events
    elif event_type in ("comment_created", "comment_updated", "comment_deleted"):
        if issue_data:
            issue_key = issue_data.get("key")
            if issue_key:
                try:
                    sync_comments(company, issue_key)
                except Exception:
                    logger.exception("Webhook: failed to sync comments for %s", issue_key)

    return JsonResponse({"ok": True})
