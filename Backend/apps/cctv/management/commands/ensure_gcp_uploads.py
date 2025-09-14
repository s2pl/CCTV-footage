"""
Management command to ensure all recordings are uploaded to GCP
This can be run as a cron job to guarantee no recordings are missed
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from apps.cctv.models import Recording
from apps.cctv.storage_service import storage_service
import os
import time
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Ensure all completed recordings are uploaded to GCP storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force upload even if auto-upload is disabled',
        )
        parser.add_argument(
            '--max-age-hours',
            type=int,
            default=168,  # 7 days
            help='Only process recordings newer than this many hours (default: 168 = 7 days)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Maximum number of recordings to process in one run (default: 10)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔄 Ensuring GCP uploads are complete...\n')
        )

        # Check if GCP auto-upload is enabled
        if not getattr(settings, 'GCP_STORAGE_AUTO_UPLOAD', True) and not options['force']:
            self.stdout.write(
                self.style.WARNING('⚠️  GCP_STORAGE_AUTO_UPLOAD is disabled. Use --force to override.')
            )
            return

        # Check if GCP is configured
        if not storage_service.use_gcp:
            self.stdout.write(
                self.style.ERROR('❌ GCP Storage is not enabled or available.')
            )
            return

        # Get recordings that need uploading
        from datetime import timedelta
        from django.utils import timezone
        
        cutoff_time = timezone.now() - timedelta(hours=options['max_age_hours'])
        
        recordings_to_upload = Recording.objects.filter(
            status='completed',
            storage_type='local',
            created_at__gte=cutoff_time
        ).exclude(
            file_path=''
        ).exclude(
            file_path__endswith='.tmp'
        )[:options['batch_size']]

        if not recordings_to_upload:
            self.stdout.write('✅ All recordings are already uploaded to GCP!')
            return

        total_count = recordings_to_upload.count()
        self.stdout.write(f'📊 Found {total_count} recordings to upload')

        uploaded_count = 0
        failed_count = 0
        skipped_count = 0

        for recording in recordings_to_upload:
            try:
                result = self.upload_single_recording(recording)
                if result == 'uploaded':
                    uploaded_count += 1
                    self.stdout.write(f'  ✅ {recording.name} - {recording.camera.name}')
                elif result == 'skipped':
                    skipped_count += 1
                    self.stdout.write(f'  ⏭️  {recording.name} - {recording.camera.name} (file missing)')
                else:
                    failed_count += 1
                    self.stdout.write(f'  ❌ {recording.name} - {recording.camera.name} (failed)')

            except Exception as e:
                failed_count += 1
                logger.error(f'Error uploading recording {recording.id}: {str(e)}')
                self.stdout.write(f'  ❌ {recording.name} - {recording.camera.name} (error: {str(e)[:50]})')

        # Final summary
        self.stdout.write('\n🎉 Upload check completed!')
        self.stdout.write('-' * 40)
        self.stdout.write(f'✅ Successfully uploaded: {uploaded_count}')
        self.stdout.write(f'⏭️  Skipped (missing files): {skipped_count}')
        self.stdout.write(f'❌ Failed: {failed_count}')
        self.stdout.write(f'📊 Total processed: {uploaded_count + skipped_count + failed_count}')

        if failed_count > 0:
            self.stdout.write('\n⚠️  Some recordings failed to upload. Check the logs for details.')

    def upload_single_recording(self, recording):
        """Upload a single recording to GCP Storage"""
        # Check if local file exists
        local_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, recording.file_path))
        
        if not os.path.exists(local_path):
            logger.warning(f'Local file not found for recording {recording.id}: {local_path}')
            return 'skipped'

        # Skip .tmp files
        if local_path.endswith('.tmp'):
            logger.warning(f'Skipping .tmp file: {local_path}')
            return 'skipped'

        try:
            # Upload to GCP Storage using the storage service
            storage_result = storage_service.upload_recording(
                local_file_path=local_path,
                recording_id=str(recording.id),
                camera_id=str(recording.camera.id),
                filename=os.path.basename(local_path)
            )

            if storage_result[0]:  # storage_path is not None
                storage_path, storage_type = storage_result
                
                # Update recording with GCP storage info
                recording.file_path = storage_path
                recording.storage_type = storage_type
                recording.save(update_fields=['file_path', 'storage_type'])

                # Clean up local file after successful upload if enabled
                if getattr(settings, 'GCP_STORAGE_CLEANUP_LOCAL', True):
                    try:
                        time.sleep(2)  # Wait for GCP to process
                        os.remove(local_path)
                        logger.info(f'Cleaned up local file after upload: {local_path}')
                    except Exception as cleanup_error:
                        logger.warning(f'Failed to cleanup local file {local_path}: {str(cleanup_error)}')

                return 'uploaded'
            else:
                return 'failed'

        except Exception as e:
            logger.error(f'Error uploading recording {recording.id}: {str(e)}')
            return 'failed'
