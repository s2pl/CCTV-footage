import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import authService from '../services/authService';
import { User, LoginCredentials } from '../services/authService';
import { USER_ROLES, UserRole } from '../services/hierarchyTypes';
import { HierarchyService } from '../services';
import { logTokenStatus } from '../utils/tokenUtils';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  debugTokens: () => void;
  
  // Hierarchy-based permissions
  userRole: UserRole | null;
  isAdmin: boolean;
  isDev: boolean;
  isSuperAdmin: boolean;
  canCreateRole: (targetRole: UserRole) => boolean;
  canManageRole: (targetRole: UserRole) => boolean;
  hasRoleLevel: (requiredRole: UserRole) => boolean;
  canAccessFeature: (feature: string) => boolean;
  getCreatableRoles: () => UserRole[];
  getManageableRoles: () => UserRole[];
  getAccessibleFeatures: () => string[];
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isInitialized, setIsInitialized] = useState(false);
  const [hotReloadCounter, setHotReloadCounter] = useState(0);

  // Detect hot reload in development
  useEffect(() => {
    if (import.meta.env.DEV && import.meta.hot) {
      setHotReloadCounter(prev => prev + 1);
      console.log('Hot reload detected, reinitializing auth...');
    }
  }, []);

  // Initialize auth state on mount
  useEffect(() => {
    const initializeAuth = async () => {
              try {
          console.log('Initializing authentication...');
          logTokenStatus(); // Log current token status
        
        // Check if user is already authenticated
        if (authService.isAuthenticated()) {
          const currentUser = authService.getCurrentUser();
          if (currentUser) {
            console.log('User already authenticated:', currentUser.username);
            setUser(currentUser);
          } else {
            console.log('User data missing, attempting token refresh...');
            // Try to refresh token if user data is missing
            try {
              await authService.refreshToken();
              const refreshedUser = authService.getCurrentUser();
              if (refreshedUser) {
                console.log('User data restored after refresh:', refreshedUser.username);
                setUser(refreshedUser);
              }
            } catch {
              console.log('Token refresh failed during initialization');
              // Refresh failed, clear auth state
              authService.logout();
            }
          }
        } else {
          console.log('No valid authentication found');
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        authService.logout();
      } finally {
        setIsLoading(false);
        setIsInitialized(true);
      }
    };

    initializeAuth();
  }, []);

  // Set up token refresh interval - refresh every 25 minutes (tokens expire in 30 minutes)
  useEffect(() => {
    if (!user) return;

    const refreshInterval = setInterval(async () => {
      try {
        console.log('Refreshing token...');
        await authService.refreshToken();
        const refreshedUser = authService.getCurrentUser();
        if (refreshedUser) {
          setUser(refreshedUser);
          console.log('Token refreshed successfully');
        }
      } catch (error) {
        console.error('Token refresh failed:', error);
        // Don't logout immediately on refresh failure, let the API interceptor handle it
        // This prevents unnecessary logouts when the refresh endpoint is temporarily unavailable
      }
    }, 25 * 60 * 1000); // 25 minutes

    return () => clearInterval(refreshInterval);
  }, [user]);

  // Set up a more frequent check for token validity (every 5 minutes)
  useEffect(() => {
    if (!user) return;

    const validityCheckInterval = setInterval(async () => {
      try {
        // Check if token is still valid by making a simple API call
        const token = authService.getAccessToken();
        if (!token) {
          console.log('No access token found, logging out');
          logout();
          return;
        }

        // Try to refresh if token is close to expiration (within 5 minutes)
        const tokenData = JSON.parse(atob(token.split('.')[1]));
        const expirationTime = tokenData.exp * 1000;
        const currentTime = Date.now();
        const timeUntilExpiry = expirationTime - currentTime;

        if (timeUntilExpiry < 5 * 60 * 1000) { // Less than 5 minutes
          console.log('Token expiring soon, refreshing...');
          await authService.refreshToken();
          const refreshedUser = authService.getCurrentUser();
          if (refreshedUser) {
            setUser(refreshedUser);
          }
        }
      } catch (error) {
        console.error('Token validity check failed:', error);
        // Don't logout on validity check failure
      }
    }, 5 * 60 * 1000); // 5 minutes

    return () => clearInterval(validityCheckInterval);
  }, [user]);

  const login = async (credentials: LoginCredentials) => {
    try {
      setIsLoading(true);
      const response = await authService.login(credentials);
      setUser(response.user);
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };



  const logout = () => {
    authService.logout();
    setUser(null);
  };

  const refreshToken = async () => {
    try {
      const response = await authService.refreshToken();
      setUser(response.user);
    } catch (error) {
      console.error('Token refresh error:', error);
      logout();
      throw error;
    }
  };



  const debugTokens = () => {
    logTokenStatus(); // Use the utility function we created
  };

  // Get user role from user object or localStorage
  const getUserRole = (): UserRole | null => {
    if (user?.role) {
      return user.role as UserRole;
    }
    const storedRole = localStorage.getItem('userRole');
    return storedRole as UserRole || null;
  };

  // Hierarchy-based permission checks
  const userRole = getUserRole();
  const isAdmin = userRole === USER_ROLES.ADMIN || userRole === USER_ROLES.SUPERADMIN;
  const isDev = userRole === USER_ROLES.DEV || isAdmin;
  const isSuperAdmin = userRole === USER_ROLES.SUPERADMIN;

  const canCreateRole = (targetRole: UserRole): boolean => {
    if (!userRole) return false;
    return HierarchyService.canCreateRole(userRole, targetRole);
  };

  const canManageRole = (targetRole: UserRole): boolean => {
    if (!userRole) return false;
    return HierarchyService.canManageRole(userRole, targetRole);
  };

  const hasRoleLevel = (requiredRole: UserRole): boolean => {
    if (!userRole) return false;
    return HierarchyService.hasRoleLevel(userRole, requiredRole);
  };

  const canAccessFeature = (feature: string): boolean => {
    if (!userRole) return false;
    return HierarchyService.canAccessFeature(userRole, feature);
  };

  const getCreatableRoles = (): UserRole[] => {
    if (!userRole) return [];
    return HierarchyService.getCreatableRoles(userRole);
  };

  const getManageableRoles = (): UserRole[] => {
    if (!userRole) return [];
    return HierarchyService.getManageableRoles(userRole);
  };

  const getAccessibleFeatures = (): string[] => {
    if (!userRole) return [];
    return HierarchyService.getAccessibleFeatures(userRole);
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    refreshToken,
    debugTokens,
    
    // Hierarchy-based permissions
    userRole,
    isAdmin,
    isDev,
    isSuperAdmin,
    canCreateRole,
    canManageRole,
    hasRoleLevel,
    canAccessFeature,
    getCreatableRoles,
    getManageableRoles,
    getAccessibleFeatures,
  };

  // Don't render children until initialization is complete to prevent race conditions
  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Initializing...</p>
        </div>
      </div>
    );
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    // Check if we're in development mode and possibly during hot reload
    if (import.meta.env.DEV) {
      console.warn('useAuth called before AuthProvider is ready - this might be due to hot reload');
    }
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
