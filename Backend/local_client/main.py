"""
Main entry point for local CCTV recording client
FastAPI application with background tasks
"""
import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Local imports
try:
    # Try relative imports first (if running as module)
    from .config import config
    from .api_client import BackendAPIClient
    from .recording_manager import RecordingManager
    from .scheduler_manager import SchedulerManager
    from .sync_service import SyncService
    from .camera_manager import CameraManager
    from .storage_manager import StorageManager
    from .models import ScheduleSchema, RecordingStatusUpdate, CameraSchema
    from .utils.logger import setup_logger
except ImportError:
    # Fall back to absolute imports (if running as script)
    from config import config
    from api_client import BackendAPIClient
    from recording_manager import RecordingManager
    from scheduler_manager import SchedulerManager
    from sync_service import SyncService
    from camera_manager import CameraManager
    from storage_manager import StorageManager
    from models import ScheduleSchema, RecordingStatusUpdate, CameraSchema
    from utils.logger import setup_logger

# Setup logger
logger = setup_logger("local_client")


async def monitor_recordings():
    """Background task to monitor and handle completed recordings"""
    processed_recordings = set()
    
    # Wait for initialization
    while True:
        try:
            await asyncio.sleep(5)  # Check every 5 seconds
            
            # Ensure managers are initialized
            if not recording_manager or not api_client or not sync_service:
                continue
            
            # Check for completed recordings
            if hasattr(recording_manager, 'completed_recordings'):
                for recording_info in recording_manager.completed_recordings:
                    recording_id = recording_info.get('recording_id')
                    if recording_id and recording_id not in processed_recordings:
                        processed_recordings.add(recording_id)
                        try:
                            await handle_recording_completion(recording_info)
                            logger.info(f"Processed completed recording: {recording_id}")
                        except Exception as e:
                            logger.error(f"Error processing completed recording {recording_id}: {str(e)}")
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in recording monitor: {str(e)}")
            await asyncio.sleep(10)


# Global managers
api_client: BackendAPIClient = None
recording_manager: RecordingManager = None
scheduler_manager: SchedulerManager = None
sync_service: SyncService = None
camera_manager: CameraManager = None
storage_manager: StorageManager = None


async def execute_recording(camera: CameraSchema, schedule: ScheduleSchema):
    """Callback for scheduled recordings"""
    try:
        logger.info(f"Executing scheduled recording: {schedule.name} for camera {camera.name}")
        
        # Check if camera is still valid
        if not camera or not camera.id:
            logger.error("Invalid camera data for recording")
            return
        
        # Check if already recording on this camera
        if recording_manager.is_recording(str(camera.id)):
            logger.warning(f"Camera {camera.name} is already recording, skipping scheduled recording")
            return
        
        # Register recording with backend
        try:
            recording_id = await api_client.register_recording(
                camera_id=str(camera.id),
                schedule_id=str(schedule.id) if schedule and schedule.id else None,
                recording_name=schedule.name if schedule else None
            )
        except Exception as e:
            logger.error(f"Failed to register recording with backend: {str(e)}")
            return
        
        # Calculate duration if schedule has end time
        duration_minutes = None
        if schedule and schedule.end_time:
            try:
                start_time = datetime.strptime(schedule.start_time, '%H:%M:%S').time()
                end_time = datetime.strptime(schedule.end_time, '%H:%M:%S').time()
                start_datetime = datetime.combine(datetime.now().date(), start_time)
                end_datetime = datetime.combine(datetime.now().date(), end_time)
                if end_datetime < start_datetime:
                    end_datetime = end_datetime.replace(day=end_datetime.day + 1)
                
                duration_minutes = (end_datetime - start_datetime).total_seconds() / 60
            except Exception as e:
                logger.warning(f"Could not calculate duration: {str(e)}")
        
        # Start recording
        try:
            success = recording_manager.start_recording(
                camera=camera,
                recording_id=recording_id,
                duration_minutes=duration_minutes,
                schedule_id=str(schedule.id) if schedule and schedule.id else None
            )
        except Exception as e:
            logger.error(f"Failed to start recording: {str(e)}")
            # Try to update status as failed
            try:
                await sync_service.queue_status_update(
                    RecordingStatusUpdate(
                        recording_id=recording_id,
                        status='failed',
                        error_message=f"Failed to start recording: {str(e)}"
                    )
                )
            except:
                pass
            return
        
        if success:
            # Update status
            await sync_service.queue_status_update(
                RecordingStatusUpdate(
                    recording_id=recording_id,
                    status='recording',
                    progress=0.0
                )
            )
        else:
            # Report failure
            await sync_service.queue_status_update(
                RecordingStatusUpdate(
                    recording_id=recording_id,
                    status='failed',
                    error_message='Failed to start recording'
                )
            )
        
    except Exception as e:
        logger.error(f"Error executing scheduled recording: {str(e)}")


async def handle_recording_completion(recording_info: Dict[str, Any]):
    """Handle completed recording"""
    try:
        recording_id = recording_info['recording_id']
        file_path = recording_info['file_path']
        camera_id = str(recording_info['camera'].id)
        
        if not recording_info.get('completed'):
            # Recording failed
            await sync_service.queue_status_update(
                RecordingStatusUpdate(
                    recording_id=recording_id,
                    status='failed',
                    error_message='Recording did not complete successfully'
                )
            )
            return
        
        # Upload to GCP if storage manager is available
        gcp_path = None
        if storage_manager.is_available():
            gcp_path, upload_success = await storage_manager.upload_recording(
                local_path=file_path,
                recording_id=recording_id,
                camera_id=camera_id
            )
            
            if upload_success:
                logger.info(f"Recording {recording_id} uploaded to GCP: {gcp_path}")
            else:
                logger.warning(f"Failed to upload recording {recording_id}, will retry")
                # Move to pending if needed
                await storage_manager.move_to_pending(file_path)
        else:
            # Bucket not connected - keep file locally
            logger.info(f"Recording {recording_id} stored locally at: {file_path}")
            logger.info("   File will remain local until GCP bucket is configured")
        
        # Update status
        await sync_service.queue_status_update(
            RecordingStatusUpdate(
                recording_id=recording_id,
                status='completed',
                progress=100.0,
                frames_recorded=recording_info.get('frames_written', 0),
                file_size=recording_info.get('file_size', 0),
                gcp_path=gcp_path
            )
        )
        
    except Exception as e:
        logger.error(f"Error handling recording completion: {str(e)}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global api_client, recording_manager, scheduler_manager, sync_service
    global camera_manager, storage_manager
    
    # Startup
    logger.info("Starting Local CCTV Recording Client...")
    
    # Validate configuration
    config_valid, errors = config.validate()
    if not config_valid:
        logger.error("Configuration validation failed. Please check your .env file.")
        logger.error("Required configuration missing - cannot start client.")
        sys.exit(1)
    
    # Setup directories
    config.setup_directories()
    
    # Initialize managers
    api_client = BackendAPIClient()
    recording_manager = RecordingManager()
    storage_manager = StorageManager()
    camera_manager = CameraManager()
    
    scheduler_manager = SchedulerManager(recording_callback=execute_recording)
    
    sync_service = SyncService(
        api_client=api_client,
        scheduler_manager=scheduler_manager,
        recording_manager=recording_manager,
        status_update_callback=handle_recording_completion
    )
    
    # Start scheduler
    scheduler_manager.start()
    
    # Initial sync
    try:
        # Fetch cameras
        cameras = await api_client.fetch_cameras()
        if cameras:
            camera_manager.update_cameras(cameras)
            logger.info(f"Initial sync: {len(cameras)} cameras assigned")
        else:
            logger.warning("No cameras assigned to this client. Please assign cameras in Django admin.")
            camera_manager.update_cameras([])
        
        # Sync schedules
        await sync_service.sync_schedules()
    except Exception as e:
        logger.warning(f"Initial sync failed: {str(e)}")
        # Continue anyway - will retry in background
    
    # Start sync service
    await sync_service.start()
    
    # Start monitoring task for completed recordings
    monitoring_task = asyncio.create_task(monitor_recordings())
    
    # Display bucket status
    bucket_status = storage_manager.get_bucket_status()
    if bucket_status['connected']:
        logger.info(f"[OK] Storage: GCP bucket '{bucket_status['bucket_name']}' connected")
    else:
        logger.info("[WARNING] Storage: GCP bucket not connected - recordings will be stored locally")
        logger.info("   Local storage path: " + str(config.RECORDINGS_DIR))
        if not bucket_status.get('gcp_available'):
            logger.info("   Note: google-cloud-storage package not installed")
        elif not bucket_status.get('has_credentials'):
            logger.info("   Note: GCP credentials file not found")
        else:
            logger.info("   Note: Bucket configuration missing or invalid")
    
    logger.info("Client started successfully")
    
    yield
    
    # Cancel monitoring task
    monitoring_task.cancel()
    try:
        await monitoring_task
    except asyncio.CancelledError:
        pass
    
    # Shutdown
    logger.info("Shutting down Local CCTV Recording Client...")
    
    # Stop sync service
    await sync_service.stop()
    
    # Stop scheduler
    scheduler_manager.stop()
    
    # Stop all recordings
    for camera_id in list(recording_manager.get_active_recordings().keys()):
        recording_info = recording_manager.stop_recording(camera_id)
        if recording_info:
            await handle_recording_completion(recording_info)
    
    # Close API client
    if api_client:
        await api_client.__aexit__(None, None, None)
    
    logger.info("Client shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Local CCTV Recording Client",
    description="Local client for recording CCTV cameras and uploading to GCP",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/status")
async def get_status():
    """Get client status"""
    try:
        active_recordings = recording_manager.get_active_recordings() if recording_manager else {}
        
        # Safely build recording info
        recording_info = []
        for cam_id, info in active_recordings.items():
            try:
                recording_info.append({
                    "camera_id": str(cam_id),
                    "camera_name": info['camera'].name if 'camera' in info and hasattr(info['camera'], 'name') else 'Unknown',
                    "recording_id": info.get('recording_id', 'unknown'),
                    "frames": info.get('frame_count', 0),
                    "started": info['start_time'].isoformat() if 'start_time' in info else datetime.now().isoformat()
                })
            except Exception as e:
                logger.warning(f"Error building recording info for {cam_id}: {str(e)}")
                continue
        
        return {
            "status": "running",
            "active_recordings": len(active_recordings),
            "schedules": len(scheduler_manager.get_active_schedules()) if scheduler_manager else 0,
            "cameras": len(camera_manager.cameras) if camera_manager else 0,
            "sync_status": sync_service.get_status() if sync_service else {"running": False},
            "bucket_status": storage_manager.get_bucket_status() if storage_manager else {"connected": False},
            "recording_info": recording_info
        }
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/manual-record")
async def manual_record(camera_id: str, duration_minutes: int = None):
    """Trigger manual recording"""
    try:
        # Check if no cameras available
        if not camera_manager.cameras:
            raise HTTPException(status_code=503, detail="No cameras available. Please assign cameras in Django admin.")
        
        camera = camera_manager.cameras.get(camera_id)
        if not camera:
            available_cameras = list(camera_manager.cameras.keys())
            raise HTTPException(
                status_code=404, 
                detail=f"Camera not found. Available cameras: {available_cameras}"
            )
        
        # Check if already recording
        if recording_manager.is_recording(camera_id):
            raise HTTPException(status_code=400, detail="Camera is already recording")
        
        # Register with backend
        try:
            recording_id = await api_client.register_recording(
                camera_id=camera_id,
                recording_name=f"Manual Recording {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
        except Exception as e:
            logger.error(f"Failed to register recording with backend: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to register recording: {str(e)}")
        
        # Start recording
        try:
            success = recording_manager.start_recording(
                camera=camera,
                recording_id=recording_id,
                duration_minutes=duration_minutes
            )
        except Exception as e:
            logger.error(f"Failed to start recording: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to start recording: {str(e)}")
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to start recording")
        
        return {
            "message": "Recording started",
            "recording_id": recording_id,
            "camera_id": camera_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting manual recording: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/schedules")
async def get_schedules():
    """Get active schedules"""
    schedules = scheduler_manager.get_active_schedules()
    return {
        "count": len(schedules),
        "schedules": [
            {
                "id": str(s.id),
                "name": s.name,
                "type": s.schedule_type,
                "camera": s.camera.name,
                "start_time": s.start_time,
                "end_time": s.end_time
            }
            for s in schedules.values()
        ]
    }


@app.post("/stop-recording/{camera_id}")
async def stop_recording(camera_id: str):
    """Stop recording for a camera"""
    try:
        if not recording_manager.is_recording(camera_id):
            raise HTTPException(status_code=400, detail="No active recording for this camera")
        
        recording_info = recording_manager.stop_recording(camera_id)
        
        if recording_info:
            await handle_recording_completion(recording_info)
            return {"message": "Recording stopped", "recording_id": recording_info['recording_id']}
        else:
            raise HTTPException(status_code=500, detail="Failed to stop recording")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping recording: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Run with uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level=config.LOG_LEVEL.lower(),
        reload=False
    )

