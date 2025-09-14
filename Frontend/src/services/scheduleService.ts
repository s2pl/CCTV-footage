import api from './api';
import { API_URLS } from './urls';
import { handleApiError, logError } from './errorHandler';
import { 
  RecordingSchedule, 
  ScheduleResponse, 
  ApiResponse, 
  ScheduleStatusResponse,
  SchedulesListResponse 
} from './types';

class ScheduleService {
  // List Recording Schedules
  async getSchedules(): Promise<SchedulesListResponse> {
    try {
      const response = await api.get(API_URLS.CCTV.SCHEDULES.LIST_SCHEDULES);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'ScheduleService.getSchedules');
      throw serviceError;
    }
  }

  // Get Schedule Details
  async getSchedule(scheduleId: string): Promise<RecordingSchedule> {
    try {
      const response = await api.get(API_URLS.CCTV.SCHEDULES.GET_SCHEDULE(scheduleId));
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'ScheduleService.getSchedule');
      throw serviceError;
    }
  }

  // Create Recording Schedule
  async createSchedule(scheduleData: Partial<RecordingSchedule>): Promise<ScheduleResponse> {
    try {
      const response = await api.post(API_URLS.CCTV.SCHEDULES.CREATE_SCHEDULE, scheduleData);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'ScheduleService.createSchedule');
      throw serviceError;
    }
  }

  // Update Recording Schedule
  async updateSchedule(scheduleId: string, scheduleData: Partial<RecordingSchedule>): Promise<ApiResponse> {
    try {
      const response = await api.put(API_URLS.CCTV.SCHEDULES.UPDATE_SCHEDULE(scheduleId), scheduleData);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'ScheduleService.updateSchedule');
      throw serviceError;
    }
  }

  // Delete Recording Schedule
  async deleteSchedule(scheduleId: string): Promise<ApiResponse> {
    try {
      const response = await api.delete(API_URLS.CCTV.SCHEDULES.DELETE_SCHEDULE(scheduleId));
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'ScheduleService.deleteSchedule');
      throw serviceError;
    }
  }

  // Activate Schedule
  async activateSchedule(scheduleId: string): Promise<ApiResponse> {
    try {
      const response = await api.post(API_URLS.CCTV.SCHEDULES.ACTIVATE_SCHEDULE(scheduleId));
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'ScheduleService.activateSchedule');
      throw serviceError;
    }
  }

  // Deactivate Schedule
  async deactivateSchedule(scheduleId: string): Promise<ApiResponse> {
    try {
      const response = await api.post(API_URLS.CCTV.SCHEDULES.DEACTIVATE_SCHEDULE(scheduleId));
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'ScheduleService.deactivateSchedule');
      throw serviceError;
    }
  }

  // Get Schedule Status
  async getScheduleStatus(scheduleId: string): Promise<ScheduleStatusResponse> {
    try {
      const response = await api.get(API_URLS.CCTV.SCHEDULES.GET_SCHEDULE_STATUS(scheduleId));
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'ScheduleService.getScheduleStatus');
      throw serviceError;
    }
  }
}

export default new ScheduleService();
