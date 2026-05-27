"""
Google Forms views.
Scopes required: forms.body.readonly (read) + forms.body (create/write)
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

FORMS_API = "https://forms.googleapis.com/v1/forms"
DRIVE_API = "https://www.googleapis.com/drive/v3"


# ── Page View ──────────────────────────────────────────────────────────────────

@platform_access_required("google")
def forms_view(request):
    """Google Forms list page."""
    integration, token = get_google_token(request)
    google_connected = integration is not None
    has_access = has_platform_access(request, "google")

    if not token:
        if integration:
            logger.warning("Google token expired for company %s — Forms page loaded without auth", getattr(request, 'company', 'unknown'))
        else:
            logger.warning("Google not connected for company %s — Forms page accessed", getattr(request, 'company', 'unknown'))
        return render(request, "google_hub/forms.html", {
            "google_connected": False,
            "has_access": bool(has_access),
            "error": "Google session expired. Please reconnect." if integration else None,
        })

    log_activity(request, "forms_viewed", "google")
    return render(request, "google_hub/forms.html", {
        "google_connected": google_connected,
        "has_access": bool(has_access),
    })


# ── API Endpoints ──────────────────────────────────────────────────────────────

@platform_access_required("google")
def forms_list_api(request):
    """AJAX: List Google Forms from Drive."""
    _, token = get_google_token(request)
    if not token:
        return JsonResponse({"error": "Google session expired."}, status=401)

    search_q = request.GET.get("q", "").strip()
    query = "mimeType='application/vnd.google-apps.form' and trashed=false"
    if search_q:
        query += f" and name contains '{search_q}'"

    try:
        data = google_api_get(token, f"{DRIVE_API}/files", {
            "q": query,
            "fields": "files(id,name,modifiedTime,webViewLink,owners)",
            "pageSize": 50,
            "orderBy": "modifiedTime desc",
        })
        forms = data.get("files", [])
        return JsonResponse({"forms": forms})
    except Exception as e:
        logger.exception("forms_list_api error")
        return JsonResponse({"error": str(e)}, status=500)


@platform_access_required("google")
def forms_get_api(request, form_id):
    """AJAX: Fetch a Google Form (structure + questions)."""
    _, token = get_google_token(request)
    if not token:
        return JsonResponse({"error": "Google session expired."}, status=401)

    try:
        form = google_api_get(token, f"{FORMS_API}/{form_id}")
        log_activity(request, "form_read", "google",
                     form.get("info", {}).get("title", form_id)[:200])
        return JsonResponse({"form": form})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@platform_access_required("google", "reply")
@require_POST
def forms_create_api(request):
    """AJAX: Create a new Google Form."""
    _, token = get_google_token(request)
    if not token:
        return JsonResponse({"error": "Google session expired."}, status=401)

    try:
        body = json.loads(request.body)
    except (ValueError, KeyError):
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    title = body.get("title", "Untitled Form").strip()
    description = body.get("description", "")
    if not title:
        return JsonResponse({"error": "Title is required."}, status=400)

    try:
        form = google_api_post(token, FORMS_API, {
            "info": {"title": title, "documentTitle": title},
        })
        log_activity(request, "form_created", "google", title[:200])
        return JsonResponse({"ok": True, "form": form})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
