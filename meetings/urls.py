from django.urls import path
from . import views

app_name = "meetings"

urlpatterns = [
    path("", views.meetings_list, name="list"),
    path("calendly-bot/", views.calendly_bot_page, name="calendly_bot"),
    path("calendly-bot/send/", views.calendly_bot_send, name="calendly_bot_send"),
]
