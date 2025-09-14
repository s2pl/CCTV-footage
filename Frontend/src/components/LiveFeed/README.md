# LiveFeed Component

The LiveFeed component has been updated to properly integrate with the `cctvService` for live video streaming from CCTV cameras.

## Features

### Live Video Streaming
- **Real-time video feeds**: Displays live video streams from online cameras
- **Quality selection**: Switch between main and sub stream qualities
- **Auto-streaming**: Automatically starts streams for online cameras
- **Stream health monitoring**: Tracks stream status and errors
- **Camera recovery**: Automatic and manual recovery for offline cameras

### Camera Management
- **Grid layouts**: 2x2, 3x3, and 4x4 grid views
- **Single camera view**: Focus on one camera in full detail
- **Fullscreen mode**: Immersive viewing experience
- **Camera status indicators**: Online, offline, maintenance status

### Recording Controls
- **Start/Stop recording**: Control recording for individual cameras
- **Recording status**: Visual indicators for active recordings
- **Duration control**: Set recording duration in minutes

### Stream Controls
- **Mute/Unmute**: Audio control for individual streams
- **Stream restart**: Restart failed or stalled streams
- **Quality switching**: Change stream quality on the fly
- **Error handling**: Automatic retry and error display
- **Camera recovery**: Bring offline cameras back online automatically or manually

## API Integration

The component uses the following `cctvService` methods:

### Stream Management
```typescript
// Get camera stream information
await cctvService.getCameraStreamInfo(cameraId)

// Get live stream blob
await cctvService.getLiveStream(cameraId, quality)

// Get stream info
await cctvService.getStreamInfo(cameraId)
```

### Camera Management
```typescript
// Get all cameras
await cctvService.getCameras()

// Get single camera
await cctvService.getCamera(cameraId)

// Test camera connection
await cctvService.testCameraConnection(cameraId)
```

### Recording Control
```typescript
// Start recording
await cctvService.startRecording(cameraId, {
  duration_minutes: 60,
  recording_name: 'Custom Recording',
  quality: 'main'
})

// Stop recording
await cctvService.stopRecording(cameraId)

// Get recording status
await cctvService.getRecordingStatus(cameraId)
```

## Component Structure

### State Management
- `streamingCameras`: Set of cameras currently streaming
- `streamErrors`: Map of camera IDs to error messages
- `streamQualities`: Map of camera IDs to current quality settings
- `videoRefs`: Ref map for video elements

### Key Functions
- `startStream(cameraId, quality)`: Initialize video stream
- `stopStream(cameraId)`: Stop and cleanup stream
- `handleRestartStream(cameraId)`: Restart failed stream
- `changeStreamQuality(cameraId, quality)`: Switch stream quality

### Video Element Setup
```typescript
<video
  ref={(el) => {
    if (el) videoRefs.current.set(camera.id, el);
  }}
  className="w-full h-full object-cover"
  muted={isMuted}
  playsInline
  autoPlay
  loop
/>
```

## Usage

### Basic Implementation
```typescript
import LiveFeedView from './components/LiveFeed/LiveFeedView';

function App() {
  return (
    <div className="h-screen">
      <LiveFeedView />
    </div>
  );
}
```

### With Custom Styling
```typescript
<div className="h-screen bg-gray-100">
  <LiveFeedView />
</div>
```

## Error Handling

The component includes comprehensive error handling:

- **Stream errors**: Displayed with retry buttons
- **Connection timeouts**: 10-second timeout with automatic cleanup
- **API failures**: Graceful fallback to error states
- **Network issues**: Automatic retry mechanisms

## Performance Considerations

- **Auto-streaming**: Only starts streams for online cameras
- **Cleanup**: Properly disposes of video elements and streams
- **Memory management**: Efficient handling of multiple video streams
- **Grid optimization**: Limits displayed cameras based on grid size

## Testing

Use the included `StreamTest` component to verify API connectivity:

```typescript
import StreamTest from './components/LiveFeed/StreamTest';

// Test stream APIs
<StreamTest />
```

## Troubleshooting

### Common Issues

1. **Streams not starting**
   - Check camera status (must be 'online')
   - Verify API endpoints are accessible
   - Check browser console for errors

2. **Video not playing**
   - Ensure camera supports the requested quality
   - Check network connectivity
   - Verify video codec support

3. **Recording failures**
   - Check camera permissions
   - Verify recording settings
   - Check backend recording service

### Debug Information

Enable console logging to see detailed stream information:
- Stream URLs and quality settings
- Connection status and errors
- API response data

## Dependencies

- `cctvService`: Main service for CCTV operations
- `useCCTV`: Hook for camera data and operations
- `lucide-react`: Icon components
- `tailwindcss`: Styling framework

## Future Enhancements

- **Stream analytics**: View count, bandwidth usage
- **Advanced controls**: PTZ camera control
- **Recording playback**: View recorded footage
- **Multi-view layouts**: Custom grid arrangements
- **Stream recording**: Save live streams locally
