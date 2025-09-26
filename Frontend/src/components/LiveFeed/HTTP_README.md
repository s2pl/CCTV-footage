# HTTP Live Feed

This component provides direct HTTP streaming for cameras that support HTTP/MJPEG streaming without requiring an RTSP server.

## Features

- **Direct HTTP Streaming**: Connects directly to cameras via HTTP on ports 80 or 443
- **Custom URL Support**: Enter direct camera URLs like `http://192.168.1.9/index.html#preview.html`
- **Multiple Stream Paths**: Supports common HTTP stream paths like `/video`, `/mjpeg`, `/stream`, etc.
- **Port Selection**: Choose between HTTP (port 80) or HTTPS (port 443)
- **Grid and Single View**: Switch between grid view for multiple cameras or single camera focus
- **Real-time Testing**: Test HTTP connections and stream paths
- **Error Handling**: Clear error messages and retry functionality

## Supported Camera Types

This feature works with cameras that support:
- HTTP/MJPEG streaming
- Direct HTTP video feeds
- IP cameras with built-in web servers
- Cameras accessible on the same network

## Common Stream Paths

- `/video` - Generic video stream
- `/mjpeg` - MJPEG stream
- `/stream` - Common stream path
- `/live` - Live stream
- `/cam` - Camera stream
- `/snapshot` - Static image (for testing)

## Usage

### Using Camera List
1. Navigate to "HTTP Live Feed" in the sidebar
2. Select a camera from the dropdown
3. Choose the appropriate port (80 for HTTP, 443 for HTTPS)
4. Select the correct stream path for your camera
5. The stream will load automatically

### Using Custom URL
1. Navigate to "HTTP Live Feed" in the sidebar
2. Check the "Custom URL" checkbox
3. Enter your camera's direct URL (e.g., `http://192.168.1.9/index.html#preview.html`)
4. The stream will load directly from your custom URL

## Benefits over RTSP

- **No Server Required**: Direct connection to cameras
- **Lower Latency**: No intermediate RTSP server processing
- **Simpler Setup**: Works with cameras on the same network
- **Better Compatibility**: Works with cameras that don't support RTSP

## Troubleshooting

### For Camera List Mode
If streams don't load:
1. Check if the camera supports HTTP streaming
2. Verify the camera is accessible on the network
3. Try different stream paths
4. Check if the camera requires authentication
5. Ensure the correct port is selected

### For Custom URL Mode
If streams don't load:
1. Check if the URL is accessible in a browser
2. Verify the camera supports HTTP streaming
3. Check network connectivity
4. Ensure the URL is complete and correct
5. Try accessing the URL directly to test

## Technical Details

- Uses standard HTML `<img>` tags for streaming
- Supports MJPEG and other HTTP-based video formats
- Automatic cache busting with timestamp parameters
- Cross-origin request handling
- Error recovery and retry mechanisms
