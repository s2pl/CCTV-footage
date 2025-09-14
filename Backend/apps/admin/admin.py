from django.contrib import admin
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from django_object_actions import DjangoObjectActions
from django.contrib.admin import DateFieldListFilter
from django.urls import reverse
from .models import AdminPanel

@admin.register(AdminPanel)
class AdminPanelAdmin(ImportExportModelAdmin, DjangoObjectActions):
    list_display = ('id', 'name', 'status', 'created_at', 'updated_at', 'custom_actions')
    list_filter = (
        ('status', admin.ChoicesFieldListFilter),
        ('created_at', DateFieldListFilter),
    )
    search_fields = ('name', 'description', 'id')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    list_per_page = 25
    save_on_top = True
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description'),
            'description': 'Enter the basic details of the model'
        }),
        ('Status Information', {
            'fields': ('status', 'some_critical_field'),
            'description': 'Current status of the item'
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
            'description': 'Automatically managed timestamps'
        }),
    )
    
    def custom_actions(self, obj):
        view_url = reverse('admin_custom:view_details', args=[obj.id])
        process_url = reverse('admin_custom:process_item', args=[obj.id])
        return format_html(
            '<a class="button btn btn-info" href="{}" title="View Details">'
            '<i class="fas fa-eye"></i> View</a>&nbsp;'
            '<a class="button btn btn-success" href="{}" title="Process Item">'
            '<i class="fas fa-cogs"></i> Process</a>',
            view_url,
            process_url
        )
    
    custom_actions.short_description = 'Actions'

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ('some_critical_field',)
        return self.readonly_fields