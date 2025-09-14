import React, { useState } from 'react';
import { streamingService, systemService } from '../../services';

const StreamTest: React.FC = () => {
  const [streamInfo, setStreamInfo] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const testStreamAPI = async (cameraId: string) => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('Testing stream API for camera:', cameraId);
      
      // Test getCameraStreamInfo
      const info = await streamingService.getCameraStreamInfo(cameraId);
      console.log('Stream info response:', info);
      setStreamInfo(info);
      
      // Test getLiveStream
      try {
        const liveStream = await streamingService.getLiveStreamBlob(cameraId, 'main');
        console.log('Live stream response:', liveStream);
      } catch (streamError) {
        console.warn('Live stream test failed (expected for some cameras):', streamError);
      }
      
    } catch (err) {
      console.error('Stream API test failed:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const testSystemOverview = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('Testing system overview API');
      const overview = await systemService.getSystemOverview();
      console.log('System overview response:', overview);
      
    } catch (err) {
      console.error('System overview test failed:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const testHealthCheck = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('Testing health check API');
      const health = await systemService.getHealth();
      console.log('Health check response:', health);
      
    } catch (err) {
      console.error('Health check test failed:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const testCameraRecovery = async (cameraId: string) => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('Testing camera recovery API for camera:', cameraId);
      
      const response = await streamingService.setCameraOnline(cameraId);
      console.log('Camera recovery response:', response);
      setStreamInfo(response);
      
    } catch (err) {
      console.error('Camera recovery test failed:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Stream API Test</h1>
      
      <div className="space-y-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Test Stream APIs</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Camera ID:</label>
              <input
                type="text"
                placeholder="Enter camera ID to test"
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                defaultValue="test-camera-1"
              />
            </div>
            
            <div className="flex space-x-4">
              <button
                onClick={() => testStreamAPI('test-camera-1')}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Testing...' : 'Test Stream API'}
              </button>
              
              <button
                onClick={testSystemOverview}
                disabled={loading}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
              >
                {loading ? 'Testing...' : 'Test System Overview'}
              </button>
              
              <button
                onClick={testHealthCheck}
                disabled={loading}
                className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50"
              >
                {loading ? 'Testing...' : 'Test Health Check'}
              </button>
              
              <button
                onClick={() => testCameraRecovery('test-camera-1')}
                disabled={loading}
                className="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 disabled:opacity-50"
              >
                {loading ? 'Testing...' : 'Test Camera Recovery'}
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <h3 className="text-sm font-medium text-red-800">Error</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        )}

        {streamInfo && (
          <div className="bg-green-50 border border-green-200 rounded-md p-4">
            <h3 className="text-sm font-medium text-green-800">
              {(streamInfo as any).success !== undefined ? 'Camera Recovery Response' : 'Stream Info Response'}
            </h3>
            <pre className="text-sm text-green-700 mt-2 overflow-auto">
              {JSON.stringify(streamInfo, null, 2)}
            </pre>
          </div>
        )}

        <div className="bg-gray-50 p-6 rounded-lg">
          <h3 className="text-lg font-semibold mb-4">API Endpoints Available</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium text-gray-900">Stream APIs</h4>
              <ul className="text-sm text-gray-600 mt-2 space-y-1">
                <li>• getCameraStreamInfo(cameraId)</li>
                <li>• getLiveStream(cameraId, quality)</li>
                <li>• getStreamInfo(cameraId)</li>
                <li>• getActiveStreams()</li>
                <li>• getAllStreams()</li>
                <li>• setCameraOnline(cameraId)</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-900">Camera APIs</h4>
              <ul className="text-sm text-gray-600 mt-2 space-y-1">
                <li>• getCameras()</li>
                <li>• getCamera(cameraId)</li>
                <li>• testCameraConnection(cameraId)</li>
                <li>• startRecording(cameraId, data)</li>
                <li>• stopRecording(cameraId)</li>
                <li>• recoverStream(cameraId)</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StreamTest;
