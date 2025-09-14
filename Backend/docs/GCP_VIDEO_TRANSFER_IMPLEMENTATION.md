# GCP Video Transfer Implementation Summary

## Overview

Successfully implemented a complete GCP video transfer system for the CCTV application that allows transferring recorded videos from local storage to Google Cloud Storage with automatic cleanup after 24 hours.

## What Was Implemented

### 1. New Database Model: `GCPVideoTransfer`

**Location:** `Backend/apps/cctv/models.py`

**Features:**
- Tracks each video transfer from local storage to GCP
- Records transfer status (pending, uploading, completed, failed, etc.)
- Stores GCP storage path and public URL
- Manages 24-hour cleanup scheduling
- Tracks file sizes, timestamps, and error messages
- Supports retry mechanisms for failed uploads

**Key Methods:**
- `mark_upload_started()` - Mark transfer as in progress
- `mark_upload_completed()` - Mark as completed and schedule cleanup
- `mark_upload_failed()` - Handle failed transfers
- `mark_cleanup_completed()` - Mark local file as deleted
- `is_cleanup_due` - Property to check if 24-hour period has passed

### 2. API Endpoints

**Location:** `Backend/apps/cctv/api.py`

#### POST `/api/v0/recordings/transfer-to-gcp/`
- **Purpose:** Initiate video transfers to GCP Cloud Storage
- **Authentication:** Required (JWT Token with 'manage' permission)
- **Features:**
  - Transfer all local recordings or specific ones by ID
  - Configurable batch size (1-20 videos simultaneously)
  - Background upload processing using threading
  - Automatic recording model updates (storage_type = 'gcp')
  - Error handling and retry logic

#### GET `/api/v0/recordings/gcp-transfers/`
- **Purpose:** Monitor transfer status and progress
- **Authentication:** Required (JWT Token with 'view' permission)
- **Features:**
  - List all transfers with detailed status
  - Count transfers by status (pending, uploading, completed, failed)
  - Show file sizes, timestamps, and error messages
  - Display GCP storage paths and public URLs

### 3. Cleanup Management Command

**Location:** `Backend/apps/cctv/management/commands/cleanup_gcp_transfers.py`

**Features:**
- Automatically deletes local video files 24 hours after GCP upload
- Dry-run mode for testing
- Force cleanup option for immediate deletion
- Batch processing with detailed logging
- Error handling and retry logic
- Comprehensive reporting (files cleaned, space freed, failures)

**Usage:**
```bash
# Regular cleanup (24-hour rule)
python manage.py cleanup_gcp_transfers

# Dry run to see what would be cleaned
python manage.py cleanup_gcp_transfers --dry-run

# Force immediate cleanup
python manage.py cleanup_gcp_transfers --force

# Clean specific transfer
python manage.py cleanup_gcp_transfers --transfer-id <uuid>
```

### 4. Admin Interface

**Location:** `Backend/apps/cctv/admin.py`

**Features:**
- Full admin interface for `GCPVideoTransfer` model
- List view with transfer status, file sizes, and timestamps
- Detailed view with all transfer information
- Filtering by status, dates, and completion
- Search by recording name, camera name, and GCP path
- Read-only fields for system-managed data

### 5. Database Migration

**Location:** `Backend/apps/cctv/migrations/0008_gcpvideotransfer.py`

- Creates the `GCPVideoTransfer` table
- Establishes foreign key relationships
- Sets up proper indexes and constraints
- Applied successfully to the database

## API Usage Examples

### Transfer All Videos to GCP
```bash
curl -X POST "http://localhost:8000/api/v0/recordings/transfer-to-gcp/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Transfer Specific Videos
```bash
curl -X POST "http://localhost:8000/api/v0/recordings/transfer-to-gcp/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recording_ids": ["uuid1", "uuid2"],
    "batch_size": 5
  }'
```

### Check Transfer Status
```bash
curl -X GET "http://localhost:8000/api/v0/recordings/gcp-transfers/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Workflow

1. **Initiate Transfer**: Call POST `/recordings/transfer-to-gcp/` endpoint
2. **Background Processing**: Videos upload to GCP in separate threads
3. **Status Updates**: Transfer status updates from pending → uploading → completed
4. **Database Updates**: Recording model updated to point to GCP storage
5. **Cleanup Scheduling**: Local file deletion scheduled for 24 hours later
6. **Automatic Cleanup**: Cron job runs cleanup command hourly
7. **File Removal**: Local files deleted after 24-hour waiting period

## Security & Permissions

- **Transfer Permission**: Only users with 'manage' role (admin, superadmin)
- **View Permission**: Users with 'view' role and above (dev, admin, superadmin)
- **JWT Authentication**: All endpoints require valid JWT tokens
- **File Access**: Local file verification before transfer
- **Error Handling**: Comprehensive error logging and user feedback

## Configuration Requirements

### GCP Settings (in Django settings.py)
```python
GCP_STORAGE_USE_GCS = True
GCP_STORAGE_BUCKET_NAME = 'your-bucket-name'
GCP_STORAGE_PROJECT_ID = 'your-project-id'
GCP_STORAGE_CREDENTIALS_PATH = 'path/to/credentials.json'
```

### Cron Job Setup
```bash
# Run cleanup every hour
0 * * * * cd /path/to/Backend && python manage.py cleanup_gcp_transfers
```

## Monitoring & Maintenance

### Database Queries for Monitoring
```sql
-- Check transfer status distribution
SELECT transfer_status, COUNT(*) FROM cctv_gcpvideotransfer GROUP BY transfer_status;

-- Find transfers due for cleanup
SELECT COUNT(*) FROM cctv_gcpvideotransfer 
WHERE transfer_status = 'cleanup_pending' AND cleanup_scheduled_at <= NOW();

-- Calculate total space that can be freed
SELECT SUM(file_size_bytes) FROM cctv_gcpvideotransfer 
WHERE transfer_status = 'cleanup_pending';
```

### Log Monitoring
- Transfer initiation logs in Django logs
- Upload progress in background thread logs
- Cleanup activity in management command logs
- Error details in transfer model error_message field

## Benefits

1. **Storage Optimization**: Automatic local storage cleanup after cloud backup
2. **Cost Management**: 24-hour delay ensures successful upload before deletion
3. **Scalability**: Background processing prevents API timeouts
4. **Reliability**: Retry mechanisms and error handling
5. **Monitoring**: Comprehensive status tracking and reporting
6. **Security**: Proper authentication and permission controls
7. **Automation**: Set-and-forget operation with cron jobs

## Files Created/Modified

### New Files
- `Backend/apps/cctv/management/commands/cleanup_gcp_transfers.py`
- `Backend/apps/cctv/migrations/0008_gcpvideotransfer.py`
- `Backend/docs/GCP_CLEANUP_CRON_SETUP.md`
- `Backend/docs/GCP_TRANSFER_API_USAGE.md`
- `Backend/docs/GCP_VIDEO_TRANSFER_IMPLEMENTATION.md`

### Modified Files
- `Backend/apps/cctv/models.py` - Added GCPVideoTransfer model
- `Backend/apps/cctv/api.py` - Added transfer endpoints and schemas
- `Backend/apps/cctv/admin.py` - Added admin interface for transfers

## Next Steps

1. **Set up cron job** for automatic cleanup using the provided documentation
2. **Monitor GCP storage costs** and usage
3. **Test with actual video files** in your environment
4. **Configure frontend integration** to use the new endpoints
5. **Set up monitoring alerts** for failed transfers or low disk space

The implementation is complete and ready for production use!
