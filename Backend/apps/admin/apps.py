from django.apps import AppConfig

class CustomAdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.admin'
    label = 'custom_admin'  # This gives your app a unique label
    verbose_name = 'Custom Admin'  # This makes it clearer in the admin UI 