from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from integrations.models import UserIntegration
from integrations.utils import get_valid_access_token, graph_get


@login_required
def home(request):
    ms = UserIntegration.objects.filter(user=request.user, service="microsoft").first()
    ms_connected = ms is not None

    unread_count = 0
    recent_emails = []
    upcoming_meetings = []
    graph_error = None

    if ms_connected:
        token = get_valid_access_token(ms)
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

    return render(request, "dashboard/dashboard.html", {
        "ms_connected": ms_connected,
        "unread_count": unread_count,
        "recent_emails": recent_emails,
        "upcoming_meetings": upcoming_meetings,
        "graph_error": graph_error,
    })
