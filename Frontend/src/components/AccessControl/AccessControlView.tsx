import React, { useState } from 'react';
import { Shield, Key, Users, Plus, Edit, Trash2, RefreshCw } from 'lucide-react';
import { useData } from '../../hooks/useData';

interface AccessEndpoint {
  id: string;
  name: string;
  endpoint: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  allowedUsers: string[];
  allowedCameras: string[];
  active: boolean;
  createdAt: string;
}

const AccessControlView: React.FC = () => {
  const { users, cameras } = useData();
  const [endpoints, setEndpoints] = useState<AccessEndpoint[]>([
    {
      id: '1',
      name: 'Live Feed Access',
      endpoint: '/api/camera/live/{camera_id}',
      method: 'GET',
      allowedUsers: ['1', '2'],
      allowedCameras: ['1', '2'],
      active: true,
      createdAt: new Date().toISOString()
    },
    {
      id: '2',
      name: 'Recording Control',
      endpoint: '/api/camera/record/{camera_id}',
      method: 'POST',
      allowedUsers: ['1'],
      allowedCameras: ['1', '2', '3'],
      active: true,
      createdAt: new Date().toISOString()
    }
  ]);
  const [showForm, setShowForm] = useState(false);
  const [editingEndpoint, setEditingEndpoint] = useState<AccessEndpoint | null>(null);
  const [loading, setLoading] = useState(false);

  const getUserName = (userId: string) => {
    return users.find(u => u.id === userId)?.username || 'Unknown User';
  };

  const getCameraName = (cameraId: string) => {
    return cameras.find(c => c.id === cameraId)?.name || 'Unknown Camera';
  };

  const handleRefresh = async () => {
    setLoading(true);
    try {
      // Simulate refresh - in a real app, this would fetch fresh data
      await new Promise(resolve => setTimeout(resolve, 1000));
    } catch (error) {
      console.error('Error refreshing access control:', error);
    } finally {
      setLoading(false);
    }
  };

  const EndpointForm: React.FC<{ endpoint?: AccessEndpoint | null; onClose: () => void }> = ({ endpoint, onClose }) => {
    const [formData, setFormData] = useState({
      name: endpoint?.name || '',
      endpoint: endpoint?.endpoint || '',
      method: endpoint?.method || 'GET' as const,
      allowedUsers: endpoint?.allowedUsers || [],
      allowedCameras: endpoint?.allowedCameras || [],
      active: endpoint?.active ?? true
    });

    const handleSubmit = (e: React.FormEvent) => {
      e.preventDefault();
      
      const newEndpoint: AccessEndpoint = {
        id: endpoint?.id || Date.now().toString(),
        ...formData,
        createdAt: endpoint?.createdAt || new Date().toISOString()
      };

      if (endpoint) {
        setEndpoints(prev => prev.map(ep => ep.id === endpoint.id ? newEndpoint : ep));
      } else {
        setEndpoints(prev => [...prev, newEndpoint]);
      }
      
      onClose();
    };

    const toggleUser = (userId: string) => {
      setFormData(prev => ({
        ...prev,
        allowedUsers: prev.allowedUsers.includes(userId)
          ? prev.allowedUsers.filter(id => id !== userId)
          : [...prev.allowedUsers, userId]
      }));
    };

    const toggleCamera = (cameraId: string) => {
      setFormData(prev => ({
        ...prev,
        allowedCameras: prev.allowedCameras.includes(cameraId)
          ? prev.allowedCameras.filter(id => id !== cameraId)
          : [...prev.allowedCameras, cameraId]
      }));
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              {endpoint ? 'Edit Access Endpoint' : 'Create Access Endpoint'}
            </h2>
          </div>
          
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Endpoint Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="e.g., Live Feed Access"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  HTTP Method
                </label>
                <select
                  value={formData.method}
                  onChange={(e) => setFormData(prev => ({ ...prev, method: e.target.value as 'GET' | 'POST' | 'PUT' | 'DELETE' }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="GET">GET</option>
                  <option value="POST">POST</option>
                  <option value="PUT">PUT</option>
                  <option value="DELETE">DELETE</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                API Endpoint *
              </label>
              <input
                type="text"
                value={formData.endpoint}
                onChange={(e) => setFormData(prev => ({ ...prev, endpoint: e.target.value }))}
                required
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="/api/camera/live/{camera_id}"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Allowed Users
              </label>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {users.map(user => (
                  <label key={user.id} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={formData.allowedUsers.includes(user.id)}
                      onChange={() => toggleUser(user.id)}
                      className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-900 dark:text-white">{user.username} ({user.role})</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Allowed Cameras
              </label>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {cameras.map(camera => (
                  <label key={camera.id} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={formData.allowedCameras.includes(camera.id)}
                      onChange={() => toggleCamera(camera.id)}
                      className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-900 dark:text-white">{camera.name} ({camera.location})</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={formData.active}
                  onChange={(e) => setFormData(prev => ({ ...prev, active: e.target.checked }))}
                  className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Endpoint is active
                </span>
              </label>
            </div>

            <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
              >
                {endpoint ? 'Update Endpoint' : 'Create Endpoint'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Access Control</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage API endpoints and user access permissions
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          <button
            onClick={() => setShowForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Create Endpoint</span>
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="flex items-center">
            <Key className="w-8 h-8 text-blue-600 dark:text-blue-400" />
            <div className="ml-4">
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{endpoints.length}</p>
              <p className="text-gray-600 dark:text-gray-400">Total Endpoints</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="flex items-center">
            <Shield className="w-8 h-8 text-green-600 dark:text-green-400" />
            <div className="ml-4">
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {endpoints.filter(ep => ep.active).length}
              </p>
              <p className="text-gray-600 dark:text-gray-400">Active Endpoints</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="flex items-center">
            <Users className="w-8 h-8 text-purple-600 dark:text-purple-400" />
            <div className="ml-4">
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{users.length}</p>
              <p className="text-gray-600 dark:text-gray-400">Total Users</p>
            </div>
          </div>
        </div>
      </div>

      {/* Endpoints Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Endpoint
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Method
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Users
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Cameras
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {endpoints.map((endpoint) => (
                <tr key={endpoint.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4">
                    <div>
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {endpoint.name}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400 font-mono">
                        {endpoint.endpoint}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs rounded-full font-mono ${
                      endpoint.method === 'GET' ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300' :
                      endpoint.method === 'POST' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300' :
                      endpoint.method === 'PUT' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300' :
                      'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300'
                    }`}>
                      {endpoint.method}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                    <div className="space-y-1">
                      {endpoint.allowedUsers.slice(0, 2).map(userId => (
                        <div key={userId} className="text-xs">{getUserName(userId)}</div>
                      ))}
                      {endpoint.allowedUsers.length > 2 && (
                        <div className="text-xs text-gray-500">+{endpoint.allowedUsers.length - 2} more</div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                    <div className="space-y-1">
                      {endpoint.allowedCameras.slice(0, 2).map(cameraId => (
                        <div key={cameraId} className="text-xs">{getCameraName(cameraId)}</div>
                      ))}
                      {endpoint.allowedCameras.length > 2 && (
                        <div className="text-xs text-gray-500">+{endpoint.allowedCameras.length - 2} more</div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      endpoint.active 
                        ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300'
                        : 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-300'
                    }`}>
                      {endpoint.active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end space-x-2">
                      <button
                        onClick={() => {
                          setEditingEndpoint(endpoint);
                          setShowForm(true);
                        }}
                        className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => {
                          if (confirm('Are you sure you want to delete this endpoint?')) {
                            setEndpoints(prev => prev.filter(ep => ep.id !== endpoint.id));
                          }
                        }}
                        className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {showForm && (
        <EndpointForm
          endpoint={editingEndpoint}
          onClose={() => {
            setShowForm(false);
            setEditingEndpoint(null);
          }}
        />
      )}
    </div>
  );
};

export default AccessControlView;