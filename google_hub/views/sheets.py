"""
Google Sheets views.
Scopes required: spreadsheets.readonly (read) + spreadsheets (create/write)
"""
import json
import logging

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from companies.middleware import has_platform_access, log_activity, platform_access_required
from integrations.google_utils import google_api_get, google_api_post
from google_hub.helpers import get_google_token

logger = logging.getLogger(__name__)

SHEETS_API = "https://sheets.googleapis.com/v4/spreadsheets"
DRIVE_API = "https://www.googleapis.com/drive/v3"


# ── Page View ──────────────────────────────────────────────────────────────────

@platform_access_required("google")
def sheets_view(request):
    """Google Sheets list page."""
    integration, token = get_google_token(request)
    google_connected = integration is not None
    has_access = has_platform_access(request, "google")

    if not token:
        if integration:
            logger.warning("Google token expired for company %s — Sheets page loaded without auth", getattr(request, 'company', 'unknown'))
        else:
            logger.warning("Google not connected for company %s — Sheets page accessed", getattr(request, 'company', 'unknown'))
        return render(request, "google_hub/sheets.html", {
            "google_connected": False,
            "has_access": bool(has_access),
            "error": "Google session expired. Please reconnect." if integration else None,
        })

    log_activity(request, "sheets_viewed", "google")
    return render(request, "google_hub/sheets.html", {
        "google_connected": google_connected,
        "has_access": bool(has_access),
    })


# ── API Endpoints ──────────────────────────────────────────────────────────────

@platform_access_required("google")
def sheets_list_api(request):
    """AJAX: List Google Sheets spreadsheets from Drive."""
    _, token = get_google_token(request)
    if not token:
        return JsonResponse({"error": "Google session expired."}, status=401)

    search_q = request.GET.get("q", "").strip()
    query = "mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
    if search_q:
        query += f" and name contains '{search_q}'"

    try:
        data = google_api_get(token, f"{DRIVE_API}/files", {
            "q": query,
            "fields": "files(id,name,modifiedTime,webViewLink,owners)",
            "pageSize": 50,
            "orderBy": "modifiedTime desc",
        })
        sheets = data.get("files", [])
        return JsonResponse({"sheets": sheets})
    except Exception as e:
        logger.exception("sheets_list_api error")
        return JsonResponse({"error": str(e)}, status=500)


@platform_access_required("google")
def sheets_get_api(request, spreadsheet_id):
    """AJAX: Fetch metadata + values from a spreadsheet.
    Query param: range (e.g. 'Sheet1!A1:Z100') — defaults to first sheet.
    """
    _, token = get_google_token(request)
    if not token:
        return JsonResponse({"error": "Google session expired."}, status=401)

    cell_range = request.GET.get("range", "")

    try:
        meta = google_api_get(token, f"{SHEETS_API}/{spreadsheet_id}", {
            "fields": "spreadsheetId,properties,sheets.properties",
        })

        values_data = {}
        if cell_range:
            values_data = google_api_get(
                token,
                f"{SHEETS_API}/{spreadsheet_id}/values/{cell_range}",
            )

        log_activity(request, "sheet_read", "google",
                     meta.get("properties", {}).get("title", spreadsheet_id)[:200])
        return JsonResponse({"spreadsheet": meta, "values": values_data})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@platform_access_required("google", "reply")
@require_POST
def sheets_create_api(request):
    """AJAX: Create a new Google Sheets spreadsheet."""
    _, token = get_google_token(request)
    if not token:
        return JsonResponse({"error": "Google session expired."}, status=401)

    try:
        body = json.loads(request.body)
    except (ValueError, KeyError):
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    title = body.get("title", "Untitled Spreadsheet").strip()
    if not title:
        return JsonResponse({"error": "Title is required."}, status=400)

    try:
        sheet = google_api_post(token, SHEETS_API, {
            "properties": {"title": title},
        })
        log_activity(request, "sheet_created", "google", title[:200])
        return JsonResponse({"ok": True, "spreadsheet": sheet})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
