from django.db import models


class JiraProject(models.Model):
    """Local mirror of a Jira project."""

    company = models.ForeignKey(
        "companies.Company", on_delete=models.CASCADE, related_name="jira_projects"
    )
    project_id = models.CharField(max_length=50)
    key = models.CharField(max_length=20)
    name = models.CharField(max_length=255)
    project_type = models.CharField(max_length=50, blank=True)
    lead_display_name = models.CharField(max_length=255, blank=True)
    avatar_url = models.URLField(max_length=500, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("company", "project_id")
        ordering = ["key"]

    def __str__(self):
        return f"{self.key} — {self.name}"


class JiraIssue(models.Model):
    """Local mirror of a Jira issue."""

    STATUS_CATEGORIES = [
        ("new", "New"),
        ("indeterminate", "In Progress"),
        ("done", "Done"),
        ("undefined", "Undefined"),
    ]

    company = models.ForeignKey(
        "companies.Company", on_delete=models.CASCADE, related_name="jira_issues"
    )
    project = models.ForeignKey(
        JiraProject, on_delete=models.CASCADE, related_name="issues", null=True, blank=True
    )
    issue_id = models.CharField(max_length=50)
    issue_key = models.CharField(max_length=50)
    summary = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    issue_type = models.CharField(max_length=50)
    status = models.CharField(max_length=100)
    status_category = models.CharField(max_length=20, choices=STATUS_CATEGORIES, default="undefined")
    priority = models.CharField(max_length=50, blank=True)
    labels = models.JSONField(default=list, blank=True)
    assignee_display_name = models.CharField(max_length=255, blank=True)
    reporter_display_name = models.CharField(max_length=255, blank=True)
    created_at_jira = models.DateTimeField(null=True, blank=True)
    updated_at_jira = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)

    last_synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("company", "issue_id")
        ordering = ["-updated_at_jira"]
        indexes = [
            models.Index(fields=["company", "status_category"]),
            models.Index(fields=["company", "issue_key"]),
        ]

    def __str__(self):
        return f"{self.issue_key}: {self.summary[:60]}"

    @property
    def status_color(self):
        return {
            "new": "#0052CC",
            "indeterminate": "#FF991F",
            "done": "#36B37E",
        }.get(self.status_category, "#6B778C")


class JiraComment(models.Model):
    """Local mirror of a Jira issue comment."""

    issue = models.ForeignKey(JiraIssue, on_delete=models.CASCADE, related_name="comments")
    comment_id = models.CharField(max_length=50)
    author_display_name = models.CharField(max_length=255)
    body = models.TextField()
    created_at_jira = models.DateTimeField()

    class Meta:
        unique_together = ("issue", "comment_id")
        ordering = ["created_at_jira"]

    def __str__(self):
        return f"{self.author_display_name}: {self.body[:40]}"


class JiraSyncLog(models.Model):
    """Tracks sync operations."""

    company = models.ForeignKey(
        "companies.Company", on_delete=models.CASCADE, related_name="jira_sync_logs"
    )
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    projects_synced = models.IntegerField(default=0)
    issues_synced = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default="running")
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"Sync {self.company} @ {self.started_at:%Y-%m-%d %H:%M} — {self.status}"
