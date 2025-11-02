"""
Schedule manager for local client
Manages APScheduler to execute recordings based on schedules
"""
import logging
from datetime import datetime, time as dt_time
from typing import Dict, Optional, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

try:
    from .config import config
    from .models import ScheduleSchema, CameraSchema
except ImportError:
    from config import config
    from models import ScheduleSchema, CameraSchema

logger = logging.getLogger(__name__)


class SchedulerManager:
    """Manages recording schedules using APScheduler"""
    
    def __init__(self, recording_callback):
        """
        Initialize scheduler
        
        Args:
            recording_callback: Async function to call when schedule triggers
                callback(camera: CameraSchema, schedule: ScheduleSchema)
        """
        self.scheduler = AsyncIOScheduler()
        self.recording_callback = recording_callback
        self.active_schedules: Dict[str, ScheduleSchema] = {}
        self.schedule_jobs: Dict[str, str] = {}  # schedule_id -> job_id
        
    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
    
    def add_schedule(self, schedule: ScheduleSchema):
        """Add a new schedule"""
        # Validate schedule
        if not schedule or not schedule.id:
            logger.error("Invalid schedule data provided")
            return
        
        if not schedule.camera or not schedule.camera.id:
            logger.error(f"Schedule {schedule.id} has no valid camera")
            return
        
        schedule_id = str(schedule.id)
        
        # Remove existing schedule if present
        if schedule_id in self.active_schedules:
            self.remove_schedule(schedule_id)
        
        if not schedule.is_active:
            logger.debug(f"Schedule {schedule_id} is not active, skipping")
            return
        
        try:
            # Parse times
            start_time = datetime.strptime(schedule.start_time, '%H:%M:%S').time()
            end_time = datetime.strptime(schedule.end_time, '%H:%M:%S').time()
            
            # Create trigger based on schedule type
            if schedule.schedule_type == 'once':
                trigger = self._create_once_trigger(schedule, start_time)
            elif schedule.schedule_type == 'daily':
                trigger = self._create_daily_trigger(schedule, start_time, end_time)
            elif schedule.schedule_type == 'weekly':
                trigger = self._create_weekly_trigger(schedule, start_time, end_time)
            elif schedule.schedule_type == 'continuous':
                trigger = self._create_continuous_trigger(schedule, start_time, end_time)
            else:
                logger.warning(f"Unknown schedule type: {schedule.schedule_type}")
                return
            
            if trigger:
                # Schedule the job
                job_id = f"schedule_{schedule_id}"
                self.scheduler.add_job(
                    self._execute_recording,
                    trigger,
                    id=job_id,
                    args=(schedule,),
                    replace_existing=True
                )
                
                self.active_schedules[schedule_id] = schedule
                self.schedule_jobs[schedule_id] = job_id
                
                logger.info(f"Added schedule: {schedule.name} (ID: {schedule_id})")
            else:
                logger.warning(f"Could not create trigger for schedule {schedule_id}")
                
        except Exception as e:
            logger.error(f"Error adding schedule {schedule_id}: {str(e)}")
    
    def _create_once_trigger(self, schedule: ScheduleSchema, start_time: dt_time) -> Optional[DateTrigger]:
        """Create trigger for one-time schedule"""
        if not schedule.start_date:
            return None
        
        start_datetime = datetime.strptime(schedule.start_date, '%Y-%m-%d')
        start_datetime = start_datetime.replace(
            hour=start_time.hour,
            minute=start_time.minute,
            second=start_time.second
        )
        
        # Only schedule if in the future
        if start_datetime <= datetime.now():
            logger.debug(f"One-time schedule {schedule.id} is in the past, skipping")
            return None
        
        return DateTrigger(run_date=start_datetime)
    
    def _create_daily_trigger(self, schedule: ScheduleSchema, start_time: dt_time, end_time: dt_time):
        """Create trigger for daily schedule"""
        return CronTrigger(
            hour=start_time.hour,
            minute=start_time.minute,
            second=start_time.second
        )
    
    def _create_weekly_trigger(self, schedule: ScheduleSchema, start_time: dt_time, end_time: dt_time):
        """Create trigger for weekly schedule"""
        if not schedule.days_of_week:
            return None
        
        # Map day names to cron day numbers (0=Monday, 6=Sunday)
        day_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2,
            'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        days = [day_map.get(day.lower()) for day in schedule.days_of_week if day.lower() in day_map]
        
        if not days:
            return None
        
        return CronTrigger(
            day_of_week=','.join(map(str, days)),
            hour=start_time.hour,
            minute=start_time.minute,
            second=start_time.second
        )
    
    def _create_continuous_trigger(self, schedule: ScheduleSchema, start_time: dt_time, end_time: dt_time):
        """Create trigger for continuous schedule (runs every minute during time window)"""
        # For continuous, we check every minute if we're in the time window
        return IntervalTrigger(minutes=1)
    
    async def _execute_recording(self, schedule: ScheduleSchema):
        """Execute recording when schedule triggers"""
        try:
            # Validate schedule
            if not schedule or not schedule.id:
                logger.error("Invalid schedule provided to _execute_recording")
                return
            
            if not schedule.camera or not schedule.camera.id:
                logger.error(f"Schedule {schedule.id} has no valid camera")
                return
            
            if not schedule.camera.rtsp_url:
                logger.error(f"Camera {schedule.camera.name} has no RTSP URL configured")
                return
            
            logger.info(f"Schedule triggered: {schedule.name} for camera {schedule.camera.name}")
            
            # Check if within time window for continuous schedules
            if schedule.schedule_type == 'continuous':
                start_time = datetime.strptime(schedule.start_time, '%H:%M:%S').time()
                end_time = datetime.strptime(schedule.end_time, '%H:%M:%S').time()
                now_time = datetime.now().time()
                
                if not (start_time <= now_time <= end_time):
                    logger.debug(f"Outside time window for continuous schedule {schedule.id}")
                    return
            
            # Check date range if specified
            if schedule.start_date:
                start_date = datetime.strptime(schedule.start_date, '%Y-%m-%d').date()
                if datetime.now().date() < start_date:
                    return
            
            if schedule.end_date:
                end_date = datetime.strptime(schedule.end_date, '%Y-%m-%d').date()
                if datetime.now().date() > end_date:
                    logger.info(f"Schedule {schedule.id} has ended, removing")
                    self.remove_schedule(str(schedule.id))
                    return
            
            # Call the recording callback
            await self.recording_callback(schedule.camera, schedule)
            
        except Exception as e:
            logger.error(f"Error executing schedule {schedule.id}: {str(e)}")
    
    def remove_schedule(self, schedule_id: str):
        """Remove a schedule"""
        schedule_id = str(schedule_id)
        
        if schedule_id in self.schedule_jobs:
            job_id = self.schedule_jobs[schedule_id]
            try:
                self.scheduler.remove_job(job_id)
                logger.info(f"Removed schedule job {job_id}")
            except Exception as e:
                logger.warning(f"Error removing job {job_id}: {str(e)}")
            
            del self.schedule_jobs[schedule_id]
        
        if schedule_id in self.active_schedules:
            del self.active_schedules[schedule_id]
    
    def update_schedules(self, schedules: List[ScheduleSchema]):
        """Update all schedules (add new, update existing, remove old)"""
        # Handle empty schedules list
        if not schedules:
            # Remove all existing schedules
            for schedule_id in list(self.active_schedules.keys()):
                self.remove_schedule(schedule_id)
            logger.info("All schedules removed (no schedules from backend)")
            return
        
        new_schedule_ids = {str(s.id) for s in schedules}
        current_schedule_ids = set(self.active_schedules.keys())
        
        # Remove schedules that are no longer present
        to_remove = current_schedule_ids - new_schedule_ids
        for schedule_id in to_remove:
            self.remove_schedule(schedule_id)
            logger.info(f"Removed obsolete schedule: {schedule_id}")
        
        # Add or update schedules
        added_count = 0
        for schedule in schedules:
            try:
                self.add_schedule(schedule)
                added_count += 1
            except Exception as e:
                logger.warning(f"Failed to add schedule {schedule.id}: {str(e)}")
        
        logger.info(f"Schedules updated: {len(self.active_schedules)} active ({added_count} processed)")
    
    def get_active_schedules(self) -> Dict[str, ScheduleSchema]:
        """Get all active schedules"""
        return self.active_schedules.copy()
