from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin
from django.contrib.auth.models import Group

from ecommerce.admin_site import admin_site
from .models import CustomUser


class UserAdmin(BaseUserAdmin):
    ordering = ('email',)
    list_display = ('email', 'is_staff')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    search_fields = ('email',)
    filter_horizontal = ()


admin_site.register(CustomUser, UserAdmin)
admin_site.register(Group, GroupAdmin)
