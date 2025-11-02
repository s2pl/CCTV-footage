# Local CCTV Recording Client

Standalone Python application for recording CCTV cameras locally and uploading to Google Cloud Storage.

## Features

- **Offline Recording**: Records based on schedules even when backend is unreachable
- **Auto-Sync**: Automatically syncs schedules from backend
- **GCP Upload**: Direct uploads to Google Cloud Storage
- **Resilient**: Queues status updates and uploads for retry
- **Multi-Camera**: Supports multiple cameras simultaneously

## Installation

### Prerequisites

- Python 3.8+
- OpenCV with FFMPEG support
- Google Cloud Storage credentials
- Access to backend API

### Setup

1. **Install Dependencies**

```bash
cd Backend/local_client
pip install -r requirements.txt
```

2. **Configure Environment**

```bash
cp .env.example .env
# Edit .env with your configuration
```

Required configuration:
- `BACKEND_API_URL`: Backend API URL
- `CLIENT_TOKEN`: Authentication token (get from Django admin)
- `GCP_CREDENTIALS_PATH`: Path to GCP service account JSON
- `GCP_BUCKET_NAME`: GCP bucket name
- `RECORDING_BASE_DIR`: Local recording directory

3. **Create Recording Directories**

```bash
mkdir -p recordings/recordings recordings/logs recordings/cache recordings/pending_uploads
```

4. **Verify Configuration**

```bash
python -c "from config import config; print('Config valid' if config.validate() else 'Config invalid')"
```

## Running the Client

### Development Mode

```bash
python main.py
```

### Production with Systemd

1. Copy service file:

```bash
sudo cp cctv-client.service /etc/systemd/system/
```

2. Edit service file with correct paths:

```bash
sudo nano /etc/systemd/system/cctv-client.service
```

3. Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable cctv-client
sudo systemctl start cctv-client
```

4. Check status:

```bash
sudo systemctl status cctv-client
sudo journalctl -u cctv-client -f
```

## Backend Setup

1. **Create Local Recording Client** in Django Admin:
   - Go to CCTV > Local Recording Clients
   - Add new client with name and save (token auto-generated)
   - Copy the client token to your `.env` file

2. **Assign Cameras**:
   - Edit the client
   - Select cameras to assign
   - Set camera `recording_mode` to "Local Client Recording"

3. **Create Schedules**:
   - Create schedules as usual in Django admin
   - They will automatically sync to the local client

## Directory Structure

```
recordings/
├── recordings/          # Recorded videos organized by camera/date
│   └── {camera_id}/
│       └── {YYYYMMDD}/
│           └── recording_*.avi
├── pending_uploads/     # Files waiting for upload retry
├── logs/               # Application logs
│   └── client.log
└── cache/              # Cached data for offline operation
    ├── schedules.json
    └── pending_updates.json
```

## Monitoring

### Local Status Endpoint

```bash
curl http://localhost:8001/status
```

### Backend Dashboard

View client status in Django admin under "Local Recording Clients"

### Logs

```bash
tail -f recordings/logs/client.log
```

## Troubleshooting

### Client Not Connecting

1. Check `BACKEND_API_URL` and `CLIENT_TOKEN` in `.env`
2. Verify network connectivity
3. Check backend logs for authentication errors

### Recording Failures

1. Check camera RTSP URLs are accessible
2. Verify OpenCV installation: `python -c "import cv2; print(cv2.__version__)"`
3. Check disk space: `df -h`
4. Review logs for specific errors

### Upload Failures

1. Verify GCP credentials path
2. Check GCP bucket permissions
3. Check network connectivity to GCP
4. Files will be moved to `pending_uploads/` for retry

## Configuration Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKEND_API_URL` | Backend API base URL | - |
| `CLIENT_TOKEN` | Authentication token | - |
| `CLIENT_ID` | Client UUID (optional) | - |
| `GCP_CREDENTIALS_PATH` | Path to GCP JSON credentials | - |
| `GCP_BUCKET_NAME` | GCP storage bucket | - |
| `GCP_PROJECT_ID` | GCP project ID | - |
| `RECORDING_BASE_DIR` | Base directory for recordings | `./recordings` |
| `CLEANUP_AFTER_UPLOAD` | Delete local files after upload | `true` |
| `KEEP_LOCAL_DAYS` | Days to keep local recordings | `1` |
| `SYNC_INTERVAL_SECONDS` | Schedule sync interval | `30` |
| `HEARTBEAT_INTERVAL_SECONDS` | Heartbeat interval | `60` |
| `MAX_RETRY_ATTEMPTS` | Max API retry attempts | `5` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `MAX_CONCURRENT_RECORDINGS` | Max simultaneous recordings | `4` |

## API Endpoints

The local client exposes these endpoints:

- `GET /health` - Health check
- `GET /status` - Current recording status and system info
- `POST /manual-record` - Trigger manual recording
- `GET /schedules` - View synced schedules

## Support

For issues or questions, contact the system administrator.

