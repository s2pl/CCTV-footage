import api from './api';
import { API_URLS } from './urls';
import { handleApiError, logError } from './errorHandler';
import { 
  Recording, 
  RecordingControl, 
  RecordingStatus, 
  RecordingOverview, 
  RecordingStats,
  RecordingsListResponse,
  GCPTransferRequest,
  GCPTransferResponse,
  GCPTransferListResponse
} from './types';

class RecordingService {
  // Start Recording
  async startRecording(cameraId: string, recordingData: RecordingControl): Promise<{
    message: string;
    recording_id: string;
    recording_name: string;
    duration_minutes: number;
    estimated_end_time: string;
  }> {
    try {
      const response = await api.post(API_URLS.CCTV.CAMERAS.START_RECORDING(cameraId), recordingData);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'RecordingService.startRecording');
      throw serviceError;
    }
  }

  // Stop Recording
  async stopRecording(cameraId: string): Promise<{
    message: string;
    recording_id: string;
    recording_name: string;
  }> {
    try {
      const response = await api.post(API_URLS.CCTV.CAMERAS.STOP_RECORDING(cameraId));
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'RecordingService.stopRecording');
      throw serviceError;
    }
  }

  // Get Recording Status
  async getRecordingStatus(cameraId: string): Promise<RecordingStatus> {
    try {
      const response = await api.get(API_URLS.CCTV.CAMERAS.RECORDING_STATUS(cameraId));
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'RecordingService.getRecordingStatus');
      throw serviceError;
    }
  }

  // Get Recording Overview
  async getRecordingOverview(): Promise<RecordingOverview> {
    try {
      const response = await api.get(API_URLS.CCTV.CAMERAS.RECORDING_OVERVIEW);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'RecordingService.getRecordingOverview');
      throw serviceError;
    }
  }

  // Test Recording (5-minute test recording)
  async testRecording(cameraId: string): Promise<{
    message: string;
    recording_id: string;
    recording_name: string;
    duration_minutes: number;
    estimated_end_time: string;
  }> {
    try {
      const response = await api.post(API_URLS.CCTV.CAMERAS.DRF.TEST_RECORDING(cameraId), {
        duration_minutes: 5,
        recording_name: `Test Recording - ${cameraId}`,
        quality: 'main'
      });
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'RecordingService.testRecording');
      throw serviceError;
    }
  }

  // List Recordings
  async getRecordings(): Promise<RecordingsListResponse> {
    try {
      const response = await api.get(API_URLS.CCTV.RECORDINGS.LIST_RECORDINGS);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'RecordingService.getRecordings');
      throw serviceError;
    }
  }

  // Get Recording Details
  async getRecording(recordingId: string): Promise<Recording> {
    try {
      const response = await api.get(API_URLS.CCTV.RECORDINGS.GET_RECORDING(recordingId));
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'RecordingService.getRecording');
      throw serviceError;
    }
  }

  // Get Recording Statistics
  async getRecordingStats(): Promise<RecordingStats> {
    try {
      const response = await api.get(API_URLS.CCTV.RECORDINGS.GET_STATS);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'RecordingService.getRecordingStats');
      throw serviceError;
    }
  }

  // Download Recording
  async downloadRecording(recordingId: string): Promise<Blob> {
    try {
      const response = await api.get(API_URLS.CCTV.RECORDINGS.DRF.DOWNLOAD(recordingId), {
        responseType: 'blob',
      });
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'RecordingService.downloadRecording');
      throw serviceError;
    }
  }

  // Stream Recording Playback
  async streamRecording(recordingId: string): Promise<Blob> {
    try {
      const response = await api.get(API_URLS.CCTV.RECORDINGS.PLAYBACK(recordingId), {
        responseType: 'blob',
      });
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'RecordingService.streamRecording');
      throw serviceError;
    }
  }

  // Transfer Recordings to GCP
  async transferToGCP(transferData: GCPTransferRequest): Promise<GCPTransferResponse> {
    try {
      const response = await api.post(API_URLS.CCTV.RECORDINGS.TRANSFER_TO_GCP, transferData);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'RecordingService.transferToGCP');
      throw serviceError;
    }
  }

  // Get GCP Transfer Status
  async getGCPTransfers(): Promise<GCPTransferListResponse> {
    try {
      const response = await api.get(API_URLS.CCTV.RECORDINGS.GCP_TRANSFERS);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'RecordingService.getGCPTransfers');
      throw serviceError;
    }
  }
}

export default new RecordingService();
