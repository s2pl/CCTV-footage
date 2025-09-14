# GCP Cloud Storage Integration

This document describes the GCP Cloud Storage integration for the CCTV recording system. The integration allows you to store video recordings in Google Cloud Storage instead of local storage while maintaining the same API endpoints and functionality.

## Features

- **Unified Storage Interface**: Seamlessly switch between local and GCP storage
- **Same API Endpoints**: No changes required to existing frontend code
- **Automatic File Management**: Files are automatically uploaded to GCP after recording
- **Signed URLs**: Secure access to recordings with time-limited URLs
- **Migration Support**: Tools to migrate existing recordings to GCP
- **Fallback Support**: Graceful fallback to local storage if GCP is unavailable

## Architecture

### Storage Service Layer

The `UnifiedStorageService` class provides a single interface for both local and GCP storage:

```python
from apps.cctv.storage_service import storage_service

# Upload a recording
storage_path = storage_service.upload_recording(
    local_file_path="/path/to/local/file.mp4",
    recording_id="uuid",
    camera_id="uuid", 
    filename="recording.mp4"
)

# Get file URL
file_url = storage_service.get_file_url(storage_path)

# Check if file exists
exists = storage_service.file_exists(storage_path)
```

### Database Integration

The `Recording` model has been updated to work with both storage types:

- `file_path`: Stores the storage path (local relative path or GCP object path)
- `file_exists`: Checks existence in the configured storage
- `file_url`: Returns appropriate URL for the storage type
- `update_file_info()`: Updates file size from the storage system

### API Endpoints

All existing API endpoints continue to work unchanged:

- `GET /api/recordings/` - List recordings
- `GET /api/recordings/{id}/download/` - Download recording
- `GET /api/recordings/{id}/stream/` - Stream recording
- `POST /api/recordings/` - Create new recording

## Configuration

### Environment Variables

Add these variables to your `.env` file:

```env
# Enable GCP Storage
GCP_STORAGE_USE_GCS=True

# GCP Project Configuration
GCP_STORAGE_PROJECT_ID=your-project-id
GCP_STORAGE_BUCKET_NAME=your-bucket-name

# Optional: Path to service account key file
GCP_STORAGE_CREDENTIALS_PATH=/path/to/service-account.json
```

### Service Account Setup

1. Create a GCP service account with Storage Object Admin role
2. Download the JSON key file
3. Set the path in `GCP_STORAGE_CREDENTIALS_PATH` or use `GOOGLE_APPLICATION_CREDENTIALS` environment variable

## File Structure

Recordings are stored in GCP with the same structure as local storage:

```
bucket-name/
└── media/
    └── recordings/
        └── {camera_id}/
            ├── {camera_name}_{timestamp}.mp4
            ├── SCHEDULED_{camera_name}_{timestamp}.mp4
            └── ...
```

## Usage Examples

### Recording a Video

```python
from apps.cctv.streaming import recording_manager

# Start recording (automatically uses configured storage)
recording = recording_manager.start_recording(
    camera=camera,
    duration_minutes=5,
    recording_name="Test Recording"
)

# The file is automatically uploaded to GCP (if enabled)
print(f"Recording stored at: {recording.file_path}")
print(f"Access URL: {recording.file_url}")
```

### Accessing Recordings

```python
from apps.cctv.models import Recording

# Get a recording
recording = Recording.objects.get(id="uuid")

# Check if file exists (works with both local and GCP)
if recording.file_exists:
    print(f"File URL: {recording.file_url}")
    print(f"File size: {recording.file_size_mb} MB")
else:
    print("File not found")
```

### Downloading Files

```python
# For GCP storage, this returns a signed URL
# For local storage, this serves the file directly
response = requests.get(f"/api/recordings/{recording_id}/download/")
```

## Management Commands

### Test GCP Configuration

```bash
python manage.py test_gcp_storage
```

Options:
- `--upload-test`: Test file upload
- `--download-test`: Test file download  
- `--list-bucket`: List bucket contents

### Migrate Existing Recordings

```bash
python manage.py migrate_to_gcp
```

Options:
- `--dry-run`: Preview what would be migrated
- `--batch-size N`: Process N recordings at a time
- `--recording-id UUID`: Migrate specific recording
- `--camera-id UUID`: Migrate recordings for specific camera

## Error Handling

The system includes comprehensive error handling:

1. **GCP Unavailable**: Falls back to local storage
2. **Upload Failures**: Logs errors and continues with local storage
3. **Authentication Issues**: Clear error messages in logs
4. **Network Problems**: Retry logic and graceful degradation

## Security Considerations

1. **Service Account Permissions**: Use minimal required permissions
2. **Signed URLs**: Time-limited access to recordings
3. **Bucket Permissions**: Configure appropriate bucket-level access
4. **Credential Management**: Never commit service account keys to version control

## Performance Considerations

1. **Upload Strategy**: Files are uploaded after recording completion
2. **Local Cleanup**: Local files can be removed after successful upload
3. **Caching**: Consider implementing caching for frequently accessed files
4. **CDN**: Use Cloud CDN for better global performance

## Monitoring and Logging

The system provides detailed logging for:

- Storage service initialization
- File upload/download operations
- Error conditions and fallbacks
- Performance metrics

Check the Django logs for storage-related messages:

```bash
tail -f logs/debug.log | grep -i storage
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify service account key is valid
   - Check IAM permissions
   - Ensure project ID is correct

2. **Bucket Access Issues**
   - Verify bucket name and existence
   - Check bucket permissions
   - Ensure bucket is in the correct region

3. **Upload Failures**
   - Check network connectivity
   - Verify file permissions
   - Check GCP quotas and limits

### Debug Mode

Enable debug logging for GCP operations:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'google.cloud': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'apps.cctv.storage_service': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Migration Guide

### From Local to GCP Storage

1. **Setup GCP**: Follow the GCP setup guide
2. **Test Configuration**: Run `test_gcp_storage` command
3. **Migrate Existing Files**: Use `migrate_to_gcp` command
4. **Enable GCP**: Set `GCP_STORAGE_USE_GCS=True`
5. **Verify**: Test new recordings and existing file access

### From GCP to Local Storage

1. **Disable GCP**: Set `GCP_STORAGE_USE_GCS=False`
2. **Download Files**: Use GCP console or gsutil to download files
3. **Update Database**: Update file paths in database if needed
4. **Verify**: Test file access and new recordings

## Cost Optimization

1. **Storage Classes**: Use appropriate storage classes (Standard, Nearline, Coldline)
2. **Lifecycle Policies**: Automatically delete or archive old recordings
3. **Regional Storage**: Choose storage location close to your users
4. **Monitoring**: Use GCP Cost Management tools to monitor usage

## Support

For issues related to:

- **GCP Setup**: Check the [GCP Setup Guide](GCP_SETUP_GUIDE.md)
- **Integration Issues**: Review logs and this documentation
- **Performance**: Consider implementing caching or CDN
- **Security**: Review IAM permissions and bucket policies
