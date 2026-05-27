"""
Google Calendar views.
Scopes required: https://www.googleapis.com/auth/calendar
"""
import json
import logging

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from companies.middleware import log_activity, platform_access_required
from integrations.google_utils import (
    calendar_list_events,
    calendar_create_event,
    calendar_delete_event,
    calendar_get_event,
)
from google_hub.helpers import get_google_token

logger = logging.getLogger(__name__)


@platform_access_required("google")
def calendar_view(request):
    """Show upcoming Google Calendar events."""
    integration, token = get_google_token(request)
    events = []
    error = None
    google_connected = integration is not None

    if not token:
        if integration:
            error = "Google session expired. Please reconnect."
            logger.warning("Google token expired for company %s — Calendar page loaded without auth", getattr(request, 'company', 'unknown'))
        else:
            logger.warning("Google not connected for company %s — Calendar page accessed", getattr(request, 'company', 'unknown'))
        return render(request, "google_hub/calendar.html", {
            "events": [], "error": error, "google_connected": google_connected,
        })

    try:
        days = int(request.GET.get("days", 7))
        days = max(1, min(days, 90))  # clamp 1–90
        events = calendar_list_events(token, days=days, max_results=50)
        log_activity(request, "calendar_viewed", "google", f"{len(events)} upcoming events")
    except Exception as e:
        error = str(e)

    return render(request, "google_hub/calendar.html", {
        "events": events,
        "error": error,
        "google_connected": google_connected,
    })


# ── AJAX: list events ──────────────────────────────────────────────────────────

@platform_access_required("google")
def calendar_events_api(request):
    """AJAX: Return upcoming events as JSON."""
    _, token = get_google_token(request)
    if not token:
        return JsonResponse({"error": "Not connected."}, status=401)
    try:
        days = int(request.GET.get("days", 7))
        days = max(1, min(days, 90))
        events = calendar_list_events(token, days=days, max_results=50)
        return JsonResponse({"events": events})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ── AJAX: create event ─────────────────────────────────────────────────────────

@platform_access_required("google", "reply")
@require_POST
def calendar_event_create(request):
    """AJAX: Create a new Google Calendar event."""
    _, token = get_google_token(request)
    if not token:
        return JsonResponse({"error": "Google session expired."}, status=401)

    try:
        body = json.loads(request.body)
    except (ValueError, KeyError):
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    summary = body.get("summary", "").strip()
    start = body.get("start", "")
    end = body.get("end", "")
    if not summary or not start or not end:
        return JsonResponse({"error": "summary, start, and end are required."}, status=400)

    event_body = {
        "summary": summary,
        "description": body.get("description", ""),
        "location": body.get("location", ""),
        "start": {"dateTime": start, "timeZone": body.get("timeZone", "UTC")},
        "end": {"dateTime": end, "timeZone": body.get("timeZone", "UTC")},
    }

    # Optionally create a Google Meet link
    if body.get("add_meet"):
        event_body["conferenceData"] = {
            "createRequest": {"requestId": f"meet-{summary[:20]}", "conferenceSolutionKey": {"type": "hangoutsMeet"}}
        }

    # Attendees
    attendees = body.get("attendees", [])
    if attendees:
        event_body["attendees"] = [{"email": e} for e in attendees if e]

    try:
        params = {"conferenceDataVersion": 1} if body.get("add_meet") else {}
        from integrations.google_utils import CALENDAR_API_BASE
        import requests as http_req
        resp = http_req.post(
            f"{CALENDAR_API_BASE}/calendars/primary/events",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=event_body,
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        event = resp.json()
        log_activity(request, "calendar_event_created", "google", summary[:200])
        return JsonResponse({"ok": True, "event": event})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ── AJAX: delete event ─────────────────────────────────────────────────────────

@platform_access_required("google", "reply")
@require_POST
def calendar_event_delete(request, event_id):
    """AJAX: Delete a calendar event."""
    _, token = get_google_token(request)
    if not token:
        return JsonResponse({"error": "Google session expired."}, status=401)
    try:
        calendar_delete_event(token, event_id)
        log_activity(request, "calendar_event_deleted", "google", event_id)
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ── AJAX: get single event ─────────────────────────────────────────────────────

@platform_access_required("google")
def calendar_event_detail(request, event_id):
    """AJAX: Fetch a single calendar event."""
    _, token = get_google_token(request)
    if not token:
        return JsonResponse({"error": "Not connected."}, status=401)
    try:
        event = calendar_get_event(token, event_id)
        return JsonResponse({"event": event})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

