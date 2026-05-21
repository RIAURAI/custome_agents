from django.db import models
from django.contrib.auth.models import User


class UserIntegration(models.Model):
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
