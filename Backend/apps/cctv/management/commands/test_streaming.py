"""
Django management command to test and diagnose CCTV streaming issues
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from apps.cctv.models import Camera
from apps.cctv.streaming import stream_manager, test_camera_connection
import cv2
import time
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test and diagnose CCTV streaming issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--camera-id',
            type=str,
            help='Test a specific camera by ID'
        )
        parser.add_argument(
            '--test-connection',
            action='store_true',
            help='Test camera connections'
        )
        parser.add_argument(
            '--test-streaming',
            action='store_true',
            help='Test streaming functionality'
        )
        parser.add_argument(
            '--fix-issues',
            action='store_true',
            help='Attempt to fix detected issues'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 CCTV Streaming Diagnostics Tool')
        )
        
        if options['test_connection']:
            self.test_camera_connections()
        
        if options['test_streaming']:
            self.test_streaming_functionality()
        
        if options['fix_issues']:
            self.attempt_fixes()
        
        if not any([options['test_connection'], options['test_streaming'], options['fix_issues']]):
            self.run_full_diagnostic()

    def run_full_diagnostic(self):
        """Run a full diagnostic on all cameras"""
        self.stdout.write('\n📊 Running full diagnostic...')
        
        cameras = Camera.objects.filter(is_active=True)
        self.stdout.write(f'Found {cameras.count()} active cameras')
        
        for camera in cameras:
            self.stdout.write(f'\n🎥 Camera: {camera.name} (ID: {camera.id})')
            self.stdout.write(f'   Status: {camera.status}')
            self.stdout.write(f'   Online: {camera.is_online}')
            self.stdout.write(f'   RTSP URL: {camera.rtsp_url}')
            
            # Test connection
            success, message = test_camera_connection(camera.rtsp_url)
            self.stdout.write(f'   Connection: {"✅" if success else "❌"} {message}')
            
            # Check stream health
            health = stream_manager.get_stream_health(camera.id, 'main')
            self.stdout.write(f'   Stream Health: {health["status"]}')
            
            if health['status'] == 'unhealthy':
                self.stdout.write(f'   Error: {health.get("error", "Unknown")}')

    def test_camera_connections(self):
        """Test connections to all cameras"""
        self.stdout.write('\n🔌 Testing camera connections...')
        
        cameras = Camera.objects.filter(is_active=True)
        
        for camera in cameras:
            self.stdout.write(f'\nTesting {camera.name}...')
            
            try:
                success, message = test_camera_connection(camera.rtsp_url)
                
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {camera.name}: Connection successful')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ {camera.name}: {message}')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ {camera.name}: Exception - {str(e)}')
                )

    def test_streaming_functionality(self):
        """Test streaming functionality for cameras"""
        self.stdout.write('\n🎬 Testing streaming functionality...')
        
        cameras = Camera.objects.filter(is_active=True)
        
        for camera in cameras:
            self.stdout.write(f'\nTesting stream for {camera.name}...')
            
            try:
                # Try to start a stream
                stream_info = stream_manager.start_stream(camera, 'main')
                
                if stream_info:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {camera.name}: Stream started successfully')
                    )
                    
                    # Test frame reading
                    time.sleep(2)  # Wait for frames
                    frame = stream_manager.get_frame(camera.id, 'main')
                    
                    if frame is not None:
                        self.stdout.write(
                            self.style.SUCCESS(f'✅ {camera.name}: Frame reading successful')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'⚠️ {camera.name}: No frames available')
                        )
                    
                    # Stop the stream
                    stream_manager.stop_stream(camera.id, 'main')
                    self.stdout.write(f'🛑 {camera.name}: Stream stopped')
                    
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ {camera.name}: Failed to start stream')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ {camera.name}: Streaming error - {str(e)}')
                )

    def attempt_fixes(self):
        """Attempt to fix detected issues"""
        self.stdout.write('\n🔧 Attempting to fix detected issues...')
        
        cameras = Camera.objects.filter(is_active=True)
        
        for camera in cameras:
            self.stdout.write(f'\nAttempting to fix {camera.name}...')
            
            try:
                # Check if camera needs reconnection
                if not camera.is_online:
                    self.stdout.write(f'   Reconnecting {camera.name}...')
                    camera.mark_as_online()
                    self.stdout.write(f'   ✅ {camera.name} marked as online')
                
                # Check stream health
                health = stream_manager.get_stream_health(camera.id, 'main')
                
                if health['status'] == 'unhealthy':
                    self.stdout.write(f'   Recovering stream for {camera.name}...')
                    recovered = stream_manager.recover_stream(camera.id, 'main')
                    
                    if recovered:
                        self.stdout.write(f'   ✅ {camera.name} stream recovered')
                    else:
                        self.stdout.write(f'   ❌ {camera.name} stream recovery failed')
                else:
                    self.stdout.write(f'   ✅ {camera.name} stream is healthy')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Error fixing {camera.name}: {str(e)}')
                )

    def check_opencv_installation(self):
        """Check OpenCV installation and version"""
        self.stdout.write('\n📦 Checking OpenCV installation...')
        
        try:
            version = cv2.__version__
            self.stdout.write(f'OpenCV version: {version}')
            
            # Test basic OpenCV functionality
            test_frame = cv2.imread(settings.MEDIA_ROOT + '/logo/logo.png')
            if test_frame is not None:
                self.stdout.write('✅ OpenCV image reading: OK')
            else:
                self.stdout.write('⚠️ OpenCV image reading: Test image not found')
                
        except Exception as e:
            self.stdout.write(f'❌ OpenCV error: {str(e)}')
            return False
        
        return True
