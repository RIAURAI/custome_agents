from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import SlackMessage, AutoReplyRule


@admin.register(SlackMessage)
class SlackMessageAdmin(ModelAdmin):
    list_display = ("channel_name", "sender_name", "ai_classification", "is_auto_replied", "tracked_at")
    list_filter = ("ai_classification", "is_auto_replied", "company")
    search_fields = ("sender_name", "channel_name", "text", "ai_summary")
    readonly_fields = ("tracked_at",)
    date_hierarchy = "tracked_at"


@admin.register(AutoReplyRule)
class AutoReplyRuleAdmin(ModelAdmin):
    list_display = ("company", "channel_name", "is_enabled", "auto_send")
    list_filter = ("is_enabled", "auto_send", "company")
    search_fields = ("company__name", "channel_name", "channel_id")
