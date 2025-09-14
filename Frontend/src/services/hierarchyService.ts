import { USER_ROLES, UserRole, ROLE_HIERARCHY, ROLE_CREATION_PERMISSIONS, ROLE_MANAGEMENT_PERMISSIONS } from './hierarchyTypes';

/**
 * Hierarchical Role-Based Access Control Service
 * Provides utilities for managing user roles and permissions based on the hierarchy system
 */
export class HierarchyService {
  /**
   * Check if a user can create users with a specific role
   */
  static canCreateRole(userRole: UserRole, targetRole: UserRole): boolean {
    return ROLE_CREATION_PERMISSIONS[userRole]?.includes(targetRole) || false;
  }

  /**
   * Check if a user can manage users with a specific role
   */
  static canManageRole(userRole: UserRole, targetRole: UserRole): boolean {
    return ROLE_MANAGEMENT_PERMISSIONS[userRole]?.includes(targetRole) || false;
  }

  /**
   * Check if a user has a higher or equal role level
   */
  static hasRoleLevel(userRole: UserRole, requiredRole: UserRole): boolean {
    return ROLE_HIERARCHY[userRole] >= ROLE_HIERARCHY[requiredRole];
  }

  /**
   * Get all roles that a user can create
   */
  static getCreatableRoles(userRole: UserRole): UserRole[] {
    return ROLE_CREATION_PERMISSIONS[userRole] || [];
  }

  /**
   * Get all roles that a user can manage
   */
  static getManageableRoles(userRole: UserRole): UserRole[] {
    return ROLE_MANAGEMENT_PERMISSIONS[userRole] || [];
  }

  /**
   * Validate role assignment based on hierarchy
   */
  static validateRoleAssignment(assignerRole: UserRole, targetRole: UserRole): boolean {
    return this.canCreateRole(assignerRole, targetRole);
  }

  /**
   * Check if current user can perform an action on a target role
   */
  static canPerformAction(action: 'create' | 'manage' | 'view', userRole: UserRole, targetRole: UserRole): boolean {
    switch (action) {
      case 'create':
        return this.canCreateRole(userRole, targetRole);
      case 'manage':
        return this.canManageRole(userRole, targetRole);
      case 'view':
        return this.canManageRole(userRole, targetRole);
      default:
        return false;
    }
  }

  /**
   * Get role display name
   */
  static getRoleDisplayName(role: UserRole): string {
    const displayNames: Record<UserRole, string> = {
      [USER_ROLES.VISITOR]: 'Visitor',
      [USER_ROLES.DEV]: 'Developer',
      [USER_ROLES.ADMIN]: 'Admin',
      [USER_ROLES.SUPERADMIN]: 'Super Admin'
    };
    return displayNames[role] || role;
  }

  /**
   * Get role description
   */
  static getRoleDescription(role: UserRole): string {
    const descriptions: Record<UserRole, string> = {
      [USER_ROLES.VISITOR]: 'Basic system access, read-only access to public features',
      [USER_ROLES.DEV]: 'Access to development features, limited user management capabilities',
      [USER_ROLES.ADMIN]: 'Can manage users (except superadmins), access to admin panel',
      [USER_ROLES.SUPERADMIN]: 'Full system access, can create, modify, and delete any user'
    };
    return descriptions[role] || 'No description available';
  }

  /**
   * Get role icon (for UI purposes)
   */
  static getRoleIcon(role: UserRole): string {
    const icons: Record<UserRole, string> = {
      [USER_ROLES.VISITOR]: '👁️',
      [USER_ROLES.DEV]: '💻',
      [USER_ROLES.ADMIN]: '🛡️',
      [USER_ROLES.SUPERADMIN]: '👑'
    };
    return icons[role] || '❓';
  }

  /**
   * Get role color (for UI purposes)
   */
  static getRoleColor(role: UserRole): string {
    const colors: Record<UserRole, string> = {
      [USER_ROLES.VISITOR]: '#6B7280',
      [USER_ROLES.DEV]: '#3B82F6',
      [USER_ROLES.ADMIN]: '#F59E0B',
      [USER_ROLES.SUPERADMIN]: '#DC2626'
    };
    return colors[role] || '#6B7280';
  }

  /**
   * Check if user can access a specific feature based on role
   */
  static canAccessFeature(userRole: UserRole, feature: string): boolean {
    const featurePermissions: Record<string, UserRole[]> = {
      'user_management': [USER_ROLES.DEV, USER_ROLES.ADMIN, USER_ROLES.SUPERADMIN], // Dev has limited user management
      'admin_panel': [USER_ROLES.ADMIN, USER_ROLES.SUPERADMIN],
      'system_config': [USER_ROLES.SUPERADMIN],
      'cctv_management': [USER_ROLES.DEV, USER_ROLES.ADMIN, USER_ROLES.SUPERADMIN],
      'mailer_management': [USER_ROLES.ADMIN, USER_ROLES.SUPERADMIN],
      'general_management': [USER_ROLES.ADMIN, USER_ROLES.SUPERADMIN],
      'development_features': [USER_ROLES.DEV, USER_ROLES.ADMIN, USER_ROLES.SUPERADMIN]
    };

    const requiredRoles = featurePermissions[feature];
    return requiredRoles ? requiredRoles.includes(userRole) : false;
  }

  /**
   * Get all accessible features for a user role
   */
  static getAccessibleFeatures(userRole: UserRole): string[] {
    const allFeatures = [
      'user_management',
      'admin_panel', 
      'system_config',
      'cctv_management',
      'mailer_management',
      'general_management'
    ];

    return allFeatures.filter(feature => this.canAccessFeature(userRole, feature));
  }

  /**
   * Validate user creation data based on hierarchy
   */
  static validateUserCreation(userData: { role: UserRole; [key: string]: unknown }, creatorRole: UserRole): {
    isValid: boolean;
    errors: string[];
  } {
    const errors: string[] = [];

    // Check if creator can create the target role
    if (!this.canCreateRole(creatorRole, userData.role)) {
      errors.push(`Permission denied. You cannot create users with role: ${userData.role}`);
    }

    // Check if creator is trying to create a user with equal or higher role
    if (ROLE_HIERARCHY[userData.role] >= ROLE_HIERARCHY[creatorRole]) {
      errors.push(`Permission denied. You cannot create users with equal or higher role level`);
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Get role hierarchy tree for visualization
   */
  static getRoleHierarchyTree(): Array<{ role: UserRole; level: number; canCreate: UserRole[]; canManage: UserRole[] }> {
    return Object.entries(ROLE_HIERARCHY).map(([role, level]) => ({
      role: role as UserRole,
      level,
      canCreate: ROLE_CREATION_PERMISSIONS[role as UserRole] || [],
      canManage: ROLE_MANAGEMENT_PERMISSIONS[role as UserRole] || []
    })).sort((a, b) => a.level - b.level);
  }
}

export default HierarchyService;
