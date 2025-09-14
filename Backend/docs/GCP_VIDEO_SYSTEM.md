# GCP Video Upload & Access System

## Overview

This system automatically uploads scheduled recordings to Google Cloud Storage (GCP) and provides secure access for playback and download.

## 🚀 Features

- **Automatic Upload**: New recordings are automatically uploaded to GCP after completion
- **Secure Access**: Videos are accessed via signed URLs with configurable expiration
- **Fallback Support**: Falls back to local storage if GCP upload fails
- **Background Sync**: Periodic background task syncs any missed uploads
- **Multiple Access Methods**: Download, streaming, and programmatic URL access
- **Cross-Platform**: Works on Windows, Linux, and macOS

## 📋 Configuration

### Required Settings

```python
# In config/settings.py

# GCP Cloud Storage Configuration
GCP_STORAGE_BUCKET_NAME = 'your-bucket-name'
GCP_STORAGE_PROJECT_ID = 'your-project-id'
GCP_STORAGE_CREDENTIALS_PATH = 'path/to/credentials.json'
GCP_STORAGE_USE_GCS = True

# GCP Storage Behavior
GCP_STORAGE_AUTO_UPLOAD = True    # Auto-upload new recordings
GCP_STORAGE_CLEANUP_LOCAL = True  # Clean up local files after upload
```

### GCP Setup

1. **Create GCP Project and Bucket**
   ```bash
   # Create bucket
   gsutil mb gs://your-bucket-name
   
   # Set bucket permissions (if needed)
   gsutil iam ch serviceAccount:your-service-account@project.iam.gserviceaccount.com:objectAdmin gs://your-bucket-name
   ```

2. **Service Account Permissions**
   - `storage.objects.create`
   - `storage.objects.get`
   - `storage.objects.delete`
   - `storage.objects.list`

## 🎬 How It Works

### 1. Recording Process

```
Camera Recording → Local Storage → GCP Upload → Local Cleanup (optional)
```

1. **Recording Creation**: When a scheduled recording starts, it's initially saved locally
2. **Recording Completion**: After recording finishes successfully
3. **Automatic Upload**: System uploads the video to GCP bucket
4. **Database Update**: Recording's `storage_type` is updated to 'gcp'
5. **Local Cleanup**: Local file is deleted (if `GCP_STORAGE_CLEANUP_LOCAL=True`)

### 2. Video Access

```
Request → Check Storage Type → Generate Signed URL → Redirect/Stream
```

- **GCP Videos**: Accessed via time-limited signed URLs (default: 2 hours)
- **Local Videos**: Served directly from Django media files
- **Security**: All access requires authentication and proper permissions

## 🔧 API Endpoints

### Download Video
```http
GET /api/recordings/{id}/download/
```
Downloads the video file with proper content headers.

### Stream Video
```http
GET /api/recordings/{id}/stream/
```
Streams the video for in-browser playback.

### Get Video URL
```http
GET /api/recordings/{id}/get_url/
```
Returns a JSON response with the video URL and metadata:

```json
{
  "url": "https://storage.googleapis.com/bucket/path/to/video.mp4?X-Goog-Algorithm=...",
  "storage_type": "gcp",
  "expires_in_minutes": 120,
  "content_type": "video/mp4",
  "file_size": 15728640,
  "file_size_mb": 15.0,
  "recording_name": "Scheduled Recording",
  "camera_name": "Main Camera",
  "created_at": "2025-01-15T10:30:00Z",
  "duration": 300.0
}
```

### Bulk URL Generation
```http
GET /api/recordings/get_urls/?ids=uuid1&ids=uuid2&ids=uuid3
```

## 🛠️ Management Commands

### Sync Recordings to GCP
```bash
# Dry run to see what would be synced
python manage.py sync_recordings_to_gcp --dry-run

# Sync up to 5 recordings
python manage.py sync_recordings_to_gcp --batch-size=5

# Skip missing files instead of failing
python manage.py sync_recordings_to_gcp --skip-missing

# Force sync even if auto-upload is disabled
python manage.py sync_recordings_to_gcp --force
```

### Migrate Existing Recordings
```bash
# Migrate all local recordings to GCP
python manage.py migrate_to_gcp --batch-size=3 --skip-missing --cleanup-tmp
```

## 🔄 Background Tasks

The system includes automatic background tasks:

- **GCP Sync**: Runs every 30 minutes to upload any missed recordings
- **Cleanup**: Daily cleanup of old recordings (respects retention settings)
- **Schedule Check**: Hourly check for expired one-time schedules

## 🧪 Testing

### Run Test Suite
```bash
cd Backend
python test_gcp_video_access.py
```

The test suite checks:
- GCP configuration and connectivity
- Recording upload status
- Video accessibility via signed URLs
- API endpoint functionality

### Manual Testing

1. **Create a Test Recording**
   ```python
   # In Django shell
   from apps.cctv.models import Camera
   camera = Camera.objects.first()
   recording = camera.auto_record_5min()  # 5-second test recording
   ```

2. **Check Upload Status**
   ```python
   recording.refresh_from_db()
   print(f"Storage: {recording.storage_type}")
   print(f"File exists: {recording.file_exists}")
   ```

3. **Generate Access URL**
   ```python
   from apps.cctv.storage_service import storage_service
   url = storage_service.get_file_url(recording.file_path, signed=True)
   print(f"URL: {url}")
   ```

## 📱 Frontend Integration

### JavaScript Example
```javascript
// Get video URL
fetch(`/api/recordings/${recordingId}/get_url/`, {
    headers: {
        'Authorization': 'Bearer ' + token
    }
})
.then(response => response.json())
.then(data => {
    if (data.url) {
        // Use the URL in video player
        videoElement.src = data.url;
        
        // Set up expiration handling
        if (data.expires_in_minutes) {
            setTimeout(() => {
                // Refresh URL before expiration
                refreshVideoUrl();
            }, (data.expires_in_minutes - 5) * 60 * 1000);
        }
    }
});
```

### React Component Example
```jsx
const VideoPlayer = ({ recordingId }) => {
    const [videoUrl, setVideoUrl] = useState(null);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
        fetchVideoUrl();
    }, [recordingId]);
    
    const fetchVideoUrl = async () => {
        try {
            const response = await fetch(`/api/recordings/${recordingId}/get_url/`);
            const data = await response.json();
            setVideoUrl(data.url);
            
            // Auto-refresh before expiration
            if (data.expires_in_minutes) {
                setTimeout(fetchVideoUrl, (data.expires_in_minutes - 5) * 60 * 1000);
            }
        } catch (error) {
            console.error('Failed to fetch video URL:', error);
        } finally {
            setLoading(false);
        }
    };
    
    if (loading) return <div>Loading video...</div>;
    
    return (
        <video controls width="100%">
            <source src={videoUrl} type="video/mp4" />
            Your browser does not support the video tag.
        </video>
    );
};
```

## 🔒 Security Considerations

1. **Signed URLs**: All GCP access uses signed URLs with limited expiration
2. **Authentication**: API endpoints require user authentication
3. **Permissions**: Users can only access recordings they have permission for
4. **CORS**: Proper CORS headers for cross-origin access
5. **Content-Type**: Proper content type headers for security

## 📊 Monitoring

### Check System Status
```python
# In Django shell
from apps.cctv.models import Recording

# Count by storage type
gcp_count = Recording.objects.filter(storage_type='gcp').count()
local_count = Recording.objects.filter(storage_type='local').count()

print(f"GCP: {gcp_count}, Local: {local_count}")

# Check recent uploads
recent = Recording.objects.filter(
    storage_type='gcp',
    created_at__gte=timezone.now() - timedelta(days=1)
).count()
print(f"Uploaded in last 24h: {recent}")
```

### Logs to Monitor
- `apps.cctv.streaming`: Recording completion and upload
- `apps.cctv.storage_service`: GCP operations
- `apps.cctv.scheduler`: Background sync tasks

## 🚨 Troubleshooting

### Common Issues

1. **"GCP Storage bucket not available"**
   - Check credentials file exists and is valid
   - Verify service account has proper permissions
   - Test network connectivity to GCP

2. **"Failed to upload recording to GCP Storage"**
   - Check bucket permissions
   - Verify file isn't corrupted or in use
   - Check GCP quotas and billing

3. **"Unable to generate download URL"**
   - File might not exist in GCP
   - Check service account signing permissions
   - Verify file path is correct

4. **Videos not uploading automatically**
   - Check `GCP_STORAGE_AUTO_UPLOAD` setting
   - Verify background scheduler is running
   - Check for errors in recording completion

### Debug Commands

```bash
# Check GCP connectivity
python test_gcp_video_access.py

# Force sync specific recording
python manage.py sync_recordings_to_gcp --recording-id=<uuid>

# Clean up .tmp files
python manage.py migrate_to_gcp --cleanup-tmp --dry-run
```

## 📈 Performance Optimization

1. **Batch Operations**: Use batch sizes of 3-5 for uploads to avoid timeouts
2. **Timeout Settings**: Automatic timeout scaling based on file size
3. **Background Processing**: Non-blocking uploads don't affect recording
4. **CDN**: Consider CloudFlare or GCP CDN for better video delivery
5. **Compression**: Use efficient video codecs (H.264, H.265)

## 🔮 Future Enhancements

- **Multi-region Support**: Distribute videos across GCP regions
- **Video Transcoding**: Automatic conversion to web-optimized formats
- **Streaming Optimization**: HLS/DASH for adaptive bitrate streaming
- **Analytics**: Track video access and usage patterns
- **Backup Strategy**: Multi-cloud backup support
