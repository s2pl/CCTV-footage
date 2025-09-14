"""
Scheduling service for automatic camera recordings
"""

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.date import DateTrigger
    from apscheduler.triggers.cron import CronTrigger
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    # Create dummy classes for when APScheduler is not available
    class BackgroundScheduler:
        def __init__(self):
            pass
        def start(self):
            pass
        def add_job(self, *args, **kwargs):
            pass
        def remove_job(self, *args, **kwargs):
            pass
        def get_jobs(self):
            return []
        def shutdown(self):
            pass
    
    class DateTrigger:
        def __init__(self, *args, **kwargs):
            pass
    
    class CronTrigger:
        def __init__(self, *args, **kwargs):
            pass
from django.utils import timezone
from datetime import datetime, time, timedelta
import logging
import os
from django.conf import settings
from .models import RecordingSchedule, Recording, Camera
from .streaming import recording_manager

logger = logging.getLogger(__name__)


class RecordingScheduler:
    """Manages scheduled recordings for cameras"""
    
    def __init__(self):
        if SCHEDULER_AVAILABLE:
            self.scheduler = BackgroundScheduler(
                job_defaults={
                    'coalesce': True,  # Combine missed jobs
                    'max_instances': 1,  # Only one instance of each job
                    'misfire_grace_time': 300  # 5 minutes grace time for missed jobs
                }
            )
            self.scheduler.start()
        else:
            self.scheduler = BackgroundScheduler()
            logger.warning("APScheduler not available. Scheduling functionality will be limited.")
        self.active_jobs = {}
    
    def add_schedule(self, schedule):
        """Add a new recording schedule"""
        try:
            if schedule.schedule_type == 'once':
                self._add_one_time_schedule(schedule)
            elif schedule.schedule_type == 'daily':
                self._add_daily_schedule(schedule)
            elif schedule.schedule_type == 'weekly':
                self._add_weekly_schedule(schedule)
            elif schedule.schedule_type == 'continuous':
                self._add_continuous_schedule(schedule)
            
            logger.info(f"Added schedule: {schedule.name} for camera {schedule.camera.name}")
            
        except Exception as e:
            logger.error(f"Error adding schedule {schedule.name}: {str(e)}")
            raise
    
    def _add_one_time_schedule(self, schedule):
        """Add a one-time recording schedule"""
        if not schedule.start_date:
            raise ValueError("Start date is required for one-time schedules")
        
        # Combine date and time for start
        start_datetime = datetime.combine(schedule.start_date, schedule.start_time)
        start_datetime = timezone.make_aware(start_datetime)
        
        # Check if the scheduled time is in the past
        if start_datetime < timezone.now():
            logger.warning(f"Schedule {schedule.name} is scheduled for the past ({start_datetime}), deactivating it")
            schedule.is_active = False
            schedule.save()
            return
        
        # Calculate duration
        if schedule.end_time:
            end_datetime = datetime.combine(schedule.start_date, schedule.end_time)
            end_datetime = timezone.make_aware(end_datetime)
            
            # Handle overnight recordings
            if end_datetime <= start_datetime:
                end_datetime += timedelta(days=1)
            
            duration_minutes = int((end_datetime - start_datetime).total_seconds() / 60)
        else:
            duration_minutes = 60  # Default 1 hour
        
        # Schedule start job
        start_job_id = f"start_{schedule.id}"
        self.scheduler.add_job(
            func=self._start_recording,
            trigger=DateTrigger(run_date=start_datetime),
            args=[schedule, duration_minutes],
            id=start_job_id,
            name=f"Start recording: {schedule.name}"
        )
        
        self.active_jobs[str(schedule.id)] = [start_job_id]
    
    def _add_daily_schedule(self, schedule):
        """Add a daily recurring recording schedule"""
        # Calculate duration
        duration_minutes = self._calculate_duration(schedule.start_time, schedule.end_time)
        
        # Schedule daily job
        job_id = f"daily_{schedule.id}"
        self.scheduler.add_job(
            func=self._start_recording,
            trigger=CronTrigger(
                hour=schedule.start_time.hour,
                minute=schedule.start_time.minute
            ),
            args=[schedule, duration_minutes],
            id=job_id,
            name=f"Daily recording: {schedule.name}"
        )
        
        self.active_jobs[str(schedule.id)] = [job_id]
    
    def _add_weekly_schedule(self, schedule):
        """Add a weekly recurring recording schedule"""
        if not schedule.days_of_week:
            raise ValueError("Days of week must be specified for weekly schedules")
        
        # Map day names to numbers
        day_mapping = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        # Calculate duration
        duration_minutes = self._calculate_duration(schedule.start_time, schedule.end_time)
        
        job_ids = []
        for day_name in schedule.days_of_week:
            if day_name.lower() in day_mapping:
                day_number = day_mapping[day_name.lower()]
                
                job_id = f"weekly_{schedule.id}_{day_name}"
                self.scheduler.add_job(
                    func=self._start_recording,
                    trigger=CronTrigger(
                        day_of_week=day_number,
                        hour=schedule.start_time.hour,
                        minute=schedule.start_time.minute
                    ),
                    args=[schedule, duration_minutes],
                    id=job_id,
                    name=f"Weekly recording: {schedule.name} ({day_name})"
                )
                job_ids.append(job_id)
        
        self.active_jobs[str(schedule.id)] = job_ids
    
    def _add_continuous_schedule(self, schedule):
        """Add a continuous recording schedule"""
        # For continuous recording, we'll start immediately and restart when it ends
        job_id = f"continuous_{schedule.id}"
        
        # Start recording immediately
        self.scheduler.add_job(
            func=self._start_continuous_recording,
            trigger=DateTrigger(run_date=timezone.now()),
            args=[schedule],
            id=job_id,
            name=f"Continuous recording: {schedule.name}"
        )
        
        self.active_jobs[str(schedule.id)] = [job_id]
    
    def _calculate_duration(self, start_time, end_time):
        """Calculate duration in minutes between start and end time"""
        if not end_time:
            return 60  # Default 1 hour
        
        # Create datetime objects for calculation
        today = datetime.today().date()
        start_dt = datetime.combine(today, start_time)
        end_dt = datetime.combine(today, end_time)
        
        # Handle overnight recordings
        if end_dt <= start_dt:
            end_dt += timedelta(days=1)
        
        return int((end_dt - start_dt).total_seconds() / 60)
    
    def _start_recording(self, schedule, duration_minutes):
        """Start a scheduled recording"""
        try:
            if not schedule.is_active:
                logger.info(f"Schedule {schedule.name} is inactive, skipping recording")
                return
            
            if recording_manager.is_recording(schedule.camera.id):
                logger.warning(f"Camera {schedule.camera.name} is already recording, skipping")
                return
            
            # Create recording name with SCHEDULED prefix
            recording_name = f"SCHEDULED - {schedule.name} - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Start recording
            recording = recording_manager.start_recording(
                camera=schedule.camera,
                duration_minutes=duration_minutes,
                recording_name=recording_name,
                user=schedule.created_by,
                is_scheduled=True,
                schedule_id=schedule.id
            )
            
            # Link recording to schedule
            recording.schedule = schedule
            recording.save()
            
            logger.info(f"Started scheduled recording: {recording_name}")
            
            # For 'once' type schedules, mark as inactive after starting recording
            if schedule.schedule_type == 'once':
                logger.info(f"Deactivating 'once' schedule '{schedule.name}' (ID: {schedule.id}) after recording started")
                schedule.is_active = False
                schedule.save()
                # Remove the schedule from active jobs since it's now completed
                self.remove_schedule(schedule.id)
            
        except Exception as e:
            logger.error(f"Error starting scheduled recording for {schedule.name}: {str(e)}")
    
    def _start_continuous_recording(self, schedule):
        """Start a continuous recording and schedule the next one"""
        try:
            if not schedule.is_active:
                logger.info(f"Continuous schedule {schedule.name} is inactive, stopping")
                return
            
            # Start recording for a chunk (e.g., 1 hour segments)
            chunk_duration = 60  # 60 minutes per chunk
            recording_name = f"SCHEDULED - {schedule.name} - Continuous {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            recording = recording_manager.start_recording(
                camera=schedule.camera,
                duration_minutes=chunk_duration,
                recording_name=recording_name,
                user=schedule.created_by,
                is_scheduled=True,
                schedule_id=schedule.id
            )
            
            recording.schedule = schedule
            recording.save()
            
            # Schedule the next continuous recording
            next_start = timezone.now() + timedelta(minutes=chunk_duration)
            next_job_id = f"continuous_{schedule.id}_{int(timezone.now().timestamp())}"
            
            self.scheduler.add_job(
                func=self._start_continuous_recording,
                trigger=DateTrigger(run_date=next_start),
                args=[schedule],
                id=next_job_id,
                name=f"Next continuous recording: {schedule.name}"
            )
            
            logger.info(f"Started continuous recording chunk: {recording_name}")
            
        except Exception as e:
            logger.error(f"Error starting continuous recording for {schedule.name}: {str(e)}")
    
    def remove_schedule(self, schedule_id):
        """Remove a recording schedule"""
        schedule_id_str = str(schedule_id)
        
        if schedule_id_str in self.active_jobs:
            job_ids = self.active_jobs[schedule_id_str].copy()  # Create a copy to avoid modification during iteration
            removed_count = 0
            
            for job_id in job_ids:
                try:
                    # Check if job exists before trying to remove it
                    existing_job = self.scheduler.get_job(job_id)
                    if existing_job:
                        self.scheduler.remove_job(job_id)
                        logger.debug(f"Removed job: {job_id}")
                        removed_count += 1
                    else:
                        logger.debug(f"Job {job_id} not found in scheduler (already removed)")
                except Exception as e:
                    # Only log as debug for 'No job by the id' errors, as they're expected
                    if "No job by the id" in str(e):
                        logger.debug(f"Job {job_id} already removed: {str(e)}")
                    else:
                        logger.warning(f"Error removing job {job_id}: {str(e)}")
            
            del self.active_jobs[schedule_id_str]
            if removed_count > 0:
                logger.info(f"Removed {removed_count} jobs for schedule {schedule_id}")
            else:
                logger.debug(f"No active jobs found to remove for schedule {schedule_id}")
        else:
            logger.debug(f"No active jobs tracked for schedule {schedule_id}")
    
    def update_schedule(self, schedule):
        """Update an existing schedule"""
        # Remove old schedule
        self.remove_schedule(schedule.id)
        
        # Add updated schedule
        if schedule.is_active:
            self.add_schedule(schedule)
    
    def get_active_jobs(self):
        """Get all active scheduled jobs"""
        return self.scheduler.get_jobs()
    
    def shutdown(self):
        """Shutdown the scheduler"""
        self.scheduler.shutdown()
        logger.info("Recording scheduler shutdown")


# Global scheduler instance
recording_scheduler = RecordingScheduler()

# Delay scheduling until after all functions are defined
def _schedule_maintenance_jobs_delayed():
    """Schedule maintenance jobs after all functions are defined"""
    try:
        if recording_scheduler.scheduler and hasattr(recording_scheduler.scheduler, 'running') and recording_scheduler.scheduler.running:
            # Use the existing schedule_cleanup function
            schedule_cleanup()
            logger.info("✅ Scheduled maintenance jobs including GCP sync")
    except Exception as e:
        logger.error(f"Failed to schedule maintenance jobs: {str(e)}")


def initialize_schedules():
    """Initialize all active schedules on startup"""
    try:
        # First, check for 'once' schedules that have passed their time
        check_expired_once_schedules()
        
        active_schedules = RecordingSchedule.objects.filter(is_active=True)
        
        for schedule in active_schedules:
            recording_scheduler.add_schedule(schedule)
        
        logger.info(f"Initialized {active_schedules.count()} recording schedules")
        
    except Exception as e:
        logger.error(f"Error initializing schedules: {str(e)}")


def check_expired_once_schedules():
    """Check for 'once' type schedules that have passed their scheduled time and deactivate them"""
    try:
        current_time = timezone.now()
        
        # Find active 'once' schedules where the scheduled time has passed
        expired_schedules = RecordingSchedule.objects.filter(
            is_active=True,
            schedule_type='once',
            start_date__isnull=False
        )
        
        deactivated_count = 0
        for schedule in expired_schedules:
            # Combine date and time for comparison
            scheduled_datetime = datetime.combine(schedule.start_date, schedule.start_time)
            scheduled_datetime = timezone.make_aware(scheduled_datetime)
            
            # If the scheduled time has passed, deactivate the schedule
            if scheduled_datetime < current_time:
                logger.info(f"Deactivating expired 'once' schedule '{schedule.name}' (ID: {schedule.id}) - scheduled time was {scheduled_datetime}")
                schedule.is_active = False
                schedule.save()
                
                # Remove from active jobs if it exists
                recording_scheduler.remove_schedule(schedule.id)
                deactivated_count += 1
        
        if deactivated_count > 0:
            logger.info(f"Deactivated {deactivated_count} expired 'once' schedules")
            
    except Exception as e:
        logger.error(f"Error checking expired 'once' schedules: {str(e)}")


def cleanup_old_recordings():
    """Clean up old recordings based on camera settings"""
    try:
        from django.db.models import Q
        
        # Get all cameras with auto cleanup enabled
        cameras = Camera.objects.filter(max_recording_hours__gt=0)
        
        for camera in cameras:
            cutoff_time = timezone.now() - timedelta(hours=camera.max_recording_hours)
            
            # Find old recordings
            old_recordings = Recording.objects.filter(
                camera=camera,
                start_time__lt=cutoff_time,
                status='completed'
            )
            
            # Delete files and records
            deleted_count = 0
            for recording in old_recordings:
                try:
                    # Delete file
                    if recording.file_path:
                        file_path = os.path.join(settings.MEDIA_ROOT, recording.file_path)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    
                    # Delete record
                    recording.delete()
                    deleted_count += 1
                    
                except Exception as e:
                    logger.error(f"Error deleting recording {recording.id}: {str(e)}")
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old recordings for camera {camera.name}")
                
    except Exception as e:
        logger.error(f"Error during recording cleanup: {str(e)}")


def sync_recordings_to_gcp():
    """Background task to sync local recordings to GCP storage"""
    try:
        from django.conf import settings
        from .models import Recording
        from .storage_service import storage_service
        import os
        
        # Check if GCP auto-upload is enabled
        if not getattr(settings, 'GCP_STORAGE_AUTO_UPLOAD', True):
            logger.debug("GCP auto-upload is disabled, skipping sync")
            return
            
        if not storage_service.use_gcp:
            logger.debug("GCP storage not available, skipping sync")
            return
        
        # Get recordings that need to be synced (max 10 per run to avoid overload)
        recordings_to_sync = Recording.objects.filter(
            file_path__isnull=False,
            storage_type='local',
            status='completed'
        ).exclude(file_path='')[:10]
        
        if not recordings_to_sync:
            logger.debug("No recordings need GCP sync")
            return
            
        logger.info(f"🔄 Starting background GCP sync for {len(recordings_to_sync)} recordings")
        
        synced_count = 0
        failed_count = 0
        
        for recording in recordings_to_sync:
            try:
                # Check if local file exists
                local_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, recording.file_path))
                
                if not os.path.exists(local_path) or local_path.endswith('.tmp'):
                    continue
                
                # Upload to GCP
                storage_result = storage_service.upload_recording(
                    local_file_path=local_path,
                    recording_id=str(recording.id),
                    camera_id=str(recording.camera.id),
                    filename=os.path.basename(local_path)
                )
                
                if storage_result[0]:  # storage_path is not None
                    storage_path, storage_type = storage_result
                    
                    # Update recording
                    recording.file_path = storage_path
                    recording.storage_type = storage_type
                    recording.save(update_fields=['file_path', 'storage_type'])
                    
                    synced_count += 1
                    logger.info(f"✅ Synced recording {recording.name} to GCP")
                    
                    # Clean up local file if enabled
                    if getattr(settings, 'GCP_STORAGE_CLEANUP_LOCAL', True):
                        try:
                            os.remove(local_path)
                            logger.debug(f"🗑️ Cleaned up local file: {local_path}")
                        except Exception as cleanup_error:
                            logger.warning(f"Failed to cleanup {local_path}: {str(cleanup_error)}")
                else:
                    failed_count += 1
                    logger.warning(f"❌ Failed to sync recording {recording.name} to GCP")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"Error syncing recording {recording.id}: {str(e)}")
        
        if synced_count > 0 or failed_count > 0:
            logger.info(f"🔄 GCP sync completed: {synced_count} synced, {failed_count} failed")
                
    except Exception as e:
        logger.error(f"Error during GCP sync: {str(e)}")


# Schedule cleanup and maintenance jobs
def schedule_cleanup():
    """Schedule the cleanup and maintenance jobs"""
    # Daily cleanup of old recordings
    recording_scheduler.scheduler.add_job(
        func=cleanup_old_recordings,
        trigger=CronTrigger(hour=2, minute=0),  # Run at 2 AM daily
        id='cleanup_old_recordings',
        name='Cleanup old recordings'
    )
    
    # Check for expired 'once' schedules every hour
    recording_scheduler.scheduler.add_job(
        func=check_expired_once_schedules,
        trigger=CronTrigger(minute=0),  # Run every hour
        id='check_expired_schedules',
        name='Check expired once schedules'
    )
    
    # Sync recordings to GCP every 30 minutes
    recording_scheduler.scheduler.add_job(
        func=sync_recordings_to_gcp,
        trigger=CronTrigger(minute='*/30'),  # Run every 30 minutes
        id='sync_recordings_gcp',
        name='Sync recordings to GCP'
    )


# Initialize maintenance jobs after all functions are defined
_schedule_maintenance_jobs_delayed()