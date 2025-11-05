"""
Django Ninja API for CCTV management with comprehensive Swagger documentation
"""

from ninja import NinjaAPI, Router, Schema, Field
from ninja.pagination import paginate
from ninja.errors import HttpError
from ninja.security import HttpBearer
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from typing import List, Optional
import uuid
import logging

from .models import Camera, RecordingSchedule, Recording, CameraAccess, LiveStream, LocalRecordingClient
from .serializers import (
    CameraSerializer, RecordingSerializer, LiveStreamSerializer, CameraAccessSerializer, 
    RecordingScheduleSerializer, LocalClientScheduleSerializer, RecordingStatusUpdateSerializer,
    HeartbeatSerializer, LocalRecordingClientSerializer
)

logger = logging.getLogger(__name__)

# Import user authentication from users app
from apps.users.auth import verify_jwt_token

# CCTV JWT Authentication class for Django Ninja
class CCTVJWTAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            user = verify_jwt_token(token)
            # Basic role check - only allow dev and above to access CCTV
            if user.role not in ['superadmin', 'admin', 'dev']:
                return None
            # Set the user on the request object for Django Ninja compatibility
            request.user = user
            return user
        except Exception:
            return None

# Create authentication instance
cctv_jwt_auth = CCTVJWTAuth()

# CCTV Permission Helper Functions
def check_cctv_access(user, action='view'):
    """
    Check if user has access to CCTV features based on role hierarchy
    
    Permissions:
    - superadmin: Full access (create, manage, delete cameras and recordings)
    - admin: Full access (create, manage, delete cameras and recordings) 
    - dev: Limited access (view, control cameras, manage recordings)
    - visitor: No access to CCTV
    """
    role_permissions = {
        'superadmin': ['view', 'create', 'update', 'delete', 'control', 'manage'],
        'admin': ['view', 'create', 'update', 'delete', 'control', 'manage'],
        'dev': ['view', 'control', 'update'],
        'visitor': []
    }
    
    allowed_actions = role_permissions.get(user.role, [])
    return action in allowed_actions

def check_camera_access(user, camera=None):
    """Check if user can access a specific camera"""
    if not check_cctv_access(user, 'view'):
        return False
    
    # Superadmin and admin can access all cameras
    if user.role in ['superadmin', 'admin']:
        return True
    
    # For dev users, check if camera is public or they have specific access
    if camera:
        if camera.is_public:
            return True
        # Check specific camera access
        try:
            CameraAccess.objects.get(user=user, camera=camera, is_active=True)
            return True
        except CameraAccess.DoesNotExist:
            return False
    
    return True  # For listing, dev can see public cameras

# Schema definitions for Swagger documentation
class StreamResponseSchema(Schema):
    """Response schema for stream endpoint"""
    message: str = Field(..., description="Stream status message")
    camera_id: str = Field(..., description="Camera UUID")
    quality: str = Field(..., description="Stream quality (main/sub)")
    content_type: str = Field(..., description="MIME type of the stream")

class CameraRegistrationSchema(Schema):
    name: str = Field(..., description="Camera name/label", example="Front Door Camera")
    description: Optional[str] = Field(None, description="Camera description", example="Main entrance surveillance camera")
    ip_address: Optional[str] = Field(None, description="Camera IP address", example="192.168.1.100")
    port: Optional[int] = Field(554, description="RTSP port (usually 554)", example=554)
    username: Optional[str] = Field("", description="Camera username (leave empty for no auth)", example="admin")
    password: Optional[str] = Field("", description="Camera password (leave empty for no auth)", example="password123")
    rtsp_url: Optional[str] = Field(None, description="Full RTSP URL", example="rtsp://admin:password@192.168.1.100:554/stream1")
    rtsp_url_sub: Optional[str] = Field(None, description="Secondary RTSP stream URL", example="rtsp://admin:password@192.168.1.100:554/stream2")
    rtsp_path: Optional[str] = Field(None, description="Custom RTSP path (e.g., /live/0/MAIN, /stream1)", example="/live/0/SUB")
    camera_type: Optional[str] = Field("rtsp", description="Camera type", example="rtsp")
    location: Optional[str] = Field(None, description="Physical location", example="Front Entrance")
    auto_record: Optional[bool] = Field(False, description="Enable automatic recording", example=False)
    record_quality: Optional[str] = Field("medium", description="Recording quality", example="medium")
    max_recording_hours: Optional[int] = Field(24, description="Maximum hours to keep recordings", example=24)
    is_public: Optional[bool] = Field(False, description="Whether basic users can access this camera", example=False)
    test_connection: Optional[bool] = Field(True, description="Test connection before creating", example=True)
    start_recording: Optional[bool] = Field(False, description="Start 5-minute test recording", example=False)

class CameraUpdateSchema(Schema):
    name: Optional[str] = Field(None, description="Camera name", example="Front Door Camera")
    description: Optional[str] = Field(None, description="Camera description", example="Main entrance surveillance")
    ip_address: Optional[str] = Field(None, description="Camera IP address", example="192.168.1.100")
    port: Optional[int] = Field(None, description="RTSP port", example=554)
    username: Optional[str] = Field(None, description="RTSP username", example="admin")
    password: Optional[str] = Field(None, description="RTSP password", example="password123")
    rtsp_url: Optional[str] = Field(None, description="Main RTSP stream URL", example="rtsp://admin:password@192.168.1.100:554/stream1")
    rtsp_url_sub: Optional[str] = Field(None, description="Sub stream RTSP URL", example="rtsp://admin:password@192.168.1.100:554/stream2")
    rtsp_path: Optional[str] = Field(None, description="Custom RTSP path (e.g., /live/0/SUB, /stream1)", example="/live/0/SUB")
    camera_type: Optional[str] = Field(None, description="Camera type", example="rtsp")
    location: Optional[str] = Field(None, description="Camera location", example="Front Door")
    auto_record: Optional[bool] = Field(None, description="Enable automatic recording", example=True)
    record_quality: Optional[str] = Field(None, description="Recording quality", example="high")
    max_recording_hours: Optional[int] = Field(None, description="Maximum recording duration in hours", example=24)
    is_public: Optional[bool] = Field(None, description="Whether basic users can access this camera", example=False)
    status: Optional[str] = Field(None, description="Camera status", example="active")

class RecordingControlSchema(Schema):
    duration_minutes: Optional[int] = None
    recording_name: Optional[str] = None
    quality: Optional[str] = "main"

class ScheduleCreateSchema(Schema):
    camera: str = Field(..., description="Camera UUID", example="048d7515-e0c8-463d-97ce-8e51fe27280d")
    name: str = Field(..., description="Schedule name", example="Daily Morning Recording")
    schedule_type: str = Field(..., description="Schedule type: once, daily, weekly, continuous", example="daily")
    start_time: str = Field(..., description="Start time in HH:MM:SS format", example="08:00:00")
    end_time: str = Field(..., description="End time in HH:MM:SS format", example="10:00:00")
    start_date: Optional[str] = Field(None, description="Start date for one-time schedules (YYYY-MM-DD)", example="2025-08-15")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)", example="2025-08-30")
    days_of_week: Optional[List[str]] = Field(default=[], description="Days for weekly schedules", example=["monday", "tuesday", "wednesday", "thursday", "friday"])
    recording_quality: Optional[str] = Field("main", description="Recording quality (main/sub)", example="main")
    is_active: Optional[bool] = Field(True, description="Whether schedule is active", example=True)

class ScheduleUpdateSchema(Schema):
    name: Optional[str] = Field(None, description="Schedule name")
    schedule_type: Optional[str] = Field(None, description="Schedule type (once/daily/weekly/continuous)")
    start_time: Optional[str] = Field(None, description="Start time in HH:MM:SS format")
    end_time: Optional[str] = Field(None, description="End time in HH:MM:SS format")
    start_date: Optional[str] = Field(None, description="Start date for one-time schedules (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    days_of_week: Optional[List[str]] = Field(None, description="Days for weekly schedules")
    recording_quality: Optional[str] = Field(None, description="Recording quality (main/sub)")
    is_active: Optional[bool] = Field(None, description="Whether schedule is active")

class CameraResponseSchema(Schema):
    id: str
    name: str
    ip_address: str
    rtsp_url: str
    status: str
    location: Optional[str] = None

class RecordingStatusSchema(Schema):
    camera_id: str
    camera_name: str
    is_recording: bool
    recording_info: Optional[dict] = None
    recent_recordings: List[dict] = []

class RecordingStatsSchema(Schema):
    total_recordings: int
    completed_recordings: int
    failed_recordings: int
    active_recordings: int
    total_size_bytes: int
    total_size_gb: float
    total_duration_seconds: float
    total_duration_hours: float
    success_rate: float

class SuccessResponseSchema(Schema):
    message: str
    recording_id: Optional[str] = None
    recording_name: Optional[str] = None

class CameraRegistrationResponseSchema(Schema):
    message: str
    camera: CameraResponseSchema
    recording: Optional[dict] = None

class CameraUpdateResponseSchema(Schema):
    message: str = Field(..., description="Success message")
    camera_id: str = Field(..., description="Updated camera UUID")
    updated_fields: List[str] = Field(..., description="List of fields that were updated")
    camera: dict = Field(..., description="Updated camera information")

class CameraDeleteResponseSchema(Schema):
    message: str = Field(..., description="Success message")
    camera_id: str = Field(..., description="Deleted camera UUID")
    deleted_at: str = Field(..., description="Deletion timestamp")

class CameraDetailResponseSchema(Schema):
    id: str = Field(..., description="Camera UUID")
    name: str = Field(..., description="Camera name")
    description: str = Field(..., description="Camera description")
    ip_address: str = Field(..., description="Camera IP address")
    port: int = Field(..., description="RTSP port")
    rtsp_url: str = Field(..., description="Main RTSP stream URL")
    rtsp_url_sub: Optional[str] = Field(None, description="Sub stream RTSP URL")
    rtsp_path: Optional[str] = Field(None, description="Custom RTSP path")
    camera_type: str = Field(..., description="Camera type")
    status: str = Field(..., description="Camera status")
    location: Optional[str] = Field(None, description="Camera location")
    auto_record: bool = Field(..., description="Automatic recording enabled")
    record_quality: str = Field(..., description="Recording quality")
    max_recording_hours: Optional[int] = Field(None, description="Maximum recording duration")
    is_online: bool = Field(..., description="Camera online status")
    recording_count: int = Field(..., description="Total number of recordings")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    last_seen: Optional[str] = Field(None, description="Last seen timestamp")

class RecordingOverviewResponseSchema(Schema):
    total_cameras: int = Field(..., description="Total number of cameras")
    recording_cameras: int = Field(..., description="Number of cameras currently recording")
    online_cameras: int = Field(..., description="Number of online cameras")
    cameras: List[dict] = Field(..., description="List of camera information with recording status")

class RecordingStatsResponseSchema(Schema):
    total_recordings: int = Field(..., description="Total number of recordings")
    completed_recordings: int = Field(..., description="Number of completed recordings")
    failed_recordings: int = Field(..., description="Number of failed recordings")
    active_recordings: int = Field(..., description="Number of active recordings")
    success_rate: float = Field(..., description="Success rate percentage")
    total_size_bytes: int = Field(..., description="Total size in bytes")
    total_size_gb: float = Field(..., description="Total size in GB")
    total_duration_seconds: float = Field(..., description="Total duration in seconds")
    total_duration_hours: float = Field(..., description="Total duration in hours")

class ScheduleDetailResponseSchema(Schema):
    id: str = Field(..., description="Schedule UUID")
    camera: str = Field(..., description="Camera UUID")
    camera_name: str = Field(..., description="Camera name")
    name: str = Field(..., description="Schedule name")
    schedule_type: str = Field(..., description="Schedule type")
    start_time: str = Field(..., description="Start time")
    end_time: str = Field(..., description="End time")
    start_date: Optional[str] = Field(None, description="Start date")
    end_date: Optional[str] = Field(None, description="End date")
    days_of_week: List[str] = Field(..., description="Days of week for weekly schedules")
    is_active: bool = Field(..., description="Schedule active status")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

class RecordingDetailResponseSchema(Schema):
    id: str = Field(..., description="Recording UUID")
    camera: str = Field(..., description="Camera UUID")
    camera_name: str = Field(..., description="Camera name")
    schedule: Optional[str] = Field(None, description="Schedule UUID")
    schedule_name: Optional[str] = Field(None, description="Schedule name")
    name: str = Field(..., description="Recording name")
    file_path: str = Field(..., description="File path")
    file_size: int = Field(..., description="File size in bytes")
    file_size_mb: float = Field(..., description="File size in MB")
    duration: Optional[str] = Field(None, description="Recording duration")
    duration_seconds: float = Field(..., description="Duration in seconds")
    start_time: str = Field(..., description="Start time")
    end_time: Optional[str] = Field(None, description="End time")
    status: str = Field(..., description="Recording status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    resolution: Optional[str] = Field(None, description="Video resolution")
    frame_rate: Optional[float] = Field(None, description="Frame rate")
    codec: Optional[str] = Field(None, description="Video codec")
    file_url: str = Field(..., description="File download URL")
    is_active: bool = Field(..., description="Recording active status")
    file_exists: bool = Field(..., description="File exists on disk")

class ScheduleUpdateResponseSchema(Schema):
    message: str = Field(..., description="Success message")
    schedule_id: str = Field(..., description="Updated schedule UUID")
    updated_fields: List[str] = Field(..., description="List of fields that were updated")
    schedule: dict = Field(..., description="Updated schedule information")

class ScheduleDeleteResponseSchema(Schema):
    message: str = Field(..., description="Success message")
    schedule_id: str = Field(..., description="Deleted schedule UUID")
    schedule_name: str = Field(..., description="Deleted schedule name")
    deleted_at: str = Field(..., description="Deletion timestamp")

class ScheduleActivationResponseSchema(Schema):
    message: str = Field(..., description="Success message")
    schedule_id: str = Field(..., description="Schedule UUID")
    schedule_name: str = Field(..., description="Schedule name")
    camera_name: str = Field(..., description="Camera name")
    action: str = Field(..., description="Action performed (activate/deactivate)")
    timestamp: str = Field(..., description="Action timestamp")

class CameraItemSchema(Schema):
    """Schema for individual camera items in the list response"""
    id: str = Field(..., description="Camera UUID")
    name: str = Field(..., description="Camera name")
    ip_address: str = Field(..., description="Camera IP address")
    status: str = Field(..., description="Camera status")
    location: Optional[str] = Field(None, description="Camera location")
    camera_type: str = Field(..., description="Camera type")
    is_online: bool = Field(..., description="Camera online status")
    last_seen: Optional[str] = Field(None, description="Last seen timestamp")
    rtsp_url: Optional[str] = Field(None, description="Main RTSP stream URL")
    rtsp_url_sub: Optional[str] = Field(None, description="Sub stream RTSP URL")
    auto_record: bool = Field(..., description="Automatic recording enabled")
    record_quality: str = Field(..., description="Recording quality")
    max_recording_hours: int = Field(..., description="Maximum recording duration in hours")

class CameraListResponseSchema(Schema):
    total_cameras: int = Field(..., description="Total number of cameras")
    online_cameras: int = Field(..., description="Number of online cameras")
    recording_cameras: int = Field(..., description="Number of cameras currently recording")
    cameras: List[CameraItemSchema] = Field(..., description="List of cameras")

class RecordingItemSchema(Schema):
    id: str = Field(..., description="Recording UUID")
    camera: str = Field(..., description="Camera UUID")
    camera_name: str = Field(..., description="Camera name")
    schedule: Optional[str] = Field(None, description="Schedule UUID")
    schedule_name: Optional[str] = Field(None, description="Schedule name")
    name: str = Field(..., description="Recording name")
    file_size_mb: float = Field(..., description="File size in MB")
    duration_seconds: Optional[float] = Field(None, description="Duration in seconds")
    start_time: str = Field(..., description="Start time")
    end_time: Optional[str] = Field(None, description="End time")
    status: str = Field(..., description="Recording status")
    file_url: str = Field(..., description="File download URL")
    # Additional fields that the serializer might return
    file_path: Optional[str] = Field(None, description="File path")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    duration: Optional[str] = Field(None, description="Duration")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    resolution: Optional[str] = Field(None, description="Video resolution")
    frame_rate: Optional[float] = Field(None, description="Frame rate")
    codec: Optional[str] = Field(None, description="Video codec")
    is_active: Optional[bool] = Field(None, description="Recording active status")
    file_exists: Optional[bool] = Field(None, description="File exists on disk")
    absolute_file_path: Optional[str] = Field(None, description="Absolute file path")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")

class RecordingListResponseSchema(Schema):
    total_recordings: int = Field(..., description="Total number of recordings")
    completed_recordings: int = Field(..., description="Number of completed recordings")
    failed_recordings: int = Field(..., description="Number of failed recordings")
    recordings: List[RecordingItemSchema] = Field(..., description="List of recordings")

class ScheduleItemSchema(Schema):
    id: str = Field(..., description="Schedule UUID")
    camera: str = Field(..., description="Camera UUID")
    camera_name: str = Field(..., description="Camera name")
    name: str = Field(..., description="Schedule name")
    schedule_type: str = Field(..., description="Schedule type")
    start_time: str = Field(..., description="Start time")
    end_time: str = Field(..., description="End time")
    is_active: bool = Field(..., description="Schedule active status")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

class ScheduleListResponseSchema(Schema):
    total_schedules: int = Field(..., description="Total number of schedules")
    active_schedules: int = Field(..., description="Number of active schedules")
    schedules: List[ScheduleItemSchema] = Field(..., description="List of schedules")

class StreamSessionItemSchema(Schema):
    id: str = Field(..., description="Stream session UUID")
    camera: str = Field(..., description="Camera UUID")
    camera_name: str = Field(..., description="Camera name")
    user: Optional[str] = Field(None, description="User UUID")
    username: Optional[str] = Field(None, description="Username")
    quality: str = Field(..., description="Stream quality")
    start_time: str = Field(..., description="Start time")
    end_time: Optional[str] = Field(None, description="End time")
    duration_seconds: Optional[float] = Field(None, description="Duration in seconds")
    is_active: bool = Field(..., description="Stream active status")

class StreamSessionListResponseSchema(Schema):
    total_streams: int = Field(..., description="Total number of stream sessions")
    active_streams: int = Field(..., description="Number of active streams")
    streams: List[StreamSessionItemSchema] = Field(..., description="List of stream sessions")

class ScheduleResponseSchema(Schema):
    message: str
    schedule_id: str

class StreamInfoSchema(Schema):
    camera_id: str = Field(..., description="Camera UUID")
    camera_name: str = Field(..., description="Camera name")
    status: str = Field(..., description="Camera status")
    is_online: bool = Field(..., description="Whether camera is online")
    is_streaming: bool = Field(..., description="Whether camera is currently streaming")
    stream_urls: dict = Field(..., description="Available stream URLs")
    supported_qualities: List[str] = Field(..., description="Supported quality options")
    rtsp_info: dict = Field(..., description="RTSP connection information")

class ActiveStreamSchema(Schema):
    stream_key: str = Field(..., description="Unique stream identifier")
    camera_id: str = Field(..., description="Camera UUID")
    camera_name: str = Field(..., description="Camera name")
    quality: str = Field(..., description="Stream quality")
    viewers: int = Field(..., description="Number of viewers")
    last_update: Optional[str] = Field(None, description="Last frame update timestamp")
    uptime_seconds: int = Field(..., description="Stream uptime in seconds")

class ActiveStreamsResponseSchema(Schema):
    total_active_streams: int = Field(..., description="Total number of active streams")
    streams: List[ActiveStreamSchema] = Field(..., description="List of active streams")

# GCP Video Transfer Schemas
class GCPTransferRequestSchema(Schema):
    """Schema for initiating GCP video transfer"""
    recording_ids: Optional[List[str]] = Field(None, description="List of specific recording IDs to transfer (optional - if not provided, all local recordings will be transferred)")
    batch_size: Optional[int] = Field(5, description="Number of videos to process simultaneously", ge=1, le=20)

class GCPTransferResponseSchema(Schema):
    """Response schema for GCP video transfer initiation"""
    message: str = Field(..., description="Transfer initiation status message")
    total_recordings: int = Field(..., description="Total number of recordings found for transfer")
    initiated_transfers: int = Field(..., description="Number of transfers successfully initiated")
    already_transferred: int = Field(..., description="Number of recordings already transferred")
    failed_initiations: int = Field(..., description="Number of transfers that failed to initiate")
    transfer_ids: List[str] = Field(..., description="List of transfer IDs created")

class GCPTransferStatusSchema(Schema):
    """Schema for GCP transfer status"""
    transfer_id: str = Field(..., description="Transfer ID")
    recording_name: str = Field(..., description="Recording name")
    transfer_status: str = Field(..., description="Current transfer status")
    file_size_mb: float = Field(..., description="File size in MB")
    gcp_storage_path: Optional[str] = Field(None, description="GCP storage path")
    gcp_public_url: Optional[str] = Field(None, description="GCP public URL")
    upload_started_at: Optional[str] = Field(None, description="Upload start timestamp")
    upload_completed_at: Optional[str] = Field(None, description="Upload completion timestamp")
    cleanup_scheduled_at: Optional[str] = Field(None, description="Cleanup scheduled timestamp")
    cleanup_completed_at: Optional[str] = Field(None, description="Cleanup completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_count: int = Field(..., description="Number of retry attempts")

class GCPTransferListResponseSchema(Schema):
    """Response schema for listing GCP transfers"""
    transfers: List[GCPTransferStatusSchema] = Field(..., description="List of transfer statuses")
    total_count: int = Field(..., description="Total number of transfers")
    pending_count: int = Field(..., description="Number of pending transfers")
    uploading_count: int = Field(..., description="Number of currently uploading transfers")
    completed_count: int = Field(..., description="Number of completed transfers")
    failed_count: int = Field(..., description="Number of failed transfers")

User = get_user_model()

# Helper function to format serializer errors
def format_serializer_errors(errors):
    """Convert DRF serializer errors to a readable string"""
    error_messages = []
    for field, field_errors in errors.items():
        if isinstance(field_errors, list):
            field_errors_str = ', '.join(str(error) for error in field_errors)
        else:
            field_errors_str = str(field_errors)
        error_messages.append(f"{field}: {field_errors_str}")
    return '; '.join(error_messages)

# Create router for CCTV endpoints
router = Router(tags=["CCTV Management"])

# Health check endpoint for Swagger
@router.get("/health/", 
            summary="API Health Check",
            description="Simple health check endpoint to verify API is working",
            tags=["System"])
def health_check(request):
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": timezone.now().isoformat(),
        "service": "CCTV API",
        "version": "1.0.0"
    }

def get_cctv_api():
    """Return the CCTV API router for integration"""
    return router



# Camera endpoints
@router.get("/cameras/", response=CameraListResponseSchema, summary="List Cameras", description="Get a list of all cameras accessible to the authenticated user", auth=cctv_jwt_auth)
def list_cameras(request):
    """List all cameras accessible to the user based on their role"""
    from .serializers import CameraListSerializer
    
    current_user = request.auth
    if not current_user:
        raise HttpError(401, "Authentication required")
    
    if not check_cctv_access(current_user, 'view'):
        raise HttpError(403, "CCTV access denied. Dev role or higher required.")
    
    # Get cameras based on user role
    if current_user.role in ['superadmin', 'admin']:
        # Superadmin and admin can see all cameras
        queryset = Camera.objects.filter(is_active=True)
    else:
        # Dev users can see public cameras and cameras they have access to
        user_camera_ids = CameraAccess.objects.filter(
            user=current_user, 
            is_active=True
        ).values_list('camera_id', flat=True)
        
        queryset = Camera.objects.filter(
            is_active=True
        ).filter(
            models.Q(is_public=True) | models.Q(id__in=user_camera_ids)
        )
    
    # Use the list serializer directly
    cameras_data = [CameraListSerializer(camera).data for camera in queryset]
    
    return {
        "total_cameras": len(cameras_data),
        "online_cameras": sum(1 for cam in cameras_data if cam.get('is_online', False)),
        "recording_cameras": 0,  # This would need to be calculated from recording manager
        "cameras": cameras_data
    }


@router.get("/cameras/multi-stream/", auth=cctv_jwt_auth,
            summary="Multi-Camera Stream Dashboard",
            description="Get a dashboard view with multiple camera streams for monitoring multiple feeds simultaneously")
def multi_camera_stream_dashboard(request):
    """Get multi-camera stream dashboard information"""
    from .models import Camera
    from .streaming import stream_manager
    
    try:
        # Get all active cameras
        cameras = Camera.objects.filter(is_active=True, status='active')
        
        dashboard_data = []
        for camera in cameras:
            # Check if camera is currently streaming
            is_streaming = any(info['camera'].id == camera.id for info in stream_manager.active_streams.values())
            
            # Get stream health
            health = stream_manager.get_stream_health(camera.id, 'main')
            
            camera_info = {
                "camera_id": str(camera.id),
                "camera_name": camera.name,
                "status": camera.status,
                "is_online": camera.status == 'active' and camera.last_seen is not None,
                "is_streaming": is_streaming,
                "stream_health": health,
                "stream_urls": {
                    "main": f"/v0/api/cctv/cameras/{camera.id}/stream/?quality=main",
                    "sub": f"/v0/api/cctv/cameras/{camera.id}/stream/?quality=sub" if camera.rtsp_url_sub else None
                },
                "location": camera.location,
                "last_seen": camera.last_seen.isoformat() if camera.last_seen else None,
                "rtsp_url": camera.rtsp_url,
                "supported_qualities": ["main"] + (["sub"] if camera.rtsp_url_sub else [])
            }
            
            dashboard_data.append(camera_info)
        
        return {
            "total_cameras": len(dashboard_data),
            "online_cameras": sum(1 for cam in dashboard_data if cam['is_online']),
            "streaming_cameras": sum(1 for cam in dashboard_data if cam['is_streaming']),
            "cameras": dashboard_data
        }
        
    except Exception as e:
        logger.error(f"Error getting multi-camera dashboard: {str(e)}")
        raise HttpError(500, f"Internal server error: {str(e)}")


@router.post("/cameras/register/", response=CameraRegistrationResponseSchema,  
            summary="Register Camera", auth=cctv_jwt_auth, 
            description="""
            Register a new camera with IP address or RTSP URL. Optionally test connection and start recording.
            
            **Complete Payload Example:**
            ```json
            {
              "name": "Front Door Camera",
              "description": "Main entrance surveillance camera",
              "ip_address": "192.168.1.100",
              "port": 554,
              "username": "admin",
              "password": "password123",
              "rtsp_url": "rtsp://admin:password@192.168.1.100:554/stream1",
              "rtsp_url_sub": "rtsp://admin:password@192.168.1.100:554/stream2",
              "rtsp_path": "/live/0/SUB",
              "camera_type": "rtsp",
              "location": "Front Entrance",
              "auto_record": true,
              "record_quality": "high",
              "max_recording_hours": 48,
              "is_public": false,
              "test_connection": true,
              "start_recording": false
            }
            ```
            
            **Minimal Payload Example:**
            ```json
            {
              "name": "Simple Camera",
              "ip_address": "192.168.1.101",
              "rtsp_url": "rtsp://192.168.1.101:554/stream1"
            }
            ```
            """)
def register_camera(request, camera_data: CameraRegistrationSchema):
    """Register/setup a new camera with comprehensive options (Admin/Superadmin only)"""
    from .serializers import CameraRegistrationSerializer
    from .streaming import test_camera_connection, safe_save_camera
    from django.utils import timezone
    from datetime import timedelta
    
    current_user = request.auth
    if not current_user:
        raise HttpError(401, "Authentication required")
    
    if not check_cctv_access(current_user, 'create'):
        raise HttpError(403, "Camera registration denied. Admin role or higher required.")
    
    try:
        
        # Convert Ninja schema to dictionary for Django serializer
        camera_data_dict = camera_data.dict()
        
        # Normalize blanks before serializer validation
        # - drop blank username/password so DRF doesn't flag them
        if 'username' in camera_data_dict and (camera_data_dict['username'] is None or camera_data_dict['username'] == ''):
            camera_data_dict.pop('username')
        if 'password' in camera_data_dict and (camera_data_dict['password'] is None or camera_data_dict['password'] == ''):
            camera_data_dict.pop('password')
        # Normalize localhost to a valid IP for IPAddressField
        if camera_data_dict.get('ip_address') == 'localhost':
            camera_data_dict['ip_address'] = '127.0.0.1'
        
        # Validate input data
        serializer = CameraRegistrationSerializer(data=camera_data_dict)
        if not serializer.is_valid():
            # Convert serializer errors to a proper error message
            raise HttpError(400, format_serializer_errors(serializer.errors))
        
        data = serializer.validated_data
        
        # Test connection if requested - verify camera is actually working
        if data.get('test_connection', True):
            logger.info(f"Testing connection for camera: {data['rtsp_url']}")
            success, message = test_camera_connection(data['rtsp_url'])
            if not success:
                raise HttpError(400, f'Camera connection test failed: {message}. Please verify the RTSP URL is correct and the camera is accessible.')
        
        # Prepare camera data for creation
        camera_creation_data = {
            'name': data['name'],
            'description': data.get('description', f'Camera at {data.get("ip_address", "unknown")}'),
            'ip_address': data['ip_address'],
            'port': data.get('port', 554),
            'username': data.get('username'),
            'password': data.get('password'),
            'rtsp_url': data['rtsp_url'],
            'rtsp_url_sub': data.get('rtsp_url_sub'),
            'rtsp_path': data.get('rtsp_path'),
            'camera_type': data.get('camera_type', 'rtsp'),
            'location': data.get('location'),
            'auto_record': data.get('auto_record', False),
            'record_quality': data.get('record_quality', 'medium'),
            'max_recording_hours': data.get('max_recording_hours', 24),
            'is_public': data.get('is_public', False),
        }
        
        # If rtsp_path is not provided but rtsp_url is, extract path from URL
        if not camera_creation_data.get('rtsp_path') and camera_creation_data.get('rtsp_url'):
            from urllib.parse import urlparse
            try:
                parsed = urlparse(camera_creation_data['rtsp_url'])
                if parsed.path:
                    camera_creation_data['rtsp_path'] = parsed.path
            except Exception:
                pass  # If parsing fails, continue without path
        
        # Handle blank username and password explicitly
        username = camera_creation_data.get('username')
        password = camera_creation_data.get('password')
        
        # Convert empty strings to None for proper database storage
        if username == '':
            username = None
        if password == '':
            password = None
        
        # Create camera with initial status 'inactive' - will be set to 'active' if streaming works
        camera = Camera.objects.create(
            name=camera_creation_data['name'],
            description=camera_creation_data.get('description', ''),
            ip_address=camera_creation_data['ip_address'],
            port=camera_creation_data.get('port', 554),
            username=username,
            password=password,
            rtsp_url=camera_creation_data['rtsp_url'],
            rtsp_url_sub=camera_creation_data.get('rtsp_url_sub', ''),
            rtsp_path=camera_creation_data.get('rtsp_path'),
            camera_type=camera_creation_data.get('camera_type', 'rtsp'),
            status='inactive',  # Start as inactive, will be set to active if streaming works
            location=camera_creation_data.get('location', ''),
            auto_record=camera_creation_data.get('auto_record', False),
            record_quality=camera_creation_data.get('record_quality', 'medium'),
            max_recording_hours=camera_creation_data.get('max_recording_hours', 24),
            is_public=camera_creation_data.get('is_public', False),
            created_by=current_user
        )
        
        # Verify streaming actually works before marking camera as active
        streaming_works = False
        stream_error = None
        
        try:
            from .streaming import stream_manager
            logger.info(f"Verifying streaming for newly registered camera: {camera.name}")
            
            # Attempt to start stream
            stream_info = stream_manager.start_stream(camera, 'main')
            
            if stream_info:
                # Give stream a moment to stabilize
                import time
                time.sleep(1)
                
                # Check if stream is actually providing frames
                frame = stream_manager.get_frame(camera.id, 'main')
                
                if frame is not None and frame.size > 0:
                    streaming_works = True
                    logger.info(f"Stream verification successful for camera: {camera.name}")
                    
                    # Mark camera as active and online
                    camera.status = 'active'
                    camera.is_online = True
                    camera.is_streaming = True
                    camera.last_seen = timezone.now()
                    safe_save_camera(camera, update_fields=['status', 'is_online', 'is_streaming', 'last_seen'])
                    
                    logger.info(f"Camera {camera.name} successfully registered and streaming")
                else:
                    stream_error = "Stream started but no frames received"
                    logger.warning(f"Stream verification failed for camera {camera.name}: {stream_error}")
                    # Stop the failed stream
                    try:
                        stream_manager.stop_stream(camera.id, 'main')
                    except:
                        pass
            else:
                stream_error = "Failed to start stream"
                logger.warning(f"Stream start failed for camera {camera.name}: {stream_error}")
                
        except Exception as e:
            stream_error = str(e)
            logger.error(f"Error verifying stream for camera {camera.name}: {stream_error}")
            # Stop stream if it was partially started
            try:
                from .streaming import stream_manager
                stream_manager.stop_stream(camera.id, 'main')
            except:
                pass
        
        # If streaming failed, set appropriate status
        if not streaming_works:
            camera.status = 'error'
            camera.is_online = False
            camera.is_streaming = False
            safe_save_camera(camera, update_fields=['status', 'is_online', 'is_streaming'])
            
            # Include warning in response but don't fail registration
            logger.warning(f"Camera {camera.name} registered but streaming verification failed: {stream_error}")
        
        # Build response message based on streaming status
        if streaming_works:
            message = 'Camera registered and streaming successfully'
        else:
            message = f'Camera registered but streaming verification failed: {stream_error if stream_error else "Unknown error"}. Camera status set to "error".'
        
        response_data = {
            'message': message,
            'camera': {
                'id': str(camera.id),
                'name': camera.name,
                'description': camera.description,
                'ip_address': camera.ip_address,
                'port': camera.port,
                'username': camera.username,
                'rtsp_url': camera.rtsp_url,
                'rtsp_url_sub': camera.rtsp_url_sub,
                'rtsp_path': camera.rtsp_path,
                'camera_type': camera.camera_type,
                'status': camera.status,
                'location': camera.location,
                'auto_record': camera.auto_record,
                'record_quality': camera.record_quality,
                'max_recording_hours': camera.max_recording_hours,
                'is_public': camera.is_public,
                'is_online': camera.is_online,
                'is_streaming': camera.is_streaming
            }
        }
        
        # Add warning if streaming failed
        if not streaming_works:
            response_data['warning'] = stream_error or 'Streaming verification failed'
            response_data['status'] = 'partial_success'
        
        # Start test recording if requested
        if data.get('start_recording', False):
            try:
                recording = camera.auto_record_5min(user=current_user)
                if recording:
                    response_data['recording'] = {
                        'id': str(recording.id),
                        'name': recording.name,
                        'duration_minutes': 5,
                        'estimated_end_time': (timezone.now() + timedelta(minutes=5)).isoformat()
                    }
                else:
                    response_data['warning'] = 'Camera created but test recording failed to start'
            except Exception as e:
                response_data['warning'] = f'Camera created but test recording failed: {str(e)}'
        
        return response_data
            
    except HttpError:
        # Re-raise HttpError as-is (it already has proper error message)
        raise
    except Exception as e:
        # Handle other exceptions
        raise HttpError(500, f"Internal server error: {str(e)}")


@router.post("/cameras/{camera_id}/start_recording/", response=SuccessResponseSchema,
            summary="Start Recording", auth=cctv_jwt_auth,
            description="Start recording from a camera with optional duration and custom name")
def start_recording(request, camera_id: uuid.UUID, recording_data: RecordingControlSchema):
    """Start recording from camera (Dev role or higher required)"""
    from .streaming import recording_manager
    from datetime import datetime
    
    current_user = request.auth
    if not current_user:
        raise HttpError(401, "Authentication required")
    
    if not check_cctv_access(current_user, 'control'):
        raise HttpError(403, "Recording control denied. Dev role or higher required.")
    
    try:
        camera = get_object_or_404(Camera, id=camera_id)
        
        if not check_camera_access(current_user, camera):
            raise HttpError(403, "Access denied to this camera")
        
        # Auto-generate recording name if not provided
        recording_name = recording_data.recording_name
        if not recording_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            recording_name = f"{camera.name}_{timestamp}"
        
        recording = recording_manager.start_recording(
            camera=camera,
            duration_minutes=recording_data.duration_minutes,
            recording_name=recording_name,
            user=current_user
        )
        
        return {
            'message': 'Recording started successfully',
            'recording_id': str(recording.id),
            'recording_name': recording.name
        }
        
    except Exception as e:
        raise HttpError(500, str(e))


@router.post("/cameras/{camera_id}/stop_recording/", response=SuccessResponseSchema,
            summary="Stop Recording", auth=cctv_jwt_auth,
            description="Stop the current recording for a camera")
def stop_recording(request, camera_id: uuid.UUID):
    """Stop recording from camera (Dev role or higher required)"""
    from .streaming import recording_manager
    
    current_user = request.auth
    if not current_user:
        raise HttpError(401, "Authentication required")
    
    if not check_cctv_access(current_user, 'control'):
        raise HttpError(403, "Recording control denied. Dev role or higher required.")
    
    try:
        camera = get_object_or_404(Camera, id=camera_id)
        
        if not check_camera_access(current_user, camera):
            raise HttpError(403, "Access denied to this camera")
        
        recording = recording_manager.stop_recording(camera_id)
        
        return {
            'message': 'Recording stopped successfully',
            'recording_id': str(recording.id),
            'recording_name': recording.name
        }
        
    except Exception as e:
        raise HttpError(500, str(e))


@router.get("/cameras/{camera_id}/recording_status/", response=RecordingStatusSchema, auth=cctv_jwt_auth,
            summary="Recording Status",
            description="Get the current recording status and recent recordings for a camera")
def recording_status(request, camera_id: uuid.UUID):
    """Get current recording status for camera"""
    from .streaming import recording_manager
    from django.utils import timezone
    from datetime import timedelta
    
    try:
        camera = get_object_or_404(Camera, id=camera_id)
        is_recording = recording_manager.is_recording(camera_id)
        
        response_data = {
            'camera_id': str(camera.id),
            'camera_name': camera.name,
            'is_recording': is_recording,
            'recording_info': None
        }
        
        if is_recording:
            # Get active recording info
            recording_info = recording_manager.active_recordings.get(str(camera_id))
            if recording_info:
                recording = recording_info['recording']
                elapsed_time = (timezone.now() - recording_info['start_time']).total_seconds()
                
                response_data['recording_info'] = {
                    'recording_id': str(recording.id),
                    'recording_name': recording.name,
                    'start_time': recording.start_time.isoformat(),
                    'elapsed_seconds': int(elapsed_time),
                    'elapsed_formatted': str(timedelta(seconds=int(elapsed_time))),
                    'frame_count': recording_info['frame_count'],
                    'duration_minutes': recording_info['duration_minutes'],
                    'estimated_end_time': None
                }
                
                if recording_info['duration_minutes']:
                    estimated_end = recording_info['start_time'] + timedelta(minutes=recording_info['duration_minutes'])
                    response_data['recording_info']['estimated_end_time'] = estimated_end.isoformat()
        
        # Get recent recordings
        recent_recordings = Recording.objects.filter(camera=camera).order_by('-start_time')[:5]
        response_data['recent_recordings'] = []
        
        for rec in recent_recordings:
            response_data['recent_recordings'].append({
                'id': str(rec.id),
                'name': rec.name,
                'status': rec.status,
                'start_time': rec.start_time.isoformat(),
                'duration': str(rec.duration) if rec.duration else None,
                'file_size_mb': round(rec.file_size / (1024 * 1024), 2) if rec.file_size else 0
            })
        
        return response_data
        
    except Exception as e:
        raise HttpError(500, str(e))


@router.get("/cameras/recording_overview/", response=RecordingOverviewResponseSchema, auth=cctv_jwt_auth,
            summary="Recording Overview", 
            description="Get overview of all camera recording statuses and recent activity")
def recording_overview(request):
    """Get overview of all camera recording statuses"""
    from .streaming import recording_manager
    
    try:
        # Since auth is disabled, get all cameras directly
        cameras = Camera.objects.all()
        
        overview = []
        
        for camera in cameras:
            is_recording = recording_manager.is_recording(camera.id)
            
            camera_info = {
                'camera_id': str(camera.id),
                'camera_name': camera.name,
                'ip_address': camera.ip_address,
                'status': camera.status,
                'is_online': camera.is_online,
                'is_recording': is_recording,
                'total_recordings': camera.recordings.count(),
                'last_recording': None
            }
            
            # Get last recording
            last_recording = camera.recordings.order_by('-start_time').first()
            if last_recording:
                camera_info['last_recording'] = {
                    'id': str(last_recording.id),
                    'name': last_recording.name,
                    'start_time': last_recording.start_time.isoformat(),
                    'status': last_recording.status
                }
            
            overview.append(camera_info)
        
        return {
            'total_cameras': len(overview),
            'recording_cameras': sum(1 for c in overview if c['is_recording']),
            'online_cameras': sum(1 for c in overview if c['is_online']),
            'cameras': overview
        }
        
    except Exception as e:
        raise HttpError(500, str(e))


@router.get("/cameras/{camera_id}/", response=CameraDetailResponseSchema, auth=cctv_jwt_auth,
            summary="Get Camera Details",
            description="Retrieve detailed information about a specific camera")
def get_camera(request, camera_id: uuid.UUID):
    """Get a specific camera (with role-based access control)"""
    from .serializers import CameraSerializer
    
    current_user = request.auth
    if not current_user:
        raise HttpError(401, "Authentication required")
    
    camera = get_object_or_404(Camera, id=camera_id)
    
    if not check_camera_access(current_user, camera):
        raise HttpError(403, "Access denied to this camera")
    
    return CameraSerializer(camera).data


@router.post("/cameras/{camera_id}/validate_update/", response=dict, auth=cctv_jwt_auth,
            summary="Validate Camera Update Payload",
            description="Test camera update payload without making changes (for debugging)")
def validate_camera_update(request, camera_id: uuid.UUID, camera_data: CameraUpdateSchema):
    """Validate camera update payload without making changes (Admin/Superadmin only)"""
    from .serializers import CameraSerializer
    
    current_user = request.auth
    if not current_user:
        raise HttpError(401, "Authentication required")
    
    if not check_cctv_access(current_user, 'update'):
        raise HttpError(403, "Camera update validation denied. Admin role or higher required.")
    
    camera = get_object_or_404(Camera, id=camera_id)
    
    if not check_camera_access(current_user, camera):
        raise HttpError(403, "Access denied to this camera")
    
    try:
        # Convert Ninja schema to dictionary for Django serializer
        update_data = camera_data.dict(exclude_unset=True)
        
        # Filter out fields that are not part of the Camera model
        model_fields = {
            'name', 'description', 'ip_address', 'port', 'username', 'password',
            'rtsp_url', 'rtsp_url_sub', 'rtsp_path', 'camera_type', 'status',
            'location', 'auto_record', 'record_quality', 'max_recording_hours', 'is_public'
        }
        
        # Remove non-model fields
        update_data = {k: v for k, v in update_data.items() if k in model_fields}
        
        # Set default values for missing fields to ensure model compatibility
        if 'max_recording_hours' not in update_data:
            update_data['max_recording_hours'] = camera.max_recording_hours or 24
        if 'is_public' not in update_data:
            update_data['is_public'] = camera.is_public if hasattr(camera, 'is_public') else False
        
        # Handle special cases for username/password
        if 'username' in update_data and update_data['username'] == '':
            update_data['username'] = None
        if 'password' in update_data and update_data['password'] == '':
            update_data['password'] = None  # Convert empty string to None for database
        elif 'password' in update_data and update_data['password'] is None:
            update_data['password'] = ''  # Keep as empty string if explicitly set to None
        
        # Test validation without saving
        serializer = CameraSerializer(camera, data=update_data, partial=True, context={'request': request})
        
        if serializer.is_valid():
            return {
                "valid": True,
                "message": "Payload is valid and ready for update",
                "camera_id": str(camera_id),
                "fields_to_update": list(update_data.keys()),
                "validation_data": update_data
            }
        else:
            return {
                "valid": False,
                "message": "Payload validation failed",
                "camera_id": str(camera_id),
                "errors": serializer.errors,
                "error_summary": format_serializer_errors(serializer.errors)
            }
            
    except Exception as e:
        return {
            "valid": False,
            "message": f"Validation error: {str(e)}",
            "camera_id": str(camera_id),
            "error": str(e)
        }


@router.put("/cameras/{camera_id}/", response=CameraUpdateResponseSchema, auth=cctv_jwt_auth,
            summary="Update Camera",
            description="""
            Update camera configuration and settings (Admin/Superadmin only).
            
            **Update Payload Examples:**
            
            **Update Basic Info:**
            ```json
            {
              "name": "Updated Camera Name",
              "description": "Updated description",
              "location": "New Location"
            }
            ```
            
            **Update Connection Settings:**
            ```json
            {
              "ip_address": "192.168.1.200",
              "port": 8554,
              "username": "newuser",
              "password": "newpass",
              "rtsp_url": "rtsp://newuser:newpass@192.168.1.200:8554/stream1",
              "rtsp_path": "/live/0/MAIN"
            }
            ```
            
            **Update Recording Settings:**
            ```json
            {
              "auto_record": true,
              "record_quality": "high",
              "max_recording_hours": 72,
              "is_public": true
            }
            ```
            
            **Update Status:**
            ```json
            {
              "status": "maintenance"
            }
            ```
            """)
def update_camera(request, camera_id: uuid.UUID, camera_data: CameraUpdateSchema):
    """Update a camera (Admin/Superadmin only)"""
    from .serializers import CameraSerializer
    from .streaming import test_camera_connection
    
    current_user = request.auth
    if not current_user:
        raise HttpError(401, "Authentication required")
    
    if not check_cctv_access(current_user, 'update'):
        raise HttpError(403, "Camera update denied. Admin role or higher required.")
    
    camera = get_object_or_404(Camera, id=camera_id)
    
    if not check_camera_access(current_user, camera):
        raise HttpError(403, "Access denied to this camera")
    
    try:
        # Convert Ninja schema to dictionary for Django serializer
        update_data = camera_data.dict(exclude_unset=True)
        
        # Filter out fields that are not part of the Camera model
        model_fields = {
            'name', 'description', 'ip_address', 'port', 'username', 'password',
            'rtsp_url', 'rtsp_url_sub', 'rtsp_path', 'camera_type', 'status',
            'location', 'auto_record', 'record_quality', 'max_recording_hours', 'is_public'
        }
        
        # Remove non-model fields
        update_data = {k: v for k, v in update_data.items() if k in model_fields}
        
        # Set default values for missing fields to ensure model compatibility
        if 'max_recording_hours' not in update_data:
            update_data['max_recording_hours'] = camera.max_recording_hours or 24
        if 'is_public' not in update_data:
            update_data['is_public'] = camera.is_public if hasattr(camera, 'is_public') else False
        
        # Handle special cases for username/password
        if 'username' in update_data and update_data['username'] == '':
            update_data['username'] = None
        if 'password' in update_data and update_data['password'] == '':
            update_data['password'] = None
        
        # Normalize localhost to valid IP
        if update_data.get('ip_address') == 'localhost':
            update_data['ip_address'] = '127.0.0.1'
        
        # Test connection if RTSP URL is being updated
        if 'rtsp_url' in update_data:
            success, message = test_camera_connection(update_data['rtsp_url'])
            if not success:
                raise HttpError(400, f'Camera connection test failed: {message}')
        
        # If rtsp_path is not provided but rtsp_url is being updated, extract path from URL
        if not update_data.get('rtsp_path') and update_data.get('rtsp_url'):
            from urllib.parse import urlparse
            try:
                parsed = urlparse(update_data['rtsp_url'])
                if parsed.path:
                    update_data['rtsp_path'] = parsed.path
            except Exception:
                pass  # If parsing fails, continue without path
        
        # Update camera using serializer
        serializer = CameraSerializer(camera, data=update_data, partial=True, context={'request': request})
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Attempting to update camera {camera_id} with data: {update_data}")
        
        if serializer.is_valid():
            # Save the updated camera
            updated_camera = serializer.save()
            logger.info(f"Camera {camera_id} updated successfully")
            
            # Return success response with updated camera info
            return {
                "message": "Camera updated successfully",
                "camera_id": str(updated_camera.id),
                "updated_fields": list(update_data.keys()),
                "camera": {
                    "id": str(updated_camera.id),
                    "name": updated_camera.name,
                    "description": updated_camera.description,
                    "ip_address": updated_camera.ip_address,
                    "port": updated_camera.port,
                    "username": updated_camera.username,
                    "rtsp_url": updated_camera.rtsp_url,
                    "rtsp_url_sub": updated_camera.rtsp_url_sub,
                    "rtsp_path": updated_camera.rtsp_path,
                    "camera_type": updated_camera.camera_type,
                    "status": updated_camera.status,
                    "location": updated_camera.location,
                    "auto_record": updated_camera.auto_record,
                    "record_quality": updated_camera.record_quality,
                    "max_recording_hours": updated_camera.max_recording_hours,
                    "is_public": updated_camera.is_public,
                    "is_online": updated_camera.is_online,
                    "updated_at": updated_camera.updated_at.isoformat()
                }
            }
        else:
            # Enhanced error logging for debugging
            logger.error(f"Camera update validation failed for camera {camera_id}: {serializer.errors}")
            logger.error(f"Update data: {update_data}")
            logger.error(f"Validation errors: {serializer.errors}")
            
            # Return detailed validation errors
            error_details = format_serializer_errors(serializer.errors)
            raise HttpError(400, f"Validation failed: {error_details}")
            
    except HttpError:
        # Re-raise HttpError as-is
        raise
    except Exception as e:
        # Handle other exceptions
        raise HttpError(500, f"Internal server error: {str(e)}")


@router.delete("/cameras/{camera_id}/", response=CameraDeleteResponseSchema, auth=cctv_jwt_auth,
               summary="Delete Camera",
               description="Permanently delete a camera and all associated data (Admin/Superadmin only)")
def delete_camera(request, camera_id: uuid.UUID):
    """Delete a camera (Admin/Superadmin only)"""
    from django.utils import timezone
    
    current_user = request.auth
    if not current_user:
        raise HttpError(401, "Authentication required")
    
    if not check_cctv_access(current_user, 'delete'):
        raise HttpError(403, "Camera deletion denied. Admin role or higher required.")
    
    camera = get_object_or_404(Camera, id=camera_id)
    
    if not check_camera_access(current_user, camera):
        raise HttpError(403, "Access denied to this camera")
    
    try:
        # Store camera info before deletion
        camera_name = camera.name
        camera_id_str = str(camera.id)
        
        # Delete the camera
        camera.delete()
        
        return {
            "message": f"Camera '{camera_name}' deleted successfully",
            "camera_id": camera_id_str,
            "deleted_at": timezone.now().isoformat()
        }
        
    except Exception as e:
        raise HttpError(500, f"Failed to delete camera: {str(e)}")


# Live Streaming endpoints
@router.get("/cameras/stream/status/", 
            summary="Stream System Status",
            description="Get the current status of the streaming system without starting any streams",
            tags=["Live Streaming"],
            response=StreamResponseSchema)
def stream_system_status(request):
    """Get streaming system status without starting streams"""
    return {
        "message": "Streaming system is operational",
        "camera_id": "system",
        "quality": "status",
        "content_type": "application/json"
    }

@router.get("/cameras/stream/test/", 
            summary="Stream Test Endpoint",
            description="Test endpoint to verify streaming system without starting actual streams",
            tags=["Live Streaming"])
def stream_test(request):
    """Test endpoint for streaming system"""
    return {
        "message": "Streaming system test successful",
        "timestamp": timezone.now().isoformat(),
        "status": "ready",
        "note": "This endpoint tests the API without starting actual video streams"
    }

@router.get("/cameras/{camera_id}/stream/", 
            summary="Live Video Stream (No Auth Required)",
            description="Get live MJPEG video stream from camera. No authentication required. Returns a multipart HTTP stream that can be displayed in HTML img tags or video players.",
            tags=["Live Streaming"],
            deprecated=False)

def camera_live_stream(request, camera_id: uuid.UUID, quality: str = "main"):
    """Stream live video from camera - No authentication required"""
    from django.http import StreamingHttpResponse, HttpResponse
    from django.shortcuts import get_object_or_404
    from .models import Camera
    
    # Handle CORS preflight requests
    if request.method == 'OPTIONS':
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        response['Access-Control-Max-Age'] = '86400'  # 24 hours
        return response
    
    # Import streaming modules only when actually streaming (not during schema generation)
    try:
        from .streaming import generate_frames, stream_manager
    except ImportError:
        return HttpResponse('Streaming module not available', status=503)
    
    try:
        camera = get_object_or_404(Camera, id=camera_id)
        
        # Check if camera is accessible (allow inactive cameras to be activated)
        if camera.status == 'error':
            return HttpResponse(f'Camera {camera.name} has an error status and cannot stream', status=503)
        
        # Check if camera has valid RTSP URL
        if not camera.rtsp_url:
            return HttpResponse(f'Camera {camera.name} has no valid RTSP URL configured', status=400)
        
        # Auto-activate camera if it's inactive (but not in error state)
        if camera.status == 'inactive':
            camera.set_status('active')
            camera.is_online = True
            camera.is_streaming = False  # Will be set to True when stream actually starts
            camera.save(update_fields=['status', 'is_online', 'is_streaming'])
            logger.info(f"Auto-activated camera {camera.name} for streaming - set is_online=True, is_streaming=False")
        
        # Validate quality parameter
        if quality not in ['main', 'sub']:
            quality = 'main'
        
        if quality == 'sub' and not camera.rtsp_url_sub:
            quality = 'main'  # Fallback to main if sub not available
        
        # Check if this is a schema generation request (prevent hanging)
        if hasattr(request, '_ninja_schema_generation'):
            return HttpResponse('Schema generation - streaming not available', status=503)
        
        # Generate streaming response with timeout protection
        try:
            # Test camera connection before starting stream
            from .opencv_config import test_camera_connection_robust
            stream_url = camera.get_stream_url(quality)
            connection_ok, connection_msg = test_camera_connection_robust(stream_url, max_attempts=2)
            
            if not connection_ok:
                logger.warning(f"Camera connection test failed: {connection_msg}")
                return HttpResponse(f'Camera connection failed: {connection_msg}', status=503)
            
            response = StreamingHttpResponse(
                generate_frames(camera, quality),
                content_type='multipart/x-mixed-replace; boundary=frame'
            )
            
            # Add headers to prevent caching and enable CORS
            response['Cache-Control'] = 'no-cache, no-store, max-age=0, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = 'Thu, 01 Jan 1970 00:00:00 GMT'
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type'
            response['Access-Control-Max-Age'] = '86400'  # 24 hours
            response['X-Camera-Name'] = camera.name
            response['X-Stream-Quality'] = quality
            
        except Exception as stream_error:
            logger.error(f"Error creating streaming response: {str(stream_error)}")
            return HttpResponse(f'Stream creation error: {str(stream_error)}', status=503)
        
        return response
        
    except Camera.DoesNotExist:
        return HttpResponse('Camera not found', status=404)
    except Exception as e:
        logger.error(f"Streaming error for camera {camera_id}: {str(e)}")
        return HttpResponse(f'Streaming Error: {str(e)}', status=500)


@router.get("/cameras/{camera_id}/stream/info/", response=StreamInfoSchema,
            summary="Stream Information", auth=cctv_jwt_auth,
            description="Get information about camera stream capabilities and current status")
def camera_stream_info(request, camera_id: uuid.UUID):
    """Get camera stream information"""
    camera = get_object_or_404(Camera, id=camera_id)
    
    # Check if camera is currently streaming
    from .streaming import stream_manager
    is_streaming = any(info['camera'].id == camera_id for info in stream_manager.active_streams.values())
    
    return {
        "camera_id": str(camera.id),
        "camera_name": camera.name,
        "status": camera.status,
        "is_online": camera.is_online,
        "is_streaming": is_streaming,
        "stream_urls": {
            "main": f"/v0/api/cctv/cameras/{camera.id}/stream/?quality=main",
            "sub": f"/v0/api/cctv/cameras/{camera.id}/stream/?quality=sub" if camera.rtsp_url_sub else None
        },
        "supported_qualities": ["main"] + (["sub"] if camera.rtsp_url_sub else []),
        "rtsp_info": {
            "main_url": camera.rtsp_url,
            "sub_url": camera.rtsp_url_sub,
            "ip_address": camera.ip_address,
            "port": camera.port
        }
    }


@router.get("/cameras/{camera_id}/stream/thumbnail/", auth=cctv_jwt_auth,
            summary="Camera Thumbnail",
            description="Get a single JPEG thumbnail from camera for dashboard preview")
def camera_thumbnail(request, camera_id: uuid.UUID, quality: str = "main"):
    """Get a single thumbnail frame from camera"""
    from django.http import HttpResponse
    from .streaming import stream_manager
    import cv2
    
    camera = get_object_or_404(Camera, id=camera_id)
    
    try:
        # Get a single frame
        frame = stream_manager.get_frame(camera.id, quality)
        
        if frame is not None:
            # Encode as JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ret:
                response = HttpResponse(buffer.tobytes(), content_type='image/jpeg')
                response['Cache-Control'] = 'no-cache, no-store, max-age=0, must-revalidate'
                return response
        
        # Return a placeholder if no frame available
        return HttpResponse(status=204)  # No content
        
    except Exception as e:
        logger.error(f"Error getting thumbnail for camera {camera.name}: {str(e)}")
        return HttpResponse(status=500)


@router.get("/cameras/{camera_id}/stream/snapshot/", auth=cctv_jwt_auth,
            summary="Camera Snapshot",
            description="Capture and save a snapshot from camera")
def camera_snapshot(request, camera_id: uuid.UUID, quality: str = "main"):
    """Capture and save a snapshot from camera"""
    from django.http import JsonResponse
    from .streaming import stream_manager
    import cv2
    import os
    from django.conf import settings
    from django.utils import timezone
    
    camera = get_object_or_404(Camera, id=camera_id)
    
    try:
        # Get a single frame
        frame = stream_manager.get_frame(camera.id, quality)
        
        if frame is not None:
            # Create snapshots directory
            snapshots_dir = os.path.join(settings.MEDIA_ROOT, 'snapshots', str(camera.id))
            os.makedirs(snapshots_dir, exist_ok=True)
            
            # Generate filename
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            filename = f"snapshot_{timestamp}.jpg"
            file_path = os.path.join(snapshots_dir, filename)
            
            # Save snapshot
            ret = cv2.imwrite(file_path, frame)
            
            if ret:
                # Return success with file info
                relative_path = os.path.join('snapshots', str(camera.id), filename)
                return JsonResponse({
                    "success": True,
                    "message": "Snapshot captured successfully",
                    "snapshot": {
                        "filename": filename,
                        "file_path": relative_path,
                        "full_url": f"{request.build_absolute_uri('/')[:-1]}{settings.MEDIA_URL}{relative_path}",
                        "timestamp": timezone.now().isoformat(),
                        "camera_name": camera.name
                    }
                })
            else:
                return JsonResponse({
                    "success": False,
                    "message": "Failed to save snapshot"
                }, status=500)
        else:
            return JsonResponse({
                "success": False,
                "message": "No frame available from camera"
            }, status=400)
        
    except Exception as e:
        logger.error(f"Error capturing snapshot for camera {camera.name}: {str(e)}")
        return JsonResponse({
            "success": False,
            "message": f"Error capturing snapshot: {str(e)}"
        }, status=500)


@router.get("/streams/", response=StreamSessionListResponseSchema, 
            summary="List Stream Sessions", auth=cctv_jwt_auth,
            description="Get a list of all live stream sessions (may be empty if anonymous streaming is used)")
def list_stream_sessions(request):
    """List all live stream sessions"""
    from .serializers import LiveStreamSerializer
    from .streaming import stream_manager
    
    # Note: Will be empty if anonymous streaming is used
    queryset = LiveStream.objects.all().order_by('-start_time')
    
    # Format data according to StreamSessionItemSchema
    streams_data = []
    for stream in queryset:
        # Try to get quality from active streams if available
        quality = "main"  # Default quality
        if stream.is_active:
            # Check if there's an active stream for this camera
            for stream_key, stream_info in stream_manager.active_streams.items():
                if str(stream_info['camera'].id) == str(stream.camera.id):
                    quality = stream_info['quality']
                    break
        
        stream_data = {
            "id": str(stream.id),
            "camera": str(stream.camera.id),  # Convert UUID to string
            "camera_name": stream.camera.name,
            "user": str(stream.user.id) if stream.user else None,  # Convert UUID to string
            "username": stream.user.username if stream.user else None,
            "quality": quality,
            "start_time": stream.start_time.isoformat(),
            "end_time": stream.end_time.isoformat() if stream.end_time else None,
            "duration_seconds": LiveStreamSerializer(stream).data.get('duration_seconds'),
            "is_active": stream.is_active
        }
        streams_data.append(stream_data)
    
    return {
        "total_streams": len(streams_data),
        "active_streams": sum(1 for stream in streams_data if stream.get('is_active', False)),
        "streams": streams_data
    }


@router.get("/streams/active/", response=ActiveStreamsResponseSchema,
            summary="Active Streams", auth=cctv_jwt_auth, 
            description="Get information about currently active streaming sessions from the streaming manager (real-time)")
def active_streams(request):
    """Get all currently active streams"""
    from .streaming import stream_manager
    from django.utils import timezone
    
    active_streams_info = []
    
    for stream_key, stream_info in stream_manager.active_streams.items():
        camera = stream_info['camera']
        active_streams_info.append({
            "stream_key": stream_key,
            "camera_id": str(camera.id),
            "camera_name": camera.name,
            "quality": stream_info['quality'],
            "viewers": stream_info['viewers'],
            "last_update": stream_info['last_update'].isoformat() if stream_info['last_update'] else None,
            "uptime_seconds": int((timezone.now() - stream_info['last_update']).total_seconds()) if stream_info['last_update'] else 0
        })
    
    return {
        "total_active_streams": len(active_streams_info),
        "streams": active_streams_info
    }


# Live Stream Activation endpoints
@router.post("/cameras/{camera_id}/activate_stream/", 
            summary="Activate Live Stream",
            description="Start a live stream for a specific camera. This endpoint activates the streaming manager and creates a LiveStream session record.",
            auth=cctv_jwt_auth)
def activate_live_stream(request, camera_id: uuid.UUID, quality: str = "main"):
    """Activate a live stream for a camera"""
    from .models import Camera, LiveStream
    from .streaming import stream_manager
    from django.utils import timezone
    import uuid
    
    try:
        # Get the camera
        camera = get_object_or_404(Camera, id=camera_id)
        
        # Debug logging
        logger.info(f"Attempting to activate stream for camera: {camera.name} (ID: {camera_id})")
        logger.info(f"Camera status: {camera.status}, is_online: {camera.is_online}, last_seen: {camera.last_seen}")
        logger.info(f"Request user: {request.user}, User type: {type(request.user)}")
        
        # Verify we have a valid authenticated user
        if not request.user or request.user.is_anonymous:
            raise HttpError(401, "Authentication required - valid user not found")
        
        # Check if camera is accessible (don't require it to be "online" since we're about to activate it)
        if camera.status == 'error':
            raise HttpError(400, f"Camera {camera.name} has an error status and cannot be activated")
        
        # Mark camera as online since we're about to activate it
        camera.mark_as_online()
        
        # Check if there's already an active stream for this camera
        existing_stream = LiveStream.objects.filter(
            camera=camera,
            is_active=True
        ).first()
        
        if existing_stream:
            raise HttpError(400, f"Live stream is already active for camera {camera.name}")
        
        # Validate quality parameter
        if quality not in ['main', 'sub']:
            quality = 'main'
        
        # Check if sub stream is available
        if quality == 'sub' and not camera.rtsp_url_sub:
            raise HttpError(400, f"Sub stream not available for camera {camera.name}")
        
        # Start the stream using streaming manager
        try:
            stream_info = stream_manager.start_stream(camera, quality)
            if not stream_info:
                raise HttpError(500, "Failed to start stream")
        except Exception as e:
            logger.error(f"Error starting stream: {str(e)}")
            raise HttpError(500, f"Stream error: {str(e)}")
        
        # Create LiveStream record
        session_id = str(uuid.uuid4())
        live_stream = LiveStream.objects.create(
            camera=camera,
            user=request.user,
            session_id=session_id,
            client_ip=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            is_active=True
        )
        
        # Update camera status
        camera.set_status('active')
        
        logger.info(f"Live stream activated for camera {camera.name} by user {request.user.email}")
        
        return {
            "success": True,
            "message": "Live stream activated successfully",
            "stream_info": {
                "session_id": session_id,
                "camera_id": str(camera.id),
                "camera_name": camera.name,
                "quality": quality,
                "stream_url": f"/v0/api/cctv/cameras/{camera.id}/stream/?quality={quality}",
                "rtsp_url": camera.get_stream_url(quality),
                "start_time": live_stream.start_time.isoformat(),
                "camera_status": camera.status
            }
        }
        
    except HttpError:
        raise
    except Exception as e:
        logger.error(f"Error activating live stream: {str(e)}")
        raise HttpError(500, f"Internal server error: {str(e)}")


@router.post("/cameras/{camera_id}/deactivate_stream/", 
            summary="Deactivate Live Stream",
            description="Stop a live stream for a specific camera. This endpoint stops the streaming manager and updates the LiveStream session record.",
            auth=cctv_jwt_auth)
def deactivate_live_stream(request, camera_id: uuid.UUID):
    """Deactivate a live stream for a camera"""
    from .models import Camera, LiveStream
    from .streaming import stream_manager
    from django.utils import timezone
    
    try:
        # Get the camera
        camera = get_object_or_404(Camera, id=camera_id)
        
        # Verify we have a valid authenticated user
        if not request.user or request.user.is_anonymous:
            raise HttpError(401, "Authentication required - valid user not found")
        
        # Find active stream for this camera
        active_stream = LiveStream.objects.filter(
            camera=camera,
            is_active=True
        ).first()
        
        if not active_stream:
            raise HttpError(400, f"No active stream found for camera {camera.name}")
        
        # Stop the stream using streaming manager
        try:
            stream_manager.stop_stream(camera.id, 'main')  # Stop main stream
            if camera.rtsp_url_sub:
                stream_manager.stop_stream(camera.id, 'sub')  # Stop sub stream if exists
        except Exception as e:
            logger.warning(f"Error stopping stream: {str(e)}")
            # Continue with cleanup even if stream manager fails
        
        # Update LiveStream record
        active_stream.is_active = False
        active_stream.end_time = timezone.now()
        active_stream.save()
        
        # Update camera status if no other active streams
        other_active_streams = LiveStream.objects.filter(
            camera=camera,
            is_active=True
        ).exclude(id=active_stream.id).count()
        
        if other_active_streams == 0:
            camera.set_status('inactive')
        
        logger.info(f"Live stream deactivated for camera {camera.name} by user {request.user.email}")
        
        return {
            "success": True,
            "message": "Live stream deactivated successfully",
            "stream_info": {
                "session_id": active_stream.session_id,
                "camera_id": str(camera.id),
                "camera_name": camera.name,
                "duration_seconds": (active_stream.end_time - active_stream.start_time).total_seconds(),
                "stop_time": active_stream.end_time.isoformat(),
                "camera_status": camera.status
            }
        }
        
    except HttpError:
        raise
    except Exception as e:
        logger.error(f"Error deactivating live stream: {str(e)}")
        raise HttpError(500, f"Internal server error: {str(e)}")


@router.get("/cameras/{camera_id}/stream_status/", 
            summary="Stream Status",
            description="Get the current status of live streaming for a specific camera",
            auth=cctv_jwt_auth)
def get_stream_status(request, camera_id: uuid.UUID):
    """Get the current streaming status for a camera"""
    from .models import Camera, LiveStream
    from .streaming import stream_manager
    
    try:
        # Get the camera
        camera = get_object_or_404(Camera, id=camera_id)
        
        # Verify we have a valid authenticated user
        if not request.user or request.user.is_anonymous:
            raise HttpError(401, "Authentication required - valid user not found")
        
        # Check if camera is currently streaming
        is_streaming = any(info['camera'].id == camera_id for info in stream_manager.active_streams.values())
        
        # Get active stream record
        active_stream = LiveStream.objects.filter(
            camera=camera,
            is_active=True
        ).first()
        
        # Get stream info from streaming manager
        stream_info = None
        if is_streaming:
            for stream_key, info in stream_manager.active_streams.items():
                if info['camera'].id == camera_id:
                    stream_info = {
                        "stream_key": stream_key,
                        "quality": info['quality'],
                        "viewers": info['viewers'],
                        "last_update": info['last_update'].isoformat() if info['last_update'] else None
                    }
                    break
        
        return {
            "camera_id": str(camera.id),
            "camera_name": camera.name,
            "camera_status": camera.status,
            "is_online": camera.is_online,
            "is_streaming": is_streaming,
            "stream_info": stream_info,
            "active_session": {
                "session_id": active_stream.session_id if active_stream else None,
                "start_time": active_stream.start_time.isoformat() if active_stream else None,
                "duration_seconds": (timezone.now() - active_stream.start_time).total_seconds() if active_stream else None,
                "user": active_stream.user.email if active_stream else None
            } if active_stream else None,
            "stream_urls": {
                "main": f"/v0/api/cctv/cameras/{camera.id}/stream/?quality=main",
                "sub": f"/v0/api/cctv/cameras/{camera.id}/stream/?quality=sub" if camera.rtsp_url_sub else None
            },
            "supported_qualities": ["main"] + (["sub"] if camera.rtsp_url_sub else [])
        }
        
    except Exception as e:
        logger.error(f"Error getting stream status: {str(e)}")
        raise HttpError(500, f"Internal server error: {str(e)}")


@router.post("/cameras/{camera_id}/recover_stream/", 
            summary="Recover Stream",
            description="Attempt to recover a failed or unhealthy stream for a camera",
            auth=cctv_jwt_auth)
def recover_camera_stream(request, camera_id: uuid.UUID, quality: str = "main"):
    """Attempt to recover a failed stream for a camera"""
    from .models import Camera
    from .streaming import stream_manager
    
    try:
        # Get the camera
        camera = get_object_or_404(Camera, id=camera_id)
        
        # Verify we have a valid authenticated user
        if not request.user or request.user.is_anonymous:
            raise HttpError(401, "Authentication required - valid user not found")
        
        # Check if user has access to this camera
        if not check_camera_access(request.user, camera):
            raise HttpError(403, "Access denied to this camera")
        
        # Attempt to recover the stream
        logger.info(f"User {request.user.email} requested stream recovery for camera {camera.name}")
        
        recovered_stream = stream_manager.recover_stream(camera_id, quality)
        
        if recovered_stream:
            return {
                "success": True,
                "message": f"Stream recovered successfully for camera {camera.name}",
                "camera_id": str(camera.id),
                "camera_name": camera.name,
                "quality": quality,
                "recovery_time": timezone.now().isoformat()
            }
        else:
            raise HttpError(500, f"Failed to recover stream for camera {camera.name}")
        
    except HttpError:
        raise
    except Exception as e:
        logger.error(f"Error recovering stream for camera {camera_id}: {str(e)}")
        raise HttpError(500, f"Internal server error: {str(e)}")


@router.get("/cameras/{camera_id}/stream_health/", 
            summary="Stream Health",
            description="Get detailed health information about a camera's stream",
            auth=cctv_jwt_auth)
def get_stream_health(request, camera_id: uuid.UUID, quality: str = "main"):
    """Get detailed stream health information for a camera"""
    from .models import Camera
    from .streaming import stream_manager
    
    try:
        # Get the camera
        camera = get_object_or_404(Camera, id=camera_id)
        
        # Verify we have a valid authenticated user
        if not request.user or request.user.is_anonymous:
            raise HttpError(401, "Authentication required - valid user not found")
        
        # Check if user has access to this camera
        if not check_camera_access(request.user, camera):
            raise HttpError(403, "Access denied to this camera")
        
        # Get stream health from streaming manager
        health_info = stream_manager.get_stream_health(camera_id, quality)
        
        # Add camera-specific information
        health_info.update({
            "camera_id": str(camera.id),
            "camera_name": camera.name,
            "camera_status": camera.status,
            "is_online": camera.is_online,
            "last_seen": camera.last_seen.isoformat() if camera.last_seen else None,
            "rtsp_url": camera.get_stream_url(quality),
            "quality": quality
        })
        
        return health_info
        
    except Exception as e:
        logger.error(f"Error getting stream health for camera {camera_id}: {str(e)}")
        raise HttpError(500, f"Internal server error: {str(e)}")


@router.post("/cameras/{camera_id}/test_connection/", 
            summary="Test Camera Connection",
            description="Test the connection to a camera's RTSP stream",
            auth=cctv_jwt_auth)
def test_camera_connection(request, camera_id: uuid.UUID):
    """Test the connection to a camera's RTSP stream"""
    from .models import Camera
    import cv2
    
    try:
        # Get the camera
        camera = get_object_or_404(Camera, id=camera_id)
        
        # Verify we have a valid authenticated user
        if not request.user or request.user.is_anonymous:
            raise HttpError(401, "Authentication required - valid user not found")
        
        # Check if user has access to this camera
        if not check_camera_access(request.user, camera):
            raise HttpError(403, "Access denied to this camera")
        
        # Test RTSP connection using robust method
        rtsp_url = camera.get_stream_url("main")
        
        try:
            # Import OpenCV configuration for robust testing
            from .opencv_config import test_camera_connection_robust
            
            # Test connection with robust method
            connection_ok, connection_msg = test_camera_connection_robust(rtsp_url)
            
            if not connection_ok:
                return {
                    "success": False,
                    "message": f"Cannot connect to RTSP stream: {connection_msg}",
                    "camera_id": str(camera.id),
                    "camera_name": camera.name,
                    "rtsp_url": rtsp_url,
                    "error": connection_msg
                }
            
            # If connection is successful, try to get frame info
            try:
                cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
                ret, frame = cap.read()
                cap.release()
                
                frame_size = f"{frame.shape[1]}x{frame.shape[0]}" if ret and frame is not None else "Unknown"
            except:
                frame_size = "Unknown"
            
            return {
                "success": True,
                "message": f"Successfully connected to camera {camera.name}",
                "camera_id": str(camera.id),
                "camera_name": camera.name,
                "rtsp_url": rtsp_url,
                "frame_size": frame_size
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error testing RTSP connection: {str(e)}",
                "camera_id": str(camera.id),
                "camera_name": camera.name,
                "rtsp_url": rtsp_url,
                "error": str(e)
            }
        
    except Exception as e:
        logger.error(f"Error testing connection for camera {camera_id}: {str(e)}")
        raise HttpError(500, f"Internal server error: {str(e)}")


@router.post("/cameras/{camera_id}/test_recording/", 
            summary="Test Recording",
            description="Test recording functionality for a camera (5-minute test recording)",
            auth=cctv_jwt_auth)
def test_camera_recording(request, camera_id: uuid.UUID):
    """Test recording functionality for a camera"""
    from .models import Camera
    from .streaming import recording_manager
    from datetime import datetime, timedelta
    
    try:
        # Get the camera
        camera = get_object_or_404(Camera, id=camera_id)
        
        # Verify we have a valid authenticated user
        if not request.user or request.user.is_anonymous:
            raise HttpError(401, "Authentication required - valid user not found")
        
        # Check if user has access to this camera
        if not check_camera_access(request.user, camera):
            raise HttpError(403, "Access denied to this camera")
        
        # Check if camera is already recording
        if recording_manager.is_recording(camera.id):
            raise HttpError(400, "Camera is already recording. Stop current recording first.")
        
        # Start a 5-minute test recording
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        recording_name = f"TEST_RECORDING_{camera.name}_{timestamp}"
        
        recording = recording_manager.start_recording(
            camera=camera,
            duration_minutes=5,
            recording_name=recording_name,
            user=request.user
        )
        
        return {
            "success": True,
            "message": "Test recording started successfully",
            "recording_id": str(recording.id),
            "recording_name": recording.name,
            "duration_minutes": 5,
            "estimated_end_time": (datetime.now() + timedelta(minutes=5)).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting test recording for camera {camera_id}: {str(e)}")
        raise HttpError(500, f"Internal server error: {str(e)}")


@router.post("/cameras/{camera_id}/set_online/", 
            summary="Set Camera Online",
            description="Manually set a camera status to online and mark it as available for live streaming",
            auth=cctv_jwt_auth)
def set_camera_online(request, camera_id: uuid.UUID):
    """Manually set a camera status to online for live streaming"""
    from .models import Camera
    from .streaming import stream_manager
    from django.utils import timezone
    
    try:
        # Get the camera
        camera = get_object_or_404(Camera, id=camera_id)
        
        # Verify we have a valid authenticated user
        if not request.user or request.user.is_anonymous:
            raise HttpError(401, "Authentication required - valid user not found")
        
        # Check if user has permission to control cameras
        if not check_cctv_access(request.user, 'control'):
            raise HttpError(403, "Camera control denied. Dev role or higher required.")
        
        # Check if user has access to this camera
        if not check_camera_access(request.user, camera):
            raise HttpError(403, "Access denied to this camera")
        
        # Store previous status for logging
        previous_status = camera.status
        
        # Set camera status to active and mark as online
        camera.set_status('active')
        camera.mark_as_online()
        
        # Try to initialize/start stream to ensure it's ready for viewing
        try:
            # Auto-start streaming for immediate availability
            stream_info = stream_manager.start_stream(camera, 'main')
            stream_started = bool(stream_info)
            logger.info(f"Stream auto-started for camera {camera.name}: {stream_started}")
        except Exception as stream_error:
            logger.warning(f"Failed to auto-start stream for camera {camera.name}: {str(stream_error)}")
            stream_started = False
            # Don't fail the entire operation if streaming fails
        
        # Check if camera is currently streaming
        is_streaming = any(info['camera'].id == camera.id for info in stream_manager.active_streams.values())
        
        logger.info(f"Camera {camera.name} status changed from '{previous_status}' to 'active' by user {request.user.email}")
        
        return {
            "success": True,
            "message": f"Camera '{camera.name}' is now online and ready for live streaming",
            "camera_id": str(camera.id),
            "camera_name": camera.name,
            "previous_status": previous_status,
            "current_status": camera.status,
            "is_online": camera.is_online,
            "is_streaming": is_streaming,
            "last_seen": camera.last_seen.isoformat() if camera.last_seen else None,
            "stream_auto_started": stream_started,
            "stream_urls": {
                "main": f"/v0/api/cctv/cameras/{camera.id}/stream/?quality=main",
                "sub": f"/v0/api/cctv/cameras/{camera.id}/stream/?quality=sub" if camera.rtsp_url_sub else None
            },
            "timestamp": timezone.now().isoformat()
        }
        
    except HttpError:
        raise
    except Exception as e:
        logger.error(f"Error setting camera {camera_id} online: {str(e)}")
        raise HttpError(500, f"Internal server error: {str(e)}")


# Recording endpoints
@router.get("/recordings/", response=RecordingListResponseSchema, auth=cctv_jwt_auth,
            summary="List Recordings",
            description="Get a paginated list of all video recordings accessible to the user")
def list_recordings(request):
    """List all recordings accessible to the user"""
    from .serializers import RecordingSerializer
    
    # Since auth is disabled, return all recordings
    queryset = Recording.objects.all().order_by('-start_time')
    recordings_data = []
    
    for recording in queryset:
        serializer_data = RecordingSerializer(recording).data
        # Convert UUID objects to strings for schema validation
        if 'camera' in serializer_data and serializer_data['camera']:
            serializer_data['camera'] = str(serializer_data['camera'])
        if 'schedule' in serializer_data and serializer_data['schedule']:
            serializer_data['schedule'] = str(serializer_data['schedule'])
        if 'id' in serializer_data:
            serializer_data['id'] = str(serializer_data['id'])
        recordings_data.append(serializer_data)
    
    return {
        "total_recordings": len(recordings_data),
        "completed_recordings": sum(1 for rec in recordings_data if rec.get('status') == 'completed'),
        "failed_recordings": sum(1 for rec in recordings_data if rec.get('status') == 'failed'),
        "recordings": recordings_data
    }


@router.get("/recordings/stats/", response=RecordingStatsResponseSchema,
            summary="Recording Statistics", auth=cctv_jwt_auth,
            description="Get comprehensive statistics about recordings including success rates and storage usage")
def recording_stats(request):
    """Get recording statistics"""
    try:
        # Since auth is disabled, get all recordings directly
        recordings = Recording.objects.all()
        
        total_recordings = recordings.count()
        completed_recordings = recordings.filter(status='completed').count()
        failed_recordings = recordings.filter(status='failed').count()
        recording_recordings = recordings.filter(status='recording').count()
        
        total_size = sum(r.file_size for r in recordings if r.file_size)
        total_duration = sum(
            (r.duration.total_seconds() for r in recordings if r.duration), 
            start=0
        )
        
        success_rate = (completed_recordings / total_recordings * 100) if total_recordings > 0 else 0
        
        return {
            'total_recordings': total_recordings,
            'completed_recordings': completed_recordings,
            'failed_recordings': failed_recordings,
            'active_recordings': recording_recordings,
            'success_rate': round(success_rate, 2),
            'total_size_bytes': total_size,
            'total_size_gb': round(total_size / (1024 * 1024 * 1024), 2) if total_size else 0,
            'total_duration_seconds': total_duration,
            'total_duration_hours': round(total_duration / 3600, 2) if total_duration else 0
        }
        
    except Exception as e:
        raise HttpError(500, str(e))


@router.get("/recordings/gcp-transfers/", response=GCPTransferListResponseSchema, auth=cctv_jwt_auth,
           summary="List GCP Transfer Status",
           description="Get the status of all video transfers to GCP Cloud Storage")
def list_gcp_transfers(request):
    """List all GCP video transfer statuses"""
    from .models import GCPVideoTransfer
    
    # Check if user has permission to view transfers
    if not check_cctv_access(request.user, 'view'):
        raise HttpError(403, "You don't have permission to view GCP transfers")
    
    try:
        transfers = GCPVideoTransfer.objects.select_related('recording', 'recording__camera').all()
        
        # Count transfers by status
        pending_count = transfers.filter(transfer_status='pending').count()
        uploading_count = transfers.filter(transfer_status='uploading').count()
        completed_count = transfers.filter(transfer_status__in=['completed', 'cleanup_pending', 'cleanup_completed']).count()
        failed_count = transfers.filter(transfer_status='failed').count()
        
        # Prepare transfer data
        transfer_data = []
        for transfer in transfers:
            transfer_data.append({
                "transfer_id": str(transfer.id),
                "recording_name": transfer.recording.name,
                "transfer_status": transfer.transfer_status,
                "file_size_mb": round(transfer.file_size_bytes / (1024 * 1024), 2) if transfer.file_size_bytes else 0.0,
                "gcp_storage_path": transfer.gcp_storage_path,
                "gcp_public_url": transfer.gcp_public_url,
                "upload_started_at": transfer.upload_started_at.isoformat() if transfer.upload_started_at else None,
                "upload_completed_at": transfer.upload_completed_at.isoformat() if transfer.upload_completed_at else None,
                "cleanup_scheduled_at": transfer.cleanup_scheduled_at.isoformat() if transfer.cleanup_scheduled_at else None,
                "cleanup_completed_at": transfer.cleanup_completed_at.isoformat() if transfer.cleanup_completed_at else None,
                "error_message": transfer.error_message,
                "retry_count": transfer.retry_count,
            })
        
        return {
            "transfers": transfer_data,
            "total_count": len(transfer_data),
            "pending_count": pending_count,
            "uploading_count": uploading_count,
            "completed_count": completed_count,
            "failed_count": failed_count,
        }
        
    except Exception as e:
        logger.error(f"Error listing GCP transfers: {str(e)}")
        raise HttpError(500, f"Internal server error: {str(e)}")


@router.post("/recordings/transfer-to-gcp/", response=GCPTransferResponseSchema, auth=cctv_jwt_auth,
            summary="Transfer Videos to GCP Cloud Storage",
            description="Initiate transfer of recorded videos from local storage to GCP Cloud Storage. Videos will be automatically deleted from local storage after 24 hours.")
def transfer_recordings_to_gcp_new(request, transfer_request: GCPTransferRequestSchema):
    """
    Transfer recorded videos to GCP Cloud Storage with automatic local cleanup after 24 hours
    
    This endpoint will:
    1. Find all local recordings (or specific ones if IDs provided)
    2. Initiate background upload to GCP Cloud Storage
    3. Update the recording storage_type to 'gcp'
    4. Create GCPVideoTransfer records to track the process
    5. Schedule automatic cleanup of local files after 24 hours
    """
    from .models import Recording, GCPVideoTransfer
    from .storage_service import storage_service
    from django.db import transaction
    import os
    
    # Check if user has permission to transfer recordings
    if not check_cctv_access(request.user, 'manage'):
        raise HttpError(403, "You don't have permission to transfer recordings to GCP")
    
    # Check if GCP is configured
    if not storage_service.use_gcp:
        raise HttpError(400, "GCP Storage is not configured. Please contact administrator.")
    
    try:
        with transaction.atomic():
            # Get recordings to transfer
            recordings_query = Recording.objects.filter(
                storage_type='local',
                file_path__isnull=False
            ).exclude(file_path='').exclude(file_path__endswith='.tmp')
            
            # Filter by specific recording IDs if provided
            if transfer_request.recording_ids:
                recordings_query = recordings_query.filter(
                    id__in=transfer_request.recording_ids
                )
            
            recordings = list(recordings_query)
            total_recordings = len(recordings)
            
            if total_recordings == 0:
                return {
                    "message": "No recordings found for transfer",
                    "total_recordings": 0,
                    "initiated_transfers": 0,
                    "already_transferred": 0,
                    "failed_initiations": 0,
                    "transfer_ids": []
                }
            
            initiated_transfers = 0
            already_transferred = 0
            failed_initiations = 0
            transfer_ids = []
            
            for recording in recordings:
                try:
                    # Check if transfer already exists
                    existing_transfer, created = GCPVideoTransfer.objects.get_or_create(
                        recording=recording,
                        defaults={
                            'original_local_path': recording.file_path,
                            'initiated_by': request.user,
                            'file_size_bytes': recording.file_size or 0,
                        }
                    )
                    
                    if not created:
                        if existing_transfer.transfer_status in ['completed', 'uploading', 'cleanup_pending', 'cleanup_completed']:
                            already_transferred += 1
                            continue
                        elif existing_transfer.transfer_status == 'failed' and existing_transfer.retry_count >= 3:
                            # Skip recordings that have failed too many times
                            failed_initiations += 1
                            continue
                    
                    # Verify local file exists
                    local_file_path = os.path.join(settings.MEDIA_ROOT, recording.file_path)
                    if not os.path.exists(local_file_path):
                        existing_transfer.mark_upload_failed(f"Local file not found: {local_file_path}")
                        failed_initiations += 1
                        continue
                    
                    # Update file size if not set
                    if existing_transfer.file_size_bytes == 0:
                        existing_transfer.file_size_bytes = os.path.getsize(local_file_path)
                        existing_transfer.save(update_fields=['file_size_bytes'])
                    
                    # Start the transfer process in background
                    from threading import Thread
                    thread = Thread(target=_perform_gcp_upload_new, args=(existing_transfer,))
                    thread.daemon = True
                    thread.start()
                    
                    transfer_ids.append(str(existing_transfer.id))
                    initiated_transfers += 1
                    
                except Exception as e:
                    logger.error(f"Failed to initiate transfer for recording {recording.id}: {str(e)}")
                    failed_initiations += 1
            
            return {
                "message": f"Successfully initiated {initiated_transfers} video transfers to GCP Cloud Storage",
                "total_recordings": total_recordings,
                "initiated_transfers": initiated_transfers,
                "already_transferred": already_transferred,
                "failed_initiations": failed_initiations,
                "transfer_ids": transfer_ids
            }
            
    except Exception as e:
        logger.error(f"Error initiating GCP transfers: {str(e)}")
        raise HttpError(500, f"Internal server error: {str(e)}")


def _perform_gcp_upload_new(gcp_transfer):
    """Background function to perform the actual GCP upload"""
    from .storage_service import storage_service
    from django.conf import settings
    import os
    
    try:
        # Mark upload as started
        gcp_transfer.mark_upload_started()
        
        recording = gcp_transfer.recording
        local_file_path = os.path.join(settings.MEDIA_ROOT, recording.file_path)
        
        # Generate GCP storage path
        gcp_path = f"recordings/{recording.camera.id}/{recording.id}/{os.path.basename(recording.file_path)}"
        
        # Upload to GCP
        success = storage_service.upload_file(
            file_path=local_file_path,
            destination_path=gcp_path,
            content_type="video/mp4",
            timeout=600  # 10 minutes timeout for large files
        )
        
        if success:
            # Get public URL
            public_url = storage_service.get_file_url(gcp_path)
            
            # Mark upload as completed
            gcp_transfer.mark_upload_completed(gcp_path, public_url)
            
            # Update recording to point to GCP
            recording.storage_type = 'gcp'
            recording.file_path = gcp_path
            recording.save(update_fields=['storage_type', 'file_path'])
            
            logger.info(f"Successfully uploaded recording {recording.id} to GCP: {gcp_path}")
        else:
            gcp_transfer.mark_upload_failed("Failed to upload file to GCP storage")
            
    except Exception as e:
        error_msg = f"Upload failed: {str(e)}"
        gcp_transfer.mark_upload_failed(error_msg)
        logger.error(f"GCP upload failed for transfer {gcp_transfer.id}: {error_msg}")


@router.get("/recordings/{recording_id}/", response=RecordingDetailResponseSchema, auth=cctv_jwt_auth,
            summary="Get Recording Details",
            description="Retrieve detailed information about a specific video recording")
def get_recording(request, recording_id: uuid.UUID):
    """Get a specific recording"""
    from .serializers import RecordingSerializer
    
    # Since auth is disabled, get recording directly from DB
    recording = get_object_or_404(Recording, id=recording_id)
    return RecordingSerializer(recording).data


# Schedule endpoints
@router.get("/schedules/", response=ScheduleListResponseSchema,
            summary="List Recording Schedules", auth=cctv_jwt_auth,
            description="Get a paginated list of all recording schedules with their current status")
def list_schedules(request):
    """List all recording schedules accessible to the user"""
    from .serializers import RecordingScheduleSerializer
    
    # Since auth is disabled, return all schedules
    queryset = RecordingSchedule.objects.all().order_by('-created_at')
    schedules_data = [RecordingScheduleSerializer(schedule).data for schedule in queryset]
    
    return {
        "total_schedules": len(schedules_data),
        "active_schedules": sum(1 for sched in schedules_data if sched.get('is_active', False)),
        "schedules": schedules_data
    }


@router.post("/schedules/", 
             summary="Create Recording Schedule", auth=cctv_jwt_auth,
             description="Create a new automated recording schedule for a camera")
def create_schedule(request, schedule_data: ScheduleCreateSchema):
    """Create a new recording schedule"""
    from .serializers import RecordingScheduleSerializer
    
    # Handle user for schedule creation (use superuser if no auth)
    # Get superuser for schedule creation
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        raise HttpError(500, "No admin user found for schedule creation")
    
    # Convert schema to dict and set created_by in the data
    schedule_data_dict = schedule_data.dict()
    schedule_data_dict['created_by'] = user.id if user else None
    
    serializer = RecordingScheduleSerializer(data=schedule_data_dict, context={'request': request})
    if serializer.is_valid():
        schedule = serializer.save()
        # Return only the fields expected by ScheduleResponseSchema
        response_data = {
            "message": "Schedule created successfully", 
            "schedule_id": str(schedule.id)
        }
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Creating schedule response: {response_data}")
        # Ensure we return a simple dict, not serializer data
        return dict(response_data)
    else:
        # Debug logging for validation errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Schedule validation failed: {serializer.errors}")
        raise HttpError(400, format_serializer_errors(serializer.errors))


@router.get("/schedules/{schedule_id}/", response=ScheduleDetailResponseSchema,
            summary="Get Schedule Details", auth=cctv_jwt_auth,
            description="Retrieve detailed information about a specific recording schedule")
def get_schedule(request, schedule_id: uuid.UUID):
    """Get a specific recording schedule"""
    from .serializers import RecordingScheduleSerializer
    
    # Since auth is disabled, get schedule directly from DB
    schedule = get_object_or_404(RecordingSchedule, id=schedule_id)
    return RecordingScheduleSerializer(schedule).data


@router.put("/schedules/{schedule_id}/", response=ScheduleUpdateResponseSchema,
            summary="Update Recording Schedule", auth=cctv_jwt_auth,
            description="Update an existing recording schedule configuration")
def update_schedule(request, schedule_id: uuid.UUID, schedule_data: ScheduleUpdateSchema):
    """Update a recording schedule"""
    from .serializers import RecordingScheduleSerializer
    
    # Since auth is disabled, get schedule directly from DB
    schedule = get_object_or_404(RecordingSchedule, id=schedule_id)
    schedule_data_dict = schedule_data.dict(exclude_unset=True)
    serializer = RecordingScheduleSerializer(schedule, data=schedule_data_dict, partial=True, context={'request': request})
    if serializer.is_valid():
        # Save the updated schedule
        updated_schedule = serializer.save()
        
        # Return success response with updated schedule info
        return {
            "message": "Schedule updated successfully",
            "schedule_id": str(updated_schedule.id),
            "updated_fields": list(schedule_data_dict.keys()),
            "schedule": {
                "id": str(updated_schedule.id),
                "name": updated_schedule.name,
                "camera": str(updated_schedule.camera.id),
                "camera_name": updated_schedule.camera.name,
                "schedule_type": updated_schedule.schedule_type,
                "start_time": updated_schedule.start_time.isoformat(),
                "end_time": updated_schedule.end_time.isoformat(),
                "is_active": updated_schedule.is_active,
                "updated_at": updated_schedule.updated_at.isoformat()
            }
        }
    else:
        raise HttpError(400, format_serializer_errors(serializer.errors))


@router.delete("/schedules/{schedule_id}/", response=ScheduleDeleteResponseSchema,
               summary="Delete Recording Schedule", auth=cctv_jwt_auth,
               description="Permanently delete a recording schedule")
def delete_schedule(request, schedule_id: uuid.UUID):
    """Delete a recording schedule"""
    from django.utils import timezone
    
    # Since auth is disabled, get schedule directly from DB
    schedule = get_object_or_404(RecordingSchedule, id=schedule_id)
    
    try:
        # Store schedule info before deletion
        schedule_name = schedule.name
        schedule_id_str = str(schedule.id)
        
        # Delete the schedule
        schedule.delete()
        
        return {
            "message": f"Schedule '{schedule_name}' deleted successfully",
            "schedule_id": schedule_id_str,
            "schedule_name": schedule_name,
            "deleted_at": timezone.now().isoformat()
        }
        
    except Exception as e:
        raise HttpError(500, f"Failed to delete schedule: {str(e)}")


@router.post("/schedules/{schedule_id}/activate/", response=ScheduleActivationResponseSchema,
             summary="Activate Schedule", auth=cctv_jwt_auth,
             description="Enable a recording schedule to start automated recordings")
def activate_schedule(request, schedule_id: uuid.UUID):
    """Activate a recording schedule"""
    import logging
    logger = logging.getLogger(__name__)
    
    schedule = get_object_or_404(RecordingSchedule, id=schedule_id)
    schedule.is_active = True
    schedule.save()
    
    # Log activation with schedule ID and name
    logger.info(f"Schedule activated via API - ID: {schedule.id}, Name: '{schedule.name}', Camera: {schedule.camera.name}")
    
    # Add to scheduler if available
    try:
        from .scheduler import recording_scheduler
        recording_scheduler.add_schedule(schedule)
    except ImportError:
        pass  # Scheduler not available
    except AttributeError:
        pass  # Method doesn't exist
    
    return {
        "message": f"Schedule '{schedule.name}' activated successfully",
        "schedule_id": str(schedule.id),
        "schedule_name": schedule.name,
        "camera_name": schedule.camera.name,
        "action": "activate",
        "timestamp": timezone.now().isoformat()
    }


@router.post("/schedules/{schedule_id}/deactivate/", response=ScheduleActivationResponseSchema,
             summary="Deactivate Schedule", auth=cctv_jwt_auth, 
             description="Disable a recording schedule to stop automated recordings")
def deactivate_schedule(request, schedule_id: uuid.UUID):
    """Deactivate a recording schedule"""
    import logging
    logger = logging.getLogger(__name__)
    
    schedule = get_object_or_404(RecordingSchedule, id=schedule_id)
    schedule.is_active = False
    schedule.save()
    
    # Log deactivation with schedule ID and name
    logger.info(f"Schedule deactivated via API - ID: {schedule.id}, Name: '{schedule.name}', Camera: {schedule.camera.name}")
    
    # Remove from scheduler if available
    try:
        from .scheduler import recording_scheduler
        recording_scheduler.remove_schedule(schedule.id)
    except ImportError:
        pass  # Scheduler not available
    except AttributeError:
        pass  # Method doesn't exist
    
    return {
        "message": f"Schedule '{schedule.name}' deactivated successfully",
        "schedule_id": str(schedule.id),
        "schedule_name": schedule.name,
        "camera_name": schedule.camera.name,
        "action": "deactivate",
        "timestamp": timezone.now().isoformat()
    }


@router.get("/schedules/{schedule_id}/status/", 
            summary="Schedule Status",
            description="Get the current status and next run time of a recording schedule",
            auth=cctv_jwt_auth)
def get_schedule_status(request, schedule_id: uuid.UUID):
    """Get the current status and next run time of a recording schedule"""
    from .models import RecordingSchedule
    from .scheduler import recording_scheduler
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    try:
        # Get the schedule
        schedule = get_object_or_404(RecordingSchedule, id=schedule_id)
        
        # Verify we have a valid authenticated user
        if not request.user or request.user.is_anonymous:
            raise HttpError(401, "Authentication required - valid user not found")
        
        # Check if user has access to this schedule
        if not check_cctv_access(request.user, 'view'):
            raise HttpError(403, "Access denied to this schedule")
        
        # Get scheduler information
        scheduler_info = {
            "is_active": schedule.is_active,
            "next_run_time": None,
            "last_run_time": None,
            "total_runs": 0,
            "missed_runs": 0
        }
        
        if schedule.is_active:
            # Calculate next run time based on schedule type
            now = timezone.now()
            today = now.date()
            current_time = now.time()
            
            if schedule.schedule_type == 'once':
                if schedule.start_date and schedule.start_date >= today:
                    scheduled_datetime = datetime.combine(schedule.start_date, schedule.start_time)
                    scheduled_datetime = timezone.make_aware(scheduled_datetime)
                    if scheduled_datetime > now:
                        scheduler_info["next_run_time"] = scheduled_datetime.isoformat()
                    else:
                        scheduler_info["next_run_time"] = "Already passed"
                else:
                    scheduler_info["next_run_time"] = "Schedule expired"
                    
            elif schedule.schedule_type == 'daily':
                # Calculate next daily run
                if current_time < schedule.start_time:
                    # Today at start_time
                    next_run = datetime.combine(today, schedule.start_time)
                else:
                    # Tomorrow at start_time
                    next_run = datetime.combine(today + timedelta(days=1), schedule.start_time)
                next_run = timezone.make_aware(next_run)
                scheduler_info["next_run_time"] = next_run.isoformat()
                
            elif schedule.schedule_type == 'weekly':
                if schedule.days_of_week:
                    # Find next occurrence
                    day_mapping = {
                        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                        'friday': 4, 'saturday': 5, 'sunday': 6
                    }
                    
                    current_weekday = now.weekday()
                    next_run = None
                    
                    # Check remaining days this week
                    for day_name in schedule.days_of_week:
                        day_num = day_mapping.get(day_name.lower())
                        if day_num is not None:
                            if day_num > current_weekday:
                                # This week
                                days_ahead = day_num - current_weekday
                                next_run = datetime.combine(today + timedelta(days=days_ahead), schedule.start_time)
                                break
                            elif day_num == current_weekday and current_time < schedule.start_time:
                                # Today
                                next_run = datetime.combine(today, schedule.start_time)
                                break
                    
                    # If no remaining days this week, check next week
                    if not next_run:
                        for day_name in schedule.days_of_week:
                            day_num = day_mapping.get(day_name.lower())
                            if day_num is not None:
                                days_ahead = 7 - current_weekday + day_num
                                next_run = datetime.combine(today + timedelta(days=days_ahead), schedule.start_time)
                                break
                    
                    if next_run:
                        next_run = timezone.make_aware(next_run)
                        scheduler_info["next_run_time"] = next_run.isoformat()
                        
            elif schedule.schedule_type == 'continuous':
                scheduler_info["next_run_time"] = "Continuous - runs continuously"
        
        # Get recording statistics
        recordings = schedule.recordings.all()
        scheduler_info["total_runs"] = recordings.count()
        scheduler_info["last_run_time"] = recordings.order_by('-start_time').first().start_time.isoformat() if recordings.exists() else None
        
        return {
            "schedule_id": str(schedule.id),
            "schedule_name": schedule.name,
            "camera_name": schedule.camera.name,
            "schedule_type": schedule.schedule_type,
            "scheduler_info": scheduler_info,
            "schedule_details": {
                "start_time": schedule.start_time.isoformat(),
                "end_time": schedule.end_time.isoformat(),
                "start_date": schedule.start_date.isoformat() if schedule.start_date else None,
                "end_date": schedule.end_date.isoformat() if schedule.end_date else None,
                "days_of_week": schedule.days_of_week,
                "is_active": schedule.is_active
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting schedule status for {schedule_id}: {str(e)}")
        raise HttpError(500, f"Internal server error: {str(e)}")


# Dashboard Analytics and Activity Endpoints

@router.get("/dashboard/analytics", summary="Get Dashboard Analytics", description="Get chart data for dashboard", tags=["Dashboard"], auth=cctv_jwt_auth)
def get_dashboard_analytics(request):
    """
    Get analytics data for dashboard charts including:
    - Camera status distribution
    - Recording activity over time
    - Storage usage trends
    - System performance metrics
    """
    try:
        from django.db.models import Count, Q
        from django.utils import timezone
        from datetime import datetime, timedelta
        import calendar
        
        # Get current date and time ranges
        now = timezone.now()
        today = now.date()
        last_7_days = today - timedelta(days=7)
        last_30_days = today - timedelta(days=30)
        
        # Camera status distribution
        camera_status = list(Camera.objects.values('status').annotate(count=Count('status')))
        
        # Recording activity for last 7 days
        recording_activity = []
        for i in range(7):
            date = today - timedelta(days=i)
            count = Recording.objects.filter(start_time__date=date).count()
            recording_activity.append({
                'date': date.isoformat(),
                'day': calendar.day_name[date.weekday()],
                'recordings': count
            })
        recording_activity.reverse()  # Show oldest to newest
        
        # Hourly recording activity for today
        hourly_activity = []
        for hour in range(24):
            start_hour = datetime.combine(today, datetime.min.time()) + timedelta(hours=hour)
            end_hour = start_hour + timedelta(hours=1)
            start_hour = timezone.make_aware(start_hour)
            end_hour = timezone.make_aware(end_hour)
            
            count = Recording.objects.filter(
                start_time__gte=start_hour,
                start_time__lt=end_hour
            ).count()
            
            hourly_activity.append({
                'hour': f"{hour:02d}:00",
                'recordings': count
            })
        
        # Schedule type distribution
        schedule_types = list(RecordingSchedule.objects.values('schedule_type').annotate(count=Count('schedule_type')))
        
        # Storage usage simulation (replace with actual storage calculation)
        storage_data = []
        for i in range(30):
            date = today - timedelta(days=i)
            # Simulate storage growth over time
            base_storage = 1000  # GB
            daily_growth = 50 * (30 - i)  # Simulate gradual growth
            storage_data.append({
                'date': date.isoformat(),
                'storage_gb': base_storage + daily_growth
            })
        storage_data.reverse()
        
        # System metrics
        total_cameras = Camera.objects.count()
        online_cameras = Camera.objects.filter(status='active').count()
        total_recordings = Recording.objects.count()
        total_schedules = RecordingSchedule.objects.count()
        active_schedules = RecordingSchedule.objects.filter(is_active=True).count()
        
        return {
            "camera_status_distribution": camera_status,
            "recording_activity_7_days": recording_activity,
            "hourly_activity_today": hourly_activity,
            "schedule_type_distribution": schedule_types,
            "storage_usage_30_days": storage_data,
            "system_metrics": {
                "total_cameras": total_cameras,
                "online_cameras": online_cameras,
                "offline_cameras": total_cameras - online_cameras,
                "total_recordings": total_recordings,
                "total_schedules": total_schedules,
                "active_schedules": active_schedules,
                "uptime_percentage": round((online_cameras / total_cameras * 100) if total_cameras > 0 else 0, 1)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard analytics: {str(e)}")
        raise HttpError(500, f"Internal server error: {str(e)}")


@router.get("/dashboard/activity", summary="Get Recent Activity", description="Get recent system activity and events", tags=["Dashboard"], auth=cctv_jwt_auth)
def get_recent_activity(request, limit: int = 20):
    """
    Get recent activity including:
    - Camera status changes
    - Recording events
    - Schedule activations
    - System events
    """
    try:
        from django.db.models import Q
        from django.utils import timezone
        from datetime import timedelta
        
        # Get recent activity from different sources
        activities = []
        
        # Recent recordings (last 24 hours)
        recent_recordings = Recording.objects.filter(
            start_time__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-start_time')[:10]
        
        for recording in recent_recordings:
            duration = None
            if recording.end_time:
                duration = int((recording.end_time - recording.start_time).total_seconds())
            
            activities.append({
                'id': str(recording.id),
                'type': 'recording',
                'title': f"Recording started on {recording.camera.name}",
                'description': f"Duration: {duration}s" if duration else "Recording in progress",
                'camera_name': recording.camera.name,
                'camera_id': str(recording.camera.id),
                'timestamp': recording.start_time.isoformat(),
                'status': 'completed' if recording.end_time else 'active',
                'metadata': {
                    'file_size': recording.file_size,
                    'file_path': recording.file_path,
                }
            })
        
        # Recent schedule activations/deactivations
        recent_schedules = RecordingSchedule.objects.filter(
            updated_at__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-updated_at')[:10]
        
        for schedule in recent_schedules:
            activities.append({
                'id': str(schedule.id),
                'type': 'schedule',
                'title': f"Schedule '{schedule.name}' {'activated' if schedule.is_active else 'deactivated'}",
                'description': f"Camera: {schedule.camera.name} - Type: {schedule.schedule_type}",
                'camera_name': schedule.camera.name,
                'camera_id': str(schedule.camera.id),
                'timestamp': schedule.updated_at.isoformat(),
                'status': 'active' if schedule.is_active else 'inactive',
                'metadata': {
                    'schedule_type': schedule.schedule_type,
                    'days_of_week': schedule.days_of_week,
                }
            })

        
        # Recent camera updates
        recent_cameras = Camera.objects.filter(
            updated_at__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-updated_at')[:5]
        
        for camera in recent_cameras:
            activities.append({
                'id': str(camera.id),
                'type': 'camera',
                'title': f"Camera '{camera.name}' status updated",
                'description': f"Status: {camera.status} - Location: {camera.location}",
                'camera_name': camera.name,
                'camera_id': str(camera.id),
                'timestamp': camera.updated_at.isoformat(),
                'status': camera.status,
                'metadata': {
                    'ip_address': camera.ip_address,
                    'location': camera.location,
                }
            })
        
        # Sort all activities by timestamp (most recent first)
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Limit the results
        activities = activities[:limit]
        
        return {
            "activities": activities,
            "total_count": len(activities),
            "last_updated": timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting recent activity: {str(e)}")
        raise HttpError(500, f"Internal server error: {str(e)}")



@router.post("/recordings/transfer-to-gcp/", response=GCPTransferResponseSchema, auth=cctv_jwt_auth,
            summary="Transfer Videos to GCP Cloud Storage",
            description="Initiate transfer of recorded videos from local storage to GCP Cloud Storage. Videos will be automatically deleted from local storage after 24 hours.")
def transfer_recordings_to_gcp(request, transfer_request: GCPTransferRequestSchema):
    """
    Transfer recorded videos to GCP Cloud Storage with automatic local cleanup after 24 hours
    
    This endpoint will:
    1. Find all local recordings (or specific ones if IDs provided)
    2. Initiate background upload to GCP Cloud Storage
    3. Update the recording storage_type to 'gcp'
    4. Create GCPVideoTransfer records to track the process
    5. Schedule automatic cleanup of local files after 24 hours
    """
    from .models import Recording, GCPVideoTransfer
    from .storage_service import storage_service
    from django.db import transaction
    import os
    
    # Check if user has permission to transfer recordings
    if not check_cctv_access(request.user, 'manage'):
        raise HttpError(403, "You don't have permission to transfer recordings to GCP")
    
    # Check if GCP is configured
    if not storage_service.use_gcp:
        raise HttpError(400, "GCP Storage is not configured. Please contact administrator.")
    
    try:
        with transaction.atomic():
            # Get recordings to transfer
            recordings_query = Recording.objects.filter(
                storage_type='local',
                file_path__isnull=False
            ).exclude(file_path='').exclude(file_path__endswith='.tmp')
            
            # Filter by specific recording IDs if provided
            if transfer_request.recording_ids:
                recordings_query = recordings_query.filter(
                    id__in=transfer_request.recording_ids
                )
            
            recordings = list(recordings_query)
            total_recordings = len(recordings)
            
            if total_recordings == 0:
                return {
                    "message": "No recordings found for transfer",
                    "total_recordings": 0,
                    "initiated_transfers": 0,
                    "already_transferred": 0,
                    "failed_initiations": 0,
                    "transfer_ids": []
                }
            
            initiated_transfers = 0
            already_transferred = 0
            failed_initiations = 0
            transfer_ids = []
            
            for recording in recordings:
                try:
                    # Check if transfer already exists
                    existing_transfer, created = GCPVideoTransfer.objects.get_or_create(
                        recording=recording,
                        defaults={
                            'original_local_path': recording.file_path,
                            'initiated_by': request.user,
                            'file_size_bytes': recording.file_size or 0,
                        }
                    )
                    
                    if not created:
                        if existing_transfer.transfer_status in ['completed', 'uploading', 'cleanup_pending', 'cleanup_completed']:
                            already_transferred += 1
                            continue
                        elif existing_transfer.transfer_status == 'failed' and existing_transfer.retry_count >= 3:
                            # Skip recordings that have failed too many times
                            failed_initiations += 1
                            continue
                    
                    # Verify local file exists
                    local_file_path = os.path.join(settings.MEDIA_ROOT, recording.file_path)
                    if not os.path.exists(local_file_path):
                        existing_transfer.mark_upload_failed(f"Local file not found: {local_file_path}")
                        failed_initiations += 1
                        continue
                    
                    # Update file size if not set
                    if existing_transfer.file_size_bytes == 0:
                        existing_transfer.file_size_bytes = os.path.getsize(local_file_path)
                        existing_transfer.save(update_fields=['file_size_bytes'])
                    
                    # Start the transfer process in background
                    from threading import Thread
                    thread = Thread(target=_perform_gcp_upload, args=(existing_transfer,))
                    thread.daemon = True
                    thread.start()
                    
                    transfer_ids.append(str(existing_transfer.id))
                    initiated_transfers += 1
                    
                except Exception as e:
                    logger.error(f"Failed to initiate transfer for recording {recording.id}: {str(e)}")
                    failed_initiations += 1
            
            return {
                "message": f"Successfully initiated {initiated_transfers} video transfers to GCP Cloud Storage",
                "total_recordings": total_recordings,
                "initiated_transfers": initiated_transfers,
                "already_transferred": already_transferred,
                "failed_initiations": failed_initiations,
                "transfer_ids": transfer_ids
            }
            
    except Exception as e:
        logger.error(f"Error initiating GCP transfers: {str(e)}")
        raise HttpError(500, f"Internal server error: {str(e)}")

def _perform_gcp_upload(gcp_transfer):
    """Background function to perform the actual GCP upload"""
    from .storage_service import storage_service
    from django.conf import settings
    import os
    
    try:
        # Mark upload as started
        gcp_transfer.mark_upload_started()
        
        recording = gcp_transfer.recording
        local_file_path = os.path.join(settings.MEDIA_ROOT, recording.file_path)
        
        # Generate GCP storage path
        gcp_path = f"recordings/{recording.camera.id}/{recording.id}/{os.path.basename(recording.file_path)}"
        
        # Upload to GCP
        success = storage_service.upload_file(
            file_path=local_file_path,
            destination_path=gcp_path,
            content_type="video/mp4",
            timeout=600  # 10 minutes timeout for large files
        )
        
        if success:
            # Get public URL
            public_url = storage_service.get_file_url(gcp_path)
            
            # Mark upload as completed
            gcp_transfer.mark_upload_completed(gcp_path, public_url)
            
            # Update recording to point to GCP
            recording.storage_type = 'gcp'
            recording.file_path = gcp_path
            recording.save(update_fields=['storage_type', 'file_path'])
            
            logger.info(f"Successfully uploaded recording {recording.id} to GCP: {gcp_path}")
        else:
            gcp_transfer.mark_upload_failed("Failed to upload file to GCP storage")
            
    except Exception as e:
        error_msg = f"Upload failed: {str(e)}"
        gcp_transfer.mark_upload_failed(error_msg)
        logger.error(f"GCP upload failed for transfer {gcp_transfer.id}: {error_msg}")


# Create the API instance with comprehensive documentation
api = NinjaAPI(
    title="CCTV Management API",
    version="4.0.0",
    description="""
    ## 🎥 CCTV Management System API
    
    Comprehensive REST API for managing IP CCTV cameras, video recordings, and live streaming.
   
    """,
    docs_url="/docs",
    openapi_url="/openapi.json",
    urls_namespace="cctv_system",  # Changed to unique namespace
    csrf=False  # Disable CSRF for API endpoints
)

# Create a separate API instance for direct local-client routes (compatibility)
# This allows /api/local-client/* to work directly
local_client_api = NinjaAPI(
    title="Local Client API",
    version="5.0.0",
    description="API for local CCTV recording clients",
    urls_namespace="local_client_direct",
    csrf=False
)

# Add additional info to OpenAPI schema
@api.get("/health", summary="Health Check", description="Check if the API is running", tags=["System"])
def health_check(request):
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "service": "CCTV Management API",
        "version": "1.0.0",
        "features": [
            "Camera Management",
            "Live Video Streaming",
            "Recording Control", 
            "H264 Codec Optimization",
            "Real-time Monitoring",
            "Automated Scheduling",
            "Stream Session Tracking"
        ]
    }

# Local Client API Router
local_client_router = Router(tags=["Local Client"])

# Register endpoints on both routers with different paths
# Main router uses /local-client prefix, direct router uses no prefix

@local_client_router.get(
    "/local-client/schedules",
    summary="Get schedules for local client",
    description="Returns all active schedules for cameras assigned to this client"
)
def get_local_client_schedules(request, client_id: str = None, last_sync: str = None):
    """Get schedules for local client"""
    from django.utils import timezone
    from datetime import timedelta
    
    try:
        # Authenticate client using token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HttpError(401, "Missing or invalid authorization token")
        
        client_token = auth_header.split('Bearer ')[1]
        
        # Verify client token
        try:
            client = LocalRecordingClient.objects.get(client_token=client_token)
        except LocalRecordingClient.DoesNotExist:
            raise HttpError(401, "Invalid client token")
        
        # Update client heartbeat
        client.mark_online()
        if hasattr(request, 'META') and 'REMOTE_ADDR' in request.META:
            client.ip_address = request.META['REMOTE_ADDR']
            client.save(update_fields=['ip_address'])
        
        # Get assigned cameras
        assigned_cameras = client.assigned_cameras.filter(recording_mode='local_client', is_active=True)
        
        # Check if client has any assigned cameras
        if not assigned_cameras.exists():
            logger.info(f"Client {client.name} has no assigned cameras")
            return []  # Return empty list instead of error
        
        # Get active schedules for assigned cameras
        schedules = RecordingSchedule.objects.filter(
            camera__in=assigned_cameras,
            is_active=True
        ).select_related('camera')
        
        # Filter by last_sync if provided
        if last_sync:
            try:
                sync_time = timezone.datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                schedules = schedules.filter(updated_at__gte=sync_time)
            except:
                pass  # If parsing fails, return all schedules
        
        # Check if no schedules found
        if not schedules.exists():
            logger.info(f"No active schedules found for client {client.name}")
            return []  # Return empty list instead of error
        
        serializer = LocalClientScheduleSerializer(schedules, many=True)
        data = serializer.data
        
        # Validate that we have data
        if not data:
            return []
        
        # Transform to match client's expected format with nested camera object
        result = []
        for item in data:
            try:
                # Validate required fields
                if not all(k in item for k in ['id', 'name', 'schedule_type', 'start_time', 'end_time', 'camera_id', 'camera_name']):
                    logger.warning(f"Schedule missing required fields: {item.get('id', 'unknown')}")
                    continue
                
                # Create nested camera object
                schedule_data = {
                    'id': str(item['id']),
                    'name': item['name'],
                    'schedule_type': item['schedule_type'],
                    'start_time': str(item['start_time']),
                    'end_time': str(item['end_time']),
                    'start_date': str(item.get('start_date')) if item.get('start_date') else None,
                    'end_date': str(item.get('end_date')) if item.get('end_date') else None,
                    'days_of_week': item.get('days_of_week', []) if item.get('days_of_week') else [],
                    'is_active': item.get('is_active', True),
                    'camera': {
                        'id': str(item['camera_id']),
                        'name': item['camera_name'],
                        'ip_address': item.get('camera_ip_address', ''),
                        'rtsp_url': item.get('camera_rtsp_url', ''),
                        'rtsp_url_sub': item.get('camera_rtsp_url_sub'),
                        'camera_type': item.get('camera_type', 'rtsp'),
                        'location': item.get('camera_location'),
                        'record_quality': item.get('camera_record_quality', 'medium')
                    }
                }
                result.append(schedule_data)
            except Exception as e:
                logger.error(f"Error transforming schedule {item.get('id', 'unknown')}: {str(e)}")
                continue
        
        return result
        
    except HttpError:
        raise
    except Exception as e:
        logger.error(f"Error fetching schedules for local client: {str(e)}")
        raise HttpError(500, f"Error fetching schedules: {str(e)}")


@local_client_router.post(
    "/local-client/recordings/status",
    summary="Update recording status",
    description="Update recording status from local client"
)
def update_recording_status(request):
    """Update recording status from local client"""
    from django.utils import timezone
    import json
    
    try:
        # Parse request body
        body = json.loads(request.body)
        
        # Authenticate client
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HttpError(401, "Missing or invalid authorization token")
        
        client_token = auth_header.split('Bearer ')[1]
        
        try:
            client = LocalRecordingClient.objects.get(client_token=client_token)
        except LocalRecordingClient.DoesNotExist:
            raise HttpError(401, "Invalid client token")
        
        # Validate data using serializer
        serializer = RecordingStatusUpdateSerializer(data=body)
        if not serializer.is_valid():
            raise HttpError(400, f"Invalid data: {serializer.errors}")
        
        data = serializer.validated_data
        
        # Get recording
        try:
            recording = Recording.objects.get(id=data['recording_id'], recorded_by_client=client)
        except Recording.DoesNotExist:
            raise HttpError(404, "Recording not found")
        
        # Update recording status
        recording.status = data['status']
        
        if 'progress' in data and data['progress'] is not None:
            # Store progress in a JSON field or custom field
            pass
        
        if 'frames_recorded' in data and data['frames_recorded'] is not None:
            # Could store in a custom field if needed
            pass
        
        if 'file_size' in data and data['file_size'] is not None:
            recording.file_size = data['file_size']
        
        if 'error_message' in data and data['error_message']:
            recording.error_message = data['error_message']
        
        if data['status'] == 'completed':
            recording.end_time = timezone.now()
            if recording.start_time:
                recording.duration = recording.end_time - recording.start_time
            if 'gcp_path' in data and data['gcp_path']:
                recording.file_path = data['gcp_path']
                recording.storage_type = 'gcp'
                recording.upload_status = 'completed'
        elif data['status'] == 'failed':
            recording.upload_status = 'failed'
        elif data['status'] == 'recording':
            recording.upload_status = 'uploading'
        
        recording.save()
        
        return {"message": "Recording status updated successfully"}
        
    except HttpError:
        raise
    except Exception as e:
        logger.error(f"Error updating recording status: {str(e)}")
        raise HttpError(500, f"Error updating status: {str(e)}")


@local_client_router.post(
    "/local-client/recordings/register",
    summary="Register new recording",
    description="Register a new recording before starting"
)
def register_recording(request, camera_id: str, schedule_id: str = None, recording_name: str = None):
    """Register a new recording"""
    from django.utils import timezone
    
    try:
        # Authenticate client
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HttpError(401, "Missing or invalid authorization token")
        
        client_token = auth_header.split('Bearer ')[1]
        
        try:
            client = LocalRecordingClient.objects.get(client_token=client_token)
        except LocalRecordingClient.DoesNotExist:
            raise HttpError(401, "Invalid client token")
        
        # Get camera
        try:
            camera = Camera.objects.get(id=camera_id, is_active=True)
            if camera not in client.assigned_cameras.all():
                raise HttpError(403, "Camera not assigned to this client")
            if camera.recording_mode != 'local_client':
                raise HttpError(403, f"Camera recording mode is '{camera.recording_mode}', not 'local_client'")
        except Camera.DoesNotExist:
            raise HttpError(404, f"Camera not found or inactive: {camera_id}")
        except Camera.MultipleObjectsReturned:
            # Should not happen with UUID, but handle just in case
            camera = Camera.objects.filter(id=camera_id, is_active=True).first()
            if not camera:
                raise HttpError(404, f"Camera not found: {camera_id}")
        
        # Get schedule if provided
        schedule = None
        if schedule_id:
            try:
                schedule = RecordingSchedule.objects.get(id=schedule_id)
            except RecordingSchedule.DoesNotExist:
                pass
        
        # Create recording
        if not recording_name:
            recording_name = f"Recording - {camera.name} - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        recording = Recording.objects.create(
            camera=camera,
            schedule=schedule,
            name=recording_name,
            start_time=timezone.now(),
            status='scheduled',
            recorded_by_client=client,
            upload_status='pending'
        )
        
        return {
            "recording_id": str(recording.id),
            "message": "Recording registered successfully"
        }
        
    except HttpError:
        raise
    except Exception as e:
        logger.error(f"Error registering recording: {str(e)}")
        raise HttpError(500, f"Error registering recording: {str(e)}")


@local_client_router.post(
    "/local-client/heartbeat",
    summary="Send heartbeat",
    description="Send periodic heartbeat with system status"
)
def send_heartbeat(request):
    """Send heartbeat from local client"""
    from django.utils import timezone
    import json
    
    try:
        # Parse request body
        body = json.loads(request.body)
        
        # Authenticate client
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HttpError(401, "Missing or invalid authorization token")
        
        client_token = auth_header.split('Bearer ')[1]
        
        try:
            client = LocalRecordingClient.objects.get(client_token=client_token)
        except LocalRecordingClient.DoesNotExist:
            raise HttpError(401, "Invalid client token")
        
        # Validate data using serializer
        serializer = HeartbeatSerializer(data=body)
        if not serializer.is_valid():
            raise HttpError(400, f"Invalid data: {serializer.errors}")
        
        data = serializer.validated_data
        
        # Update client status
        client.mark_online()
        if hasattr(request, 'META') and 'REMOTE_ADDR' in request.META:
            client.ip_address = request.META['REMOTE_ADDR']
        if 'system_info' in data and data['system_info']:
            client.system_info = data['system_info']
        client.save()
        
        return {
            "message": "Heartbeat received",
            "client_id": str(client.id),
            "status": client.status
        }
        
    except HttpError:
        raise
    except Exception as e:
        logger.error(f"Error processing heartbeat: {str(e)}")
        raise HttpError(500, f"Error processing heartbeat: {str(e)}")


@local_client_router.get(
    "/local-client/cameras",
    summary="Get cameras for local client",
    description="Returns cameras assigned to this client"
)
def get_local_client_cameras(request):
    """Get cameras assigned to local client"""
    try:
        # Authenticate client
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HttpError(401, "Missing or invalid authorization token")
        
        client_token = auth_header.split('Bearer ')[1]
        
        try:
            client = LocalRecordingClient.objects.get(client_token=client_token)
        except LocalRecordingClient.DoesNotExist:
            raise HttpError(401, "Invalid client token")
        
        # Update heartbeat
        client.mark_online()
        
        # Get assigned cameras
        cameras = client.assigned_cameras.filter(recording_mode='local_client', is_active=True)
        
        # Check if no cameras assigned
        if not cameras.exists():
            logger.info(f"Client {client.name} has no assigned cameras")
            return []  # Return empty list instead of error
        
        serializer = CameraSerializer(cameras, many=True)
        data = serializer.data
        
        # Validate that we have data
        if not data:
            return []
        
        # Transform to match client's expected format
        result = []
        for item in data:
            try:
                # Validate required fields
                if not all(k in item for k in ['id', 'name', 'rtsp_url']):
                    logger.warning(f"Camera missing required fields: {item.get('id', 'unknown')}")
                    continue
                
                camera_data = {
                    'id': str(item['id']),
                    'name': item['name'],
                    'ip_address': item.get('ip_address', ''),
                    'rtsp_url': item.get('rtsp_url', ''),
                    'rtsp_url_sub': item.get('rtsp_url_sub'),
                    'camera_type': item.get('camera_type', 'rtsp'),
                    'location': item.get('location'),
                    'record_quality': item.get('record_quality', 'medium')
                }
                result.append(camera_data)
            except Exception as e:
                logger.error(f"Error transforming camera {item.get('id', 'unknown')}: {str(e)}")
                continue
        
        return result
        
    except HttpError:
        raise
    except Exception as e:
        logger.error(f"Error fetching cameras for local client: {str(e)}")
        raise HttpError(500, f"Error fetching cameras: {str(e)}")


# Include the router
api.add_router("", router)  # No prefix since we want /cameras/, not /cctv/cameras/
api.add_router("", local_client_router)  # Add local client router for /cctv/local-client/*

# Create duplicate endpoints for direct API access (without /local-client prefix)
# This allows /api/local-client/* to work directly (for client compatibility)
local_client_direct_router = Router(tags=["Local Client"])

# Add health check for local-client API
@local_client_direct_router.get("/health", summary="Health Check", description="Check if the API is running", tags=["Local Client"])
def local_client_health_check(request):
    """Health check endpoint for local client API"""
    return {
        "status": "healthy",
        "service": "Local Client API",
        "version": "1.0.0"
    }

# Register all endpoints on the direct router without the /local-client prefix
local_client_direct_router.get("/schedules", summary="Get schedules for local client", description="Returns all active schedules for cameras assigned to this client")(get_local_client_schedules)
local_client_direct_router.post("/recordings/status", summary="Update recording status", description="Update recording status from local client")(update_recording_status)
local_client_direct_router.post("/recordings/register", summary="Register new recording", description="Register a new recording before starting")(register_recording)
local_client_direct_router.post("/heartbeat", summary="Send heartbeat", description="Send periodic heartbeat with system status")(send_heartbeat)
local_client_direct_router.get("/cameras", summary="Get cameras for local client", description="Returns cameras assigned to this client")(get_local_client_cameras)

# Mount the direct router to the separate API instance
local_client_api.add_router("", local_client_direct_router)
