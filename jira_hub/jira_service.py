"""
Thin REST wrapper around Jira Cloud API v3.
Uses Basic Auth (email + API token) from CompanyIntegration.
"""
import base64
import logging
from datetime import datetime

import requests

from integrations.utils import decrypt_token

logger = logging.getLogger(__name__)


class JiraAPIError(Exception):
    """Raised when Jira API returns a non-2xx response."""
    def __init__(self, status_code, message=""):
        self.status_code = status_code
        self.message = message
        super().__init__(f"Jira API {status_code}: {message}")


class JiraClient:
    """Jira Cloud REST API v3 client for a single CompanyIntegration."""

    def __init__(self, integration):
        self.integration = integration
        self.base_url = integration.jira_site_url.rstrip("/")
        email = integration.jira_user_email
        token = decrypt_token(integration.jira_api_token_enc)
        auth_bytes = base64.b64encode(f"{email}:{token}".encode()).decode()
        self._headers = {
            "Authorization": f"Basic {auth_bytes}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # ── Low-level HTTP ────────────────────────────────────────────────────

    def _request(self, method, path, **kwargs):
        url = f"{self.base_url}{path}"
        kwargs.setdefault("headers", self._headers)
        kwargs.setdefault("timeout", 15)
        try:
            resp = requests.request(method, url, **kwargs)
        except requests.exceptions.RequestException as exc:
            logger.error("Jira request failed: %s %s — %s", method, path, exc)
            raise JiraAPIError(0, str(exc)) from exc

        if resp.status_code >= 400:
            msg = resp.text[:300] if resp.text else ""
            logger.warning("Jira %s %s → %s: %s", method, path, resp.status_code, msg)
            raise JiraAPIError(resp.status_code, msg)
        return resp.json() if resp.content else {}

    def _get(self, path, **params):
        return self._request("GET", path, params=params)

    def _post(self, path, data):
        return self._request("POST", path, json=data)

    def _put(self, path, data):
        return self._request("PUT", path, json=data)

    # ── Projects ──────────────────────────────────────────────────────────

    def list_projects(self):
        """Return all projects visible to this user."""
        return self._get("/rest/api/3/project", expand="lead")

    def get_project(self, key):
        return self._get(f"/rest/api/3/project/{key}")

    # ── Issues ────────────────────────────────────────────────────────────

    def search_issues(self, jql="", start_at=0, max_results=50, fields=None):
        """Search issues with JQL."""
        payload = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
            "fields": fields or [
                "summary", "status", "issuetype", "priority", "assignee",
                "reporter", "created", "updated", "labels", "description",
                "duedate", "project",
            ],
        }
        return self._post("/rest/api/3/search", payload)

    def get_issue(self, key):
        return self._get(f"/rest/api/3/issue/{key}")

    def create_issue(self, project_key, summary, description="", issue_type="Task", **extra):
        """Create a new issue. Returns the created issue dict."""
        fields = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
        }
        if description:
            fields["description"] = self._text_to_adf(description)
        fields.update(extra)
        return self._post("/rest/api/3/issue", {"fields": fields})

    def update_issue(self, key, fields):
        return self._put(f"/rest/api/3/issue/{key}", {"fields": fields})

    # ── Transitions ───────────────────────────────────────────────────────

    def list_transitions(self, key):
        data = self._get(f"/rest/api/3/issue/{key}/transitions")
        return data.get("transitions", [])

    def transition_issue(self, key, transition_id):
        return self._post(f"/rest/api/3/issue/{key}/transitions", {
            "transition": {"id": str(transition_id)},
        })

    # ── Comments ──────────────────────────────────────────────────────────

    def get_comments(self, key):
        data = self._get(f"/rest/api/3/issue/{key}/comment")
        return data.get("comments", [])

    def add_comment(self, key, body_text):
        return self._post(f"/rest/api/3/issue/{key}/comment", {
            "body": self._text_to_adf(body_text),
        })

    # ── Users ─────────────────────────────────────────────────────────────

    def myself(self):
        return self._get("/rest/api/3/myself")

    # ── Webhooks ──────────────────────────────────────────────────────────

    def register_webhook(self, url, events=None):
        """Register a Jira webhook. Returns the webhook id."""
        if events is None:
            events = [
                "jira:issue_created",
                "jira:issue_updated",
                "jira:issue_deleted",
                "comment_created",
                "comment_updated",
                "comment_deleted",
            ]
        payload = {
            "name": "WorkHub Integration",
            "url": url,
            "events": events,
            "filters": {},
            "excludeBody": False,
        }
        result = self._post("/rest/webhooks/1.0/webhook", payload)
        return result

    def delete_webhook(self, webhook_id):
        """Delete a registered Jira webhook."""
        return self._request("DELETE", f"/rest/webhooks/1.0/webhook/{webhook_id}")

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _text_to_adf(text):
        """Convert plain text to Atlassian Document Format (ADF)."""
        paragraphs = text.split("\n\n") if "\n\n" in text else [text]
        content = []
        for para in paragraphs:
            content.append({
                "type": "paragraph",
                "content": [{"type": "text", "text": para}],
            })
        return {
            "version": 1,
            "type": "doc",
            "content": content,
        }

    @staticmethod
    def adf_to_text(adf):
        """Extract plain text from ADF document."""
        if not adf or not isinstance(adf, dict):
            return ""
        parts = []
        for block in adf.get("content", []):
            for inline in block.get("content", []):
                if inline.get("type") == "text":
                    parts.append(inline.get("text", ""))
            parts.append("\n")
        return "".join(parts).strip()
