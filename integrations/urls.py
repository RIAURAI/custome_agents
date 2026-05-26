from django.urls import path
from . import views

app_name = "integrations"

urlpatterns = [
    path("", views.connect_view, name="connect"),
    path("microsoft/save-credentials/", views.microsoft_save_credentials, name="microsoft_save_credentials"),
    path("microsoft/save-features/", views.microsoft_save_features, name="microsoft_save_features"),
    path("microsoft/connect/", views.microsoft_connect, name="microsoft_connect"),
    path("callback/", views.microsoft_callback, name="callback"),
    path("microsoft/disconnect/", views.microsoft_disconnect, name="microsoft_disconnect"),
    # Slack
    path("slack/connect/", views.slack_connect, name="slack_connect"),
    path("slack/callback/", views.slack_callback, name="slack_callback"),
    path("slack/disconnect/", views.slack_disconnect, name="slack_disconnect"),
    # Slack — dynamic manual credential entry (per-user, no OAuth app required)
    path("slack/manual-connect/", views.slack_manual_connect, name="slack_manual_connect"),
    # Calendly
    path("calendly/save-credentials/", views.calendly_save_credentials, name="calendly_save_credentials"),
    path("calendly/connect/", views.calendly_connect, name="calendly_connect"),
    path("calendly/callback/", views.calendly_callback, name="calendly_callback"),
    path("calendly/disconnect/", views.calendly_disconnect, name="calendly_disconnect"),
]
