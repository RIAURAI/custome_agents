from django.contrib import admin

from .models import DiscordMessage, DiscordAutoReplyRule


@admin.register(DiscordMessage)
class DiscordMessageAdmin(admin.ModelAdmin):
    list_display = (
        "sender_name", "channel_name", "guild_name",
        "ai_classification", "is_auto_replied", "is_dm", "tracked_at",
    )
    list_filter = ("ai_classification", "is_auto_replied", "is_dm")
    search_fields = ("sender_name", "text", "channel_name")
    readonly_fields = ("tracked_at",)


@admin.register(DiscordAutoReplyRule)
class DiscordAutoReplyRuleAdmin(admin.ModelAdmin):
    list_display = ("company", "channel_name", "channel_id", "is_enabled", "auto_send")
    list_filter = ("is_enabled", "auto_send")
    search_fields = ("channel_name", "channel_id")

