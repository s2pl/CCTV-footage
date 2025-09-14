import React, { useState, useEffect, useCallback } from 'react';
import { Camera, Settings, RefreshCw, Info, Play, Square, Volume2, VolumeX, RotateCcw } from 'lucide-react';
import { useCCTV } from '../../hooks/useCCTV';
import { streamingService } from '../../services';
import type { Camera as CameraType, StreamInfo } from '../../services/types';

const SimpleLiveFeed: React.FC = () => {
  const { cameras, loading } = useCCTV();
  const [selectedCamera, setSelectedCamera] = useState<string | null>(null);
  const [streamInfo, setStreamInfo] = useState<StreamInfo | null>(null);
  const [currentQuality, setCurrentQuality] = useState<string>('main');
  const [streamError, setStreamError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamKey, setStreamKey] = useState(0); // For forcing image refresh
  const [isRecovering, setIsRecovering] = useState(false);
  const [recoveryAttempts, setRecoveryAttempts] = useState(0);

  // Get cameras array safely
  const camerasArray = Array.isArray(cameras) ? cameras : [];
  const availableCameras = camerasArray.filter(cam => cam.status === 'active');
  const allCameras = camerasArray; // Show all cameras in selector, not just active ones

  // Auto-select first camera if none selected
  useEffect(() => {
    if (!selectedCamera && availableCameras.length > 0) {
      setSelectedCamera(availableCameras[0].id);
    }
  }, [availableCameras, selectedCamera]);

  // Load stream info when camera changes
  useEffect(() => {
    if (selectedCamera) {
      loadStreamInfo(selectedCamera);
    }
  }, [selectedCamera]);

  const loadStreamInfo = useCallback(async (cameraId: string) => {
    try {
      setStreamError(null);
      console.log('Loading stream info for camera:', cameraId);
      
      const info = await streamingService.getCameraStreamInfo(cameraId);
      setStreamInfo(info);
      setCurrentQuality(info.supported_qualities[0] || 'main');
      setIsStreaming(info.is_streaming);
      setRecoveryAttempts(0); // Reset recovery attempts on successful load
      
      console.log('Stream info loaded:', info);
    } catch (error) {
      console.error('Error loading stream info:', error);
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
  }, [camerasArray, recoveryAttempts, isRecovering]);

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
            refreshStream();
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
  }, [isRecovering, recoveryAttempts, selectedCamera, loadStreamInfo]);

  // Manual Recovery Function
  const manualCameraRecovery = useCallback(async () => {
    if (!selectedCamera) return;
    
    setRecoveryAttempts(0); // Reset attempts for manual recovery
    await attemptCameraRecovery(selectedCamera);
  }, [selectedCamera, attemptCameraRecovery]);

  const refreshStream = () => {
    setStreamKey(prev => prev + 1);
    setStreamError(null);
  };

  const toggleQuality = () => {
    if (streamInfo && streamInfo.supported_qualities.length > 1) {
      const currentIndex = streamInfo.supported_qualities.indexOf(currentQuality);
      const nextIndex = (currentIndex + 1) % streamInfo.supported_qualities.length;
      setCurrentQuality(streamInfo.supported_qualities[nextIndex]);
      setStreamKey(prev => prev + 1);
    }
  };

  const getStreamUrl = () => {
    if (!selectedCamera) return '';
    return streamingService.getLiveStreamUrl(selectedCamera, currentQuality);
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
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Camera className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <p className="text-lg font-medium text-gray-600 dark:text-gray-400">No Active Cameras</p>
          <p className="text-sm text-gray-500">Please check your camera configuration.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">🎥 Live Feed</h1>
        
        {/* Camera Selector */}
        <div className="flex items-center space-x-4">
          <select
            value={selectedCamera || ''}
            onChange={(e) => {
              setSelectedCamera(e.target.value);
              setRecoveryAttempts(0); // Reset recovery attempts for new camera
              setIsRecovering(false); // Clear recovery state
            }}
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

      {/* Stream Container */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden">
        {/* Stream Status Bar */}
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
                className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                title="Refresh Stream"
              >
                <RefreshCw className="w-4 h-4" />
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
            </div>
          </div>
        </div>

        {/* Stream Display */}
        <div className="relative bg-black aspect-video flex items-center justify-center">
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
                  disabled={isRecovering}
                >
                  <RefreshCw className={`w-4 h-4 ${isRecovering ? 'animate-spin' : ''}`} />
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
          ) : (
            <img
              key={`${selectedCamera}-${currentQuality}-${streamKey}`}
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
        {streamInfo && (
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
      {import.meta.env.DEV && streamInfo && (
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

export default SimpleLiveFeed;
