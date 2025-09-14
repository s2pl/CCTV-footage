# GCP Video Transfer API Usage Guide

This document explains how to use the new GCP video transfer endpoints in the CCTV management system.

## Overview

The system now provides endpoints to transfer recorded videos from local storage to Google Cloud Storage (GCP) with automatic cleanup after 24 hours.

## API Endpoints

### 1. Transfer Videos to GCP

**Endpoint:** `POST /api/v0/recordings/transfer-to-gcp/`

**Description:** Initiate transfer of recorded videos from local storage to GCP Cloud Storage.

**Authentication:** Required (JWT Token)

**Request Body:**
```json
{
  "recording_ids": ["uuid1", "uuid2"],  // Optional: specific recordings to transfer
  "batch_size": 5                       // Optional: number of videos to process simultaneously (1-20)
}
```

**Response:**
```json
{
  "message": "Successfully initiated 3 video transfers to GCP Cloud Storage",
  "total_recordings": 5,
  "initiated_transfers": 3,
  "already_transferred": 1,
  "failed_initiations": 1,
  "transfer_ids": ["transfer-uuid1", "transfer-uuid2", "transfer-uuid3"]
}
```

### 2. Check Transfer Status

**Endpoint:** `GET /api/v0/recordings/gcp-transfers/`

**Description:** Get the status of all video transfers to GCP Cloud Storage.

**Authentication:** Required (JWT Token)

**Response:**
```json
{
  "transfers": [
    {
      "transfer_id": "uuid",
      "recording_name": "Front Door - 2024-01-15 10:30:00",
      "transfer_status": "completed",
      "file_size_mb": 125.5,
      "gcp_storage_path": "recordings/camera-id/recording-id/video.mp4",
      "gcp_public_url": "https://storage.googleapis.com/bucket/path/video.mp4",
      "upload_started_at": "2024-01-15T10:30:00Z",
      "upload_completed_at": "2024-01-15T10:35:00Z",
      "cleanup_scheduled_at": "2024-01-16T10:35:00Z",
      "cleanup_completed_at": null,
      "error_message": null,
      "retry_count": 0
    }
  ],
  "total_count": 1,
  "pending_count": 0,
  "uploading_count": 0,
  "completed_count": 1,
  "failed_count": 0
}
```

## Transfer Status Values

- **`pending`**: Transfer is queued but not yet started
- **`uploading`**: File is currently being uploaded to GCP
- **`completed`**: Upload successful, cleanup scheduled for 24 hours later
- **`failed`**: Upload failed (check error_message)
- **`cleanup_pending`**: Upload complete, waiting for 24-hour cleanup
- **`cleanup_completed`**: Local file has been deleted

## Usage Examples

### Using curl

```bash
# Get JWT token first (replace with your auth endpoint)
TOKEN="your-jwt-token"

# Transfer all local recordings to GCP
curl -X POST "http://localhost:8000/api/v0/recordings/transfer-to-gcp/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'

# Transfer specific recordings
curl -X POST "http://localhost:8000/api/v0/recordings/transfer-to-gcp/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recording_ids": ["uuid1", "uuid2"],
    "batch_size": 3
  }'

# Check transfer status
curl -X GET "http://localhost:8000/api/v0/recordings/gcp-transfers/" \
  -H "Authorization: Bearer $TOKEN"
```

### Using JavaScript/Fetch

```javascript
const API_BASE = 'http://localhost:8000/api/v0';
const token = 'your-jwt-token';

// Transfer videos to GCP
async function transferToGCP(recordingIds = null, batchSize = 5) {
  const response = await fetch(`${API_BASE}/recordings/transfer-to-gcp/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      recording_ids: recordingIds,
      batch_size: batchSize
    })
  });
  
  return await response.json();
}

// Check transfer status
async function getTransferStatus() {
  const response = await fetch(`${API_BASE}/recordings/gcp-transfers/`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    }
  });
  
  return await response.json();
}

// Usage
transferToGCP().then(result => {
  console.log('Transfer initiated:', result);
});

getTransferStatus().then(status => {
  console.log('Transfer status:', status);
});
```

### Using Python Requests

```python
import requests

API_BASE = 'http://localhost:8000/api/v0'
TOKEN = 'your-jwt-token'

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json'
}

# Transfer all recordings
response = requests.post(f'{API_BASE}/recordings/transfer-to-gcp/', 
                        headers=headers, 
                        json={})
print(response.json())

# Transfer specific recordings
response = requests.post(f'{API_BASE}/recordings/transfer-to-gcp/', 
                        headers=headers, 
                        json={
                            'recording_ids': ['uuid1', 'uuid2'],
                            'batch_size': 3
                        })
print(response.json())

# Check status
response = requests.get(f'{API_BASE}/recordings/gcp-transfers/', headers=headers)
print(response.json())
```

## Workflow

1. **Initiate Transfer**: Call the transfer endpoint to start uploading videos to GCP
2. **Monitor Progress**: Use the status endpoint to check upload progress
3. **Automatic Cleanup**: After 24 hours, local files are automatically deleted
4. **Access Videos**: Use the `gcp_public_url` to access videos in the cloud

## Error Handling

### Common Error Responses

```json
{
  "detail": "You don't have permission to transfer recordings to GCP"
}
```

```json
{
  "detail": "GCP Storage is not configured. Please contact administrator."
}
```

```json
{
  "detail": "No recordings found for transfer"
}
```

### Transfer Failures

If a transfer fails, check the `error_message` field in the transfer status:

```json
{
  "transfer_status": "failed",
  "error_message": "Local file not found: /path/to/video.mp4",
  "retry_count": 1
}
```

## Best Practices

1. **Batch Processing**: Use appropriate batch sizes (5-10) to avoid overwhelming the system
2. **Monitor Status**: Regularly check transfer status for failed uploads
3. **Handle Failures**: Implement retry logic for failed transfers
4. **Storage Planning**: Ensure sufficient GCP storage quota
5. **Network Considerations**: Large file transfers may take time

## Permissions

Users need the following permissions to use these endpoints:
- **Transfer Videos**: `manage` permission level (admin, superadmin)
- **View Status**: `view` permission level (dev, admin, superadmin)

## Integration with Frontend

The endpoints are designed to work with the existing CCTV frontend. Consider adding:

1. **Transfer Button**: In the recordings list/detail view
2. **Progress Indicator**: Show upload progress
3. **Status Dashboard**: Display transfer statistics
4. **Error Notifications**: Alert users of failed transfers

## Monitoring and Maintenance

- Set up the cleanup cron job (see `GCP_CLEANUP_CRON_SETUP.md`)
- Monitor GCP storage usage and costs
- Regularly check for failed transfers
- Keep an eye on local disk space before transfers complete
