"""
Management command to clear codec cache
"""

from django.core.management.base import BaseCommand
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clear codec cache to force retesting with new codec priorities'

    def handle(self, *args, **options):
        self.stdout.write('Clearing codec cache...')
        
        try:
            from apps.cctv.opencv_config import clear_codec_cache
            clear_codec_cache()
            self.stdout.write(self.style.SUCCESS('✅ Codec cache cleared successfully'))
            self.stdout.write('Next recording will test codecs with new priorities')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error clearing codec cache: {str(e)}'))
            logger.exception("Codec cache clear failed")
