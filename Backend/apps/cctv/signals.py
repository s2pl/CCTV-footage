"""
Django signals for CCTV app
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import RecordingSchedule, Recording
from .scheduler import recording_scheduler
import logging
import threading

logger = logging.getLogger(__name__)

# Track recordings being processed to avoid duplicate uploads
_upload_in_progress = set()


@receiver(post_save, sender=RecordingSchedule)
def handle_schedule_save(sender, instance, created, **kwargs):
    """Handle when a recording schedule is saved"""
    try:
        if created and instance.is_active:
            # Add new schedule
            recording_scheduler.add_schedule(instance)
            logger.info(f"Added new recording schedule: {instance.name}")
        elif not created:
            # Update existing schedule
            recording_scheduler.update_schedule(instance)
            logger.info(f"Updated recording schedule: {instance.name}")
    except Exception as e:
        logger.error(f"Error handling schedule save for {instance.name}: {str(e)}")


@receiver(post_delete, sender=RecordingSchedule)
def handle_schedule_delete(sender, instance, **kwargs):
    """Handle when a recording schedule is deleted"""
    try:
        recording_scheduler.remove_schedule(instance.id)
        logger.info(f"Removed recording schedule: {instance.name}")
    except Exception as e:
        logger.error(f"Error handling schedule delete for {instance.name}: {str(e)}")


@receiver(post_save, sender=Recording)
def handle_recording_completion(sender, instance, created, **kwargs):
    """Handle recording completion and ensure GCP upload"""
    # Only process completed recordings that are in local storage
    if (instance.status == 'completed' and 
        instance.storage_type == 'local' and 
        instance.file_path and 
        not instance.file_path.endswith('.tmp')):
        
        # Run upload in background thread to avoid blocking
        def background_upload():
            try:
                from django.conf import settings
                from .storage_service import storage_service
                import os
                
                # Only proceed if GCP is enabled
                if not getattr(settings, 'GCP_STORAGE_USE_GCS', False):
                    return
                    
                if not storage_service.use_gcp:
                    return
                
                # Get full file path
                local_file_path = os.path.join(settings.MEDIA_ROOT, instance.file_path)
                
                # Check if file exists
                if not os.path.exists(local_file_path):
                    logger.warning(f"Signal upload: File not found for recording {instance.id}: {local_file_path}")
                    return
                
                logger.info(f"🔄 Signal-triggered upload for recording {instance.id}: {instance.name}")
                
                # Upload to GCP
                storage_result = storage_service.upload_recording(
                    local_file_path=local_file_path,
                    recording_id=str(instance.id),
                    camera_id=str(instance.camera.id),
                    filename=os.path.basename(local_file_path)
                )
                
                if storage_result[0]:  # storage_path is not None
                    storage_path, storage_type = storage_result
                    
                    # Update recording with GCP storage info
                    Recording.objects.filter(id=instance.id).update(
                        file_path=storage_path,
                        storage_type=storage_type
                    )
                    
                    logger.info(f"✅ Signal upload successful for recording {instance.id}: {storage_path}")
                    
                    # Clean up local file if enabled
                    if getattr(settings, 'GCP_STORAGE_CLEANUP_LOCAL', True):
                        try:
                            import time
                            time.sleep(2)  # Wait for GCP to process
                            os.remove(local_file_path)
                            logger.info(f"🗑️ Local file cleaned up via signal: {local_file_path}")
                        except Exception as cleanup_error:
                            logger.warning(f"Signal cleanup failed: {str(cleanup_error)}")
                else:
                    logger.warning(f"Signal upload failed for recording {instance.id}, will retry via background sync")
                    
            except Exception as e:
                logger.error(f"Error in signal-triggered upload for recording {instance.id}: {str(e)}")
        
        # Start background thread (don't block the main process)
        thread = threading.Thread(target=background_upload, daemon=True)
        thread.start()
        logger.debug(f"Started background upload thread for recording {instance.id}")
