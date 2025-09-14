import api from './api';
import { API_URLS } from './urls';
import { handleApiError, logError } from './errorHandler';

export interface AdminPanel {
  id: number;
  name: string;
  description: string;
  status: string;
  some_critical_field: string;
  created_at?: string;
  updated_at?: string;
}

export interface AdminPanelCreate {
  name: string;
  description: string;
  status: string;
  some_critical_field: string;
}

export interface AdminPanelUpdate {
  name?: string;
  description?: string;
  status?: string;
  some_critical_field?: string;
}

export interface ApiResponse {
  success: boolean;
  message?: string;
  error?: string;
  data?: Record<string, string | number | boolean | undefined>;
}

export interface CSRFResponse {
  csrfToken: string;
}

export interface SystemHealth {
  status: 'healthy' | 'warning' | 'critical';
  services: {
    database: boolean;
    cache: boolean;
    storage: boolean;
    external_apis: boolean;
  };
  uptime: number;
  memory_usage: number;
  cpu_usage: number;
  disk_usage: number;
  last_check: string;
}

export interface SystemLog {
  id: string;
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  message: string;
  timestamp: string;
  source: string;
  user_id?: string;
  ip_address?: string;
  user_agent?: string;
}

export interface SystemLogsResponse {
  logs: SystemLog[];
  total: number;
  page: number;
  page_size: number;
}

export interface UserActivity {
  id: string;
  user_id: string;
  username: string;
  action: string;
  resource: string;
  resource_id?: string;
  ip_address: string;
  user_agent: string;
  timestamp: string;
  success: boolean;
  details?: Record<string, string | number | boolean | undefined>;
}

export interface UserActivityResponse {
  activities: UserActivity[];
  total: number;
  page: number;
  page_size: number;
}

export interface SystemStats {
  total_users: number;
  active_users: number;
  total_cameras: number;
  online_cameras: number;
  total_recordings: number;
  total_storage_gb: number;
  system_load: number;
  memory_usage_percent: number;
  disk_usage_percent: number;
  last_24h_requests: number;
  last_24h_errors: number;
}

export interface BackupInfo {
  id: string;
  filename: string;
  size_bytes: number;
  created_at: string;
  backup_type: 'full' | 'incremental' | 'database' | 'files';
  status: 'completed' | 'in_progress' | 'failed';
  description?: string;
}

export interface BackupListResponse {
  backups: BackupInfo[];
  total: number;
}

export interface RestoreRequest {
  backup_id: string;
  restore_type: 'full' | 'database' | 'files';
  confirm_destructive: boolean;
}

class AdminService {
  /**
   * Get all admin panels
   */
  async getPanels(): Promise<AdminPanel[]> {
    try {
      const response = await api.get(API_URLS.ADMIN.PANELS.LIST);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AdminService.getPanels');
      throw serviceError;
    }
  }

  /**
   * Get admin panel by ID
   */
  async getPanel(panelId: string | number): Promise<AdminPanel> {
    try {
      const response = await api.get(API_URLS.ADMIN.PANELS.GET_PANEL(panelId));
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AdminService.getPanel');
      throw serviceError;
    }
  }

  /**
   * Create new admin panel
   */
  async createPanel(panelData: AdminPanelCreate): Promise<AdminPanel> {
    try {
      const response = await api.post(API_URLS.ADMIN.PANELS.CREATE, panelData);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AdminService.createPanel');
      throw serviceError;
    }
  }

  /**
   * Update admin panel
   */
  async updatePanel(panelId: string | number, panelData: AdminPanelUpdate): Promise<AdminPanel> {
    try {
      const response = await api.put(API_URLS.ADMIN.PANELS.GET_PANEL(panelId), panelData);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AdminService.updatePanel');
      throw serviceError;
    }
  }

  /**
   * Delete admin panel
   */
  async deletePanel(panelId: string | number): Promise<ApiResponse> {
    try {
      const response = await api.delete(API_URLS.ADMIN.PANELS.DELETE_PANEL(panelId));
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AdminService.deletePanel');
      throw serviceError;
    }
  }

  /**
   * Get CSRF token
   */
  async getCSRFToken(): Promise<CSRFResponse> {
    try {
      const response = await api.get(API_URLS.ADMIN.CSRF_TOKEN);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AdminService.getCSRFToken');
      throw serviceError;
    }
  }

  // Note: The following methods use endpoints that are in the MISSING_ENDPOINTS section
  // These would need to be implemented in the backend first
  
  /**
   * Get system health status (MISSING ENDPOINT)
   */
  async getSystemHealth(): Promise<SystemHealth> {
    try {
      // This endpoint doesn't exist in the backend yet
      const response = await api.get('/admin/system/health/');
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AdminService.getSystemHealth');
      throw serviceError;
    }
  }

  /**
   * Get system logs with pagination (MISSING ENDPOINT)
   */
  async getSystemLogs(page: number = 1, pageSize: number = 50, level?: string): Promise<SystemLogsResponse> {
    try {
      const params: Record<string, string> = {
        page: page.toString(),
        page_size: pageSize.toString()
      };
      if (level) params.level = level;

      // This endpoint doesn't exist in the backend yet
      const response = await api.get('/admin/system/logs/', { params });
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AdminService.getSystemLogs');
      throw serviceError;
    }
  }

  /**
   * Clear system logs (MISSING ENDPOINT)
   */
  async clearSystemLogs(olderThanDays?: number): Promise<ApiResponse> {
    try {
      const params: Record<string, string> = {};
      if (olderThanDays) params.older_than_days = olderThanDays.toString();

      // This endpoint doesn't exist in the backend yet
      const response = await api.post('/admin/system/logs/clear/', params);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AdminService.clearSystemLogs');
      throw serviceError;
    }
  }

  /**
   * Get user activity logs (MISSING ENDPOINT)
   */
  async getUserActivity(page: number = 1, pageSize: number = 50, userId?: string): Promise<UserActivityResponse> {
    try {
      const params: Record<string, string> = {
        page: page.toString(),
        page_size: pageSize.toString()
      };
      if (userId) params.user_id = userId;

      // This endpoint doesn't exist in the backend yet
      const response = await api.get('/admin/system/user-activity/', { params });
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AdminService.getUserActivity');
      throw serviceError;
    }
  }

  /**
   * Get system statistics (MISSING ENDPOINT)
   */
  async getSystemStats(): Promise<SystemStats> {
    try {
      // This endpoint doesn't exist in the backend yet
      const response = await api.get('/admin/system/stats/');
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AdminService.getSystemStats');
      throw serviceError;
    }
  }

  /**
   * Create system backup (MISSING ENDPOINT)
   */
  async backupSystem(backupType: 'full' | 'incremental' | 'database' | 'files', description?: string): Promise<ApiResponse> {
    try {
      // This endpoint doesn't exist in the backend yet
      const response = await api.post('/admin/system/backup/', {
        backup_type: backupType,
        description,
      });
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AdminService.backupSystem');
      throw serviceError;
    }
  }

  /**
   * Restore system from backup (MISSING ENDPOINT)
   */
  async restoreSystem(restoreRequest: RestoreRequest): Promise<ApiResponse> {
    try {
      // This endpoint doesn't exist in the backend yet
      const response = await api.post('/admin/system/restore/', restoreRequest);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AdminService.restoreSystem');
      throw serviceError;
    }
  }

  /**
   * Get list of available backups (MISSING ENDPOINT)
   */
  async getBackupList(): Promise<BackupListResponse> {
    try {
      // This endpoint doesn't exist in the backend yet
      const response = await api.get('/admin/system/backups/');
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AdminService.getBackupList');
      throw serviceError;
    }
  }

  /**
   * Delete backup (MISSING ENDPOINT)
   */
  async deleteBackup(backupId: string | number): Promise<ApiResponse> {
    try {
      // This endpoint doesn't exist in the backend yet
      const response = await api.delete(`/admin/system/backups/${backupId}/`);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AdminService.deleteBackup');
      throw serviceError;
    }
  }

  // Custom admin endpoints that exist in the backend
  async viewDetails(id: number): Promise<unknown> {
    try {
      const response = await api.get(API_URLS.ADMIN.CUSTOM.VIEW_DETAILS(id));
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AdminService.viewDetails');
      throw serviceError;
    }
  }

  async processItem(id: number): Promise<ApiResponse> {
    try {
      const response = await api.post(API_URLS.ADMIN.CUSTOM.PROCESS_ITEM(id));
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AdminService.processItem');
      throw serviceError;
    }
  }
}

export default new AdminService();
