import api from './api';
import { API_URLS } from './urls';
import { handleApiError, ServiceError, logError } from './errorHandler';

export interface LoginCredentials {
  username?: string;
  email?: string;
  password: string;
}

export interface User {
  user_id: number;
  id: string; // For compatibility with existing components
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  phone_no?: string;
  avatar_url?: string;
  bio?: string;
  current_streak?: number;
  challenges_completed?: number;
  total_points?: number;
  rank?: number;
  title?: string;
  role?: string;
  active?: boolean;
  permissions?: Permission[];
  lastLogin?: string;
}

export interface Permission {
  cameraId: string;
  canView: boolean;
  canControl: boolean;
  canRecord: boolean;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
  message: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  phone_no?: string;
  role?: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirm {
  email: string;
  otp: string;
  new_password: string;
  confirm_password: string;
}

export interface UsernameCheckRequest {
  username: string;
}

export interface UsernameUpdateRequest {
  user_id: number;
  username: string;
}

export interface AvatarUpdateRequest {
  user_id: number;
  avatar: File;
}

export interface UserRoleUpdate {
  role: string;
}

export interface UserActivationUpdate {
  is_active: boolean;
}

export interface UserCreateRequest {
  username: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  phone_no?: string;
  role?: string;
}

export interface UserUpdateRequest {
  username?: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  phone_no?: string;
  role?: string;
}

export interface ApiResponse {
  message: string;
  success?: boolean;
  [key: string]: string | number | boolean | undefined;
}

export interface UserRoleResponse {
  message: string;
  user_id: number;
  role: string;
}

export interface UserActivationResponse {
  message: string;
  user_id: number;
  is_active: boolean;
}

export interface UserDeleteResponse {
  message: string;
  success: boolean;
}

// Error response interface for better type safety
interface ApiErrorResponse {
  response?: {
    status?: number;
    data?: unknown;
  };
}

export interface PasswordResetResponse {
  message: string;
  email: string;
}

class AuthService {
  // Login user
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    try {
      console.log('Sending login credentials:', credentials);
      
      // Ensure we're sending the data in the correct format
      let payload: Record<string, string>;
      
      if (credentials.email) {
        payload = {
          email: credentials.email,
          password: credentials.password
        };
      } else if (credentials.username) {
        payload = {
          username: credentials.username,
          password: credentials.password
        };
      } else {
        throw new ServiceError('Either email or username must be provided');
      }
      
      console.log('Sending payload to backend:', payload);
      
      const response = await api.post(API_URLS.USERS.AUTH.LOGIN, payload);
      const data = response.data;
      
      // Store tokens and user data
      localStorage.setItem('accessToken', data.access_token);
      localStorage.setItem('refreshToken', data.refresh_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      
      return data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AuthService.login');
      throw serviceError;
    }
  }

  // Logout
  async logout(): Promise<void> {
    try {
      await api.post(API_URLS.USERS.AUTH.LOGOUT);
    } catch (error) {
      // Even if logout fails on server, clear local storage
      console.warn('Server logout failed:', error);
    } finally {
      this.clearAuthData();
    }
  }

  // Clear authentication data
  private clearAuthData(): void {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
    localStorage.removeItem('userRole');
  }

  // Change password
  async changePassword(oldPassword: string, newPassword: string): Promise<{ message: string }> {
    try {
      const response = await api.post(API_URLS.USERS.AUTH.CHANGE_PASSWORD, {
        old_password: oldPassword,
        new_password: newPassword
      });
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AuthService.changePassword');
      throw serviceError;
    }
  }

  // Refresh token
  async refreshToken(): Promise<AuthResponse> {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) {
        throw new ServiceError('No refresh token available');
      }

      console.log('Attempting to refresh token...');
      const response = await api.post(API_URLS.USERS.AUTH.REFRESH, {
        refresh_token: refreshToken,
      });

      const data = response.data;
      
      // Update stored tokens
      localStorage.setItem('accessToken', data.access_token);
      localStorage.setItem('refreshToken', data.refresh_token);
      
      console.log('Token refreshed successfully');
      return data;
    } catch (error: unknown) {
      console.error('Token refresh failed:', error);
      
      // Only clear tokens if it's a critical error (invalid refresh token)
      if (error && typeof error === 'object' && 'response' in error) {
        const apiError = error as ApiErrorResponse;
        if (apiError.response?.status === 401 || apiError.response?.status === 400) {
          console.log('Clearing invalid tokens due to refresh failure');
          localStorage.removeItem('accessToken');
          localStorage.removeItem('refreshToken');
          localStorage.removeItem('user');
        }
      }
      
      const serviceError = handleApiError(error);
      logError(serviceError, 'AuthService.refreshToken');
      throw serviceError;
    }
  }

  // Request password reset
  async requestPasswordReset(email: string): Promise<PasswordResetResponse> {
    try {
      const response = await api.post(API_URLS.USERS.AUTH.REQUEST_PASSWORD_RESET, { email });
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AuthService.requestPasswordReset');
      throw serviceError;
    }
  }

  // Verify password reset with OTP
  async verifyPasswordReset(email: string, otp: string, newPassword: string): Promise<{ message: string }> {
    try {
      const response = await api.post(API_URLS.USERS.AUTH.VERIFY_PASSWORD_RESET, {
        email,
        otp,
        new_password: newPassword
      });
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AuthService.verifyPasswordReset');
      throw serviceError;
    }
  }

  // Get current user profile
  async getProfile(): Promise<User> {
    try {
      const response = await api.get(API_URLS.USERS.GET_PROFILE);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AuthService.getProfile');
      throw serviceError;
    }
  }

  // Update current user profile
  async updateProfile(profileData: Partial<User>): Promise<User> {
    try {
      const response = await api.put(API_URLS.USERS.UPDATE_PROFILE, profileData);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AuthService.updateProfile');
      throw serviceError;
    }
  }

  // Get user activities
  async getActivities(): Promise<Array<{
    id: string;
    action: string;
    resource: string;
    resource_id?: string;
    ip_address: string;
    user_agent: string;
    timestamp: string;
    success: boolean;
    error_message?: string;
  }>> {
    try {
      const response = await api.get(API_URLS.USERS.GET_ACTIVITIES);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AuthService.getActivities');
      throw serviceError;
    }
  }

  // Get user sessions
  async getSessions(): Promise<Array<{
    id: string;
    user_agent: string;
    ip_address: string;
    created_at: string;
    last_activity: string;
    is_current: boolean;
  }>> {
    try {
      const response = await api.get(API_URLS.USERS.GET_SESSIONS);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AuthService.getSessions');
      throw serviceError;
    }
  }

  // Revoke all sessions
  async revokeAllSessions(): Promise<{ message: string }> {
    try {
      const response = await api.post(API_URLS.USERS.REVOKE_ALL_SESSIONS);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'AuthService.revokeAllSessions');
      throw serviceError;
    }
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    const token = localStorage.getItem('accessToken');
    if (!token) return false;
    
    try {
      // Check if token is expired
      const tokenData = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Date.now() / 1000;
      
      if (tokenData.exp < currentTime) {
        console.log('Token expired, clearing auth data');
        this.clearAuthData();
        return false;
      }
      
      return true;
    } catch (error: unknown) {
      console.error('Error parsing token:', error);
      this.clearAuthData();
      return false;
    }
  }

  // Check if token is close to expiration (within specified minutes)
  isTokenExpiringSoon(minutes: number = 5): boolean {
    const token = localStorage.getItem('accessToken');
    if (!token) return true;
    
    try {
      const tokenData = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Date.now() / 1000;
      const timeUntilExpiry = tokenData.exp - currentTime;
      
      return timeUntilExpiry < (minutes * 60);
    } catch (error: unknown) {
      console.error('Error checking token expiration:', error);
      return true;
    }
  }

  // Get current user
  getCurrentUser(): User | null {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  }

  // Get access token
  getAccessToken(): string | null {
    return localStorage.getItem('accessToken');
  }

  // Get refresh token
  getRefreshToken(): string | null {
    return localStorage.getItem('refreshToken');
  }


}

export default new AuthService();
