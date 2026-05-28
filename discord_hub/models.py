from django.db import models


class DiscordMessage(models.Model):
    """Every Discord message received by the bot, with AI analysis."""

    CLASSIFICATION_CHOICES = [
        ("question", "Question"),
        ("request", "Request"),
        ("fyi", "FYI / Informational"),
        ("urgent", "Urgent"),
        ("general", "General"),
    ]

    company = models.ForeignKey(
        "companies.Company", on_delete=models.CASCADE, related_name="discord_messages"
    )
    message_id = models.CharField(max_length=30, unique=True)  # Discord snowflake ID
    guild_id = models.CharField(max_length=30, blank=True)
    guild_name = models.CharField(max_length=255, blank=True)
    channel_id = models.CharField(max_length=30)
    channel_name = models.CharField(max_length=255, blank=True)
    sender_id = models.CharField(max_length=30)
    sender_name = models.CharField(max_length=255, blank=True)
    text = models.TextField()
    is_dm = models.BooleanField(default=False)

    # AI fields
    ai_classification = models.CharField(
        max_length=20, choices=CLASSIFICATION_CHOICES, blank=True
    )
    ai_summary = models.TextField(blank=True)
    ai_reply = models.TextField(blank=True)
    is_auto_replied = models.BooleanField(default=False)
    reply_sent_at = models.DateTimeField(null=True, blank=True)

    tracked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-tracked_at"]

    def __str__(self):
        return f"[#{self.channel_name}] {self.sender_name}: {self.text[:50]}"


class DiscordAutoReplyRule(models.Model):
    """Per-channel auto-reply rules — mirrors Slack's AutoReplyRule."""

    company = models.ForeignKey(
        "companies.Company", on_delete=models.CASCADE, related_name="discord_auto_rules"
    )
    channel_id = models.CharField(
        max_length=30,
        help_text="Discord channel ID, or '*' for all channels.",
    )
    channel_name = models.CharField(max_length=255, blank=True)
    is_enabled = models.BooleanField(default=False)
    auto_send = models.BooleanField(
        default=False,
        help_text="Send reply automatically. If False, only save as draft.",
    )
    keywords = models.TextField(
        blank=True,
        help_text="Comma-separated keywords that trigger auto-reply. Leave empty to reply to all.",
    )
    custom_instructions = models.TextField(
        blank=True,
        help_text="Custom AI instructions for this channel.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("company", "channel_id")

    def __str__(self):
        status = "ON" if self.is_enabled else "OFF"
        return f"[{status}] #{self.channel_name} ({self.company.name})"

