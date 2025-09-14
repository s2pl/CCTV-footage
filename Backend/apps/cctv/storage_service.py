"""
GCP Cloud Storage service for handling video recordings and media files.
This service provides a unified interface for both local and GCP storage.
"""

import os
import logging
from typing import Optional, BinaryIO, Union, Tuple
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile
import tempfile
import shutil

logger = logging.getLogger(__name__)

try:
    from google.cloud import storage
    from google.oauth2 import service_account
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False
    logger.warning("Google Cloud Storage not available. Install google-cloud-storage package.")


class GCPStorageService:
    """Service for managing files in Google Cloud Storage"""
    
    def __init__(self):
        self.bucket_name = settings.GCP_STORAGE_BUCKET_NAME
        self.project_id = settings.GCP_STORAGE_PROJECT_ID
        self.credentials_path = settings.GCP_STORAGE_CREDENTIALS_PATH
        self._client = None
        self._bucket = None
    
    @property
    def client(self):
        """Get or create GCP storage client"""
        if self._client is None and GCP_AVAILABLE:
            try:
                if self.credentials_path and os.path.exists(self.credentials_path):
                    # Use service account credentials from file
                    credentials = service_account.Credentials.from_service_account_file(
                        self.credentials_path
                    )
                    self._client = storage.Client(
                        project=self.project_id,
                        credentials=credentials
                    )
                else:
                    # Use default credentials (environment variable or metadata server)
                    self._client = storage.Client(project=self.project_id)
                
                logger.info(f"GCP Storage client initialized for project: {self.project_id}")
            except Exception as e:
                logger.error(f"Failed to initialize GCP Storage client: {str(e)}")
                self._client = None
        
        return self._client
    
    @property
    def bucket(self):
        """Get or create bucket reference"""
        if self._bucket is None and self.client:
            try:
                self._bucket = self.client.bucket(self.bucket_name)
                # Test bucket access
                self._bucket.reload()
                logger.info(f"GCP Storage bucket '{self.bucket_name}' is accessible")
            except Exception as e:
                logger.error(f"Failed to access GCP Storage bucket '{self.bucket_name}': {str(e)}")
                self._bucket = None
        
        return self._bucket
    
    def upload_file(self, file_path: str, destination_path: str, content_type: str = None, timeout: int = 300) -> bool:
        """
        Upload a file to GCP Storage
        
        Args:
            file_path: Local file path to upload
            destination_path: Destination path in the bucket
            content_type: MIME type of the file
            timeout: Upload timeout in seconds (default: 300)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.bucket:
            logger.error("GCP Storage bucket not available")
            return False
        
        # Normalize file path for Windows
        file_path = os.path.normpath(file_path)
        
        # Check if file exists and is not a .tmp file
        if not os.path.exists(file_path):
            logger.error(f"Local file not found: {file_path}")
            return False
            
        if file_path.endswith('.tmp'):
            logger.warning(f"Skipping .tmp file: {file_path}")
            return False
        
        try:
            blob = self.bucket.blob(destination_path)
            
            # Set content type if provided
            if content_type:
                blob.content_type = content_type
            
            # Upload the file with timeout
            blob.upload_from_filename(file_path, timeout=timeout)
            
            logger.info(f"Successfully uploaded {file_path} to gs://{self.bucket_name}/{destination_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload file to GCP Storage: {str(e)}")
            return False
    
    def upload_file_content(self, file_content: Union[bytes, BinaryIO], destination_path: str, content_type: str = None) -> bool:
        """
        Upload file content to GCP Storage
        
        Args:
            file_content: File content as bytes or file-like object
            destination_path: Destination path in the bucket
            content_type: MIME type of the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.bucket:
            logger.error("GCP Storage bucket not available")
            return False
        
        try:
            blob = self.bucket.blob(destination_path)
            
            # Set content type if provided
            if content_type:
                blob.content_type = content_type
            
            # Upload the content
            blob.upload_from_file(file_content, rewind=True)
            
            logger.info(f"Successfully uploaded content to gs://{self.bucket_name}/{destination_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload content to GCP Storage: {str(e)}")
            return False
    
    def download_file(self, source_path: str, destination_path: str) -> bool:
        """
        Download a file from GCP Storage
        
        Args:
            source_path: Source path in the bucket
            destination_path: Local destination path
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.bucket:
            logger.error("GCP Storage bucket not available")
            return False
        
        try:
            blob = self.bucket.blob(source_path)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            
            # Download the file
            blob.download_to_filename(destination_path)
            
            logger.info(f"Successfully downloaded gs://{self.bucket_name}/{source_path} to {destination_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download file from GCP Storage: {str(e)}")
            return False
    
    def get_file_url(self, file_path: str, signed: bool = True, expiration_minutes: int = 120) -> str:
        """
        Get public or signed URL for a file in GCP Storage
        
        Args:
            file_path: Path to the file in the bucket
            signed: Whether to generate a signed URL (default: True for security)
            expiration_minutes: Expiration time for signed URLs (in minutes, default: 120)
            
        Returns:
            str: URL to the file, or empty string if failed
        """
        if not self.bucket:
            logger.error("GCP Storage bucket not available")
            return ""
        
        try:
            blob = self.bucket.blob(file_path)
            
            # Check if file exists first
            if not blob.exists():
                logger.error(f"File does not exist in GCP Storage: {file_path}")
                return ""
            
            if signed:
                # Generate signed URL with proper permissions
                from datetime import timedelta
                url = blob.generate_signed_url(
                    expiration=timedelta(minutes=expiration_minutes),
                    method='GET',
                    version='v4'  # Use v4 signing for better compatibility
                )
                logger.debug(f"Generated signed URL for {file_path} (expires in {expiration_minutes}min)")
            else:
                # Get public URL (only works if bucket/blob is public)
                url = blob.public_url
                logger.debug(f"Generated public URL for {file_path}")
            
            return url
            
        except Exception as e:
            logger.error(f"Failed to get file URL from GCP Storage: {str(e)}")
            return ""
    
    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in GCP Storage
        
        Args:
            file_path: Path to the file in the bucket
            
        Returns:
            bool: True if file exists, False otherwise
        """
        if not self.bucket:
            return False
        
        try:
            blob = self.bucket.blob(file_path)
            return blob.exists()
        except Exception as e:
            logger.error(f"Failed to check file existence in GCP Storage: {str(e)}")
            return False
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from GCP Storage
        
        Args:
            file_path: Path to the file in the bucket
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.bucket:
            logger.error("GCP Storage bucket not available")
            return False
        
        try:
            blob = self.bucket.blob(file_path)
            blob.delete()
            
            logger.info(f"Successfully deleted gs://{self.bucket_name}/{file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file from GCP Storage: {str(e)}")
            return False
    
    def get_file_size(self, file_path: str) -> Optional[int]:
        """
        Get file size from GCP Storage
        
        Args:
            file_path: Path to the file in the bucket
            
        Returns:
            int: File size in bytes, or None if failed
        """
        if not self.bucket:
            return None
        
        try:
            blob = self.bucket.blob(file_path)
            blob.reload()
            return blob.size
        except Exception as e:
            logger.error(f"Failed to get file size from GCP Storage: {str(e)}")
            return None


class UnifiedStorageService:
    """
    Unified storage service that can work with both local and GCP storage
    based on configuration settings.
    """
    
    def __init__(self):
        self.use_gcp = getattr(settings, 'GCP_STORAGE_USE_GCS', False) and GCP_AVAILABLE
        self.gcp_service = GCPStorageService() if self.use_gcp else None
        
        logger.info(f"UnifiedStorageService initialized - Using {'GCP' if self.use_gcp else 'Local'} storage")
        logger.info(f"GCP_STORAGE_USE_GCS: {getattr(settings, 'GCP_STORAGE_USE_GCS', False)}")
        logger.info(f"GCP_AVAILABLE: {GCP_AVAILABLE}")
    
    def upload_recording(self, local_file_path: str, recording_id: str, camera_id: str, filename: str) -> Optional[str]:
        """
        Upload a recording file to storage (local or GCP)
        
        Args:
            local_file_path: Local file path to upload
            recording_id: Recording UUID
            camera_id: Camera UUID
            filename: Original filename
            
        Returns:
            tuple: (storage_path, storage_type) where storage_path is the file path and storage_type is 'gcp' or 'local'
        """
        # Create storage path maintaining the same structure as local storage
        storage_path = f"recordings/{camera_id}/{filename}"
        
        if self.use_gcp and self.gcp_service:
            # Upload to GCP Storage with proper timeout and content type
            file_size = 0
            try:
                file_size = os.path.getsize(local_file_path)
            except:
                pass
                
            # Set timeout based on file size (minimum 5 minutes, up to 15 minutes for large files)
            timeout = max(300, min(900, file_size // (1024 * 1024) * 30))  # 30 seconds per MB
            
            success = self.gcp_service.upload_file(
                local_file_path, 
                storage_path,
                content_type=self._get_content_type(filename),
                timeout=timeout
            )
            
            if success:
                logger.info(f"✅ Successfully uploaded recording to GCP: {storage_path} ({self._format_size(file_size)})")
                
                # Verify upload by checking if file exists in GCP
                if self.gcp_service.file_exists(storage_path):
                    logger.info(f"✅ Upload verified: {storage_path}")
                    
                    # Clean up local file after successful upload if enabled
                    if getattr(settings, 'GCP_STORAGE_CLEANUP_LOCAL', True):
                        try:
                            os.remove(local_file_path)
                            logger.info(f"🗑️ Cleaned up local file: {local_file_path}")
                        except Exception as e:
                            logger.warning(f"Failed to clean up local file {local_file_path}: {str(e)}")
                    
                    return storage_path, 'gcp'
                else:
                    logger.error(f"Upload verification failed for {storage_path}")
                    return os.path.relpath(local_file_path, settings.MEDIA_ROOT), 'local'
            else:
                # Fallback to local storage if GCP upload fails
                logger.warning(f"Failed to upload recording to GCP Storage: {storage_path}")
                logger.info("Falling back to local storage...")
                return os.path.relpath(local_file_path, settings.MEDIA_ROOT), 'local'
        else:
            # Use local storage (existing behavior)
            return os.path.relpath(local_file_path, settings.MEDIA_ROOT), 'local'
    
    def get_file_url(self, file_path: str, signed: bool = True, expiration_minutes: int = 120) -> str:
        """
        Get URL for accessing a file
        
        Args:
            file_path: Storage path to the file
            signed: Whether to generate a signed URL (for GCP, default: True)
            expiration_minutes: Expiration time for signed URLs (default: 120 minutes)
            
        Returns:
            str: URL to access the file, or empty string if failed
        """
        if not file_path:
            return ""
            
        try:
            if self.use_gcp and self.gcp_service:
                url = self.gcp_service.get_file_url(file_path, signed=signed, expiration_minutes=expiration_minutes)
                return url if url is not None else ""
            else:
                # Local storage URL
                return f"{settings.MEDIA_URL}{file_path}"
        except Exception as e:
            logger.error(f"Error getting file URL for {file_path}: {str(e)}")
            return ""
    
    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in storage
        
        Args:
            file_path: Storage path to the file
            
        Returns:
            bool: True if file exists, False otherwise
        """
        if not file_path:
            return False
            
        if self.use_gcp and self.gcp_service:
            try:
                exists = self.gcp_service.file_exists(file_path)
                if exists:
                    logger.debug(f"File exists in GCP: {file_path}")
                else:
                    logger.debug(f"File not found in GCP: {file_path}")
                return exists
            except Exception as e:
                logger.error(f"Error checking file existence in GCP: {str(e)}")
                return False
        else:
            # Check local file
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)
            exists = os.path.exists(full_path)
            if exists:
                logger.debug(f"File exists locally: {full_path}")
            else:
                logger.debug(f"File not found locally: {full_path}")
            return exists
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage
        
        Args:
            file_path: Storage path to the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.use_gcp and self.gcp_service:
            return self.gcp_service.delete_file(file_path)
        else:
            # Delete local file
            if file_path:
                full_path = os.path.join(settings.MEDIA_ROOT, file_path)
                try:
                    os.remove(full_path)
                    logger.info(f"Deleted local file: {full_path}")
                    return True
                except Exception as e:
                    logger.error(f"Failed to delete local file {full_path}: {str(e)}")
                    return False
            return False
    
    def get_file_size(self, file_path: str) -> Optional[int]:
        """
        Get file size
        
        Args:
            file_path: Storage path to the file
            
        Returns:
            int: File size in bytes, or None if failed
        """
        if self.use_gcp and self.gcp_service:
            return self.gcp_service.get_file_size(file_path)
        else:
            # Get local file size
            if file_path:
                full_path = os.path.join(settings.MEDIA_ROOT, file_path)
                try:
                    return os.path.getsize(full_path)
                except Exception as e:
                    logger.error(f"Failed to get local file size {full_path}: {str(e)}")
                    return None
            return None
    
    def download_file_to_temp(self, file_path: str) -> Optional[str]:
        """
        Download a file to a temporary location for processing
        
        Args:
            file_path: Storage path to the file
            
        Returns:
            str: Temporary file path, or None if failed
        """
        if self.use_gcp and self.gcp_service:
            # Create temporary file
            temp_fd, temp_path = tempfile.mkstemp()
            os.close(temp_fd)
            
            # Download from GCP to temp file
            success = self.gcp_service.download_file(file_path, temp_path)
            if success:
                return temp_path
            else:
                # Clean up temp file on failure
                try:
                    os.remove(temp_path)
                except:
                    pass
                return None
        else:
            # Return local file path
            if file_path:
                full_path = os.path.join(settings.MEDIA_ROOT, file_path)
                if os.path.exists(full_path):
                    return full_path
            return None
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type based on file extension"""
        ext = os.path.splitext(filename)[1].lower()
        content_types = {
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska',
            '.webm': 'video/webm',
            '.flv': 'video/x-flv',
        }
        return content_types.get(ext, 'video/mp4')
    
    def _format_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"


# Global storage service instance
storage_service = UnifiedStorageService()
