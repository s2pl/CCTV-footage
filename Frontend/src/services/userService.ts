import api from './api';
import { API_URLS } from './urls';
import { handleApiError, logError } from './errorHandler';

export interface User {
  user_id?: number;
  id: string; // For compatibility with existing components
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  phone_no?: string;
  phone_number?: string; // Backend uses phone_number
  avatar_url?: string;
  bio?: string;
  current_streak?: number;
  challenges_completed?: number;
  total_points?: number;
  rank?: number;
  title?: string;
  role?: string;
  active?: boolean;
  is_active?: boolean; // Backend uses is_active
  is_verified?: boolean;
  permissions?: Permission[];
  lastLogin?: string;
  last_login?: string; // Backend uses last_login
  created_at?: string;
  updated_at?: string;
}

export interface Permission {
  cameraId: string;
  canView: boolean;
  canControl: boolean;
  canRecord: boolean;
}

export interface UserCreateRequest {
  username?: string;
  email: string;
  password: string;
  password_confirm: string;
  first_name?: string;
  last_name?: string;
  phone_no?: string;
  phone_number?: string; // Backend uses phone_number
  role?: string;
  bio?: string;
}

export interface UserUpdateRequest {
  username?: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  phone_no?: string;
  phone_number?: string; // Backend uses phone_number
  role?: string;
  bio?: string;
}

export interface ApiResponse {
  message: string;
  success?: boolean;
  [key: string]: string | number | boolean | undefined;
}

export interface PaginatedResponse<T> {
  items: T[];
  count: number;
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

class UserService {
  // Get all users
  async getUsers(): Promise<User[]> {
    try {
      const response = await api.get(API_URLS.USERS.LIST_USERS);
      
      // Extract users array from response
      const users = this.extractUsersFromResponse(response.data);
      
      // Map backend response to frontend User interface
      return users.map((user: unknown) => this.mapBackendUserToFrontend(user));
    } catch (error: unknown) {
      // Check if it's an authentication error
      if (error.response?.status === 401) {
        console.error('Authentication required for getUsers endpoint');
      } else if (error.response?.status === 403) {
        console.error('Admin access required for getUsers endpoint');
      }
      
      const serviceError = handleApiError(error);
      logError(serviceError, 'UserService.getUsers');
      throw serviceError;
    }
  }

  // Get user by ID
  async getUser(userId: string | number): Promise<User> {
    try {
      const response = await api.get(API_URLS.USERS.GET_USER(userId));
      return this.mapBackendUserToFrontend(response.data);
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'UserService.getUser');
      throw serviceError;
    }
  }

  // Create new user
  async createUser(userData: UserCreateRequest): Promise<User> {
    try {
      // Map frontend data to backend format
      const backendData = this.mapFrontendUserToBackend(userData);
      const response = await api.post(API_URLS.USERS.CREATE_USER, backendData);
      return this.mapBackendUserToFrontend(response.data);
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'UserService.createUser');
      throw serviceError;
    }
  }

  // Update user
  async updateUser(userId: string | number, userData: UserUpdateRequest): Promise<User> {
    try {
      // Map frontend data to backend format
      const backendData = this.mapFrontendUserToBackend(userData);
      const response = await api.put(API_URLS.USERS.UPDATE_USER(userId), backendData);
      return this.mapBackendUserToFrontend(response.data);
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'UserService.updateUser');
      throw serviceError;
    }
  }

  // Delete user
  async deleteUser(userId: string | number): Promise<UserDeleteResponse> {
    try {
      const response = await api.delete(API_URLS.USERS.DELETE_USER(userId));
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'UserService.deleteUser');
      throw serviceError;
    }
  }

  // Update user role
  async updateUserRole(userId: string | number, role: string): Promise<UserRoleResponse> {
    try {
      const response = await api.put(API_URLS.USERS.CHANGE_USER_ROLE(userId), { role });
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'UserService.updateUserRole');
      throw serviceError;
    }
  }

  // Toggle user activation (enable/disable)
  async toggleUserActivation(userId: string | number): Promise<UserActivationResponse> {
    try {
      const response = await api.put(API_URLS.USERS.TOGGLE_USER_ACTIVATION(userId));
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'UserService.toggleUserActivation');
      throw serviceError;
    }
  }

  // Get users by role (using query parameter)
  async getUsersByRole(role: string): Promise<User[]> {
    try {
      const response = await api.get(API_URLS.USERS.LIST_USERS, {
        params: { role }
      });
      
      // Extract users array from response
      const users = this.extractUsersFromResponse(response.data);
      
      // Map backend response to frontend User interface
      return users.map((user: unknown) => this.mapBackendUserToFrontend(user));
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'UserService.getUsersByRole');
      throw serviceError;
    }
  }

  // Helper method to extract user array from API response
  private extractUsersFromResponse(responseData: unknown): unknown[] {
    if (Array.isArray(responseData)) {
      return responseData;
    } else if (responseData && responseData.items && Array.isArray(responseData.items)) {
      // Handle paginated response with 'items' property (Django Ninja pagination)
      return responseData.items;
    } else if (responseData && responseData.results && Array.isArray(responseData.results)) {
      // Handle paginated response (Django Ninja with @paginate)
      return responseData.results;
    } else if (responseData && responseData.users && Array.isArray(responseData.users)) {
      // Handle wrapped response
      return responseData.users;
    } else if (responseData && responseData.data && Array.isArray(responseData.data)) {
      // Handle nested data response
      return responseData.data;
    } else {
      console.error('Unexpected response structure:', responseData);
      throw new Error(`Invalid response format: expected array of users, got ${typeof responseData}`);
    }
  }

  // Helper method to map backend user response to frontend User interface
  private mapBackendUserToFrontend(backendUser: unknown): User {
    return {
      id: backendUser.id,
      username: backendUser.username,
      email: backendUser.email,
      first_name: backendUser.first_name,
      last_name: backendUser.last_name,
      phone_no: backendUser.phone_number, // Map phone_number to phone_no
      phone_number: backendUser.phone_number,
      bio: backendUser.bio,
      role: backendUser.role,
      active: backendUser.is_active, // Map is_active to active
      is_active: backendUser.is_active,
      is_verified: backendUser.is_verified,
      lastLogin: backendUser.last_login, // Map last_login to lastLogin
      last_login: backendUser.last_login,
      created_at: backendUser.created_at,
      updated_at: backendUser.updated_at,
      user_id: backendUser.user_id
    };
  }

  // Helper method to map frontend user data to backend format
  private mapFrontendUserToBackend(frontendUser: Partial<User>): unknown {
    const backendUser: Record<string, unknown> = { ...frontendUser };
    
    // Map frontend fields to backend fields
    if (frontendUser.phone_no) {
      backendUser.phone_number = frontendUser.phone_no;
      delete backendUser.phone_no;
    }
    if (frontendUser.active !== undefined) {
      backendUser.is_active = frontendUser.active;
      delete backendUser.active;
    }
    if (frontendUser.lastLogin) {
      backendUser.last_login = frontendUser.lastLogin;
      delete backendUser.lastLogin;
    }
    
    return backendUser;
  }

  // Get user activities (using the correct endpoint from urls.ts)
  async getUserActivities(): Promise<Array<{
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
      logError(serviceError, 'UserService.getUserActivities');
      throw serviceError;
    }
  }

  // Get user sessions
  async getUserSessions(): Promise<Array<{
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
      logError(serviceError, 'UserService.getUserSessions');
      throw serviceError;
    }
  }

  // Revoke all user sessions (for current user)
  async revokeAllSessions(): Promise<{ message: string }> {
    try {
      const response = await api.post(API_URLS.USERS.REVOKE_ALL_SESSIONS);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'UserService.revokeAllSessions');
      throw serviceError;
    }
  }

  // Revoke all sessions for a specific user (Admin only)
  async revokeUserSessions(userId: string | number): Promise<{ message: string }> {
    try {
      const response = await api.post(API_URLS.USERS.REVOKE_USER_SESSIONS(userId));
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'UserService.revokeUserSessions');
      throw serviceError;
    }
  }
  // Get current user profile
  async getProfile(): Promise<User> {
    try {
      const response = await api.get(API_URLS.USERS.GET_PROFILE);
      return this.mapBackendUserToFrontend(response.data);
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'UserService.getProfile');
      throw serviceError;
    }
  }

  // Update current user profile
  async updateProfile(profileData: Partial<User>): Promise<User> {
    try {
      // Map frontend data to backend format
      const backendData = this.mapFrontendUserToBackend(profileData);
      const response = await api.put(API_URLS.USERS.UPDATE_PROFILE, backendData);
      return this.mapBackendUserToFrontend(response.data);
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'UserService.updateProfile');
      throw serviceError;
    }
  }

  // Password Reset Methods
  async requestPasswordReset(email: string): Promise<{ message: string; success: boolean }> {
    try {
      const response = await api.post(API_URLS.USERS.AUTH.REQUEST_PASSWORD_RESET, { email });
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'UserService.requestPasswordReset');
      throw serviceError;
    }
  }

  async verifyPasswordReset(data: {
    email: string;
    otp: string;
    new_password: string;
    new_password_confirm: string;
  }): Promise<{ message: string; success: boolean }> {
    try {
      const response = await api.post(API_URLS.USERS.AUTH.VERIFY_PASSWORD_RESET, data);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'UserService.verifyPasswordReset');
      throw serviceError;
    }
  }

  // Change Password
  async changePassword(data: {
    old_password: string;
    new_password: string;
    new_password_confirm: string;
  }): Promise<{ message: string; success?: boolean }> {
    try {
      const response = await api.post(API_URLS.USERS.AUTH.CHANGE_PASSWORD, data);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'UserService.changePassword');
      throw serviceError;
    }
  }
}

export default new UserService();
