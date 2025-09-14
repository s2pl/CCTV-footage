import { useState, useEffect, useCallback } from 'react';
import { 
  cameraService, 
  recordingService, 
  streamingService, 
  scheduleService, 
  accessControlService, 
  systemService 
} from '../services';
import { 
  Camera, 
  RecordingSchedule, 
  Recording, 
  CameraAccess,
  RecordingsListResponse,
  SchedulesListResponse 
} from '../services/types';
import { 
  ServiceError, 
  isNetworkError, 
  isAuthError, 
  isValidationError, 
  isServerError, 
  getErrorMessage 
} from '../services/errorHandler';

export const useCCTV = () => {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [schedules, setSchedules] = useState<RecordingSchedule[]>([]);
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [recordingStats, setRecordingStats] = useState<{ total_recordings: number; completed_recordings: number; failed_recordings: number } | null>(null);
  const [scheduleStats, setScheduleStats] = useState<{ total_schedules: number; active_schedules: number } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<'network' | 'auth' | 'validation' | 'server' | 'unknown' | null>(null);

  // Helper function to handle errors
  const handleError = useCallback((err: unknown) => {
    if (err instanceof ServiceError) {
      setError(getErrorMessage(err));
      
      if (isNetworkError(err)) {
        setErrorType('network');
      } else if (isAuthError(err)) {
        setErrorType('auth');
      } else if (isValidationError(err)) {
        setErrorType('validation');
      } else if (isServerError(err)) {
        setErrorType('server');
      } else {
        setErrorType('unknown');
      }
    } else {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
      setErrorType('unknown');
    }
    console.error('CCTV Service Error:', err);
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
    setErrorType(null);
  }, []);

  // Fetch all cameras
  const fetchCameras = useCallback(async () => {
    try {
      setLoading(true);
      clearError();
      const data = await cameraService.getCameras();
      setCameras(data);
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  }, [clearError, handleError]);

  // Get single camera
  const getCamera = useCallback(async (cameraId: string) => {
    try {
      clearError();
      const camera = await cameraService.getCamera(cameraId);
      return camera;
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [clearError, handleError]);

  // Fetch all schedules
  const fetchSchedules = useCallback(async () => {
    try {
      setLoading(true);
      clearError();
      const data = await scheduleService.getSchedules();
      setSchedules(data.schedules);
      setScheduleStats({
        total_schedules: data.total_schedules,
        active_schedules: data.active_schedules
      });
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  }, [clearError, handleError]);

  // Fetch all recordings
  const fetchRecordings = useCallback(async () => {
    try {
      setLoading(true);
      clearError();
      const data = await recordingService.getRecordings();
      setRecordings(data.recordings);
      setRecordingStats({
        total_recordings: data.total_recordings,
        completed_recordings: data.completed_recordings,
        failed_recordings: data.failed_recordings
      });
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  }, [clearError, handleError]);

  // Create new camera
  const createCamera = useCallback(async (cameraData: {
    name: string;
    description?: string;
    ip_address?: string;
    port?: number;
    username?: string;
    password?: string;
    rtsp_url: string;
    rtsp_url_sub?: string;
    camera_type?: string;
    location?: string;
    auto_record?: boolean;
    record_quality?: string;
    test_connection?: boolean;
    start_recording?: boolean;
  }) => {
    try {
      setLoading(true);
      clearError();
      const result = await cameraService.createCamera(cameraData);
      await fetchCameras(); // Refresh the list
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchCameras, clearError, handleError]);

  // Update camera
  const updateCamera = useCallback(async (cameraId: string, cameraData: Partial<Camera>) => {
    try {
      setLoading(true);
      clearError();
      const result = await cameraService.updateCamera(cameraId, cameraData);
      await fetchCameras(); // Refresh the list
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchCameras, clearError, handleError]);

  // Delete camera
  const deleteCamera = useCallback(async (cameraId: string) => {
    try {
      setLoading(true);
      clearError();
      await cameraService.deleteCamera(cameraId);
      await fetchCameras(); // Refresh the list
    } catch (err) {
      handleError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchCameras, clearError, handleError]);

  // Test camera connection
  const testCameraConnection = useCallback(async (cameraId: string) => {
    try {
      clearError();
      const result = await cameraService.testCameraConnection(cameraId);
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [clearError, handleError]);

  // Start recording
  const startRecording = useCallback(async (cameraId: string, recordingData: {
    duration_minutes?: number;
    recording_name?: string;
    quality?: string;
  }) => {
    try {
      clearError();
      const result = await recordingService.startRecording(cameraId, recordingData);
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [clearError, handleError]);

  // Stop recording
  const stopRecording = useCallback(async (cameraId: string) => {
    try {
      clearError();
      const result = await recordingService.stopRecording(cameraId);
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [clearError, handleError]);

  // Quick record (5 minute recording)
  const quickRecord = useCallback(async (cameraId: string) => {
    try {
      clearError();
      const result = await recordingService.startRecording(cameraId, {
        duration_minutes: 5,
        recording_name: `Quick Record - ${new Date().toLocaleString()}`,
        quality: 'main'
      });
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [clearError, handleError]);

  // Get recording status
  const getRecordingStatus = useCallback(async (cameraId: string) => {
    try {
      clearError();
      const result = await recordingService.getRecordingStatus(cameraId);
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [clearError, handleError]);

  // Get recording overview
  const getRecordingOverview = useCallback(async () => {
    try {
      clearError();
      const result = await recordingService.getRecordingOverview();
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [clearError, handleError]);

  // Get stream info
  const getStreamInfo = useCallback(async (cameraId: string) => {
    try {
      clearError();
      const result = await streamingService.getStreamInfo(cameraId);
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [clearError, handleError]);

  // Get camera stream info
  const getCameraStreamInfo = useCallback(async (cameraId: string) => {
    try {
      clearError();
      const result = await streamingService.getCameraStreamInfo(cameraId);
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [clearError, handleError]);

  // Get camera live stream
  const getCameraLiveStream = useCallback(async (cameraId: string, quality: string = 'main') => {
    try {
      clearError();
      const result = await streamingService.getLiveStream(cameraId, quality);
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [clearError, handleError]);

  // Get active streams
  const getActiveStreams = useCallback(async () => {
    try {
      clearError();
      const result = await streamingService.getActiveStreams();
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [clearError, handleError]);

  // Get all streams
  const getAllStreams = useCallback(async () => {
    try {
      clearError();
      const result = await streamingService.getAllStreams();
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [clearError, handleError]);

  // Get recording stats
  const getRecordingStats = useCallback(async () => {
    try {
      clearError();
      const result = await recordingService.getRecordingStats();
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [clearError, handleError]);

  // Get recording by ID
  const getRecording = useCallback(async (recordingId: string) => {
    try {
      clearError();
      const result = await recordingService.getRecording(recordingId);
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [clearError, handleError]);

  // Download recording
  const downloadRecording = useCallback(async (recordingId: string) => {
    try {
      clearError();
      const result = await recordingService.downloadRecording(recordingId);
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [clearError, handleError]);

  // Stream recording
  const streamRecording = useCallback(async (recordingId: string) => {
    try {
      clearError();
      const result = await recordingService.streamRecording(recordingId);
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [clearError, handleError]);

  // Create schedule
  const createSchedule = useCallback(async (scheduleData: Partial<RecordingSchedule>) => {
    try {
      setLoading(true);
      clearError();
      const result = await scheduleService.createSchedule(scheduleData);
      await fetchSchedules(); // Refresh the list
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchSchedules, clearError, handleError]);

  // Update schedule
  const updateSchedule = useCallback(async (scheduleId: string, scheduleData: Partial<RecordingSchedule>) => {
    try {
      setLoading(true);
      clearError();
      const result = await scheduleService.updateSchedule(scheduleId, scheduleData);
      await fetchSchedules(); // Refresh the list
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchSchedules, clearError, handleError]);

  // Delete schedule
  const deleteSchedule = useCallback(async (scheduleId: string) => {
    try {
      setLoading(true);
      clearError();
      await scheduleService.deleteSchedule(scheduleId);
      await fetchSchedules(); // Refresh the list
    } catch (err) {
      handleError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchSchedules, clearError, handleError]);

  // Activate schedule
  const activateSchedule = useCallback(async (scheduleId: string) => {
    try {
      clearError();
      const result = await scheduleService.activateSchedule(scheduleId);
      await fetchSchedules(); // Refresh the list
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [fetchSchedules, clearError, handleError]);

  // Deactivate schedule
  const deactivateSchedule = useCallback(async (scheduleId: string) => {
    try {
      clearError();
      const result = await scheduleService.deactivateSchedule(scheduleId);
      await fetchSchedules(); // Refresh the list
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [fetchSchedules, clearError, handleError]);

  // Get schedule by ID
  const getScheduleById = useCallback(async (scheduleId: string) => {
    try {
      clearError();
      const result = await scheduleService.getSchedule(scheduleId);
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [clearError, handleError]);

  // Get camera access
  const getCameraAccess = useCallback(async () => {
    try {
      clearError();
      const result = await accessControlService.getCameraAccess();
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [clearError, handleError]);

  // Create camera access
  const createCameraAccess = useCallback(async (accessData: Partial<CameraAccess>) => {
    try {
      setLoading(true);
      clearError();
      const result = await accessControlService.createCameraAccess(accessData);
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [clearError, handleError]);

  // Update camera access
  const updateCameraAccess = useCallback(async (accessId: string, accessData: Partial<CameraAccess>) => {
    try {
      setLoading(true);
      clearError();
      const result = await accessControlService.updateCameraAccess(accessId, accessData);
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [clearError, handleError]);

  // Delete camera access
  const deleteCameraAccess = useCallback(async (accessId: string) => {
    try {
      setLoading(true);
      clearError();
      await accessControlService.deleteCameraAccess(accessId);
    } catch (err) {
      handleError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [clearError, handleError]);

  // Get health status
  const getHealth = useCallback(async () => {
    try {
      clearError();
      const result = await systemService.getHealth();
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [clearError, handleError]);

  // Refresh all data
  const refreshAll = useCallback(async () => {
    try {
      setLoading(true);
      clearError();
      await Promise.all([
        fetchCameras(),
        fetchSchedules(),
        fetchRecordings(),
      ]);
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  }, [fetchCameras, fetchSchedules, fetchRecordings, clearError, handleError]);

  // Load initial data
  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  // Stream Activation/Deactivation
  const activateStream = useCallback(async (cameraId: string) => {
    try {
      clearError();
      const result = await streamingService.activateLiveStream(cameraId);
      await fetchCameras(); // Refresh the list to update status
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [clearError, handleError, fetchCameras]);

  const deactivateStream = useCallback(async (cameraId: string) => {
    try {
      clearError();
      const result = await streamingService.deactivateLiveStream(cameraId);
      await fetchCameras(); // Refresh the list to update status
      return result;
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [clearError, handleError, fetchCameras]);

  return {
    // State
    cameras,
    schedules,
    recordings,
    recordingStats,
    scheduleStats,
    loading,
    error,
    errorType,
    
    // Actions
    fetchCameras,
    getCamera,
    fetchSchedules,
    fetchRecordings,
    createCamera,
    updateCamera,
    deleteCamera,
    testCameraConnection,
    startRecording,
    stopRecording,
    quickRecord,
    getRecordingStatus,
    getRecordingOverview,
    getStreamInfo,
    getCameraStreamInfo,
    getCameraLiveStream,
    getActiveStreams,
    getAllStreams,
    getRecordingStats,
    getRecording,
    downloadRecording,
    streamRecording,
    createSchedule,
    updateSchedule,
    deleteSchedule,
    activateSchedule,
    deactivateSchedule,
    getScheduleById,
    getCameraAccess,
    createCameraAccess,
    updateCameraAccess,
    deleteCameraAccess,
    getHealth,
    refreshAll,
    activateStream,
    deactivateStream,
    
    // Error handling
    clearError,
  };
};
