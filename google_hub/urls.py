from django.urls import path

from .views import gmail, calendar, meet, drive, docs, sheets, forms

app_name = "google_hub"

urlpatterns = [
    # ── Gmail ─────────────────────────────────────────────────────────
    path("", gmail.gmail_inbox, name="inbox"),
    path("sent/", gmail.gmail_sent, name="sent"),
    path("drafts/", gmail.gmail_drafts, name="drafts"),
    path("search/", gmail.gmail_search, name="search"),
    path("compose/", gmail.gmail_compose, name="compose"),
    path("message/<str:message_id>/", gmail.gmail_detail, name="detail"),
    path("api/gmail/draft/", gmail.gmail_save_draft, name="save_draft"),
    path("api/gmail/unread/", gmail.gmail_unread_count_api, name="unread_count"),
    path("api/gmail/labels/", gmail.gmail_labels_api, name="labels"),

    # ── Calendar ──────────────────────────────────────────────────────
    path("calendar/", calendar.calendar_view, name="calendar"),
    path("api/calendar/events/", calendar.calendar_events_api, name="calendar_events"),
    path("api/calendar/events/create/", calendar.calendar_event_create, name="calendar_event_create"),
    path("api/calendar/events/<str:event_id>/delete/", calendar.calendar_event_delete, name="calendar_event_delete"),
    path("api/calendar/events/<str:event_id>/", calendar.calendar_event_detail, name="calendar_event_detail"),

    # ── Meet ──────────────────────────────────────────────────────────
    path("meet/", meet.meet_view, name="meet"),
    path("meet/create/", meet.meet_create, name="meet_create"),

    # ── Drive ─────────────────────────────────────────────────────────
    path("drive/", drive.drive_view, name="drive"),
    path("api/drive/files/", drive.drive_list_api, name="drive_list"),
    path("api/drive/files/upload/", drive.drive_upload_api, name="drive_upload"),
    path("api/drive/files/<str:file_id>/download/", drive.drive_download_api, name="drive_download"),
    path("api/drive/files/<str:file_id>/delete/", drive.drive_delete_api, name="drive_delete"),

    # ── Docs ──────────────────────────────────────────────────────────
    path("docs/", docs.docs_view, name="docs"),
    path("api/docs/", docs.docs_list_api, name="docs_list"),
    path("api/docs/create/", docs.docs_create_api, name="docs_create"),
    path("api/docs/<str:document_id>/", docs.docs_get_api, name="docs_get"),

    # ── Sheets ────────────────────────────────────────────────────────
    path("sheets/", sheets.sheets_view, name="sheets"),
    path("api/sheets/", sheets.sheets_list_api, name="sheets_list"),
    path("api/sheets/create/", sheets.sheets_create_api, name="sheets_create"),
    path("api/sheets/<str:spreadsheet_id>/", sheets.sheets_get_api, name="sheets_get"),

    # ── Forms ─────────────────────────────────────────────────────────
    path("forms/", forms.forms_view, name="forms"),
    path("api/forms/", forms.forms_list_api, name="forms_list"),
    path("api/forms/create/", forms.forms_create_api, name="forms_create"),
    path("api/forms/<str:form_id>/", forms.forms_get_api, name="forms_get"),
]
