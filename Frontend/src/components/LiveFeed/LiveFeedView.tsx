import React, { useState, useEffect, useCallback } from 'react';

import { Camera, Settings, RefreshCw, Info, Play, Pause, Grid, Maximize2, Wifi, WifiOff, Eye, EyeOff, RotateCcw } from 'lucide-react';
import { useCCTV } from '../../hooks/useCCTV';
import { useLiveFeedManager } from '../../hooks/useLiveFeedManager';
import { streamingService } from '../../services';
import type { StreamInfo } from '../../services/types';

interface LiveFeedViewProps {
  isActivePage?: boolean;
}

const LiveFeedView: React.FC<LiveFeedViewProps> = ({ isActivePage = false }) => {
  const { cameras, loading } = useCCTV();
  const [selectedCamera, setSelectedCamera] = useState<string | null>(null);
  const [streamInfo, setStreamInfo] = useState<StreamInfo | null>(null);
  const [currentQuality, setCurrentQuality] = useState<string>('main');
  const [streamError, setStreamError] = useState<string | null>(null);
  const [isRecovering, setIsRecovering] = useState(false);
  const [recoveryAttempts, setRecoveryAttempts] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const [viewMode, setViewMode] = useState<'single' | 'grid'>('single');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [bandwidthSaverMode, setBandwidthSaverMode] = useState(false);
  const [autoPauseEnabled, setAutoPauseEnabled] = useState(true);

  // Use the live feed manager for intelligent streaming control
  const feedManager = useLiveFeedManager({
    isOnLiveFeedPage: isActivePage,
    autoPauseOnPageHidden: autoPauseEnabled,
    bandwidthSaverMode
  });

  // Get cameras array safely
  const camerasArray = Array.isArray(cameras) ? cameras : [];
  const availableCameras = camerasArray.filter(cam => cam.status === 'active');
  const allCameras = camerasArray; // Show all cameras in selector, not just active ones

  const loadStreamInfo = useCallback(async (cameraId: string) => {
    // Prevent concurrent requests for the same camera
    if (!cameraId) return;
    
    try {
      setStreamError(null);
      console.log('Loading stream info for camera:', cameraId);
      
      const info = await streamingService.getCameraStreamInfo(cameraId);
      
      // Only update state if this is still the selected camera
      if (selectedCamera === cameraId) {
        setStreamInfo(info);
        setCurrentQuality(info.supported_qualities[0] || 'main');
        console.log('Stream info loaded:', info);
        
        // Reset recovery attempts on successful load
        setRecoveryAttempts(0);
      }
    } catch (error) {
      console.error('Error loading stream info:', error);
      // Only set error if this is still the selected camera
      if (selectedCamera === cameraId) {
        setStreamError(error instanceof Error ? error.message : 'Failed to load stream info');
        
        // Auto-attempt recovery for offline cameras (max 2 attempts)
        const selectedCameraData = camerasArray.find(cam => cam.id === cameraId);
        if (selectedCameraData && 
            (selectedCameraData.status === 'offline' || selectedCameraData.status === 'inactive') &&
            recoveryAttempts < 2 && 
            !isRecovering) {
          console.log(`Camera ${selectedCameraData.name} is offline, attempting auto-recovery...`);
          attemptCameraRecovery(cameraId);
        }
      }
    }
  }, [selectedCamera, camerasArray, recoveryAttempts, isRecovering]);

  // Camera Recovery Function
  const attemptCameraRecovery = useCallback(async (cameraId: string) => {
    if (isRecovering || recoveryAttempts >= 2) return;
    
    try {
      setIsRecovering(true);
      setRecoveryAttempts(prev => prev + 1);
      console.log(`Attempting to recover camera ${cameraId} (attempt ${recoveryAttempts + 1}/2)`);
      
      const response = await streamingService.setCameraOnline(cameraId);
      
      if (response.success) {
        console.log(`Camera recovery successful:`, response);
        setStreamError(null);
        
        // Wait a moment for camera to initialize, then reload stream info
        setTimeout(() => {
          if (selectedCamera === cameraId) {
            loadStreamInfo(cameraId);
            feedManager.refreshStreams();
          }
        }, 2000);
        
        // Show success message temporarily
        setStreamError(`Camera "${response.camera_name}" is now online! ${response.stream_auto_started ? 'Stream started automatically.' : ''}`);
        setTimeout(() => setStreamError(null), 5000);
      }
    } catch (error) {
      console.error('Camera recovery failed:', error);
      const errorMessage = error instanceof Error ? error.message : 'Recovery failed';
      setStreamError(`Recovery attempt ${recoveryAttempts + 1} failed: ${errorMessage}`);
      
      // If we've reached max attempts, show final error
      if (recoveryAttempts >= 1) {
        setTimeout(() => {
          setStreamError('Camera recovery failed. Please check camera connection and try manual recovery.');
        }, 3000);
      }
    } finally {
      setIsRecovering(false);
    }
  }, [isRecovering, recoveryAttempts, selectedCamera, loadStreamInfo, feedManager]);

  // Manual Recovery Function
  const manualCameraRecovery = useCallback(async () => {
    if (!selectedCamera) return;
    
    setRecoveryAttempts(0); // Reset attempts for manual recovery
    await attemptCameraRecovery(selectedCamera);
  }, [selectedCamera, attemptCameraRecovery]);

  // Auto-select first camera if none selected
  useEffect(() => {
    if (!selectedCamera) {
      if (availableCameras.length > 0) {
        setSelectedCamera(availableCameras[0].id);
      } else if (allCameras.length > 0) {
        setSelectedCamera(allCameras[0].id);
      }
    }
  }, [availableCameras, allCameras, selectedCamera]);

  // Load stream info when camera changes (simplified - no dependency on feedManager)
  useEffect(() => {
    if (selectedCamera && isActivePage) {
      loadStreamInfo(selectedCamera);
    }
  }, [selectedCamera, isActivePage, loadStreamInfo]);

  const refreshStream = async () => {
    setIsRefreshing(true);

    if (selectedCamera) {
      try {
        // First try to set camera online using the set-online API
        const res = await streamingService.setCameraOnline(selectedCamera);
        if (res.success) {
          console.log(`Camera "${res.camera_name}" is now online${res.stream_auto_started ? ' and streaming' : ''}.`);
          setStreamError(`Camera "${res.camera_name}" is now online${res.stream_auto_started ? ' and streaming' : ''}.`);
          setTimeout(() => setStreamError(null), 5000);

        } else {
          console.warn('Set online failed:', res.message);
          setStreamError(res.message || 'Failed to set camera online');
          setTimeout(() => setStreamError(null), 5000);
        }
      } catch (error) {
        console.error('Error setting camera online:', error);
        setStreamError('Error setting camera online');
        setTimeout(() => setStreamError(null), 5000);
      }
    }

    // Always refresh the stream regardless of set-online result
    feedManager.refreshStreams();
    setIsRefreshing(false);
  };

  const toggleBandwidthSaver = () => {
    const newMode = !bandwidthSaverMode;
    setBandwidthSaverMode(newMode);
    if (newMode) {
      setCurrentQuality('sub'); // Switch to lower quality
    } else {
      setCurrentQuality('main'); // Switch back to main quality
    }
    feedManager.refreshStreams(); // Refresh stream with new quality
    console.log('Bandwidth saver mode:', newMode);
  };

  const toggleAutoPause = () => {
    setAutoPauseEnabled(!autoPauseEnabled);
    console.log('Auto-pause on page hidden:', !autoPauseEnabled);
  };

  const toggleQuality = () => {
    if (streamInfo && streamInfo.supported_qualities.length > 1) {
      const currentIndex = streamInfo.supported_qualities.indexOf(currentQuality);
      const nextIndex = (currentIndex + 1) % streamInfo.supported_qualities.length;
      setCurrentQuality(streamInfo.supported_qualities[nextIndex]);
      feedManager.refreshStreams();
    }
  };

  const getStreamUrl = (cameraId?: string, quality?: string) => {
    const camId = cameraId || selectedCamera;
    if (!camId || feedManager.isPaused || !isActivePage) return '';
    
    try {
      const effectiveQuality = bandwidthSaverMode ? 'sub' : (quality || currentQuality);
      return streamingService.getLiveStreamUrl(camId, effectiveQuality);
    } catch (error) {
      console.error('Error generating stream URL:', error);
      return '';
    }
  };

  const onStreamLoad = () => {
    setStreamError(null);
    console.log('Stream loaded successfully');
  };

  const onStreamError = () => {
    const errorMessage = 'Failed to load stream. Check if server is running and camera is accessible.';
    setStreamError(errorMessage);
    console.error('Stream failed to load');
    
    // Auto-attempt recovery for stream errors (max 2 attempts)
    if (selectedCamera && recoveryAttempts < 2 && !isRecovering) {
      const selectedCameraData = camerasArray.find(cam => cam.id === selectedCamera);
      if (selectedCameraData && 
          (selectedCameraData.status === 'offline' || selectedCameraData.status === 'inactive')) {
        console.log(`Stream error detected for offline camera, attempting auto-recovery...`);
        attemptCameraRecovery(selectedCamera);
      }
    }
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  // Debounced camera change handler to prevent crashes from rapid switching
  const handleCameraChange = (newCameraId: string) => {
    if (newCameraId === selectedCamera) return; // No change
    
    console.log('Switching camera from', selectedCamera, 'to', newCameraId);
    setSelectedCamera(newCameraId);
    setStreamError(null); // Clear any previous errors
    setRecoveryAttempts(0); // Reset recovery attempts for new camera
    setIsRecovering(false); // Clear recovery state
  };

  const selectedCameraData = allCameras.find(cam => cam.id === selectedCamera);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading cameras...</p>
        </div>
      </div>
    );
  }

  if (availableCameras.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">🎥 Live Feed</h1>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="mb-4">
            <p className="text-gray-700 dark:text-gray-300">
              No active cameras. You can attempt to bring an offline camera online.
            </p>
          </div>

          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {allCameras.map((camera) => (
              <div key={camera.id} className="py-3 flex items-center justify-between">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {camera.name} <span className="text-gray-500">• {camera.location}</span>
                  </p>
                  <p className="text-xs mt-1">
                    <span className={`font-medium ${camera.status === 'active' ? 'text-green-600' : camera.status === 'offline' || camera.status === 'inactive' ? 'text-red-600' : 'text-gray-500'}`}>
                      {camera.status?.toString().toUpperCase()}
                    </span>
                  </p>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleCameraChange(camera.id)}
                    className="px-3 py-1.5 text-sm rounded-lg bg-gray-600 hover:bg-gray-700 text-white"
                    title="Select camera"
                  >
                    Select
                  </button>

                  {camera.status !== 'active' && (
                    <button
                      onClick={() => {
                        setSelectedCamera(camera.id);
                        setRecoveryAttempts(0);
                        attemptCameraRecovery(camera.id);
                      }}
                      disabled={isRecovering}
                      className="px-3 py-1.5 text-sm rounded-lg bg-orange-600 hover:bg-orange-700 text-white disabled:opacity-50"
                      title={isRecovering ? 'Recovering camera...' : 'Set camera online'}
                    >
                      {isRecovering ? 'Recovering…' : 'Set Online'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Grid view for multiple cameras
  if (viewMode === 'grid') {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">🎥 Live Feed - Grid View</h1>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setViewMode('single')}
              className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              title="Single View"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Grid of Cameras */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {availableCameras.map(camera => (
            <div key={camera.id} className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden">
              {/* Camera Header */}
              <div className="p-3 bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
                <h3 className="font-medium text-gray-900 dark:text-white text-sm truncate">
                  {camera.name}
                </h3>
                <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                  {camera.location}
                </p>
              </div>

              {/* Camera Stream */}
              <div className="relative bg-black aspect-video">
                {feedManager.isPaused ? (
                  <div className="w-full h-full flex items-center justify-center text-white">
                    <div className="text-center">
                      <Pause className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                      <p className="text-sm text-gray-400">Paused</p>
                    </div>
                  </div>
                ) : (
                  <img
                    key={`${camera.id}-main-${feedManager.streamKey}`}
                    src={`${getStreamUrl(camera.id, 'main')}&t=${Date.now()}`}
                    alt={`Live feed from ${camera.name}`}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.style.display = 'none';
                    }}
                  />
                )}
                
                {/* Overlay with controls */}
                <div className="absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-30 transition-all duration-200 flex items-center justify-center opacity-0 hover:opacity-100">
                  <button
                    onClick={() => {
                      handleCameraChange(camera.id);
                      setViewMode('single');
                    }}
                    className="p-2 bg-white bg-opacity-80 text-gray-800 rounded-lg hover:bg-opacity-100 transition-all"
                    title="View Full"
                  >
                    <Maximize2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Single camera view
  return (
    <div className={`space-y-6 ${isFullscreen ? 'fixed inset-0 z-50 bg-black p-4' : ''}`}>
      {/* Header */}
      {!isFullscreen && (
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">🎥 Live Feed</h1>
            
            {/* Stream Status Indicator */}
            <div className="flex items-center space-x-2">
              {feedManager.isPageVisible ? (
                <div title="Page Active">
                  <Wifi className="w-5 h-5 text-green-500" />
                </div>
              ) : (
                <div title="Page Hidden">
                  <WifiOff className="w-5 h-5 text-red-500" />
                </div>
              )}
              
              {feedManager.isPaused ? (
                <div className="flex items-center space-x-1 text-orange-600 dark:text-orange-400">
                  <Pause className="w-4 h-4" />
                  <span className="text-sm font-medium">
                    {feedManager.pauseReason === 'manually-paused' ? 'Paused' : 
                     feedManager.pauseReason === 'not-on-page' ? 'Not Active' : 
                     feedManager.pauseReason === 'page-hidden' ? 'Tab Hidden' : 'Paused'}
                  </span>
                </div>
              ) : (
                <div className="flex items-center space-x-1 text-green-600 dark:text-green-400">
                  <Play className="w-4 h-4" />
                  <span className="text-sm font-medium">Streaming</span>
                </div>
              )}
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* Pause/Play Toggle */}
            <button
              onClick={feedManager.togglePause}
              className={`p-2 rounded-lg transition-colors ${
                feedManager.isManuallyPaused 
                  ? 'bg-orange-600 hover:bg-orange-700 text-white' 
                  : 'bg-green-600 hover:bg-green-700 text-white'
              }`}
              title={feedManager.isManuallyPaused ? "Resume Streaming" : "Pause Streaming"}
            >
              {feedManager.isManuallyPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
            </button>

            {/* Bandwidth Saver Toggle */}
            <button
              onClick={toggleBandwidthSaver}
              className={`p-2 rounded-lg transition-colors ${
                bandwidthSaverMode 
                  ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                  : 'bg-gray-600 hover:bg-gray-700 text-white'
              }`}
              title={`Bandwidth Saver: ${bandwidthSaverMode ? 'ON' : 'OFF'}`}
            >
              {bandwidthSaverMode ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
            </button>

            {/* Auto-pause Toggle */}
            <button
              onClick={toggleAutoPause}
              className={`p-2 rounded-lg transition-colors ${
                autoPauseEnabled 
                  ? 'bg-purple-600 hover:bg-purple-700 text-white' 
                  : 'bg-gray-600 hover:bg-gray-700 text-white'
              }`}
              title={`Auto-pause when tab hidden: ${autoPauseEnabled ? 'ON' : 'OFF'}`}
            >
              {autoPauseEnabled ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
            </button>

            {/* View Mode Toggle */}
            <button
              onClick={() => setViewMode('grid')}
              className="p-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              title="Grid View"
            >
              <Grid className="w-4 h-4" />
            </button>

            {/* Camera Selector */}
            <select
              value={selectedCamera || ''}
              onChange={(e) => handleCameraChange(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg bg-white dark:bg-gray-800 dark:border-gray-600 dark:text-white"
            >
              {allCameras.map(camera => (
                <option key={camera.id} value={camera.id}>
                  {camera.name} - {camera.location} 
                  {camera.status !== 'active' ? ` (${camera.status.toUpperCase()})` : ''}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* Stream Container */}
      <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden ${isFullscreen ? 'h-full' : ''}`}>
        {/* Stream Status Bar */}
        {!isFullscreen && (
          <div className="p-4 bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="font-medium text-gray-900 dark:text-white">
                  {selectedCameraData?.name || 'Unknown Camera'}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {selectedCameraData?.location} • Quality: {currentQuality}
                </p>
                {streamInfo?.active_session && (
                  <p className="text-xs text-blue-600 dark:text-blue-400">
                    Session: {Math.floor(streamInfo.active_session.duration_seconds / 60)}m active
                  </p>
                )}
              </div>
              
              {/* Stream Controls */}
              <div className="flex items-center space-x-2">
                <button
                  onClick={refreshStream}
                  disabled={isRefreshing}
                  className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Refresh Stream"
                >
                  <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                </button>
                
                {streamInfo && streamInfo.supported_qualities.length > 1 && (
                  <button
                    onClick={toggleQuality}
                    className="p-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                    title="Toggle Quality"
                  >
                    <Settings className="w-4 h-4" />
                  </button>
                )}
                
                <button
                  onClick={() => loadStreamInfo(selectedCamera!)}
                  className="p-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  title="Stream Info"
                >
                  <Info className="w-4 h-4" />
                </button>

                {/* Manual Recovery Button */}
                {selectedCameraData && 
                 (selectedCameraData.status === 'offline' || selectedCameraData.status === 'inactive') && (
                  <button
                    onClick={manualCameraRecovery}
                    disabled={isRecovering}
                    className="p-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors disabled:opacity-50"
                    title={isRecovering ? `Recovering camera... (${recoveryAttempts}/2)` : "Recover offline camera"}
                  >
                    <RotateCcw className={`w-4 h-4 ${isRecovering ? 'animate-spin' : ''}`} />
                  </button>
                )}

                <button
                  onClick={toggleFullscreen}
                  className="p-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                  title="Fullscreen"
                >
                  <Maximize2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Stream Display */}
        <div className={`relative bg-black flex items-center justify-center ${isFullscreen ? 'h-full' : 'aspect-video'}`}>
          {/* Fullscreen Controls */}
          {isFullscreen && (
            <div className="absolute top-4 right-4 z-10 flex items-center space-x-2">
              <span className="text-white text-sm bg-black bg-opacity-50 px-3 py-1 rounded">
                {selectedCameraData?.name} • {currentQuality}
              </span>
              <button
                onClick={refreshStream}
                disabled={isRefreshing}
                className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="Refresh"
              >
                <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              </button>
              <button
                onClick={toggleQuality}
                className="p-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                title="Quality"
              >
                <Settings className="w-4 h-4" />
              </button>
              <button
                onClick={toggleFullscreen}
                className="p-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                title="Exit Fullscreen"
              >
                ✕
              </button>
            </div>
          )}

          {streamError ? (
            <div className="text-center text-white">
              <div className="mb-4">
                <Camera className="w-16 h-16 mx-auto text-red-400" />
              </div>
              <p className="text-lg font-medium text-red-400">
                {streamError.includes('now online') ? 'Camera Recovered!' : 'Stream Error'}
              </p>
              <p className="text-sm text-gray-300 max-w-md mx-auto mt-2">{streamError}</p>
              
              <div className="flex items-center justify-center space-x-3 mt-4">
                <button
                  onClick={refreshStream}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
                  disabled={isRecovering || isRefreshing}
                >
                  <RefreshCw className={`w-4 h-4 ${(isRecovering || isRefreshing) ? 'animate-spin' : ''}`} />
                  <span>Retry</span>
                </button>
                
                {/* Show recovery button for offline cameras */}
                {selectedCameraData && 
                 (selectedCameraData.status === 'offline' || selectedCameraData.status === 'inactive') && 
                 !streamError.includes('now online') && (
                  <button
                    onClick={manualCameraRecovery}
                    disabled={isRecovering}
                    className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
                  >
                    <RotateCcw className={`w-4 h-4 ${isRecovering ? 'animate-spin' : ''}`} />
                    <span>{isRecovering ? 'Recovering...' : 'Recover Camera'}</span>
                  </button>
                )}
              </div>
              
              {/* Recovery status */}
              {isRecovering && (
                <p className="text-xs text-yellow-400 mt-2">
                  Attempting to bring camera online... (Attempt {recoveryAttempts}/2)
                </p>
              )}
              
              {recoveryAttempts > 0 && !isRecovering && !streamError.includes('now online') && (
                <p className="text-xs text-gray-400 mt-2">
                  Recovery attempts: {recoveryAttempts}/2
                </p>
              )}
            </div>
          ) : !selectedCamera ? (
            <div className="text-center text-white">
              <Camera className="w-16 h-16 mx-auto text-gray-400" />
              <p className="text-lg font-medium">Select a Camera</p>
            </div>
          ) : feedManager.isPaused ? (
            <div className="text-center text-white">
              <div className="mb-4">
                <Pause className="w-16 h-16 mx-auto text-blue-400" />
              </div>
              <p className="text-lg font-medium text-blue-400">Stream Paused</p>
              <p className="text-sm text-gray-300 max-w-md mx-auto mt-2">
                {feedManager.pauseReason === 'manually-paused' ? 'Click play to resume streaming' : 
                 feedManager.pauseReason === 'not-on-page' ? 'Navigate to LiveFeed page to start streaming' : 
                 feedManager.pauseReason === 'page-hidden' ? 'Switch back to this tab to resume streaming' : 'Streaming paused to save bandwidth'}
              </p>
              {feedManager.pauseReason === 'manually-paused' && (
                <button
                  onClick={feedManager.togglePause}
                  className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2 mx-auto"
                >
                  <Play className="w-4 h-4" />
                  <span>Resume</span>
                </button>
              )}
            </div>
          ) : (
            <img
              key={`${selectedCamera}-${currentQuality}-${feedManager.streamKey}`}
              src={`${getStreamUrl()}&t=${Date.now()}`}
              alt={`Live feed from ${selectedCameraData?.name}`}
              className="w-full h-full object-cover"
              onLoad={onStreamLoad}
              onError={onStreamError}
              style={{ display: streamError ? 'none' : 'block' }}
            />
          )}
        </div>

        {/* Stream Info Panel */}
        {!isFullscreen && streamInfo && (
          <div className="p-4 bg-gray-50 dark:bg-gray-700 border-t border-gray-200 dark:border-gray-600">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="font-medium text-gray-600 dark:text-gray-400">Status:</span>
                <p className="text-gray-900 dark:text-white">{streamInfo.camera_status}</p>
              </div>
              <div>
                <span className="font-medium text-gray-600 dark:text-gray-400">Online:</span>
                <p className={`font-medium ${streamInfo.is_online ? 'text-green-600' : 'text-red-600'}`}>
                  {streamInfo.is_online ? 'Yes' : 'No'}
                </p>
              </div>
              <div>
                <span className="font-medium text-gray-600 dark:text-gray-400">Streaming:</span>
                <p className={`font-medium ${streamInfo.is_streaming ? 'text-green-600' : 'text-red-600'}`}>
                  {streamInfo.is_streaming ? 'Active' : 'Inactive'}
                </p>
              </div>
              <div>
                <span className="font-medium text-gray-600 dark:text-gray-400">Qualities:</span>
                <p className="text-gray-900 dark:text-white">
                  {streamInfo.supported_qualities.join(', ')}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Debug Info */}
      {!isFullscreen && import.meta.env.DEV && streamInfo && (
        <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-4">
          <h3 className="font-medium text-gray-900 dark:text-white mb-2">Debug Info</h3>
          <pre className="text-xs text-gray-600 dark:text-gray-400 overflow-auto">
            {JSON.stringify(streamInfo, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default LiveFeedView;