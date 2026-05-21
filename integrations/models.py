from django.db import models
from django.conf import settings
from django.contrib.auth.models import User


class UserIntegration(models.Model):
    """DEPRECATED — kept for migration compatibility. Use CompanyIntegration."""

    SERVICE_CHOICES = [
        ("microsoft", "Microsoft (Outlook + Teams)"),
        ("slack", "Slack"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="integrations")
    service = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    # Tokens stored as bytes (Fernet-encrypted)
    access_token_enc = models.BinaryField(null=True, blank=True)
    refresh_token_enc = models.BinaryField(null=True, blank=True)
    token_expiry = models.DateTimeField(null=True, blank=True)
    ms_account_name = models.CharField(max_length=255, blank=True)
    ms_account_email = models.CharField(max_length=255, blank=True)
    # Slack-specific fields
    slack_team_id = models.CharField(max_length=100, blank=True)
    slack_team_name = models.CharField(max_length=255, blank=True)
    slack_user_id = models.CharField(max_length=100, blank=True)
    slack_bot_user_id = models.CharField(max_length=100, blank=True)
    # App-level token (xapp-...) for Socket Mode — optional
    slack_app_token_enc = models.BinaryField(null=True, blank=True)
    # Signing Secret — used to verify incoming Slack webhook requests per user
    slack_signing_secret_enc = models.BinaryField(null=True, blank=True)
    connected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "service")

    def __str__(self):
        return f"{self.user.username} → {self.service}"


class CompanyIntegration(models.Model):
    """Company-level integration. Tokens belong to the company, connected by an admin."""

    SERVICE_CHOICES = [
        ("microsoft", "Microsoft (Outlook + Teams)"),
        ("slack", "Slack"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("expired", "Token Expired"),
        ("error", "Error"),
        ("disconnected", "Disconnected"),
    ]

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="integrations",
    )
    service = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    # Tokens stored as bytes (Fernet-encrypted)
    access_token_enc = models.BinaryField(null=True, blank=True)
    refresh_token_enc = models.BinaryField(null=True, blank=True)
    token_expiry = models.DateTimeField(null=True, blank=True)

    # Microsoft-specific
    ms_account_name = models.CharField(max_length=255, blank=True)
    ms_account_email = models.CharField(max_length=255, blank=True)

    # Slack-specific
    slack_team_id = models.CharField(max_length=100, blank=True)
    slack_team_name = models.CharField(max_length=255, blank=True)
    slack_user_id = models.CharField(max_length=100, blank=True)
    slack_bot_user_id = models.CharField(max_length=100, blank=True)
    slack_app_token_enc = models.BinaryField(null=True, blank=True)
    slack_signing_secret_enc = models.BinaryField(null=True, blank=True)

    # Audit
    connected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="connected_integrations",
    )
    connected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("company", "service")

    def __str__(self):
        return f"{self.company.name} → {self.service} ({self.status})"
