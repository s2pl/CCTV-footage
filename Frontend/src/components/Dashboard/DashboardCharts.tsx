import React from 'react';
import { DashboardAnalytics } from '../../services/types';

interface DashboardChartsProps {
  analytics: DashboardAnalytics;
}

const DashboardCharts: React.FC<DashboardChartsProps> = ({ analytics }) => {
  if (!analytics) return null;

  const { recording_activity_7_days, hourly_activity_today, schedule_type_distribution, camera_status_distribution } = analytics;

  // Simple bar chart component
  const SimpleBarChart: React.FC<{ data: Array<{ label: string; value: number }>, title: string }> = ({ data, title }) => {
    const maxValue = Math.max(...data.map(d => d.value));
    
    return (
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{title}</h3>
        <div className="space-y-3">
          {data.map((item, index) => (
            <div key={index} className="flex items-center">
              <div className="w-20 text-sm text-gray-600 dark:text-gray-400 truncate">
                {item.label}
              </div>
              <div className="flex-1 mx-3">
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${maxValue > 0 ? (item.value / maxValue) * 100 : 0}%` }}
                  />
                </div>
              </div>
              <div className="w-8 text-sm font-medium text-gray-900 dark:text-white text-right">
                {item.value}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Simple pie chart component (using CSS for basic visualization)
  const SimplePieChart: React.FC<{ data: Array<{ label: string; value: number }>, title: string }> = ({ data, title }) => {
    const total = data.reduce((sum, item) => sum + item.value, 0);
    const colors = ['bg-blue-500', 'bg-green-500', 'bg-yellow-500', 'bg-red-500', 'bg-purple-500', 'bg-indigo-500'];
    
    return (
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{title}</h3>
        <div className="space-y-3">
          {data.map((item, index) => {
            const percentage = total > 0 ? Math.round((item.value / total) * 100) : 0;
            return (
              <div key={index} className="flex items-center">
                <div className={`w-4 h-4 rounded-full ${colors[index % colors.length]} mr-3`} />
                <div className="flex-1">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">{item.label}</span>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">{item.value} ({percentage}%)</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
      {/* Recording Activity (Last 7 Days) */}
      <SimpleBarChart
        title="Recording Activity (Last 7 Days)"
        data={recording_activity_7_days.map(item => ({
          label: item.day.slice(0, 3),
          value: item.recordings
        }))}
      />

      {/* Camera Status Distribution */}
      <SimplePieChart
        title="Camera Status Distribution"
        data={camera_status_distribution.map(item => ({
          label: item.status,
          value: item.count
        }))}
      />

      {/* Schedule Type Distribution */}
      <SimplePieChart
        title="Schedule Types"
        data={schedule_type_distribution.map(item => ({
          label: item.schedule_type,
          value: item.count
        }))}
      />

      {/* Hourly Activity Today */}
      <SimpleBarChart
        title="Hourly Recording Activity (Today)"
        data={hourly_activity_today.filter((_, index) => index % 2 === 0).map(item => ({
          label: item.hour,
          value: item.recordings
        }))}
      />
    </div>
  );
};

export default DashboardCharts;
