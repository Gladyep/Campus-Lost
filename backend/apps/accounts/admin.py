from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ('email',)
    list_display = ('email', 'name', 'campus', 'role', 'is_active', 'is_staff')
    fieldsets = ((None, {'fields': ('email', 'password')}), ('Profile', {'fields': ('name', 'campus', 'role')}), ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}), ('Dates', {'fields': ('last_login', 'date_joined')}))
    add_fieldsets = ((None, {'classes': ('wide',), 'fields': ('email', 'name', 'password1', 'password2')}),)
    search_fields = ('email', 'name')