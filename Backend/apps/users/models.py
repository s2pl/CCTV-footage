from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone
import uuid


class CustomUserManager(UserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        username = extra_fields.pop('username', email.split('@')[0])
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'superadmin')
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = [
        ('superadmin', 'Super Admin'),
        ('admin', 'Admin'),
        ('dev', 'Developer'),
        ('visitor', 'Visitor'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='visitor')
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Profile fields
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    avatar = models.FileField(upload_to='users/avatar/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True, max_length=500)
    
    # Override username to use email as primary identifier
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    objects = CustomUserManager()
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    
    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email.split('@')[0]
        super().save(*args, **kwargs)
    
    @property
    def is_superadmin(self):
        return self.role == 'superadmin'
    
    @property
    def is_admin(self):
        return self.role in ['superadmin', 'admin']
    
    @property
    def is_developer(self):
        return self.role in ['superadmin', 'admin', 'dev']
    
    def can_manage_users(self):
        return self.role in ['superadmin', 'admin']
    
    def can_access_admin_panel(self):
        return self.role in ['superadmin', 'admin']
    
    def can_create_user_with_role(self, target_role):
        """
        Check if current user can create another user with the specified role
        
        Hierarchy (as per README.md):
        - superadmin: can create anyone (superadmin, admin, dev, visitor)
        - admin: can create dev and visitor (but NOT superadmin or other admins)
        - dev: can create visitor only
        - visitor: cannot create anyone
        """
        role_hierarchy = {
            'superadmin': ['superadmin', 'admin', 'dev', 'visitor'],
            'admin': ['dev', 'visitor'],  # Admin CANNOT create other admins or superadmins
            'dev': ['visitor'],
            'visitor': []
        }
        
        allowed_roles = role_hierarchy.get(self.role, [])
        return target_role in allowed_roles
    
    def can_manage_user(self, target_user):
        """
        Check if current user can manage (update/delete/change role) another user
        
        Rules (as per README.md):
        - superadmin: can manage anyone (except themselves for deletion)
        - admin: can manage dev and visitor users (except superadmins)
        - dev: limited user management capabilities (visitor users only)
        - visitor: cannot manage anyone
        """
        if self.role == 'superadmin':
            return True
        elif self.role == 'admin':
            # Admin can manage users except superadmins
            return target_user.role in ['admin', 'dev', 'visitor']
        elif self.role == 'dev':
            # Developer has limited user management capabilities
            return target_user.role == 'visitor'
        else:
            return False


class UserSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    token = models.CharField(max_length=500, unique=True)  # Access token
    refresh_token = models.CharField(max_length=500, unique=True, default='')  # Refresh token
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # Access token expiry
    refresh_expires_at = models.DateTimeField(default=timezone.now)  # Refresh token expiry
    is_active = models.BooleanField(default=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Session for {self.user.email} - {self.created_at}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def is_refresh_expired(self):
        return timezone.now() > self.refresh_expires_at


class UserActivity(models.Model):
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('download', 'Download'),
        ('upload', 'Upload'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
    
    def __str__(self):
        return f"{self.user.email} - {self.get_activity_type_display()} - {self.created_at}"
