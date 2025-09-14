import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { API_URLS } from './urls';
import { 
  USER_ROLES, 
  UserRole, 
  ROLE_HIERARCHY, 
  ROLE_CREATION_PERMISSIONS, 
  ROLE_MANAGEMENT_PERMISSIONS 
} from './hierarchyTypes';

// Re-export hierarchy types for backward compatibility
export { USER_ROLES, ROLE_HIERARCHY, ROLE_CREATION_PERMISSIONS, ROLE_MANAGEMENT_PERMISSIONS };
export type { UserRole };

// Hierarchy utility functions
export const hierarchyUtils = {
  /**
   * Check if a user can create users with a specific role
   */
  canCreateRole: (userRole: UserRole, targetRole: UserRole): boolean => {
    return ROLE_CREATION_PERMISSIONS[userRole]?.includes(targetRole) || false;
  },

  /**
   * Check if a user can manage users with a specific role
   */
  canManageRole: (userRole: UserRole, targetRole: UserRole): boolean => {
    return ROLE_MANAGEMENT_PERMISSIONS[userRole]?.includes(targetRole) || false;
  },

  /**
   * Check if a user has a higher or equal role level
   */
  hasRoleLevel: (userRole: UserRole, requiredRole: UserRole): boolean => {
    return ROLE_HIERARCHY[userRole] >= ROLE_HIERARCHY[requiredRole];
  },

  /**
   * Get all roles that a user can create
   */
  getCreatableRoles: (userRole: UserRole): UserRole[] => {
    return ROLE_CREATION_PERMISSIONS[userRole] || [];
  },

  /**
   * Get all roles that a user can manage
   */
  getManageableRoles: (userRole: UserRole): UserRole[] => {
    return ROLE_MANAGEMENT_PERMISSIONS[userRole] || [];
  },

  /**
   * Validate role assignment based on hierarchy
   */
  validateRoleAssignment: (assignerRole: UserRole, targetRole: UserRole): boolean => {
    return hierarchyUtils.canCreateRole(assignerRole, targetRole);
  }
};

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_URLS.BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Flag to prevent multiple simultaneous refresh attempts
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: string | null) => void;
  reject: (reason: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token);
    }
  });
  
  failedQueue = [];
};

// Request interceptor to add auth token and role validation
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add role validation for hierarchy-sensitive endpoints
    if (config.url && config.url.includes('/users/')) {
      const userRole = localStorage.getItem('userRole') as UserRole;
      if (userRole) {
        config.headers['X-User-Role'] = userRole;
      }
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh and role validation
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        }).catch((err) => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        const response = await axios.post(`${API_URLS.BASE}${API_URLS.TOKEN.REFRESH}`, {
          refresh: refreshToken,
        });

        const tokens = response.data;
        localStorage.setItem('accessToken', tokens.access_token);
        localStorage.setItem('refreshToken', tokens.refresh_token);

        // Process queued requests
        processQueue(null, tokens.access_token);

        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${tokens.access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError);
        
        // Process queued requests with error
        processQueue(refreshError, null);
        
        // Clear auth data and redirect to login only if it's a critical error
        const errorResponse = refreshError as { response?: { status?: number } };
        if (errorResponse?.response?.status === 401 || errorResponse?.response?.status === 400) {
          localStorage.removeItem('accessToken');
          localStorage.removeItem('refreshToken');
          localStorage.removeItem('user');
          localStorage.removeItem('userRole');
          
          // Only redirect if we're not already on the login page
          if (window.location.pathname !== '/login' && window.location.pathname !== '/') {
            window.location.href = '/login';
          }
        }
        
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // Handle role-based permission errors
    if (error.response?.status === 403) {
      const errorData = error.response.data;
      if (errorData?.error?.includes('Permission denied') || errorData?.error?.includes('role')) {
        console.error('Role-based permission error:', errorData);
        // You can add custom handling for role permission errors here
      }
    }

    return Promise.reject(error);
  }
);

// Enhanced API methods with hierarchy support
export const hierarchyApi = {
  /**
   * Create a user with role validation
   */
  createUserWithRole: async (userData: { role: UserRole; [key: string]: unknown }, creatorRole: UserRole) => {
    // Validate role assignment
    if (!hierarchyUtils.validateRoleAssignment(creatorRole, userData.role)) {
      throw new Error(`Permission denied. You cannot create users with role: ${userData.role}`);
    }
    
    return api.post(API_URLS.USERS.CREATE_USER, userData);
  },

  /**
   * Update user role with hierarchy validation
   */
  updateUserRole: async (userId: string | number, newRole: UserRole, updaterRole: UserRole) => {
    // Validate role assignment
    if (!hierarchyUtils.validateRoleAssignment(updaterRole, newRole)) {
      throw new Error(`Permission denied. You cannot assign role: ${newRole}`);
    }
    
    return api.put(API_URLS.USERS.CHANGE_USER_ROLE(userId), { role: newRole });
  },

  /**
   * Get users by role with hierarchy filtering
   */
  getUsersByRole: async (role: UserRole, requesterRole: UserRole) => {
    // Check if requester can view users of this role
    if (!hierarchyUtils.canManageRole(requesterRole, role)) {
      throw new Error(`Permission denied. You cannot view users with role: ${role}`);
    }
    
    return api.get(API_URLS.USERS.LIST_USERS, {
      params: { role }
    });
  },

  /**
   * Check if current user can perform an action on a target role
   */
  canPerformAction: (action: 'create' | 'manage' | 'view', userRole: UserRole, targetRole: UserRole): boolean => {
    switch (action) {
      case 'create':
        return hierarchyUtils.canCreateRole(userRole, targetRole);
      case 'manage':
        return hierarchyUtils.canManageRole(userRole, targetRole);
      case 'view':
        return hierarchyUtils.canManageRole(userRole, targetRole);
      default:
        return false;
    }
  }
};

export default api;
