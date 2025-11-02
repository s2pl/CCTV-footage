# Local Client Integration Status

## ✅ Integration Complete

The local CCTV recording client is properly connected and integrated with the backend.

## API Endpoints

### Local Client Specific Endpoints

All endpoints are accessible at: `http://localhost:8000/v0/api/local-client/`

| Endpoint | Method | Description | Authentication |
|----------|--------|-------------|----------------|
| `/health` | GET | Health check | No |
| `/schedules` | GET | Fetch recording schedules | Bearer Token |
| `/cameras` | GET | Get assigned cameras | Bearer Token |
| `/recordings/register` | POST | Register new recording | Bearer Token |
| `/recordings/status` | POST | Update recording status | Bearer Token |
| `/heartbeat` | POST | Send client heartbeat | Bearer Token |

### Documentation

- **Local Client API Docs**: `http://localhost:8000/v0/api/local-client/docs`
- **CCTV API Docs**: `http://localhost:8000/v0/api/cctv/docs`
- **OpenAPI Spec**: `http://localhost:8000/v0/api/local-client/openapi.json`

## Architecture

```
┌─────────────────────┐
│  Local Client       │
│  (Python App)       │
│  - Recordings       │
│  - Scheduling       │
│  - GCP Upload       │
└──────────┬──────────┘
           │
           │ HTTP/REST API
           │ Bearer Token Auth
           │
┌──────────▼──────────┐
│  Backend Server     │
│  (Django)           │
│  - Client Auth      │
│  - Schedule Sync    │
│  - Status Tracking  │
└──────────┬──────────┘
           │
           │
┌──────────▼──────────┐
│  PostgreSQL DB      │
│  - Cameras          │
│  - Schedules        │
│  - Recordings       │
│  - Clients          │
└─────────────────────┘
```

## Features Implemented

### ✅ Backend Integration

- [x] Django Ninja API endpoints for local clients
- [x] Separate API namespace (`local_client_direct`)
- [x] Token-based authentication
- [x] Client registration and management
- [x] Schedule synchronization
- [x] Recording status tracking
- [x] Heartbeat monitoring
- [x] Health check endpoints

### ✅ Local Client Features

- [x] FastAPI application server
- [x] Backend API client with retry logic
- [x] Camera management
- [x] Schedule synchronization
- [x] Recording manager with OpenCV
- [x] Storage manager for local/GCP
- [x] Background task scheduling
- [x] Async operations with asyncio
- [x] Configuration management
- [x] Comprehensive logging

### ✅ Documentation

- [x] Setup guide (`SETUP_GUIDE.md`)
- [x] Authentication guide (`CLIENT_AUTH_README.md`)
- [x] Implementation summary (`IMPLEMENTATION_SUMMARY.md`)
- [x] API documentation (Swagger/OpenAPI)
- [x] Environment template (`env.template`)
- [x] Connection test script (`test_connection.py`)

## File Structure

```
Backend/
├── local_client/              # Local recording client
│   ├── main.py                # FastAPI application entry point
│   ├── config.py              # Configuration management
│   ├── api_client.py          # Backend API client
│   ├── camera_manager.py      # Camera operations
│   ├── recording_manager.py   # Recording control
│   ├── scheduler_manager.py   # Schedule management
│   ├── sync_service.py        # Backend sync service
│   ├── storage_manager.py     # File/GCP storage
│   ├── models.py              # Data models (Pydantic)
│   ├── utils/                 # Utilities
│   │   ├── logger.py
│   │   ├── retry.py
│   │   └── file_watcher.py
│   ├── recordings/            # Recording storage
│   │   ├── recordings/        # Video files
│   │   ├── logs/             # Client logs
│   │   ├── cache/            # Cached data
│   │   └── pending_uploads/  # Upload queue
│   ├── requirements.txt       # Python dependencies
│   ├── env.template          # Environment template
│   ├── test_connection.py    # Connection test
│   ├── SETUP_GUIDE.md        # Complete setup guide
│   ├── CLIENT_AUTH_README.md # Authentication guide
│   └── README.md             # Client documentation
│
└── apps/cctv/
    └── api.py                # Backend API (includes local-client endpoints)
```

## Setup Quick Start

### 1. Create Client in Django Admin

```
1. Navigate to: http://localhost:8000/admin/
2. Go to: CCTV → Local Recording Clients → Add
3. Enter name and description
4. Save and copy the CLIENT_TOKEN
```

### 2. Configure Local Client

```bash
cd Backend/local_client
cp env.template .env
# Edit .env and add your CLIENT_TOKEN
```

### 3. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Install packages
pip install -r requirements.txt
```

### 4. Test Connection

```bash
python test_connection.py
```

### 5. Run Client

```bash
python main.py
```

## API Authentication

The local client uses Bearer token authentication:

```python
headers = {
    'Authorization': f'Bearer {CLIENT_TOKEN}',
    'Content-Type': 'application/json'
}
```

The backend validates tokens against the `LocalRecordingClient` model:

```python
client = LocalRecordingClient.objects.get(client_token=token)
```

## Configuration Options

### Required Settings

- `BACKEND_API_URL`: Backend server URL
- `CLIENT_TOKEN`: Authentication token from Django Admin

### Optional Settings

- `GCP_CREDENTIALS_PATH`: GCP service account JSON
- `GCP_BUCKET_NAME`: GCP storage bucket
- `RECORDING_BASE_DIR`: Local recording directory
- `SYNC_INTERVAL_SECONDS`: Schedule sync interval (default: 30)
- `HEARTBEAT_INTERVAL_SECONDS`: Heartbeat interval (default: 60)
- `LOG_LEVEL`: Logging level (default: INFO)

See `env.template` for complete configuration options.

## Monitoring

### Backend Dashboard

View client status in Django Admin:
- Go to: CCTV → Local Recording Clients
- Check: Last heartbeat, active recordings, status

### Local Client Status

Access local client status:
```bash
curl http://localhost:8001/status
curl http://localhost:8001/health
```

### Logs

Client logs are stored in:
```
recordings/logs/client.log
```

## Troubleshooting

### Connection Issues

1. **Test backend connection**:
   ```bash
   curl http://localhost:8000/health/
   ```

2. **Test local-client API**:
   ```bash
   curl http://localhost:8000/v0/api/local-client/health
   ```

3. **Run connection test**:
   ```bash
   python test_connection.py
   ```

### Authentication Errors

- Verify `CLIENT_TOKEN` in `.env` matches Django Admin
- Check client is active in Django Admin
- Ensure no extra spaces in token

### No Cameras/Schedules

- Assign cameras to client in Django Admin
- Set camera `recording_mode` to "Local Client Recording"
- Create active schedules for assigned cameras

## Support Documentation

Comprehensive guides available:

1. **SETUP_GUIDE.md** - Complete setup walkthrough
2. **CLIENT_AUTH_README.md** - Authentication details
3. **IMPLEMENTATION_SUMMARY.md** - Technical implementation
4. **README.md** - Quick reference

## Testing Checklist

- [ ] Backend server running
- [ ] Local client API endpoints accessible
- [ ] Client created in Django Admin
- [ ] CLIENT_TOKEN configured in .env
- [ ] Dependencies installed
- [ ] Connection test passes
- [ ] Cameras assigned to client
- [ ] Schedules created and active
- [ ] Local client starts successfully
- [ ] Recordings working
- [ ] GCP uploads working (if configured)

## Version Information

- **Backend API Version**: 4.0.0 (CCTV API)
- **Local Client API Version**: 5.0.0
- **Django Ninja**: 1.4.5
- **FastAPI**: 0.120.1+
- **Python**: 3.8+

## Security Notes

1. **Keep CLIENT_TOKEN secure** - treat like a password
2. **Use HTTPS in production** - don't expose tokens over HTTP
3. **Rotate tokens if compromised** - create new client in Django Admin
4. **Limit network access** - firewall rules for API access
5. **Monitor client activity** - check last heartbeat regularly

---

**Status**: ✅ Fully Integrated and Operational  
**Last Verified**: 2025-10-28  
**Maintainer**: System Administrator

