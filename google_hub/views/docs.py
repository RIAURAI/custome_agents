"""
Google Docs views.
Scopes required: documents.readonly (read) + documents (create/write)
"""
import logging

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from companies.middleware import has_platform_access, log_activity, platform_access_required
from integrations.google_utils import google_api_get, google_api_post
from google_hub.helpers import get_google_token

logger = logging.getLogger(__name__)

DOCS_API = "https://docs.googleapis.com/v1/documents"
DRIVE_API = "https://www.googleapis.com/drive/v3"


# ── Page View ──────────────────────────────────────────────────────────────────

@platform_access_required("google")
def docs_view(request):
    """Google Docs list page."""
    integration, token = get_google_token(request)
    google_connected = integration is not None
    has_access = has_platform_access(request, "google")

    if not token:
        if integration:
            logger.warning("Google token expired for company %s — Docs page loaded without auth", getattr(request, 'company', 'unknown'))
        else:
            logger.warning("Google not connected for company %s — Docs page accessed", getattr(request, 'company', 'unknown'))
        return render(request, "google_hub/docs.html", {
            "google_connected": False,
            "has_access": bool(has_access),
            "error": "Google session expired. Please reconnect." if integration else None,
        })

    log_activity(request, "docs_viewed", "google")
    return render(request, "google_hub/docs.html", {
        "google_connected": google_connected,
        "has_access": bool(has_access),
    })


# ── API Endpoints ──────────────────────────────────────────────────────────────

@platform_access_required("google")
def docs_list_api(request):
    """AJAX: List Google Docs documents from Drive."""
    _, token = get_google_token(request)
    if not token:
        return JsonResponse({"error": "Google session expired."}, status=401)

    search_q = request.GET.get("q", "").strip()
    query = "mimeType='application/vnd.google-apps.document' and trashed=false"
    if search_q:
        query += f" and name contains '{search_q}'"

    try:
        data = google_api_get(token, f"{DRIVE_API}/files", {
            "q": query,
            "fields": "files(id,name,modifiedTime,webViewLink,owners)",
            "pageSize": 50,
            "orderBy": "modifiedTime desc",
        })
        docs = data.get("files", [])
        return JsonResponse({"docs": docs})
    except Exception as e:
        logger.exception("docs_list_api error")
        return JsonResponse({"error": str(e)}, status=500)


@platform_access_required("google")
def docs_get_api(request, document_id):
    """AJAX: Fetch full content of a Google Doc."""
    _, token = get_google_token(request)
    if not token:
        return JsonResponse({"error": "Google session expired."}, status=401)

    try:
        doc = google_api_get(token, f"{DOCS_API}/{document_id}")
        log_activity(request, "doc_read", "google", doc.get("title", document_id)[:200])
        return JsonResponse({"doc": doc})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@platform_access_required("google", "reply")
@require_POST
def docs_create_api(request):
    """AJAX: Create a new Google Doc."""
    _, token = get_google_token(request)
    if not token:
        return JsonResponse({"error": "Google session expired."}, status=401)

    import json
    try:
        body = json.loads(request.body)
    except (ValueError, KeyError):
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    title = body.get("title", "Untitled Document").strip()
    if not title:
        return JsonResponse({"error": "Title is required."}, status=400)

    try:
        doc = google_api_post(token, DOCS_API, {"title": title})
        log_activity(request, "doc_created", "google", title[:200])
        return JsonResponse({"ok": True, "doc": doc})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
