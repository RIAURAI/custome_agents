from django.urls import path
from . import views

app_name = "companies"

urlpatterns = [
    # Team management (admin only)
    path("team/", views.team_view, name="team"),
    path("activity/", views.activity_log_view, name="activity_log"),
    path("invite/", views.invite_member, name="invite"),
    path("invite/<uuid:token>/revoke/", views.revoke_invite, name="revoke_invite"),
    path("member/<int:membership_id>/access/", views.manage_access, name="manage_access"),
    path("member/<int:membership_id>/remove/", views.remove_member, name="remove_member"),

    # Accept invite (public-ish — invite token required)
    path("join/<uuid:token>/", views.accept_invite, name="accept_invite"),
]
