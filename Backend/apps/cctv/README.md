# CCTV Management System

A comprehensive Django app for managing IP CCTV cameras with RTSP streaming, recording capabilities, and scheduling features.

## Features

### 🎥 Camera Management
- Add IP cameras with RTSP URL support
- Test camera connections
- Monitor camera status (online/offline)
- Camera access control and permissions

### 📹 Live Streaming
- Real-time RTSP stream viewing
- Multiple quality levels (main/sub streams)
- Session tracking and management
- Browser-compatible MJPEG streaming

### 🔴 Recording Management
- Manual start/stop recording
- Scheduled recordings (one-time, daily, weekly, continuous)
- Automatic file management
- Recording quality settings
- Storage optimization with automatic cleanup

### ⏰ Scheduling System
- Flexible scheduling options:
  - **One-time**: Record at specific date/time
  - **Daily**: Record at same time every day
  - **Weekly**: Record on specific days of the week
  - **Continuous**: 24/7 recording in chunks
- Background job processing
- Schedule management and monitoring

### 🔐 Access Control
- User-based camera permissions
- Role-based access (view, control, admin)
- Time-restricted access
- Granular permissions (record, schedule, download)

## Installation

1. **Dependencies**: The following packages are required and included in `requirements.txt`:
   ```
   opencv-python==4.10.0.84
   opencv-contrib-python==4.10.0.84
   ffmpeg-python==0.2.0
   Pillow==10.4.0
   numpy==1.26.4
   imageio==2.36.0
   APScheduler==3.10.4
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Add to Django settings**:
   ```python
   INSTALLED_APPS = [
       # ... other apps
       'apps.cctv',
   ]
   ```

4. **Run migrations**:
   ```bash
   python manage.py migrate cctv
   ```

5. **Setup CCTV system**:
   ```bash
   python manage.py setup_cctv --create-dirs --init-scheduler
   ```

## API Endpoints

### Cameras
- `GET /v0/api/cctv/cameras/` - List all cameras
- `POST /v0/api/cctv/cameras/` - Create new camera
- `GET /v0/api/cctv/cameras/{id}/` - Get camera details
- `PUT /v0/api/cctv/cameras/{id}/` - Update camera
- `DELETE /v0/api/cctv/cameras/{id}/` - Delete camera
- `POST /v0/api/cctv/cameras/{id}/test_connection/` - Test camera connection
- `GET /v0/api/cctv/cameras/{id}/stream/` - Live video stream
- `POST /v0/api/cctv/cameras/{id}/start_recording/` - Start recording
- `POST /v0/api/cctv/cameras/{id}/stop_recording/` - Stop recording
- `GET /v0/api/cctv/cameras/{id}/recording_status/` - Get recording status

### Recordings
- `GET /v0/api/cctv/recordings/` - List all recordings
- `GET /v0/api/cctv/recordings/{id}/` - Get recording details
- `GET /v0/api/cctv/recordings/{id}/download/` - Download recording

### Schedules
- `GET /v0/api/cctv/schedules/` - List all schedules
- `POST /v0/api/cctv/schedules/` - Create new schedule
- `GET /v0/api/cctv/schedules/{id}/` - Get schedule details
- `PUT /v0/api/cctv/schedules/{id}/` - Update schedule
- `DELETE /v0/api/cctv/schedules/{id}/` - Delete schedule
- `POST /v0/api/cctv/schedules/{id}/activate/` - Activate schedule
- `POST /v0/api/cctv/schedules/{id}/deactivate/` - Deactivate schedule

### Live Streams
- `GET /v0/api/cctv/streams/` - List all stream sessions
- `GET /v0/api/cctv/streams/active/` - List active streams

## Models

### Camera
- Basic information (name, description, location)
- Connection details (IP, port, credentials, RTSP URLs)
- Recording settings (auto-record, quality, retention)
- Status tracking (online/offline, last seen)

### RecordingSchedule
- Schedule configuration (type, timing, days)
- Camera association
- Active/inactive status

### Recording
- Recording metadata (name, duration, file size)
- File path and access URL
- Status tracking (recording, completed, failed)
- Quality information (resolution, frame rate)

### CameraAccess
- User permissions for cameras
- Access levels (view, control, admin)
- Time restrictions
- Granular permissions

### LiveStream
- Active streaming sessions
- User and camera tracking
- Session duration and client info

## Usage Examples

### Adding a Camera

```python
# Via API
POST /v0/api/cctv/cameras/
{
    "name": "Front Door Camera",
    "description": "Main entrance monitoring",
    "ip_address": "192.168.1.100",
    "port": 554,
    "username": "admin",
    "password": "password123",
    "rtsp_url": "rtsp://admin:password123@192.168.1.100:554/stream1",
    "location": "Front Door",
    "auto_record": true,
    "record_quality": "high"
}
```

### Creating a Schedule

```python
# Daily recording from 9 AM to 5 PM
POST /v0/api/cctv/schedules/
{
    "name": "Business Hours Recording",
    "camera": "camera-uuid-here",
    "schedule_type": "daily",
    "start_time": "09:00:00",
    "end_time": "17:00:00",
    "is_active": true
}

# Weekly recording on weekdays
POST /v0/api/cctv/schedules/
{
    "name": "Weekday Security",
    "camera": "camera-uuid-here", 
    "schedule_type": "weekly",
    "start_time": "18:00:00",
    "end_time": "06:00:00",
    "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday"],
    "is_active": true
}
```

### Streaming Video

```html
<!-- Embed live stream in web page -->
<img src="/v0/api/cctv/cameras/{camera-id}/stream/?quality=main" 
     alt="Live Camera Feed" 
     style="width: 100%; height: auto;">
```

### Manual Recording Control

```python
# Start recording
POST /v0/api/cctv/cameras/{camera-id}/start_recording/
{
    "duration_minutes": 60,
    "recording_name": "Manual Security Check"
}

# Stop recording
POST /v0/api/cctv/cameras/{camera-id}/stop_recording/
```

## Directory Structure

```
media/
├── recordings/          # Camera recordings organized by camera ID
│   └── {camera-id}/
│       └── *.mp4
├── thumbnails/          # Camera snapshots
└── logs/               # System logs
```

## Security Considerations

1. **Authentication**: All endpoints require user authentication
2. **Access Control**: Fine-grained permissions per camera
3. **HTTPS**: Use HTTPS in production for secure streaming
4. **Network Security**: Ensure camera networks are properly segmented
5. **Storage**: Implement secure storage for recordings

## Performance Tips

1. **Quality Settings**: Use appropriate quality levels for bandwidth
2. **Storage Management**: Configure automatic cleanup policies
3. **Concurrent Streams**: Monitor server resources for multiple streams
4. **Network**: Ensure adequate bandwidth for streaming and recording

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Install missing dependencies
   ```bash
   pip install opencv-python APScheduler
   ```

2. **Camera Connection Failed**: 
   - Check IP address and credentials
   - Verify RTSP URL format
   - Test network connectivity

3. **Recording Failed**:
   - Check media directory permissions
   - Verify disk space
   - Check camera stream stability

4. **Scheduler Not Working**:
   - Ensure APScheduler is installed
   - Check Django timezone settings
   - Verify schedule configuration

### Logs

Check Django logs and CCTV-specific logs in `media/logs/` for debugging.

## Future Enhancements

- [ ] Motion detection and alerts
- [ ] Cloud storage integration
- [ ] Mobile app support
- [ ] Advanced analytics
- [ ] Multi-camera views
- [ ] Export/backup functionality
