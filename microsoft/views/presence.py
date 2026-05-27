"""
Teams Presence views.
Scopes required: Presence.Read, Presence.Read.All
"""
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from companies.middleware import has_platform_access, log_activity
from integrations.utils import graph_get, graph_post, friendly_graph_error
from microsoft.helpers import get_ms_token

logger = logging.getLogger(__name__)


@login_required
def presence_view(request):
    """Full presence page — my presence + team presence grid."""
    integration, token = get_ms_token(request)
    ms_connected = integration is not None
    has_access = has_platform_access(request, "microsoft")

    my_presence = None
    error = None

    if ms_connected and has_access and token:
        try:
            my_presence = graph_get(token, "/me/presence")
        except Exception as e:
            error = friendly_graph_error(e)

    if my_presence:
        log_activity(request, "presence_viewed", "microsoft")

    return render(request, "microsoft/presence.html", {
        "ms_connected": ms_connected,
        "has_access": bool(has_access),
        "my_presence": my_presence,
        "error": error,
    })


@login_required
def presence_api(request):
    """AJAX: Get my current presence status."""
    _, token = get_ms_token(request)
    if not token:
        return JsonResponse({"error": "Not connected"}, status=401)
    try:
        data = graph_get(token, "/me/presence")
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({"error": friendly_graph_error(e)}, status=500)


@login_required
def team_presence_api(request):
    """AJAX: Get presence for organization users (bulk)."""
    _, token = get_ms_token(request)
    if not token:
        return JsonResponse({"error": "Not connected"}, status=401)

    try:
        users_data = graph_get(token, "/users", {
            "$select": "id,displayName,mail,userPrincipalName,jobTitle,department",
            "$top": "50",
        })
        users = users_data.get("value", [])
        user_ids = [u["id"] for u in users if u.get("id")]

        if not user_ids:
            return JsonResponse({"users": [], "presences": []})

        presence_data = graph_post(token, "/communications/getPresencesByUserId", {
            "ids": user_ids[:50],
        })
        presences = presence_data.get("value", [])

        presence_map = {p["id"]: p for p in presences}
        for user in users:
            p = presence_map.get(user["id"], {})
            user["availability"] = p.get("availability", "Offline")
            user["activity"] = p.get("activity", "Offline")

        return JsonResponse({"users": users})
    except Exception as e:
        return JsonResponse({"error": friendly_graph_error(e)}, status=500)
