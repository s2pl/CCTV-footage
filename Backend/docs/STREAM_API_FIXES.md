# CCTV Live Stream API Fixes

## Summary
Fixed the live stream API endpoint `/v0/api/cctv/cameras/{camera_id}/stream/` to work properly without authentication and provide real-time MJPEG video streaming.

## Changes Made

### 1. API Endpoint Fixes (`apps/cctv/api.py`)

#### Removed Authentication Requirement
- **Before**: `@router.get("/cameras/{camera_id}/stream/", auth=cctv_jwt_auth, ...)`
- **After**: `@router.get("/cameras/{camera_id}/stream/", ...)`
- **Impact**: Stream endpoint is now accessible without authentication as intended

#### Enhanced Error Handling
- Added proper camera status validation
- Added RTSP URL validation
- Added quality parameter validation with fallback
- Improved error messages with specific HTTP status codes

#### CORS Support
- Added comprehensive CORS headers for cross-origin requests
- Added OPTIONS request handling for preflight requests
- Headers include:
  - `Access-Control-Allow-Origin: *`
  - `Access-Control-Allow-Methods: GET, OPTIONS`
  - `Access-Control-Allow-Headers: Content-Type`
  - `Access-Control-Max-Age: 86400`

#### Response Headers
- Added custom headers for debugging:
  - `X-Camera-Name`: Camera name
  - `X-Stream-Quality`: Stream quality being served
- Proper cache control headers to prevent caching

### 2. Streaming Improvements (`apps/cctv/streaming.py`)

#### Enhanced Frame Generation
- Improved error handling in `generate_frames()` function
- Added frame rate control (25 FPS target)
- Better JPEG encoding with quality settings (85% quality)
- Added stream health monitoring
- Improved cleanup handling

#### Stream Health Monitoring
- Added `is_stream_active()` method to RTSPStreamManager
- Periodic stream health checks every 100 frames
- Automatic stream recovery on failures
- Better error reporting and logging

### 3. Test Files Created

#### HTML Test Interface (`test_stream.html`)
- Complete web interface for testing streams
- UUID validation
- Stream quality selection
- Real-time stream monitoring
- Connection testing functionality
- Responsive design with error handling

#### Python Test Script (`test_stream_endpoint.py`)
- Command-line testing tool
- Validates UUID format
- Tests stream info endpoint
- Tests stream endpoint accessibility
- Validates CORS headers
- Provides usage examples

## API Usage

### Endpoint
```
GET /v0/api/cctv/cameras/{camera_id}/stream/?quality=main
```

### Parameters
- `camera_id`: UUID of the camera
- `quality`: Stream quality (`main` or `sub`)

### Response
- **Content-Type**: `multipart/x-mixed-replace; boundary=frame`
- **Format**: MJPEG stream
- **Headers**: CORS-enabled with custom debugging headers

### Example Usage

#### Browser
```html
<img src="/v0/api/cctv/cameras/123e4567-e89b-12d3-a456-426614174000/stream/?quality=main" alt="Live Stream">
```

#### JavaScript
```javascript
const streamUrl = '/v0/api/cctv/cameras/123e4567-e89b-12d3-a456-426614174000/stream/?quality=main';
const img = document.getElementById('streamImage');
img.src = streamUrl;
```

#### Python
```python
import requests

stream_url = 'http://localhost:8000/v0/api/cctv/cameras/123e4567-e89b-12d3-a456-426614174000/stream/?quality=main'
response = requests.get(stream_url, stream=True)

for chunk in response.iter_content(chunk_size=1024):
    # Process MJPEG data
    pass
```

## Testing

### 1. Using the HTML Test Interface
1. Open `Backend/test_stream.html` in your browser
2. Enter a valid camera UUID
3. Select stream quality
4. Click "Start Stream"

### 2. Using the Python Test Script
```bash
cd Backend
python test_stream_endpoint.py <camera_id>
```

### 3. Direct Browser Testing
Navigate to:
```
http://localhost:8000/v0/api/cctv/cameras/{camera_id}/stream/?quality=main
```

## Error Handling

The API now provides specific error responses:

- **404**: Camera not found
- **400**: Invalid RTSP URL configuration
- **503**: Camera not active
- **500**: Internal streaming error

## Performance Optimizations

- Reduced buffer size for lower latency
- Optimized frame rate (25 FPS)
- Efficient JPEG encoding (85% quality)
- Automatic stream cleanup
- Connection pooling for multiple viewers

## Security Considerations

- No authentication required for public streaming
- CORS enabled for cross-origin access
- Input validation for camera IDs and quality parameters
- Proper error handling to prevent information leakage

## Browser Compatibility

The MJPEG stream format is supported by:
- Chrome/Chromium
- Firefox
- Safari
- Edge
- Most mobile browsers

## Next Steps

1. Test with actual camera hardware
2. Monitor performance under load
3. Consider adding stream authentication if needed
4. Implement stream recording features
5. Add stream analytics and monitoring
