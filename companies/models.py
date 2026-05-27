import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.crypto import get_random_string


class Company(models.Model):
    """A tenant in the WorkHub platform. Owns integrations, members, and data."""

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    logo = models.ImageField(upload_to="company_logos/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Companies"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "company"
            candidate = base
            while Company.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{get_random_string(6).lower()}"
            self.slug = candidate
        super().save(*args, **kwargs)

    @property
    def owner(self):
        membership = self.memberships.filter(role=Membership.Role.OWNER).first()
        return membership.user if membership else None


class Membership(models.Model):
    """Links a user to a company with a role."""

    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    invited_at = models.DateTimeField(blank=True, null=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("user", "company")
        ordering = ["-joined_at"]

    def __str__(self):
        return f"{self.user} @ {self.company} ({self.role})"

    @property
    def is_owner(self):
        return self.role == self.Role.OWNER

    @property
    def is_admin(self):
        return self.role in (self.Role.OWNER, self.Role.ADMIN)


class Invitation(models.Model):
    """Pending invite for a user to join a company."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        EXPIRED = "expired", "Expired"
        REVOKED = "revoked", "Revoked"

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    email = models.EmailField()
    role = models.CharField(
        max_length=20,
        choices=Membership.Role.choices,
        default=Membership.Role.MEMBER,
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_invitations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Invite {self.email} → {self.company.name} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def is_valid(self):
        return self.status == self.Status.PENDING and not self.is_expired


class PlatformAccess(models.Model):
    """Controls which platforms a member can access and at what level."""

    class Permission(models.TextChoices):
        VIEW = "view", "View Only"
        REPLY = "reply", "View + Reply"
        MANAGE = "manage", "Full Manage"

    membership = models.ForeignKey(
        Membership,
        on_delete=models.CASCADE,
        related_name="platform_access",
    )
    integration = models.ForeignKey(
        "integrations.CompanyIntegration",
        on_delete=models.CASCADE,
        related_name="access_grants",
    )
    permission = models.CharField(
        max_length=20,
        choices=Permission.choices,
        default=Permission.VIEW,
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="granted_access",
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("membership", "integration")
        ordering = ["-granted_at"]

    def __str__(self):
        return f"{self.membership.user} → {self.integration.service} ({self.permission})"


class ActivityLog(models.Model):
    """Tracks user actions across the platform for audit and analytics."""

    class Action(models.TextChoices):
        # Auth / Team
        LOGIN = "login", "Logged in"
        INVITE_SENT = "invite_sent", "Sent invitation"
        INVITE_ACCEPTED = "invite_accepted", "Accepted invitation"
        MEMBER_REMOVED = "member_removed", "Removed member"
        ACCESS_UPDATED = "access_updated", "Updated platform access"
        # Integrations
        INTEGRATION_CONNECTED = "integration_connected", "Connected integration"
        INTEGRATION_DISCONNECTED = "integration_disconnected", "Disconnected integration"
        # Email
        EMAIL_VIEWED = "email_viewed", "Viewed email"
        EMAIL_SENT = "email_sent", "Sent email"
        # Meetings
        MEETINGS_VIEWED = "meetings_viewed", "Viewed meetings"
        # Slack
        SLACK_CHANNEL_VIEWED = "slack_channel_viewed", "Viewed Slack channel"
        SLACK_MESSAGE_SENT = "slack_message_sent", "Sent Slack message"
        SLACK_AUTO_REPLY = "slack_auto_reply", "Slack auto-reply sent"
        # Microsoft 365 features
        PRESENCE_VIEWED = "presence_viewed", "Viewed presence"
        CHAT_VIEWED = "chat_viewed", "Viewed Teams chat"
        CHAT_MESSAGE_SENT = "chat_message_sent", "Sent Teams message"
        CHANNEL_MESSAGE_SENT = "channel_message_sent", "Sent channel message"
        ONEDRIVE_BROWSED = "onedrive_browsed", "Browsed OneDrive"
        ONEDRIVE_UPLOADED = "onedrive_uploaded", "Uploaded to OneDrive"
        ONEDRIVE_DOWNLOADED = "onedrive_downloaded", "Downloaded from OneDrive"
        ONEDRIVE_DELETED = "onedrive_deleted", "Deleted OneDrive item"
        ONEDRIVE_SHARED = "onedrive_shared", "Shared OneDrive item"
        TODO_VIEWED = "todo_viewed", "Viewed To Do"
        TODO_CREATED = "todo_created", "Created task"
        TODO_UPDATED = "todo_updated", "Updated task"
        TODO_DELETED = "todo_deleted", "Deleted task"
        PLANNER_VIEWED = "planner_viewed", "Viewed Planner"
        CONTACTS_VIEWED = "contacts_viewed", "Viewed contacts"
        # AI
        AI_SUMMARIZE = "ai_summarize", "AI summarization"
        AI_REPLY = "ai_reply", "AI reply generated"

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="activity_logs",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
    )
    action = models.CharField(max_length=40, choices=Action.choices)
    platform = models.CharField(max_length=50, blank=True)  # "microsoft", "slack", ""
    detail = models.TextField(blank=True)  # Extra context (e.g., email subject, channel name)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["company", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["action"]),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else "System"
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {user_str}: {self.get_action_display()}"

