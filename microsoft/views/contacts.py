"""
Contacts / People views.
Scopes required: People.Read, User.ReadBasic.All
"""
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from companies.middleware import has_platform_access, log_activity
from integrations.utils import graph_get, friendly_graph_error
from microsoft.helpers import get_ms_token

logger = logging.getLogger(__name__)


@login_required
def people_view(request):
    """People & contacts page."""
    integration, token = get_ms_token(request)
    ms_connected = integration is not None
    has_access = has_platform_access(request, "microsoft")
    log_activity(request, "contacts_viewed", "microsoft")

    return render(request, "microsoft/contacts.html", {
        "ms_connected": ms_connected,
        "has_access": bool(has_access),
    })


@login_required
def people_api(request):
    """AJAX: Get relevant people for the current user."""
    _, token = get_ms_token(request)
    if not token:
        return JsonResponse({"error": "Not connected"}, status=401)
    try:
        data = graph_get(token, "/me/people", {
            "$top": "50",
            "$select": "displayName,givenName,surname,emailAddresses,phones,department,jobTitle,userPrincipalName,scoredEmailAddresses",
        })
        return JsonResponse({"people": data.get("value", [])})
    except Exception as e:
        return JsonResponse({"error": friendly_graph_error(e)}, status=500)


@login_required
def directory_api(request):
    """AJAX: Search org directory users."""
    _, token = get_ms_token(request)
    if not token:
        return JsonResponse({"error": "Not connected"}, status=401)

    query = request.GET.get("q", "").strip()
    try:
        params = {
            "$select": "id,displayName,mail,userPrincipalName,jobTitle,department,officeLocation",
            "$top": "50",
        }
        if query:
            params["$filter"] = (
                f"startswith(displayName,'{query}') or startswith(mail,'{query}')"
            )
        data = graph_get(token, "/users", params)
        return JsonResponse({"users": data.get("value", [])})
    except Exception as e:
        return JsonResponse({"error": friendly_graph_error(e)}, status=500)
