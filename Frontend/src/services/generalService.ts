import api from './api';
import { API_URLS } from './urls';
import { handleApiError, logError } from './errorHandler';

export interface Scraper {
  id: string;
  username: string;
  primary_contact: string;
  email: string;
  additional_emails: Record<string, unknown>;
  phone: string;
  additional_phones: Record<string, unknown>;
  website: string;
  bio: string;
  followers: number | null;
  following: number | null;
  posts: number | null;
  social_links: Record<string, unknown>;
  contact_methods: Record<string, unknown>;
  contact_aggregator: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

export interface CSVUploadResponse {
  success: boolean;
  message?: string;
  error?: string;
}

export interface ApiResponse {
  success: boolean;
  message?: string;
  error?: string;
  data?: unknown;
}

export interface ScraperListResponse {
  scrapers: Scraper[];
  total: number;
  page: number;
  page_size: number;
}

export interface ScraperSearchParams {
  query?: string;
  category?: string;
  page?: number;
  page_size?: number;
}

export interface ScraperStats {
  total_scrapers: number;
  active_scrapers: number;
  categories: Record<string, number>;
  total_followers: number;
  total_posts: number;
}

export interface BulkUpdateRequest {
  scraper_ids: string[];
  updates: Partial<Scraper>;
}

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

// NOTE: The General app exists but is NOT included in the main URL configuration
// To use these endpoints, you need to add the general app to config/urls.py:
// path(f'{version}{sub}/general/', include('apps.general.urls')),

class GeneralService {
  /**
   * Upload CSV file with scraper data
   * REQUIRES: General app to be added to main URLs
   */
  async uploadCSV(file: File): Promise<CSVUploadResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post(API_URLS.GENERAL.UPLOAD_CSV, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'GeneralService.uploadCSV');
      throw serviceError;
    }
  }

  /**
   * Get dashboard data
   * REQUIRES: General app to be added to main URLs
   */
  async getDashboard(): Promise<unknown> {
    try {
      const response = await api.get(API_URLS.GENERAL.DASHBOARD);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'GeneralService.getDashboard');
      throw serviceError;
    }
  }

  /**
   * Get settings
   * REQUIRES: General app to be added to main URLs
   */
  async getSettings(): Promise<unknown> {
    try {
      const response = await api.get(API_URLS.GENERAL.SETTINGS);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'GeneralService.getSettings');
      throw serviceError;
    }
  }

  /**
   * Update settings
   * REQUIRES: General app to be added to main URLs
   */
  async updateSettings(settings: Record<string, unknown>): Promise<unknown> {
    try {
      const response = await api.put(API_URLS.GENERAL.SETTINGS, settings);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'GeneralService.updateSettings');
      throw serviceError;
    }
  }

  // Note: All other methods would require the general app endpoints to be implemented
  // and added to the main URL configuration. The current general app endpoints
  // that are available are:
  // - /general/upload-csv
  // - /general/dashboard
  // - /general/settings
  
  // To activate these endpoints, add this line to config/urls.py:
  // path(f'{version}{sub}/general/', include('apps.general.urls')),
  /**
   * Check if general app is available
   */
  async isAvailable(): Promise<boolean> {
    try {
      const response = await api.get(API_URLS.GENERAL.DASHBOARD);
      return response.status === 200;
    } catch {
      // If we get a 404, the general app is not included in URLs
      return false;
    }
  }
}

export default new GeneralService();
