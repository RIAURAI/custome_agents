"""
OneDrive file browser views.
Scopes required: Files.ReadWrite
"""
import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from companies.middleware import has_platform_access, log_activity, ratelimit
from integrations.utils import (
    graph_get, graph_post, graph_put, graph_delete, friendly_graph_error,
)
from microsoft.helpers import get_ms_token

import requests as http_requests

logger = logging.getLogger(__name__)


@login_required
def browser_view(request):
    """OneDrive file browser page."""
    integration, token = get_ms_token(request)
    ms_connected = integration is not None
    has_access = has_platform_access(request, "microsoft")
    log_activity(request, "onedrive_browsed", "microsoft")

    return render(request, "microsoft/onedrive.html", {
        "ms_connected": ms_connected,
        "has_access": bool(has_access),
    })


@login_required
def list_files_api(request):
    """AJAX: List files/folders at a path. Query param: item_id (empty = root)."""
    _, token = get_ms_token(request)
    if not token:
        return JsonResponse({"error": "Not connected"}, status=401)

    item_id = request.GET.get("item_id", "")
    try:
        if item_id:
            endpoint = f"/me/drive/items/{item_id}/children"
        else:
            endpoint = "/me/drive/root/children"

        data = graph_get(token, endpoint, {
            "$select": "id,name,size,lastModifiedDateTime,folder,file,webUrl,parentReference",
            "$top": "100",
            "$orderby": "name",
        })
        items = data.get("value", [])

        if item_id:
            folder_info = graph_get(token, f"/me/drive/items/{item_id}", {
                "$select": "id,name,parentReference",
            })
        else:
            folder_info = {"id": "root", "name": "My Files"}

        return JsonResponse({"items": items, "folder": folder_info})
    except Exception as e:
        return JsonResponse({"error": friendly_graph_error(e)}, status=500)


@login_required
def search_files_api(request):
    """AJAX: Search files in OneDrive."""
    _, token = get_ms_token(request)
    if not token:
        return JsonResponse({"error": "Not connected"}, status=401)

    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"items": []})

    try:
        data = graph_get(token, f"/me/drive/root/search(q='{query}')", {
            "$select": "id,name,size,lastModifiedDateTime,folder,file,webUrl,parentReference",
            "$top": "30",
        })
        return JsonResponse({"items": data.get("value", [])})
    except Exception as e:
        return JsonResponse({"error": friendly_graph_error(e)}, status=500)


@login_required
def download_file_api(request, item_id):
    """Proxy download — streams file from OneDrive to user."""
    _, token = get_ms_token(request)
    if not token:
        return JsonResponse({"error": "Not connected"}, status=401)

    try:
        item = graph_get(token, f"/me/drive/items/{item_id}", {
            "$select": "name,@microsoft.graph.downloadUrl",
        })
        download_url = item.get("@microsoft.graph.downloadUrl")
        if not download_url:
            return JsonResponse({"error": "Download not available"}, status=404)

        resp = http_requests.get(download_url, stream=True, timeout=60)
        response = HttpResponse(
            resp.iter_content(chunk_size=8192),
            content_type=resp.headers.get("Content-Type", "application/octet-stream"),
        )
        response["Content-Disposition"] = f'attachment; filename="{item.get("name", "file")}"'
        log_activity(request, "onedrive_downloaded", "microsoft", item.get("name", "")[:200])
        return response
    except Exception as e:
        return JsonResponse({"error": friendly_graph_error(e)}, status=500)


@login_required
@require_POST
@ratelimit(max_calls=10, period=60)
def upload_file_api(request):
    """Upload a file to OneDrive. Uses simple upload for <4MB."""
    _, token = get_ms_token(request)
    if not token:
        return JsonResponse({"error": "Not connected"}, status=401)

    uploaded = request.FILES.get("file")
    if not uploaded:
        return JsonResponse({"error": "No file provided"}, status=400)

    parent_id = request.POST.get("parent_id", "")
    filename = uploaded.name

    try:
        if parent_id:
            endpoint = f"/me/drive/items/{parent_id}:/{filename}:/content"
        else:
            endpoint = f"/me/drive/root:/{filename}:/content"

        data = uploaded.read()
        result = graph_put(token, endpoint, data, content_type=uploaded.content_type or "application/octet-stream")
        log_activity(request, "onedrive_uploaded", "microsoft", filename[:200])
        return JsonResponse({"item": result})
    except Exception as e:
        return JsonResponse({"error": friendly_graph_error(e)}, status=500)


@login_required
@require_POST
def create_folder_api(request):
    """Create a new folder in OneDrive."""
    _, token = get_ms_token(request)
    if not token:
        return JsonResponse({"error": "Not connected"}, status=401)

    try:
        body = json.loads(request.body)
        name = body.get("name", "").strip()
        parent_id = body.get("parent_id", "")

        if not name:
            return JsonResponse({"error": "Folder name required"}, status=400)

        if parent_id:
            endpoint = f"/me/drive/items/{parent_id}/children"
        else:
            endpoint = "/me/drive/root/children"

        result = graph_post(token, endpoint, {
            "name": name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "rename",
        })
        return JsonResponse({"item": result})
    except Exception as e:
        return JsonResponse({"error": friendly_graph_error(e)}, status=500)


@login_required
@require_POST
@ratelimit(max_calls=10, period=60)
def delete_item_api(request, item_id):
    """Delete a file or folder from OneDrive."""
    _, token = get_ms_token(request)
    if not token:
        return JsonResponse({"error": "Not connected"}, status=401)

    try:
        graph_delete(token, f"/me/drive/items/{item_id}")
        log_activity(request, "onedrive_deleted", "microsoft", item_id)
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": friendly_graph_error(e)}, status=500)


@login_required
@require_POST
def share_link_api(request, item_id):
    """Create a sharing link for a file."""
    _, token = get_ms_token(request)
    if not token:
        return JsonResponse({"error": "Not connected"}, status=401)

    try:
        result = graph_post(token, f"/me/drive/items/{item_id}/createLink", {
            "type": "view",
            "scope": "organization",
        })
        link = result.get("link", {}).get("webUrl", "")
        log_activity(request, "onedrive_shared", "microsoft", link[:200])
        return JsonResponse({"link": link})
    except Exception as e:
        return JsonResponse({"error": friendly_graph_error(e)}, status=500)
