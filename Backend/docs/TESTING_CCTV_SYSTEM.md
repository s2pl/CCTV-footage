# CCTV Streaming System Testing Guide

This guide will help you test the CCTV streaming system to ensure all functionality is working correctly.

## 🚀 Quick Start Testing

### 1. Start the Django Server
```bash
cd Backend
python manage.py runserver 8000
```

### 2. Test the System

#### Option A: Python Script (Recommended)
```bash
cd Backend
python test_cctv_system.py
```

#### Option B: PowerShell Script (Windows)
```powershell
cd Backend
.\test_cctv_powershell.ps1
```

#### Option C: Manual Testing with curl
```bash
# 1. Get JWT token
curl -X POST "http://localhost:8000/v0/api/token/" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@admin.com", "password": "@Rishi21"}'

# 2. Use the token to test endpoints
TOKEN="YOUR_JWT_TOKEN_HERE"

# Test multi-stream dashboard
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/v0/api/cctv/cameras/multi-stream/"

# Test stream activation
curl -X POST -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/v0/api/cctv/cameras/CAMERA_ID/activate_stream/?quality=main"
```

## 🧪 What the Tests Cover

### Authentication Tests
- ✅ JWT token generation
- ✅ Token validation
- ✅ API access with authentication

### API Endpoint Tests
- ✅ Multi-stream dashboard (`/cctv/cameras/multi-stream/`)
- ✅ OpenAPI documentation (`/openapi.json`)
- ✅ Stream health checks (`/cameras/{id}/stream_health/`)
- ✅ Connection testing (`/cameras/{id}/test_connection/`)
- ✅ Stream activation (`/cameras/{id}/activate_stream/`)
- ✅ Thumbnail generation (`/cameras/{id}/stream/thumbnail/`)
- ✅ Snapshot capture (`/cameras/{id}/stream/snapshot/`)
- ✅ Stream deactivation (`/cameras/{id}/deactivate_stream/`)

### Streaming Tests
- ✅ MJPEG streaming
- ✅ HTTP-based streaming
- ✅ Quality selection (main/sub)
- ✅ Frame rate control
- ✅ Error handling

## 🌐 Web Interface Testing

### 1. Multi-Stream Dashboard
Visit: `http://localhost:8000/cctv/dashboard/`

**Features to test:**
- Camera status indicators
- Stream controls (start/stop)
- Quality selection
- MJPEG vs HTTP streaming toggle
- Snapshot capture
- Connection testing

### 2. HTTP Streaming Dashboard
Visit: `http://localhost:8000/cctv/http-streaming/`

**Features to test:**
- HTTP-based frame polling
- Adjustable FPS controls
- Real-time FPS monitoring
- Stream quality selection

## 📱 API Testing with Postman/Insomnia

### Import this collection:
```json
{
  "info": {
    "name": "CCTV Streaming System",
    "description": "Test collection for CCTV streaming API"
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000/v0/api"
    },
    {
      "key": "auth_token",
      "value": ""
    }
  ],
  "item": [
    {
      "name": "Get JWT Token",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"email\": \"admin@admin.com\",\n  \"password\": \"@Rishi21\"\n}"
        },
        "url": "{{base_url}}/token/"
      }
    },
    {
      "name": "Multi-Stream Dashboard",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{auth_token}}"
          }
        ],
        "url": "{{base_url}}/cctv/cameras/multi-stream/"
      }
    },
    {
      "name": "Activate Stream",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{auth_token}}"
          }
        ],
        "url": "{{base_url}}/cctv/cameras/CAMERA_ID/activate_stream/?quality=main"
      }
    }
  ]
}
```

## 🔍 Manual Testing Steps

### 1. Test Authentication
```bash
# Test login
curl -X POST "http://localhost:8000/v0/api/token/" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@admin.com", "password": "@Rishi21"}'
```

**Expected Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 2. Test Dashboard
```bash
# Get camera list
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/v0/api/cctv/cameras/multi-stream/"
```

**Expected Response:**
```json
{
  "total_cameras": 1,
  "online_cameras": 1,
  "streaming_cameras": 0,
  "cameras": [
    {
      "camera_id": "uuid-here",
      "camera_name": "Main",
      "status": "active",
      "is_online": true,
      "is_streaming": false
    }
  ]
}
```

### 3. Test Stream Activation
```bash
# Start a stream
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/v0/api/cctv/cameras/CAMERA_ID/activate_stream/?quality=main"
```

### 4. Test Live Stream
```bash
# View MJPEG stream
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/v0/api/cctv/cameras/CAMERA_ID/stream/?quality=main"
```

### 5. Test Thumbnail
```bash
# Get thumbnail
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/v0/api/cctv/cameras/CAMERA_ID/stream/thumbnail/?quality=main"
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Authentication Failed
- Check if the server is running
- Verify credentials: `admin@admin.com` / `@Rishi21`
- Check Django admin for user existence

#### 2. Camera Not Found
- Ensure cameras are added to the database
- Check camera status in Django admin
- Verify RTSP URLs are accessible

#### 3. Stream Not Working
- Check OpenCV installation
- Verify camera network connectivity
- Check firewall settings
- Review Django logs for errors

#### 4. CORS Issues
- Ensure Django CORS settings are configured
- Check if requests are coming from allowed origins

### Debug Commands

#### Check Django Logs
```bash
cd Backend
python manage.py runserver 8000 --verbosity 2
```

#### Check Database
```bash
cd Backend
python manage.py shell
```
```python
from apps.cctv.models import Camera
Camera.objects.all().values('name', 'status', 'is_active')
```

#### Test OpenCV
```bash
cd Backend
python test_streaming_simple.py
```

## 📊 Performance Testing

### Load Testing
```bash
# Install Apache Bench
# Test concurrent requests
ab -n 100 -c 10 -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/v0/api/cctv/cameras/multi-stream/"
```

### Memory Usage
```bash
# Monitor Django process
ps aux | grep "python manage.py runserver"
```

## 🎯 Success Criteria

A successful test run should show:
- ✅ All authentication tests pass
- ✅ Dashboard loads with camera data
- ✅ Streams can be activated/deactivated
- ✅ Live video feeds are visible
- ✅ Snapshots and thumbnails are generated
- ✅ API documentation is accessible
- ✅ Error handling works correctly

## 📝 Test Report Template

```markdown
# CCTV System Test Report

**Date:** [Date]
**Tester:** [Name]
**Server:** localhost:8000
**User:** admin@admin.com

## Test Results
- [ ] Authentication
- [ ] Dashboard Loading
- [ ] Stream Activation
- [ ] Live Streaming
- [ ] Snapshot Capture
- [ ] Thumbnail Generation
- [ ] Error Handling

## Issues Found
[List any issues encountered]

## Recommendations
[Suggestions for improvement]
```

## 🚀 Next Steps

After successful testing:
1. Deploy to production environment
2. Set up monitoring and logging
3. Configure backup and recovery
4. Train users on the system
5. Document operational procedures

---

**Need Help?** Check the Django logs and ensure all dependencies are installed correctly.
