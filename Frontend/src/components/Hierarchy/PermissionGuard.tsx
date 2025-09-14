import React, { ReactNode } from 'react';
import { useHierarchy } from '../../hooks/useHierarchy';
import { UserRole } from '../../services/hierarchyTypes';

interface PermissionGuardProps {
  children: ReactNode;
  requiredRole?: UserRole;
  requiredRoles?: UserRole[];
  requiredFeature?: string;
  action?: 'create' | 'manage' | 'view';
  targetRole?: UserRole;
  fallback?: ReactNode;
  showFallback?: boolean;
  className?: string;
}

/**
 * Permission Guard Component
 * Conditionally renders content based on user permissions and role hierarchy
 */
export const PermissionGuard: React.FC<PermissionGuardProps> = ({
  children,
  requiredRole,
  requiredRoles,
  requiredFeature,
  action,
  targetRole,
  fallback = null,
  showFallback = true,
  className = ''
}) => {
  const {
    hasRoleLevel,
    hasAnyRole,
    canAccessFeature,
    canPerformAction
  } = useHierarchy();

  // Check if user has access
  const hasAccess = (): boolean => {
    // Check required role level
    if (requiredRole && !hasRoleLevel(requiredRole)) {
      return false;
    }

    // Check if user has any of the required roles
    if (requiredRoles && requiredRoles.length > 0 && !hasAnyRole(requiredRoles)) {
      return false;
    }

    // Check feature access
    if (requiredFeature && !canAccessFeature(requiredFeature)) {
      return false;
    }

    // Check action permissions on target role
    if (action && targetRole && !canPerformAction(action, targetRole)) {
      return false;
    }

    return true;
  };

  // If user has access, render children
  if (hasAccess()) {
    return <>{children}</>;
  }

  // If no access and fallback is disabled, render nothing
  if (!showFallback) {
    return null;
  }

  // Render fallback content
  return (
    <div className={`permission-guard-fallback ${className}`}>
      {fallback}
    </div>
  );
};

/**
 * Higher-order component for protecting routes/components
 */
export const withPermission = <P extends object>(
  Component: React.ComponentType<P>,
  permissionProps: Omit<PermissionGuardProps, 'children'>
) => {
  return (props: P) => (
    <PermissionGuard {...permissionProps}>
      <Component {...props} />
    </PermissionGuard>
  );
};

/**
 * Hook for checking permissions in components
 */
export const usePermission = () => {
  const hierarchy = useHierarchy();

  return {
    ...hierarchy,
    // Additional permission checking methods
    canAccessRoute: (route: string): boolean => {
      const routePermissions: Record<string, string> = {
        '/admin': 'admin_panel',
        '/users': 'user_management',
        '/cctv': 'cctv_management',
        '/mailer': 'mailer_management',
        '/general': 'general_management',
        '/system': 'system_config'
      };

      const requiredFeature = routePermissions[route];
      return requiredFeature ? hierarchy.canAccessFeature(requiredFeature) : true;
    },

    canViewUser: (targetUserRole: UserRole): boolean => {
      return hierarchy.canManageRole(targetUserRole);
    },

    canEditUser: (targetUserRole: UserRole): boolean => {
      return hierarchy.canManageRole(targetUserRole);
    },

    canDeleteUser: (targetUserRole: UserRole): boolean => {
      return hierarchy.canManageRole(targetUserRole);
    },

    canCreateUser: (targetUserRole: UserRole): boolean => {
      return hierarchy.canCreateRole(targetUserRole);
    }
  };
};

export default PermissionGuard;
