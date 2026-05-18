from django.urls import path
from . import views

app_name = "ai_assistant"

urlpatterns = [
    path("", views.home, name="home"),
    path("ask/", views.ask, name="ask"),
]
