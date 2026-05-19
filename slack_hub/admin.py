from django.contrib import admin
from .models import SlackMessage, AutoReplyRule

admin.site.register(SlackMessage)
admin.site.register(AutoReplyRule)
