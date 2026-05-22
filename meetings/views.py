from datetime import datetime, timezone, timedelta
import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from companies.middleware import log_activity, platform_access_required
from integrations.models import CompanyIntegration
from integrations.utils import get_company_integration, get_valid_access_token, graph_get
from slack_hub.calendly_agent import CalendlyAgent
from integrations.calendly_service import CalendlyService, CalendlyServiceError


@platform_access_required("microsoft")
def meetings_list(request):
    ms = get_company_integration(request, "microsoft")
    meetings = []
    error = None

    if not ms:
        return render(request, "meetings/meetings.html", {
            "meetings": [],
            "ms_connected": False,
        })

    token = get_valid_access_token(ms)
    if not token:
        return render(request, "meetings/meetings.html", {
            "meetings": [],
            "ms_connected": False,
            "error": "Microsoft session expired. Please reconnect your account.",
        })

    try:
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=7)
        data = graph_get(token, "/me/calendarView", {
            "startDateTime": now.isoformat(),
            "endDateTime": end.isoformat(),
            "$select": "id,subject,start,end,organizer,onlineMeeting,bodyPreview,webLink",
            "$top": "20",
            "$orderby": "start/dateTime",
        })
        meetings = data.get("value", [])
        log_activity(request, "meetings_viewed", "microsoft", f"{len(meetings)} upcoming")
    except Exception as e:
        error = str(e)

    return render(request, "meetings/meetings.html", {
        "meetings": meetings,
        "error": error,
        "ms_connected": True,
    })


# ── Calendly Bot (Standalone — No Slack Dependency) ─────────────────────────

@login_required
def calendly_bot_page(request):
    """Render the Calendly bot page with scheduled events, event types, and chat."""
    company = getattr(request, "company", None)
    calendly_connected = False
    scheduled_events = []
    event_types = []
    user_info = {}
    error = None

    if company:
        integration = CompanyIntegration.objects.filter(
            company=company, service="calendly", status="active"
        ).first()
        calendly_connected = integration is not None

        if calendly_connected:
            try:
                service = CalendlyService(company)
                scheduled_events = service.get_scheduled_events()[:10]
                event_types = service.get_event_types()
                user_info = service.get_user_info()
            except CalendlyServiceError as e:
                error = str(e)

    return render(request, "meetings/calendly_bot.html", {
        "calendly_connected": calendly_connected,
        "scheduled_events": scheduled_events,
        "event_types": event_types,
        "user_info": user_info,
        "error": error,
    })


@login_required
@require_POST
def calendly_bot_send(request):
    """AJAX endpoint: send a message to the Calendly bot and get a response."""
    company = getattr(request, "company", None)
    if not company:
        return JsonResponse({"error": "No company context."}, status=400)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid request."}, status=400)

    message = body.get("message", "").strip()
    if not message:
        return JsonResponse({"error": "Empty message."}, status=400)

    # Process through Calendly Agent
    agent = CalendlyAgent(company)
    result = agent.process_message(message)

    # Log the interaction
    log_activity(request, "calendly_bot_message", "calendly", message[:100])

    return JsonResponse({
        "reply": result.get("reply_text", ""),
        "action": result.get("action"),
        "data": result.get("data"),
        "error": result.get("error", False),
        "calendly_connected": result.get("calendly_available", True),
    })
