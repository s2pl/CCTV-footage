from rest_framework import serializers
from .models import Camera, RecordingSchedule, Recording, CameraAccess, LiveStream, LocalRecordingClient


class CameraSerializer(serializers.ModelSerializer):
    """Serializer for Camera model"""
    
    is_online = serializers.ReadOnlyField()
    recording_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Camera
        fields = [
            'id', 'name', 'description', 'ip_address', 'port', 'username', 
            'password', 'rtsp_url', 'rtsp_url_sub', 'camera_type', 'status', 
            'location', 'auto_record', 'record_quality', 'max_recording_hours',
            'created_at', 'updated_at', 
            'last_seen', 'is_online', 'recording_count'
        ]
        extra_kwargs = {
            'password': {'write_only': True},  # Don't expose password in API responses
            'username': {'required': False, 'allow_blank': True},
            'password': {'required': False, 'allow_blank': True, 'write_only': True},
        }
    
    def get_recording_count(self, obj):
        """Get the total number of recordings for this camera"""
        return obj.recordings.count()
    
    def create(self, validated_data):
        """Create camera without authentication"""
        camera = super().create(validated_data)
        
        # Auto-start streaming for new cameras to ensure is_streaming = true
        try:
            from .streaming import stream_manager
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Auto-starting stream for new camera: {camera.name}")
            stream_manager.start_stream(camera, 'main')
            logger.info(f"Stream started successfully for camera: {camera.name}")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to auto-start stream for camera {camera.name}: {str(e)}")
            # Don't fail creation if streaming fails
        
        return camera


class CameraListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for camera lists"""
    
    is_online = serializers.ReadOnlyField()
    
    class Meta:
        model = Camera
        fields = [
            'id', 'name', 'ip_address', 'status', 'location', 
            'camera_type', 'is_online', 'last_seen',
            'rtsp_url', 'rtsp_url_sub', 'auto_record', 'record_quality', 'max_recording_hours'
        ]


class RecordingScheduleSerializer(serializers.ModelSerializer):
    """Serializer for RecordingSchedule model"""
    
    camera_name = serializers.CharField(source='camera.name', read_only=True)
    
    class Meta:
        model = RecordingSchedule
        fields = [
            'id', 'camera', 'camera_name', 'name', 'schedule_type', 
            'start_time', 'end_time', 'start_date', 'end_date', 
            'days_of_week', 'is_active', 'created_by', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'created_by': {'write_only': True},  # Only write, don't include in response
        }

    
    def create(self, validated_data):
        """Create schedule without authentication"""
        # Ensure created_by is set if not provided
        if 'created_by' not in validated_data:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.filter(is_superuser=True).first()
            if user:
                validated_data['created_by'] = user
        return super().create(validated_data)
    
    def to_representation(self, instance):
        """Convert model instance to dictionary with proper field types"""
        data = super().to_representation(instance)
        # Convert camera to string UUID if it exists
        if 'camera' in data and data['camera']:
            data['camera'] = str(data['camera'])
        # Convert created_by to string UUID if it exists
        if 'created_by' in data and data['created_by']:
            data['created_by'] = str(data['created_by'])
        return data
    
    def validate(self, data):
        """Validate schedule data"""
        from django.utils import timezone
        from datetime import datetime, time
        
        if data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError("End time must be after start time")
        
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError("End date must be after start date")
        
        # Validate that start_date is not in the past for 'once' schedules
        if data.get('schedule_type') == 'once' and data.get('start_date'):
            today = timezone.now().date()
            if data['start_date'] < today:
                raise serializers.ValidationError("Start date cannot be in the past for one-time schedules")
            
            # Also check if the combined date and time is in the past
            if data.get('start_time'):
                scheduled_datetime = datetime.combine(data['start_date'], data['start_time'])
                scheduled_datetime = timezone.make_aware(scheduled_datetime)
                if scheduled_datetime < timezone.now():
                    raise serializers.ValidationError("Scheduled date and time cannot be in the past")
        
        if data.get('schedule_type') == 'weekly' and not data.get('days_of_week'):
            raise serializers.ValidationError("Days of week must be specified for weekly schedules")
        
        return data


class RecordingSerializer(serializers.ModelSerializer):
    """Serializer for Recording model"""
    
    camera_name = serializers.CharField(source='camera.name', read_only=True)
    schedule_name = serializers.CharField(source='schedule.name', read_only=True)
    file_url = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    file_exists = serializers.ReadOnlyField()
    absolute_file_path = serializers.ReadOnlyField()
    duration_seconds = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()
    recorded_by_client_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Recording
        fields = [
            'id', 'camera', 'camera_name', 'schedule', 'schedule_name', 
            'name', 'file_path', 'file_size', 'file_size_mb', 'duration', 
            'duration_seconds', 'start_time', 'end_time', 'status', 
            'error_message', 'resolution', 'frame_rate', 'codec', 
            'created_at', 'updated_at', 'file_url', 'is_active',
            'file_exists', 'absolute_file_path', 'recorded_by_client',
            'recorded_by_client_name', 'upload_status'
        ]
        extra_kwargs = {
            'file_path': {'read_only': True},
            'file_size': {'read_only': True},
        }
    
    def get_duration_seconds(self, obj):
        """Get duration in seconds"""
        if obj.duration:
            return obj.duration.total_seconds()
        return None
    
    def get_file_size_mb(self, obj):
        """Get file size in MB"""
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return 0
    
    def get_recorded_by_client_name(self, obj):
        """Get the name of the local recording client"""
        if obj.recorded_by_client:
            return obj.recorded_by_client.name
        return None
    
    def create(self, validated_data):
        """Set the created_by field to the current user"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
    
    def to_representation(self, instance):
        """Convert model instance to dictionary with proper field types"""
        data = super().to_representation(instance)
        # Convert camera to string UUID if it exists
        if 'camera' in data and data['camera']:
            data['camera'] = str(data['camera'])
        # Convert schedule to string UUID if it exists
        if 'schedule' in data and data['schedule']:
            data['schedule'] = str(data['schedule'])
        # Convert created_by to string UUID if it exists
        if 'created_by' in data and data['created_by']:
            data['created_by'] = str(data['created_by'])
        return data


class RecordingListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for recording lists"""
    
    camera_name = serializers.CharField(source='camera.name', read_only=True)
    duration_seconds = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = Recording
        fields = [
            'id', 'camera_name', 'name', 'start_time', 'end_time', 
            'status', 'duration_seconds', 'file_size_mb'
        ]
    
    def get_duration_seconds(self, obj):
        if obj.duration:
            return obj.duration.total_seconds()
        return None
    
    def get_file_size_mb(self, obj):
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return 0


class CameraAccessSerializer(serializers.ModelSerializer):
    """Serializer for CameraAccess model"""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    camera_name = serializers.CharField(source='camera.name', read_only=True)
    granted_by_username = serializers.CharField(source='granted_by.username', read_only=True)
    
    class Meta:
        model = CameraAccess
        fields = [
            'id', 'user', 'user_username', 'camera', 'camera_name', 
            'access_level', 'can_record', 'can_schedule', 'can_download',
            'access_start_time', 'access_end_time', 'granted_by', 
            'granted_by_username', 'granted_at', 'is_active'
        ]
        extra_kwargs = {
            'granted_by': {'read_only': True},
        }
    
    def create(self, validated_data):
        """Set the granted_by field to the current user"""
        validated_data['granted_by'] = self.context['request'].user
        return super().create(validated_data)
    
    def to_representation(self, instance):
        """Convert model instance to dictionary with proper field types"""
        data = super().to_representation(instance)
        # Convert foreign key fields to string UUIDs if they exist
        if 'user' in data and data['user']:
            data['user'] = str(data['user'])
        if 'camera' in data and data['camera']:
            data['camera'] = str(data['camera'])
        if 'granted_by' in data and data['granted_by']:
            data['granted_by'] = str(data['granted_by'])
        return data


class LiveStreamSerializer(serializers.ModelSerializer):
    """Serializer for LiveStream model"""
    
    camera_name = serializers.CharField(source='camera.name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    duration_seconds = serializers.SerializerMethodField()
    
    class Meta:
        model = LiveStream
        fields = [
            'id', 'camera', 'camera_name', 'user', 'user_username', 
            'session_id', 'start_time', 'end_time', 'is_active', 
            'client_ip', 'user_agent', 'duration_seconds'
        ]
        extra_kwargs = {
            'user': {'read_only': True},
            'session_id': {'read_only': True},
            'client_ip': {'read_only': True},
            'user_agent': {'read_only': True},
        }
    
    def get_duration_seconds(self, obj):
        """Get session duration in seconds"""
        if obj.end_time:
            return (obj.end_time - obj.start_time).total_seconds()
        elif obj.is_active:
            from django.utils import timezone
            return (timezone.now() - obj.start_time).total_seconds()
        return None
    
    def to_representation(self, instance):
        """Convert model instance to dictionary with proper field types"""
        data = super().to_representation(instance)
        # Convert foreign key fields to string UUIDs if they exist
        if 'camera' in data and data['camera']:
            data['camera'] = str(data['camera'])
        if 'user' in data and data['user']:
            data['user'] = str(data['user'])
        return data


class CameraStreamUrlSerializer(serializers.Serializer):
    """Serializer for camera stream URL requests"""
    
    quality = serializers.ChoiceField(
        choices=[('main', 'Main Stream'), ('sub', 'Sub Stream')],
        default='main'
    )


class RecordingControlSerializer(serializers.Serializer):
    """Serializer for recording control actions"""
    
    duration_minutes = serializers.IntegerField(
        min_value=1, 
        max_value=1440,  # 24 hours
        required=False,
        help_text="Recording duration in minutes (optional for continuous recording)"
    )
    recording_name = serializers.CharField(
        max_length=255,
        required=False,
        help_text="Custom name for the recording"
    )
    quality = serializers.ChoiceField(
        choices=[('main', 'Main Stream'), ('sub', 'Sub Stream')],
        default='main',
        required=False,
        help_text="Recording quality/stream selection"
    )


class CameraRegistrationSerializer(serializers.Serializer):
    """Serializer for camera registration/setup"""
    
    name = serializers.CharField(max_length=255, help_text="Camera name/label")
    description = serializers.CharField(max_length=500, required=False, help_text="Camera description")
    
    # Option 1: Use IP address and build RTSP URL
    ip_address = serializers.IPAddressField(required=False, help_text="Camera IP address")
    port = serializers.IntegerField(default=554, min_value=1, max_value=65535, help_text="RTSP port")
    username = serializers.CharField(max_length=100, required=False, allow_blank=True, help_text="Camera username")
    password = serializers.CharField(max_length=100, required=False, allow_blank=True, help_text="Camera password")
    
    # Option 2: Use complete RTSP URL
    rtsp_url = serializers.CharField(max_length=500, required=False, help_text="Complete RTSP URL")
    rtsp_url_sub = serializers.CharField(max_length=500, required=False, help_text="Secondary RTSP stream URL")
    
    # Camera settings
    camera_type = serializers.ChoiceField(
        choices=[('ip', 'IP Camera'), ('rtsp', 'RTSP Camera'), ('webcam', 'Webcam')],
        default='rtsp'
    )
    location = serializers.CharField(max_length=255, required=False, help_text="Physical location")
    auto_record = serializers.BooleanField(default=False, help_text="Enable automatic recording")
    record_quality = serializers.ChoiceField(
        choices=[('high', 'High'), ('medium', 'Medium'), ('low', 'Low')],
        default='medium'
    )
    
    # Auto-setup options
    test_connection = serializers.BooleanField(default=True, help_text="Test connection before creating")
    start_recording = serializers.BooleanField(default=False, help_text="Start 5-minute test recording")
    
    def validate(self, data):
        """Validate camera registration data"""
        ip_address = data.get('ip_address')
        rtsp_url = data.get('rtsp_url')
        
        # Must provide either IP address or RTSP URL
        if not ip_address and not rtsp_url:
            raise serializers.ValidationError("Either ip_address or rtsp_url must be provided")
        
        # If IP address is provided, build RTSP URL
        if ip_address and not rtsp_url:
            username = data.get('username', '')
            password = data.get('password', '')
            port = data.get('port', 554)
            
            # Build RTSP URL
            auth = ""
            if username and password:
                auth = f"{username}:{password}@"
            elif username:
                auth = f"{username}@"
            
            data['rtsp_url'] = f"rtsp://{auth}{ip_address}:{port}/stream1"
        
        # Ensure we have a valid IP address
        if not data.get('ip_address'):
            if rtsp_url:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(rtsp_url)
                    data['ip_address'] = parsed.hostname or '127.0.0.1'
                except:
                    data['ip_address'] = '127.0.0.1'
            else:
                data['ip_address'] = '127.0.0.1'
        
        # If RTSP URL is provided, extract IP address if not provided
        if rtsp_url and not ip_address:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(rtsp_url)
                data['ip_address'] = parsed.hostname
                data['port'] = parsed.port or 554
                
                if parsed.username:
                    data['username'] = parsed.username
                if parsed.password:
                    data['password'] = parsed.password
            except Exception:
                pass  # Keep original values
        
        return data


class ScheduleCreateSerializer(serializers.Serializer):
    """Serializer for creating recording schedules"""
    
    camera_id = serializers.UUIDField(help_text="Camera ID to schedule recordings for")
    name = serializers.CharField(max_length=255, help_text="Schedule name")
    
    schedule_type = serializers.ChoiceField(
        choices=[('once', 'One Time'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('continuous', 'Continuous')],
        help_text="Type of schedule"
    )
    
    # Time settings
    start_time = serializers.TimeField(help_text="Recording start time")
    end_time = serializers.TimeField(help_text="Recording end time")
    
    # Date settings (for one-time schedules)
    start_date = serializers.DateField(required=False, help_text="Start date (for one-time schedules)")
    end_date = serializers.DateField(required=False, help_text="End date")
    
    # Weekly schedule settings
    days_of_week = serializers.ListField(
        child=serializers.ChoiceField(choices=[
            ('monday', 'Monday'), ('tuesday', 'Tuesday'), ('wednesday', 'Wednesday'),
            ('thursday', 'Thursday'), ('friday', 'Friday'), ('saturday', 'Saturday'), ('sunday', 'Sunday')
        ]),
        required=False,
        help_text="Days of week for weekly schedules"
    )
    
    # Recording settings
    recording_quality = serializers.ChoiceField(
        choices=[('main', 'Main Stream'), ('sub', 'Sub Stream')],
        default='main',
        help_text="Recording quality/stream"
    )
    
    is_active = serializers.BooleanField(default=True, help_text="Activate schedule immediately")
    
    def validate(self, data):
        """Validate schedule data"""
        # Check time range
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("End time must be after start time")
        
        # Check date range for one-time schedules
        if data['schedule_type'] == 'once':
            if not data.get('start_date'):
                raise serializers.ValidationError("Start date is required for one-time schedules")
            
            if data.get('end_date') and data['start_date'] > data['end_date']:
                raise serializers.ValidationError("End date must be after start date")
        
        # Check days for weekly schedules
        if data['schedule_type'] == 'weekly' and not data.get('days_of_week'):
            raise serializers.ValidationError("Days of week must be specified for weekly schedules")
        
        # Validate camera exists
        from .models import Camera
        try:
            Camera.objects.get(id=data['camera_id'])
        except Camera.DoesNotExist:
            raise serializers.ValidationError("Camera not found")
        
        return data


class LiveStreamActivationSerializer(serializers.Serializer):
    """Serializer for live stream activation requests"""
    
    quality = serializers.ChoiceField(
        choices=[('main', 'Main Stream'), ('sub', 'Sub Stream')],
        default='main',
        required=False,
        help_text="Stream quality to activate (main or sub)"
    )
    
    def validate_quality(self, value):
        """Validate stream quality"""
        if value not in ['main', 'sub']:
            raise serializers.ValidationError("Quality must be 'main' or 'sub'")
        return value


class LiveStreamStatusSerializer(serializers.Serializer):
    """Serializer for live stream status responses"""
    
    is_active = serializers.BooleanField(help_text="Whether the stream is currently active")
    session_id = serializers.CharField(help_text="Unique session identifier")
    start_time = serializers.DateTimeField(help_text="When the stream started")
    end_time = serializers.DateTimeField(required=False, help_text="When the stream ended (if stopped)")
    duration_seconds = serializers.FloatField(required=False, help_text="Stream duration in seconds")
    quality = serializers.CharField(help_text="Stream quality (main or sub)")
    stream_url = serializers.CharField(help_text="URL to access the stream")
    camera_info = serializers.DictField(help_text="Camera information")
    user_info = serializers.DictField(help_text="User who started the stream")


class LocalRecordingClientSerializer(serializers.ModelSerializer):
    """Serializer for LocalRecordingClient model"""
    
    assigned_cameras_count = serializers.SerializerMethodField()
    recordings_count = serializers.SerializerMethodField()
    
    class Meta:
        model = LocalRecordingClient
        fields = [
            'id', 'name', 'client_token', 'ip_address', 'last_heartbeat',
            'status', 'system_info', 'assigned_cameras', 'assigned_cameras_count',
            'recordings_count', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'client_token': {'write_only': True},  # Don't expose token in API responses for security
        }
    
    def get_assigned_cameras_count(self, obj):
        """Get the number of cameras assigned to this client"""
        return obj.assigned_cameras.count()
    
    def get_recordings_count(self, obj):
        """Get the number of recordings made by this client"""
        return obj.recordings.count()


class LocalClientScheduleSerializer(serializers.ModelSerializer):
    """Serializer for schedules returned to local clients"""
    
    # Use simple serializers instead of nested ModelSerializer for Django Ninja compatibility
    camera_id = serializers.CharField(source='camera.id', read_only=True)
    camera_name = serializers.CharField(source='camera.name', read_only=True)
    camera_rtsp_url = serializers.CharField(source='camera.rtsp_url', read_only=True)
    camera_rtsp_url_sub = serializers.CharField(source='camera.rtsp_url_sub', read_only=True, allow_null=True)
    camera_ip_address = serializers.CharField(source='camera.ip_address', read_only=True)
    camera_location = serializers.CharField(source='camera.location', read_only=True, allow_null=True)
    camera_type = serializers.CharField(source='camera.camera_type', read_only=True)
    camera_record_quality = serializers.CharField(source='camera.record_quality', read_only=True)
    
    class Meta:
        model = RecordingSchedule
        fields = [
            'id', 'camera_id', 'camera_name', 'camera_rtsp_url', 'camera_rtsp_url_sub',
            'camera_ip_address', 'camera_location', 'camera_type', 'camera_record_quality',
            'name', 'schedule_type',
            'start_time', 'end_time', 'start_date', 'end_date',
            'days_of_week', 'is_active', 'created_at', 'updated_at'
        ]


class RecordingStatusUpdateSerializer(serializers.Serializer):
    """Serializer for recording status updates from local client"""
    
    recording_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=['scheduled', 'recording', 'completed', 'failed', 'stopped'])
    progress = serializers.FloatField(required=False, help_text="Recording progress percentage (0-100)")
    frames_recorded = serializers.IntegerField(required=False)
    file_size = serializers.IntegerField(required=False)
    error_message = serializers.CharField(required=False, allow_blank=True)
    gcp_path = serializers.CharField(required=False, allow_blank=True)


class HeartbeatSerializer(serializers.Serializer):
    """Serializer for local client heartbeat"""
    
    client_id = serializers.UUIDField()
    active_recordings = serializers.IntegerField()
    available_space_gb = serializers.FloatField()
    last_upload = serializers.DateTimeField(required=False)
    system_info = serializers.DictField(required=False)
