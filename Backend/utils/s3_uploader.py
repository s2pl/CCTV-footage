"""
AWS S3 Uploader Utility
Handles uploading files to AWS S3 bucket
"""
import boto3
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from django.conf import settings

logger = logging.getLogger(__name__)


class S3Uploader:
    """Utility class for uploading files to AWS S3"""
    
    def __init__(self):
        """Initialize S3 client"""
        try:
            # Check if AWS credentials are configured
            if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
                raise ValueError("AWS credentials not configured in settings")
            
            if not settings.AWS_STORAGE_BUCKET_NAME:
                raise ValueError("AWS bucket name not configured in settings")
            
            # Initialize S3 client
            session_config = {
                'aws_access_key_id': settings.AWS_ACCESS_KEY_ID,
                'aws_secret_access_key': settings.AWS_SECRET_ACCESS_KEY,
                'region_name': settings.AWS_REGION_NAME,
            }
            
            # Add session token if provided (for temporary credentials)
            if hasattr(settings, 'AWS_SESSION_TOKEN') and settings.AWS_SESSION_TOKEN:
                session_config['aws_session_token'] = settings.AWS_SESSION_TOKEN
            
            # Create S3 client with signature version
            self.s3_client = boto3.client(
                's3',
                **session_config,
                config=boto3.session.Config(
                    signature_version=settings.AWS_S3_SIGNATURE_VERSION
                )
            )
            
            self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
            self.region = settings.AWS_REGION_NAME
            
            logger.info(f"S3 client initialized for bucket: {self.bucket_name} in region: {self.region}")
            
        except (NoCredentialsError, PartialCredentialsError) as e:
            logger.error(f"AWS credentials error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error initializing S3 client: {str(e)}")
            raise
    
    def upload_file(
        self, 
        file_path: str, 
        s3_key: str, 
        metadata: Optional[Dict[str, str]] = None,
        extra_args: Optional[Dict] = None,
        content_type: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Upload a file to S3 bucket
        
        Args:
            file_path: Local path to file to upload
            s3_key: S3 object key (path in bucket)
            metadata: Optional metadata to attach to object
            extra_args: Optional extra arguments for upload
            content_type: Optional content type override
            
        Returns:
            Tuple of (success: bool, url: Optional[str])
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return False, None
            
            # Get file size
            file_size = file_path.stat().st_size
            logger.info(f"Uploading file: {file_path.name} ({file_size / (1024*1024):.2f} MB)")
            
            # Prepare upload arguments
            upload_args = extra_args or {}
            
            # Add metadata if provided
            if metadata:
                upload_args['Metadata'] = metadata
            
            # Set content type based on file extension or override
            if content_type:
                upload_args['ContentType'] = content_type
            elif file_path.suffix:
                content_types = {
                    '.mp4': 'video/mp4',
                    '.avi': 'video/x-msvideo',
                    '.mkv': 'video/x-matroska',
                    '.mov': 'video/quicktime',
                    '.webm': 'video/webm',
                    '.flv': 'video/x-flv',
                    '.wmv': 'video/x-ms-wmv',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                }
                if file_path.suffix.lower() in content_types:
                    upload_args['ContentType'] = content_types[file_path.suffix.lower()]
            
            # Set default ACL if not provided
            if 'ACL' not in upload_args and hasattr(settings, 'AWS_DEFAULT_ACL'):
                if settings.AWS_DEFAULT_ACL and settings.AWS_DEFAULT_ACL != 'private':
                    upload_args['ACL'] = settings.AWS_DEFAULT_ACL
            
            # Upload file
            logger.debug(f"Starting upload to s3://{self.bucket_name}/{s3_key}")
            self.s3_client.upload_file(
                str(file_path),
                self.bucket_name,
                s3_key,
                ExtraArgs=upload_args
            )
            
            # Generate file URL
            file_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            
            logger.info(f"✅ Successfully uploaded {file_path.name} to s3://{self.bucket_name}/{s3_key}")
            return True, file_url
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"AWS ClientError uploading {file_path}: {error_code} - {str(e)}")
            return False, None
        except Exception as e:
            logger.error(f"Error uploading {file_path} to S3: {str(e)}")
            return False, None
    
    def upload_fileobj(
        self,
        file_obj,
        s3_key: str,
        metadata: Optional[Dict[str, str]] = None,
        extra_args: Optional[Dict] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Upload a file-like object to S3 bucket
        
        Args:
            file_obj: File-like object to upload
            s3_key: S3 object key (path in bucket)
            metadata: Optional metadata to attach to object
            extra_args: Optional extra arguments for upload
            
        Returns:
            Tuple of (success: bool, url: Optional[str])
        """
        try:
            # Prepare upload arguments
            upload_args = extra_args or {}
            
            # Add metadata if provided
            if metadata:
                upload_args['Metadata'] = metadata
            
            # Upload file object
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                s3_key,
                ExtraArgs=upload_args
            )
            
            # Generate file URL
            file_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            
            logger.info(f"✅ Successfully uploaded file object to s3://{self.bucket_name}/{s3_key}")
            return True, file_url
            
        except Exception as e:
            logger.error(f"Error uploading file object to S3: {str(e)}")
            return False, None
    
    def generate_presigned_url(
        self, 
        s3_key: str, 
        expiration: int = 3600,
        http_method: str = 'get_object'
    ) -> Optional[str]:
        """
        Generate a presigned URL for temporary access to private object
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)
            http_method: HTTP method for the URL ('get_object' or 'put_object')
            
        Returns:
            Presigned URL or None if error
        """
        try:
            url = self.s3_client.generate_presigned_url(
                http_method,
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            logger.debug(f"Generated presigned URL for {s3_key} (expires in {expiration}s)")
            return url
        except Exception as e:
            logger.error(f"Error generating presigned URL for {s3_key}: {str(e)}")
            return None
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3 bucket
        
        Args:
            s3_key: S3 object key to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"✅ Successfully deleted s3://{self.bucket_name}/{s3_key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting {s3_key} from S3: {str(e)}")
            return False
    
    def delete_files(self, s3_keys: List[str]) -> Tuple[int, int]:
        """
        Delete multiple files from S3 bucket
        
        Args:
            s3_keys: List of S3 object keys to delete
            
        Returns:
            Tuple of (success_count, error_count)
        """
        if not s3_keys:
            return 0, 0
        
        success_count = 0
        error_count = 0
        
        try:
            # S3 allows batch delete of up to 1000 objects at a time
            batch_size = 1000
            for i in range(0, len(s3_keys), batch_size):
                batch = s3_keys[i:i + batch_size]
                
                objects = [{'Key': key} for key in batch]
                response = self.s3_client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={'Objects': objects}
                )
                
                # Count successes and errors
                if 'Deleted' in response:
                    success_count += len(response['Deleted'])
                if 'Errors' in response:
                    error_count += len(response['Errors'])
                    for error in response['Errors']:
                        logger.error(f"Error deleting {error['Key']}: {error['Message']}")
            
            logger.info(f"Batch delete completed: {success_count} succeeded, {error_count} failed")
            return success_count, error_count
            
        except Exception as e:
            logger.error(f"Error during batch delete: {str(e)}")
            return success_count, len(s3_keys) - success_count
    
    def list_files(self, prefix: str = '', max_keys: int = 1000) -> List[Dict]:
        """
        List files in bucket with given prefix
        
        Args:
            prefix: S3 key prefix to filter results
            max_keys: Maximum number of keys to return
            
        Returns:
            List of dictionaries containing file information
        """
        try:
            files = []
            continuation_token = None
            
            while True:
                params = {
                    'Bucket': self.bucket_name,
                    'Prefix': prefix,
                    'MaxKeys': min(max_keys - len(files), 1000)
                }
                
                if continuation_token:
                    params['ContinuationToken'] = continuation_token
                
                response = self.s3_client.list_objects_v2(**params)
                
                if 'Contents' in response:
                    for obj in response['Contents']:
                        files.append({
                            'key': obj['Key'],
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'],
                            'etag': obj['ETag']
                        })
                
                # Check if there are more results
                if not response.get('IsTruncated', False) or len(files) >= max_keys:
                    break
                
                continuation_token = response.get('NextContinuationToken')
            
            logger.info(f"Listed {len(files)} files with prefix '{prefix}'")
            return files
            
        except Exception as e:
            logger.error(f"Error listing files in S3: {str(e)}")
            return []
    
    def file_exists(self, s3_key: str) -> bool:
        """
        Check if a file exists in S3 bucket
        
        Args:
            s3_key: S3 object key to check
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"Error checking if file exists: {str(e)}")
            return False
    
    def get_file_size(self, s3_key: str) -> Optional[int]:
        """
        Get the size of a file in S3 bucket
        
        Args:
            s3_key: S3 object key
            
        Returns:
            File size in bytes, or None if error
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return response['ContentLength']
        except Exception as e:
            logger.error(f"Error getting file size for {s3_key}: {str(e)}")
            return None
    
    def copy_file(self, source_key: str, destination_key: str) -> bool:
        """
        Copy a file within the same S3 bucket
        
        Args:
            source_key: Source S3 object key
            destination_key: Destination S3 object key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            copy_source = {
                'Bucket': self.bucket_name,
                'Key': source_key
            }
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=destination_key
            )
            logger.info(f"✅ Successfully copied {source_key} to {destination_key}")
            return True
        except Exception as e:
            logger.error(f"Error copying file in S3: {str(e)}")
            return False


# Convenience functions
def upload_cctv_recording(
    local_file_path: str, 
    camera_id: str, 
    timestamp: str,
    recording_id: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Upload CCTV recording to S3 with organized structure
    
    Args:
        local_file_path: Path to local video file
        camera_id: Camera identifier
        timestamp: Recording timestamp (ISO format)
        recording_id: Optional recording ID
        
    Returns:
        Tuple of (success: bool, url: Optional[str])
    """
    try:
        uploader = S3Uploader()
        
        # Create organized S3 key structure: recordings/camera_id/date/filename
        file_path = Path(local_file_path)
        date_str = timestamp.split('T')[0]  # Extract date from timestamp
        
        # Build S3 key
        if hasattr(settings, 'AWS_LOCATION'):
            base_location = settings.AWS_LOCATION
        else:
            base_location = 'recordings'
        
        s3_key = f"{base_location}/{camera_id}/{date_str}/{file_path.name}"
        
        # Prepare metadata
        metadata = {
            'camera_id': str(camera_id),
            'timestamp': timestamp,
            'upload_date': datetime.now().isoformat(),
        }
        
        if recording_id:
            metadata['recording_id'] = str(recording_id)
        
        # Upload file
        success, url = uploader.upload_file(
            file_path=local_file_path,
            s3_key=s3_key,
            metadata=metadata
        )
        
        return success, url
        
    except Exception as e:
        logger.error(f"Error in upload_cctv_recording: {str(e)}")
        return False, None


def get_recording_url(s3_key: str, expiration: int = 7200) -> Optional[str]:
    """
    Get a presigned URL for accessing a recording
    
    Args:
        s3_key: S3 object key
        expiration: URL expiration time in seconds (default: 2 hours)
        
    Returns:
        Presigned URL or None if error
    """
    try:
        uploader = S3Uploader()
        return uploader.generate_presigned_url(s3_key, expiration)
    except Exception as e:
        logger.error(f"Error getting recording URL: {str(e)}")
        return None

