from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from companies.middleware import has_platform_access
from integrations.utils import get_company_integration, get_valid_access_token, graph_get


@login_required
def home(request):
    ms_integration = get_company_integration(request, "microsoft")
    ms_connected = ms_integration is not None
    ms_has_access = has_platform_access(request, "microsoft")

    unread_count = 0
    recent_emails = []
    upcoming_meetings = []
    graph_error = None

    if ms_connected and ms_has_access:
        token = get_valid_access_token(ms_integration)
        if token:
            try:
                # Unread email count
                data = graph_get(token, "/me/messages", {
                    "$filter": "isRead eq false",
                    "$select": "id",
                    "$top": "1",
                    "$count": "true",
                })
                unread_count = data.get("@odata.count", 0)

                # 5 most recent emails
                email_data = graph_get(token, "/me/messages", {
                    "$select": "subject,from,receivedDateTime,isRead,bodyPreview",
                    "$top": "5",
                    "$orderby": "receivedDateTime desc",
                })
                recent_emails = email_data.get("value", [])
                # Ensure 'from' key exists for template safety
                for em in recent_emails:
                    if "from" not in em:
                        em["from"] = {"emailAddress": {"name": "Unknown", "address": ""}}

                # Today's meetings
                from datetime import datetime, timezone, timedelta
                now = datetime.now(timezone.utc)
                end = now + timedelta(days=1)
                meeting_data = graph_get(token, "/me/calendarView", {
                    "startDateTime": now.isoformat(),
                    "endDateTime": end.isoformat(),
                    "$select": "subject,start,end,onlineMeeting,webLink",
                    "$top": "5",
                    "$orderby": "start/dateTime",
                })
                upcoming_meetings = meeting_data.get("value", [])
            except Exception as e:
                graph_error = str(e)

    slack_integration = get_company_integration(request, "slack")
    slack_connected = slack_integration is not None
    slack_has_access = has_platform_access(request, "slack")

    return render(request, "dashboard/dashboard.html", {
        "ms_connected": ms_connected,
        "ms_has_access": bool(ms_has_access),
        "slack_connected": slack_connected,
        "slack_has_access": bool(slack_has_access),
        "unread_count": unread_count,
        "recent_emails": recent_emails,
        "upcoming_meetings": upcoming_meetings,
        "graph_error": graph_error,
    })
