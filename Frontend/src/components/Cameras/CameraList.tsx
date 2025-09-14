import React, { useState, useRef, useCallback } from 'react';
import { Plus, Edit, Trash2, Settings, Search, Camera, Download, Upload, AlertCircle, CheckCircle, X, Video, VideoOff, RotateCcw } from 'lucide-react';
import { useCCTV } from '../../hooks/useCCTV';
import { Camera as CameraType } from '../../services/types';
import { streamingService } from '../../services';
import CameraForm from './CameraForm';

const CameraList: React.FC = () => {
  const { 
    cameras, 
    getCamera,
    deleteCamera, 
    createCamera, 
    getCameraStreamInfo,
    loading, 
    error, 
    clearError 
  } = useCCTV();

  // Ensure cameras is an array before using array methods
  const camerasArray = Array.isArray(cameras) ? cameras : [];
  const [showForm, setShowForm] = useState(false);
  const [editingCamera, setEditingCamera] = useState<CameraType | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [recordingFilter, setRecordingFilter] = useState<string>('all');
  const [showImportModal, setShowImportModal] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importStatus, setImportStatus] = useState<{ type: 'success' | 'error' | null; message: string }>({ type: null, message: '' });
  const [operationLoading, setOperationLoading] = useState<{ [key: string]: boolean }>({});
  const [fetchingCameraDetails, setFetchingCameraDetails] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const setOperationLoadingState = useCallback((operation: string, loading: boolean) => {
    setOperationLoading(prev => ({ ...prev, [operation]: loading }));
  }, []);

  const handleEdit = async (camera: CameraType) => {
    console.log('Editing camera from list:', camera);
    setFetchingCameraDetails(true);
    
    try {
      // Fetch complete camera details from server
      console.log('Fetching complete camera details for ID:', camera.id);
      const fullCameraDetails = await getCamera(camera.id);
      console.log('Fetched complete camera details:', fullCameraDetails);
      
      setEditingCamera(fullCameraDetails);
      setShowForm(true);
    } catch (error) {
      console.error('Error fetching camera details:', error);
      // Fallback to using the camera data from the list
      setEditingCamera(camera);
      setShowForm(true);
    } finally {
      setFetchingCameraDetails(false);
    }
  };

  const handleDelete = useCallback(async (id: string, cameraName: string) => {
    if (confirm(`Are you sure you want to delete "${cameraName}"? This action cannot be undone.`)) {
      const operationKey = `delete-${id}`;
      try {
        setOperationLoadingState(operationKey, true);
        await deleteCamera(id);
      } catch (error) {
        console.error('Error deleting camera:', error);
      } finally {
        setOperationLoadingState(operationKey, false);
      }
    }
  }, [deleteCamera, setOperationLoadingState]);


  const handleSetOnline = useCallback(async (id: string, cameraName: string) => {
    const operationKey = `setonline-${id}`;
    try {
      setOperationLoadingState(operationKey, true);
      const res = await streamingService.setCameraOnline(id);
      if (res.success) {
        alert(`Camera "${cameraName}" is now online${res.stream_auto_started ? ' and streaming' : ''}.`);
      } else {
        alert(res.message || 'Failed to set camera online');
      }
    } catch (e) {
      console.error('Error setting camera online:', e);
      alert('Error setting camera online');
    } finally {
      setOperationLoadingState(operationKey, false);
    }
  }, [setOperationLoadingState]);


  const handleGetStreamInfo = async (cameraId: string) => {
    const operationKey = `info-${cameraId}`;
    try {
      setOperationLoadingState(operationKey, true);
      const streamInfo = await getCameraStreamInfo(cameraId);
      console.log('Stream info:', streamInfo);
      alert(`Stream Info:\nStatus: ${streamInfo.camera_status}\nOnline: ${streamInfo.is_online ? 'Yes' : 'No'}\nStreaming: ${streamInfo.is_streaming ? 'Yes' : 'No'}\nQualities: ${streamInfo.supported_qualities.join(', ')}`);
    } catch (error) {
      console.error('Error getting stream info:', error);
      alert('Error getting stream info');
    } finally {
      setOperationLoadingState(operationKey, false);
    }
  };



  const handleCloseForm = () => {
    setShowForm(false);
    setEditingCamera(null);
  };

  // CSV Export functionality
  const handleExportCSV = () => {
    const headers = ['Name', 'Location', 'IP Address', 'Port', 'Username', 'RTSP Path', 'Sub Stream URL', 'Status', 'Recording Enabled', 'Created At'];
    const csvContent = [
      headers.join(','),
      ...camerasArray.map(camera => [
        camera.name,
        camera.location || 'Unknown',
        camera.ip_address,
        camera.port || 554,
        camera.username || 'admin',
        camera.rtsp_path || '/stream1',
        camera.rtsp_url_sub || '',
        camera.status,
        camera.auto_record ? 'Yes' : 'No',
        camera.created_at || new Date().toISOString()
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `cameras_export_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // CSV Import functionality
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type === 'text/csv') {
      setImportFile(file);
      setImportStatus({ type: null, message: '' });
    } else {
      setImportStatus({ type: 'error', message: 'Please select a valid CSV file.' });
    }
  };

  const handleImportCSV = async () => {
    if (!importFile) return;

    try {
      const text = await importFile.text();
      const lines = text.split('\n').filter(line => line.trim());
      const headers = lines[0].split(',').map(h => h.trim());
      
      // Validate headers
      const requiredHeaders = ['Name', 'Location', 'IP Address', 'Port', 'Username', 'Status', 'Recording Enabled'];
      const missingHeaders = requiredHeaders.filter(h => !headers.includes(h));
      
      if (missingHeaders.length > 0) {
        setImportStatus({ 
          type: 'error', 
          message: `Missing required columns: ${missingHeaders.join(', ')}` 
        });
        return;
      }

      // Parse CSV data
      const camerasData = lines.slice(1).map((line, index) => {
        const values = line.split(',').map(v => v.trim());
        return {
          name: values[headers.indexOf('Name')] || `Camera ${index + 1}`,
          location: values[headers.indexOf('Location')] || 'Unknown',
          ipAddress: values[headers.indexOf('IP Address')] || '192.168.1.100',
          port: parseInt(values[headers.indexOf('Port')]) || 554,
          username: values[headers.indexOf('Username')] || 'admin',
          password: 'password123', // Default password
          rtspPath: values[headers.indexOf('RTSP Path')] || '/stream1',
          status: values[headers.indexOf('Status')] || 'online',
          recordingEnabled: values[headers.indexOf('Recording Enabled')]?.toLowerCase() === 'yes',
          lastSeen: new Date().toISOString()
        };
      });

              // Add cameras using the CCTV service
        for (const cameraData of camerasData) {
          try {
            const auth = cameraData.username ? `${cameraData.username}${cameraData.password ? ':' + cameraData.password : ''}@` : '';
            await createCamera({
              name: cameraData.name,
              location: cameraData.location,
              ip_address: cameraData.ipAddress,
              port: cameraData.port,
              username: cameraData.username,
              password: cameraData.password,
              rtsp_url: `rtsp://${auth}${cameraData.ipAddress}:${cameraData.port}${cameraData.rtspPath}`,
              auto_record: cameraData.recordingEnabled,
              record_quality: 'medium',
              test_connection: false // Skip connection test during bulk import
            });
          } catch (error) {
            console.error('Error adding camera:', error);
          }
        }

      setImportStatus({ 
        type: 'success', 
        message: `Successfully imported ${camerasData.length} cameras!` 
      });
      
      // Clear file and close modal after success
      setTimeout(() => {
        setShowImportModal(false);
        setImportFile(null);
        setImportStatus({ type: null, message: '' });
      }, 2000);

    } catch {
      setImportStatus({ 
        type: 'error', 
        message: 'Error reading CSV file. Please check the file format.' 
      });
    }
  };

  const handleCloseImportModal = () => {
    setShowImportModal(false);
    setImportFile(null);
    setImportStatus({ type: null, message: '' });
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };



  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'online':
        return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300';
      case 'offline':
        return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300';
      case 'maintenance':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-300';
    }
  };

  const filteredCameras = camerasArray.filter(camera => {
    const matchesSearch = camera.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (camera.location || '').toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || camera.status === statusFilter;
    const matchesRecording = recordingFilter === 'all' || 
                            (recordingFilter === 'enabled' && camera.auto_record) ||
                            (recordingFilter === 'disabled' && !camera.auto_record);
    
    return matchesSearch && matchesStatus && matchesRecording;
  });

  const stats = {
    total: camerasArray.length,
    online: camerasArray.filter(c => c.status === 'online').length,
    offline: camerasArray.filter(c => c.status === 'offline').length,
    maintenance: camerasArray.filter(c => c.status === 'maintenance').length,
    recording: camerasArray.filter(c => c.auto_record).length
  };

  // Show loading state while data is being fetched
  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Cameras</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage your IP cameras and monitoring devices
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500 dark:text-gray-400">Loading cameras...</div>
        </div>
      </div>
    );
  }

  // Show loading state while fetching camera details for editing
  if (fetchingCameraDetails) {
    return (
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Cameras</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage your IP cameras and monitoring devices
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center space-x-2 text-gray-500 dark:text-gray-400">
            <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <span>Loading camera details...</span>
          </div>
        </div>
      </div>
    );
  }

  if (showForm) {
    return (
      <CameraForm
        camera={editingCamera}
        onClose={handleCloseForm}
      />
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Cameras</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage your IP cameras and monitoring devices
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleExportCSV}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
          >
            <Download className="w-4 h-4" />
            <span>Export CSV</span>
          </button>
          <button
            onClick={() => setShowImportModal(true)}
            className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
          >
            <Upload className="w-4 h-4" />
            <span>Import CSV</span>
          </button>
          <button
            onClick={() => setShowForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Add Camera</span>
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-5 h-5 text-red-500" />
              <span className="text-red-800 dark:text-red-200">{error}</span>
            </div>
            <button
              onClick={clearError}
              className="text-red-500 hover:text-red-700 dark:hover:text-red-300"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 text-center">
          <div className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total}</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Total</div>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 text-center">
          <div className="text-2xl font-bold text-green-600">{stats.online}</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Online</div>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 text-center">
          <div className="text-2xl font-bold text-red-600">{stats.offline}</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Offline</div>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 text-center">
          <div className="text-2xl font-bold text-yellow-600">{stats.maintenance}</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Maintenance</div>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 text-center">
          <div className="text-2xl font-bold text-blue-600">{stats.recording}</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Recording</div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex flex-col lg:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search cameras by name or location..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Status</option>
            <option value="online">Online</option>
            <option value="offline">Offline</option>
            <option value="maintenance">Maintenance</option>
          </select>
          
          <select
            value={recordingFilter}
            onChange={(e) => setRecordingFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Recording</option>
            <option value="enabled">Recording Enabled</option>
            <option value="disabled">Recording Disabled</option>
          </select>
        </div>
      </div>

      {/* Cameras Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Camera
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  RTSP Path
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Sub Stream
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Quality & Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Recording
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Additional Info
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Last Seen
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {filteredCameras.map((camera) => (
                <tr key={camera.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center">
                        <Camera className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                      </div>
                      <div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {camera.name}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {camera.location || 'No location set'}
                        </div>
                        {camera.ip_address && (
                          <div className="text-xs text-gray-400 dark:text-gray-500">
                            {camera.ip_address}{camera.port ? `:${camera.port}` : ''}
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center space-x-2">

                      <div className="flex flex-col">
                        <span className={`px-2 py-1 text-xs rounded-full capitalize ${getStatusBadge(camera.status)}`}>
                          {camera.status}
                        </span>
                        <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          {camera.is_online ? 'Online' : 'Offline'}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                    {camera.rtsp_path ? (
                      <div className="flex flex-col">
                        <span className="font-mono text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                          {camera.rtsp_path}
                        </span>
                        <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          Custom path
                        </span>
                      </div>
                    ) : (
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        Default (/stream1)
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                    {camera.rtsp_url_sub ? (
                      <div className="flex flex-col">
                        <span className="font-mono text-xs bg-blue-100 dark:bg-blue-900/20 px-2 py-1 rounded">
                          {camera.rtsp_url_sub}
                        </span>
                        <span className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                          Sub stream
                        </span>
                      </div>
                    ) : (
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        Not configured
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                    <span className="capitalize">{camera.record_quality || 'medium'}</span>
                    {camera.camera_type && (
                      <span className="ml-2 px-2 py-1 text-xs rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                        {camera.camera_type.toUpperCase()}
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center space-x-2">
                      {camera.auto_record ? (
                        <Video className="w-4 h-4 text-green-600" />
                      ) : (
                        <VideoOff className="w-4 h-4 text-gray-400" />
                      )}
                      <div className="flex flex-col">
                        <span className="text-sm text-gray-900 dark:text-white">
                          {camera.auto_record ? 'Enabled' : 'Disabled'}
                        </span>
                        {camera.auto_record && (
                          <span className="text-xs text-green-600 dark:text-green-400">
                            Auto-recording active
                          </span>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                    <div className="flex flex-col space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs text-gray-500 dark:text-gray-400">Max Hours:</span>
                        <span className="font-mono text-xs bg-blue-100 dark:bg-blue-900/20 px-2 py-1 rounded">
                          {camera.max_recording_hours || 24}h
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs text-gray-500 dark:text-gray-400">Access:</span>
                        <span className={`px-2 py-1 text-xs rounded-full ${camera.is_public ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'}`}>
                          {camera.is_public ? 'Public' : 'Private'}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                    {camera.last_seen ? (
                      <div>
                        <div>{new Date(camera.last_seen).toLocaleDateString()}</div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          {new Date(camera.last_seen).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </div>
                      </div>
                    ) : (
                      <div className="text-gray-500 dark:text-gray-400">
                        Never seen
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end space-x-2">
                      <button
                        onClick={() => handleEdit(camera)}
                        className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                        title="Edit Camera"
                      >
                        <Edit className="w-4 h-4" />
                      </button>

                      <button 
                        onClick={() => handleGetStreamInfo(camera.id)}
                        disabled={operationLoading[`info-${camera.id}`]}
                        className="p-2 text-gray-400 hover:text-purple-600 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Stream Info"
                      >
                        {operationLoading[`info-${camera.id}`] ? (
                          <div className="w-4 h-4 border-2 border-purple-600 border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <Settings className="w-4 h-4" />
                        )}
                      </button>

                      {(camera.status !== 'online' || !camera.is_online) && (
                        <button
                          onClick={() => handleSetOnline(camera.id, camera.name)}
                          disabled={operationLoading[`setonline-${camera.id}`]}
                          className="p-2 text-gray-400 hover:text-orange-600 hover:bg-orange-50 dark:hover:bg-orange-900/20 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                          title="Set Camera Online"
                        >
                          {operationLoading[`setonline-${camera.id}`] ? (
                            <div className="w-4 h-4 border-2 border-orange-600 border-t-transparent rounded-full animate-spin" />
                          ) : (
                            <RotateCcw className="w-4 h-4" />
                          )}
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(camera.id, camera.name)}
                        disabled={operationLoading[`delete-${camera.id}`]}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Delete Camera"
                      >
                        {operationLoading[`delete-${camera.id}`] ? (
                          <div className="w-4 h-4 border-2 border-red-600 border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {filteredCameras.length === 0 && (
          <div className="text-center py-12">
            <Camera className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No cameras found</h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Try adjusting your search or filter criteria.
            </p>
          </div>
        )}
      </div>

      {/* CSV Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Import Cameras from CSV
              </h3>
              <button
                onClick={handleCloseImportModal}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Status Messages */}
            {importStatus.type && (
              <div className={`mb-4 p-3 rounded-lg flex items-center ${
                importStatus.type === 'success' 
                  ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-300'
                  : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300'
              }`}>
                {importStatus.type === 'success' ? (
                  <CheckCircle className="w-5 h-5 mr-2" />
                ) : (
                  <AlertCircle className="w-5 h-5 mr-2" />
                )}
                {importStatus.message}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Select CSV File
                </label>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  onChange={handleFileSelect}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  File must contain columns: Name, Location, IP Address, Port, Username, Resolution, FPS, Status, Recording Enabled
                </p>
              </div>

              {importFile && (
                <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="text-sm text-gray-900 dark:text-white">
                    <strong>Selected file:</strong> {importFile.name}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Size: {(importFile.size / 1024).toFixed(2)} KB
                  </div>
                </div>
              )}

              <div className="flex gap-3 pt-4">
                <button
                  onClick={handleCloseImportModal}
                  className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleImportCSV}
                  disabled={!importFile}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Import Cameras
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CameraList;