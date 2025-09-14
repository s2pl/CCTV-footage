import { useState, useEffect } from 'react';
import { dashboardService } from '../services';
import { DashboardAnalytics, RecentActivityResponse } from '../services/types';

interface UseDashboardResult {
  analytics: DashboardAnalytics | null;
  activity: RecentActivityResponse | null;
  loading: boolean;
  error: string | null;
  refreshDashboard: () => Promise<void>;
  refreshAnalytics: () => Promise<void>;
  refreshActivity: () => Promise<void>;
}

/**
 * Custom hook for managing dashboard data
 * @param autoRefresh Whether to automatically refresh data on mount
 * @param activityLimit Number of activity items to fetch
 * @returns Dashboard data and control functions
 */
export const useDashboard = (
  autoRefresh: boolean = true,
  activityLimit: number = 20
): UseDashboardResult => {
  const [analytics, setAnalytics] = useState<DashboardAnalytics | null>(null);
  const [activity, setActivity] = useState<RecentActivityResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshAnalytics = async () => {
    try {
      setError(null);
      const analyticsData = await dashboardService.getAnalytics();
      setAnalytics(analyticsData);
    } catch (err) {
      console.error('Error fetching analytics:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch analytics');
    }
  };

  const refreshActivity = async () => {
    try {
      setError(null);
      const activityData = await dashboardService.getRecentActivity(activityLimit);
      setActivity(activityData);
    } catch (err) {
      console.error('Error fetching activity:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch activity');
    }
  };

  const refreshDashboard = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [analyticsData, activityData] = await Promise.all([
        dashboardService.getAnalytics(),
        dashboardService.getRecentActivity(activityLimit)
      ]);
      
      setAnalytics(analyticsData);
      setActivity(activityData);
    } catch (err) {
      console.error('Error refreshing dashboard:', err);
      setError(err instanceof Error ? err.message : 'Failed to refresh dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (autoRefresh) {
      refreshDashboard();
    }
  }, [autoRefresh, activityLimit]);

  return {
    analytics,
    activity,
    loading,
    error,
    refreshDashboard,
    refreshAnalytics,
    refreshActivity,
  };
};

export default useDashboard;
