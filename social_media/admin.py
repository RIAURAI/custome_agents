from django.contrib import admin
from .models import SocialMediaAccount, SocialMediaPost, SocialMediaMessage, AutoReplyRule, BotConversationLog


@admin.register(SocialMediaAccount)
class SocialMediaAccountAdmin(admin.ModelAdmin):
    list_display = ("company", "platform", "account_name", "status", "connected_at")
    list_filter = ("platform", "status")
    search_fields = ("account_name", "account_id", "company__name")


@admin.register(SocialMediaPost)
class SocialMediaPostAdmin(admin.ModelAdmin):
    list_display = ("account", "status", "created_by", "created_at", "published_at")
    list_filter = ("status", "account__platform")
    search_fields = ("content",)


@admin.register(SocialMediaMessage)
class SocialMediaMessageAdmin(admin.ModelAdmin):
    list_display = ("account", "direction", "sender_name", "timestamp", "is_read")
    list_filter = ("direction", "is_read", "account__platform")
    search_fields = ("content", "sender_name", "sender_id")


@admin.register(AutoReplyRule)
class AutoReplyRuleAdmin(admin.ModelAdmin):
    list_display = ("company", "platform", "account", "is_enabled", "auto_send", "persona_name")
    list_filter = ("platform", "is_enabled", "auto_send")
    search_fields = ("company__name", "persona_name", "custom_instructions")


@admin.register(BotConversationLog)
class BotConversationLogAdmin(admin.ModelAdmin):
    list_display = ("account", "action", "ai_classification", "was_sent", "created_at")
    list_filter = ("action", "was_sent", "account__platform")
    search_fields = ("ai_summary", "ai_reply_text")
