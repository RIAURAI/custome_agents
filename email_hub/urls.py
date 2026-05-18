from django.urls import path
from . import views

app_name = "email_hub"

urlpatterns = [
    path("", views.inbox, name="inbox"),
    path("<str:email_id>/", views.email_detail, name="detail"),
    path("compose/new/", views.compose, name="compose"),
]
