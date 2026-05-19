from django.urls import path
from . import views

app_name = "integrations"

urlpatterns = [
    path("", views.connect_view, name="connect"),
    path("microsoft/connect/", views.microsoft_connect, name="microsoft_connect"),
    path("callback/", views.microsoft_callback, name="callback"),
    path("microsoft/disconnect/", views.microsoft_disconnect, name="microsoft_disconnect"),
    # Slack
    path("slack/connect/", views.slack_connect, name="slack_connect"),
    path("slack/callback/", views.slack_callback, name="slack_callback"),
    path("slack/disconnect/", views.slack_disconnect, name="slack_disconnect"),
]
