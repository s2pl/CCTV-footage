import api from './api';
import { API_URLS } from './urls';
import { DashboardAnalytics, RecentActivityResponse } from './types';

/**
 * Dashboard Service for retrieving analytics and activity data
 */
export class DashboardService {
  /**
   * Get dashboard analytics data including charts and metrics
   * @returns Promise with dashboard analytics data
   */
  static async getAnalytics(): Promise<DashboardAnalytics> {
    try {
      const response = await api.get(API_URLS.CCTV.DASHBOARD.GET_ANALYTICS);
      return response.data;
    } catch (error) {
      console.error('Error fetching dashboard analytics:', error);
      throw error;
    }
  }

  /**
   * Get recent system activity
   * @param limit Number of activities to retrieve (default: 20)
   * @returns Promise with recent activity data
   */
  static async getRecentActivity(limit: number = 20): Promise<RecentActivityResponse> {
    try {
      const response = await api.get(API_URLS.CCTV.DASHBOARD.GET_ACTIVITY_WITH_LIMIT(limit));
      return response.data;
    } catch (error) {
      console.error('Error fetching recent activity:', error);
      throw error;
    }
  }

  /**
   * Get system metrics only (subset of analytics)
   * @returns Promise with system metrics
   */
  static async getSystemMetrics() {
    try {
      const analytics = await this.getAnalytics();
      return analytics.system_metrics;
    } catch (error) {
      console.error('Error fetching system metrics:', error);
      throw error;
    }
  }

  /**
   * Get camera status distribution for charts
   * @returns Promise with camera status data
   */
  static async getCameraStatusDistribution() {
    try {
      const analytics = await this.getAnalytics();
      return analytics.camera_status_distribution;
    } catch (error) {
      console.error('Error fetching camera status distribution:', error);
      throw error;
    }
  }

  /**
   * Get recording activity for the last 7 days
   * @returns Promise with recording activity data
   */
  static async getRecordingActivity() {
    try {
      const analytics = await this.getAnalytics();
      return analytics.recording_activity_7_days;
    } catch (error) {
      console.error('Error fetching recording activity:', error);
      throw error;
    }
  }

  /**
   * Get hourly recording activity for today
   * @returns Promise with hourly activity data
   */
  static async getHourlyActivity() {
    try {
      const analytics = await this.getAnalytics();
      return analytics.hourly_activity_today;
    } catch (error) {
      console.error('Error fetching hourly activity:', error);
      throw error;
    }
  }

  /**
   * Get schedule type distribution
   * @returns Promise with schedule type data
   */
  static async getScheduleTypeDistribution() {
    try {
      const analytics = await this.getAnalytics();
      return analytics.schedule_type_distribution;
    } catch (error) {
      console.error('Error fetching schedule type distribution:', error);
      throw error;
    }
  }

  /**
   * Get storage usage data for the last 30 days
   * @returns Promise with storage usage data
   */
  static async getStorageUsage() {
    try {
      const analytics = await this.getAnalytics();
      return analytics.storage_usage_30_days;
    } catch (error) {
      console.error('Error fetching storage usage:', error);
      throw error;
    }
  }

  /**
   * Refresh all dashboard data (utility method)
   * @param limit Number of activities to retrieve
   * @returns Promise with all dashboard data
   */
  static async refreshDashboard(limit: number = 20) {
    try {
      const [analytics, activity] = await Promise.all([
        this.getAnalytics(),
        this.getRecentActivity(limit)
      ]);

      return {
        analytics,
        activity,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('Error refreshing dashboard:', error);
      throw error;
    }
  }
}

export default DashboardService;
