import api from './api';
import { API_URLS } from './urls';
import { handleApiError, logError } from './errorHandler';
import { 
  CameraAccess, 
  ApiResponse 
} from './types';

class AccessControlService {
  // Get Camera Access List
  async getCameraAccess(): Promise<CameraAccess[]> {
    try {
      const response = await api.get(API_URLS.CCTV.ACCESS.DRF.LIST);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AccessControlService.getCameraAccess');
      throw serviceError;
    }
  }

  // Get Camera Access by ID
  async getCameraAccessById(accessId: string): Promise<CameraAccess> {
    try {
      const response = await api.get(API_URLS.CCTV.ACCESS.DRF.RETRIEVE(accessId));
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AccessControlService.getCameraAccessById');
      throw serviceError;
    }
  }

  // Create Camera Access
  async createCameraAccess(accessData: Partial<CameraAccess>): Promise<CameraAccess> {
    try {
      const response = await api.post(API_URLS.CCTV.ACCESS.DRF.CREATE, accessData);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AccessControlService.createCameraAccess');
      throw serviceError;
    }
  }

  // Update Camera Access
  async updateCameraAccess(accessId: string, accessData: Partial<CameraAccess>): Promise<CameraAccess> {
    try {
      const response = await api.put(API_URLS.CCTV.ACCESS.DRF.UPDATE(accessId), accessData);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AccessControlService.updateCameraAccess');
      throw serviceError;
    }
  }

  // Delete Camera Access
  async deleteCameraAccess(accessId: string): Promise<ApiResponse> {
    try {
      const response = await api.delete(API_URLS.CCTV.ACCESS.DRF.DELETE(accessId));
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AccessControlService.deleteCameraAccess');
      throw serviceError;
    }
  }
}

export default new AccessControlService();
