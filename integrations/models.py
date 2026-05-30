from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
import json


class UserIntegration(models.Model):
    """DEPRECATED — kept for migration compatibility. Use CompanyIntegration."""

    SERVICE_CHOICES = [
        ("microsoft", "Microsoft (Outlook + Teams)"),
        ("google", "Google Workspace (Gmail + Calendar + Meet)"),
        ("slack", "Slack"),
        ("calendly", "Calendly"),
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
    # User OAuth Token (xoxp-...) — for posting as the user (not the bot)
    slack_user_token_enc = models.BinaryField(null=True, blank=True)
    # Calendly-specific fields
    calendly_organization_uri = models.CharField(max_length=500, blank=True)
    calendly_user_uri = models.CharField(max_length=500, blank=True)
    connected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "service")

    def __str__(self):
        return f"{self.user.username} → {self.service}"


class CompanyIntegration(models.Model):
    """Company-level integration. Tokens belong to the company, connected by an admin."""

    SERVICE_CHOICES = [
        ("microsoft", "Microsoft (Outlook + Teams)"),
        ("google", "Google Workspace (Gmail + Calendar + Meet)"),
        ("slack", "Slack"),
        ("calendly", "Calendly"),
        ("discord", "Discord"),
        ("jira", "Jira"),
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

    # Microsoft-specific — per-company Azure App Registration (BYOB)
    ms_client_id_enc = models.BinaryField(null=True, blank=True)
    ms_client_secret_enc = models.BinaryField(null=True, blank=True)
    ms_tenant_id = models.CharField(max_length=100, blank=True, default="common")
    ms_account_name = models.CharField(max_length=255, blank=True)
    ms_account_email = models.CharField(max_length=255, blank=True)
    # Feature-based dynamic scopes — list of enabled feature keys (e.g. ["email", "calendar", "onedrive"])
    # Maps to MS_FEATURE_SCOPES in settings.py. Only enabled features' scopes are requested during OAuth.
    enabled_ms_features = models.JSONField(default=list, blank=True)

    # Slack-specific
    slack_team_id = models.CharField(max_length=100, blank=True)
    slack_team_name = models.CharField(max_length=255, blank=True)
    slack_user_id = models.CharField(max_length=100, blank=True)
    slack_bot_user_id = models.CharField(max_length=100, blank=True)
    slack_app_token_enc = models.BinaryField(null=True, blank=True)
    slack_signing_secret_enc = models.BinaryField(null=True, blank=True)
    # User OAuth Token (xoxp-...) — for posting as the user (not the bot)
    slack_user_token_enc = models.BinaryField(null=True, blank=True)

    # Google Workspace-specific
    google_account_name = models.CharField(max_length=255, blank=True)
    google_account_email = models.CharField(max_length=255, blank=True)
    google_project_id = models.CharField(max_length=255, blank=True)  # GCP Project ID
    # Per-company Google OAuth app credentials (stored encrypted)
    google_client_id_enc = models.BinaryField(null=True, blank=True)
    google_client_secret_enc = models.BinaryField(null=True, blank=True)

    # Calendly-specific
    calendly_organization_uri = models.CharField(max_length=500, blank=True)
    calendly_user_uri = models.CharField(max_length=500, blank=True)
    # Per-company Calendly OAuth app credentials (stored encrypted)
    calendly_client_id_enc = models.BinaryField(null=True, blank=True)
    calendly_client_secret_enc = models.BinaryField(null=True, blank=True)

    # Discord-specific
    discord_guild_id = models.CharField(max_length=100, blank=True)
    discord_guild_name = models.CharField(max_length=255, blank=True)
    discord_bot_token_enc = models.BinaryField(null=True, blank=True)
    discord_webhook_url = models.URLField(max_length=500, blank=True)

    # Jira-specific
    jira_site_url = models.URLField(max_length=500, blank=True, help_text="e.g. https://yourteam.atlassian.net")
    jira_project_key = models.CharField(max_length=50, blank=True)
    jira_user_email = models.CharField(max_length=255, blank=True)
    jira_api_token_enc = models.BinaryField(null=True, blank=True)
    jira_account_id = models.CharField(max_length=128, blank=True, help_text="Atlassian accountId from /rest/api/3/myself")
    jira_display_name = models.CharField(max_length=255, blank=True)
    jira_avatar_url = models.URLField(max_length=500, blank=True)
    jira_webhook_id = models.CharField(max_length=100, blank=True, help_text="Jira webhook ID for deletion")
    jira_webhook_secret = models.CharField(max_length=64, blank=True, help_text="Shared secret for webhook validation")



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

    # ── Microsoft dynamic-scopes helpers ──────────────────────────────────

    def get_ms_scopes(self) -> list[str]:
        """Build the full scope list from MS_BASE_SCOPES + enabled features."""
        from django.conf import settings as _s
        scopes = list(_s.MS_BASE_SCOPES)
        features = self.enabled_ms_features or _s.MS_DEFAULT_FEATURES
        for feat in features:
            feat_info = _s.MS_FEATURE_SCOPES.get(feat)
            if feat_info:
                scopes.extend(feat_info["scopes"])
        return list(dict.fromkeys(scopes))  # dedupe, preserve order

    def has_ms_feature(self, feature_key: str) -> bool:
        """Check if a specific MS feature is enabled."""
        features = self.enabled_ms_features or []
        return feature_key in features
