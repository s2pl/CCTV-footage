import { useAuth } from '../contexts/AuthContext';
import { HierarchyService } from '../services';
import { USER_ROLES, UserRole } from '../services/hierarchyTypes';

/**
 * Custom hook for accessing hierarchy-related functionality
 * Provides easy access to role-based permissions and hierarchy utilities
 */
export const useHierarchy = () => {
  // Add safety check for auth context
  let authData;
  try {
    authData = useAuth();
  } catch (error) {
    // Auth context not available yet - return default values
    return {
      hasRole: () => false,
      hasAnyRole: () => false,
      hasAllRoles: () => false,
      canCreateRole: () => false,
      canManageRole: () => false,
      canDeleteRole: () => false,
      hasRoleLevel: () => false,
      getCreatableRoles: () => [],
      getManageableRoles: () => [],
      getHigherRoles: () => [],
      getLowerRoles: () => [],
      getEqualOrLowerRoles: () => [],
      getAllRoles: () => Object.values(USER_ROLES),
      isAdmin: false,
      isDev: false,
      isSuperAdmin: false,
      userRole: null,
      roleHierarchy: USER_ROLES,
    };
  }

  const { userRole } = authData;

  // Check if user has a specific role
  const hasRole = (role: UserRole): boolean => {
    return userRole === role;
  };

  // Check if user has any of the specified roles
  const hasAnyRole = (roles: UserRole[]): boolean => {
    return roles.includes(userRole!);
  };

  // Check if user has all of the specified roles (useful for combined permissions)
  const hasAllRoles = (roles: UserRole[]): boolean => {
    return roles.every(role => userRole === role);
  };

  // Check if user can create users with a specific role
  const canCreateRole = (targetRole: UserRole): boolean => {
    if (!userRole) return false;
    return HierarchyService.canCreateRole(userRole, targetRole);
  };

  // Check if user can manage users with a specific role
  const canManageRole = (targetRole: UserRole): boolean => {
    if (!userRole) return false;
    return HierarchyService.canManageRole(userRole, targetRole);
  };

  // Check if user has a higher or equal role level
  const hasRoleLevel = (requiredRole: UserRole): boolean => {
    if (!userRole) return false;
    return HierarchyService.hasRoleLevel(userRole, requiredRole);
  };

  // Check if user can access a specific feature
  const canAccessFeature = (feature: string): boolean => {
    if (!userRole) return false;
    return HierarchyService.canAccessFeature(userRole, feature);
  };

  // Get all roles that the user can create
  const getCreatableRoles = (): UserRole[] => {
    if (!userRole) return [];
    return HierarchyService.getCreatableRoles(userRole);
  };

  // Get all roles that the user can manage
  const getManageableRoles = (): UserRole[] => {
    if (!userRole) return [];
    return HierarchyService.getManageableRoles(userRole);
  };

  // Get all features that the user can access
  const getAccessibleFeatures = (): string[] => {
    if (!userRole) return [];
    return HierarchyService.getAccessibleFeatures(userRole);
  };

  // Get role information for display purposes
  const getRoleInfo = (role?: UserRole): {
    displayName: string;
    description: string;
    icon: string;
    color: string;
  } => {
    const targetRole = role || userRole;
    if (!targetRole) {
      return {
        displayName: 'Unknown',
        description: 'No role assigned',
        icon: '❓',
        color: '#6B7280'
      };
    }

    return {
      displayName: HierarchyService.getRoleDisplayName(targetRole),
      description: HierarchyService.getRoleDescription(targetRole),
      icon: HierarchyService.getRoleIcon(targetRole),
      color: HierarchyService.getRoleColor(targetRole)
    };
  };

  // Validate user creation data based on hierarchy
  const validateUserCreation = (userData: { role: UserRole; [key: string]: unknown }) => {
    if (!userRole) {
      return { isValid: false, errors: ['User not authenticated'] };
    }
    return HierarchyService.validateUserCreation(userData, userRole);
  };

  // Get role hierarchy tree for visualization
  const getRoleHierarchyTree = () => {
    return HierarchyService.getRoleHierarchyTree();
  };

  // Check if user can perform an action on a target role
  const canPerformAction = (action: 'create' | 'manage' | 'view', targetRole: UserRole): boolean => {
    if (!userRole) return false;
    return HierarchyService.canPerformAction(action, userRole, targetRole);
  };

  // Convenience methods for common role checks
  const isVisitor = hasRole(USER_ROLES.VISITOR);
  const isDev = hasRole(USER_ROLES.DEV);
  const isAdmin = hasRole(USER_ROLES.ADMIN);
  const isSuperAdmin = hasRole(USER_ROLES.SUPERADMIN);

  // Check if user has elevated permissions (dev or above)
  const hasElevatedPermissions = hasRoleLevel(USER_ROLES.DEV);

  // Check if user has administrative permissions (admin or above)
  const hasAdminPermissions = hasRoleLevel(USER_ROLES.ADMIN);

  // Check if user has superadmin permissions
  const hasSuperAdminPermissions = isSuperAdmin;

  return {
    // User role information
    userRole,
    isVisitor,
    isDev,
    isAdmin,
    isSuperAdmin,
    hasElevatedPermissions,
    hasAdminPermissions,
    hasSuperAdminPermissions,

    // Role checking methods
    hasRole,
    hasAnyRole,
    hasAllRoles,
    hasRoleLevel,

    // Permission checking methods
    canCreateRole,
    canManageRole,
    canAccessFeature,
    canPerformAction,

    // Role management methods
    getCreatableRoles,
    getManageableRoles,
    getAccessibleFeatures,

    // Utility methods
    getRoleInfo,
    validateUserCreation,
    getRoleHierarchyTree,

    // Constants
    USER_ROLES
  };
};

export default useHierarchy;
