from django.db import models
from django.conf import settings


class SocialMediaAccount(models.Model):
    """A connected social media account for a company."""

    PLATFORM_CHOICES = [
        ("whatsapp", "WhatsApp Business"),
        ("linkedin", "LinkedIn"),
        ("facebook", "Facebook"),
        ("instagram", "Instagram"),
        ("telegram", "Telegram"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("expired", "Token Expired"),
        ("disconnected", "Disconnected"),
        ("error", "Error"),
    ]

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="social_accounts",
    )
    platform = models.CharField(max_length=30, choices=PLATFORM_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    # Account info
    account_name = models.CharField(max_length=255, blank=True)
    account_id = models.CharField(max_length=255, blank=True)
    profile_url = models.URLField(max_length=500, blank=True)

    # Encrypted tokens
    access_token_enc = models.BinaryField(null=True, blank=True)
    refresh_token_enc = models.BinaryField(null=True, blank=True)
    token_expiry = models.DateTimeField(null=True, blank=True)

    # Platform-specific fields
    page_id = models.CharField(max_length=255, blank=True, help_text="Facebook/Instagram Page ID")
    phone_number_id = models.CharField(max_length=100, blank=True, help_text="WhatsApp Business Phone Number ID")
    waba_id = models.CharField(max_length=100, blank=True, help_text="WhatsApp Business Account ID")
    telegram_bot_username = models.CharField(max_length=100, blank=True, help_text="Telegram Bot @username")
    telegram_chat_id = models.CharField(max_length=100, blank=True, help_text="Default Telegram Chat/Group ID")
    api_key_enc = models.BinaryField(null=True, blank=True, help_text="Encrypted API Key / App Secret")
    webhook_secret = models.CharField(max_length=255, blank=True, help_text="Webhook verification token")
    webhook_url = models.URLField(max_length=500, blank=True, help_text="Platform webhook callback URL")

    # Permissions — what this connection is allowed to do
    can_read_messages = models.BooleanField(default=True, help_text="Permission to read incoming messages")
    can_send_messages = models.BooleanField(default=False, help_text="Permission to send/reply to messages")
    can_auto_reply = models.BooleanField(default=False, help_text="Permission for AI bot auto-reply")
    can_post_content = models.BooleanField(default=False, help_text="Permission to publish posts")

    # Connection test info
    last_tested_at = models.DateTimeField(null=True, blank=True)
    last_test_result = models.CharField(max_length=255, blank=True)

    connected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="connected_social_accounts",
    )
    connected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("company", "platform", "account_id")
        ordering = ["-connected_at"]

    def __str__(self):
        return f"{self.company.name} — {self.get_platform_display()} ({self.account_name})"


class SocialMediaPost(models.Model):
    """A post/message published or scheduled on social media."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("scheduled", "Scheduled"),
        ("published", "Published"),
        ("failed", "Failed"),
    ]

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="social_posts",
    )
    account = models.ForeignKey(
        SocialMediaAccount,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    content = models.TextField(help_text="Post content / message text")
    media_url = models.URLField(max_length=1000, blank=True, help_text="Attached image/video URL")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    platform_post_id = models.CharField(max_length=255, blank=True, help_text="ID returned by platform after publishing")

    scheduled_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.account.get_platform_display()} post — {self.status}"


class SocialMediaMessage(models.Model):
    """Incoming/outgoing messages (WhatsApp, LinkedIn DMs, etc.)."""

    DIRECTION_CHOICES = [
        ("inbound", "Inbound"),
        ("outbound", "Outbound"),
    ]

    account = models.ForeignKey(
        SocialMediaAccount,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    sender_name = models.CharField(max_length=255, blank=True)
    sender_id = models.CharField(max_length=255, blank=True)
    recipient_id = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    message_type = models.CharField(max_length=50, default="text", help_text="text, image, video, document, etc.")
    platform_message_id = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField()
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.direction} — {self.sender_name or self.sender_id}"


class AutoReplyRule(models.Model):
    """Company-configurable auto-reply rules for social media platforms."""

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="social_auto_rules",
    )
    account = models.ForeignKey(
        SocialMediaAccount,
        on_delete=models.CASCADE,
        related_name="auto_reply_rules",
        null=True,
        blank=True,
        help_text="Leave blank to apply to all accounts of this platform.",
    )
    platform = models.CharField(max_length=30, choices=SocialMediaAccount.PLATFORM_CHOICES)
    is_enabled = models.BooleanField(default=False)
    auto_send = models.BooleanField(default=False, help_text="Send reply without human confirmation")

    # Filters
    keywords = models.TextField(
        blank=True,
        help_text="Comma-separated keywords that trigger auto-reply. Empty = reply to all.",
    )
    reply_to_dms = models.BooleanField(default=True, help_text="Auto-reply to direct messages")
    reply_to_comments = models.BooleanField(default=False, help_text="Auto-reply to post comments")
    reply_to_groups = models.BooleanField(default=False, help_text="Auto-reply in group chats")

    # AI instructions
    custom_instructions = models.TextField(
        blank=True,
        help_text="Custom instructions for the AI bot (tone, style, what to include/exclude).",
    )
    persona_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Bot persona name (e.g., 'Business Assistant')",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.company.name} — {self.get_platform_display()} rule"


class BotConversationLog(models.Model):
    """Logs AI bot interactions — analysis, auto-replies, actions taken."""

    ACTION_CHOICES = [
        ("classified", "Message Classified"),
        ("auto_replied", "Auto Reply Sent"),
        ("read", "Message Read"),
        ("escalated", "Escalated to Human"),
        ("ignored", "Ignored (no rule match)"),
    ]

    account = models.ForeignKey(
        SocialMediaAccount,
        on_delete=models.CASCADE,
        related_name="bot_logs",
    )
    message = models.ForeignKey(
        SocialMediaMessage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bot_logs",
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    ai_classification = models.CharField(max_length=50, blank=True)
    ai_summary = models.TextField(blank=True)
    ai_reply_text = models.TextField(blank=True)
    ai_confidence = models.FloatField(null=True, blank=True, help_text="AI confidence score 0-1")
    was_sent = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.account.get_platform_display()} — {self.get_action_display()}"

