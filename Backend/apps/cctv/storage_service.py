"""
Cloud Storage service for handling video recordings and media files.
This service provides a unified interface for local, AWS S3, and GCP storage.
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

# Check AWS availability
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    logger.warning("AWS SDK (boto3) not available. Install boto3 package for AWS S3 support.")

# Check GCP availability
try:
    from google.cloud import storage
    from google.oauth2 import service_account
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False
    logger.warning("Google Cloud Storage not available. Install google-cloud-storage package.")


class AWSS3StorageService:
    """Service for managing files in AWS S3"""
    
    def __init__(self):
        self.bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '')
        self.region_name = getattr(settings, 'AWS_REGION_NAME', 'ap-south-1')
        self.access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', '')
        self.secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', '')
        self._client = None
        self._s3_resource = None
    
    @property
    def client(self):
        """Get or create AWS S3 client"""
        if self._client is None and AWS_AVAILABLE:
            try:
                self._client = boto3.client(
                    's3',
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name=self.region_name
                )
                logger.info(f"AWS S3 client initialized for bucket: {self.bucket_name}")
            except Exception as e:
                logger.error(f"Failed to initialize AWS S3 client: {str(e)}")
                self._client = None
        
        return self._client
    
    @property
    def s3_resource(self):
        """Get or create AWS S3 resource"""
        if self._s3_resource is None and AWS_AVAILABLE:
            try:
                self._s3_resource = boto3.resource(
                    's3',
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name=self.region_name
                )
            except Exception as e:
                logger.error(f"Failed to initialize AWS S3 resource: {str(e)}")
                self._s3_resource = None
        
        return self._s3_resource
    
    def upload_file(self, file_path: str, destination_path: str, content_type: str = None, timeout: int = 300) -> bool:
        """
        Upload a file to AWS S3
        
        Args:
            file_path: Local file path to upload
            destination_path: Destination path in the bucket
            content_type: MIME type of the file
            timeout: Upload timeout in seconds (default: 300)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.client:
            logger.error("AWS S3 client not available")
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
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            # Upload the file
            self.client.upload_file(
                file_path,
                self.bucket_name,
                destination_path,
                ExtraArgs=extra_args
            )
            
            logger.info(f"Successfully uploaded {file_path} to s3://{self.bucket_name}/{destination_path}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to upload file to AWS S3: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading to AWS S3: {str(e)}")
            return False
    
    def upload_file_content(self, file_content: Union[bytes, BinaryIO], destination_path: str, content_type: str = None) -> bool:
        """
        Upload file content to AWS S3
        
        Args:
            file_content: File content as bytes or file-like object
            destination_path: Destination path in the bucket
            content_type: MIME type of the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.client:
            logger.error("AWS S3 client not available")
            return False
        
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            # Upload the content
            if isinstance(file_content, bytes):
                self.client.put_object(
                    Bucket=self.bucket_name,
                    Key=destination_path,
                    Body=file_content,
                    **extra_args
                )
            else:
                self.client.upload_fileobj(
                    file_content,
                    self.bucket_name,
                    destination_path,
                    ExtraArgs=extra_args
                )
            
            logger.info(f"Successfully uploaded content to s3://{self.bucket_name}/{destination_path}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to upload content to AWS S3: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading content to AWS S3: {str(e)}")
            return False
    
    def download_file(self, source_path: str, destination_path: str) -> bool:
        """
        Download a file from AWS S3
        
        Args:
            source_path: Source path in the bucket
            destination_path: Local destination path
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.client:
            logger.error("AWS S3 client not available")
            return False
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            
            # Download the file
            self.client.download_file(
                self.bucket_name,
                source_path,
                destination_path
            )
            
            logger.info(f"Successfully downloaded s3://{self.bucket_name}/{source_path} to {destination_path}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to download file from AWS S3: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading from AWS S3: {str(e)}")
            return False
    
    def get_file_url(self, file_path: str, signed: bool = True, expiration_minutes: int = 120) -> str:
        """
        Get public or signed URL for a file in AWS S3
        
        Args:
            file_path: Path to the file in the bucket
            signed: Whether to generate a signed URL (default: True for security)
            expiration_minutes: Expiration time for signed URLs (in minutes, default: 120)
            
        Returns:
            str: URL to the file, or empty string if failed
        """
        if not self.client:
            logger.error("AWS S3 client not available")
            return ""
        
        try:
            # Skip .tmp files - they're temporary and shouldn't be accessed
            if file_path.endswith('.tmp'):
                logger.debug(f"Skipping .tmp file URL generation: {file_path}")
                return ""
            
            # Check if file exists first
            if not self.file_exists(file_path):
                logger.warning(f"File does not exist in AWS S3: {file_path}")
                return ""
            
            if signed:
                # Generate presigned URL
                expiration_seconds = expiration_minutes * 60
                url = self.client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self.bucket_name,
                        'Key': file_path
                    },
                    ExpiresIn=expiration_seconds
                )
                logger.debug(f"Generated presigned URL for {file_path} (expires in {expiration_minutes}min)")
            else:
                # Get public URL (only works if bucket/object is public)
                url = f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{file_path}"
                logger.debug(f"Generated public URL for {file_path}")
            
            return url
            
        except ClientError as e:
            logger.error(f"Failed to get file URL from AWS S3: {str(e)}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error getting file URL from AWS S3: {str(e)}")
            return ""
    
    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in AWS S3
        
        Args:
            file_path: Path to the file in the bucket
            
        Returns:
            bool: True if file exists, False otherwise
        """
        if not self.client:
            return False
        
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=file_path)
            return True
        except ClientError as e:
            # If a 404 error is returned, the object doesn't exist
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"Failed to check file existence in AWS S3: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking file existence in AWS S3: {str(e)}")
            return False
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from AWS S3
        
        Args:
            file_path: Path to the file in the bucket
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.client:
            logger.error("AWS S3 client not available")
            return False
        
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            
            logger.info(f"Successfully deleted s3://{self.bucket_name}/{file_path}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete file from AWS S3: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting from AWS S3: {str(e)}")
            return False
    
    def get_file_size(self, file_path: str) -> Optional[int]:
        """
        Get file size from AWS S3
        
        Args:
            file_path: Path to the file in the bucket
            
        Returns:
            int: File size in bytes, or None if failed
        """
        if not self.client:
            return None
        
        try:
            response = self.client.head_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            return response['ContentLength']
        except ClientError as e:
            logger.error(f"Failed to get file size from AWS S3: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting file size from AWS S3: {str(e)}")
            return None


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
    Unified storage service that can work with local, AWS S3, or GCP storage
    based on configuration settings.
    """
    
    def __init__(self):
        # Determine which cloud storage backend to use
        cloud_backend = getattr(settings, 'CLOUD_STORAGE_BACKEND', 'LOCAL').upper()
        
        # Initialize services based on backend
        self.use_aws = cloud_backend == 'AWS' and AWS_AVAILABLE
        self.use_gcp = cloud_backend == 'GCP' and GCP_AVAILABLE
        self.use_both = cloud_backend == 'BOTH' and AWS_AVAILABLE and GCP_AVAILABLE
        
        # Initialize cloud service instances
        self.aws_service = AWSS3StorageService() if (self.use_aws or self.use_both) else None
        self.gcp_service = GCPStorageService() if (self.use_gcp or self.use_both) else None
        
        # Log initialization status
        storage_type = 'Local'
        if self.use_both:
            storage_type = 'AWS + GCP (Both)'
        elif self.use_aws:
            storage_type = 'AWS S3'
        elif self.use_gcp:
            storage_type = 'GCP Cloud Storage'
        
        logger.info(f"UnifiedStorageService initialized - Using {storage_type} storage")
        logger.info(f"CLOUD_STORAGE_BACKEND: {cloud_backend}")
        logger.info(f"AWS_AVAILABLE: {AWS_AVAILABLE}")
        logger.info(f"GCP_AVAILABLE: {GCP_AVAILABLE}")
    
    def upload_recording(self, local_file_path: str, recording_id: str, camera_id: str, filename: str) -> Optional[str]:
        """
        Upload a recording file to storage (local, AWS S3, or GCP)
        
        Args:
            local_file_path: Local file path to upload
            recording_id: Recording UUID
            camera_id: Camera UUID
            filename: Original filename
            
        Returns:
            tuple: (storage_path, storage_type) where storage_path is the file path and storage_type is 'aws', 'gcp', or 'local'
        """
        # Create storage path maintaining the same structure as local storage
        storage_path = f"recordings/{camera_id}/{filename}"
        
        # Get file size for timeout calculation
        file_size = 0
        try:
            file_size = os.path.getsize(local_file_path)
        except:
            pass
        
        # Set timeout based on file size (minimum 5 minutes, up to 15 minutes for large files)
        timeout = max(300, min(900, file_size // (1024 * 1024) * 30))  # 30 seconds per MB
        
        # Try AWS S3 first if enabled
        if self.use_aws and self.aws_service:
            success = self.aws_service.upload_file(
                local_file_path, 
                storage_path,
                content_type=self._get_content_type(filename),
                timeout=timeout
            )
            
            if success:
                logger.info(f"✅ Successfully uploaded recording to AWS S3: {storage_path} ({self._format_size(file_size)})")
                
                # Verify upload by checking if file exists in AWS
                if self.aws_service.file_exists(storage_path):
                    logger.info(f"✅ Upload verified: {storage_path}")
                    
                    # Clean up local file after successful upload if enabled
                    if getattr(settings, 'AWS_STORAGE_CLEANUP_LOCAL', True):
                        try:
                            os.remove(local_file_path)
                            logger.info(f"🗑️ Cleaned up local file: {local_file_path}")
                        except Exception as e:
                            logger.warning(f"Failed to clean up local file {local_file_path}: {str(e)}")
                    
                    # Also upload to GCP if using both
                    if self.use_both and self.gcp_service:
                        logger.info("📤 Also uploading to GCP (backup)...")
                        gcp_success = self.gcp_service.upload_file(
                            local_file_path if os.path.exists(local_file_path) else None,
                            storage_path,
                            content_type=self._get_content_type(filename),
                            timeout=timeout
                        )
                        if gcp_success:
                            logger.info(f"✅ Backup copy uploaded to GCP: {storage_path}")
                    
                    return storage_path, 'aws'
                else:
                    logger.error(f"Upload verification failed for {storage_path}")
            else:
                logger.warning(f"Failed to upload recording to AWS S3: {storage_path}")
        
        # Try GCP if AWS failed or if GCP is the primary backend
        if self.use_gcp and self.gcp_service:
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
            else:
                logger.warning(f"Failed to upload recording to GCP Storage: {storage_path}")
        
        # Fallback to local storage
        logger.info("Falling back to local storage...")
        return os.path.relpath(local_file_path, settings.MEDIA_ROOT), 'local'
    
    def get_file_url(self, file_path: str, signed: bool = True, expiration_minutes: int = 120) -> str:
        """
        Get URL for accessing a file
        
        Args:
            file_path: Storage path to the file
            signed: Whether to generate a signed URL (for cloud storage, default: True)
            expiration_minutes: Expiration time for signed URLs (default: 120 minutes)
            
        Returns:
            str: URL to access the file, or empty string if failed
        """
        if not file_path:
            return ""
            
        try:
            # Try AWS S3 first if enabled
            if self.use_aws and self.aws_service:
                url = self.aws_service.get_file_url(file_path, signed=signed, expiration_minutes=expiration_minutes)
                if url:
                    return url
                # If AWS fails and we're using both, try GCP
                if self.use_both and self.gcp_service:
                    logger.info(f"AWS URL failed, trying GCP for {file_path}")
                    url = self.gcp_service.get_file_url(file_path, signed=signed, expiration_minutes=expiration_minutes)
                    return url if url is not None else ""
                return ""
            
            # Try GCP if it's the primary backend or if AWS is not available
            if self.use_gcp and self.gcp_service:
                url = self.gcp_service.get_file_url(file_path, signed=signed, expiration_minutes=expiration_minutes)
                return url if url is not None else ""
            
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
            
        # Try AWS S3 first if enabled
        if self.use_aws and self.aws_service:
            try:
                exists = self.aws_service.file_exists(file_path)
                if exists:
                    logger.debug(f"File exists in AWS S3: {file_path}")
                    return True
                # If using both, also check GCP
                if self.use_both and self.gcp_service:
                    exists = self.gcp_service.file_exists(file_path)
                    if exists:
                        logger.debug(f"File exists in GCP: {file_path}")
                        return True
                logger.debug(f"File not found in AWS S3: {file_path}")
                return False
            except Exception as e:
                logger.error(f"Error checking file existence in AWS S3: {str(e)}")
                # Try GCP if AWS check fails and we're using both
                if self.use_both and self.gcp_service:
                    try:
                        return self.gcp_service.file_exists(file_path)
                    except:
                        pass
                return False
        
        # Try GCP if it's the primary backend
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
        success = False
        
        # Delete from AWS S3 if enabled
        if self.use_aws and self.aws_service:
            aws_success = self.aws_service.delete_file(file_path)
            success = success or aws_success
            
            # Also delete from GCP if using both
            if self.use_both and self.gcp_service:
                gcp_success = self.gcp_service.delete_file(file_path)
                success = success or gcp_success
            
            return success
        
        # Delete from GCP if it's the primary backend
        if self.use_gcp and self.gcp_service:
            return self.gcp_service.delete_file(file_path)
        
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
        # Try AWS S3 first if enabled
        if self.use_aws and self.aws_service:
            size = self.aws_service.get_file_size(file_path)
            if size is not None:
                return size
            # Try GCP if AWS fails and using both
            if self.use_both and self.gcp_service:
                return self.gcp_service.get_file_size(file_path)
            return None
        
        # Try GCP if it's the primary backend
        if self.use_gcp and self.gcp_service:
            return self.gcp_service.get_file_size(file_path)
        
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
        # Try AWS S3 first if enabled
        if self.use_aws and self.aws_service:
            # Create temporary file
            temp_fd, temp_path = tempfile.mkstemp()
            os.close(temp_fd)
            
            # Download from AWS to temp file
            success = self.aws_service.download_file(file_path, temp_path)
            if success:
                return temp_path
            
            # Try GCP if AWS fails and using both
            if self.use_both and self.gcp_service:
                success = self.gcp_service.download_file(file_path, temp_path)
                if success:
                    return temp_path
            
            # Clean up temp file on failure
            try:
                os.remove(temp_path)
            except:
                pass
            return None
        
        # Try GCP if it's the primary backend
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
