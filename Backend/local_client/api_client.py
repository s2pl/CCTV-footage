"""
Backend API client for local recording client
"""
import httpx
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

try:
    from .config import config
    from .models import (
        ScheduleSchema, RecordingRegistrationRequest, RecordingRegistrationResponse,
        RecordingStatusUpdate, HeartbeatData, HeartbeatResponse, CameraSchema
    )
    from .utils.retry import async_retry
except ImportError:
    from config import config
    from models import (
        ScheduleSchema, RecordingRegistrationRequest, RecordingRegistrationResponse,
        RecordingStatusUpdate, HeartbeatData, HeartbeatResponse, CameraSchema
    )
    from utils.retry import async_retry

logger = logging.getLogger(__name__)


class BackendAPIClient:
    """Client for communicating with backend API"""
    
    def __init__(self):
        self.base_url = config.BACKEND_API_URL.rstrip('/')
        self.client_token = config.CLIENT_TOKEN
        self.headers = {
            'Authorization': f'Bearer {self.client_token}',
            'Content-Type': 'application/json'
        }
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(headers=self.headers, timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
    
    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(headers=self.headers, timeout=self.timeout)
        return self._client
    
    @async_retry(max_attempts=3, delay=2.0)
    async def fetch_schedules(self, last_sync: Optional[datetime] = None) -> List[ScheduleSchema]:
        """Fetch schedules from backend"""
        try:
            client = self._get_client()
            params = {}
            if last_sync:
                params['last_sync'] = last_sync.isoformat()
            
            response = await client.get(
                f"{self.base_url}/v0/api/local-client/schedules",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Handle empty response
            if not data:
                logger.info("No schedules received from backend")
                return []
            
            # Parse schedules with error handling
            schedules = []
            for item in data:
                try:
                    schedule = ScheduleSchema(**item)
                    schedules.append(schedule)
                except Exception as e:
                    logger.warning(f"Failed to parse schedule data: {item}. Error: {str(e)}")
                    continue
            
            logger.info(f"Fetched {len(schedules)} schedules from backend")
            return schedules
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed - check CLIENT_TOKEN")
            raise
        except Exception as e:
            logger.error(f"Error fetching schedules: {str(e)}")
            raise
    
    @async_retry(max_attempts=3, delay=2.0)
    async def fetch_cameras(self) -> List[CameraSchema]:
        """Fetch assigned cameras from backend"""
        try:
            client = self._get_client()
            response = await client.get(f"{self.base_url}/v0/api/local-client/cameras")
            response.raise_for_status()
            
            data = response.json()
            
            # Handle empty response
            if not data:
                logger.info("No cameras received from backend")
                return []
            
            # Parse cameras with error handling
            cameras = []
            for item in data:
                try:
                    camera = CameraSchema(**item)
                    cameras.append(camera)
                except Exception as e:
                    logger.warning(f"Failed to parse camera data: {item}. Error: {str(e)}")
                    continue
            
            logger.info(f"Fetched {len(cameras)} cameras from backend")
            return cameras
            
        except Exception as e:
            logger.error(f"Error fetching cameras: {str(e)}")
            raise
    
    @async_retry(max_attempts=5, delay=1.0)
    async def register_recording(
        self,
        camera_id: str,
        schedule_id: Optional[str] = None,
        recording_name: Optional[str] = None
    ) -> str:
        """Register a new recording with backend"""
        try:
            client = self._get_client()
            response = await client.post(
                f"{self.base_url}/v0/api/local-client/recordings/register",
                params={
                    'camera_id': camera_id,
                    'schedule_id': schedule_id or '',
                    'recording_name': recording_name or ''
                }
            )
            response.raise_for_status()
            
            data = response.json()
            recording_id = data['recording_id']
            logger.info(f"Registered recording: {recording_id}")
            return recording_id
            
        except Exception as e:
            logger.error(f"Error registering recording: {str(e)}")
            raise
    
    @async_retry(max_attempts=5, delay=1.0)
    async def update_recording_status(self, status_update: RecordingStatusUpdate):
        """Update recording status"""
        try:
            client = self._get_client()
            response = await client.post(
                f"{self.base_url}/v0/api/local-client/recordings/status",
                json=status_update.dict(exclude_none=True)
            )
            response.raise_for_status()
            logger.debug(f"Updated recording {status_update.recording_id} status to {status_update.status}")
            
        except Exception as e:
            logger.error(f"Error updating recording status: {str(e)}")
            raise
    
    @async_retry(max_attempts=3, delay=2.0)
    async def send_heartbeat(self, heartbeat_data: HeartbeatData):
        """Send heartbeat to backend"""
        try:
            client = self._get_client()
            response = await client.post(
                f"{self.base_url}/v0/api/local-client/heartbeat",
                json=heartbeat_data.dict(exclude_none=True)
            )
            response.raise_for_status()
            logger.debug(f"Heartbeat sent: {heartbeat_data.active_recordings} active recordings")
            
        except Exception as e:
            logger.error(f"Error sending heartbeat: {str(e)}")
            raise
    
    async def test_connection(self) -> bool:
        """Test connection to backend"""
        try:
            client = self._get_client()
            # Try local-client health endpoint first, then main health endpoint
            try:
                response = await client.get(f"{self.base_url}/v0/api/local-client/health")
                response.raise_for_status()
                return True
            except:
                # Fallback to main health endpoint
                response = await client.get(f"{self.base_url}/api/health")
                response.raise_for_status()
                return True
        except Exception as e:
            logger.warning(f"Backend connection test failed: {str(e)}")
            return False

