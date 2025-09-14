"""
Django admin configuration for CCTV app
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Camera, RecordingSchedule, Recording, CameraAccess, LiveStream, GCPVideoTransfer


@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    """Admin configuration for Camera model"""
    
    list_display = [
        'name', 'ip_address', 'status', 'camera_type', 'location',
        'is_online_display', 'created_at'
    ]
    list_filter = ['status', 'camera_type', 'auto_record', 'created_at']
    search_fields = ['name', 'ip_address', 'location', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_seen', 'is_online']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'location', 'camera_type', 'status')
        }),
        ('Connection Details', {
            'fields': ('ip_address', 'port', 'username', 'password', 'rtsp_url', 'rtsp_url_sub')
        }),
        ('Recording Settings', {
            'fields': ('auto_record', 'record_quality', 'max_recording_hours')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at', 'last_seen', 'is_online'),
            'classes': ('collapse',)
        })
    )
    
    def is_online_display(self, obj):
        """Display online status with colored indicator"""
        if obj.is_online:
            return format_html('<span style="color: green;">●</span> Online')
        else:
            return format_html('<span style="color: red;">●</span> Offline')
    is_online_display.short_description = 'Status'
    



@admin.register(RecordingSchedule)
class RecordingScheduleAdmin(admin.ModelAdmin):
    """Admin configuration for RecordingSchedule model"""
    
    list_display = [
        'name', 'camera', 'schedule_type', 'start_time', 'end_time',
        'is_active', 'created_at'
    ]
    list_filter = ['schedule_type', 'is_active', 'created_at']
    search_fields = ['name', 'camera__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'camera', 'schedule_type', 'is_active')
        }),
        ('Time Settings', {
            'fields': ('start_time', 'end_time', 'start_date', 'end_date')
        }),
        ('Weekly Settings', {
            'fields': ('days_of_week',),
            'description': 'For weekly schedules, specify days as JSON array: ["monday", "friday"]'
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    



@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    """Admin configuration for Recording model"""
    
    list_display = [
        'name', 'camera', 'status', 'start_time', 'duration_display',
        'file_size_display'
    ]
    list_filter = ['status', 'start_time', 'camera']
    search_fields = ['name', 'camera__name']
    readonly_fields = [
        'id', 'file_path', 'file_size', 'duration', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'camera', 'schedule', 'status')
        }),
        ('Recording Details', {
            'fields': ('start_time', 'end_time', 'duration', 'resolution', 'frame_rate')
        }),
        ('File Information', {
            'fields': ('file_path', 'file_size', 'error_message')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def duration_display(self, obj):
        """Display duration in readable format"""
        if obj.duration:
            total_seconds = int(obj.duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return "-"
    duration_display.short_description = 'Duration'
    
    def file_size_display(self, obj):
        """Display file size in readable format"""
        if obj.file_size:
            size_mb = obj.file_size / (1024 * 1024)
            if size_mb >= 1024:
                size_gb = size_mb / 1024
                return f"{size_gb:.2f} GB"
            return f"{size_mb:.2f} MB"
        return "-"
    file_size_display.short_description = 'File Size'
    



@admin.register(CameraAccess)
class CameraAccessAdmin(admin.ModelAdmin):
    """Admin configuration for CameraAccess model"""
    
    list_display = [
        'camera', 'access_level', 'can_record', 'can_schedule',
        'can_download', 'is_active', 'granted_at'
    ]
    list_filter = ['access_level', 'can_record', 'can_schedule', 'can_download', 'is_active']
    search_fields = ['camera__name']
    readonly_fields = ['id', 'granted_at']
    
    fieldsets = (
        ('Access Details', {
            'fields': ('camera', 'access_level', 'is_active')
        }),
        ('Permissions', {
            'fields': ('can_record', 'can_schedule', 'can_download')
        }),
        ('Time Restrictions', {
            'fields': ('access_start_time', 'access_end_time')
        }),
        ('Metadata', {
            'fields': ('id', 'granted_at'),
            'classes': ('collapse',)
        })
    )
    



@admin.register(LiveStream)
class LiveStreamAdmin(admin.ModelAdmin):
    """Admin configuration for LiveStream model"""
    
    list_display = [
        'camera', 'session_id', 'start_time', 'end_time',
        'is_active', 'client_ip'
    ]
    list_filter = ['is_active', 'start_time']
    search_fields = ['camera__name', 'session_id', 'client_ip']
    readonly_fields = ['id', 'session_id', 'start_time', 'end_time', 'client_ip', 'user_agent']
    
    fieldsets = (
        ('Stream Information', {
            'fields': ('camera', 'session_id', 'is_active')
        }),
        ('Time Information', {
            'fields': ('start_time', 'end_time')
        }),
        ('Client Information', {
            'fields': ('client_ip', 'user_agent')
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        })
    )


@admin.register(GCPVideoTransfer)
class GCPVideoTransferAdmin(admin.ModelAdmin):
    """Admin configuration for GCPVideoTransfer model"""
    
    list_display = [
        'recording_name_display', 'transfer_status', 'file_size_display',
        'upload_completed_at', 'cleanup_scheduled_at', 'created_at'
    ]
    list_filter = ['transfer_status', 'created_at', 'upload_completed_at', 'cleanup_completed_at']
    search_fields = ['recording__name', 'recording__camera__name', 'gcp_storage_path']
    readonly_fields = [
        'id', 'recording', 'original_local_path', 'gcp_storage_path', 'gcp_public_url',
        'file_size_bytes', 'created_at', 'upload_started_at', 'upload_completed_at',
        'cleanup_scheduled_at', 'cleanup_completed_at', 'retry_count'
    ]
    
    fieldsets = (
        ('Transfer Information', {
            'fields': ('recording', 'transfer_status', 'initiated_by')
        }),
        ('File Details', {
            'fields': ('original_local_path', 'gcp_storage_path', 'gcp_public_url', 'file_size_bytes')
        }),
        ('Timeline', {
            'fields': ('created_at', 'upload_started_at', 'upload_completed_at', 
                      'cleanup_scheduled_at', 'cleanup_completed_at')
        }),
        ('Error Handling', {
            'fields': ('error_message', 'retry_count')
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        })
    )
    
    def recording_name_display(self, obj):
        """Display recording name with link"""
        if obj.recording:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:cctv_recording_change', args=[obj.recording.id]),
                obj.recording.name
            )
        return "-"
    recording_name_display.short_description = 'Recording'
    
    def file_size_display(self, obj):
        """Display file size in readable format"""
        if obj.file_size_bytes:
            size_mb = obj.file_size_bytes / (1024 * 1024)
            if size_mb >= 1024:
                size_gb = size_mb / 1024
                return f"{size_gb:.2f} GB"
            return f"{size_mb:.2f} MB"
        return "-"
    file_size_display.short_description = 'File Size'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('recording', 'recording__camera', 'initiated_by')