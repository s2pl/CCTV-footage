import React, { useState, useEffect } from 'react';
import { Camera, RefreshCw, Grid, Maximize2, Globe } from 'lucide-react';
import { useCCTV } from '../../hooks/useCCTV';

interface HttpLiveFeedViewProps {
  isActivePage?: boolean;
}

const HttpLiveFeedView: React.FC<HttpLiveFeedViewProps> = () => {
  const { cameras, loading } = useCCTV();
  const [selectedCamera, setSelectedCamera] = useState<string | null>(null);
  const [streamError, setStreamError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [viewMode, setViewMode] = useState<'single' | 'grid'>('single');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [httpPort, setHttpPort] = useState<'80' | '443'>('80');
  const [streamPath, setStreamPath] = useState<string>('/video');
  const [customUrl, setCustomUrl] = useState<string>('');
  const [useCustomUrl, setUseCustomUrl] = useState<boolean>(false);

  // Get cameras array safely
  const camerasArray = Array.isArray(cameras) ? cameras : [];
  const availableCameras = camerasArray.filter(cam => cam.status === 'active');
  const allCameras = camerasArray;

  // Generate HTTP stream URL
  const getHttpStreamUrl = (cameraId?: string) => {
    // If using custom URL, return it directly
    if (useCustomUrl && customUrl.trim()) {
      return `${customUrl.trim()}?t=${Date.now()}`;
    }
    
    const camId = cameraId || selectedCamera;
    if (!camId) return '';
    
    const camera = camerasArray.find(cam => cam.id === camId);
    if (!camera) return '';
    
    const protocol = httpPort === '443' ? 'https' : 'http';
    const baseUrl = `${protocol}://${camera.ip_address}:${httpPort}`;
    
    const path = streamPath || '/video';
    return `${baseUrl}${path}?t=${Date.now()}`;
  };

  // Test HTTP connection
  const testHttpConnection = async (cameraId?: string) => {
    // If using custom URL, test it directly
    if (useCustomUrl && customUrl.trim()) {
      try {
        await fetch(customUrl.trim(), {
          method: 'HEAD',
          mode: 'no-cors', // Allow cross-origin requests
          cache: 'no-cache'
        });
        return true; // If no error, assume connection is possible
      } catch (error) {
        console.log('Custom URL connection test failed:', error);
        return false;
      }
    }
    
    const camId = cameraId || selectedCamera;
    if (!camId) return false;
    
    const camera = camerasArray.find(cam => cam.id === camId);
    if (!camera) return false;
    
    try {
      const protocol = httpPort === '443' ? 'https' : 'http';
      const testUrl = `${protocol}://${camera.ip_address}:${httpPort}/`;
      
      await fetch(testUrl, {
        method: 'HEAD',
        mode: 'no-cors', // Allow cross-origin requests
        cache: 'no-cache'
      });
      
      return true; // If no error, assume connection is possible
    } catch (error) {
      console.log('HTTP connection test failed:', error);
      return false;
    }
  };

  // Auto-select first camera if none selected
  useEffect(() => {
    if (!selectedCamera && allCameras.length > 0) {
      setSelectedCamera(allCameras[0].id);
    }
  }, [allCameras, selectedCamera]);

  const refreshStream = async () => {
    setIsRefreshing(true);
    setStreamError(null);
    
    if (useCustomUrl && customUrl.trim()) {
      try {
        const connectionOk = await testHttpConnection();
        if (!connectionOk) {
          setStreamError('Custom URL connection failed. Please check the URL and try again.');
        }
      } catch (error) {
        console.error('Error testing custom URL connection:', error);
        setStreamError('Failed to test custom URL connection.');
      }
    } else if (selectedCamera) {
      try {
        const connectionOk = await testHttpConnection(selectedCamera);
        if (!connectionOk) {
          setStreamError('HTTP connection failed. Camera may not support HTTP streaming or may be offline.');
        }
      } catch (error) {
        console.error('Error testing HTTP connection:', error);
        setStreamError('Failed to test HTTP connection.');
      }
    }
    
    setIsRefreshing(false);
  };

  const handleCameraChange = (newCameraId: string) => {
    if (newCameraId === selectedCamera) return;
    
    console.log('Switching camera from', selectedCamera, 'to', newCameraId);
    setSelectedCamera(newCameraId);
    setStreamError(null);
  };

  const onStreamLoad = () => {
    setStreamError(null);
    console.log('HTTP stream loaded successfully');
  };

  const onStreamError = () => {
    const errorMessage = 'Failed to load HTTP stream. Camera may not support HTTP streaming or may be offline.';
    setStreamError(errorMessage);
    console.error('HTTP stream failed to load');
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">🌐 HTTP Live Feed</h1>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="mb-4">
            <p className="text-gray-700 dark:text-gray-300">
              No active cameras available for HTTP streaming. HTTP streaming requires cameras that support direct HTTP/MJPEG streaming.
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
                    <span className="text-gray-500 ml-2">• {camera.ip_address}</span>
                  </p>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleCameraChange(camera.id)}
                    className="px-3 py-1.5 text-sm rounded-lg bg-blue-600 hover:bg-blue-700 text-white"
                    title="Select camera for HTTP streaming"
                  >
                    Try HTTP
                  </button>
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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">🌐 HTTP Live Feed - Grid View</h1>
          
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
                <p className="text-xs text-blue-600 dark:text-blue-400">
                  HTTP: {camera.ip_address}:{httpPort}
                </p>
              </div>

              {/* Camera Stream */}
              <div className="relative bg-black aspect-video">
                <img
                  key={`${camera.id}-http-${httpPort}-${streamPath}`}
                  src={getHttpStreamUrl(camera.id)}
                  alt={`HTTP feed from ${camera.name}`}
                  className="w-full h-full object-cover"
                  onLoad={() => console.log(`HTTP stream loaded for ${camera.name}`)}
                  onError={() => console.log(`HTTP stream failed for ${camera.name}`)}
                />
                
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
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">🌐 HTTP Live Feed</h1>
            
            {/* HTTP Status Indicator */}
            <div className="flex items-center space-x-2">
              <Globe className="w-5 h-5 text-blue-500" />
              <span className="text-sm text-blue-600 dark:text-blue-400">
                HTTP Streaming
              </span>
            </div>
          </div>
          
           <div className="flex items-center space-x-2">
             {/* Custom URL Toggle */}
             <label className="flex items-center space-x-2 text-sm">
               <input
                 type="checkbox"
                 checked={useCustomUrl}
                 onChange={(e) => setUseCustomUrl(e.target.checked)}
                 className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
               />
               <span className="text-gray-700 dark:text-gray-300">Custom URL</span>
             </label>

             {/* Custom URL Input */}
             {useCustomUrl ? (
               <input
                 type="url"
                 value={customUrl}
                 onChange={(e) => setCustomUrl(e.target.value)}
                 placeholder="http://192.168.1.9/index.html#preview.html"
                 className="px-3 py-2 border border-gray-300 rounded-lg bg-white dark:bg-gray-800 dark:border-gray-600 dark:text-white text-sm min-w-80"
                 title="Custom Camera URL"
               />
             ) : (
               <>
                 {/* HTTP Port Selector */}
                 <select
                   value={httpPort}
                   onChange={(e) => setHttpPort(e.target.value as '80' | '443')}
                   className="px-3 py-2 border border-gray-300 rounded-lg bg-white dark:bg-gray-800 dark:border-gray-600 dark:text-white text-sm"
                   title="HTTP Port"
                 >
                   <option value="80">Port 80 (HTTP)</option>
                   <option value="443">Port 443 (HTTPS)</option>
                 </select>

                 {/* Stream Path Selector */}
                 <select
                   value={streamPath}
                   onChange={(e) => setStreamPath(e.target.value)}
                   className="px-3 py-2 border border-gray-300 rounded-lg bg-white dark:bg-gray-800 dark:border-gray-600 dark:text-white text-sm"
                   title="Stream Path"
                 >
                   <option value="/video">/video</option>
                   <option value="/mjpeg">/mjpeg</option>
                   <option value="/stream">/stream</option>
                   <option value="/live">/live</option>
                   <option value="/cam">/cam</option>
                   <option value="/snapshot">/snapshot</option>
                 </select>
               </>
             )}

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
                   {useCustomUrl ? 'Custom URL Stream' : (selectedCameraData?.name || 'Unknown Camera')}
                 </h3>
                 <p className="text-sm text-gray-600 dark:text-gray-400">
                   {useCustomUrl ? customUrl : `${selectedCameraData?.location} • HTTP: ${selectedCameraData?.ip_address}:${httpPort}${streamPath}`}
                 </p>
                 <p className="text-xs text-blue-600 dark:text-blue-400">
                   {useCustomUrl ? 'Custom URL streaming' : 'Direct HTTP streaming (no RTSP server required)'}
                 </p>
              </div>
              
              {/* Stream Controls */}
              <div className="flex items-center space-x-2">
                <button
                  onClick={refreshStream}
                  disabled={isRefreshing}
                  className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Test HTTP Connection"
                >
                  <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                </button>
                
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
                 {useCustomUrl ? 'Custom URL' : `${selectedCameraData?.name} • HTTP:${httpPort}`}
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
              <p className="text-lg font-medium text-red-400">HTTP Stream Error</p>
              <p className="text-sm text-gray-300 max-w-md mx-auto mt-2">{streamError}</p>
              
              <div className="flex items-center justify-center space-x-3 mt-4">
                <button
                  onClick={refreshStream}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
                  disabled={isRefreshing}
                >
                  <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                  <span>Retry</span>
                </button>
              </div>
              
               <div className="mt-4 text-xs text-gray-400 max-w-md mx-auto">
                 {useCustomUrl ? (
                   <div>
                     <p>Custom URL troubleshooting:</p>
                     <ul className="list-disc list-inside mt-1">
                       <li>Check if the URL is accessible</li>
                       <li>Verify the camera supports HTTP streaming</li>
                       <li>Try accessing the URL directly in a browser</li>
                       <li>Check network connectivity</li>
                     </ul>
                   </div>
                 ) : (
                   <div>
                     <p>Common HTTP stream paths:</p>
                     <ul className="list-disc list-inside mt-1">
                       <li>/video - Generic video stream</li>
                       <li>/mjpeg - MJPEG stream</li>
                       <li>/stream - Common stream path</li>
                       <li>/live - Live stream</li>
                       <li>/cam - Camera stream</li>
                     </ul>
                   </div>
                 )}
               </div>
            </div>
          ) : (!useCustomUrl && !selectedCamera) ? (
            <div className="text-center text-white">
              <Camera className="w-16 h-16 mx-auto text-gray-400" />
              <p className="text-lg font-medium">Select a Camera or Enter Custom URL</p>
            </div>
          ) : (
            <img
              key={useCustomUrl ? `custom-${customUrl}` : `${selectedCamera}-http-${httpPort}-${streamPath}`}
              src={getHttpStreamUrl()}
              alt={useCustomUrl ? 'Custom URL feed' : `HTTP feed from ${selectedCameraData?.name}`}
              className="w-full h-full object-cover"
              onLoad={onStreamLoad}
              onError={onStreamError}
              style={{ display: streamError ? 'none' : 'block' }}
            />
          )}
        </div>

         {/* Stream Info Panel */}
         {!isFullscreen && (useCustomUrl ? customUrl.trim() : selectedCameraData) && (
           <div className="p-4 bg-gray-50 dark:bg-gray-700 border-t border-gray-200 dark:border-gray-600">
             <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
               {useCustomUrl ? (
                 <>
                   <div className="md:col-span-2">
                     <span className="font-medium text-gray-600 dark:text-gray-400">Custom URL:</span>
                     <p className="text-gray-900 dark:text-white break-all">{customUrl}</p>
                   </div>
                   <div>
                     <span className="font-medium text-gray-600 dark:text-gray-400">Type:</span>
                     <p className="text-gray-900 dark:text-white">Custom URL</p>
                   </div>
                   <div>
                     <span className="font-medium text-gray-600 dark:text-gray-400">Status:</span>
                     <p className="text-gray-900 dark:text-white">Direct Connection</p>
                   </div>
                 </>
               ) : (
                 <>
                   <div>
                     <span className="font-medium text-gray-600 dark:text-gray-400">Camera:</span>
                     <p className="text-gray-900 dark:text-white">{selectedCameraData?.name}</p>
                   </div>
                   <div>
                     <span className="font-medium text-gray-600 dark:text-gray-400">IP Address:</span>
                     <p className="text-gray-900 dark:text-white">{selectedCameraData?.ip_address}</p>
                   </div>
                   <div>
                     <span className="font-medium text-gray-600 dark:text-gray-400">HTTP Port:</span>
                     <p className="text-gray-900 dark:text-white">{httpPort}</p>
                   </div>
                   <div>
                     <span className="font-medium text-gray-600 dark:text-gray-400">Stream Path:</span>
                     <p className="text-gray-900 dark:text-white">{streamPath}</p>
                   </div>
                 </>
               )}
             </div>
           </div>
         )}
      </div>
    </div>
  );
};

export default HttpLiveFeedView;
