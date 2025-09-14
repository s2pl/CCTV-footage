"""
Management command to warm up codec cache on startup
"""

from django.core.management.base import BaseCommand
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Warm up codec cache for faster recording startup'

    def handle(self, *args, **options):
        self.stdout.write('Warming up codec cache...')
        
        try:
            from apps.cctv.opencv_config import get_cached_working_codecs
            
            # Test common recording resolutions
            common_resolutions = [
                (640, 480, 25),    # VGA
                (1280, 720, 25),   # 720p
                (1920, 1080, 25),  # 1080p
            ]
            
            total_cached = 0
            for width, height, fps in common_resolutions:
                working_codecs = get_cached_working_codecs(width, height, fps)
                total_cached += len(working_codecs)
                self.stdout.write(f'  {width}x{height}@{fps}fps: {len(working_codecs)} codecs cached')
            
            self.stdout.write(self.style.SUCCESS(f'✅ Codec cache warmed up with {total_cached} total codec configurations'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error warming up codec cache: {str(e)}'))
            logger.exception("Codec cache warmup failed")
