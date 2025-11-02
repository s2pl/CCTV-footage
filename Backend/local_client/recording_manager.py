"""
Recording manager for local client
Handles OpenCV-based video recording from RTSP streams
"""
import warnings
import logging

# Suppress OpenCV warnings
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', message='.*FFMPEG.*')
warnings.filterwarnings('ignore', message='.*codec.*')
warnings.filterwarnings('ignore', message='.*tag.*')
warnings.filterwarnings('ignore', message='.*fallback.*')

import cv2
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

# Suppress cv2 logging
logging.getLogger('cv2').setLevel(logging.ERROR)

try:
    from .config import config
    from .models import CameraSchema
except ImportError:
    from config import config
    from models import CameraSchema

logger = logging.getLogger(__name__)


class RecordingManager:
    """Manages video recordings from cameras"""
    
    def __init__(self):
        self.active_recordings: Dict[str, Dict[str, Any]] = {}
        self.recording_locks = {}
        self.completed_recordings = []
        
    def start_recording(
        self,
        camera: CameraSchema,
        recording_id: str,
        duration_minutes: Optional[int] = None,
        schedule_id: Optional[str] = None
    ) -> bool:
        """Start recording from a camera"""
        # Validate inputs
        if not camera or not camera.id:
            logger.error("Invalid camera data provided")
            return False
        
        if not recording_id:
            logger.error("Recording ID is required")
            return False
        
        if not camera.rtsp_url:
            logger.error(f"Camera {camera.name} has no RTSP URL configured")
            return False
        
        camera_id = str(camera.id)
        
        if camera_id in self.active_recordings:
            logger.warning(f"Recording already in progress for camera {camera_id}")
            return False
        
        try:
            # Create recording directory
            date_str = datetime.now().strftime('%Y%m%d')
            camera_dir = config.RECORDINGS_DIR / camera_id / date_str
            camera_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename_base = f"recording_{timestamp}"
            file_path = camera_dir / f"{filename_base}.avi"
            
            logger.info(f"Starting recording for camera {camera.name}: {file_path}")
            
            # Open camera stream
            rtsp_url = camera.rtsp_url
            cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
            
            # Configure capture
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_FPS, 25)
            
            # Test connection
            ret, test_frame = cap.read()
            if not ret or test_frame is None:
                cap.release()
                raise Exception(f"Cannot read frames from camera: {rtsp_url}")
            
            # Get video properties
            fps = int(cap.get(cv2.CAP_PROP_FPS)) or 25
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if width <= 0 or height <= 0:
                height, width = test_frame.shape[:2]
            
            logger.info(f"Video properties: {width}x{height} @ {fps}fps")
            
            # Try codecs in order of preference
            codecs = [
                ('MJPG', '.avi'),
                ('mp4v', '.mp4'),
                ('XVID', '.avi')
            ]
            
            out = None
            used_codec = None
            final_path = None
            
            for codec_name, ext in codecs:
                try:
                    fourcc = cv2.VideoWriter_fourcc(*codec_name)
                    test_path = camera_dir / f"{filename_base}{ext}"
                    out = cv2.VideoWriter(str(test_path), fourcc, fps, (width, height), True)
                    
                    if out.isOpened():
                        used_codec = codec_name
                        final_path = test_path
                        logger.info(f"Using codec: {codec_name}, file: {final_path}")
                        break
                    else:
                        out.release()
                        out = None
                except Exception as e:
                    logger.warning(f"Codec {codec_name} failed: {str(e)}")
                    continue
            
            if out is None:
                cap.release()
                raise Exception("Could not initialize video writer with any codec")
            
            # Store recording info
            self.active_recordings[camera_id] = {
                'recording_id': recording_id,
                'camera': camera,
                'capture': cap,
                'writer': out,
                'file_path': final_path,
                'start_time': datetime.now(),
                'duration_minutes': duration_minutes,
                'frame_count': 0,
                'schedule_id': schedule_id,
                'codec': used_codec
            }
            
            # Start recording thread
            thread = threading.Thread(
                target=self._record_frames,
                args=(camera_id,),
                daemon=True
            )
            thread.start()
            
            logger.info(f"Recording started for camera {camera.name} (ID: {recording_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error starting recording for camera {camera.name}: {str(e)}")
            return False
    
    def _record_frames(self, camera_id: str):
        """Record frames in a separate thread"""
        recording_info = self.active_recordings.get(camera_id)
        if not recording_info:
            return
        
        cap = recording_info['capture']
        out = recording_info['writer']
        recording_id = recording_info['recording_id']
        start_time = recording_info['start_time']
        duration_minutes = recording_info['duration_minutes']
        file_path = recording_info['file_path']
        
        try:
            consecutive_failures = 0
            max_failures = 30
            frames_written = 0
            
            logger.info(f"Recording thread started for {recording_id}")
            
            while camera_id in self.active_recordings:
                try:
                    ret, frame = cap.read()
                    
                    if ret and frame is not None and frame.size > 0:
                        out.write(frame)
                        frames_written += 1
                        recording_info['frame_count'] = frames_written
                        consecutive_failures = 0
                        
                        # Log progress every 100 frames
                        if frames_written % 100 == 0:
                            elapsed = (datetime.now() - start_time).total_seconds()
                            logger.debug(f"Recording {recording_id}: {frames_written} frames, {elapsed:.1f}s elapsed")
                        
                        # Check duration limit
                        if duration_minutes:
                            elapsed_minutes = (datetime.now() - start_time).total_seconds() / 60
                            if elapsed_minutes >= duration_minutes:
                                logger.info(f"Recording {recording_id} reached duration limit")
                                break
                        
                        # Small delay to control frame rate
                        time.sleep(0.04)  # ~25 FPS
                        
                    else:
                        consecutive_failures += 1
                        if consecutive_failures >= max_failures:
                            logger.error(f"Too many failures for recording {recording_id}")
                            break
                        time.sleep(0.1)
                        
                except Exception as e:
                    logger.error(f"Frame processing error for {recording_id}: {str(e)}")
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        break
                    time.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"Critical error during recording {recording_id}: {str(e)}")
        finally:
            # Cleanup
            try:
                if cap:
                    cap.release()
            except Exception as e:
                logger.error(f"Error releasing capture: {str(e)}")
            
            try:
                if out:
                    out.release()
            except Exception as e:
                logger.error(f"Error releasing writer: {str(e)}")
            
            # Get final stats
            file_size = 0
            if file_path and file_path.exists():
                file_size = file_path.stat().st_size
            
            duration = datetime.now() - start_time
            
            # Store final recording info before removing from active
            recording_info['end_time'] = datetime.now()
            recording_info['duration'] = duration
            recording_info['file_size'] = file_size
            recording_info['frames_written'] = frames_written
            recording_info['completed'] = frames_written > 10 and file_size > 1000
            
            # Store completed recording info for callback
            completed_info = recording_info.copy()
            
            # Remove from active recordings
            if camera_id in self.active_recordings:
                self.active_recordings.pop(camera_id)
            
            # Store in completed recordings (for monitoring task)
            if not hasattr(self, 'completed_recordings'):
                self.completed_recordings = []
            self.completed_recordings.append(completed_info)
            
            # Keep only last 10 completed recordings
            if len(self.completed_recordings) > 10:
                self.completed_recordings = self.completed_recordings[-10:]
            
            logger.info(
                f"Recording {recording_id} finished: "
                f"{frames_written} frames, {file_size} bytes, {duration.total_seconds():.1f}s"
            )
    
    def stop_recording(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """Stop recording and return recording info"""
        camera_id = str(camera_id)
        
        if camera_id not in self.active_recordings:
            return None
        
        logger.info(f"Stopping recording for camera {camera_id}")
        recording_info = self.active_recordings.pop(camera_id)
        
        # Wait a bit for cleanup
        time.sleep(0.5)
        
        return recording_info
    
    def get_active_recordings(self) -> Dict[str, Dict[str, Any]]:
        """Get all active recordings"""
        return self.active_recordings.copy()
    
    def is_recording(self, camera_id: str) -> bool:
        """Check if camera is currently recording"""
        return str(camera_id) in self.active_recordings
    
    def get_recording_info(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """Get recording info for a camera"""
        return self.active_recordings.get(str(camera_id))
