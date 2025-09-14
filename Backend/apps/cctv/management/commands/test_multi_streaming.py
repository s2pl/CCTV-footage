"""
Django management command to test multi-camera streaming functionality
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
    help = 'Test multi-camera streaming functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-all',
            action='store_true',
            help='Test all cameras simultaneously'
        )
        parser.add_argument(
            '--test-multi',
            action='store_true',
            help='Test multiple camera streams'
        )
        parser.add_argument(
            '--test-api',
            action='store_true',
            help='Test streaming API endpoints'
        )
        parser.add_argument(
            '--duration',
            type=int,
            default=30,
            help='Test duration in seconds'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🎥 Multi-Camera Streaming Test Tool')
        )
        
        if options['test_all']:
            self.test_all_cameras()
        
        if options['test_multi']:
            self.test_multi_camera_streams(options['duration'])
        
        if options['test_api']:
            self.test_streaming_api()
        
        if not any([options['test_all'], options['test_multi'], options['test_api']]):
            self.run_comprehensive_test(options['duration'])

    def run_comprehensive_test(self, duration):
        """Run a comprehensive test of multi-camera streaming"""
        self.stdout.write('\n🔍 Running comprehensive multi-camera streaming test...')
        
        # Test 1: Camera connections
        self.test_camera_connections()
        
        # Test 2: Multi-camera streaming
        self.test_multi_camera_streams(duration)
        
        # Test 3: API endpoints
        self.test_streaming_api()
        
        # Test 4: Stream health monitoring
        self.test_stream_health()

    def test_camera_connections(self):
        """Test connections to all cameras"""
        self.stdout.write('\n🔌 Testing camera connections...')
        
        cameras = Camera.objects.filter(is_active=True)
        self.stdout.write(f'Found {cameras.count()} active cameras')
        
        connection_results = {}
        
        for camera in cameras:
            self.stdout.write(f'\nTesting {camera.name}...')
            
            try:
                success, message = test_camera_connection(camera.rtsp_url)
                connection_results[str(camera.id)] = {
                    'success': success,
                    'message': message,
                    'camera_name': camera.name
                }
                
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {camera.name}: Connection successful')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ {camera.name}: {message}')
                    )
                    
            except Exception as e:
                connection_results[str(camera.id)] = {
                    'success': False,
                    'message': str(e),
                    'camera_name': camera.name
                }
                self.stdout.write(
                    self.style.ERROR(f'❌ {camera.name}: Exception - {str(e)}')
                )
        
        # Summary
        successful_connections = sum(1 for result in connection_results.values() if result['success'])
        self.stdout.write(f'\n📊 Connection Summary: {successful_connections}/{len(connection_results)} successful')
        
        return connection_results

    def test_multi_camera_streams(self, duration):
        """Test multiple camera streams simultaneously"""
        self.stdout.write(f'\n🎬 Testing multi-camera streaming for {duration} seconds...')
        
        cameras = Camera.objects.filter(is_active=True)
        if cameras.count() == 0:
            self.stdout.write(self.style.WARNING('No cameras available for testing'))
            return
        
        # Start streams for all cameras
        self.stdout.write('Starting streams for all cameras...')
        started_streams = {}
        
        for camera in cameras:
            try:
                stream_info = stream_manager.start_stream(camera, 'main')
                if stream_info:
                    started_streams[str(camera.id)] = {
                        'camera': camera,
                        'stream_info': stream_info,
                        'start_time': time.time()
                    }
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {camera.name}: Stream started')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ {camera.name}: Failed to start stream')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ {camera.name}: Error - {str(e)}')
                )
        
        if not started_streams:
            self.stdout.write(self.style.ERROR('No streams started successfully'))
            return
        
        # Monitor streams
        self.stdout.write(f'\n📺 Monitoring {len(started_streams)} active streams...')
        start_time = time.time()
        
        while (time.time() - start_time) < duration:
            elapsed = time.time() - start_time
            remaining = duration - elapsed
            
            self.stdout.write(f'\r⏱️  Elapsed: {elapsed:.1f}s, Remaining: {remaining:.1f}s', ending='')
            
            # Check stream health
            healthy_streams = 0
            for camera_id, stream_data in started_streams.items():
                try:
                    frame = stream_manager.get_frame(camera_id, 'main')
                    if frame is not None:
                        healthy_streams += 1
                except:
                    pass
            
            self.stdout.write(f' | Healthy: {healthy_streams}/{len(started_streams)}', ending='')
            
            time.sleep(1)
        
        self.stdout.write('\n')  # New line after progress
        
        # Stop all streams
        self.stdout.write('\n🛑 Stopping all streams...')
        for camera_id, stream_data in started_streams.items():
            try:
                stream_manager.stop_stream(camera_id, 'main')
                camera_name = stream_data['camera'].name
                self.stdout.write(f'✅ {camera_name}: Stream stopped')
            except Exception as e:
                camera_name = stream_data['camera'].name
                self.stdout.write(f'❌ {camera_name}: Error stopping - {str(e)}')
        
        # Final summary
        total_duration = time.time() - start_time
        self.stdout.write(f'\n📊 Multi-Stream Test Summary:')
        self.stdout.write(f'   Total cameras tested: {len(started_streams)}')
        self.stdout.write(f'   Test duration: {total_duration:.1f} seconds')
        self.stdout.write(f'   Streams started: {len(started_streams)}')

    def test_streaming_api(self):
        """Test streaming API endpoints"""
        self.stdout.write('\n🌐 Testing streaming API endpoints...')
        
        cameras = Camera.objects.filter(is_active=True)
        if cameras.count() == 0:
            self.stdout.write(self.style.WARNING('No cameras available for API testing'))
            return
        
        camera = cameras.first()
        self.stdout.write(f'Testing API with camera: {camera.name}')
        
        # Test stream info endpoint
        try:
            from apps.cctv.api import camera_stream_info
            from django.test import RequestFactory
            from django.contrib.auth import get_user_model
            
            # Create a mock request
            factory = RequestFactory()
            User = get_user_model()
            user = User.objects.filter(is_superuser=True).first()
            
            if user:
                request = factory.get(f'/cameras/{camera.id}/stream/info/')
                request.user = user
                
                # Test the endpoint
                response = camera_stream_info(request, camera.id)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Stream info API: Working')
                )
                self.stdout.write(f'   Camera: {response["camera_name"]}')
                self.stdout.write(f'   Status: {response["status"]}')
                self.stdout.write(f'   Streaming: {response["is_streaming"]}')
            else:
                self.stdout.write(
                    self.style.WARNING('⚠️ No superuser found for API testing')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Stream info API error: {str(e)}')
            )

    def test_stream_health(self):
        """Test stream health monitoring"""
        self.stdout.write('\n💓 Testing stream health monitoring...')
        
        cameras = Camera.objects.filter(is_active=True)
        if cameras.count() == 0:
            self.stdout.write(self.style.WARNING('No cameras available for health testing'))
            return
        
        for camera in cameras:
            try:
                health = stream_manager.get_stream_health(camera.id, 'main')
                self.stdout.write(f'\n📊 {camera.name} Health:')
                self.stdout.write(f'   Status: {health["status"]}')
                
                if health['status'] == 'unhealthy':
                    self.stdout.write(f'   Error: {health.get("error", "Unknown")}')
                elif health['status'] == 'healthy':
                    self.stdout.write(f'   Last Update: {health.get("last_update", "Unknown")}')
                    self.stdout.write(f'   Viewers: {health.get("viewers", 0)}')
                    self.stdout.write(f'   Frame Count: {health.get("frame_count", 0)}')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ {camera.name} health check error: {str(e)}')
                )

    def test_all_cameras(self):
        """Test all cameras with comprehensive checks"""
        self.stdout.write('\n🎯 Testing all cameras comprehensively...')
        
        # Get all cameras
        cameras = Camera.objects.filter(is_active=True)
        self.stdout.write(f'Found {cameras.count()} active cameras')
        
        if cameras.count() == 0:
            self.stdout.write(self.style.WARNING('No cameras available for testing'))
            return
        
        # Test each camera individually
        for i, camera in enumerate(cameras, 1):
            self.stdout.write(f'\n{"="*50}')
            self.stdout.write(f'Camera {i}/{cameras.count()}: {camera.name}')
            self.stdout.write(f'{"="*50}')
            
            # Test connection
            try:
                success, message = test_camera_connection(camera.rtsp_url)
                if success:
                    self.stdout.write(f'✅ Connection: {message}')
                    
                    # Test streaming
                    try:
                        stream_info = stream_manager.start_stream(camera, 'main')
                        if stream_info:
                            self.stdout.write(f'✅ Streaming: Started successfully')
                            
                            # Test frame reading
                            time.sleep(2)
                            frame = stream_manager.get_frame(camera.id, 'main')
                            if frame is not None:
                                self.stdout.write(f'✅ Frame Reading: Working')
                                self.stdout.write(f'   Frame shape: {frame.shape}')
                            else:
                                self.stdout.write(f'⚠️ Frame Reading: No frames available')
                            
                            # Stop stream
                            stream_manager.stop_stream(camera.id, 'main')
                            self.stdout.write(f'🛑 Streaming: Stopped')
                        else:
                            self.stdout.write(f'❌ Streaming: Failed to start')
                    except Exception as e:
                        self.stdout.write(f'❌ Streaming Error: {str(e)}')
                else:
                    self.stdout.write(f'❌ Connection: {message}')
            except Exception as e:
                self.stdout.write(f'❌ Connection Error: {str(e)}')
        
        self.stdout.write(f'\n{"="*50}')
        self.stdout.write('Comprehensive test completed!')
        self.stdout.write(f'{"="*50}')
