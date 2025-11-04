"""
RTSP Streaming and Recording functionality for CCTV cameras
"""

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    # Create dummy cv2 module for when OpenCV is not available
    class DummyCV2:
        CAP_PROP_BUFFERSIZE = 0
        CAP_PROP_FPS = 0
        CAP_PROP_FRAME_WIDTH = 0
        CAP_PROP_FRAME_HEIGHT = 0
        
        def VideoCapture(self, *args, **kwargs):
            return DummyVideoCapture()
        
        def VideoWriter(self, *args, **kwargs):
            return DummyVideoWriter()
        
        def VideoWriter_fourcc(self, *args, **kwargs):
            return 0
        
        def imencode(self, *args, **kwargs):
            return False, b''
    
    class DummyVideoCapture:
        def read(self):
            return False, None
        def get(self, prop):
            return 0
        def set(self, prop, value):
            return True
        def release(self):
            pass
    
    class DummyVideoWriter:
        def write(self, frame):
            pass
        def release(self):
            pass
    
    cv2 = DummyCV2()

import threading
import time
import os
import uuid
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models import Camera, Recording, LiveStream
import logging

logger = logging.getLogger(__name__)


class RTSPStreamManager:
    """Manages RTSP streams for cameras"""
    
    def __init__(self):
        self.active_streams = {}
        self.recording_streams = {}
        self.stream_locks = {}
        self.health_check_interval = 30  # seconds
        self.last_health_check = {}
    
    def get_stream_key(self, camera_id, quality='main'):
        """Generate a unique key for the stream"""
        return f"{camera_id}_{quality}"
    
    def start_stream(self, camera, quality='main'):
        """Start a video stream for a camera"""
        stream_key = self.get_stream_key(camera.id, quality)
        
        if stream_key in self.active_streams:
            return self.active_streams[stream_key]
        
        # Get the appropriate stream URL
        stream_url = camera.get_stream_url(quality)
        
        try:
            # Import OpenCV configuration
            from .opencv_config import (configure_video_capture, test_camera_connection_robust, 
                                       check_opencv_compatibility, optimize_capture_for_streaming)
            
            # Check OpenCV compatibility on first use
            check_opencv_compatibility()
            
            # Test connection first with robust method
            connection_ok, connection_msg = test_camera_connection_robust(stream_url)
            if not connection_ok:
                raise Exception(f"Cannot connect to camera stream: {connection_msg}")
            
            # Create video capture object with proper backend
            cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
            
            # Configure with optimal settings for streaming
            optimize_capture_for_streaming(cap, stream_url)
            
            # Test if the stream is accessible
            ret, frame = cap.read()
            if not ret or frame is None:
                cap.release()
                raise Exception(f"Cannot read frames from camera stream: {stream_url}")
            
            # Store the stream
            self.active_streams[stream_key] = {
                'capture': cap,
                'camera': camera,
                'quality': quality,
                'last_frame': frame,
                'last_update': timezone.now(),
                'viewers': 0
            }
            
            logger.info(f"Started stream {stream_key} for camera {camera.name}")
            
            # Start the frame reading thread
            thread = threading.Thread(
                target=self._update_stream_frames,
                args=(stream_key,),
                daemon=True
            )
            thread.start()
            
            # Update camera status
            camera.status = 'active'
            camera.is_online = True
            camera.is_streaming = True
            camera.last_seen = timezone.now()
            camera.save(update_fields=['status', 'is_online', 'is_streaming', 'last_seen'])
            
            return self.active_streams[stream_key]
            
        except Exception as e:
            logger.error(f"Error starting stream for camera {camera.name}: {str(e)}")
            camera.status = 'error'
            camera.save()
            raise
    
    def _update_stream_frames(self, stream_key):
        """Continuously update frames for a stream with improved error handling"""
        stream_info = self.active_streams.get(stream_key)
        if not stream_info:
            return
        
        cap = stream_info['capture']
        camera = stream_info['camera']
        consecutive_failures = 0
        max_failures = 10
        frame_count = 0
        
        logger.info(f"Starting frame update thread for camera {camera.name}")
        
        while stream_key in self.active_streams:
            try:
                ret, frame = cap.read()
                if ret and frame is not None:
                    # Successfully got a frame
                    stream_info['last_frame'] = frame
                    stream_info['last_update'] = timezone.now()
                    stream_info['frame_count'] = stream_info.get('frame_count', 0) + 1
                    consecutive_failures = 0
                    frame_count += 1
                    
                    # Update camera last seen every 30 seconds
                    if frame_count % 750 == 0:  # ~30 seconds at 25fps
                        camera.last_seen = timezone.now()
                        camera.save(update_fields=['last_seen'])
                        
                    # Control frame rate to prevent overwhelming
                    time.sleep(0.04)  # Target ~25 FPS
                    
                else:
                    consecutive_failures += 1
                    logger.warning(f"Failed to read frame from camera {camera.name} (failure {consecutive_failures}/{max_failures})")
                    
                    if consecutive_failures >= max_failures:
                        logger.error(f"Too many consecutive failures for camera {camera.name}, stopping stream")
                        camera.status = 'error'
                        camera.save(update_fields=['status'])
                        break
                    
                    time.sleep(0.5)  # Wait before retrying
                    
            except Exception as e:
                consecutive_failures += 1
                logger.error(f"Error reading frame from camera {camera.name}: {str(e)} (failure {consecutive_failures}/{max_failures})")
                
                if consecutive_failures >= max_failures:
                    logger.error(f"Too many consecutive errors for camera {camera.name}, stopping stream")
                    camera.status = 'error'
                    camera.is_streaming = False
                    camera.save(update_fields=['status', 'is_streaming'])
                    break
                    
                time.sleep(1)  # Wait longer after errors
        
        # Clean up
        try:
            cap.release()
        except Exception as cleanup_error:
            logger.error(f"Error releasing capture for camera {camera.name}: {str(cleanup_error)}")
            
        logger.info(f"Stream thread ended for camera {camera.name} (processed {frame_count} frames)")
    
    def stop_stream(self, camera_id, quality='main'):
        """Stop a video stream"""
        stream_key = self.get_stream_key(camera_id, quality)
        
        if stream_key in self.active_streams:
            stream_info = self.active_streams.pop(stream_key)
            stream_info['capture'].release()
            
            # Update camera streaming status
            try:
                camera = stream_info['camera']
                camera.is_streaming = False
                camera.save(update_fields=['is_streaming'])
                logger.info(f"Updated camera {camera.name} is_streaming=False")
            except Exception as e:
                logger.error(f"Error updating camera streaming status: {str(e)}")
            
            logger.info(f"Stopped stream {stream_key}")
    
    def get_frame(self, camera_id, quality='main'):
        """Get the latest frame from a stream"""
        stream_key = self.get_stream_key(camera_id, quality)
        
        if stream_key not in self.active_streams:
            return None
        
        stream_info = self.active_streams[stream_key]
        return stream_info['last_frame']
    
    def add_viewer(self, camera_id, quality='main'):
        """Add a viewer to a stream"""
        stream_key = self.get_stream_key(camera_id, quality)
        
        if stream_key in self.active_streams:
            self.active_streams[stream_key]['viewers'] += 1
    
    def remove_viewer(self, camera_id, quality='main'):
        """Remove a viewer from a stream"""
        stream_key = self.get_stream_key(camera_id, quality)
        
        if stream_key in self.active_streams:
            self.active_streams[stream_key]['viewers'] -= 1
            
            # Stop stream if no viewers
            if self.active_streams[stream_key]['viewers'] <= 0:
                self.stop_stream(camera_id, quality)
    
    def recover_stream(self, camera_id, quality='main'):
        """Attempt to recover a failed stream with enhanced retry logic"""
        stream_key = self.get_stream_key(camera_id, quality)
        
        if stream_key in self.active_streams:
            # Stop the current failed stream
            self.stop_stream(camera_id, quality)
        
        try:
            # Get the camera and attempt to restart
            camera = Camera.objects.get(id=camera_id)
            logger.info(f"Attempting to recover stream for camera {camera.name}")
            
            # Test connection first
            from .opencv_config import test_camera_connection_robust
            stream_url = camera.get_stream_url(quality)
            
            connection_ok, connection_msg = test_camera_connection_robust(stream_url, max_attempts=3)
            if not connection_ok:
                logger.error(f"Cannot recover stream - connection test failed: {connection_msg}")
                camera.status = 'error'
                camera.save(update_fields=['status'])
                return None
            
            # Wait a moment before retrying
            time.sleep(2)
            
            # Try to start the stream again
            stream_info = self.start_stream(camera, quality)
            if stream_info:
                logger.info(f"Successfully recovered stream for camera {camera.name}")
                camera.status = 'active'
                camera.save(update_fields=['status'])
            
            return stream_info
            
        except Exception as e:
            logger.error(f"Failed to recover stream for camera {camera_id}: {str(e)}")
            try:
                camera = Camera.objects.get(id=camera_id)
                camera.status = 'error'
                camera.save(update_fields=['status'])
            except:
                pass
            return None
    
    def get_stream_health(self, camera_id, quality='main'):
        """Get the health status of a stream"""
        stream_key = self.get_stream_key(camera_id, quality)
        
        if stream_key not in self.active_streams:
            return {'status': 'inactive', 'error': 'Stream not found'}
        
        stream_info = self.active_streams[stream_key]
        camera = stream_info['camera']
        
        # Check if stream is healthy
        last_update = stream_info.get('last_update')
        if last_update:
            time_since_update = (timezone.now() - last_update).total_seconds()
            if time_since_update > 30:  # More than 30 seconds since last frame
                return {
                    'status': 'unhealthy',
                    'error': f'No frames for {time_since_update:.1f} seconds',
                    'last_update': last_update.isoformat(),
                    'viewers': stream_info.get('viewers', 0)
                }
        
        return {
            'status': 'healthy',
            'last_update': last_update.isoformat() if last_update else None,
            'viewers': stream_info.get('viewers', 0),
            'frame_count': stream_info.get('frame_count', 0)
        }
    
    def is_stream_active(self, camera_id, quality='main'):
        """Check if a stream is currently active and healthy"""
        stream_key = self.get_stream_key(camera_id, quality)
        
        if stream_key not in self.active_streams:
            return False
        
        stream_info = self.active_streams[stream_key]
        
        # Check if capture object is still valid
        if 'capture' not in stream_info:
            return False
        
        cap = stream_info['capture']
        if cap is None:
            return False
        
        # Check if we can still read from the stream
        try:
            ret, frame = cap.read()
            if not ret or frame is None:
                return False
            
            # Update the last frame and frame count
            stream_info['last_frame'] = frame
            stream_info['last_update'] = timezone.now()
            stream_info['frame_count'] = stream_info.get('frame_count', 0) + 1
            
            return True
        except Exception:
            return False


class RTSPRecordingManager:
    """Manages video recordings from RTSP streams"""
    
    def __init__(self):
        self.active_recordings = {}
        self.recording_locks = {}
    
    def start_recording(self, camera, duration_minutes=None, recording_name=None, user=None, is_scheduled=False, schedule_id=None):
        """Start recording from a camera"""
        if str(camera.id) in self.active_recordings:
            raise Exception("Recording already in progress for this camera")
        
        # Create recording directory if it doesn't exist
        camera_name_safe = "".join(c for c in camera.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        if not camera_name_safe:  # Fallback if camera name has no valid characters
            camera_name_safe = f"Camera_{str(camera.id)[:8]}"
            
        recording_dir = os.path.join(settings.MEDIA_ROOT, 'recordings', str(camera.id))
        os.makedirs(recording_dir, exist_ok=True)
        logger.info(f"📁 Recording directory created/verified: {recording_dir}")
        
        # Generate filename with safe camera name (extension will be determined by codec)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Add SCHEDULED prefix to filename if recording is from a schedule
        if is_scheduled:
            filename_base = f"SCHEDULED_{camera_name_safe}_{timestamp}"
        else:
            filename_base = f"{camera_name_safe}_{timestamp}"
        
        # Base file path without extension (codec will determine extension)
        file_path = os.path.join(recording_dir, filename_base)
        
        # Create recording record (file_path will be updated after codec selection)
        recording_name = recording_name or f"Recording {timestamp}"
        recording = Recording.objects.create(
            camera=camera,
            name=recording_name,
            file_path=os.path.join('recordings', str(camera.id), f"{filename_base}.tmp"),  # Temporary path
            start_time=timezone.now(),
            status='recording',
            created_by=user or camera.created_by
        )
        
        try:
            if not OPENCV_AVAILABLE:
                raise Exception("OpenCV is not available. Cannot record video.")
            
            # Import OpenCV configuration
            from .opencv_config import configure_video_capture, test_camera_connection_robust, check_opencv_compatibility
            
            # Check OpenCV compatibility on first use
            check_opencv_compatibility()
            
            # Test connection first
            connection_ok, connection_msg = test_camera_connection_robust(camera.rtsp_url)
            if not connection_ok:
                raise Exception(f"Cannot connect to camera for recording: {connection_msg}")
            
            # Setup video capture with optimized options
            cap = cv2.VideoCapture(camera.rtsp_url, cv2.CAP_FFMPEG)
            configure_video_capture(cap, camera.rtsp_url)
            
            # Additional optimizations for video recording
            try:
                # Try to set capture to prefer MP4V format (most reliable)
                cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'mp4v'))
                logger.debug("Set capture FOURCC to mp4v")
            except Exception as fourcc_error:
                logger.debug(f"Could not set capture FOURCC: {str(fourcc_error)}")
                
            # Set additional properties for better video compatibility
            try:
                # Set pixel format if available (helps with video encoding)
                if hasattr(cv2, 'CAP_PROP_FORMAT'):
                    cap.set(cv2.CAP_PROP_FORMAT, cv2.CAP_MODE_BGR)
            except Exception as format_error:
                logger.debug(f"Could not set pixel format: {str(format_error)}")
            
            # Test if we can read a frame first
            ret, test_frame = cap.read()
            if not ret or test_frame is None:
                cap.release()
                raise Exception(f"Cannot read frames from camera stream: {camera.rtsp_url}")
            
            # Get video properties
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            if fps <= 0 or fps > 60:
                fps = 25  # Default to 25 FPS if invalid
                
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # If properties are invalid, use test frame dimensions
            if width <= 0 or height <= 0:
                height, width = test_frame.shape[:2]
            
            logger.info(f"Recording properties: {width}x{height} @ {fps}fps")
            
            # Use cached working codecs or test them once
            from .opencv_config import get_cached_working_codecs, clear_codec_cache
            
            # Clear codec cache periodically to ensure we use updated priorities
            # This ensures H.264 gets priority for browser compatibility
            working_codecs = get_cached_working_codecs(width, height, fps)
            
            if not working_codecs:
                logger.warning("No working codecs found, using emergency fallback")
                # Emergency fallback - try basic codecs without testing
                working_codecs = [
                    ('MJPG', '.avi', 'Motion JPEG AVI - Emergency fallback'),
                    ('mp4v', '.mp4', 'MPEG-4 MP4 - Emergency fallback'),
                    ('XVID', '.avi', 'Xvid AVI - Emergency fallback')
                ]
            
            out = None
            used_codec = None
            used_extension = None
            
            # Use the first working codec directly (since they were already tested)
            codec, extension, description = working_codecs[0]
            logger.info(f"🎬 Using codec: {codec} ({description}) - {extension} format")
            
            fourcc = cv2.VideoWriter_fourcc(*codec)
            final_file_path = file_path + extension
            
            # Create VideoWriter with optimizations for MP4 codecs
            if codec in ['mp4v', 'MJPG', 'XVID']:
                logger.info(f"🎯 Applying MP4 optimizations for browser compatibility")
                # Use isColor=True to ensure proper color encoding
                out = cv2.VideoWriter(final_file_path, fourcc, fps, (width, height), True)
            else:
                out = cv2.VideoWriter(final_file_path, fourcc, fps, (width, height))
            
            if out.isOpened():
                used_codec = codec
                used_extension = extension
                file_path = final_file_path  # Update file path
                logger.info(f"✅ Successfully initialized recording with {codec}")
            else:
                logger.warning(f"Failed to open writer with first codec {codec}, trying fallback...")
                out.release()
                out = None
                
                # If first codec fails, try the rest as fallback
                for codec, extension, description in working_codecs[1:]:
                    try:
                        logger.info(f"🎬 Trying fallback codec: {codec} ({description})")
                        fourcc = cv2.VideoWriter_fourcc(*codec)
                        final_file_path = file_path.rsplit('.', 1)[0] + extension
                        
                        # Apply MP4 optimizations for fallback codecs too
                        if codec in ['mp4v', 'MJPG', 'XVID']:
                            logger.info(f"🎯 Applying MP4 optimizations for fallback codec")
                            out = cv2.VideoWriter(final_file_path, fourcc, fps, (width, height), True)
                        else:
                            out = cv2.VideoWriter(final_file_path, fourcc, fps, (width, height))
                        
                        if out.isOpened():
                            used_codec = codec
                            used_extension = extension
                            file_path = final_file_path
                            logger.info(f"✅ Fallback codec {codec} successful")
                            break
                        else:
                            out.release()
                            out = None
                            
                    except Exception as e:
                        logger.warning(f"❌ Fallback codec {codec} failed: {str(e)}")
                        continue
            
            if out is None:
                cap.release()
                raise Exception("Could not initialize video writer with any codec")
            
            # Update recording instance with initial file path and codec info
            try:
                # Store local file path initially (will upload to GCP after recording completes)
                relative_file_path = os.path.relpath(file_path, settings.MEDIA_ROOT)
                recording.file_path = relative_file_path
                recording.storage_type = 'local'  # Initially local, will update after GCP upload
                recording.codec = used_codec
                recording.resolution = f"{width}x{height}"
                recording.frame_rate = fps
                recording.save(update_fields=['file_path', 'storage_type', 'codec', 'resolution', 'frame_rate'])
                
                logger.info(f"📁 Recording file path set: {relative_file_path}")
                logger.info(f"🎬 Recording details: {width}x{height} @ {fps}fps using {used_codec} format {used_extension}")
                    
            except Exception as db_error:
                logger.error(f"Error updating recording database record: {str(db_error)}")
                # Continue with recording even if database update fails
            
            # Store recording info
            self.active_recordings[str(camera.id)] = {
                'recording': recording,
                'capture': cap,
                'writer': out,
                'start_time': timezone.now(),
                'duration_minutes': duration_minutes,
                'file_path': file_path,
                'frame_count': 0,
                'codec': used_codec
            }
            
            # Start recording thread
            thread = threading.Thread(
                target=self._record_frames,
                args=(str(camera.id),),
                daemon=True
            )
            thread.start()
            
            logger.info(f"Started recording for camera {camera.name}")
            return recording
            
        except Exception as e:
            recording.status = 'failed'
            recording.error_message = str(e)
            recording.save()
            logger.error(f"Error starting recording for camera {camera.name}: {str(e)}")
            raise
    
    def _record_frames(self, camera_id):
        """Record frames in a separate thread"""
        recording_info = self.active_recordings.get(camera_id)
        if not recording_info:
            return
        
        cap = recording_info['capture']
        out = recording_info['writer']
        recording = recording_info['recording']
        start_time = recording_info['start_time']
        duration_minutes = recording_info['duration_minutes']
        
        try:
            consecutive_failures = 0
            max_failures = 30  # Allow 30 consecutive failures before giving up
            frames_written = 0
            
            while camera_id in self.active_recordings:
                try:
                    # Use timeout for frame reading to prevent hanging
                    from .opencv_config import get_frame_with_timeout
                    ret, frame = get_frame_with_timeout(cap, timeout_ms=2000)
                    
                    if ret and frame is not None:
                        try:
                            # Verify frame is valid before writing
                            if frame.size > 0 and len(frame.shape) == 3:
                                out.write(frame)
                                frames_written += 1
                                recording_info['frame_count'] = frames_written
                                consecutive_failures = 0  # Reset failure count on success
                                
                                # Log progress every 100 frames (less frequent logging)
                                if frames_written % 100 == 0:
                                    logger.info(f"Recording {recording.id}: {frames_written} frames written")
                                
                                # Check if duration limit reached
                                if duration_minutes:
                                    elapsed = (timezone.now() - start_time).total_seconds() / 60
                                    if elapsed >= duration_minutes:
                                        logger.info(f"Recording {recording.id} reached duration limit: {duration_minutes} minutes")
                                        break
                            else:
                                logger.warning(f"Invalid frame received for recording {recording.id}")
                                consecutive_failures += 1
                                
                        except Exception as e:
                            logger.error(f"Error writing frame for recording {recording.id}: {str(e)}")
                            consecutive_failures += 1
                    else:
                        consecutive_failures += 1
                        if consecutive_failures % 10 == 0:  # Log every 10th failure
                            logger.warning(f"Failed to read frame for recording {recording.id} (failure #{consecutive_failures})")
                        
                        if consecutive_failures >= max_failures:
                            logger.error(f"Too many consecutive failures ({consecutive_failures}) for recording {recording.id}")
                            break
                        
                        time.sleep(0.1)  # Brief pause before retry
                        
                except Exception as frame_error:
                    logger.error(f"Frame processing error for recording {recording.id}: {str(frame_error)}")
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        break
                    time.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"Critical error during recording {recording.id}: {str(e)}")
            recording.status = 'failed'
            recording.error_message = str(e)
        finally:
            # Ensure proper cleanup
            try:
                if cap:
                    cap.release()
            except Exception as e:
                logger.error(f"Error releasing capture for recording {recording.id}: {str(e)}")
            
            try:
                if out:
                    out.release()
            except Exception as e:
                logger.error(f"Error releasing writer for recording {recording.id}: {str(e)}")
            
            # Update recording status
            recording.end_time = timezone.now()
            recording.duration = recording.end_time - recording.start_time
            
            # Get file size and validate recording
            file_path = recording_info.get('file_path', '')
            if file_path and os.path.exists(file_path):
                try:
                    file_size = os.path.getsize(file_path)
                    recording.file_size = file_size
                    
                    # Check if we actually recorded something meaningful
                    if file_size > 1000 and frames_written > 10:  # At least 1KB and 10 frames
                        recording.status = 'completed'
                        logger.info(f"✅ Recording {recording.id} completed successfully: {file_size} bytes, {frames_written} frames")
                        
                        # CRITICAL: Upload to GCP immediately after recording completion
                        upload_success = self._upload_completed_recording(recording, file_path)
                        
                        # Log upload result
                        if upload_success:
                            logger.info(f"🚀 Recording {recording.id} successfully uploaded to GCP")
                        else:
                            logger.warning(f"⚠️ Recording {recording.id} upload failed, will retry via background sync")
                        
                    else:
                        recording.status = 'failed'
                        recording.error_message = f"Recording too small: {file_size} bytes, {frames_written} frames"
                        logger.warning(f"❌ Recording {recording.id} failed: {recording.error_message}")
                except Exception as e:
                    logger.error(f"Error checking file size for recording {recording.id}: {str(e)}")
                    recording.status = 'failed'
                    recording.error_message = f"File access error: {str(e)}"
            else:
                recording.status = 'failed'
                recording.error_message = "Recording file not found"
                logger.error(f"❌ Recording {recording.id} failed: file not found at {file_path}")
            
            # Update recording properties
            if frames_written > 0 and recording.duration and recording.duration.total_seconds() > 0:
                recording.frame_rate = frames_written / recording.duration.total_seconds()
            
            # Save recording with error handling
            try:
                recording.save()
                logger.info(f"📝 Recording {recording.id} database record updated")
            except Exception as e:
                logger.error(f"Error saving recording {recording.id}: {str(e)}")
            
            # Handle 'once' schedule deactivation after successful recording completion
            if recording.schedule and recording.schedule.schedule_type == 'once' and recording.status == 'completed':
                try:
                    if recording.schedule.is_active:
                        logger.info(f"Deactivating 'once' schedule '{recording.schedule.name}' (ID: {recording.schedule.id}) after successful video storage")
                        recording.schedule.is_active = False
                        recording.schedule.save()
                        
                        # Remove from active jobs in scheduler if available
                        try:
                            from .scheduler import recording_scheduler
                            if hasattr(recording_scheduler, 'remove_schedule'):
                                recording_scheduler.remove_schedule(recording.schedule.id)
                        except (ImportError, AttributeError) as e:
                            logger.debug(f"Scheduler not available or method missing: {str(e)}")
                except Exception as e:
                    logger.error(f"Error handling schedule deactivation: {str(e)}")
            
            # Remove from active recordings
            try:
                if camera_id in self.active_recordings:
                    del self.active_recordings[camera_id]
                logger.info(f"🏁 Recording completed for camera {recording.camera.name}")
            except Exception as e:
                logger.error(f"Error cleaning up active recording: {str(e)}")
    
    def _upload_completed_recording(self, recording, local_file_path):
        """Upload completed recording to cloud storage (AWS S3 or GCP) if enabled"""
        upload_success = False
        
        try:
            from .storage_service import storage_service
            from django.conf import settings
            import time
            
            # Check which cloud storage backend is configured
            cloud_backend = getattr(settings, 'CLOUD_STORAGE_BACKEND', 'LOCAL').upper()
            
            # If no cloud storage is configured, keep local
            if cloud_backend == 'LOCAL':
                logger.debug(f"Cloud storage not enabled, keeping recording {recording.id} in local storage")
                return True  # Not an error, just not configured
            
            # Check if cloud storage service is available
            if not storage_service.use_aws and not storage_service.use_gcp:
                logger.debug(f"Cloud storage service not available, keeping recording {recording.id} in local storage")
                return True  # Not an error, just not available
            
            # Verify file exists and is accessible before upload
            if not os.path.exists(local_file_path):
                logger.error(f"Cannot upload recording {recording.id}: file not found at {local_file_path}")
                return False
            
            # Get file info
            file_size = os.path.getsize(local_file_path)
            logger.info(f"🚀 Uploading completed recording {recording.id} to {cloud_backend} storage... ({storage_service._format_size(file_size)})")
            
            # Add retry mechanism for upload
            max_retries = 3
            retry_delay = 5  # seconds
            
            for attempt in range(max_retries):
                try:
                    # Upload file to cloud storage (AWS S3 or GCP)
                    storage_result = storage_service.upload_recording(
                        local_file_path=local_file_path,
                        recording_id=str(recording.id),
                        camera_id=str(recording.camera.id),
                        filename=os.path.basename(local_file_path)
                    )
                    
                    if storage_result and storage_result[0]:  # storage_path is not None
                        storage_path, storage_type = storage_result
                        
                        # Update recording with cloud storage info
                        recording.file_path = storage_path
                        recording.storage_type = storage_type
                        
                        # Add upload timestamp
                        recording.updated_at = timezone.now()
                        recording.save(update_fields=['file_path', 'storage_type', 'updated_at'])
                        
                        logger.info(f"✅ Recording {recording.id} successfully uploaded to {storage_type.upper()}: {storage_path}")
                        upload_success = True
                        
                        # Clean up local file after successful upload based on storage type
                        cleanup_enabled = False
                        if storage_type == 'aws' and getattr(settings, 'AWS_STORAGE_CLEANUP_LOCAL', True):
                            cleanup_enabled = True
                        elif storage_type == 'gcp' and getattr(settings, 'GCP_STORAGE_CLEANUP_LOCAL', True):
                            cleanup_enabled = True
                        
                        if cleanup_enabled:
                            try:
                                # Wait a moment to ensure cloud upload is fully processed
                                time.sleep(2)
                                os.remove(local_file_path)
                                logger.info(f"🗑️ Local file cleaned up after {storage_type.upper()} upload: {local_file_path}")
                            except Exception as cleanup_error:
                                logger.warning(f"Failed to cleanup local file {local_file_path}: {str(cleanup_error)}")
                                # Don't fail the upload just because cleanup failed
                        
                        break  # Success, exit retry loop
                        
                    else:
                        logger.warning(f"Upload attempt {attempt + 1} failed for recording {recording.id}")
                        if attempt < max_retries - 1:
                            logger.info(f"Retrying upload in {retry_delay} seconds...")
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                        else:
                            logger.error(f"All upload attempts failed for recording {recording.id}, keeping in local storage")
                            
                except Exception as upload_error:
                    logger.error(f"Upload attempt {attempt + 1} error for recording {recording.id}: {str(upload_error)}")
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying upload in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        logger.error(f"All upload attempts failed for recording {recording.id}: {str(upload_error)}")
                        break
                        
        except Exception as e:
            logger.error(f"Critical error uploading recording {recording.id} to cloud storage: {str(e)}")
            upload_success = False
        
        # If upload failed, ensure recording stays in local storage for background sync
        if not upload_success:
            try:
                # Make sure storage_type is set to local for failed uploads
                if recording.storage_type != 'local':
                    recording.storage_type = 'local'
                    recording.save(update_fields=['storage_type'])
                    logger.info(f"Recording {recording.id} marked as local storage for background sync retry")
            except Exception as db_error:
                logger.error(f"Error updating recording storage type: {str(db_error)}")
        
        return upload_success
    
    def stop_recording(self, camera_id):
        """Stop an active recording"""
        if str(camera_id) not in self.active_recordings:
            raise Exception("No active recording found for this camera")
        
        recording_info = self.active_recordings[str(camera_id)]
        recording = recording_info['recording']
        
        # Update recording status
        recording.status = 'stopped'
        recording.end_time = timezone.now()
        recording.save()
        
        # The recording thread will handle cleanup and GCP upload if needed
        logger.info(f"Stopped recording for camera {recording.camera.name}")
        return recording
    
    def is_recording(self, camera_id):
        """Check if a camera is currently recording"""
        return str(camera_id) in self.active_recordings
    
    def get_active_recordings(self):
        """Get all active recordings"""
        return list(self.active_recordings.keys())


# Global instances
stream_manager = RTSPStreamManager()
recording_manager = RTSPRecordingManager()


def test_camera_connection(rtsp_url):
    """Test if a camera RTSP URL is accessible"""
    if not OPENCV_AVAILABLE:
        return False, "OpenCV is not installed. Please install opencv-python to use camera functionality."
    
    try:
        # Import OpenCV configuration for robust testing
        from .opencv_config import test_camera_connection_robust
        return test_camera_connection_robust(rtsp_url)
            
    except Exception as e:
        return False, f"Connection error: {str(e)}"


def generate_frames(camera, quality='main'):
    """Generator function for streaming frames with enhanced performance and error handling"""
    stream_started = False
    last_frame = None
    consecutive_errors = 0
    max_errors = 5
    
    try:
        # Start the stream
        stream_info = stream_manager.start_stream(camera, quality)
        stream_manager.add_viewer(camera.id, quality)
        stream_started = True
        
        # Stream frames continuously
        frame_count = 0
        last_frame_time = time.time()
        last_health_check = time.time()
        
        logger.info(f"Starting frame generation for camera {camera.name} (quality: {quality})")
        
        while True:
            try:
                frame = stream_manager.get_frame(camera.id, quality)
                
                if frame is not None:
                    # Use optimized JPEG encoding from opencv_config
                    from .opencv_config import JPEG_ENCODING_SETTINGS
                    ret, buffer = cv2.imencode('.jpg', frame, JPEG_ENCODING_SETTINGS)
                    
                    if ret:
                        frame_bytes = buffer.tobytes()
                        frame_count += 1
                        last_frame_time = time.time()
                        last_frame = frame_bytes  # Cache last good frame
                        consecutive_errors = 0
                        
                        # Yield the frame in MJPEG format
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n'
                               b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n' + 
                               frame_bytes + b'\r\n')
                    else:
                        logger.warning(f"Failed to encode frame for camera {camera.name}")
                        consecutive_errors += 1
                        
                        # Use last good frame if available
                        if last_frame and consecutive_errors < 3:
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n'
                                   b'Content-Length: ' + str(len(last_frame)).encode() + b'\r\n\r\n' + 
                                   last_frame + b'\r\n')
                else:
                    # No frame available
                    consecutive_errors += 1
                    
                    if consecutive_errors >= max_errors:
                        logger.error(f"Too many consecutive errors for camera {camera.name}, attempting recovery")
                        
                        # Try to recover the stream
                        recovery_result = stream_manager.recover_stream(camera.id, quality)
                        if recovery_result:
                            consecutive_errors = 0
                            logger.info(f"Stream recovered for camera {camera.name}")
                        else:
                            logger.error(f"Failed to recover stream for camera {camera.name}")
                            break
                    
                    # Use last good frame if available, otherwise wait
                    if last_frame and consecutive_errors < 3:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n'
                               b'Content-Length: ' + str(len(last_frame)).encode() + b'\r\n\r\n' + 
                               last_frame + b'\r\n')
                    else:
                        time.sleep(0.1)  # Wait for frames
                        continue
                
                # Adaptive frame rate control
                current_time = time.time()
                time_since_last_frame = current_time - last_frame_time
                
                if time_since_last_frame < 0.04:  # Target 25 FPS
                    time.sleep(0.04 - time_since_last_frame)
                
                # Periodic health check (every 5 seconds)
                if current_time - last_health_check > 5:
                    if not stream_manager.is_stream_active(camera.id, quality):
                        logger.warning(f"Stream no longer active for camera {camera.name}")
                        break
                    last_health_check = current_time
                        
            except Exception as frame_error:
                consecutive_errors += 1
                logger.error(f"Error processing frame for camera {camera.name}: {str(frame_error)} (error {consecutive_errors}/{max_errors})")
                
                if consecutive_errors >= max_errors:
                    logger.error(f"Too many consecutive frame errors for camera {camera.name}")
                    break
                
                # Send error frame but continue streaming
                error_msg = f"Frame processing error (attempt {consecutive_errors}/{max_errors})".encode()
                yield (b'--frame\r\n'
                       b'Content-Type: text/plain\r\n'
                       b'Content-Length: ' + str(len(error_msg)).encode() + b'\r\n\r\n' + 
                       error_msg + b'\r\n')
                time.sleep(0.5)  # Wait before retrying
                
    except Exception as e:
        logger.error(f"Critical error in frame generation for camera {camera.name}: {str(e)}")
        # Send final error frame
        error_msg = f"Critical streaming error: {str(e)}".encode()
        yield (b'--frame\r\n'
               b'Content-Type: text/plain\r\n'
               b'Content-Length: ' + str(len(error_msg)).encode() + b'\r\n\r\n' + 
               error_msg + b'\r\n')
    finally:
        try:
            if stream_started:
                stream_manager.remove_viewer(camera.id, quality)
                logger.info(f"Frame generation ended for camera {camera.name} (processed {frame_count} frames)")
        except Exception as cleanup_error:
            logger.error(f"Error during stream cleanup for camera {camera.name}: {str(cleanup_error)}")
