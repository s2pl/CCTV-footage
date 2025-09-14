import React, { useState } from 'react';
import { Plus, Edit, Trash2, Clock, Video, CheckCircle, X, AlertCircle, Filter, Download, RefreshCw, Power, PowerOff } from 'lucide-react';
import { RecordingSchedule } from '../../services/types';
import { useCCTV } from '../../hooks/useCCTV';
import ScheduleForm from './ScheduleForm';

const ScheduleView: React.FC = () => {
  const { schedules, scheduleStats, createSchedule, updateSchedule, deleteSchedule, activateSchedule, deactivateSchedule, cameras, error, clearError, loading } = useCCTV();
  const [showScheduleForm, setShowScheduleForm] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState<RecordingSchedule | null>(null);
  const [filterType, setFilterType] = useState<string>('all');
  const [filterCamera, setFilterCamera] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [success, setSuccess] = useState<string | null>(null);

  // Ensure cameras and schedules are arrays before using array methods
  const camerasArray = Array.isArray(cameras) ? cameras : [];
  const schedulesArray = Array.isArray(schedules) ? schedules : [];

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'continuous': return <Video className="w-4 h-4" />;
      case 'once': return <Clock className="w-4 h-4" />;
      case 'daily': return <RefreshCw className="w-4 h-4" />;
      case 'weekly': return <RefreshCw className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

    // Helper function to check if a one-time schedule is expired
  const isScheduleExpired = (schedule: RecordingSchedule) => {
    // Only check expiration for one-time schedules
    if (schedule.schedule_type !== 'once' || !schedule.end_date) {
      return false;
    }
    
    try {
      const today = new Date();
      const endDate = new Date(schedule.end_date);
      
      // Ensure we have valid dates
      if (isNaN(today.getTime()) || isNaN(endDate.getTime())) {
        console.warn('Invalid date found in schedule:', schedule.id, schedule.end_date);
        return false;
      }
      
      // Reset time to start of day for accurate date comparison
      today.setHours(0, 0, 0, 0);
      endDate.setHours(0, 0, 0, 0);
      
      // Schedule is expired if end date is before today
      const isExpired = endDate < today;
      
      // Debug logging for testing (remove in production)
      if (process.env.NODE_ENV === 'development' && isExpired) {
        console.log(`Schedule "${schedule.name}" is expired. End date: ${schedule.end_date}, Today: ${today.toISOString().split('T')[0]}`);
      }
      
      return isExpired;
    } catch (error) {
      console.error('Error checking schedule expiration:', error);
      return false;
    }
  };

  // Helper function to get schedule status display info
  const getScheduleStatus = (schedule: RecordingSchedule) => {
    if (isScheduleExpired(schedule)) {
      return {
        text: 'Expired',
        className: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300'
      };
    }
    
    if (schedule.is_active) {
      return {
        text: 'Active',
        className: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300'
      };
    }
    
    return {
      text: 'Inactive',
      className: 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-300'
    };
  };

  const getTypeColor = (type: string, schedule?: RecordingSchedule) => {
    // Check if schedule is expired for one-time schedules
    if (schedule && isScheduleExpired(schedule)) {
      return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300';
    }
    
    switch (type) {
      case 'continuous': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300';
      case 'once': return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300';
      case 'daily': return 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-300';
      case 'weekly': return 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-300';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
    }
  };

  const handleScheduleSubmit = async (scheduleData: Omit<RecordingSchedule, 'id'>) => {
    try {
      if (editingSchedule) {
        await updateSchedule(editingSchedule.id, scheduleData);
        setSuccess('Schedule updated successfully!');
      } else {
        await createSchedule(scheduleData);
        setSuccess('Schedule created successfully!');
      }
      setShowScheduleForm(false);
      setEditingSchedule(null);
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch {
      // Error is handled by the useData hook
    }
  };

  const handleToggleScheduleStatus = async (schedule: RecordingSchedule) => {
    try {
      if (schedule.is_active) {
        await deactivateSchedule(schedule.id);
        setSuccess(`Schedule '${schedule.name}' deactivated successfully!`);
      } else {
        await activateSchedule(schedule.id);
        setSuccess(`Schedule '${schedule.name}' activated successfully!`);
      }
      setTimeout(() => setSuccess(null), 3000);
    } catch {
      // Error is handled by the useData hook
    }
  };

  const handleEditSchedule = (schedule: RecordingSchedule) => {
    setEditingSchedule(schedule);
    setShowScheduleForm(true);
  };

  const handleDeleteSchedule = async (scheduleId: string) => {
    if (window.confirm('Are you sure you want to delete this schedule?')) {
      try {
        await deleteSchedule(scheduleId);
        setSuccess('Schedule deleted successfully!');
        setTimeout(() => setSuccess(null), 3000);
      } catch {
        // Error is handled by the useData hook
      }
    }
  };

  const handleExportSchedules = () => {
    const exportData = {
      schedules: filteredSchedules,
      exportDate: new Date().toISOString(),
      filters: {
        type: filterType,
        camera: filterCamera,
        status: filterStatus
      }
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `schedules_export_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    setSuccess('Schedules exported successfully!');
    setTimeout(() => setSuccess(null), 3000);
  };

  // Filter schedules based on current filters
  const filteredSchedules = schedulesArray.filter(schedule => {
    const matchesType = filterType === 'all' || schedule.schedule_type === filterType;
    const matchesCamera = filterCamera === 'all' || schedule.camera === filterCamera;
    
    let matchesStatus = true;
    if (filterStatus === 'enabled') {
      matchesStatus = schedule.is_active && !isScheduleExpired(schedule);
    } else if (filterStatus === 'disabled') {
      matchesStatus = !schedule.is_active && !isScheduleExpired(schedule);
    } else if (filterStatus === 'expired') {
      matchesStatus = isScheduleExpired(schedule);
    }
    // if filterStatus === 'all', matchesStatus remains true
    
    return matchesType && matchesCamera && matchesStatus;
  });

  // Get schedule statistics (enhanced with API data)
  const getScheduleStats = () => {
    const total = scheduleStats?.total_schedules || schedulesArray.length;
    const active = scheduleStats?.active_schedules || schedulesArray.filter(s => s.is_active && !isScheduleExpired(s)).length;
    const expired = schedulesArray.filter(s => isScheduleExpired(s)).length;
    const inactive = total - active - expired;
    const once = schedulesArray.filter(s => s.schedule_type === 'once').length;
    const daily = schedulesArray.filter(s => s.schedule_type === 'daily').length;
    const weekly = schedulesArray.filter(s => s.schedule_type === 'weekly').length;
    const continuous = schedulesArray.filter(s => s.schedule_type === 'continuous').length;
    
    return { total, active, inactive, expired, once, daily, weekly, continuous };
  };

  const stats = getScheduleStats();



  const handleCloseForm = () => {
    setShowScheduleForm(false);
    setEditingSchedule(null);
  };

  // Show loading state while data is being fetched
  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Recording Schedules</h1>
          <p className="text-gray-600 dark:text-gray-400">Manage automated recording schedules for your cameras</p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500 dark:text-gray-400">Loading schedules...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Recording Schedules</h1>
          <p className="text-gray-600 dark:text-gray-400">Manage automated recording schedules for your cameras</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleExportSchedules}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            <span>Export</span>
          </button>
          <button 
            onClick={() => setShowScheduleForm(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            New Schedule
          </button>
        </div>
      </div>

      {/* Error/Success Messages */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 rounded-lg flex items-center justify-between">
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 mr-2" />
            {error}
          </div>
          <button onClick={clearError} className="text-red-500 hover:text-red-700">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
      {success && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-300 px-4 py-3 rounded-lg flex items-center justify-between">
          <div className="flex items-center">
            <CheckCircle className="w-5 h-5 mr-2" />
            {success}
          </div>
          <button onClick={() => setSuccess(null)} className="text-green-500 hover:text-green-700">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Statistics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-7 gap-4">
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 text-center">
          <div className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total}</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Total</div>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 text-center">
          <div className="text-2xl font-bold text-green-600">{stats.active}</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Active</div>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 text-center">
          <div className="text-2xl font-bold text-red-600">{stats.expired}</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Expired</div>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 text-center">
          <div className="text-2xl font-bold text-green-600">{stats.once}</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">One-time</div>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 text-center">
          <div className="text-2xl font-bold text-purple-600">{stats.daily}</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Daily</div>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 text-center">
          <div className="text-2xl font-bold text-orange-600">{stats.weekly}</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Weekly</div>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 text-center">
          <div className="text-2xl font-bold text-blue-600">{stats.continuous}</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Continuous</div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex flex-col lg:flex-row gap-4">
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Filters:</span>
          </div>
          
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Types</option>
            <option value="continuous">Continuous</option>
            <option value="once">One-time</option>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
          </select>
          
          <select
            value={filterCamera}
            onChange={(e) => setFilterCamera(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Cameras</option>
            {camerasArray.map(camera => (
              <option key={camera.id} value={camera.id}>{camera.name}</option>
            ))}
          </select>
          
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Status</option>
            <option value="enabled">Enabled</option>
            <option value="disabled">Disabled</option>
            <option value="expired">Expired</option>
          </select>
          
          <button
            onClick={() => {
              setFilterType('all');
              setFilterCamera('all');
              setFilterStatus('all');
            }}
            className="px-3 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>



      {/* Schedule List */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              All Schedules ({filteredSchedules.length})
            </h3>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Schedule
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Camera
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Time
                  </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Days
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {filteredSchedules.map(schedule => (
                  <tr key={schedule.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {schedule.name}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          ID: {schedule.id.substring(0, 8)}...
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {schedule.camera_name || 'Unknown Camera'}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          {schedule.camera}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                      <div className={`p-2 rounded-lg ${getTypeColor(schedule.schedule_type, schedule)} mr-2`}>
                          {getTypeIcon(schedule.schedule_type)}
                        </div>
                      <div className="flex flex-col">
                        <span className="text-sm font-medium text-gray-900 dark:text-white capitalize">
                          {schedule.schedule_type}
                        </span>
                        {isScheduleExpired(schedule) && (
                          <span className="text-xs text-red-600 dark:text-red-400 font-medium">
                            Expired
                          </span>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm text-gray-900 dark:text-white">
                        {schedule.start_time} - {schedule.end_time}
                      </div>
                      {schedule.start_date && schedule.end_date && (
                        <div className={`text-xs ${
                          isScheduleExpired(schedule) 
                            ? 'text-red-600 dark:text-red-400' 
                            : 'text-gray-500 dark:text-gray-400'
                        }`}>
                          {schedule.start_date} to {schedule.end_date}
                          {isScheduleExpired(schedule) && (
                            <span className="ml-1 font-medium">(Expired)</span>
                          )}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900 dark:text-white">
                      {schedule.days_of_week && schedule.days_of_week.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {schedule.days_of_week.map(day => (
                            <span key={day} className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-xs rounded">
                              {typeof day === 'string' ? day.slice(0, 3) : day}
                      </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-gray-500 dark:text-gray-400">All days</span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {(() => {
                      const status = getScheduleStatus(schedule);
                      return (
                        <span className={`px-2 py-1 text-xs rounded-full ${status.className}`}>
                          {status.text}
                        </span>
                      );
                    })()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm text-gray-900 dark:text-white">
                          {schedule.created_at ? new Date(schedule.created_at).toLocaleDateString() : 'N/A'}
                        </div>
                        {schedule.updated_at && schedule.updated_at !== schedule.created_at && (
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            Updated: {new Date(schedule.updated_at).toLocaleDateString()}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end space-x-2">
                      <button 
                        onClick={() => handleToggleScheduleStatus(schedule)}
                        disabled={isScheduleExpired(schedule)}
                        className={`p-2 rounded-lg transition-colors ${
                          isScheduleExpired(schedule)
                            ? 'text-gray-300 cursor-not-allowed'
                            : schedule.is_active 
                              ? 'text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20'
                              : 'text-gray-400 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20'
                        }`}
                        title={
                          isScheduleExpired(schedule) 
                            ? 'Cannot activate expired schedule' 
                            : schedule.is_active 
                              ? 'Deactivate Schedule' 
                              : 'Activate Schedule'
                        }
                      >
                        {schedule.is_active ? <PowerOff className="w-4 h-4" /> : <Power className="w-4 h-4" />}
                      </button>
                        <button 
                          onClick={() => handleEditSchedule(schedule)}
                          className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                          title="Edit Schedule"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button 
                          onClick={() => handleDeleteSchedule(schedule.id)}
                          className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                          title="Delete Schedule"
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
          
          {filteredSchedules.length === 0 && (
            <div className="text-center py-12">
            <Clock className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No schedules found</h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Try adjusting your search or filter criteria, or create a new schedule.
            </p>
            <button 
              onClick={() => setShowScheduleForm(true)}
              className="mt-6 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 mx-auto"
            >
              <Plus className="w-4 h-4" />
              Create Schedule
            </button>
            </div>
          )}
        </div>

             {/* Schedule Form Modal */}
       {showScheduleForm && (
         <ScheduleForm
           schedule={editingSchedule}
           onClose={handleCloseForm}
           onSubmit={handleScheduleSubmit}
           cameras={camerasArray}
         />
       )}




    </div>
  );
};

export default ScheduleView;
