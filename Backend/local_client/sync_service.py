"""
Sync service for resilient schedule sync and status updates
Handles offline operation and retry logic
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any

try:
    from .config import config
    from .api_client import BackendAPIClient
    from .models import ScheduleSchema, RecordingStatusUpdate, HeartbeatData, CameraSchema
except ImportError:
    from config import config
    from api_client import BackendAPIClient
    from models import ScheduleSchema, RecordingStatusUpdate, HeartbeatData, CameraSchema

logger = logging.getLogger(__name__)


class SyncService:
    """Handles schedule sync and status updates with resilience"""
    
    def __init__(
        self,
        api_client: BackendAPIClient,
        scheduler_manager,
        recording_manager,
        status_update_callback
    ):
        """
        Initialize sync service
        
        Args:
            api_client: Backend API client
            scheduler_manager: Scheduler manager instance
            recording_manager: Recording manager instance
            status_update_callback: Callback to handle recording status updates
        """
        self.api_client = api_client
        self.scheduler_manager = scheduler_manager
        self.recording_manager = recording_manager
        self.status_update_callback = status_update_callback
        
        self.last_sync: Optional[datetime] = None
        self.sync_interval = timedelta(seconds=config.SYNC_INTERVAL_SECONDS)
        self.heartbeat_interval = timedelta(seconds=config.HEARTBEAT_INTERVAL_SECONDS)
        
        self.pending_status_updates = []
        self.pending_uploads = []
        
        self._sync_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._retry_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Start sync service"""
        if self._running:
            return
        
        self._running = True
        
        # Load pending updates from cache
        self._load_pending_updates()
        
        # Start background tasks
        self._sync_task = asyncio.create_task(self._sync_loop())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._retry_task = asyncio.create_task(self._retry_loop())
        
        logger.info("Sync service started")
    
    async def stop(self):
        """Stop sync service"""
        self._running = False
        
        # Cancel tasks
        for task in [self._sync_task, self._heartbeat_task, self._retry_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Save pending updates
        self._save_pending_updates()
        
        logger.info("Sync service stopped")
    
    async def _sync_loop(self):
        """Periodic schedule sync loop"""
        while self._running:
            try:
                await self.sync_schedules()
                await asyncio.sleep(self.sync_interval.total_seconds())
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in sync loop: {str(e)}")
                await asyncio.sleep(30)  # Wait before retry
    
    async def _heartbeat_loop(self):
        """Periodic heartbeat loop"""
        while self._running:
            try:
                await self.send_heartbeat()
                await asyncio.sleep(self.heartbeat_interval.total_seconds())
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"Heartbeat error (will retry): {str(e)}")
                await asyncio.sleep(60)  # Retry in 60s
    
    async def _retry_loop(self):
        """Periodic retry loop for pending updates"""
        while self._running:
            try:
                await self._retry_pending_updates()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in retry loop: {str(e)}")
                await asyncio.sleep(60)
    
    async def sync_schedules(self) -> bool:
        """Sync schedules from backend"""
        try:
            logger.debug("Syncing schedules from backend...")
            
            schedules = await self.api_client.fetch_schedules(self.last_sync)
            
            # Handle empty schedules gracefully
            if not schedules:
                logger.info("No schedules received from backend (this is normal if no schedules are configured)")
                # Clear existing schedules if backend returns empty list
                self.scheduler_manager.update_schedules([])
                self.last_sync = datetime.now()
                return True
            
            # Validate schedules before updating
            valid_schedules = []
            for schedule in schedules:
                try:
                    if schedule and schedule.id and schedule.camera and schedule.camera.id:
                        valid_schedules.append(schedule)
                    else:
                        logger.warning(f"Skipping invalid schedule: {schedule.id if schedule else 'None'}")
                except Exception as e:
                    logger.warning(f"Error validating schedule: {str(e)}")
                    continue
            
            # Update scheduler with new schedules
            self.scheduler_manager.update_schedules(valid_schedules)
            
            self.last_sync = datetime.now()
            logger.info(f"Synced {len(valid_schedules)} valid schedules")
            
            return True
            
        except Exception as e:
            logger.warning(f"Schedule sync failed (will retry): {str(e)}")
            return False
    
    async def send_heartbeat(self):
        """Send heartbeat to backend"""
        try:
            # Get system info
            active_recordings = len(self.recording_manager.get_active_recordings())
            
            # Calculate available space (simplified)
            import shutil
            total, used, free = shutil.disk_usage(config.RECORDING_BASE_DIR)
            available_space_gb = free / (1024 ** 3)
            
            heartbeat_data = HeartbeatData(
                client_id=config.CLIENT_ID or "unknown",
                active_recordings=active_recordings,
                available_space_gb=available_space_gb,
                last_upload=None,  # Could be tracked
                system_info={
                    'python_version': f"{asyncio.get_event_loop()._get_running_loop().__class__.__name__}",
                    'recording_dir': str(config.RECORDING_BASE_DIR)
                }
            )
            
            await self.api_client.send_heartbeat(heartbeat_data)
            logger.debug("Heartbeat sent")
            
        except Exception as e:
            logger.debug(f"Heartbeat failed: {str(e)}")
            # Don't log as error, it will retry
    
    async def queue_status_update(self, status_update: RecordingStatusUpdate):
        """Queue a status update for sending"""
        try:
            # Try to send immediately
            await self.api_client.update_recording_status(status_update)
            logger.debug(f"Status update sent immediately: {status_update.recording_id}")
        except Exception as e:
            # Queue for retry
            logger.warning(f"Failed to send status update, queuing for retry: {str(e)}")
            self.pending_status_updates.append({
                'data': status_update.dict(),
                'timestamp': datetime.now().isoformat(),
                'attempts': 0
            })
            self._save_pending_updates()
    
    async def _retry_pending_updates(self):
        """Retry pending status updates"""
        if not self.pending_status_updates:
            return
        
        logger.info(f"Retrying {len(self.pending_status_updates)} pending updates")
        
        successful = []
        for i, update in enumerate(self.pending_status_updates):
            try:
                if update['attempts'] >= config.MAX_RETRY_ATTEMPTS:
                    logger.warning(f"Max attempts reached for update {update['data'].get('recording_id')}, dropping")
                    successful.append(i)
                    continue
                
                status_update = RecordingStatusUpdate(**update['data'])
                await self.api_client.update_recording_status(status_update)
                
                successful.append(i)
                logger.info(f"Successfully sent queued update for {status_update.recording_id}")
                
            except Exception as e:
                update['attempts'] += 1
                logger.debug(f"Retry failed (attempt {update['attempts']}): {str(e)}")
        
        # Remove successful updates
        for i in reversed(successful):
            self.pending_status_updates.pop(i)
        
        if successful:
            self._save_pending_updates()
    
    def _load_pending_updates(self):
        """Load pending updates from cache"""
        cache_file = config.get_cache_file('pending_updates')
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    self.pending_status_updates = data.get('status_updates', [])
                    logger.info(f"Loaded {len(self.pending_status_updates)} pending updates from cache")
            except Exception as e:
                logger.warning(f"Failed to load pending updates: {str(e)}")
    
    def _save_pending_updates(self):
        """Save pending updates to cache"""
        cache_file = config.get_cache_file('pending_updates')
        try:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_file, 'w') as f:
                json.dump({
                    'status_updates': self.pending_status_updates,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save pending updates: {str(e)}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get sync service status"""
        return {
            'running': self._running,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'pending_updates': len(self.pending_status_updates),
            'active_schedules': len(self.scheduler_manager.get_active_schedules()),
            'sync_interval_seconds': self.sync_interval.total_seconds()
        }
