"""
Views for CCTV camera management
"""

from django.http import StreamingHttpResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
import uuid
import json
import logging

from .models import Camera, RecordingSchedule, Recording, CameraAccess, LiveStream
from .serializers import (
    CameraSerializer, CameraListSerializer, RecordingScheduleSerializer,
    RecordingSerializer, RecordingListSerializer, CameraAccessSerializer,
    LiveStreamSerializer, CameraStreamUrlSerializer, RecordingControlSerializer,
    CameraRegistrationSerializer, ScheduleCreateSerializer
)
from .streaming import stream_manager, recording_manager, test_camera_connection, generate_frames
from .scheduler import recording_scheduler

logger = logging.getLogger(__name__)
User = get_user_model()


class CameraViewSet(viewsets.ModelViewSet):
    """ViewSet for managing cameras"""
    
    queryset = Camera.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CameraListSerializer
        return CameraSerializer
    
    def get_queryset(self):
        """Filter cameras based on user access"""
        user = self.request.user
        
        # Check if user is authenticated
        if not user.is_authenticated:
            return Camera.objects.none()
        
        # Admins see all cameras
        if user.is_staff or user.is_superuser:
            return Camera.objects.all()
        
        # Regular users see their own cameras and those they have access to
        return Camera.objects.filter(
            Q(created_by=user) | 
            Q(user_accesses__user=user, user_accesses__is_active=True)
        ).distinct()
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test camera connection"""
        camera = self.get_object()
        
        try:
            success, message = test_camera_connection(camera.rtsp_url)
            
            if success:
                camera.status = 'active'
                camera.last_seen = timezone.now()
            else:
                camera.status = 'error'
            
            camera.save()
            
            return Response({
                'success': success,
                'message': message,
                'status': camera.status
            })
            
        except Exception as e:
            logger.error(f"Error testing camera connection: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def stream(self, request, pk=None):
        """Stream live video from camera"""
        camera = self.get_object()
        quality = request.GET.get('quality', 'main')
        
        try:
            # Create live stream session
            session_id = str(uuid.uuid4())
            LiveStream.objects.create(
                camera=camera,
                user=request.user,
                session_id=session_id,
                client_ip=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Generate streaming response
            response = StreamingHttpResponse(
                generate_frames(camera, quality),
                content_type='multipart/x-mixed-replace; boundary=frame'
            )
            
            response['Cache-Control'] = 'no-cache, no-store, max-age=0, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = 'Thu, 01 Jan 1970 00:00:00 GMT'
            
            return response
            
        except Exception as e:
            logger.error(f"Error starting stream for camera {camera.name}: {str(e)}")
            return HttpResponse(f'Error: {str(e)}', status=500)
    
    @action(detail=True, methods=['post'])
    def start_recording(self, request, pk=None):
        """Start recording from camera"""
        camera = self.get_object()
        
        serializer = RecordingControlSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            recording = recording_manager.start_recording(
                camera=camera,
                duration_minutes=serializer.validated_data.get('duration_minutes'),
                recording_name=serializer.validated_data.get('recording_name'),
                user=request.user
            )
            
            return Response({
                'message': 'Recording started successfully',
                'recording_id': str(recording.id),
                'recording_name': recording.name
            })
            
        except Exception as e:
            logger.error(f"Error starting recording: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def stop_recording(self, request, pk=None):
        """Stop recording from camera"""
        camera = self.get_object()
        
        try:
            recording = recording_manager.stop_recording(camera.id)
            
            return Response({
                'message': 'Recording stopped successfully',
                'recording_id': str(recording.id),
                'recording_name': recording.name
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def quick_record(self, request, pk=None):
        """Start a quick 5-second recording"""
        camera = self.get_object()
        
        try:
            # Check if camera is already recording
            if recording_manager.is_recording(camera.id):
                return Response(
                    {'error': 'Camera is already recording. Stop current recording first.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Start 5-second recording
            recording = camera.auto_record_5min(user=request.user)
            
            if recording:
                return Response({
                    'message': 'Quick 5-second recording started successfully',
                    'recording_id': str(recording.id),
                    'recording_name': recording.name,
                    'duration_seconds': 5,
                    'estimated_end_time': (timezone.now() + timedelta(seconds=5)).isoformat()
                })
            else:
                return Response(
                    {'error': 'Failed to start recording'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Error starting quick recording: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def recording_status(self, request, pk=None):
        """Get current recording status for camera"""
        camera = self.get_object()
        
        try:
            is_recording = recording_manager.is_recording(camera.id)
            
            response_data = {
                'camera_id': str(camera.id),
                'camera_name': camera.name,
                'is_recording': is_recording,
                'recording_info': None
            }
            
            if is_recording:
                # Get active recording info
                recording_info = recording_manager.active_recordings.get(str(camera.id))
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
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Error getting recording status: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def recording_overview(self, request):
        """Get overview of all camera recording statuses"""
        try:
            cameras = self.get_queryset()
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
            
            return Response({
                'total_cameras': len(overview),
                'recording_cameras': sum(1 for c in overview if c['is_recording']),
                'online_cameras': sum(1 for c in overview if c['is_online']),
                'cameras': overview
            })
            
        except Exception as e:
            logger.error(f"Error getting recording overview: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """Register/setup a new camera with comprehensive options"""
        try:
            serializer = CameraRegistrationSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            
            # Test connection if requested
            if data.get('test_connection', True):
                success, message = test_camera_connection(data['rtsp_url'])
                if not success:
                    return Response({
                        'error': f'Camera connection failed: {message}',
                        'rtsp_url': data['rtsp_url']
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Prepare camera data for creation
            camera_data = {
                'name': data['name'],
                'description': data.get('description', f'Camera at {data.get("ip_address", "unknown")}'),
                'ip_address': data['ip_address'],
                'port': data.get('port', 554),
                'username': data.get('username'),
                'password': data.get('password'),
                'rtsp_url': data['rtsp_url'],
                'rtsp_url_sub': data.get('rtsp_url_sub'),
                'camera_type': data.get('camera_type', 'rtsp'),
                'location': data.get('location'),
                'auto_record': data.get('auto_record', False),
                'record_quality': data.get('record_quality', 'medium'),
            }
            
            # Create camera
            camera_serializer = CameraSerializer(data=camera_data, context={'request': request})
            if camera_serializer.is_valid():
                camera = camera_serializer.save()
                
                # Auto-start streaming for new cameras to ensure is_streaming = true
                try:
                    from .streaming import stream_manager
                    logger.info(f"Auto-starting stream for new camera: {camera.name}")
                    stream_manager.start_stream(camera, 'main')
                    logger.info(f"Stream started successfully for camera: {camera.name}")
                except Exception as e:
                    logger.warning(f"Failed to auto-start stream for camera {camera.name}: {str(e)}")
                    # Don't fail registration if streaming fails
                
                response_data = {
                    'message': 'Camera registered successfully',
                    'camera': {
                        'id': str(camera.id),
                        'name': camera.name,
                        'ip_address': camera.ip_address,
                        'rtsp_url': camera.rtsp_url,
                        'status': camera.status,
                        'location': camera.location
                    }
                }
                
                # Start test recording if requested
                if data.get('start_recording', False):
                    try:
                        recording = camera.auto_record_5min(user=request.user)
                        if recording:
                                                         response_data['recording'] = {
                                 'id': str(recording.id),
                                 'name': recording.name,
                                 'duration_seconds': 5,
                                 'estimated_end_time': (timezone.now() + timedelta(seconds=5)).isoformat()
                            }
                        else:
                            response_data['warning'] = 'Camera created but test recording failed to start'
                    except Exception as e:
                        response_data['warning'] = f'Camera created but test recording failed: {str(e)}'
                
                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                return Response(camera_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error in camera registration: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def auto_setup(self, request):
        """Legacy endpoint - use 'register' instead"""
        # Redirect to the new register endpoint for backward compatibility
        return self.register(request)
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RecordingScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing recording schedules"""
    
    serializer_class = RecordingScheduleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter schedules based on user access"""
        user = self.request.user
        
        if user.is_staff or user.is_superuser:
            return RecordingSchedule.objects.all()
        
        return RecordingSchedule.objects.filter(created_by=user)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a recording schedule"""
        schedule = self.get_object()
        
        try:
            schedule.is_active = True
            schedule.save()
            
            # Log activation with schedule ID and name
            logger.info(f"Schedule activated - ID: {schedule.id}, Name: '{schedule.name}', Camera: {schedule.camera.name}")
            
            # Optionally start the scheduler if it exists
            try:
                from .scheduler import recording_scheduler
                recording_scheduler.add_schedule(schedule)  # Use add_schedule instead of schedule_recording
            except ImportError:
                pass  # Scheduler not available
            except AttributeError:
                pass  # Method doesn't exist
            
            return Response({
                'message': f'Schedule "{schedule.name}" (ID: {schedule.id}) activated successfully',
                'schedule_id': str(schedule.id),
                'schedule_name': schedule.name,
                'is_active': schedule.is_active
            })
            
        except Exception as e:
            logger.error(f"Error activating schedule ID: {schedule.id}, Name: '{schedule.name}': {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a recording schedule"""
        schedule = self.get_object()
        
        try:
            schedule.is_active = False
            schedule.save()
            
            # Log deactivation with schedule ID and name
            logger.info(f"Schedule deactivated - ID: {schedule.id}, Name: '{schedule.name}', Camera: {schedule.camera.name}")
            
            # Optionally stop the scheduler if it exists
            try:
                from .scheduler import recording_scheduler
                recording_scheduler.remove_schedule(schedule.id)  # Use remove_schedule instead of unschedule_recording
            except ImportError:
                pass  # Scheduler not available
            except AttributeError:
                pass  # Method doesn't exist
            
            return Response({
                'message': f'Schedule "{schedule.name}" (ID: {schedule.id}) deactivated successfully',
                'schedule_id': str(schedule.id),
                'schedule_name': schedule.name,
                'is_active': schedule.is_active
            })
            
        except Exception as e:
            logger.error(f"Error deactivating schedule ID: {schedule.id}, Name: '{schedule.name}': {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def trigger_now(self, request, pk=None):
        """Manually trigger a scheduled recording immediately"""
        schedule = self.get_object()
        
        try:
            # Check if camera is already recording
            if recording_manager.is_recording(schedule.camera.id):
                return Response(
                    {'error': 'Camera is already recording. Stop current recording first.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Calculate duration from schedule times
            duration_minutes = None
            if schedule.start_time and schedule.end_time:
                duration_delta = timedelta(
                    hours=schedule.end_time.hour - schedule.start_time.hour,
                    minutes=schedule.end_time.minute - schedule.start_time.minute
                )
                duration_minutes = int(duration_delta.total_seconds() / 60)
            
            # Start recording
            recording_name = f"Manual Trigger - {schedule.name} - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
            recording = recording_manager.start_recording(
                camera=schedule.camera,
                duration_minutes=duration_minutes,
                recording_name=recording_name,
                user=request.user
            )
            
            return Response({
                'message': f'Recording triggered from schedule "{schedule.name}"',
                'recording_id': str(recording.id),
                'recording_name': recording.name,
                'duration_minutes': duration_minutes
            })
            
        except Exception as e:
            logger.error(f"Error triggering scheduled recording: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def active_schedules(self, request):
        """Get all active schedules"""
        try:
            active_schedules = self.get_queryset().filter(is_active=True)
            
            schedules_data = []
            for schedule in active_schedules:
                schedule_info = {
                    'id': str(schedule.id),
                    'name': schedule.name,
                    'camera_id': str(schedule.camera.id),
                    'camera_name': schedule.camera.name,
                    'schedule_type': schedule.schedule_type,
                    'start_time': schedule.start_time.strftime('%H:%M') if schedule.start_time else None,
                    'end_time': schedule.end_time.strftime('%H:%M') if schedule.end_time else None,
                    'days_of_week': schedule.days_of_week,
                    'next_run': None  # Could be calculated if scheduler is available
                }
                schedules_data.append(schedule_info)
            
            return Response({
                'total_active_schedules': len(schedules_data),
                'schedules': schedules_data
            })
            
        except Exception as e:
            logger.error(f"Error getting active schedules: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RecordingViewSet(viewsets.ModelViewSet):
    """ViewSet for managing recordings"""
    
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return RecordingListSerializer
        return RecordingSerializer
    
    def get_queryset(self):
        """Filter recordings based on user access"""
        user = self.request.user
        
        if user.is_staff or user.is_superuser:
            return Recording.objects.all()
        
        return Recording.objects.filter(created_by=user)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download a recording file"""
        recording = self.get_object()
        
        try:
            from django.http import FileResponse, Http404, HttpResponseRedirect, JsonResponse
            from .storage_service import storage_service
            import tempfile
            import os
            
            logger.info(f"Download request for recording {recording.id}: {recording.name}")
            
            # Check if file exists in storage
            if not recording.file_exists:
                logger.error(f"Recording file not found: {recording.file_path}")
                raise Http404("Recording file not found")
            
            # If using GCP storage, redirect to signed URL for direct download
            if recording.storage_type == 'gcp' or getattr(settings, 'GCP_STORAGE_USE_GCS', False):
                logger.info(f"Generating GCP download URL for: {recording.file_path}")
                
                # Generate signed URL with longer expiration for downloads (2 hours)
                signed_url = storage_service.get_file_url(
                    recording.file_path, 
                    signed=True, 
                    expiration_minutes=120
                )
                
                if signed_url:
                    logger.info(f"✅ Generated download URL for {recording.name}")
                    
                    # Add download headers to the redirect response
                    response = HttpResponseRedirect(signed_url)
                    response['Content-Disposition'] = f'attachment; filename="{recording.name}.{recording.file_path.split(".")[-1]}"'
                    return response
                else:
                    logger.error(f"Failed to generate download URL for {recording.file_path}")
                    return JsonResponse({
                        'error': 'Unable to generate download URL from GCP storage',
                        'recording_id': str(recording.id),
                        'file_path': recording.file_path
                    }, status=500)
            
            # For local storage, serve file directly
            temp_file_path = storage_service.download_file_to_temp(recording.file_path)
            if not temp_file_path:
                logger.error(f"Failed to get temp file for {recording.file_path}")
                raise Http404("Recording file not found")
            
            # Determine content type and filename based on actual file extension
            file_extension = os.path.splitext(recording.file_path)[1].lower()
            
            # Map file extensions to content types
            content_type_map = {
                '.mp4': 'video/mp4',
                '.avi': 'video/x-msvideo',
                '.mov': 'video/quicktime',
                '.mkv': 'video/x-matroska'
            }
            
            content_type = content_type_map.get(file_extension, 'video/mp4')  # Default to MP4
            safe_filename = f"{recording.name}{file_extension}"  # Use actual extension
            
            # Create file response
            response = FileResponse(
                open(temp_file_path, 'rb'),
                content_type=content_type,
                as_attachment=True,
                filename=safe_filename
            )
            
            # Clean up temp file after response
            def cleanup_temp_file():
                try:
                    os.remove(temp_file_path)
                except:
                    pass
            
            response.closed = cleanup_temp_file
            
            return response
            
        except Exception as e:
            logger.error(f"Error downloading recording {recording.id}: {str(e)}")
            return Response(
                {
                    'error': str(e),
                    'recording_id': str(recording.id),
                    'storage_type': recording.storage_type,
                    'file_path': recording.file_path
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_content_type_for_file(self, file_path):
        """Get content type based on file extension"""
        file_extension = os.path.splitext(file_path)[1].lower()
        content_type_map = {
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska',
            '.webm': 'video/webm',
            '.flv': 'video/x-flv'
        }
        return content_type_map.get(file_extension, 'video/mp4')
    
    @action(detail=True, methods=['get'])
    def stream(self, request, pk=None):
        """Stream a recording file for viewing"""
        recording = self.get_object()
        
        try:
            from django.http import FileResponse, Http404, HttpResponseRedirect, JsonResponse
            from .storage_service import storage_service
            import os
            
            logger.info(f"Stream request for recording {recording.id}: {recording.name}")
            
            # Check if file exists in storage
            if not recording.file_exists:
                logger.error(f"Recording file not found for streaming: {recording.file_path}")
                raise Http404("Recording file not found")
            
            # If using GCP storage, redirect to signed URL for streaming
            if recording.storage_type == 'gcp' or getattr(settings, 'GCP_STORAGE_USE_GCS', False):
                logger.info(f"Generating GCP streaming URL for: {recording.file_path}")
                
                # Generate signed URL with longer expiration for streaming (2 hours)
                signed_url = storage_service.get_file_url(
                    recording.file_path, 
                    signed=True, 
                    expiration_minutes=120
                )
                
                if signed_url:
                    logger.info(f"✅ Generated streaming URL for {recording.name}")
                    
                    # Create response with proper headers for video streaming
                    response = HttpResponseRedirect(signed_url)
                    response['Accept-Ranges'] = 'bytes'
                    response['Content-Type'] = self._get_content_type_for_file(recording.file_path)
                    
                    # Add CORS headers for browser compatibility
                    response['Access-Control-Allow-Origin'] = '*'
                    response['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'
                    response['Access-Control-Allow-Headers'] = 'Range, Content-Type'
                    
                    return response
                else:
                    logger.error(f"Failed to generate streaming URL for {recording.file_path}")
                    return JsonResponse({
                        'error': 'Unable to generate streaming URL from GCP storage',
                        'recording_id': str(recording.id),
                        'file_path': recording.file_path
                    }, status=500)
            
            # For local storage, stream file directly
            temp_file_path = storage_service.download_file_to_temp(recording.file_path)
            if not temp_file_path:
                raise Http404("Recording file not found")
            
            # Determine content type based on actual file extension
            file_extension = os.path.splitext(recording.file_path)[1].lower()
            content_type_map = {
                '.mp4': 'video/mp4',
                '.avi': 'video/x-msvideo',
                '.mov': 'video/quicktime',
                '.mkv': 'video/x-matroska'
            }
            content_type = content_type_map.get(file_extension, 'video/mp4')  # Default to MP4
            
            # Create file response for streaming
            response = FileResponse(
                open(temp_file_path, 'rb'),
                content_type=content_type
            )
            
            # Add headers for video streaming
            response['Accept-Ranges'] = 'bytes'
            file_size = storage_service.get_file_size(recording.file_path)
            if file_size:
                response['Content-Length'] = file_size
            
            # Clean up temp file after response
            def cleanup_temp_file():
                try:
                    os.remove(temp_file_path)
                except:
                    pass
            
            response.closed = cleanup_temp_file
            
            return response
            
        except Exception as e:
            logger.error(f"Error streaming recording {recording.id}: {str(e)}")
            return Response(
                {
                    'error': str(e),
                    'recording_id': str(recording.id),
                    'storage_type': recording.storage_type,
                    'file_path': recording.file_path
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get recording statistics"""
        try:
            recordings = self.get_queryset()
            
            total_recordings = recordings.count()
            completed_recordings = recordings.filter(status='completed').count()
            failed_recordings = recordings.filter(status='failed').count()
            recording_recordings = recordings.filter(status='recording').count()
            
            total_size = sum(r.file_size for r in recordings if r.file_size)
            total_duration = sum(
                (r.duration.total_seconds() for r in recordings if r.duration), 
                start=0
            )
            
            return Response({
                'total_recordings': total_recordings,
                'completed_recordings': completed_recordings,
                'failed_recordings': failed_recordings,
                'active_recordings': recording_recordings,
                'total_size_bytes': total_size,
                'total_size_gb': round(total_size / (1024**3), 2),
                'total_duration_seconds': total_duration,
                'total_duration_hours': round(total_duration / 3600, 2),
                'success_rate': round((completed_recordings / total_recordings * 100), 2) if total_recordings > 0 else 0
            })
            
        except Exception as e:
            logger.error(f"Error getting recording stats: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CameraAccessViewSet(viewsets.ModelViewSet):
    """ViewSet for managing camera access permissions"""
    
    serializer_class = CameraAccessSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter access records based on user permissions"""
        user = self.request.user
        
        if user.is_staff or user.is_superuser:
            return CameraAccess.objects.all()
        
        return CameraAccess.objects.filter(camera__created_by=user)


class LiveStreamViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing live stream sessions"""
    
    serializer_class = LiveStreamSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter live streams based on user access"""
        user = self.request.user
        
        if user.is_staff or user.is_superuser:
            return LiveStream.objects.all()
        
        return LiveStream.objects.filter(user=user)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start a live stream for a camera"""
        try:
            from .models import Camera
            from .streaming import stream_manager
            from django.utils import timezone
            import uuid
            
            # Get the camera
            camera = get_object_or_404(Camera, id=pk)
            
            # Check if user has access to this camera
            if not self._check_camera_access(request.user, camera):
                return Response(
                    {'error': 'Access denied to this camera'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if camera is online
            if not camera.is_online:
                return Response(
                    {'error': 'Camera is offline or not accessible'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if there's already an active stream for this camera
            existing_stream = LiveStream.objects.filter(
                camera=camera,
                is_active=True
            ).first()
            
            if existing_stream:
                return Response(
                    {'error': 'Live stream is already active for this camera'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get stream quality from request
            quality = request.data.get('quality', 'main')
            if quality not in ['main', 'sub']:
                quality = 'main'
            
            # Check if sub stream is available
            if quality == 'sub' and not camera.rtsp_url_sub:
                return Response(
                    {'error': 'Sub stream not available for this camera'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Start the stream using streaming manager
            try:
                stream_info = stream_manager.start_stream(camera, quality)
                if not stream_info:
                    return Response(
                        {'error': 'Failed to start stream'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            except Exception as e:
                logger.error(f"Error starting stream: {str(e)}")
                return Response(
                    {'error': f'Stream error: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
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
            
            logger.info(f"Live stream started for camera {camera.name} by user {request.user.email}")
            
            return Response({
                'success': True,
                'message': 'Live stream started successfully',
                'stream_info': {
                    'session_id': session_id,
                    'camera_id': str(camera.id),
                    'camera_name': camera.name,
                    'quality': quality,
                    'stream_url': f"/v0/api/cctv/cameras/{camera.id}/stream/?quality={quality}",
                    'rtsp_url': camera.get_stream_url(quality),
                    'start_time': live_stream.start_time.isoformat()
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error starting live stream: {str(e)}")
            return Response(
                {'error': f'Internal server error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """Stop a live stream for a camera"""
        try:
            from .models import Camera
            from .streaming import stream_manager
            from django.utils import timezone
            
            # Get the camera
            camera = get_object_or_404(Camera, id=pk)
            
            # Check if user has access to this camera
            if not self._check_camera_access(request.user, camera):
                return Response(
                    {'error': 'Access denied to this camera'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Find active stream for this camera
            active_stream = LiveStream.objects.filter(
                camera=camera,
                is_active=True
            ).first()
            
            if not active_stream:
                return Response(
                    {'error': 'No active stream found for this camera'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
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
            
            logger.info(f"Live stream stopped for camera {camera.name} by user {request.user.email}")
            
            return Response({
                'success': True,
                'message': 'Live stream stopped successfully',
                'stream_info': {
                    'session_id': active_stream.session_id,
                    'camera_id': str(camera.id),
                    'camera_name': camera.name,
                    'duration_seconds': (active_stream.end_time - active_stream.start_time).total_seconds(),
                    'stop_time': active_stream.end_time.isoformat()
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error stopping live stream: {str(e)}")
            return Response(
                {'error': f'Internal server error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _check_camera_access(self, user, camera):
        """Check if user has access to the camera"""
        # Superusers and staff have access to all cameras
        if user.is_staff or user.is_superuser:
            return True
        
        # Check if camera is public
        if camera.is_public:
            return True
        
        # Check specific camera access
        try:
            access = CameraAccess.objects.get(
                user=user,
                camera=camera,
                is_active=True
            )
            return True
        except CameraAccess.DoesNotExist:
            return False