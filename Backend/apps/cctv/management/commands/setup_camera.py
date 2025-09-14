"""
Management command to setup a camera and start recording
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.cctv.models import Camera
from apps.cctv.streaming import test_camera_connection, recording_manager
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Setup a camera and start 5-second recording'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--ip',
            type=str,
            required=True,
            help='Camera IP address',
        )
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Camera username',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='',
            help='Camera password (empty for no password)',
        )
        parser.add_argument(
            '--port',
            type=int,
            default=554,
            help='RTSP port (default: 554)',
        )
        parser.add_argument(
            '--name',
            type=str,
            help='Camera name (optional)',
        )
        parser.add_argument(
            '--user',
            type=str,
            default='admin',
            help='Django user who owns the camera (default: admin)',
        )
        parser.add_argument(
            '--record',
            action='store_true',
            help='Start 5-second recording after setup',
        )
    
    def handle(self, *args, **options):
        ip = options['ip']
        username = options['username']
        password = options['password']
        port = options['port']
        name = options['name'] or f"Camera {ip}"
        user_username = options['user']
        start_recording = options['record']
        
        self.stdout.write(
            self.style.SUCCESS(f'Setting up camera: {name}')
        )
        self.stdout.write(f'IP: {ip}')
        self.stdout.write(f'Username: {username}')
        self.stdout.write(f'Port: {port}')
        
        # Get user
        try:
            user = User.objects.get(username=user_username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User "{user_username}" not found. Creating...')
            )
            user = User.objects.create_user(
                username=user_username,
                password='admin123',
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(
                self.style.SUCCESS(f'User "{user_username}" created')
            )
        
        # Build RTSP URL
        if username and password:
            auth = f"{username}:{password}@"
        elif username:
            auth = f"{username}@"  # Username only, no password
        else:
            auth = ""  # No authentication
        rtsp_url = f"rtsp://{auth}{ip}:{port}/stream1"
        
        self.stdout.write(f'RTSP URL: {rtsp_url}')
        
        # Test camera connection
        self.stdout.write('Testing camera connection...')
        success, message = test_camera_connection(rtsp_url)
        
        if not success:
            self.stdout.write(
                self.style.ERROR(f'Camera connection failed: {message}')
            )
            self.stdout.write(
                self.style.WARNING('Creating camera anyway for testing...')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Camera connection successful: {message}')
            )
        
        # Create camera
        try:
            camera, created = Camera.objects.get_or_create(
                ip_address=ip,
                defaults={
                    'name': name,
                    'description': f'Camera at {ip} setup via command',
                    'port': port,
                    'username': username,
                    'password': password,
                    'rtsp_url': rtsp_url,
                    'camera_type': 'rtsp',
                    'status': 'active' if success else 'error',
                    'auto_record': True,
                    'record_quality': 'medium',
                    'created_by': user,
                    'last_seen': timezone.now() if success else None
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Camera created with ID: {camera.id}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Camera already exists with ID: {camera.id}')
                )
                # Update existing camera
                camera.username = username
                camera.password = password
                camera.rtsp_url = rtsp_url
                camera.status = 'active' if success else 'error'
                camera.last_seen = timezone.now() if success else camera.last_seen
                camera.save()
                self.stdout.write('Camera updated with new credentials')
            
            # Start recording if requested
            if start_recording:
                self.stdout.write('Starting 5-second recording...')
                try:
                    recording = camera.auto_record_5min(user=user)
                    if recording:
                        self.stdout.write(
                            self.style.SUCCESS(f'Recording started: {recording.name}')
                        )
                        self.stdout.write(f'Recording ID: {recording.id}')
                        self.stdout.write(f'File will be saved to: media/recordings/{camera.id}/')
                        self.stdout.write(f'Recording duration: 5 seconds')
                        
                        # Show recording end time
                        estimated_end = timezone.now() + timezone.timedelta(seconds=5)
                        self.stdout.write(f'Estimated end time: {estimated_end}')
                        
                    else:
                        self.stdout.write(
                            self.style.ERROR('Failed to start recording')
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Recording error: {str(e)}')
                    )
            
            # Show useful information
            self.stdout.write('\n' + '='*50)
            self.stdout.write(
                self.style.SUCCESS('Camera setup complete!')
            )
            self.stdout.write(f'Camera ID: {camera.id}')
            self.stdout.write(f'Camera Name: {camera.name}')
            self.stdout.write(f'RTSP URL: {camera.rtsp_url}')
            self.stdout.write(f'Status: {camera.status}')
            
            if success:
                self.stdout.write(f'Live Stream URL: http://localhost:8000/v0/api/cctv/cameras/{camera.id}/stream/')
            
            self.stdout.write('\nAPI Endpoints:')
            self.stdout.write(f'  Camera Detail: GET /v0/api/cctv/cameras/{camera.id}/')
            self.stdout.write(f'  Recording Status: GET /v0/api/cctv/cameras/{camera.id}/recording_status/')
            self.stdout.write(f'  Start Recording: POST /v0/api/cctv/cameras/{camera.id}/start_recording/')
            self.stdout.write(f'  Quick Record: POST /v0/api/cctv/cameras/{camera.id}/quick_record/')
            self.stdout.write(f'  Stop Recording: POST /v0/api/cctv/cameras/{camera.id}/stop_recording/')
            self.stdout.write('='*50)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating camera: {str(e)}')
            )
