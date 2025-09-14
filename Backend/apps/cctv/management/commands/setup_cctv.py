"""
Management command to initialize CCTV system
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Initialize CCTV system with required directories and settings'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-dirs',
            action='store_true',
            help='Create required media directories',
        )
        parser.add_argument(
            '--init-scheduler',
            action='store_true',
            help='Initialize recording scheduler',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Setting up CCTV system...')
        )
        
        if options['create_dirs']:
            self.create_media_directories()
        
        if options['init_scheduler']:
            self.initialize_scheduler()
        
        self.stdout.write(
            self.style.SUCCESS('CCTV system setup completed!')
        )
    
    def create_media_directories(self):
        """Create required media directories"""
        directories = [
            'recordings',
            'thumbnails',
            'logs'
        ]
        
        for directory in directories:
            dir_path = os.path.join(settings.MEDIA_ROOT, directory)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                self.stdout.write(f'Created directory: {dir_path}')
            else:
                self.stdout.write(f'Directory already exists: {dir_path}')
    
    def initialize_scheduler(self):
        """Initialize the recording scheduler"""
        try:
            from apps.cctv.scheduler import initialize_schedules, schedule_cleanup
            
            # Initialize existing schedules
            initialize_schedules()
            self.stdout.write('Initialized recording schedules')
            
            # Schedule cleanup job
            schedule_cleanup()
            self.stdout.write('Scheduled cleanup job')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error initializing scheduler: {str(e)}')
            )
