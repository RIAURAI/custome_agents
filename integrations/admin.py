from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import CompanyIntegration


@admin.register(CompanyIntegration)
class CompanyIntegrationAdmin(ModelAdmin):
    list_display = ("company", "service", "status", "connected_by", "connected_at")
    list_filter = ("service", "status")
    search_fields = ("company__name", "ms_account_email", "slack_team_name")
    autocomplete_fields = ["company", "connected_by"]

