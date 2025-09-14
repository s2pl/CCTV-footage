from django.apps import AppConfig


class GeneralConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.general'
    verbose_name = 'General System'
    
    def ready(self):
        """Initialize the app when Django starts"""
        # Import permissions to ensure they're registered (lazy import to avoid circular imports)
        try:
            from apps.users.permissions import RoleBasedPermission
        except ImportError:
            pass  # Permissions module not available yet
