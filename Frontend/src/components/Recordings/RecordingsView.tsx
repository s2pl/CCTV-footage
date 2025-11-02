import React, { useState, useEffect } from 'react';
import { Search, Download, Trash2, Play, HardDrive, AlertCircle, CheckCircle, X, ExternalLink, RefreshCw } from 'lucide-react';
import { useToast } from '../Common/ToastContainer';
import { Recording } from '../../services/types';
import { useCCTV } from '../../hooks/useCCTV';
import GCPTransferPanel from './GCPTransferPanel';

const RecordingsView: React.FC = () => {
  const { showSuccess, showError, showWarning } = useToast();
  const { cameras, recordings, recordingStats, loading, error, clearError, refreshAll } = useCCTV();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [cameraFilter, setCameraFilter] = useState<string>('all');
  const [selectedRecordings, setSelectedRecordings] = useState<Set<string>>(new Set());
  const [localSuccess, setLocalSuccess] = useState<string | null>(null);
  const [playingRecording, setPlayingRecording] = useState<Recording | null>(null);

  // Ensure cameras and recordings are arrays before using array methods
  const camerasArray = Array.isArray(cameras) ? cameras : [];
  const recordingsArray = Array.isArray(recordings) ? recordings : [];

  // Filter recordings based on search and filters
  const filteredRecordings = recordingsArray.filter(recording => {
    const matchesSearch = recording.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (recording.camera_name || '').toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || recording.status === statusFilter;
    const matchesCamera = cameraFilter === 'all' || recording.camera === cameraFilter;
    
    return matchesSearch && matchesStatus && matchesCamera;
  });

  // Handle recording selection
  const toggleRecordingSelection = (recordingId: string) => {
    const newSelected = new Set(selectedRecordings);
    if (newSelected.has(recordingId)) {
      newSelected.delete(recordingId);
    } else {
      newSelected.add(recordingId);
    }
    setSelectedRecordings(newSelected);
  };

  // Handle bulk selection
  const selectAll = () => {
    setSelectedRecordings(new Set(filteredRecordings.map(r => r.id)));
  };

  const deselectAll = () => {
    setSelectedRecordings(new Set());
  };

  // Handle recording deletion
  const handleDeleteRecordings = async () => {
    if (selectedRecordings.size === 0) return;
    
    if (confirm(`Are you sure you want to delete ${selectedRecordings.size} recording(s)?`)) {
      try {
        // TODO: Implement delete functionality when available in the API
        console.log('Delete recordings:', Array.from(selectedRecordings));
        showWarning(
          'Feature Not Available',
          'Delete functionality is not yet implemented. Please check with the backend team.'
        );
        
        // For now, just clear the selection
        setSelectedRecordings(new Set());
      } catch (error) {
        console.error('Error deleting recordings:', error);
        showError(
          'Delete Failed',
          'Error deleting recordings. Please try again.'
        );
      }
    }
  };

  // Handle recording download
  const handleDownloadRecording = async (recording: Recording) => {
    try {
      if (!recording.file_exists) {
        showError('Download Failed', 'File does not exist on the server. Cannot download.');
        return;
      }

      if (!recording.file_url) {
        showError('Download Failed', 'No file URL available for this recording.');
        return;
      }

      // Open the exact URL passed by file_url without any modifications
      window.open(recording.file_url, '_blank');
      
      showSuccess('Download Started', `Download started for "${recording.name}"`);
    } catch (error) {
      console.error('Error downloading recording:', error);
      showError('Download Failed', 'Error downloading recording. Please try again.');
    }
  };

  // Handle recording playback
  const handlePlayRecording = async (recording: Recording) => {
    try {
      if (!recording.file_exists) {
        showError('Playback Failed', 'File does not exist on the server. Cannot play video.');
        return;
      }

      if (!recording.file_url) {
        showError('Playback Failed', 'No file URL available for this recording.');
        return;
      }

      setPlayingRecording(recording);
    } catch (error) {
      console.error('Error playing recording:', error);
      showError('Playback Failed', 'Error playing recording. Please try again.');
    }
  };

  // Close video modal
  const closeVideoModal = () => {
    setPlayingRecording(null);
  };

  // Handle refresh
  const handleRefresh = async () => {
    try {
      await refreshAll();
    } catch (error) {
      console.error('Error refreshing recordings:', error);
    }
  };

  // Format file size
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Format duration
  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  // Get status badge styling
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300';
      case 'recording':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300';
      case 'failed':
        return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-300';
    }
  };

  // Clear error message
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => clearError(), 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

  // Handle keyboard events for modal
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && playingRecording) {
        closeVideoModal();
      }
    };

    if (playingRecording) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [playingRecording]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Recordings</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Manage and view all camera recordings
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          {selectedRecordings.size > 0 && (
            <>
              <button
                onClick={handleDeleteRecordings}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                Delete Selected ({selectedRecordings.size})
              </button>
              <button
                onClick={deselectAll}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                Clear Selection
              </button>
            </>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
              <HardDrive className="w-6 h-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Recordings</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{recordingStats?.total_recordings || recordingsArray.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 dark:bg-green-900/20 rounded-lg">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Completed</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {recordingStats?.completed_recordings || recordingsArray.filter(r => r.status === 'completed').length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
              <Play className="w-6 h-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Active</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {recordingsArray.filter(r => r.status === 'recording').length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-red-100 dark:bg-red-900/20 rounded-lg">
              <AlertCircle className="w-6 h-6 text-red-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Failed</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {recordingStats?.failed_recordings || recordingsArray.filter(r => r.status === 'failed').length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search recordings..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="recording">Recording</option>
            <option value="failed">Failed</option>
            <option value="paused">Paused</option>
          </select>
          
          <select
            value={cameraFilter}
            onChange={(e) => setCameraFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Cameras</option>
            {camerasArray.map(camera => (
              <option key={camera.id} value={camera.id}>{camera.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* GCP Transfer Panel */}
      <GCPTransferPanel 
        selectedRecordingIds={Array.from(selectedRecordings)}
        onTransferComplete={() => {
          // Optionally refresh recordings list after transfer
          // The useCCTV hook should handle this automatically
        }}
      />

      {/* Error and Success Messages */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-center">
          <AlertCircle className="w-5 h-5 text-red-600 mr-3" />
          <span className="text-red-700 dark:text-red-300">{error}</span>
          <button
            onClick={clearError}
            className="ml-auto text-red-400 hover:text-red-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      )}

      {localSuccess && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 flex items-center">
          <CheckCircle className="w-5 h-5 text-green-600 mr-3" />
          <span className="text-green-700 dark:text-green-300">{localSuccess}</span>
          <button
            onClick={() => setLocalSuccess(null)}
            className="ml-auto text-green-400 hover:text-green-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* Recordings Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Recordings ({filteredRecordings.length})
            </h3>
            <div className="flex items-center space-x-2">
              <button
                onClick={selectAll}
                className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
              >
                Select All
              </button>
              <span className="text-gray-400">|</span>
              <button
                onClick={deselectAll}
                className="text-sm text-gray-600 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
              >
                Clear
              </button>
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  <input
                    type="checkbox"
                    checked={selectedRecordings.size === filteredRecordings.length && filteredRecordings.length > 0}
                    onChange={() => selectedRecordings.size === filteredRecordings.length ? deselectAll() : selectAll()}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Recording
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Camera
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Duration
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Size
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Schedule
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Resolution
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Start Time
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {filteredRecordings.map((recording) => (
                <tr key={recording.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <input
                      type="checkbox"
                      checked={selectedRecordings.has(recording.id)}
                      onChange={() => toggleRecordingSelection(recording.id)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {recording.name}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        ID: {recording.id.substring(0, 8)}...
                      </div>
                      {recording.end_time && (
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          Ended: {new Date(recording.end_time).toLocaleString()}
                        </div>
                      )}
                      {recording.file_exists !== undefined && (
                        <div className={`text-xs ${recording.file_exists ? 'text-green-600' : 'text-red-600'}`}>
                          {recording.file_exists ? '✓ File exists' : '✗ File missing'}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {recording.camera_name || 'Unknown Camera'}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        ID: {recording.camera}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <span className={`px-2 py-1 text-xs rounded-full capitalize ${getStatusBadge(recording.status)}`}>
                        {recording.status}
                      </span>
                      {recording.error_message && (
                        <div className="text-xs text-red-600 mt-1" title={recording.error_message}>
                          ⚠️ Error occurred
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900 dark:text-white">
                      {recording.duration_seconds ? 
                        formatDuration(Math.floor(recording.duration_seconds)) : 
                        recording.duration ? formatDuration(parseInt(recording.duration)) : 'N/A'}
                    </div>
                    {recording.is_active && (
                      <div className="text-xs text-blue-600">
                        🔴 Recording...
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900 dark:text-white">
                      {recording.file_size_mb ? 
                        `${recording.file_size_mb.toFixed(2)} MB` : 
                        recording.file_size ? formatFileSize(recording.file_size) : 'N/A'}
                    </div>
                    {recording.file_size && recording.file_size_mb && (
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {formatFileSize(recording.file_size)}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {recording.schedule_name ? (
                      <div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {recording.schedule_name}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          Scheduled
                        </div>
                      </div>
                    ) : (
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        Manual
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900 dark:text-white">
                      {recording.resolution || 'N/A'}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {recording.codec && recording.frame_rate ? `${recording.codec} @ ${recording.frame_rate}fps` : recording.codec || 'N/A'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {new Date(recording.start_time).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end space-x-2">
                      <button
                        onClick={() => handlePlayRecording(recording)}
                        disabled={!recording.file_exists || !recording.file_url}
                        className={`p-2 rounded-lg transition-colors ${
                          recording.file_exists && recording.file_url
                            ? 'text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20'
                            : 'text-gray-300 cursor-not-allowed'
                        }`}
                        title={recording.file_exists && recording.file_url ? "Play Recording" : "File not available"}
                      >
                        <Play className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDownloadRecording(recording)}
                        disabled={!recording.file_exists || !recording.file_url}
                        className={`p-2 rounded-lg transition-colors ${
                          recording.file_exists && recording.file_url
                            ? 'text-gray-400 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20'
                            : 'text-gray-300 cursor-not-allowed'
                        }`}
                        title={recording.file_exists && recording.file_url ? "Download Recording" : "File not available"}
                      >
                        <Download className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {filteredRecordings.length === 0 && (
          <div className="text-center py-12">
            <HardDrive className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No recordings found</h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Try adjusting your search or filter criteria.
            </p>
          </div>
        )}
      </div>

      {/* Video Playback Modal */}
      {playingRecording && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-6xl max-h-[90vh] w-full mx-4 overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
              <div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  {playingRecording.name}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {playingRecording.camera_name} • {new Date(playingRecording.start_time).toLocaleString()}
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => handleDownloadRecording(playingRecording)}
                  className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg transition-colors"
                  title="Download Recording"
                >
                  <Download className="w-5 h-5" />
                </button>
                <button
                  onClick={() => {
                    window.open(playingRecording.file_url, '_blank');
                  }}
                  className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                  title="Open in new tab"
                >
                  <ExternalLink className="w-5 h-5" />
                </button>
                <button
                  onClick={closeVideoModal}
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors"
                  title="Close"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
            
            <div className="p-4">
              <div className="relative bg-black rounded-lg overflow-hidden">
                <video
                  controls
                  autoPlay
                  className="w-full max-h-[70vh] object-contain"
                  onError={(e) => {
                    console.error('Video playback error:', e);
                    const fileExt = playingRecording.file_path?.split('.').pop()?.toLowerCase() || 'unknown';
                    alert(`Error loading video. File format: ${fileExt.toUpperCase()}. Please check if the file exists and is in a supported format.`);
                  }}
                >
                  {(() => {
                    const videoUrl = playingRecording.file_url;
                    const fileExt = playingRecording.file_path?.split('.').pop()?.toLowerCase();
                    
                    // Determine MIME type based on file extension
                    const getMimeType = (ext?: string) => {
                      switch(ext) {
                        case 'mp4': return 'video/mp4';
                        case 'avi': return 'video/x-msvideo';
                        case 'mov': return 'video/quicktime';
                        case 'mkv': return 'video/x-matroska';
                        default: return 'video/mp4';
                      }
                    };
                    
                    const primaryMimeType = getMimeType(fileExt);
                    
                    return (
                      <>
                        <source src={videoUrl} type={primaryMimeType} />
                        {/* Fallback sources for common formats */}
                        {primaryMimeType !== 'video/mp4' && <source src={videoUrl} type="video/mp4" />}
                        {primaryMimeType !== 'video/x-msvideo' && <source src={videoUrl} type="video/x-msvideo" />}
                      </>
                    );
                  })()}
                  Your browser does not support the video tag or the video format.
                </video>
              </div>
              
              {/* Video Information */}
              <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-500 dark:text-gray-400">Duration:</span>
                  <div className="font-medium text-gray-900 dark:text-white">
                    {playingRecording.duration_seconds ? 
                      formatDuration(Math.floor(playingRecording.duration_seconds)) : 'N/A'}
                  </div>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">Size:</span>
                  <div className="font-medium text-gray-900 dark:text-white">
                    {playingRecording.file_size_mb ? 
                      `${playingRecording.file_size_mb.toFixed(2)} MB` : 'N/A'}
                  </div>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">Resolution:</span>
                  <div className="font-medium text-gray-900 dark:text-white">
                    {playingRecording.resolution || 'N/A'}
                  </div>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">Codec:</span>
                  <div className="font-medium text-gray-900 dark:text-white">
                    {playingRecording.codec || 'N/A'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RecordingsView;
