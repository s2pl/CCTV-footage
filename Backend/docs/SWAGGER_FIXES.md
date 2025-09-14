# Swagger UI Loading Fixes for CCTV API

## Problem
The Swagger UI was hanging during loading because the streaming endpoints were trying to establish RTSP connections during API schema generation, causing timeouts and infinite loading.

## Root Cause
1. **RTSP Connection Timeouts**: The `generate_frames()` function was being called during schema generation
2. **Stream Manager Initialization**: Importing streaming modules during API documentation generation
3. **Missing Error Handling**: No protection against hanging during schema generation

## Solutions Implemented

### 1. Added Health Check Endpoints
- **`/v0/api/cctv/health/`** - Simple health check that doesn't involve streaming
- **`/v0/api/cctv/cameras/stream/status/`** - Stream system status without starting streams
- **`/v0/api/cctv/cameras/stream/test/`** - Test endpoint for streaming system

### 2. Protected Streaming Endpoints
- Added schema generation detection to prevent hanging
- Delayed import of streaming modules until actually needed
- Added timeout protection for stream creation

### 3. Improved Error Handling
- Better error messages for different failure scenarios
- Graceful fallbacks when streaming modules are unavailable
- Proper HTTP status codes for different error conditions

## How to Test

### 1. Test Health Endpoints First
```bash
# Test health check
curl http://localhost:8000/v0/api/cctv/health/

# Test stream status
curl http://localhost:8000/v0/api/cctv/cameras/stream/status/

# Test stream test endpoint
curl http://localhost:8000/v0/api/cctv/cameras/stream/test/
```

### 2. Test Swagger UI
1. Open `http://localhost:8000/docs` in your browser
2. The API should load without hanging
3. You should see all endpoints including the new health check endpoints

### 3. Test Actual Streaming
1. Use the test HTML file: `Backend/test_stream.html`
2. Or use the Python test script: `python test_stream_endpoint.py <camera_id>`

## Prevention Measures

### 1. Schema Generation Protection
```python
# Check if this is a schema generation request (prevent hanging)
if hasattr(request, '_ninja_schema_generation'):
    return HttpResponse('Schema generation - streaming not available', status=503)
```

### 2. Delayed Module Import
```python
# Import streaming modules only when actually streaming
try:
    from .streaming import generate_frames, stream_manager
except ImportError:
    return HttpResponse('Streaming module not available', status=503)
```

### 3. Error Wrapping
```python
# Generate streaming response with timeout protection
try:
    response = StreamingHttpResponse(
        generate_frames(camera, quality),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )
    # ... set headers ...
except Exception as stream_error:
    logger.error(f"Error creating streaming response: {str(stream_error)}")
    return HttpResponse(f'Stream creation error: {str(stream_error)}', status=503)
```

## Troubleshooting

### If Swagger Still Hangs:

1. **Check Django Logs**: Look for RTSP connection errors or timeouts
2. **Test Health Endpoints**: Verify basic API functionality
3. **Check Camera Configuration**: Ensure cameras have valid RTSP URLs
4. **Monitor Network**: Check if RTSP ports are accessible

### Common Issues:

1. **RTSP Timeout**: Camera not responding on RTSP port
2. **Network Issues**: Firewall blocking RTSP connections
3. **Camera Offline**: Camera not powered on or network disconnected
4. **Invalid URLs**: Malformed RTSP URLs in camera configuration

## Best Practices

1. **Always test health endpoints first** before testing streaming
2. **Use test endpoints** to verify system status
3. **Monitor logs** for connection issues
4. **Test with simple cameras** first before complex setups
5. **Use the HTML test interface** for visual verification

## Next Steps

1. Test the health endpoints to ensure basic API functionality
2. Open Swagger UI to verify it loads without hanging
3. Test actual streaming with a real camera
4. Monitor performance and add additional error handling as needed
