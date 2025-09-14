from rest_framework import permissions
from .models import User


class IsSuperAdmin(permissions.BasePermission):
    """
    Custom permission to only allow superadmin users.
    """
    
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'superadmin'
        )


class IsAdmin(permissions.BasePermission):
    """
    Custom permission to only allow admin and superadmin users.
    """
    
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_admin
        )


class IsDeveloper(permissions.BasePermission):
    """
    Custom permission to only allow developer, admin and superadmin users.
    """
    
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_developer
        )


class CanManageUsers(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage other users.
    """
    
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.can_manage_users()
        )


class CanAccessAdminPanel(permissions.BasePermission):
    """
    Custom permission to only allow users who can access admin panel.
    """
    
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.can_access_admin_panel()
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admins.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin users can access any object
        if request.user.is_admin:
            return True
        
        # Check if the user is the owner of the object
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False


class RoleBasedPermission(permissions.BasePermission):
    """
    Custom permission that checks user role against required roles.
    """
    
    def __init__(self, required_roles=None):
        self.required_roles = required_roles or []
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not self.required_roles:
            return True
        
        return request.user.role in self.required_roles


def require_roles(*roles):
    """
    Decorator to require specific roles for a view.
    Usage: @require_roles('admin', 'superadmin')
    """
    def decorator(view_class):
        view_class.permission_classes = [RoleBasedPermission(roles)]
        return view_class
    return decorator


def check_app_access(user, app_name):
    """
    Check if user has access to a specific app
    """
    if not user or not user.is_authenticated:
        return False
    
    # Superadmin has access to everything
    if user.is_superadmin:
        return True
    
    # App-specific access rules
    if app_name == 'mailer':
        return user.is_admin  # Only admin and superadmin can access mailer
    elif app_name == 'cctv':
        return True  # All authenticated users can access CCTV (with role-based restrictions)
    elif app_name == 'users':
        return user.can_manage_users()  # Only users who can manage users
    
    # Default: only authenticated users
    return True


def check_role_access(user, required_roles):
    """
    Check if user has one of the required roles
    """
    if not user or not user.is_authenticated:
        return False
    
    if isinstance(required_roles, str):
        required_roles = [required_roles]
    
    return user.role in required_roles
