from django.apps import AppConfig


class MailerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.mailer'
    verbose_name = 'Mailer System'
    
    def ready(self):
        """Initialize the app when Django starts"""
        # Import permissions to ensure they're registered (lazy import to avoid circular imports)
        try:
            from apps.users.permissions import RoleBasedPermission
        except ImportError:
            pass  # Permissions module not available yet
