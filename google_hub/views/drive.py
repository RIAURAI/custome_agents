"""
Google Drive views.
Scopes required: drive (full access — all files, images, PDFs, videos)
"""
import logging

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from companies.middleware import has_platform_access, log_activity, platform_access_required
from integrations.google_utils import google_api_get, google_api_post
from google_hub.helpers import get_google_token

logger = logging.getLogger(__name__)

DRIVE_API = "https://www.googleapis.com/drive/v3"


# ── Page View ──────────────────────────────────────────────────────────────────

@platform_access_required("google")
def drive_view(request):
    """Google Drive file browser page."""
    integration, token = get_google_token(request)
    google_connected = integration is not None
    has_access = has_platform_access(request, "google")

    if not token:
        if integration:
            logger.warning("Google token expired for company %s — Drive page loaded without auth", getattr(request, 'company', 'unknown'))
        else:
            logger.warning("Google not connected for company %s — Drive page accessed", getattr(request, 'company', 'unknown'))
        return render(request, "google_hub/drive.html", {
            "google_connected": False,
            "has_access": bool(has_access),
            "error": "Google session expired. Please reconnect." if integration else None,
        })

    log_activity(request, "drive_browsed", "google")
    return render(request, "google_hub/drive.html", {
        "google_connected": google_connected,
        "has_access": bool(has_access),
    })


# ── API Endpoints ──────────────────────────────────────────────────────────────

@platform_access_required("google")
def drive_list_api(request):
    """AJAX: List files in Google Drive. Query params: folder_id, q (search)."""
    _, token = get_google_token(request)
    if not token:
        return JsonResponse({"error": "Google session expired."}, status=401)

    folder_id = request.GET.get("folder_id", "root")
    search_q = request.GET.get("q", "").strip()

    try:
        if search_q:
            query = f"name contains '{search_q}' and trashed = false"
        else:
            query = f"'{folder_id}' in parents and trashed = false"

        data = google_api_get(token, f"{DRIVE_API}/files", {
            "q": query,
            "fields": "files(id,name,mimeType,size,modifiedTime,webViewLink,parents,iconLink)",
            "pageSize": 100,
            "orderBy": "folder,name",
        })
        files = data.get("files", [])
        log_activity(request, "drive_listed", "google", f"{len(files)} files")
        return JsonResponse({"files": files})
    except Exception as e:
        logger.exception("drive_list_api error")
        return JsonResponse({"error": str(e)}, status=500)


@platform_access_required("google")
def drive_download_api(request, file_id):
    """AJAX: Get a download/export link for a Drive file."""
    _, token = get_google_token(request)
    if not token:
        return JsonResponse({"error": "Google session expired."}, status=401)

    try:
        meta = google_api_get(token, f"{DRIVE_API}/files/{file_id}", {
            "fields": "id,name,mimeType,webViewLink,webContentLink",
        })
        return JsonResponse({"file": meta})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@platform_access_required("google", "reply")
@require_POST
def drive_upload_api(request):
    """Upload a file to Google Drive (multipart, ≤ 5 MB simple upload)."""
    import requests as http_req

    _, token = get_google_token(request)
    if not token:
        return JsonResponse({"error": "Google session expired."}, status=401)

    uploaded = request.FILES.get("file")
    folder_id = request.POST.get("folder_id", "")
    if not uploaded:
        return JsonResponse({"error": "No file provided."}, status=400)

    if uploaded.size > 5 * 1024 * 1024:
        return JsonResponse({"error": "File too large (max 5 MB for simple upload)."}, status=400)

    metadata = {"name": uploaded.name}
    if folder_id:
        metadata["parents"] = [folder_id]

    try:
        resp = http_req.post(
            "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
            headers={"Authorization": f"Bearer {token}"},
            files={
                "metadata": (None, str(metadata).replace("'", '"'), "application/json"),
                "file": (uploaded.name, uploaded.read(), uploaded.content_type),
            },
            timeout=30,
        )
        resp.raise_for_status()
        log_activity(request, "drive_uploaded", "google", uploaded.name)
        return JsonResponse({"ok": True, "file": resp.json()})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@platform_access_required("google", "reply")
@require_POST
def drive_delete_api(request, file_id):
    """Move a Drive file to trash."""
    import requests as http_req

    _, token = get_google_token(request)
    if not token:
        return JsonResponse({"error": "Google session expired."}, status=401)

    try:
        resp = http_req.patch(
            f"{DRIVE_API}/files/{file_id}",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"trashed": True},
            timeout=15,
        )
        resp.raise_for_status()
        log_activity(request, "drive_deleted", "google", file_id)
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
