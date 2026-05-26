from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from unfold.admin import ModelAdmin


class UserAdmin(ModelAdmin, BaseUserAdmin):
    pass


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
