from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.contrib.inlines.admin import TabularInline

from .models import Company, Invitation, Membership, PlatformAccess, ActivityLog


class MembershipInline(TabularInline):
    model = Membership
    extra = 0
    autocomplete_fields = ["user"]


class PlatformAccessInline(TabularInline):
    model = PlatformAccess
    extra = 0
    autocomplete_fields = ["integration"]


@admin.register(Company)
class CompanyAdmin(ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [MembershipInline]


@admin.register(Membership)
class MembershipAdmin(ModelAdmin):
    list_display = ("user", "company", "role", "is_active", "joined_at")
    list_filter = ("role", "is_active")
    search_fields = ("user__username", "user__email", "company__name")
    autocomplete_fields = ["user", "company"]
    inlines = [PlatformAccessInline]


@admin.register(Invitation)
class InvitationAdmin(ModelAdmin):
    list_display = ("email", "company", "role", "status", "created_at", "expires_at")
    list_filter = ("status", "role")
    search_fields = ("email", "company__name")
    readonly_fields = ("token",)


@admin.register(PlatformAccess)
class PlatformAccessAdmin(ModelAdmin):
    list_display = ("membership", "integration", "permission", "granted_at")
    list_filter = ("permission",)
    search_fields = ("membership__user__username", "integration__service")


@admin.register(ActivityLog)
class ActivityLogAdmin(ModelAdmin):
    list_display = ("created_at", "user", "company", "action", "platform", "ip_address")
    list_filter = ("action", "platform", "company")
    list_filter_submit = True
    search_fields = ("user__username", "detail", "company__name")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"

