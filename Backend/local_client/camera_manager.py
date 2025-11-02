"""
Camera manager for health monitoring and connection testing
"""
import cv2
import logging
import asyncio
from datetime import datetime
from typing import Dict, Optional, List
import httpx

try:
    from .config import config
    from .models import CameraSchema
except ImportError:
    from config import config
    from models import CameraSchema

logger = logging.getLogger(__name__)


class CameraManager:
    """Manages camera health monitoring"""
    
    def __init__(self):
        self.cameras: Dict[str, CameraSchema] = {}
        self.camera_status: Dict[str, Dict] = {}
        self.health_check_interval = 300  # 5 minutes
    
    def update_cameras(self, cameras: List[CameraSchema]):
        """Update camera list"""
        # Handle empty cameras list
        if not cameras:
            # Clear all cameras
            self.cameras.clear()
            self.camera_status.clear()
            logger.info("All cameras removed (no cameras from backend)")
            return
        
        new_camera_ids = {str(c.id) for c in cameras}
        current_camera_ids = set(self.cameras.keys())
        
        # Remove old cameras
        for camera_id in current_camera_ids - new_camera_ids:
            del self.cameras[camera_id]
            if camera_id in self.camera_status:
                del self.camera_status[camera_id]
            logger.debug(f"Removed camera: {camera_id}")
        
        # Add/update cameras
        added_count = 0
        for camera in cameras:
            try:
                camera_id = str(camera.id)
                self.cameras[camera_id] = camera
                if camera_id not in self.camera_status:
                    self.camera_status[camera_id] = {
                        'status': 'unknown',
                        'last_check': None,
                        'last_success': None,
                        'consecutive_failures': 0
                    }
                added_count += 1
            except Exception as e:
                logger.warning(f"Failed to add camera {camera.id}: {str(e)}")
        
        logger.info(f"Cameras updated: {len(self.cameras)} total ({added_count} processed)")
    
    async def check_camera_health(self, camera: CameraSchema) -> bool:
        """Check if camera is accessible"""
        camera_id = str(camera.id)
        
        try:
            logger.debug(f"Health check for camera {camera.name}")
            
            # Try to connect to RTSP stream
            cap = cv2.VideoCapture(camera.rtsp_url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Try to read a frame with timeout
            success = False
            for attempt in range(3):
                ret, frame = cap.read()
                if ret and frame is not None:
                    success = True
                    break
                await asyncio.sleep(0.5)
            
            cap.release()
            
            if success:
                self.camera_status[camera_id]['status'] = 'online'
                self.camera_status[camera_id]['last_success'] = datetime.now()
                self.camera_status[camera_id]['consecutive_failures'] = 0
                logger.debug(f"Camera {camera.name} is healthy")
            else:
                self.camera_status[camera_id]['status'] = 'offline'
                self.camera_status[camera_id]['consecutive_failures'] += 1
                logger.warning(f"Camera {camera.name} health check failed")
            
            self.camera_status[camera_id]['last_check'] = datetime.now()
            return success
            
        except Exception as e:
            logger.error(f"Error checking camera {camera.name}: {str(e)}")
            self.camera_status[camera_id]['status'] = 'error'
            self.camera_status[camera_id]['consecutive_failures'] += 1
            self.camera_status[camera_id]['last_check'] = datetime.now()
            return False
    
    async def check_all_cameras(self):
        """Check health of all cameras"""
        if not self.cameras:
            return
        
        logger.debug(f"Checking health of {len(self.cameras)} cameras")
        
        tasks = [
            self.check_camera_health(camera)
            for camera in self.cameras.values()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        online_count = sum(1 for r in results if r is True)
        logger.info(f"Camera health check complete: {online_count}/{len(self.cameras)} online")
    
    def get_camera_status(self, camera_id: str) -> Optional[Dict]:
        """Get status for a specific camera"""
        return self.camera_status.get(str(camera_id))
    
    def get_all_status(self) -> Dict[str, Dict]:
        """Get status for all cameras"""
        return self.camera_status.copy()
    
    def is_camera_healthy(self, camera_id: str) -> bool:
        """Check if camera is healthy"""
        status = self.camera_status.get(str(camera_id))
        if not status:
            return False
        return status['status'] == 'online' and status['consecutive_failures'] < 3
