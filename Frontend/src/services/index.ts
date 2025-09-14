// Export all individual services
export { default as cameraService } from './cameraService';
export { default as recordingService } from './recordingService';
export { default as streamingService } from './streamingService';
export { default as scheduleService } from './scheduleService';
export { default as accessControlService } from './accessControlService';
export { default as systemService } from './systemService';
export { default as dashboardService } from './dashboardService';
export { HierarchyService } from './hierarchyService';
export { default as authService } from './authService';
export { default as userService } from './userService';

// Export types
export * from './types';
export * from './hierarchyTypes';

// Legacy export for backward compatibility
// This maintains the same interface as the original cctvService
import cameraService from './cameraService';
import recordingService from './recordingService';
import streamingService from './streamingService';
import scheduleService from './scheduleService';
import accessControlService from './accessControlService';
import systemService from './systemService';
import dashboardService from './dashboardService';

// Create a combined service that maintains the original interface
const cctvService = {
  // Camera operations
  getCameras: cameraService.getCameras.bind(cameraService),
  createCamera: cameraService.createCamera.bind(cameraService),
  getCamera: cameraService.getCamera.bind(cameraService),
  updateCamera: cameraService.updateCamera.bind(cameraService),
  deleteCamera: cameraService.deleteCamera.bind(cameraService),
  testCameraConnection: cameraService.testCameraConnection.bind(cameraService),
  testCameraConnectionDRF: cameraService.testCameraConnectionDRF.bind(cameraService),

  // Recording operations
  startRecording: recordingService.startRecording.bind(recordingService),
  stopRecording: recordingService.stopRecording.bind(recordingService),
  getRecordingStatus: recordingService.getRecordingStatus.bind(recordingService),
  getRecordingOverview: recordingService.getRecordingOverview.bind(recordingService),
  testRecording: recordingService.testRecording.bind(recordingService),
  getRecordings: recordingService.getRecordings.bind(recordingService),
  getRecording: recordingService.getRecording.bind(recordingService),
  getRecordingStats: recordingService.getRecordingStats.bind(recordingService),
  downloadRecording: recordingService.downloadRecording.bind(recordingService),
  streamRecording: recordingService.streamRecording.bind(recordingService),

  // Streaming operations
  getLiveStreamUrl: streamingService.getLiveStreamUrl.bind(streamingService),
  getLiveStreamBlob: streamingService.getLiveStreamBlob.bind(streamingService),
  getCameraStreamInfo: streamingService.getCameraStreamInfo.bind(streamingService),
  getCameraThumbnail: streamingService.getCameraThumbnail.bind(streamingService),
  captureSnapshot: streamingService.captureSnapshot.bind(streamingService),
  activateStream: streamingService.activateStream.bind(streamingService),
  deactivateStream: streamingService.deactivateStream.bind(streamingService),
  getStreamStatus: streamingService.getStreamStatus.bind(streamingService),
  getStreamHealth: streamingService.getStreamHealth.bind(streamingService),
  getAllStreams: streamingService.getAllStreams.bind(streamingService),
  getActiveStreams: streamingService.getActiveStreams.bind(streamingService),
  testStreamConnection: streamingService.testCameraConnection.bind(streamingService),
  recoverStream: streamingService.recoverStream.bind(streamingService),
  getMultiStreamDashboard: streamingService.getMultiStreamDashboard.bind(streamingService),
  getStreamSystemStatus: streamingService.getStreamSystemStatus.bind(streamingService),

  // Schedule operations
  getSchedules: scheduleService.getSchedules.bind(scheduleService),
  getSchedule: scheduleService.getSchedule.bind(scheduleService),
  createSchedule: scheduleService.createSchedule.bind(scheduleService),
  updateSchedule: scheduleService.updateSchedule.bind(scheduleService),
  deleteSchedule: scheduleService.deleteSchedule.bind(scheduleService),
  activateSchedule: scheduleService.activateSchedule.bind(scheduleService),
  deactivateSchedule: scheduleService.deactivateSchedule.bind(scheduleService),
  getScheduleStatus: scheduleService.getScheduleStatus.bind(scheduleService),

  // Access control operations
  getCameraAccess: accessControlService.getCameraAccess.bind(accessControlService),
  getCameraAccessById: accessControlService.getCameraAccessById.bind(accessControlService),
  createCameraAccess: accessControlService.createCameraAccess.bind(accessControlService),
  updateCameraAccess: accessControlService.updateCameraAccess.bind(accessControlService),
  deleteCameraAccess: accessControlService.deleteCameraAccess.bind(accessControlService),

  // System operations
  getHealth: systemService.getHealth.bind(systemService),
  getSystemOverview: systemService.getSystemOverview.bind(systemService),
  getCameraStatus: systemService.getCameraStatus.bind(systemService),
  getAllRecordingStatus: systemService.getAllRecordingStatus.bind(systemService),
  testConnection: systemService.testConnection.bind(systemService),

  // Dashboard operations
  getDashboardAnalytics: dashboardService.getAnalytics.bind(dashboardService),
  getRecentActivity: dashboardService.getRecentActivity.bind(dashboardService),
  getSystemMetrics: dashboardService.getSystemMetrics.bind(dashboardService),
  getCameraStatusDistribution: dashboardService.getCameraStatusDistribution.bind(dashboardService),
  getRecordingActivity: dashboardService.getRecordingActivity.bind(dashboardService),
  getHourlyActivity: dashboardService.getHourlyActivity.bind(dashboardService),
  getScheduleTypeDistribution: dashboardService.getScheduleTypeDistribution.bind(dashboardService),
  getStorageUsage: dashboardService.getStorageUsage.bind(dashboardService),
  refreshDashboard: dashboardService.refreshDashboard.bind(dashboardService),
};

export default cctvService;
