"""
Gmail views.
Scopes required: gmail.readonly, gmail.send, gmail.modify
"""
import base64
from email.mime.text import MIMEText

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from companies.middleware import log_activity, platform_access_required
from integrations.google_utils import (
    gmail_list_messages,
    gmail_get_message,
    gmail_send_message,
    gmail_modify_message,
    gmail_list_labels,
    gmail_get_unread_count,
    gmail_create_draft,
)
from google_hub.helpers import get_google_token


# ── Gmail Views ────────────────────────────────────────────────────────────────

@platform_access_required("google")
def gmail_inbox(request):
    """Show Gmail inbox for the connected Google Workspace account."""
    integration, token = get_google_token(request)
    emails = []
    error = None
    google_connected = integration is not None

    if not token:
        if integration:
            error = "Google session expired. Please reconnect."
        return render(request, "google_hub/gmail_inbox.html", {
            "emails": [], "error": error, "google_connected": google_connected,
        })

    try:
        emails = gmail_list_messages(token, max_results=25)
        for email in emails:
            email["parsed_headers"] = {}
            for header in email.get("payload", {}).get("headers", []):
                name = header.get("name", "").lower()
                if name in ("from", "to", "subject", "date"):
                    email["parsed_headers"][name] = header.get("value", "")
            email["is_unread"] = "UNREAD" in email.get("labelIds", [])
            email["is_starred"] = "STARRED" in email.get("labelIds", [])
            email["has_attachments"] = _has_attachments(email.get("payload", {}))
            email["label_names"] = [
                lbl for lbl in email.get("labelIds", [])
                if lbl not in ("INBOX", "UNREAD", "SENT", "STARRED", "IMPORTANT",
                               "DRAFT", "TRASH", "SPAM", "CATEGORY_PERSONAL",
                               "CATEGORY_SOCIAL", "CATEGORY_PROMOTIONS",
                               "CATEGORY_UPDATES", "CATEGORY_FORUMS")
            ]
    except Exception as e:
        error = str(e)

    return render(request, "google_hub/gmail_inbox.html", {
        "emails": emails,
        "error": error,
        "google_connected": google_connected,
    })


@platform_access_required("google")
def gmail_detail(request, message_id):
    """Show a single Gmail message."""
    _, token = get_google_token(request)
    email = None
    error = None

    if not token:
        messages.error(request, "Google session expired. Please reconnect.")
        return redirect("google_hub:inbox")

    try:
        email = gmail_get_message(token, message_id, fmt="full")
        if email:
            email["parsed_headers"] = {}
            for header in email.get("payload", {}).get("headers", []):
                name = header.get("name", "").lower()
                if name in ("from", "to", "subject", "date", "cc"):
                    email["parsed_headers"][name] = header.get("value", "")

            email["body_html"] = _extract_body(email.get("payload", {}))

            if "UNREAD" in email.get("labelIds", []):
                gmail_modify_message(token, message_id, remove_labels=["UNREAD"])

            log_activity(request, "email_viewed", "google",
                         email["parsed_headers"].get("subject", "")[:200])
    except Exception as e:
        error = str(e)

    return render(request, "google_hub/gmail_detail.html", {"email": email, "error": error})


@platform_access_required("google", "reply")
def gmail_compose(request):
    """Compose and send a Gmail email."""
    _, token = get_google_token(request)
    if not token:
        messages.error(request, "Google session expired. Please reconnect.")
        return redirect("integrations:connect")

    if request.method == "POST":
        to_email = request.POST.get("to_email", "").strip()
        subject = request.POST.get("subject", "").strip()
        body = request.POST.get("body", "").strip()

        if not (to_email and subject and body):
            messages.error(request, "All fields are required.")
            return render(request, "google_hub/gmail_compose.html", {
                "to_email": to_email, "subject": subject, "body": body,
            })

        try:
            msg = MIMEText(body)
            msg["to"] = to_email
            msg["subject"] = subject
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
            gmail_send_message(token, raw)
            log_activity(request, "email_sent", "google",
                         f"To: {to_email}, Subject: {subject}"[:200])
            messages.success(request, f"Email sent to {to_email}!")
            return redirect("google_hub:inbox")
        except Exception as e:
            messages.error(request, f"Failed to send: {e}")

    return render(request, "google_hub/gmail_compose.html", {
        "to_email": request.GET.get("to", ""),
        "subject": request.GET.get("subject", ""),
    })


# ── Sent mail ──────────────────────────────────────────────────────────────────

@platform_access_required("google")
def gmail_sent(request):
    """Show sent Gmail messages."""
    integration, token = get_google_token(request)
    emails = []
    error = None
    google_connected = integration is not None

    if not token:
        if integration:
            error = "Google session expired. Please reconnect."
        return render(request, "google_hub/gmail_inbox.html", {
            "emails": [], "error": error, "google_connected": google_connected,
            "active_tab": "sent",
        })

    try:
        emails = gmail_list_messages(token, max_results=25, query="in:sent")
        for email in emails:
            email["parsed_headers"] = {}
            for header in email.get("payload", {}).get("headers", []):
                name = header.get("name", "").lower()
                if name in ("to", "from", "subject", "date"):
                    email["parsed_headers"][name] = header.get("value", "")
            email["is_starred"] = "STARRED" in email.get("labelIds", [])
            email["has_attachments"] = _has_attachments(email.get("payload", {}))
    except Exception as e:
        error = str(e)

    return render(request, "google_hub/gmail_inbox.html", {
        "emails": emails, "error": error,
        "google_connected": google_connected, "active_tab": "sent",
    })


# ── Drafts ────────────────────────────────────────────────────────────────────

@platform_access_required("google")
def gmail_drafts(request):
    """Show Gmail drafts."""
    integration, token = get_google_token(request)
    emails = []
    error = None
    google_connected = integration is not None

    if not token:
        if integration:
            error = "Google session expired. Please reconnect."
        return render(request, "google_hub/gmail_inbox.html", {
            "emails": [], "error": error, "google_connected": google_connected,
            "active_tab": "drafts",
        })

    try:
        emails = gmail_list_messages(token, max_results=25, query="in:drafts")
        for email in emails:
            email["parsed_headers"] = {}
            for header in email.get("payload", {}).get("headers", []):
                name = header.get("name", "").lower()
                if name in ("to", "from", "subject", "date"):
                    email["parsed_headers"][name] = header.get("value", "")
            email["has_attachments"] = _has_attachments(email.get("payload", {}))
    except Exception as e:
        error = str(e)

    return render(request, "google_hub/gmail_inbox.html", {
        "emails": emails, "error": error,
        "google_connected": google_connected, "active_tab": "drafts",
    })


# ── Search ────────────────────────────────────────────────────────────────────

@platform_access_required("google")
def gmail_search(request):
    """Search Gmail messages."""
    integration, token = get_google_token(request)
    emails = []
    error = None
    google_connected = integration is not None
    query_str = request.GET.get("q", "").strip()

    if token and query_str:
        try:
            emails = gmail_list_messages(token, max_results=25, query=query_str)
            for email in emails:
                email["parsed_headers"] = {}
                for header in email.get("payload", {}).get("headers", []):
                    name = header.get("name", "").lower()
                    if name in ("from", "to", "subject", "date"):
                        email["parsed_headers"][name] = header.get("value", "")
                email["is_unread"] = "UNREAD" in email.get("labelIds", [])
        except Exception as e:
            error = str(e)
    elif not query_str and token:
        pass  # empty search → show empty results

    return render(request, "google_hub/gmail_inbox.html", {
        "emails": emails, "error": error,
        "google_connected": google_connected,
        "active_tab": "search", "search_query": query_str,
    })


# ── AJAX: unread count ─────────────────────────────────────────────────────────

@platform_access_required("google")
def gmail_unread_count_api(request):
    """AJAX: Return unread inbox message count."""
    _, token = get_google_token(request)
    if not token:
        return JsonResponse({"error": "Not connected."}, status=401)
    try:
        count = gmail_get_unread_count(token)
        return JsonResponse({"unread": count})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ── AJAX: labels ──────────────────────────────────────────────────────────────

@platform_access_required("google")
def gmail_labels_api(request):
    """AJAX: Return list of Gmail labels."""
    _, token = get_google_token(request)
    if not token:
        return JsonResponse({"error": "Not connected."}, status=401)
    try:
        labels = gmail_list_labels(token)
        return JsonResponse({"labels": labels})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ── Save as draft ─────────────────────────────────────────────────────────────

@platform_access_required("google", "reply")
@require_POST
def gmail_save_draft(request):
    """Save a composed email as a Gmail draft."""
    _, token = get_google_token(request)
    if not token:
        return JsonResponse({"error": "Google session expired."}, status=401)

    to_email = request.POST.get("to_email", "").strip()
    subject = request.POST.get("subject", "").strip()
    body = request.POST.get("body", "").strip()

    try:
        msg = MIMEText(body)
        if to_email:
            msg["to"] = to_email
        msg["subject"] = subject
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        draft = gmail_create_draft(token, raw)
        log_activity(request, "draft_saved", "google", f"Subject: {subject}"[:200])
        return JsonResponse({"ok": True, "draft_id": draft.get("id")})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ── Internal helpers ───────────────────────────────────────────────────────────

def _has_attachments(payload: dict) -> bool:
    """Check if a Gmail message payload has file attachments."""
    parts = payload.get("parts", [])
    for part in parts:
        if part.get("filename"):
            return True
        if part.get("parts"):
            if _has_attachments(part):
                return True
    return False


def _extract_body(payload: dict) -> str:
    """Extract readable HTML body from a Gmail message payload."""
    mime_type = payload.get("mimeType", "")
    if mime_type == "text/html" and payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
    if mime_type == "text/plain" and payload.get("body", {}).get("data"):
        text = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
        return f"<pre style='white-space:pre-wrap;'>{text}</pre>"

    parts = payload.get("parts", [])
    for part in parts:
        if part.get("mimeType") == "text/html" and part.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
    for part in parts:
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            text = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
            return f"<pre style='white-space:pre-wrap;'>{text}</pre>"
    for part in parts:
        if "parts" in part:
            result = _extract_body(part)
            if result:
                return result
    return "<p class='text-muted'>Unable to display message body.</p>"
