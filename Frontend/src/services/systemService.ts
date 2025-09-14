import api from './api';
import { API_URLS } from './urls';
import { handleApiError, logError } from './errorHandler';
import { 
  HealthCheckResponse 
} from './types';

class SystemService {
  // Health Check
  async getHealth(): Promise<HealthCheckResponse> {
    try {
      const response = await api.get(API_URLS.CCTV.HEALTH);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'SystemService.getHealth');
      throw serviceError;
    }
  }

  // Get System Overview
  async getSystemOverview(): Promise<{
    total_cameras: number;
    online_cameras: number;
    recording_cameras: number;
    total_recordings: number;
    system_status: string;
  }> {
    try {
      const response = await api.get(API_URLS.CCTV.STATUS.OVERVIEW);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'SystemService.getSystemOverview');
      throw serviceError;
    }
  }

  // Get Camera Status
  async getCameraStatus(): Promise<Array<{
    camera_id: string;
    camera_name: string;
    status: string;
    is_online: boolean;
    last_seen?: string;
  }>> {
    try {
      const response = await api.get(API_URLS.CCTV.STATUS.CAMERAS);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'SystemService.getCameraStatus');
      throw serviceError;
    }
  }

  // Get All Recording Status
  async getAllRecordingStatus(): Promise<Array<{
    recording_id: string;
    camera_id: string;
    status: string;
    start_time: string;
    duration?: string;
  }>> {
    try {
      const response = await api.get(API_URLS.CCTV.STATUS.RECORDINGS);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'SystemService.getAllRecordingStatus');
      throw serviceError;
    }
  }

  // Test Connection
  async testConnection(): Promise<{
    success: boolean;
    message: string;
    details?: Record<string, unknown>;
  }> {
    try {
      const response = await api.post(API_URLS.CCTV.STATUS.TEST_CONNECTION);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'SystemService.testConnection');
      throw serviceError;
    }
  }
}

export default new SystemService();
