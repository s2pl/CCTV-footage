from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserActivity

User = get_user_model()


@receiver(post_save, sender=User)
def log_user_activity(sender, instance, created, **kwargs):
    """
    Log user creation and updates
    """
    if created:
        # Log user creation
        UserActivity.objects.create(
            user=instance,
            activity_type='create',
            description=f'User account created: {instance.email}',
            metadata={'role': instance.role}
        )
    else:
        # Log user updates
        UserActivity.objects.create(
            user=instance,
            activity_type='update',
            description=f'User profile updated: {instance.email}',
            metadata={'role': instance.role, 'is_active': instance.is_active}
        )


@receiver(post_delete, sender=User)
def log_user_deletion(sender, instance, **kwargs):
    """
    Log user deletion
    """
    # Note: This might not work as expected since the user is already deleted
    # Consider using pre_delete signal instead
    pass


@receiver(post_save, sender=User)
def send_welcome_email_on_registration(sender, instance, created, **kwargs):
    """
    Send welcome email when a new user is created
    """
    if created:
        try:
            # Import here to avoid circular imports
            from apps.mailer.views import WelcomeEmailService
            
            # Get user's full name or use username
            full_name = f"{instance.first_name} {instance.last_name}".strip()
            if not full_name:
                full_name = instance.username or instance.email.split('@')[0]
            
            # Send welcome email
            result = WelcomeEmailService.send_welcome_email(
                email=instance.email,
                fullname=full_name
            )
            
            # Log the activity
            UserActivity.objects.create(
                user=instance,
                activity_type='create',
                description=f'Welcome email sent to: {instance.email}',
                metadata={
                    'email_status': result.get('status', 'unknown'),
                    'email_message': result.get('message', '')
                }
            )
            
        except Exception as e:
            # Log the error but don't break user creation
            UserActivity.objects.create(
                user=instance,
                activity_type='create',
                description=f'Failed to send welcome email to: {instance.email}',
                metadata={
                    'error': str(e),
                    'email_status': 'failed'
                }
            )
