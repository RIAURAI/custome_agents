from django.db import models
from django.contrib.auth.models import User


class SlackMessage(models.Model):
    """Stores tracked Slack messages with AI analysis."""

    CLASSIFICATION_CHOICES = [
        ("question", "Question"),
        ("request", "Request"),
        ("fyi", "FYI / Informational"),
        ("urgent", "Urgent"),
        ("general", "General"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="slack_messages")
    channel_id = models.CharField(max_length=100)
    channel_name = models.CharField(max_length=255, blank=True)
    sender_id = models.CharField(max_length=100)
    sender_name = models.CharField(max_length=255, blank=True)
    text = models.TextField()
    timestamp = models.CharField(max_length=50)  # Slack ts format
    thread_ts = models.CharField(max_length=50, blank=True)

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
        unique_together = ("user", "channel_id", "timestamp")

    def __str__(self):
        return f"[{self.channel_name}] {self.sender_name}: {self.text[:50]}"


class AutoReplyRule(models.Model):
    """User-configurable auto-reply rules for Slack channels."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="slack_auto_rules")
    channel_id = models.CharField(max_length=100)
    channel_name = models.CharField(max_length=255, blank=True)
    is_enabled = models.BooleanField(default=False)
    auto_send = models.BooleanField(default=False)  # True = send without confirmation
    keywords = models.TextField(
        blank=True,
        help_text="Comma-separated keywords that trigger auto-reply. Leave empty to reply to all."
    )
    custom_instructions = models.TextField(
        blank=True,
        help_text="Custom AI instructions for generating replies in this channel."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "channel_id")

    def __str__(self):
        status = "ON" if self.is_enabled else "OFF"
        return f"[{status}] {self.channel_name} ({self.user.username})"
