# Recording Upload Guarantee System

## Overview

This document outlines the comprehensive system implemented to **guarantee** that all recorded videos are uploaded to GCP storage immediately after completion.

## 🛡️ Multi-Layer Upload Security

### Layer 1: Primary Upload (Main Recording Flow)
**Location**: `apps/cctv/streaming.py` - `_upload_completed_recording()`

- **When**: Immediately after recording completion
- **Trigger**: Called directly in the recording completion flow
- **Features**:
  - ✅ Retry mechanism (3 attempts with exponential backoff)
  - ✅ File existence verification
  - ✅ Upload verification after completion
  - ✅ Automatic local file cleanup
  - ✅ Comprehensive error logging

```python
# In recording completion flow:
if recording.status == 'completed':
    upload_success = self._upload_completed_recording(recording, file_path)
    if upload_success:
        logger.info(f"🚀 Recording {recording.id} successfully uploaded to GCP")
    else:
        logger.warning(f"⚠️ Recording {recording.id} upload failed, will retry via background sync")
```

### Layer 2: Signal-Based Safety Net
**Location**: `apps/cctv/signals.py` - `handle_recording_completion()`

- **When**: Triggered by Django signals when recording status changes to 'completed'
- **Purpose**: Catch any recordings that weren't uploaded in the primary flow
- **Features**:
  - ✅ Background thread processing (non-blocking)
  - ✅ Duplicate upload prevention
  - ✅ Automatic retry for failed uploads

### Layer 3: Background Sync (Every 30 Minutes)
**Location**: `apps/cctv/scheduler.py` - `sync_recordings_to_gcp()`

- **When**: Runs automatically every 30 minutes
- **Purpose**: Systematic check for any recordings still in local storage
- **Features**:
  - ✅ Processes up to 10 recordings per run
  - ✅ Skips files already being processed
  - ✅ Exponential backoff for failed uploads

### Layer 4: Safety Check Command
**Location**: `apps/cctv/management/commands/ensure_gcp_uploads.py`

- **When**: Can be run manually or via cron job
- **Purpose**: Comprehensive check and upload of any missed recordings
- **Usage**:
  ```bash
  # Manual run
  python manage.py ensure_gcp_uploads
  
  # Cron job (every hour)
  0 * * * * cd /path/to/project && python manage.py ensure_gcp_uploads
  ```

## 🔄 Upload Flow Diagram

```
Recording Starts → Recording Completes → Status = 'completed'
                                             ↓
                                    PRIMARY UPLOAD
                                    (Layer 1: Direct)
                                             ↓
                                      Upload Success?
                                      ↙            ↘
                                   YES              NO
                                    ↓               ↓
                              GCP Storage    SIGNAL TRIGGER
                              Local Cleanup   (Layer 2: Safety)
                                    ↓               ↓
                                 DONE         Background Upload
                                                    ↓
                                              Upload Success?
                                              ↙            ↘
                                           YES              NO
                                            ↓               ↓
                                       GCP Storage    BACKGROUND SYNC
                                       Local Cleanup   (Layer 3: 30min)
                                            ↓               ↓
                                         DONE         Retry Upload
                                                            ↓
                                                    MANUAL COMMAND
                                                    (Layer 4: Safety)
```

## 📊 Upload Verification

### Real-Time Monitoring
```python
# Check upload status
from apps.cctv.models import Recording

# Count by storage type
gcp_count = Recording.objects.filter(storage_type='gcp').count()
local_count = Recording.objects.filter(storage_type='local').count()

print(f"GCP: {gcp_count}, Local: {local_count}")
```

### Validation Script
```bash
# Run comprehensive validation
cd Backend
python validate_gcp_upload_system.py
```

### Upload Checker
```bash
# Check and ensure all recordings are uploaded
cd Backend
python ensure_recording_upload.py
```

## 🚨 Error Handling & Recovery

### Upload Failures
1. **Network Issues**: Automatic retry with exponential backoff
2. **File Missing**: Skip and log warning
3. **GCP Errors**: Log error, keep in local storage for retry
4. **Permission Issues**: Log error with detailed message

### Recovery Mechanisms
1. **Automatic**: Background sync every 30 minutes
2. **Manual**: Run management commands
3. **Monitoring**: Check logs and run validation scripts

### Logging
All upload activities are logged with detailed information:

```
✅ Recording abc123 successfully uploaded to GCP: recordings/camera-id/video.mp4
⚠️ Recording def456 upload failed, will retry via background sync
🔄 Starting background GCP sync for 3 recordings
```

## 🔧 Configuration

### Required Settings
```python
# config/settings.py
GCP_STORAGE_USE_GCS = True           # Enable GCP storage
GCP_STORAGE_AUTO_UPLOAD = True       # Enable automatic uploads
GCP_STORAGE_CLEANUP_LOCAL = True     # Clean up local files after upload
```

### Optional Settings
```python
# Customize behavior
GCP_STORAGE_UPLOAD_TIMEOUT = 300     # Upload timeout in seconds
GCP_STORAGE_RETRY_ATTEMPTS = 3       # Number of retry attempts
GCP_STORAGE_RETRY_DELAY = 5          # Initial retry delay in seconds
```

## 📈 Performance Considerations

### Upload Timing
- **Small files** (< 100MB): 5-minute timeout
- **Large files** (> 100MB): 10-minute timeout
- **Retry delays**: 5s, 10s, 20s (exponential backoff)

### Batch Processing
- **Background sync**: 10 recordings per run
- **Manual commands**: Configurable batch size
- **Signal processing**: Individual recordings

### Resource Usage
- **Background threads**: Used for signal-based uploads
- **Scheduler jobs**: Lightweight, run every 30 minutes
- **Memory usage**: Minimal, files streamed to GCP

## ✅ Testing & Validation

### Automated Tests
1. **Upload Mechanism**: Verify upload method integration
2. **Signal Integration**: Check signal handlers are registered
3. **Background Sync**: Confirm scheduler jobs are active
4. **Management Commands**: Verify commands exist and work
5. **Upload Flow**: Test actual file upload
6. **Video Access**: Verify uploaded videos are accessible

### Manual Testing
```bash
# 1. Create a test recording
python manage.py shell
>>> from apps.cctv.models import Camera
>>> camera = Camera.objects.first()
>>> recording = camera.auto_record_5min()

# 2. Wait for recording to complete and check status
>>> recording.refresh_from_db()
>>> print(f"Storage: {recording.storage_type}")  # Should be 'gcp'

# 3. Test video access
>>> from apps.cctv.storage_service import storage_service
>>> url = storage_service.get_file_url(recording.file_path, signed=True)
>>> print(f"URL: {url}")  # Should generate signed URL
```

## 🎯 Success Metrics

### Upload Success Rate
- **Target**: 99.9% of recordings uploaded within 5 minutes
- **Measurement**: Monitor logs and database statistics
- **Alert**: If local storage count > threshold

### Performance Metrics
- **Upload Speed**: Monitor upload duration vs file size
- **Retry Rate**: Track how often retries are needed
- **Background Sync**: Monitor how many recordings need background sync

## 🚀 Production Deployment

### Pre-Deployment Checklist
- [ ] GCP credentials configured
- [ ] Bucket permissions verified
- [ ] Settings properly configured
- [ ] Validation script passes all tests
- [ ] Monitoring/alerting set up

### Post-Deployment Verification
1. Create test recording
2. Verify automatic upload
3. Check background sync is running
4. Test video access via API
5. Monitor logs for any errors

## 📞 Troubleshooting

### Common Issues

**"Upload failed, will retry via background sync"**
- Check GCP credentials and permissions
- Verify network connectivity
- Check file isn't corrupted or in use

**"No recordings need GCP sync"** (but local recordings exist)
- Check if recordings have status='completed'
- Verify files aren't .tmp files
- Check if GCP_STORAGE_AUTO_UPLOAD is enabled

**"Signal upload already in progress"**
- Normal behavior, prevents duplicate uploads
- Indicates system is working correctly

### Debug Commands
```bash
# Check system status
python validate_gcp_upload_system.py

# Force upload all local recordings
python manage.py ensure_gcp_uploads --force

# Check specific recording
python manage.py shell
>>> from apps.cctv.models import Recording
>>> r = Recording.objects.get(id='recording-uuid')
>>> print(f"Status: {r.status}, Storage: {r.storage_type}, File exists: {r.file_exists}")
```

## 🎉 Conclusion

This multi-layer system provides **guaranteed upload** of all recordings to GCP storage through:

1. **Immediate upload** after recording completion
2. **Signal-based safety net** for any missed uploads
3. **Background sync** every 30 minutes
4. **Manual commands** for comprehensive checks
5. **Comprehensive logging** and monitoring
6. **Robust error handling** and retry mechanisms

The system is designed to be **fault-tolerant**, **self-healing**, and **production-ready**.
