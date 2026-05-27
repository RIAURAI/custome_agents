"""
Google Meet views.
Scopes required: meetings.space.created, meetings.space.readonly, calendar.readonly
"""
import logging

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from companies.middleware import log_activity, platform_access_required
from integrations.google_utils import calendar_list_events, meet_create_space
from google_hub.helpers import get_google_token

logger = logging.getLogger(__name__)


@platform_access_required("google")
def meet_view(request):
    """Show Google Meet meetings (calendar events with Meet links)."""
    integration, token = get_google_token(request)
    meetings = []
    error = None
    google_connected = integration is not None

    if not token:
        if integration:
            error = "Google session expired. Please reconnect."
            logger.warning("Google token expired for company %s — Meet page loaded without auth", getattr(request, 'company', 'unknown'))
        else:
            logger.warning("Google not connected for company %s — Meet page accessed", getattr(request, 'company', 'unknown'))
        return render(request, "google_hub/meet.html", {
            "meetings": [], "error": error, "google_connected": google_connected,
        })

    try:
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
    """Create a new Google Meet space and return the join link."""
    _, token = get_google_token(request)
    if not token:
        return JsonResponse({"ok": False, "error": "Google session expired."}, status=401)

    try:
        space = meet_create_space(token)
        meet_uri = space.get("meetingUri", "")
        log_activity(request, "meet_created", "google", f"Meeting: {meet_uri}")
        return JsonResponse({"ok": True, "meeting_uri": meet_uri, "space": space})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
