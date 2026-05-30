from django.urls import path
from . import views
from . import webhooks

app_name = "jira_hub"

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("projects/", views.projects_view, name="projects"),
    path("projects/<str:key>/", views.project_detail_view, name="project_detail"),
    path("issues/", views.issues_view, name="issues"),
    path("issues/create/", views.create_issue_view, name="create_issue"),
    path("issues/<str:key>/", views.issue_detail_view, name="issue_detail"),
    path("issues/<str:key>/comment/", views.add_comment_view, name="add_comment"),
    path("issues/<str:key>/transition/", views.transition_view, name="transition"),
    path("sync/", views.sync_now_view, name="sync_now"),
    # Webhook management (authenticated)
    path("webhook/register/", views.register_webhook_view, name="register_webhook"),
    path("webhook/deregister/", views.deregister_webhook_view, name="deregister_webhook"),
    # Inbound webhook from Jira (unauthenticated, validated by secret)
    path("webhook/<slug:company_slug>/<str:secret>/", webhooks.jira_webhook, name="webhook"),
]
