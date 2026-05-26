from django.contrib import admin
from django.contrib.auth.models import User

from companies.models import Company, Membership, ActivityLog
from slack_hub.models import SlackMessage


def dashboard_callback(request, context):
    """Inject dashboard statistics into the admin index template."""
    context.update(
        {
            "total_companies": Company.objects.count(),
            "total_users": User.objects.count(),
            "total_memberships": Membership.objects.count(),
            "total_slack_messages": SlackMessage.objects.count(),
            "recent_activity": ActivityLog.objects.select_related(
                "user", "company"
            ).order_by("-created_at")[:10],
        }
    )
    return context
