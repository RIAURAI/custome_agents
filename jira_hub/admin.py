from django.contrib import admin
from .models import JiraProject, JiraIssue, JiraComment, JiraSyncLog


@admin.register(JiraProject)
class JiraProjectAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "company", "project_type", "last_synced_at")
    list_filter = ("company", "project_type")
    search_fields = ("key", "name")


@admin.register(JiraIssue)
class JiraIssueAdmin(admin.ModelAdmin):
    list_display = ("issue_key", "summary", "status", "priority", "assignee_display_name", "company")
    list_filter = ("company", "status_category", "issue_type", "priority")
    search_fields = ("issue_key", "summary")


@admin.register(JiraComment)
class JiraCommentAdmin(admin.ModelAdmin):
    list_display = ("issue", "author_display_name", "created_at_jira")
    search_fields = ("body", "author_display_name")


@admin.register(JiraSyncLog)
class JiraSyncLogAdmin(admin.ModelAdmin):
    list_display = ("company", "started_at", "status", "projects_synced", "issues_synced")
    list_filter = ("company", "status")
