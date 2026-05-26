from django.urls import path
from . import views

app_name = "google_hub"

urlpatterns = [
    path("", views.gmail_inbox, name="inbox"),
    path("compose/", views.gmail_compose, name="compose"),
    path("message/<str:message_id>/", views.gmail_detail, name="detail"),
    path("calendar/", views.calendar_view, name="calendar"),
    path("meet/", views.meet_view, name="meet"),
    path("meet/create/", views.meet_create, name="meet_create"),
]
