"""
Teams Chat + Channel views.
Scopes required: Chat.ReadWrite, ChannelMessage.Send, Team.ReadBasic.All, Channel.ReadBasic.All
"""
import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from companies.middleware import has_platform_access, log_activity, ratelimit
from integrations.utils import graph_get, graph_post, friendly_graph_error
from microsoft.helpers import get_ms_token

logger = logging.getLogger(__name__)


@login_required
def chat_view(request):
    """Teams Chat inbox page."""
    integration, token = get_ms_token(request)
    ms_connected = integration is not None
    has_access = has_platform_access(request, "microsoft")

    chats = []
    error = None

    if ms_connected and has_access and token:
        try:
            data = graph_get(token, "/me/chats", {
                "$expand": "lastMessagePreview",
                "$top": "30",
                "$orderby": "lastMessagePreview/createdDateTime desc",
            })
            chats = data.get("value", [])
        except Exception as e:
            error = friendly_graph_error(e)

    if chats:
        log_activity(request, "chat_viewed", "microsoft", f"{len(chats)} chats")

    return render(request, "microsoft/chat.html", {
        "ms_connected": ms_connected,
        "has_access": bool(has_access),
        "chats": chats,
        "error": error,
    })


@login_required
def chat_messages_api(request, chat_id):
    """AJAX: Get messages for a specific chat."""
    _, token = get_ms_token(request)
    if not token:
        return JsonResponse({"error": "Not connected"}, status=401)
    try:
        data = graph_get(token, f"/me/chats/{chat_id}/messages", {
            "$top": "30",
            "$orderby": "createdDateTime desc",
        })
        messages_list = data.get("value", [])
        messages_list.reverse()
        return JsonResponse({"messages": messages_list})
    except Exception as e:
        return JsonResponse({"error": friendly_graph_error(e)}, status=500)


@login_required
@require_POST
@ratelimit(max_calls=20, period=60)
def send_chat_message_api(request, chat_id):
    """AJAX: Send a message to a chat."""
    _, token = get_ms_token(request)
    if not token:
        return JsonResponse({"error": "Not connected"}, status=401)
    try:
        body = json.loads(request.body)
        content = body.get("content", "").strip()
        if not content:
            return JsonResponse({"error": "Message cannot be empty"}, status=400)

        result = graph_post(token, f"/me/chats/{chat_id}/messages", {
            "body": {"content": content, "contentType": "text"},
        })
        log_activity(request, "chat_message_sent", "microsoft", content[:100])
        return JsonResponse({"message": result})
    except Exception as e:
        return JsonResponse({"error": friendly_graph_error(e)}, status=500)


@login_required
def teams_channels_api(request):
    """AJAX: List joined teams and their channels."""
    _, token = get_ms_token(request)
    if not token:
        return JsonResponse({"error": "Not connected"}, status=401)
    try:
        teams_data = graph_get(token, "/me/joinedTeams", {
            "$select": "id,displayName,description",
        })
        teams = teams_data.get("value", [])

        for team in teams:
            try:
                ch_data = graph_get(token, f"/teams/{team['id']}/channels", {
                    "$select": "id,displayName,description",
                })
                team["channels"] = ch_data.get("value", [])
            except Exception:
                team["channels"] = []

        return JsonResponse({"teams": teams})
    except Exception as e:
        return JsonResponse({"error": friendly_graph_error(e)}, status=500)


@login_required
def channel_messages_api(request, team_id, channel_id):
    """AJAX: Get messages from a Teams channel."""
    _, token = get_ms_token(request)
    if not token:
        return JsonResponse({"error": "Not connected"}, status=401)
    try:
        data = graph_get(token, f"/teams/{team_id}/channels/{channel_id}/messages", {
            "$top": "30",
        })
        messages_list = data.get("value", [])
        return JsonResponse({"messages": messages_list})
    except Exception as e:
        return JsonResponse({"error": friendly_graph_error(e)}, status=500)


@login_required
@require_POST
@ratelimit(max_calls=20, period=60)
def send_channel_message_api(request, team_id, channel_id):
    """AJAX: Send a message to a Teams channel."""
    _, token = get_ms_token(request)
    if not token:
        return JsonResponse({"error": "Not connected"}, status=401)
    try:
        body = json.loads(request.body)
        content = body.get("content", "").strip()
        if not content:
            return JsonResponse({"error": "Message cannot be empty"}, status=400)

        result = graph_post(token, f"/teams/{team_id}/channels/{channel_id}/messages", {
            "body": {"content": content, "contentType": "text"},
        })
        log_activity(request, "channel_message_sent", "microsoft", content[:100])
        return JsonResponse({"message": result})
    except Exception as e:
        return JsonResponse({"error": friendly_graph_error(e)}, status=500)
