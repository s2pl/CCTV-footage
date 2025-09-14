"""
Management command to migrate existing recordings from local storage to GCP Cloud Storage.
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from apps.cctv.models import Recording
from apps.cctv.storage_service import storage_service
import os
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migrate existing recordings from local storage to GCP Cloud Storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually doing it',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of recordings to process in each batch (default: 10)',
        )
        parser.add_argument(
            '--recording-id',
            type=str,
            help='Migrate only a specific recording by ID',
        )
        parser.add_argument(
            '--camera-id',
            type=str,
            help='Migrate recordings for a specific camera only',
        )
        parser.add_argument(
            '--skip-missing',
            action='store_true',
            help='Skip recordings with missing local files instead of failing',
        )
        parser.add_argument(
            '--cleanup-tmp',
            action='store_true',
            help='Clean up .tmp files from the recordings directory',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting Migration to GCP Cloud Storage...\n')
        )

        # Check if GCP is configured
        if not storage_service.use_gcp:
            raise CommandError('GCP Storage is not enabled. Set GCP_STORAGE_USE_GCS=True in your settings.')

        # Get recordings to migrate
        recordings = self.get_recordings_to_migrate(options)

        if not recordings.exists():
            self.stdout.write('ℹ️  No recordings found to migrate.')
            return

        total_count = recordings.count()
        self.stdout.write(f'📊 Found {total_count} recordings to migrate')

        if options['dry_run']:
            self.stdout.write('🔍 DRY RUN MODE - No files will be actually migrated\n')
            self.show_migration_preview(recordings)
            return

        # Confirm migration
        if not self.confirm_migration(total_count):
            self.stdout.write('❌ Migration cancelled by user.')
            return

        # Clean up .tmp files if requested
        if options['cleanup_tmp']:
            self.cleanup_tmp_files()

        # Perform migration
        self.migrate_recordings(recordings, options['batch_size'], options.get('skip_missing', False))

    def get_recordings_to_migrate(self, options):
        """Get recordings that need to be migrated"""
        queryset = Recording.objects.filter(
            file_path__isnull=False,
            storage_type='local'  # Only migrate recordings that are still in local storage
        ).exclude(file_path='').exclude(file_path__endswith='.tmp')  # Exclude .tmp files

        # Filter by specific recording ID
        if options['recording_id']:
            queryset = queryset.filter(id=options['recording_id'])

        # Filter by camera ID
        if options['camera_id']:
            queryset = queryset.filter(camera_id=options['camera_id'])

        return queryset.order_by('created_at')

    def show_migration_preview(self, recordings):
        """Show what would be migrated in dry run mode"""
        self.stdout.write('📋 Migration Preview:')
        self.stdout.write('-' * 80)

        total_size = 0
        for recording in recordings[:20]:  # Show first 20
            local_path = os.path.join(settings.MEDIA_ROOT, recording.file_path)
            file_size = 0
            
            if os.path.exists(local_path):
                file_size = os.path.getsize(local_path)
                total_size += file_size
                status = '✅ Exists'
            else:
                status = '❌ Missing'

            self.stdout.write(
                f'📹 {recording.name[:30]:<30} | '
                f'{recording.camera.name[:20]:<20} | '
                f'{self.format_size(file_size):<10} | '
                f'{status}'
            )

        if recordings.count() > 20:
            self.stdout.write(f'... and {recordings.count() - 20} more recordings')

        self.stdout.write('-' * 80)
        self.stdout.write(f'📊 Total size: {self.format_size(total_size)}')

    def confirm_migration(self, count):
        """Ask user to confirm migration"""
        self.stdout.write(f'\n⚠️  This will migrate {count} recordings to GCP Cloud Storage.')
        self.stdout.write('   Make sure you have:')
        self.stdout.write('   - Sufficient GCP Storage quota')
        self.stdout.write('   - Proper backup of your data')
        self.stdout.write('   - Tested GCP connectivity')
        
        response = input('\nDo you want to continue? (yes/no): ')
        return response.lower() in ['yes', 'y']

    def migrate_recordings(self, recordings, batch_size, skip_missing=False):
        """Perform the actual migration"""
        total_count = recordings.count()
        migrated_count = 0
        failed_count = 0
        skipped_count = 0

        self.stdout.write(f'\n🔄 Starting migration of {total_count} recordings...\n')

        # Process in batches
        for i in range(0, total_count, batch_size):
            batch = recordings[i:i + batch_size]
            self.stdout.write(f'📦 Processing batch {i//batch_size + 1} ({len(batch)} recordings)...')

            for recording in batch:
                try:
                    result = self.migrate_single_recording(recording, skip_missing)
                    if result == 'migrated':
                        migrated_count += 1
                        self.stdout.write(f'  ✅ {recording.name} - {recording.camera.name} - {recording.start_time}')
                    elif result == 'skipped':
                        skipped_count += 1
                        self.stdout.write(f'  ⏭️  {recording.name} - {recording.camera.name} - {recording.start_time} (already in GCP)')
                    elif result == 'missing':
                        if skip_missing:
                            skipped_count += 1
                            self.stdout.write(f'  ⚠️  {recording.name} - {recording.camera.name} - {recording.start_time} (missing file, skipped)')
                        else:
                            failed_count += 1
                            self.stdout.write(f'  ❌ {recording.name} - {recording.camera.name} - {recording.start_time} (missing file)')
                    else:
                        failed_count += 1
                        self.stdout.write(f'  ❌ {recording.name} - {recording.camera.name} - {recording.start_time} (failed)')

                except Exception as e:
                    failed_count += 1
                    logger.error(f'Error migrating recording {recording.id}: {str(e)}')
                    self.stdout.write(f'  ❌ {recording.name} - {recording.camera.name} - {recording.start_time} (error: {str(e)[:100]})')

            # Progress update
            processed = min(i + batch_size, total_count)
            self.stdout.write(f'📊 Progress: {processed}/{total_count} ({processed/total_count*100:.1f}%)\n')

        # Final summary
        self.stdout.write('🎉 Migration completed!')
        self.stdout.write('-' * 50)
        self.stdout.write(f'✅ Successfully migrated: {migrated_count}')
        self.stdout.write(f'⏭️  Skipped (already in GCP or missing files): {skipped_count}')
        self.stdout.write(f'❌ Failed: {failed_count}')
        self.stdout.write(f'📊 Total processed: {migrated_count + skipped_count + failed_count}')

        if failed_count > 0:
            self.stdout.write('\n⚠️  Some recordings failed to migrate. Check the logs for details.')

    def migrate_single_recording(self, recording, skip_missing=False):
        """Migrate a single recording to GCP Storage"""
        # Check if file already exists in GCP
        if storage_service.file_exists(recording.file_path):
            return 'skipped'

        # Normalize and check local file path
        local_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, recording.file_path))
        
        # Skip .tmp files
        if local_path.endswith('.tmp'):
            logger.warning(f'Skipping .tmp file: {local_path}')
            return 'missing' if skip_missing else 'failed'
            
        if not os.path.exists(local_path):
            logger.warning(f'Local file not found: {local_path}')
            return 'missing' if skip_missing else 'failed'

        # Get file size before upload
        try:
            file_size = os.path.getsize(local_path)
        except Exception as e:
            logger.error(f'Cannot get file size for {local_path}: {str(e)}')
            return 'failed'

        # Upload to GCP Storage with increased timeout for large files
        timeout = 300 if file_size < 100 * 1024 * 1024 else 600  # 5min for small files, 10min for large
        
        success = storage_service.gcp_service.upload_file(
            local_path,
            recording.file_path,
            content_type=self.get_content_type(recording.file_path),
            timeout=timeout
        )

        if success:
            # Update storage type and file size
            recording.storage_type = 'gcp'
            
            # Update file size from GCP if available
            gcp_size = storage_service.gcp_service.get_file_size(recording.file_path)
            if gcp_size:
                recording.file_size = gcp_size
            else:
                recording.file_size = file_size  # Use local file size as fallback
                
            recording.save(update_fields=['storage_type', 'file_size'])

            # Optionally remove local file after successful upload
            # Uncomment the following lines if you want to delete local files after migration
            # try:
            #     os.remove(local_path)
            #     logger.info(f'Removed local file after migration: {local_path}')
            # except Exception as e:
            #     logger.warning(f'Failed to remove local file {local_path}: {str(e)}')

            return 'migrated'
        else:
            return 'failed'

    def get_content_type(self, file_path):
        """Get content type based on file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        content_types = {
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska',
            '.webm': 'video/webm',
            '.flv': 'video/x-flv',
        }
        return content_types.get(ext, 'video/mp4')

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
    
    def cleanup_tmp_files(self):
        """Clean up .tmp files from recordings directory"""
        self.stdout.write('🧹 Cleaning up .tmp files...')
        
        recordings_dir = os.path.join(settings.MEDIA_ROOT, 'recordings')
        if not os.path.exists(recordings_dir):
            self.stdout.write('📁 Recordings directory not found')
            return
            
        tmp_files_removed = 0
        for root, dirs, files in os.walk(recordings_dir):
            for file in files:
                if file.endswith('.tmp'):
                    tmp_file_path = os.path.join(root, file)
                    try:
                        os.remove(tmp_file_path)
                        tmp_files_removed += 1
                        self.stdout.write(f'  🗑️  Removed: {tmp_file_path}')
                    except Exception as e:
                        self.stdout.write(f'  ❌ Failed to remove {tmp_file_path}: {str(e)}')
        
        self.stdout.write(f'✅ Removed {tmp_files_removed} .tmp files\n')
