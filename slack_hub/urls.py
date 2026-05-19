from django.urls import path
from . import views

app_name = "slack_hub"

urlpatterns = [
    path("", views.channels_view, name="channels"),
    path("channel/<str:channel_id>/", views.channel_messages_view, name="channel_messages"),
    path("track/", views.track_view, name="track"),
    path("settings/", views.auto_reply_settings_view, name="settings"),
    # AI endpoints (JSON API)
    path("ai/analyze/", views.ai_analyze_view, name="ai_analyze"),
    path("ai/reply/", views.ai_reply_view, name="ai_reply"),
    path("ai/summarize/", views.ai_summarize_channel_view, name="ai_summarize"),
]
