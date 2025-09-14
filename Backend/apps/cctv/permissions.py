from rest_framework import permissions
from django.contrib.auth import get_user_model
from .models import Camera, CameraAccess

User = get_user_model()


class CanAccessCamera(permissions.BasePermission):
    """
    Custom permission to check if user can access a specific camera
    """
    
    def has_object_permission(self, request, view, obj):
        # Superadmin and admin users can access all cameras
        if request.user.is_superadmin or request.user.is_admin:
            return True
        
        # Check if camera is public
        if isinstance(obj, Camera) and obj.is_public:
            return True
        
        # Check if user has specific access to this camera
        if isinstance(obj, Camera):
            try:
                access = CameraAccess.objects.get(
                    user=request.user, 
                    camera=obj, 
                    is_active=True
                )
                return True
            except CameraAccess.DoesNotExist:
                pass
        
        # Check if user created this camera
        if isinstance(obj, Camera) and obj.created_by == request.user:
            return True
        
        return False


class CanControlCamera(permissions.BasePermission):
    """
    Permission to control camera (start/stop recording, etc.)
    """
    
    def has_object_permission(self, request, view, obj):
        # Superadmin and admin users can control all cameras
        if request.user.is_superadmin or request.user.is_admin:
            return True
        
        # Check if user has control access to this camera
        if isinstance(obj, Camera):
            try:
                access = CameraAccess.objects.get(
                    user=request.user, 
                    camera=obj, 
                    is_active=True
                )
                return access.access_level in ['control', 'admin'] or access.can_record
            except CameraAccess.DoesNotExist:
                pass
        
        # Check if user created this camera
        if isinstance(obj, Camera) and obj.created_by == request.user:
            return True
        
        return False


class CanManageCamera(permissions.BasePermission):
    """
    Permission to manage camera (edit settings, delete, etc.)
    """
    
    def has_object_permission(self, request, view, obj):
        # Superadmin can manage all cameras
        if request.user.is_superadmin:
            return True
        
        # Admin can manage cameras they didn't create only if they have admin access
        if request.user.is_admin:
            if isinstance(obj, Camera):
                if obj.created_by == request.user:
                    return True
                try:
                    access = CameraAccess.objects.get(
                        user=request.user, 
                        camera=obj, 
                        is_active=True
                    )
                    return access.access_level == 'admin'
                except CameraAccess.DoesNotExist:
                    return False
        
        # Check if user created this camera
        if isinstance(obj, Camera) and obj.created_by == request.user:
            return True
        
        return False


class CanCreateCamera(permissions.BasePermission):
    """
    Permission to create new cameras
    """
    
    def has_permission(self, request, view):
        # Only admin and superadmin can create cameras
        return request.user.is_admin or request.user.is_superadmin


class CanAccessRecording(permissions.BasePermission):
    """
    Permission to access recordings
    """
    
    def has_object_permission(self, request, view, obj):
        # Superadmin and admin users can access all recordings
        if request.user.is_superadmin or request.user.is_admin:
            return True
        
        # Check if user created this recording
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
        
        # Check if user has access to the camera that made this recording
        if hasattr(obj, 'camera'):
            return self.can_access_camera(request.user, obj.camera)
        
        return False
    
    def can_access_camera(self, user, camera):
        """Helper method to check camera access"""
        # Check if camera is public
        if camera.is_public:
            return True
        
        # Check if user has specific access to this camera
        try:
            access = CameraAccess.objects.get(
                user=user, 
                camera=camera, 
                is_active=True
            )
            return True
        except CameraAccess.DoesNotExist:
            pass
        
        # Check if user created this camera
        if camera.created_by == user:
            return True
        
        return False


class CanDownloadRecording(permissions.BasePermission):
    """
    Permission to download recordings
    """
    
    def has_object_permission(self, request, view, obj):
        # First check if user can access the recording
        if not CanAccessRecording().has_object_permission(request, view, obj):
            return False
        
        # Superadmin and admin users can download all recordings
        if request.user.is_superadmin or request.user.is_admin:
            return True
        
        # Check if user has download permission for this camera
        if hasattr(obj, 'camera'):
            try:
                access = CameraAccess.objects.get(
                    user=request.user, 
                    camera=obj.camera, 
                    is_active=True
                )
                return access.can_download
            except CameraAccess.DoesNotExist:
                pass
        
        # Check if user created this recording or camera
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
        if hasattr(obj, 'camera') and obj.camera.created_by == request.user:
            return True
        
        return False


class CanScheduleRecording(permissions.BasePermission):
    """
    Permission to create/manage recording schedules
    """
    
    def has_permission(self, request, view):
        # Only admin, superadmin, and developers can create schedules
        return request.user.is_developer
    
    def has_object_permission(self, request, view, obj):
        # Superadmin can manage all schedules
        if request.user.is_superadmin:
            return True
        
        # Admin can manage schedules for cameras they have access to
        if request.user.is_admin:
            if hasattr(obj, 'camera'):
                return CanManageCamera().has_object_permission(request, view, obj.camera)
        
        # Check if user created this schedule
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
        
        # Check if user has scheduling permission for this camera
        if hasattr(obj, 'camera'):
            try:
                access = CameraAccess.objects.get(
                    user=request.user, 
                    camera=obj.camera, 
                    is_active=True
                )
                return access.can_schedule
            except CameraAccess.DoesNotExist:
                pass
        
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the object.
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


# Role-based permission shortcuts
def require_admin(view_func):
    """Decorator to require admin role"""
    def wrapper(self, request, *args, **kwargs):
        if not request.user.is_admin:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required")
        return view_func(self, request, *args, **kwargs)
    return wrapper


def require_superadmin(view_func):
    """Decorator to require superadmin role"""
    def wrapper(self, request, *args, **kwargs):
        if not request.user.is_superadmin:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Superadmin access required")
        return view_func(self, request, *args, **kwargs)
    return wrapper
