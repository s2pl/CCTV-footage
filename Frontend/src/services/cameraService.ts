import api from './api';
import { API_URLS } from './urls';
import { handleApiError, logError } from './errorHandler';
import { 
  Camera, 
  CameraRegistration, 
  CameraRegistrationResponse, 
  ApiResponse, 
  TestConnectionResponse 
} from './types';

class CameraService {
  // Helper method to extract camera array from API response
  private extractCamerasFromResponse(responseData: unknown): Camera[] {
    if (Array.isArray(responseData)) {
      return responseData;
    }
    
    if (responseData && typeof responseData === 'object') {
      const data = responseData as Record<string, unknown>;
      
      if (data.items && Array.isArray(data.items)) {
        // Handle paginated response with 'items' property (Django Ninja pagination)
        return data.items as Camera[];
      } else if (data.results && Array.isArray(data.results)) {
        // Handle paginated response (Django Ninja with @paginate)
        return data.results as Camera[];
      } else if (data.cameras && Array.isArray(data.cameras)) {
        // Handle wrapped response
        return data.cameras as Camera[];
      } else if (data.data && Array.isArray(data.data)) {
        // Handle nested data response
        return data.data as Camera[];
      }
    }
    
    console.error('Unexpected CCTV response structure:', responseData);
    // Return empty array instead of throwing error to prevent UI crashes
    return [];
  }

  // List Cameras
  async getCameras(): Promise<Camera[]> {
    try {
      const response = await api.get(API_URLS.CCTV.CAMERAS.LIST_CAMERAS);
      return this.extractCamerasFromResponse(response.data);
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'CameraService.getCameras');
      throw serviceError;
    }
  }

  // Register Camera
  async createCamera(cameraData: CameraRegistration): Promise<CameraRegistrationResponse> {
    try {
      const response = await api.post(API_URLS.CCTV.CAMERAS.CREATE_CAMERA, cameraData);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'CameraService.createCamera');
      throw serviceError;
    }
  }

  // Get Camera Details
  async getCamera(cameraId: string): Promise<Camera> {
    try {
      const response = await api.get(API_URLS.CCTV.CAMERAS.GET_CAMERA(cameraId));
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'CameraService.getCamera');
      throw serviceError;
    }
  }

  // Update Camera
  async updateCamera(cameraId: string, cameraData: Partial<Camera>): Promise<ApiResponse> {
    try {
      const response = await api.put(API_URLS.CCTV.CAMERAS.UPDATE_CAMERA(cameraId), cameraData);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'CameraService.updateCamera');
      throw serviceError;
    }
  }

  // Delete Camera
  async deleteCamera(cameraId: string): Promise<ApiResponse> {
    try {
      const response = await api.delete(API_URLS.CCTV.CAMERAS.DELETE_CAMERA(cameraId));
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'CameraService.deleteCamera');
      throw serviceError;
    }
  }

  // Test Camera Connection
  async testCameraConnection(cameraId: string): Promise<TestConnectionResponse> {
    try {
      const response = await api.post(API_URLS.CCTV.CAMERAS.DRF.TEST_CONNECTION(cameraId));
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'CameraService.testCameraConnection');
      throw serviceError;
    }
  }

  // Test camera connection (DRF endpoint)
  async testCameraConnectionDRF(cameraId: string): Promise<{
    success: boolean;
    message: string;
    status: string;
  }> {
    try {
      const response = await api.post(API_URLS.CCTV.CAMERAS.DRF.TEST_CONNECTION(cameraId));
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'CameraService.testCameraConnectionDRF');
      throw serviceError;
    }
  }
}

export default new CameraService();
