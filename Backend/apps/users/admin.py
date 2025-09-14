from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, UserSession, UserActivity


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'email', 'username', 'first_name', 'last_name', 'role', 
        'is_active', 'is_verified', 'created_at', 'last_login'
    ]
    list_filter = [
        'role', 'is_active', 'is_verified', 'created_at', 'last_login'
    ]
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {
            'fields': ('username', 'first_name', 'last_name', 'phone_number', 'avatar', 'bio')
        }),
        ('Permissions', {
            'fields': ('role', 'is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role'),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return ('created_at', 'updated_at')
        return ()


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'created_at', 'expires_at', 'is_active', 'ip_address'
    ]
    list_filter = ['is_active', 'created_at', 'expires_at']
    search_fields = ['user__email', 'user__username', 'ip_address']
    ordering = ['-created_at']
    readonly_fields = ['id', 'token', 'created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def has_add_permission(self, request):
        return False


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'activity_type', 'description', 'ip_address', 'created_at'
    ]
    list_filter = ['activity_type', 'created_at']
    search_fields = ['user__email', 'user__username', 'description', 'ip_address']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'metadata']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
