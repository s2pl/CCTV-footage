from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class CctvConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.cctv'
    verbose_name = 'CCTV System'

    def ready(self):
        """Initialize the CCTV app"""
        try:
            # Import signals
            from . import signals
            logger.info("✅ CCTV app signals loaded successfully")
            
            # CCTV uses Django Ninja REST API, not traditional Django URLs
            # API endpoints are available at /v0/api/cctv/
            logger.info("🔗 CCTV REST API configured at /v0/api/cctv/")
            
            # Warm up codec cache in background (don't block startup)
            import threading
            def warmup_codecs():
                try:
                    from .opencv_config import get_cached_working_codecs
                    # Cache common resolutions used in CCTV systems
                    common_resolutions = [
                        (640, 480, 25),    # VGA
                        (1280, 720, 25),   # 720p HD
                        (1920, 1080, 25),  # 1080p Full HD
                    ]
                    
                    for width, height, fps in common_resolutions:
                        get_cached_working_codecs(width, height, fps)
                    
                    logger.info("🎬 Codec cache warmed up for common resolutions")
                except Exception as e:
                    logger.warning(f"Codec warmup failed: {str(e)}")
            
            # Start warmup in background thread with delay to avoid startup conflicts
            def delayed_warmup():
                import time
                time.sleep(2)  # Wait 2 seconds after startup
                warmup_codecs()
            
            warmup_thread = threading.Thread(target=delayed_warmup, daemon=True)
            warmup_thread.start()
            
            logger.info("🎥 CCTV app initialization complete - No authentication required")
            
        except Exception as e:
            logger.error(f"❌ Error initializing CCTV app: {str(e)}")