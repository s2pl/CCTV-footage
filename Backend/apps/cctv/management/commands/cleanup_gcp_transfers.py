"""
Management command to clean up local video files after GCP transfer completion.
This command should be run periodically (e.g., every hour) to check for files
that are due for cleanup (24 hours after GCP upload completion).
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
from apps.cctv.models import GCPVideoTransfer
import os
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up local video files 24 hours after successful GCP transfer'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned up without actually deleting files',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force cleanup even if not yet 24 hours old (use with caution)',
        )
        parser.add_argument(
            '--transfer-id',
            type=str,
            help='Clean up a specific transfer by ID',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🧹 Starting GCP Transfer Cleanup...\n')
        )

        # Get transfers that are due for cleanup
        transfers = self.get_transfers_for_cleanup(options)

        if not transfers.exists():
            self.stdout.write('ℹ️  No transfers found that are due for cleanup.')
            return

        total_count = transfers.count()
        self.stdout.write(f'📊 Found {total_count} transfers due for cleanup')

        if options['dry_run']:
            self.stdout.write('🔍 DRY RUN MODE - No files will be actually deleted\n')
            self.show_cleanup_preview(transfers)
            return

        # Perform cleanup
        self.cleanup_transfers(transfers, options.get('force', False))

    def get_transfers_for_cleanup(self, options):
        """Get transfers that are due for cleanup"""
        queryset = GCPVideoTransfer.objects.filter(
            transfer_status__in=['completed', 'cleanup_pending'],
            upload_completed_at__isnull=False,
            cleanup_completed_at__isnull=True,  # Not yet cleaned up
        )

        # Filter by specific transfer ID
        if options['transfer_id']:
            queryset = queryset.filter(id=options['transfer_id'])
        elif not options.get('force', False):
            # Only include transfers that are actually due for cleanup (24 hours old)
            from datetime import timedelta
            cleanup_threshold = timezone.now() - timedelta(hours=24)
            queryset = queryset.filter(upload_completed_at__lte=cleanup_threshold)

        return queryset.select_related('recording', 'recording__camera')

    def show_cleanup_preview(self, transfers):
        """Show what would be cleaned up in dry run mode"""
        self.stdout.write('📋 Files that would be cleaned up:')
        self.stdout.write('-' * 80)
        
        total_size = 0
        for transfer in transfers:
            local_file_path = os.path.join(settings.MEDIA_ROOT, transfer.original_local_path)
            file_exists = os.path.exists(local_file_path)
            file_size = 0
            
            if file_exists:
                file_size = os.path.getsize(local_file_path)
                total_size += file_size
            
            status_icon = "✅" if file_exists else "❌"
            size_mb = round(file_size / (1024 * 1024), 2) if file_size > 0 else 0
            
            self.stdout.write(
                f'{status_icon} {transfer.recording.name} '
                f'({size_mb} MB) - {local_file_path}'
            )
            
            if not file_exists:
                self.stdout.write(f'    ⚠️  File already missing')
        
        self.stdout.write('-' * 80)
        total_size_mb = round(total_size / (1024 * 1024), 2)
        self.stdout.write(f'📊 Total space to be freed: {total_size_mb} MB')

    def cleanup_transfers(self, transfers, force=False):
        """Perform the actual cleanup of local files"""
        cleaned_count = 0
        failed_count = 0
        already_missing_count = 0
        total_size_freed = 0

        for transfer in transfers:
            try:
                local_file_path = os.path.join(settings.MEDIA_ROOT, transfer.original_local_path)
                
                # Check if file exists
                if not os.path.exists(local_file_path):
                    self.stdout.write(
                        f'⚠️  File already missing: {transfer.recording.name}'
                    )
                    # Mark as cleaned up even if file was already missing
                    transfer.mark_cleanup_completed()
                    already_missing_count += 1
                    continue
                
                # Check if cleanup is actually due (unless forced)
                if not force and not transfer.is_cleanup_due:
                    self.stdout.write(
                        f'⏰ Cleanup not yet due for: {transfer.recording.name} '
                        f'(uploaded {transfer.upload_completed_at})'
                    )
                    continue
                
                # Get file size before deletion
                file_size = os.path.getsize(local_file_path)
                
                # Delete the local file
                os.remove(local_file_path)
                
                # Mark transfer as cleaned up
                transfer.mark_cleanup_completed()
                
                size_mb = round(file_size / (1024 * 1024), 2)
                total_size_freed += file_size
                cleaned_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Cleaned up: {transfer.recording.name} ({size_mb} MB)'
                    )
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Failed to clean up {transfer.recording.name}: {str(e)}'
                    )
                )
                failed_count += 1

        # Final summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('📊 Cleanup Summary:')
        self.stdout.write(f'   ✅ Files cleaned up: {cleaned_count}')
        self.stdout.write(f'   ⚠️  Already missing: {already_missing_count}')
        self.stdout.write(f'   ❌ Failed cleanups: {failed_count}')
        
        total_freed_mb = round(total_size_freed / (1024 * 1024), 2)
        self.stdout.write(f'   💾 Space freed: {total_freed_mb} MB')
        
        if cleaned_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n🎉 Successfully cleaned up {cleaned_count} files!')
            )
        
        if failed_count > 0:
            self.stdout.write(
                self.style.WARNING(f'\n⚠️  {failed_count} files failed to clean up. Check logs for details.')
            )
