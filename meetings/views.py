from datetime import datetime, timezone, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from integrations.models import UserIntegration
from integrations.utils import get_valid_access_token, graph_get


@login_required
def meetings_list(request):
    ms = UserIntegration.objects.filter(user=request.user, service="microsoft").first()
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
    except Exception as e:
        error = str(e)

    return render(request, "meetings/meetings.html", {
        "meetings": meetings,
        "error": error,
        "ms_connected": True,
    })
