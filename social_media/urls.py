from django.urls import path
from . import views, webhooks

app_name = "social_media"

urlpatterns = [
    # Dashboard
    path("", views.dashboard_view, name="dashboard"),
    path("setup-guide/", views.setup_guide, name="setup_guide"),

    # Account connections
    path("connect/<str:platform>/", views.connect_account, name="connect_account"),
    path("disconnect/<int:pk>/", views.disconnect_account, name="disconnect_account"),
    path("test-connection/<int:pk>/", views.test_connection, name="test_connection"),

    # Posts
    path("posts/", views.posts_list, name="posts_list"),
    path("posts/create/", views.create_post, name="create_post"),
    path("posts/<int:pk>/", views.post_detail, name="post_detail"),
    path("posts/<int:pk>/delete/", views.delete_post, name="delete_post"),

    # Messages
    path("messages/", views.messages_inbox, name="messages_inbox"),
    path("messages/<int:account_id>/<str:contact_id>/", views.conversation_view, name="conversation"),

    # AI Bot Settings
    path("bot/", views.bot_settings, name="bot_settings"),
    path("bot/rules/create/", views.create_bot_rule, name="create_bot_rule"),
    path("bot/rules/<int:pk>/edit/", views.edit_bot_rule, name="edit_bot_rule"),
    path("bot/rules/<int:pk>/delete/", views.delete_bot_rule, name="delete_bot_rule"),
    path("bot/rules/<int:pk>/toggle/", views.toggle_bot_rule, name="toggle_bot_rule"),
    path("bot/analytics/", views.bot_analytics, name="bot_analytics"),

    # Webhook endpoints (called by platforms)
    path("webhooks/whatsapp/", webhooks.whatsapp_webhook, name="webhook_whatsapp"),
    path("webhooks/facebook/", webhooks.facebook_webhook, name="webhook_facebook"),
    path("webhooks/instagram/", webhooks.facebook_webhook, name="webhook_instagram"),
    path("webhooks/linkedin/", webhooks.linkedin_webhook, name="webhook_linkedin"),
    path("webhooks/telegram/", webhooks.telegram_webhook, name="webhook_telegram"),
]
