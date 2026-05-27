"""
Microsoft To Do & Planner views.
Scopes required: Tasks.ReadWrite, Group.Read.All (for Planner)
"""
import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from companies.middleware import has_platform_access, log_activity, ratelimit
from integrations.utils import (
    graph_get, graph_post, graph_patch, graph_delete, friendly_graph_error,
)
from microsoft.helpers import get_ms_token

logger = logging.getLogger(__name__)


# ── To Do ───────────────────────────────────────────────────────────

@login_required
def todo_view(request):
    """To Do main page."""
    integration, token = get_ms_token(request)
    ms_connected = integration is not None
    has_access = has_platform_access(request, "microsoft")

    lists_data = []
    error = None
    if token:
        try:
            data = graph_get(token, "/me/todo/lists", {"$top": "50"})
            lists_data = data.get("value", [])
        except Exception as e:
            error = friendly_graph_error(e)

    if lists_data:
        log_activity(request, "todo_viewed", "microsoft", f"{len(lists_data)} lists")

    return render(request, "microsoft/todo.html", {
        "ms_connected": ms_connected,
        "has_access": bool(has_access),
        "todo_lists": lists_data,
        "error": error,
    })


@login_required
def todo_tasks_api(request, list_id):
    """AJAX: Get tasks for a To Do list."""
    _, token = get_ms_token(request)
    if not token:
        return JsonResponse({"error": "Not connected"}, status=401)
    try:
        data = graph_get(token, f"/me/todo/lists/{list_id}/tasks", {
            "$top": "100",
            "$orderby": "createdDateTime desc",
        })
        return JsonResponse({"tasks": data.get("value", [])})
    except Exception as e:
        return JsonResponse({"error": friendly_graph_error(e)}, status=500)


@login_required
@require_POST
@ratelimit(max_calls=20, period=60)
def create_task_api(request, list_id):
    """Create a new task in a To Do list."""
    _, token = get_ms_token(request)
    if not token:
        return JsonResponse({"error": "Not connected"}, status=401)
    try:
        body = json.loads(request.body)
        title = body.get("title", "").strip()
        if not title:
            return JsonResponse({"error": "Title required"}, status=400)
        payload = {"title": title}
        if body.get("dueDateTime"):
            payload["dueDateTime"] = {
                "dateTime": body["dueDateTime"] + "T00:00:00",
                "timeZone": "UTC",
            }
        if body.get("importance"):
            payload["importance"] = body["importance"]
        result = graph_post(token, f"/me/todo/lists/{list_id}/tasks", payload)
        log_activity(request, "todo_created", "microsoft", title[:200])
        return JsonResponse({"task": result})
    except Exception as e:
        return JsonResponse({"error": friendly_graph_error(e)}, status=500)


@login_required
@require_POST
@ratelimit(max_calls=30, period=60)
def update_task_api(request, list_id, task_id):
    """Update a task (toggle complete, edit title, etc)."""
    _, token = get_ms_token(request)
    if not token:
        return JsonResponse({"error": "Not connected"}, status=401)
    try:
        body = json.loads(request.body)
        result = graph_patch(token, f"/me/todo/lists/{list_id}/tasks/{task_id}", body)
        log_activity(request, "todo_updated", "microsoft")
        return JsonResponse({"task": result})
    except Exception as e:
        return JsonResponse({"error": friendly_graph_error(e)}, status=500)


@login_required
@require_POST
@ratelimit(max_calls=15, period=60)
def delete_task_api(request, list_id, task_id):
    """Delete a task."""
    _, token = get_ms_token(request)
    if not token:
        return JsonResponse({"error": "Not connected"}, status=401)
    try:
        graph_delete(token, f"/me/todo/lists/{list_id}/tasks/{task_id}")
        log_activity(request, "todo_deleted", "microsoft")
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": friendly_graph_error(e)}, status=500)


@login_required
@require_POST
def create_list_api(request):
    """Create a new To Do list."""
    _, token = get_ms_token(request)
    if not token:
        return JsonResponse({"error": "Not connected"}, status=401)
    try:
        body = json.loads(request.body)
        name = body.get("displayName", "").strip()
        if not name:
            return JsonResponse({"error": "Name required"}, status=400)
        result = graph_post(token, "/me/todo/lists", {"displayName": name})
        return JsonResponse({"list": result})
    except Exception as e:
        return JsonResponse({"error": friendly_graph_error(e)}, status=500)


# ── Planner ─────────────────────────────────────────────────────────

@login_required
def planner_view(request):
    """Planner page."""
    integration, token = get_ms_token(request)
    ms_connected = integration is not None
    has_access = has_platform_access(request, "microsoft")

    plans = []
    error = None
    if token:
        try:
            data = graph_get(token, "/me/planner/tasks", {"$top": "100"})
            plans = data.get("value", [])
        except Exception as e:
            error = friendly_graph_error(e)

    if plans:
        log_activity(request, "planner_viewed", "microsoft", f"{len(plans)} tasks")

    return render(request, "microsoft/planner.html", {
        "ms_connected": ms_connected,
        "has_access": bool(has_access),
        "planner_tasks": plans,
        "error": error,
    })


@login_required
def planner_tasks_api(request):
    """AJAX: Get all planner tasks for the current user."""
    _, token = get_ms_token(request)
    if not token:
        return JsonResponse({"error": "Not connected"}, status=401)
    try:
        data = graph_get(token, "/me/planner/tasks", {"$top": "100"})
        return JsonResponse({"tasks": data.get("value", [])})
    except Exception as e:
        return JsonResponse({"error": friendly_graph_error(e)}, status=500)
