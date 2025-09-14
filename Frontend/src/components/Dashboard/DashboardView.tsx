import React from 'react';
import { Camera, Users, Eye, Activity, AlertTriangle, CheckCircle, TrendingUp } from 'lucide-react';
import { useCCTV } from '../../hooks/useCCTV';
import { useUsers } from '../../hooks/useUsers';
import { useDashboard } from '../../hooks/useDashboard';
import DashboardCharts from './DashboardCharts';
// import AuthDebug from '../Debug/AuthDebug';

interface DashboardViewProps {
  onNavigate?: (view: string) => void;
}

const DashboardView: React.FC<DashboardViewProps> = () => {
  const { cameras, loading: camerasLoading } = useCCTV();
  const { users, loading: usersLoading } = useUsers();
  const { analytics, activity, loading: dashboardLoading, error: dashboardError, refreshDashboard } = useDashboard();

  // Ensure cameras and users are arrays before using filter
  const camerasArray = Array.isArray(cameras) ? cameras : [];
  const usersArray = Array.isArray(users) ? users : [];

  const onlineCameras = camerasArray.filter(cam => cam.status === 'online').length;
  const activeUsers = usersArray.filter(user => user.active).length;
  const recordingCameras = camerasArray.filter(cam => cam.auto_record).length;

  // System metrics from analytics

  const systemMetrics = analytics?.system_metrics;

  const stats = [
    {
      title: 'Total Cameras',
      value: systemMetrics?.total_cameras || camerasArray.length,
      icon: Camera,
      color: 'blue',
      change: '+2 this month',
      trend: 'up'
    },
    {
      title: 'Online Cameras',
      value: systemMetrics?.online_cameras || onlineCameras,
      icon: CheckCircle,
      color: 'green',
      change: systemMetrics?.uptime_percentage ? `${systemMetrics.uptime_percentage}% uptime` : 
              (camerasArray.length > 0 ? `${Math.round((onlineCameras / camerasArray.length) * 100)}% uptime` : '0% uptime'),
      trend: 'stable'
    },
    {
      title: 'Active Users',
      value: activeUsers,
      icon: Users,
      color: 'purple',
      change: '+1 this week',
      trend: 'up'
    },
    {
      title: 'Total Recordings',
      value: systemMetrics?.total_recordings || recordingCameras,
      icon: Eye,
      color: 'orange',
      change: systemMetrics?.active_schedules ? `${systemMetrics.active_schedules} active schedules` : 
              (camerasArray.length > 0 ? `${Math.round((recordingCameras / camerasArray.length) * 100)}% active` : '0% active'),
      trend: 'stable'
    }
  ];

  // Convert recent activity to alert format
  const recentAlerts = activity?.activities?.slice(0, 4).map(act => {
    const timeAgo = new Date(act.timestamp).toLocaleString();
    let type = 'info';
    
    if (act.type === 'recording' && act.status === 'active') type = 'success';
    else if (act.type === 'camera' && act.status === 'active') type = 'success';
    else if (act.type === 'camera' && act.status === 'error') type = 'error';
    else if (act.type === 'schedule' && act.status === 'active') type = 'success';
    else if (act.type === 'schedule' && act.status === 'inactive') type = 'warning';
    
    return {
      id: act.id,
      type,
      message: act.title,
      time: timeAgo,
      camera: act.camera_name
    };
  }) || [
    { id: '1', type: 'info', message: 'No recent activity available', time: 'N/A', camera: '' },
  ];

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'warning': return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case 'info': return <Activity className="w-4 h-4 text-blue-500" />;
      case 'success': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error': return <AlertTriangle className="w-4 h-4 text-red-500" />;
      default: return <Activity className="w-4 h-4 text-gray-500" />;
    }
  };

  const getAlertColor = (type: string) => {
    switch (type) {
      case 'warning': return 'border-l-yellow-500 bg-yellow-50 dark:bg-yellow-900/10';
      case 'info': return 'border-l-blue-500 bg-blue-50 dark:bg-blue-900/10';
      case 'success': return 'border-l-green-500 bg-green-50 dark:bg-green-900/10';
      case 'error': return 'border-l-red-500 bg-red-50 dark:bg-red-900/10';
      default: return 'border-l-gray-500 bg-gray-50 dark:bg-gray-900/10';
    }
  };

  // const handleQuickAction = (action: string) => {
  //   if (onNavigate) {
  //     onNavigate(action);
  //   }
  // };

  // Show loading state while data is being fetched
  if (camerasLoading || usersLoading || dashboardLoading) {
    return (
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Monitor your security system status and performance
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500 dark:text-gray-400">Loading dashboard data...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-h-screen overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600 scrollbar-track-transparent">
      <div>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Monitor your security system status and performance
            </p>
          </div>
          <button
            onClick={refreshDashboard}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            disabled={dashboardLoading}
          >
            {dashboardLoading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
        
        {dashboardError && (
          <div className="mt-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 rounded-lg">
            <p className="font-medium">Dashboard Error</p>
            <p className="text-sm">{dashboardError}</p>
            <button
              onClick={refreshDashboard}
              className="mt-2 text-sm underline hover:no-underline"
            >
              Try again
            </button>
          </div>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 overflow-x-auto">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div
              key={index}
              className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    {stat.title}
                  </p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
                    {stat.value}
                  </p>
                  <div className="flex items-center mt-2">
                    <span className={`text-sm text-${stat.color}-600 dark:text-${stat.color}-400`}>
                      {stat.change}
                    </span>
                    {stat.trend === 'up' && <TrendingUp className="w-4 h-4 ml-2 text-green-500" />}
                  </div>
                </div>
                <div className={`p-3 bg-${stat.color}-100 dark:bg-${stat.color}-900/20 rounded-full`}>
                  <Icon className={`w-6 h-6 text-${stat.color}-600 dark:text-${stat.color}-400`} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Camera and System Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 overflow-x-auto">
        {/* Camera Status */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Camera Status
          </h3>
          <div className="space-y-4 max-h-64 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600 scrollbar-track-transparent">
            {camerasArray.map((camera) => (
              <div key={camera.id} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${
                    camera.status === 'online' ? 'bg-green-500' :
                    camera.status === 'offline' ? 'bg-red-500' : 'bg-yellow-500'
                  }`} />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {camera.name}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {camera.location}
                    </p>
                  </div>
                </div>
                <span className={`px-2 py-1 text-xs rounded-full capitalize ${
                  camera.status === 'online' ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300' :
                  camera.status === 'offline' ? 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300' :
                  'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300'
                }`}>
                  {camera.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Alerts */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Recent Alerts
          </h3>
          <div className="space-y-3 max-h-64 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600 scrollbar-track-transparent">
            {recentAlerts.map((alert) => (
              <div key={alert.id} className={`p-3 rounded-lg border-l-4 ${getAlertColor(alert.type)}`}>
                <div className="flex items-start gap-3">
                  {getAlertIcon(alert.type)}
                  <div className="flex-1">
                    <p className="text-sm text-gray-900 dark:text-white">{alert.message}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{alert.time}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Dashboard Charts */}
      {analytics && <DashboardCharts analytics={analytics} />}

      {/* Authentication Debug - Only show in development */}
      {/* {process.env.NODE_ENV === 'development' && (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700 mb-6">
          <AuthDebug />
        </div>
      )} */}

      {/* Quick Actions */}
      {/* <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Quick Actions
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button 
            onClick={() => handleQuickAction('cameras')}
            className="p-4 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-center cursor-pointer"
          >
            <Camera className="w-6 h-6 mx-auto mb-2 text-blue-600" />
            <span className="text-sm font-medium text-gray-900 dark:text-white">Add Camera</span>
          </button>
          <button 
            onClick={() => handleQuickAction('users')}
            className="p-4 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-center cursor-pointer"
          >
            <Users className="w-6 h-6 mx-auto mb-2 text-purple-600" />
            <span className="text-sm font-medium text-gray-900 dark:text-white">Add User</span>
          </button>
          <button 
            onClick={() => handleQuickAction('schedule')}
            className="p-4 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-center cursor-pointer"
          >
            <Clock className="w-6 h-6 mx-auto mb-2 text-orange-600" />
            <span className="text-sm font-medium text-gray-900 dark:text-white">Schedule</span>
          </button>
          <button 
            onClick={() => handleQuickAction('access-control')}
            className="p-4 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-center cursor-pointer"
          >
            <Shield className="w-6 h-6 mx-auto mb-2 text-green-600" />
            <span className="text-sm font-medium text-gray-900 dark:text-white">Access Control</span>
          </button>
        </div>
      </div> */}
    </div>
  );
};

export default DashboardView;