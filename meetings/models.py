from django.db import models
from django.conf import settings


class Meeting(models.Model):
    """
    Tracks meetings scheduled via Calendly through the AI bot.
    Decoupled from Slack — records who scheduled, when, and how.
    """

    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
    ]

    CREATED_VIA_CHOICES = [
        ("slack_bot", "Slack Bot"),
        ("web_ui", "Web UI"),
        ("webhook", "Webhook"),
    ]

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="meetings",
    )

    # Calendly references
    calendly_event_uri = models.CharField(
        max_length=500, blank=True, db_index=True,
        help_text="Calendly event resource URI",
    )
    event_type_name = models.CharField(
        max_length=255, blank=True,
        help_text="e.g. '30 Minute Meeting'",
    )
    event_type_uri = models.CharField(
        max_length=500, blank=True,
        help_text="Calendly event type resource URI",
    )

    # Scheduling
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    scheduling_link = models.URLField(max_length=500, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="scheduled",
    )

    # Invitee info (filled when booked via webhook or API)
    invitee_name = models.CharField(max_length=255, blank=True)
    invitee_email = models.EmailField(blank=True)

    # Origin tracking
    created_via = models.CharField(
        max_length=20, choices=CREATED_VIA_CHOICES, default="slack_bot",
    )
    slack_channel_id = models.CharField(
        max_length=100, blank=True,
        help_text="Slack channel where the meeting was requested",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="requested_meetings",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_time"]

    def __str__(self):
        return f"{self.event_type_name} — {self.status} ({self.company.name})"
