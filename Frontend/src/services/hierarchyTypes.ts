// User role hierarchy configuration (matches backend)
export const USER_ROLES = {
  VISITOR: 'visitor',
  DEV: 'dev',
  ADMIN: 'admin',
  SUPERADMIN: 'superadmin'
} as const;

export type UserRole = typeof USER_ROLES[keyof typeof USER_ROLES];

// Role hierarchy levels (higher number = higher privilege)
export const ROLE_HIERARCHY: Record<UserRole, number> = {
  [USER_ROLES.VISITOR]: 1,
  [USER_ROLES.DEV]: 2,
  [USER_ROLES.ADMIN]: 3,
  [USER_ROLES.SUPERADMIN]: 4
};

// Role creation permissions (who can create what roles) - matches README.md
export const ROLE_CREATION_PERMISSIONS: Record<UserRole, UserRole[]> = {
  [USER_ROLES.VISITOR]: [], // Visitor: cannot create anyone
  [USER_ROLES.DEV]: [USER_ROLES.VISITOR], // Developer: can create visitor only
  [USER_ROLES.ADMIN]: [USER_ROLES.DEV, USER_ROLES.VISITOR], // Admin: can create dev and visitor (NOT other admins or superadmins)
  [USER_ROLES.SUPERADMIN]: [USER_ROLES.SUPERADMIN, USER_ROLES.ADMIN, USER_ROLES.DEV, USER_ROLES.VISITOR] // Super Admin: can create anyone
};

// Role management permissions (who can manage what roles) - matches README.md
export const ROLE_MANAGEMENT_PERMISSIONS: Record<UserRole, UserRole[]> = {
  [USER_ROLES.VISITOR]: [], // Visitor: cannot manage anyone
  [USER_ROLES.DEV]: [USER_ROLES.VISITOR], // Developer: limited user management capabilities (visitor users only)
  [USER_ROLES.ADMIN]: [USER_ROLES.ADMIN, USER_ROLES.DEV, USER_ROLES.VISITOR], // Admin: can manage users (except superadmins)
  [USER_ROLES.SUPERADMIN]: [USER_ROLES.SUPERADMIN, USER_ROLES.ADMIN, USER_ROLES.DEV, USER_ROLES.VISITOR] // Super Admin: can manage anyone
};

// Role display information
export const ROLE_INFO: Record<UserRole, {
  displayName: string;
  description: string;
  icon: string;
  color: string;
}> = {
  [USER_ROLES.VISITOR]: {
    displayName: 'Visitor',
    description: 'Basic system access, read-only access to public features',
    icon: '👁️',
    color: '#6b7280'
  },
  [USER_ROLES.DEV]: {
    displayName: 'Developer',
    description: 'Access to development features, limited user management',
    icon: '💻',
    color: '#3b82f6'
  },
  [USER_ROLES.ADMIN]: {
    displayName: 'Admin',
    description: 'Can manage users (except superadmins), access to admin panel',
    icon: '🛡️',
    color: '#f59e0b'
  },
  [USER_ROLES.SUPERADMIN]: {
    displayName: 'Super Admin',
    description: 'Full system access, can create and manage any user',
    icon: '👑',
    color: '#dc2626'
  }
};
