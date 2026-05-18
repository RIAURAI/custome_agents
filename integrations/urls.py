from django.urls import path
from . import views

app_name = "integrations"

urlpatterns = [
    path("", views.connect_view, name="connect"),
    path("microsoft/connect/", views.microsoft_connect, name="microsoft_connect"),
    path("callback/", views.microsoft_callback, name="callback"),
    path("microsoft/disconnect/", views.microsoft_disconnect, name="microsoft_disconnect"),
]
