from django.db import models
from django.core.validators import URLValidator
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
User = get_user_model()

class Camera(models.Model):
    """Model for IP CCTV cameras"""
    
    CAMERA_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Maintenance'),
        ('error', 'Error'),
    ]
    
    CAMERA_TYPE_CHOICES = [
        ('ip', 'IP Camera'),
        ('rtsp', 'RTSP Camera'),
        ('webcam', 'Webcam'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Camera name/label")
    description = models.TextField(blank=True, null=True, help_text="Camera description")
    
    # Camera connection details
    ip_address = models.GenericIPAddressField(help_text="Camera IP address")
    port = models.PositiveIntegerField(default=554, help_text="RTSP port (usually 554)")
    username = models.CharField(max_length=100, blank=True, null=True, help_text="Camera username")
    password = models.CharField(max_length=100, blank=True, null=True, help_text="Camera password")
    
    # RTSP URLs
    rtsp_url = models.CharField(
        max_length=500,
        help_text="Full RTSP URL (e.g., rtsp://admin:password@192.168.1.100:554/stream1)"
    )
    rtsp_url_sub = models.CharField(
        max_length=500, 
        blank=True, 
        null=True,
        help_text="Secondary RTSP stream URL (lower quality)"
    )
    rtsp_path = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Custom RTSP path (e.g., /live/0/SUB, /stream1, /cam/realmonitor)"
    )
    
    # Camera properties
    camera_type = models.CharField(max_length=10, choices=CAMERA_TYPE_CHOICES, default='rtsp')
    status = models.CharField(max_length=15, choices=CAMERA_STATUS_CHOICES, default='inactive')
    location = models.CharField(max_length=255, blank=True, null=True, help_text="Physical location")
    
    # Recording settings
    auto_record = models.BooleanField(default=False, help_text="Enable automatic recording")
    record_quality = models.CharField(
        max_length=10, 
        choices=[('high', 'High'), ('medium', 'Medium'), ('low', 'Low')],
        default='medium'
    )
    max_recording_hours = models.PositiveIntegerField(
        default=24, 
        help_text="Maximum hours to keep recordings"
    )
    
    # Access control
    is_public = models.BooleanField(default=False, help_text="Whether basic users can access this camera")
    is_active = models.BooleanField(default=True, help_text="Whether this camera is active and accessible")
    
    # Streaming status
    is_online = models.BooleanField(default=False, help_text="Whether camera is currently online")
    is_streaming = models.BooleanField(default=False, help_text="Whether camera is currently streaming")
    
    # User management
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='created_cameras',
        help_text="User who created this camera"
    )
    assigned_users = models.ManyToManyField(
        User,
        through='CameraAccess',
        through_fields=('camera', 'user'),
        related_name='accessible_cameras',
        blank=True,
        help_text="Users who have access to this camera"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen = models.DateTimeField(blank=True, null=True, help_text="Last time camera was online")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Camera'
        verbose_name_plural = 'Cameras'
    
    def __str__(self):
        return f"{self.name} ({self.ip_address})"
    
    def check_online_status(self):
        """Check if camera is currently online based on last_seen"""
        if not self.last_seen:
            return False
        from django.utils import timezone
        return (timezone.now() - self.last_seen).seconds < 300  # 5 minutes threshold
    
    def get_stream_url(self, quality='main'):
        """Get the appropriate stream URL"""
        if quality == 'sub' and self.rtsp_url_sub:
            return self.rtsp_url_sub
        return self.rtsp_url
    
    def build_rtsp_url(self):
        """Build RTSP URL from components if not provided"""
        if self.rtsp_url:
            return self.rtsp_url
        
        # Build URL from components
        auth = ""
        if self.username and self.password:
            auth = f"{self.username}:{self.password}@"
        elif self.username:
            auth = f"{self.username}@"  # Username only, no password
        
        # Use custom path if provided, otherwise default to /stream1
        path = self.rtsp_path if self.rtsp_path else "/stream1"
        # Ensure path starts with /
        if not path.startswith('/'):
            path = '/' + path
        
        return f"rtsp://{auth}{self.ip_address}:{self.port}{path}"
    
    def extract_rtsp_path(self, full_url):
        """Extract RTSP path from a full URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(full_url)
            return parsed.path
        except Exception:
            return None
    
    def set_rtsp_path_from_url(self, full_url):
        """Set RTSP path from a full URL and update IP/port if needed"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(full_url)
            
            # Extract path
            if parsed.path:
                self.rtsp_path = parsed.path
            
            # Extract IP and port if not already set
            if parsed.hostname and not self.ip_address:
                self.ip_address = parsed.hostname
            
            if parsed.port and not self.port:
                self.port = parsed.port
            
            # Extract username and password if present
            if parsed.username and not self.username:
                self.username = parsed.username
            
            if parsed.password and not self.password:
                self.password = parsed.password
                
        except Exception as e:
            logger.error(f"Failed to parse RTSP URL {full_url}: {str(e)}")
    
    def mark_as_online(self):
        """Mark camera as online by updating last_seen timestamp and is_online field"""
        from django.utils import timezone
        self.last_seen = timezone.now()
        self.is_online = True
        self.save(update_fields=['last_seen', 'is_online'])
    
    def mark_as_offline(self):
        """Mark camera as offline by setting last_seen to None and is_online to False"""
        self.last_seen = None
        self.is_online = False
        self.is_streaming = False
        self.save(update_fields=['last_seen', 'is_online', 'is_streaming'])
    
    def set_status(self, new_status):
        """Set camera status and handle related logic"""
        valid_statuses = [choice[0] for choice in self.CAMERA_STATUS_CHOICES]
        if new_status in valid_statuses:
            self.status = new_status
            self.save(update_fields=['status'])
            
            # If setting to active, mark as online
            if new_status == 'active':
                self.mark_as_online()
            # If setting to maintenance or error, mark as offline
            elif new_status in ['maintenance', 'error']:
                self.mark_as_offline()
    
    def auto_record_5min(self, user=None):
        """Start automatic 5-second recording"""
        from .streaming import recording_manager
        
        try:
            recording_name = f"Auto 5sec - {self.name} - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
            recording = recording_manager.start_recording(
                camera=self,
                duration_minutes=0.083,  # 5 seconds
                recording_name=recording_name,
                user=user or self.created_by
            )
            return recording
        except Exception as e:
            logger.error(f"Failed to start auto recording for {self.name}: {str(e)}")
            return None


class RecordingSchedule(models.Model):
    """Model for scheduling camera recordings"""
    
    SCHEDULE_TYPE_CHOICES = [
        ('once', 'One Time'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('continuous', 'Continuous'),
    ]
    
    DAYS_OF_WEEK = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name='schedules')
    name = models.CharField(max_length=255, help_text="Schedule name")
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='recording_schedules',
        help_text="User who created this schedule"
    )
    
    # Schedule settings
    schedule_type = models.CharField(max_length=15, choices=SCHEDULE_TYPE_CHOICES, default='once')
    start_time = models.TimeField(help_text="Recording start time")
    end_time = models.TimeField(help_text="Recording end time")
    
    # For specific date scheduling
    start_date = models.DateField(blank=True, null=True, help_text="Start date (for one-time schedules)")
    end_date = models.DateField(blank=True, null=True, help_text="End date")
    
    # For weekly scheduling
    days_of_week = models.JSONField(
        default=list, 
        blank=True,
        help_text="List of days for weekly schedules (e.g., ['monday', 'friday'])"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Recording Schedule'
        verbose_name_plural = 'Recording Schedules'
    
    def __str__(self):
        return f"{self.name} - {self.camera.name}"


class Recording(models.Model):
    """Model for camera recordings"""
    
    RECORDING_STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('recording', 'Recording'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('stopped', 'Stopped'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name='recordings')
    schedule = models.ForeignKey(
        RecordingSchedule, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        related_name='recordings'
    )
    
    # Recording details
    name = models.CharField(max_length=255, help_text="Recording name/description")
    file_path = models.CharField(max_length=500, help_text="Path to recording file")
    storage_type = models.CharField(
        max_length=10, 
        choices=[('local', 'Local Storage'), ('gcp', 'Google Cloud Storage')], 
        default='local',
        help_text="Where the recording file is stored"
    )
    file_size = models.BigIntegerField(default=0, help_text="File size in bytes")
    duration = models.DurationField(blank=True, null=True, help_text="Recording duration")
    
    # User management
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='recordings',
        help_text="User who initiated this recording"
    )
    
    # Timestamps
    start_time = models.DateTimeField(help_text="Recording start time")
    end_time = models.DateTimeField(blank=True, null=True, help_text="Recording end time")
    
    # Status and metadata
    status = models.CharField(max_length=15, choices=RECORDING_STATUS_CHOICES, default='scheduled')
    error_message = models.TextField(blank=True, null=True, help_text="Error details if failed")
    
    # Quality settings
    resolution = models.CharField(max_length=20, blank=True, null=True, help_text="e.g., 1920x1080")
    frame_rate = models.PositiveIntegerField(blank=True, null=True, help_text="FPS")
    codec = models.CharField(max_length=10, blank=True, null=True, help_text="Video codec used (e.g., H264)")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_time']
        verbose_name = 'Recording'
        verbose_name_plural = 'Recordings'
    
    def __str__(self):
        return f"{self.name} - {self.camera.name} ({self.start_time})"
    
    @property
    def absolute_file_path(self):
        """Get the absolute file path for the recording (for local storage only)"""
        if self.file_path and not getattr(settings, 'GCP_STORAGE_USE_GCS', False):
            import os
            return os.path.join(settings.MEDIA_ROOT, self.file_path)
        return None
    
    @property
    def file_exists(self):
        """Check if the recording file exists in storage (local or GCP)"""
        if self.file_path:
            from .storage_service import storage_service
            return storage_service.file_exists(self.file_path)
        return False
    
    @property
    def file_size_mb(self):
        """Get file size in MB"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
    
    def update_file_info(self):
        """Update file size and other metadata from the actual file"""
        if self.file_path:
            from .storage_service import storage_service
            file_size = storage_service.get_file_size(self.file_path)
            if file_size is not None:
                self.file_size = file_size
                self.save(update_fields=['file_size'])
    
    @property
    def file_url(self):
        """Get the URL to access the recording file"""
        if not self.file_path:
            return ""
            
        try:
            from .storage_service import storage_service
            url = storage_service.get_file_url(self.file_path)
            return url or ""  # storage_service.get_file_url now always returns str, but keep defensive check
        except Exception as e:
            logger.error(f"Error getting file URL for recording {self.id}: {str(e)}")
            return ""
    
    @property
    def is_active(self):
        """Check if recording is currently active"""
        return self.status == 'recording'


class CameraAccess(models.Model):
    """Model for managing user access to cameras"""
    
    ACCESS_LEVEL_CHOICES = [
        ('view', 'View Only'),
        ('control', 'View & Control'),
        ('admin', 'Full Admin'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='camera_accesses')
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name='user_accesses')
    access_level = models.CharField(max_length=10, choices=ACCESS_LEVEL_CHOICES, default='view')
    granted_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='granted_camera_accesses',
        help_text="User who granted this access"
    )
    
    # Access restrictions
    can_record = models.BooleanField(default=False, help_text="Can start/stop recordings")
    can_schedule = models.BooleanField(default=False, help_text="Can create/modify schedules")
    can_download = models.BooleanField(default=True, help_text="Can download recordings")
    
    # Time restrictions
    access_start_time = models.TimeField(blank=True, null=True, help_text="Daily access start time")
    access_end_time = models.TimeField(blank=True, null=True, help_text="Daily access end time")
    
    # Metadata
    granted_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-granted_at']
        verbose_name = 'Camera Access'
        verbose_name_plural = 'Camera Accesses'
        unique_together = ['user', 'camera']
    
    def __str__(self):
        return f"{self.user.email} - {self.camera.name} ({self.access_level})"


class LiveStream(models.Model):
    """Model for tracking live stream sessions"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name='live_streams')
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='live_streams',
        help_text="User who is viewing the live stream"
    )
    
    # Stream details
    session_id = models.CharField(max_length=100, unique=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    # Client info
    client_ip = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-start_time']
        verbose_name = 'Live Stream'
        verbose_name_plural = 'Live Streams'
    
    def __str__(self):
        return f"{self.camera.name} ({self.start_time})"


class GCPVideoTransfer(models.Model):
    """Model for tracking video transfers to GCP Cloud Storage with scheduled cleanup"""
    
    TRANSFER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('uploading', 'Uploading'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cleanup_pending', 'Cleanup Pending'),
        ('cleanup_completed', 'Cleanup Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recording = models.OneToOneField(
        Recording, 
        on_delete=models.CASCADE, 
        related_name='gcp_transfer',
        help_text="Associated recording"
    )
    
    # Transfer details
    original_local_path = models.CharField(max_length=500, help_text="Original local file path")
    gcp_storage_path = models.CharField(max_length=500, help_text="Path in GCP bucket")
    gcp_public_url = models.URLField(blank=True, null=True, help_text="Public URL to access the video")
    
    # Transfer metadata
    file_size_bytes = models.BigIntegerField(default=0, help_text="File size in bytes")
    transfer_status = models.CharField(max_length=20, choices=TRANSFER_STATUS_CHOICES, default='pending')
    
    # User who initiated the transfer
    initiated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='initiated_transfers',
        help_text="User who initiated this transfer"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, help_text="When transfer was initiated")
    upload_started_at = models.DateTimeField(blank=True, null=True, help_text="When upload started")
    upload_completed_at = models.DateTimeField(blank=True, null=True, help_text="When upload completed")
    
    # Cleanup scheduling (24 hours after upload)
    cleanup_scheduled_at = models.DateTimeField(blank=True, null=True, help_text="When local file cleanup is scheduled")
    cleanup_completed_at = models.DateTimeField(blank=True, null=True, help_text="When local file was deleted")
    
    # Error handling
    error_message = models.TextField(blank=True, null=True, help_text="Error details if transfer failed")
    retry_count = models.PositiveIntegerField(default=0, help_text="Number of retry attempts")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'GCP Video Transfer'
        verbose_name_plural = 'GCP Video Transfers'
    
    def __str__(self):
        return f"Transfer: {self.recording.name} ({self.transfer_status})"
    
    @property
    def file_size_mb(self):
        """Get file size in MB"""
        if self.file_size_bytes:
            return round(self.file_size_bytes / (1024 * 1024), 2)
        return 0
    
    @property
    def is_upload_completed(self):
        """Check if upload is completed"""
        return self.transfer_status == 'completed'
    
    @property
    def is_cleanup_due(self):
        """Check if cleanup is due (24 hours after upload completion)"""
        if not self.upload_completed_at:
            return False
        
        from django.utils import timezone
        from datetime import timedelta
        cleanup_time = self.upload_completed_at + timedelta(hours=24)
        return timezone.now() >= cleanup_time
    
    def schedule_cleanup(self):
        """Schedule cleanup 24 hours after upload completion"""
        if self.upload_completed_at and not self.cleanup_scheduled_at:
            from django.utils import timezone
            from datetime import timedelta
            self.cleanup_scheduled_at = self.upload_completed_at + timedelta(hours=24)
            self.transfer_status = 'cleanup_pending'
            self.save(update_fields=['cleanup_scheduled_at', 'transfer_status'])
    
    def mark_upload_started(self):
        """Mark upload as started"""
        from django.utils import timezone
        self.upload_started_at = timezone.now()
        self.transfer_status = 'uploading'
        self.save(update_fields=['upload_started_at', 'transfer_status'])
    
    def mark_upload_completed(self, gcp_path, public_url=None):
        """Mark upload as completed and schedule cleanup"""
        from django.utils import timezone
        self.upload_completed_at = timezone.now()
        self.gcp_storage_path = gcp_path
        self.gcp_public_url = public_url
        self.transfer_status = 'completed'
        self.save(update_fields=['upload_completed_at', 'gcp_storage_path', 'gcp_public_url', 'transfer_status'])
        
        # Schedule cleanup for 24 hours later
        self.schedule_cleanup()
    
    def mark_upload_failed(self, error_message):
        """Mark upload as failed"""
        self.transfer_status = 'failed'
        self.error_message = error_message
        self.retry_count += 1
        self.save(update_fields=['transfer_status', 'error_message', 'retry_count'])
    
    def mark_cleanup_completed(self):
        """Mark local file cleanup as completed"""
        from django.utils import timezone
        self.cleanup_completed_at = timezone.now()
        self.transfer_status = 'cleanup_completed'
        self.save(update_fields=['cleanup_completed_at', 'transfer_status'])