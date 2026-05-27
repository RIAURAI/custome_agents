import base64
from email.mime.text import MIMEText

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from companies.middleware import log_activity, platform_access_required
from integrations.utils import get_company_integration
from integrations.google_utils import (
    get_valid_google_access_token,
    gmail_list_messages,
    gmail_get_message,
    gmail_send_message,
    gmail_modify_message,
    calendar_list_events,
    meet_create_space,
)


def _get_google_token(request):
    """Get a valid Google access token for the current company, or None."""
    integration = get_company_integration(request, "google")
    if not integration:
        return None, None
    token = get_valid_google_access_token(integration)
    return integration, token


# ── Gmail Views ───────────────────────────────────────────────────────────────

@platform_access_required("google")
def gmail_inbox(request):
    """Show Gmail inbox for the connected Google Workspace account."""
    integration, token = _get_google_token(request)
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
        # Parse headers for display
        for email in emails:
            email["parsed_headers"] = {}
            for header in email.get("payload", {}).get("headers", []):
                name = header.get("name", "").lower()
                if name in ("from", "subject", "date"):
                    email["parsed_headers"][name] = header.get("value", "")
            email["is_unread"] = "UNREAD" in email.get("labelIds", [])
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
    _, token = _get_google_token(request)
    email = None
    error = None

    if not token:
        messages.error(request, "Google session expired. Please reconnect.")
        return redirect("google_hub:inbox")

    try:
        email = gmail_get_message(token, message_id, fmt="full")
        if email:
            # Parse headers
            email["parsed_headers"] = {}
            for header in email.get("payload", {}).get("headers", []):
                name = header.get("name", "").lower()
                if name in ("from", "to", "subject", "date", "cc"):
                    email["parsed_headers"][name] = header.get("value", "")

            # Extract body
            email["body_html"] = _extract_body(email.get("payload", {}))

            # Mark as read
            if "UNREAD" in email.get("labelIds", []):
                gmail_modify_message(token, message_id, remove_labels=["UNREAD"])

            log_activity(request, "email_viewed", "google", email["parsed_headers"].get("subject", "")[:200])
    except Exception as e:
        error = str(e)

    return render(request, "google_hub/gmail_detail.html", {"email": email, "error": error})


def _extract_body(payload: dict) -> str:
    """Extract readable body from Gmail message payload."""
    # Check if it's a simple message
    mime_type = payload.get("mimeType", "")
    if mime_type == "text/html" and payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
    if mime_type == "text/plain" and payload.get("body", {}).get("data"):
        text = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
        return f"<pre style='white-space:pre-wrap;'>{text}</pre>"

    # Check multipart
    parts = payload.get("parts", [])
    for part in parts:
        part_mime = part.get("mimeType", "")
        if part_mime == "text/html" and part.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
    for part in parts:
        part_mime = part.get("mimeType", "")
        if part_mime == "text/plain" and part.get("body", {}).get("data"):
            text = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
            return f"<pre style='white-space:pre-wrap;'>{text}</pre>"
    # Recurse into nested multipart
    for part in parts:
        if "parts" in part:
            result = _extract_body(part)
            if result:
                return result
    return "<p class='text-muted'>Unable to display message body.</p>"


@platform_access_required("google", "reply")
def gmail_compose(request):
    """Compose and send a Gmail email."""
    _, token = _get_google_token(request)
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
            # Build RFC 2822 message
            msg = MIMEText(body)
            msg["to"] = to_email
            msg["subject"] = subject
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
            gmail_send_message(token, raw)
            log_activity(request, "email_sent", "google", f"To: {to_email}, Subject: {subject}"[:200])
            messages.success(request, f"Email sent to {to_email}!")
            return redirect("google_hub:inbox")
        except Exception as e:
            messages.error(request, f"Failed to send: {e}")

    return render(request, "google_hub/gmail_compose.html", {})


# ── Google Calendar View ──────────────────────────────────────────────────────

@platform_access_required("google")
def calendar_view(request):
    """Show upcoming Google Calendar events."""
    integration, token = _get_google_token(request)
    events = []
    error = None
    google_connected = integration is not None

    if not token:
        if integration:
            error = "Google session expired. Please reconnect."
        return render(request, "google_hub/calendar.html", {
            "events": [], "error": error, "google_connected": google_connected,
        })

    try:
        events = calendar_list_events(token, days=7, max_results=20)
        log_activity(request, "calendar_viewed", "google", f"{len(events)} upcoming events")
    except Exception as e:
        error = str(e)

    return render(request, "google_hub/calendar.html", {
        "events": events,
        "error": error,
        "google_connected": google_connected,
    })


# ── Google Meet View ──────────────────────────────────────────────────────────

@platform_access_required("google")
def meet_view(request):
    """Show Google Meet meetings (calendar events with Meet links)."""
    integration, token = _get_google_token(request)
    meetings = []
    error = None
    google_connected = integration is not None

    if not token:
        if integration:
            error = "Google session expired. Please reconnect."
        return render(request, "google_hub/meet.html", {
            "meetings": [], "error": error, "google_connected": google_connected,
        })

    try:
        # Get calendar events and filter those with Google Meet links
        events = calendar_list_events(token, days=7, max_results=30)
        for event in events:
            meet_link = ""
            conference = event.get("conferenceData", {})
            for entry_point in conference.get("entryPoints", []):
                if entry_point.get("entryPointType") == "video":
                    meet_link = entry_point.get("uri", "")
                    break
            if not meet_link and "hangoutLink" in event:
                meet_link = event.get("hangoutLink", "")
            if meet_link:
                event["meet_link"] = meet_link
                meetings.append(event)
    except Exception as e:
        error = str(e)

    return render(request, "google_hub/meet.html", {
        "meetings": meetings,
        "error": error,
        "google_connected": google_connected,
    })


@platform_access_required("google", "reply")
@require_POST
def meet_create(request):
    """Create a new Google Meet space and return the link."""
    _, token = _get_google_token(request)
    if not token:
        return JsonResponse({"ok": False, "error": "Google session expired."}, status=401)

    try:
        space = meet_create_space(token)
        meet_uri = space.get("meetingUri", "")
        log_activity(request, "meet_created", "google", f"Meeting: {meet_uri}")
        return JsonResponse({"ok": True, "meeting_uri": meet_uri, "space": space})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
