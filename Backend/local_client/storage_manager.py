"""
GCP Storage manager for uploading recordings
"""
import os
import logging
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

try:
    from google.cloud import storage
    from google.oauth2 import service_account
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False
    logging.warning("Google Cloud Storage not available. Install google-cloud-storage package.")

try:
    from .config import config
except ImportError:
    from config import config

logger = logging.getLogger(__name__)


class StorageManager:
    """Manages GCP storage uploads"""
    
    def __init__(self):
        self.bucket_name = config.GCP_BUCKET_NAME
        self.credentials_path = config.GCP_CREDENTIALS_PATH
        self._client: Optional[storage.Client] = None
        self._bucket: Optional[storage.Bucket] = None
        self.bucket_connected = False
        
        if GCP_AVAILABLE and self.bucket_name and self.credentials_path:
            self._initialize_client()
        
        if not self.bucket_connected:
            logger.warning("[WARNING] GCP Bucket is not connected - recordings will be stored locally only")
            logger.info("To connect GCP bucket, set GCP_BUCKET_NAME and GCP_CREDENTIALS_PATH in .env file")
    
    def _initialize_client(self):
        """Initialize GCP storage client"""
        try:
            if not os.path.exists(self.credentials_path):
                logger.warning(f"GCP credentials file not found: {self.credentials_path}")
                self.bucket_connected = False
                return
            
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path
            )
            self._client = storage.Client(
                project=config.GCP_PROJECT_ID,
                credentials=credentials
            )
            self._bucket = self._client.bucket(self.bucket_name)
            
            # Test bucket connection (with timeout to avoid hanging)
            try:
                # Quick check - try to get bucket metadata
                self._client.get_bucket(self.bucket_name, timeout=5)
                self.bucket_connected = True
                logger.info(f"[OK] GCP Storage bucket connected: {self.bucket_name}")
            except Exception as bucket_error:
                logger.warning(f"GCP bucket connection failed: {str(bucket_error)}")
                logger.warning(f"   Bucket name: {self.bucket_name}")
                self.bucket_connected = False
                
        except Exception as e:
            logger.error(f"Failed to initialize GCP client: {str(e)}")
            self._client = None
            self._bucket = None
            self.bucket_connected = False
    
    def is_available(self) -> bool:
        """Check if GCP storage is available"""
        return self.bucket_connected and GCP_AVAILABLE and self._client is not None and self._bucket is not None
    
    async def upload_recording(
        self,
        local_path: Path,
        recording_id: str,
        camera_id: str
    ) -> Tuple[Optional[str], bool]:
        """
        Upload recording to GCP bucket
        
        Returns:
            Tuple of (gcp_path, success)
        """
        if not self.is_available():
            logger.info(f"[WARNING] Bucket not connected - recording stored locally: {local_path}")
            logger.info("   File will be kept locally until bucket is configured")
            return None, False  # Indicates not uploaded, but file is safely stored locally
        
        try:
            # Generate GCP path: recordings/{camera_id}/{YYYYMMDD}/recording_{timestamp}.avi
            date_str = datetime.now().strftime('%Y%m%d')
            filename = local_path.name
            gcp_path = f"recordings/{camera_id}/{date_str}/{filename}"
            
            logger.info(f"Uploading {local_path} to gs://{self.bucket_name}/{gcp_path}")
            
            # Upload file
            blob = self._bucket.blob(gcp_path)
            blob.content_type = 'video/mp4' if filename.endswith('.mp4') else 'video/x-msvideo'
            
            # Upload with timeout
            file_size = local_path.stat().st_size
            timeout = max(300, min(900, file_size // (1024 * 1024) * 30))  # 30s per MB, min 5min, max 15min
            
            blob.upload_from_filename(str(local_path), timeout=timeout)
            
            # Verify upload
            if blob.exists():
                logger.info(f"Successfully uploaded recording to GCP: {gcp_path}")
                
                # Clean up local file if configured (only after successful upload)
                if config.CLEANUP_AFTER_UPLOAD and local_path.exists():
                    try:
                        local_path.unlink()
                        logger.info(f"Cleaned up local file: {local_path}")
                    except Exception as e:
                        logger.warning(f"Failed to cleanup local file: {str(e)}")
                
                return gcp_path, True
            else:
                logger.error(f"Upload verification failed for {gcp_path}")
                # Don't delete local file if upload verification failed
                return None, False
                
        except Exception as e:
            logger.error(f"Failed to upload recording to GCP: {str(e)}")
            return None, False
    
    async def move_to_pending(self, local_path: Path):
        """Move file to pending uploads directory for retry"""
        try:
            pending_path = config.PENDING_UPLOADS_DIR / local_path.name
            local_path.rename(pending_path)
            logger.info(f"Moved {local_path} to pending uploads")
        except Exception as e:
            logger.error(f"Failed to move file to pending: {str(e)}")
    
    def get_pending_uploads(self) -> list[Path]:
        """Get list of pending upload files"""
        if not config.PENDING_UPLOADS_DIR.exists():
            return []
        
        return [f for f in config.PENDING_UPLOADS_DIR.iterdir() if f.is_file()]
    
    def get_bucket_status(self) -> dict:
        """Get bucket connection status"""
        return {
            'connected': self.bucket_connected,
            'bucket_name': self.bucket_name if self.bucket_connected else None,
            'gcp_available': GCP_AVAILABLE,
            'has_credentials': bool(self.credentials_path and os.path.exists(self.credentials_path)) if self.credentials_path else False
        }

