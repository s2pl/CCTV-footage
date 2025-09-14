"""
Management command to sync local recordings to GCP Cloud Storage.
This command can be run periodically to ensure all recordings are uploaded to GCP.
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from apps.cctv.models import Recording
from apps.cctv.storage_service import storage_service
import os
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync local recordings to GCP Cloud Storage (auto-upload missed recordings)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without actually doing it',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=5,
            help='Number of recordings to process in each batch (default: 5)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force upload even if GCP_STORAGE_AUTO_UPLOAD is disabled',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔄 Starting GCP Recording Sync...\n')
        )

        # Check if GCP auto-upload is enabled
        if not getattr(settings, 'GCP_STORAGE_AUTO_UPLOAD', True) and not options['force']:
            self.stdout.write(
                self.style.WARNING('⚠️  GCP_STORAGE_AUTO_UPLOAD is disabled. Use --force to override.')
            )
            return

        # Check if GCP is configured
        if not storage_service.use_gcp:
            raise CommandError('GCP Storage is not enabled or available. Check your configuration.')

        # Get recordings that need to be synced
        recordings = self.get_recordings_to_sync()

        if not recordings.exists():
            self.stdout.write('✅ All recordings are already synced to GCP.')
            return

        total_count = recordings.count()
        self.stdout.write(f'📊 Found {total_count} recordings to sync to GCP')

        if options['dry_run']:
            self.stdout.write('🔍 DRY RUN MODE - No files will be actually synced\n')
            self.show_sync_preview(recordings)
            return

        # Perform sync
        self.sync_recordings(recordings, options['batch_size'])

    def get_recordings_to_sync(self):
        """Get recordings that are in local storage but should be in GCP"""
        return Recording.objects.filter(
            file_path__isnull=False,
            storage_type='local',
            status='completed'  # Only sync completed recordings
        ).exclude(file_path='').order_by('-created_at')

    def show_sync_preview(self, recordings):
        """Show what would be synced in dry run mode"""
        self.stdout.write('📋 Sync Preview:')
        self.stdout.write('-' * 80)

        total_size = 0
        for recording in recordings[:20]:  # Show first 20
            local_path = os.path.join(settings.MEDIA_ROOT, recording.file_path)
            file_size = recording.file_size or 0
            
            if os.path.exists(local_path):
                if not file_size:
                    try:
                        file_size = os.path.getsize(local_path)
                    except:
                        file_size = 0
                total_size += file_size
                status = '✅ Ready'
            else:
                status = '❌ Missing'

            self.stdout.write(
                f'📹 {recording.name[:35]:<35} | '
                f'{recording.camera.name[:15]:<15} | '
                f'{self.format_size(file_size):<10} | '
                f'{status}'
            )

        if recordings.count() > 20:
            self.stdout.write(f'... and {recordings.count() - 20} more recordings')

        self.stdout.write('-' * 80)
        self.stdout.write(f'📊 Total size to sync: {self.format_size(total_size)}')

    def sync_recordings(self, recordings, batch_size):
        """Perform the actual sync"""
        total_count = recordings.count()
        synced_count = 0
        failed_count = 0
        skipped_count = 0

        self.stdout.write(f'\n🔄 Starting sync of {total_count} recordings...\n')

        # Process in batches
        for i in range(0, total_count, batch_size):
            batch = recordings[i:i + batch_size]
            self.stdout.write(f'📦 Processing batch {i//batch_size + 1} ({len(batch)} recordings)...')

            for recording in batch:
                try:
                    result = self.sync_single_recording(recording)
                    if result == 'synced':
                        synced_count += 1
                        self.stdout.write(f'  ✅ {recording.name} - {recording.camera.name}')
                    elif result == 'skipped':
                        skipped_count += 1
                        self.stdout.write(f'  ⏭️  {recording.name} - {recording.camera.name} (file missing)')
                    else:
                        failed_count += 1
                        self.stdout.write(f'  ❌ {recording.name} - {recording.camera.name} (failed)')

                except Exception as e:
                    failed_count += 1
                    logger.error(f'Error syncing recording {recording.id}: {str(e)}')
                    self.stdout.write(f'  ❌ {recording.name} - {recording.camera.name} (error: {str(e)[:50]})')

            # Progress update
            processed = min(i + batch_size, total_count)
            self.stdout.write(f'📊 Progress: {processed}/{total_count} ({processed/total_count*100:.1f}%)\n')

        # Final summary
        self.stdout.write('🎉 Sync completed!')
        self.stdout.write('-' * 50)
        self.stdout.write(f'✅ Successfully synced: {synced_count}')
        self.stdout.write(f'⏭️  Skipped (missing files): {skipped_count}')
        self.stdout.write(f'❌ Failed: {failed_count}')
        self.stdout.write(f'📊 Total processed: {synced_count + skipped_count + failed_count}')

        if failed_count > 0:
            self.stdout.write('\n⚠️  Some recordings failed to sync. Check the logs for details.')

    def sync_single_recording(self, recording):
        """Sync a single recording to GCP Storage"""
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

                # Optionally clean up local file after successful upload
                if getattr(settings, 'GCP_STORAGE_CLEANUP_LOCAL', True):
                    try:
                        os.remove(local_path)
                        logger.info(f'Cleaned up local file after sync: {local_path}')
                    except Exception as cleanup_error:
                        logger.warning(f'Failed to cleanup local file {local_path}: {str(cleanup_error)}')

                return 'synced'
            else:
                return 'failed'

        except Exception as e:
            logger.error(f'Error syncing recording {recording.id}: {str(e)}')
            return 'failed'

    def format_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
