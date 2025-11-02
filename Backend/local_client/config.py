"""
Configuration management for local recording client
"""
import os
from pathlib import Path
from typing import Optional, Tuple, List
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    # Also try .env in local_client directory
    local_env = Path(__file__).parent / '.env'
    if local_env.exists():
        load_dotenv(local_env)


class Config:
    """Application configuration"""
    
    # Backend API Configuration
    BACKEND_API_URL: str = os.getenv('BACKEND_API_URL', 'http://localhost:8000')
    CLIENT_TOKEN: str = os.getenv('CLIENT_TOKEN', '7oFIZRC0y9uECFXjBUlZqV_Jx8_vFD7G3RLNzY5MrSY')
    CLIENT_ID: str = os.getenv('CLIENT_ID', '')
    
    # Cloud Storage Backend Selection
    CLOUD_STORAGE_BACKEND: str = os.getenv('CLOUD_STORAGE_BACKEND', 'AWS')  # 'AWS', 'GCP', or 'BOTH'
    
    # AWS S3 Storage Configuration
    AWS_ACCESS_KEY_ID: str = os.getenv('AWS_ACCESS_KEY_ID', 'AKIAXTORPEGA2Y4Q7JCI')
    AWS_SECRET_ACCESS_KEY: str = os.getenv('AWS_SECRET_ACCESS_KEY', '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')
    AWS_SESSION_TOKEN: str = os.getenv('AWS_SESSION_TOKEN', '')  # Optional
    AWS_REGION_NAME: str = os.getenv('AWS_REGION_NAME', 'ap-south-1')
    AWS_BUCKET_NAME: str = os.getenv('AWS_BUCKET_NAME', 'cctv-footage-bucket')
    AWS_S3_SIGNATURE_VERSION: str = os.getenv('AWS_S3_SIGNATURE_VERSION', 's3v4')
    
    # GCP Storage Configuration (Legacy/Backup)
    GCP_CREDENTIALS_PATH: str = os.getenv('GCP_CREDENTIALS_PATH', '')
    GCP_BUCKET_NAME: str = os.getenv('GCP_BUCKET_NAME', '')
    GCP_PROJECT_ID: str = os.getenv('GCP_PROJECT_ID', '')
    
    # Recording Settings
    RECORDING_BASE_DIR: str = os.getenv('RECORDING_BASE_DIR', './recordings')
    CLEANUP_AFTER_UPLOAD: bool = os.getenv('CLEANUP_AFTER_UPLOAD', 'true').lower() == 'true'
    KEEP_LOCAL_DAYS: int = int(os.getenv('KEEP_LOCAL_DAYS', '1'))
    
    # Sync Settings
    SYNC_INTERVAL_SECONDS: int = int(os.getenv('SYNC_INTERVAL_SECONDS', '30'))
    HEARTBEAT_INTERVAL_SECONDS: int = int(os.getenv('HEARTBEAT_INTERVAL_SECONDS', '60'))
    MAX_RETRY_ATTEMPTS: int = int(os.getenv('MAX_RETRY_ATTEMPTS', '5'))
    
    # System Settings
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    MAX_CONCURRENT_RECORDINGS: int = int(os.getenv('MAX_CONCURRENT_RECORDINGS', '4'))
    
    # File paths
    CACHE_DIR: Path = Path(RECORDING_BASE_DIR) / 'cache'
    LOGS_DIR: Path = Path(RECORDING_BASE_DIR) / 'logs'
    RECORDINGS_DIR: Path = Path(RECORDING_BASE_DIR) / 'recordings'
    PENDING_UPLOADS_DIR: Path = Path(RECORDING_BASE_DIR) / 'pending_uploads'
    
    @classmethod
    def validate(cls) -> Tuple[bool, List[str]]:
        """
        Validate configuration
        
        Returns:
            Tuple of (is_valid, errors_list)
            is_valid: True if can proceed (even with warnings)
            errors_list: List of error messages (empty if valid)
        """
        errors = []
        warnings = []
        
        # Required settings
        if not cls.CLIENT_TOKEN:
            errors.append("CLIENT_TOKEN is required")
        
        if not cls.BACKEND_API_URL:
            errors.append("BACKEND_API_URL is required")
        
        # Validate cloud storage configuration based on backend selection
        if cls.CLOUD_STORAGE_BACKEND in ['AWS', 'BOTH']:
            if not cls.AWS_BUCKET_NAME:
                warnings.append("AWS S3 backend selected but AWS_BUCKET_NAME is not set - S3 uploads will be disabled")
            elif not cls.AWS_ACCESS_KEY_ID or not cls.AWS_SECRET_ACCESS_KEY:
                warnings.append("AWS S3 bucket is set but AWS credentials are missing - S3 uploads will be disabled")
        
        # GCP configuration is optional - only validate if trying to use it
        if cls.CLOUD_STORAGE_BACKEND in ['GCP', 'BOTH']:
            if cls.GCP_BUCKET_NAME:
                # If bucket name is set, credentials should be provided
                if not cls.GCP_CREDENTIALS_PATH:
                    warnings.append("GCP_BUCKET_NAME is set but GCP_CREDENTIALS_PATH is missing - GCP uploads will be disabled")
                elif not Path(cls.GCP_CREDENTIALS_PATH).exists():
                    warnings.append(f"GCP credentials file not found: {cls.GCP_CREDENTIALS_PATH} - GCP uploads will be disabled")
        
        if warnings:
            logger.warning("Configuration warnings:")
            for warning in warnings:
                logger.warning(f"  - {warning}")
        
        if errors:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            return False, errors
        
        return True, []
    
    @classmethod
    def setup_directories(cls):
        """Create necessary directories"""
        directories = [
            cls.CACHE_DIR,
            cls.LOGS_DIR,
            cls.RECORDINGS_DIR,
            cls.PENDING_UPLOADS_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
    
    @classmethod
    def get_recording_path(cls, camera_id: str, date_str: str, filename: str) -> Path:
        """Get path for a recording file"""
        return cls.RECORDINGS_DIR / camera_id / date_str / filename
    
    @classmethod
    def get_cache_file(cls, name: str) -> Path:
        """Get path for cache file"""
        return cls.CACHE_DIR / f"{name}.json"


# Global config instance
config = Config()

