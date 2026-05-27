"""
google_hub/views/__init__.py
Re-exports every view so urls.py can use the package like individual modules.
"""
from .gmail import (
    gmail_inbox, gmail_detail, gmail_compose,
    gmail_sent, gmail_drafts, gmail_search,
    gmail_unread_count_api, gmail_labels_api, gmail_save_draft,
)
from .calendar import (
    calendar_view, calendar_events_api,
    calendar_event_create, calendar_event_delete, calendar_event_detail,
)
from .meet import meet_view, meet_create
from .drive import drive_view, drive_list_api, drive_upload_api, drive_download_api, drive_delete_api
from .docs import docs_view, docs_list_api, docs_get_api, docs_create_api
from .sheets import sheets_view, sheets_list_api, sheets_get_api, sheets_create_api
from .forms import forms_view, forms_list_api, forms_get_api, forms_create_api
