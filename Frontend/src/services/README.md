# Services Directory

This directory contains all the API service modules for the CCTV management system. The services have been modularized for better maintainability and organization.

## Service Structure

### Core Services

- **`types.ts`** - All TypeScript interfaces and types used across services
- **`index.ts`** - Main export file that provides both individual services and a combined legacy interface

### Individual Services

#### 1. **`cameraService.ts`** - Camera Management
Handles all camera-related operations:
- List, create, read, update, delete cameras
- Test camera connections
- Camera status management

**Usage:**
```typescript
import { cameraService } from './services';
// or
import cameraService from './services/cameraService';

const cameras = await cameraService.getCameras();
const camera = await cameraService.getCamera(cameraId);
```

#### 2. **`recordingService.ts`** - Recording Operations
Manages all recording-related functionality:
- Start/stop recordings
- Get recording status and overview
- Test recordings
- Download and stream recordings
- Recording statistics

**Usage:**
```typescript
import { recordingService } from './services';

await recordingService.startRecording(cameraId, { duration_minutes: 30 });
const status = await recordingService.getRecordingStatus(cameraId);
```

#### 3. **`streamingService.ts` - Live Streaming**
Handles live video streaming operations:
- Live stream activation/deactivation
- Stream status and health monitoring
- Camera snapshots and thumbnails
- Stream information and capabilities

**Usage:**
```typescript
import { streamingService } from './services';

const stream = await streamingService.activateLiveStream(cameraId, 'main');
const health = await streamingService.getStreamHealth(cameraId);
```

#### 4. **`scheduleService.ts` - Recording Schedules**
Manages recording schedules:
- Create, read, update, delete schedules
- Schedule activation/deactivation
- Schedule status monitoring

**Usage:**
```typescript
import { scheduleService } from './services';

const schedules = await scheduleService.getSchedules();
await scheduleService.activateSchedule(scheduleId);
```

#### 5. **`accessControlService.ts` - Access Permissions**
Handles camera access control:
- User permissions for cameras
- Access level management (view, control, record)
- Access control CRUD operations

**Usage:**
```typescript
import { accessControlService } from './services';

const access = await accessControlService.getCameraAccess();
await accessControlService.createCameraAccess(accessData);
```

#### 6. **`systemService.ts` - System Operations**
Manages system-level operations:
- Health checks
- System overview and status
- Connection testing
- Overall system monitoring

**Usage:**
```typescript
import { systemService } from './services';

const health = await systemService.getHealth();
const overview = await systemService.getSystemOverview();
```

## Migration Guide

### From Old cctvService to New Modular Services

The original `cctvService` has been split into logical modules. For backward compatibility, you can still use the combined interface:

```typescript
// Old way (still works)
import cctvService from './services';
const cameras = await cctvService.getCameras();

// New way (recommended)
import { cameraService } from './services';
const cameras = await cameraService.getCameras();
```

### Benefits of New Structure

1. **Better Organization**: Each service has a clear, focused responsibility
2. **Easier Maintenance**: Changes to one area don't affect others
3. **Better Tree Shaking**: Only import what you need
4. **Clearer Dependencies**: Each service imports only what it needs
5. **Easier Testing**: Test individual services in isolation
6. **Better Type Safety**: Types are centralized and reusable

### Import Patterns

#### Import Individual Services
```typescript
import { cameraService, recordingService } from './services';
```

#### Import Specific Types
```typescript
import { Camera, Recording, StreamInfo } from './services';
```

#### Import Everything (Legacy)
```typescript
import cctvService from './services';
```

## Error Handling

All services use centralized error handling through `errorHandler.ts`. Errors are:
- Logged with context
- Transformed into user-friendly messages
- Categorized by type (network, auth, validation, server)

## API URLs

All services use centralized URL management through `urls.ts`. This ensures:
- Consistent endpoint structure
- Easy environment switching
- Centralized URL maintenance

## Testing

Each service can be tested independently. Mock the `api` module to test service logic without making actual HTTP requests.

## Future Enhancements

- Add service-level caching
- Implement retry logic for failed requests
- Add request/response interceptors
- Implement service-level metrics and monitoring
