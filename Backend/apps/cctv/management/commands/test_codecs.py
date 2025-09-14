"""
Management command to test video codec compatibility
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test video codec compatibility for recording'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing video codec compatibility...'))
        
        try:
            from apps.cctv.opencv_config import test_codec_compatibility, check_opencv_compatibility
            
            # Check OpenCV compatibility first
            self.stdout.write("Checking OpenCV compatibility...")
            if not check_opencv_compatibility():
                self.stdout.write(self.style.ERROR('OpenCV compatibility check failed'))
                return
            
            # Test codecs with standard resolution
            width, height, fps = 640, 480, 25
            self.stdout.write(f"Testing codecs with {width}x{height} @ {fps}fps...")
            
            working_codecs = test_codec_compatibility(width, height, fps)
            
            if working_codecs:
                self.stdout.write(self.style.SUCCESS(f'Found {len(working_codecs)} working codecs:'))
                for codec, extension, description in working_codecs:
                    self.stdout.write(f'  ✅ {codec} ({extension}): {description}')
            else:
                self.stdout.write(self.style.ERROR('No working codecs found!'))
                self.stdout.write('This may indicate an issue with OpenCV installation or codec support.')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during codec testing: {str(e)}'))
            logger.exception("Codec testing failed")
