import api from './api';
import { handleApiError, logError } from './errorHandler';
import { 
  StreamInfo, 
  StreamActivationResponse, 
  StreamStatusResponse, 
  StreamHealthResponse, 
  SnapshotResponse, 
  LiveStream, 
  ActiveStreamsResponse,
  TestConnectionResponse,
  MultiStreamDashboardResponse,
  StreamSystemStatusResponse,
  SetCameraOnlineResponse,
  ApiResponse
} from './types';

class StreamingService {
  // Get Live Video Stream URL (No Auth Required)
  // Endpoint: GET /cctv/cameras/{camera_id}/stream/?quality={quality}
  getLiveStreamUrl(cameraId: string, quality: string = 'main'): string {
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/v0/api';
    return `${baseURL}/cctv/cameras/${cameraId}/stream/?quality=${quality}`;
  }

  // Get Live Video Stream as Blob (for download/processing)
  // Endpoint: GET /cctv/cameras/{camera_id}/stream/?quality={quality}
  async getLiveStreamBlob(cameraId: string, quality: string = 'main'): Promise<Blob> {
    try {
      const response = await api.get(`/cctv/cameras/${cameraId}/stream/`, {
        params: { quality },
        responseType: 'blob',
      });
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'StreamingService.getLiveStreamBlob');
      throw serviceError;
    }
  }

  // Get Stream Information
  // Endpoint: GET /cctv/cameras/{camera_id}/stream/info/
  async getCameraStreamInfo(cameraId: string): Promise<StreamInfo> {
    try {
      const response = await api.get(`/cctv/cameras/${cameraId}/stream/info/`);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'StreamingService.getCameraStreamInfo');
      throw serviceError;
    }
  }

  // Get Camera Thumbnail
  // Endpoint: GET /cctv/cameras/{camera_id}/stream/thumbnail/?quality={quality}
  async getCameraThumbnail(cameraId: string, quality: string = 'main'): Promise<Blob> {
    try {
      const response = await api.get(`/cctv/cameras/${cameraId}/stream/thumbnail/`, {
        params: { quality },
        responseType: 'blob',
      });
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'StreamingService.getCameraThumbnail');
      throw serviceError;
    }
  }

  // Activate Live Stream
  // Endpoint: POST /cctv/cameras/{camera_id}/activate_stream/?quality={quality}
  async activateStream(cameraId: string, quality: string = 'main'): Promise<StreamActivationResponse> {
    try {
      const response = await api.post(`/cctv/cameras/${cameraId}/activate_stream/`, null, {
        params: { quality }
      });
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'StreamingService.activateStream');
      throw serviceError;
    }
  }

  // Deactivate Live Stream
  // Endpoint: POST /cctv/cameras/{camera_id}/deactivate_stream/
  async deactivateStream(cameraId: string): Promise<StreamActivationResponse> {
    try {
      const response = await api.post(`/cctv/cameras/${cameraId}/deactivate_stream/`);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'StreamingService.deactivateStream');
      throw serviceError;
    }
  }

  // Get Stream Status
  // Endpoint: GET /cctv/cameras/{camera_id}/stream_status/
  async getStreamStatus(cameraId: string): Promise<StreamStatusResponse> {
    try {
      const response = await api.get(`/cctv/cameras/${cameraId}/stream_status/`);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'StreamingService.getStreamStatus');
      throw serviceError;
    }
  }

  // Get Stream Health
  // Endpoint: GET /cctv/cameras/{camera_id}/stream_health/?quality={quality}
  async getStreamHealth(cameraId: string, quality: string = 'main'): Promise<StreamHealthResponse> {
    try {
      const response = await api.get(`/cctv/cameras/${cameraId}/stream_health/`, {
        params: { quality }
      });
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'StreamingService.getStreamHealth');
      throw serviceError;
    }
  }

  // Capture Camera Snapshot
  // Endpoint: GET /cctv/cameras/{camera_id}/stream/snapshot/?quality={quality}
  async captureSnapshot(cameraId: string, quality: string = 'main'): Promise<SnapshotResponse> {
    try {
      const response = await api.get(`/cctv/cameras/${cameraId}/stream/snapshot/`, {
        params: { quality }
      });
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'StreamingService.captureSnapshot');
      throw serviceError;
    }
  }

  // List Stream Sessions
  // Endpoint: GET /cctv/streams/
  async getAllStreams(): Promise<LiveStream[]> {
    try {
      const response = await api.get('/cctv/streams/');
      return response.data.streams || response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'StreamingService.getAllStreams');
      throw serviceError;
    }
  }

  // Get Active Streams
  // Endpoint: GET /cctv/streams/active/
  async getActiveStreams(): Promise<ActiveStreamsResponse> {
    try {
      const response = await api.get('/cctv/streams/active/');
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'StreamingService.getActiveStreams');
      throw serviceError;
    }
  }

  // Test Camera Connection
  // Endpoint: POST /cctv/cameras/{camera_id}/test_connection/
  async testCameraConnection(cameraId: string): Promise<TestConnectionResponse> {
    try {
      const response = await api.post(`/cctv/cameras/${cameraId}/test_connection/`);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'StreamingService.testCameraConnection');
      throw serviceError;
    }
  }

  // Recover Stream
  // Endpoint: POST /cctv/cameras/{camera_id}/recover_stream/
  async recoverStream(cameraId: string): Promise<ApiResponse> {
    try {
      const response = await api.post(`/cctv/cameras/${cameraId}/recover_stream/`);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'StreamingService.recoverStream');
      throw serviceError;
    }
  }

  // Get Multi-Camera Stream Dashboard
  // Endpoint: GET /cctv/cameras/multi-stream/
  async getMultiStreamDashboard(): Promise<MultiStreamDashboardResponse> {
    try {
      const response = await api.get('/cctv/cameras/multi-stream/');
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'StreamingService.getMultiStreamDashboard');
      throw serviceError;
    }
  }

  // Stream System Status
  // Endpoint: GET /cctv/cameras/stream/status/
  async getStreamSystemStatus(): Promise<StreamSystemStatusResponse> {
    try {
      const response = await api.get('/cctv/cameras/stream/status/');
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'StreamingService.getStreamSystemStatus');
      throw serviceError;
    }
  }

  // Set Camera Online (Recovery)
  // Endpoint: POST /cctv/cameras/{camera_id}/set_online/
  async setCameraOnline(cameraId: string): Promise<SetCameraOnlineResponse> {
    try {
      const response = await api.post(`/cctv/cameras/${cameraId}/set_online/`);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'StreamingService.setCameraOnline');
      throw serviceError;
    }
  }
}

export default new StreamingService();
