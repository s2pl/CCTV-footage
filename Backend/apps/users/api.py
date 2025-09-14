"""
Django Ninja API for User Management with comprehensive Swagger documentation
"""

from ninja import NinjaAPI, Router, Schema, Field
from ninja.pagination import paginate
from ninja.errors import HttpError
from ninja.security import HttpBearer
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from typing import List, Optional
import uuid

from .models import User, UserSession, UserActivity
from .auth import generate_jwt_tokens, generate_jwt_token, verify_jwt_token, revoke_jwt_token, refresh_jwt_token
from .permissions import IsSuperAdmin, IsAdmin, CanManageUsers

User = get_user_model()

# Custom authentication for Django Ninja
class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            user = verify_jwt_token(token)
            return user
        except Exception:
            return None

# Apply authentication to protected endpoints
jwt_auth = JWTAuth()

# Schema definitions for Swagger documentation
class LoginSchema(Schema):
    email: str = Field(..., description="User email address", example="admin@example.com")
    password: str = Field(..., description="User password", example="SecurePass123!")

class UserRegistrationSchema(Schema):
    email: str = Field(..., description="User email address", example="user@example.com")
    username: Optional[str] = Field(None, description="Username (optional)", example="john_doe")
    password: str = Field(..., description="User password", example="SecurePass123!")
    password_confirm: str = Field(..., description="Password confirmation", example="SecurePass123!")
    first_name: Optional[str] = Field(None, description="First name", example="John")
    last_name: Optional[str] = Field(None, description="Last name", example="Doe")
    role: Optional[str] = Field("visitor", description="User role", example="visitor")
    phone_number: Optional[str] = Field(None, description="Phone number", example="+1234567890")
    bio: Optional[str] = Field(None, description="User biography", example="Software developer")

class UserUpdateSchema(Schema):
    username: Optional[str] = Field(None, description="Username", example="john_doe_updated")
    first_name: Optional[str] = Field(None, description="First name", example="John")
    last_name: Optional[str] = Field(None, description="Last name", example="Doe")
    phone_number: Optional[str] = Field(None, description="Phone number", example="+1234567890")
    bio: Optional[str] = Field(None, description="User biography", example="Senior software developer")
    is_active: Optional[bool] = Field(None, description="User active status", example=True)

class ChangePasswordSchema(Schema):
    old_password: str = Field(..., description="Current password", example="OldPass123!")
    new_password: str = Field(..., description="New password", example="NewPass123!")
    new_password_confirm: str = Field(..., description="New password confirmation", example="NewPass123!")

class RoleUpdateSchema(Schema):
    role: str = Field(..., description="New user role", example="admin")

class ActivationSchema(Schema):
    is_active: bool = Field(..., description="User activation status", example=True)

# Response schemas
class TokenResponseSchema(Schema):
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiry in seconds")
    user: dict = Field(..., description="User information")
    message: str = Field(..., description="Response message")

class RefreshTokenSchema(Schema):
    refresh_token: str = Field(..., description="JWT refresh token", example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...")

class RefreshTokenResponseSchema(Schema):
    access_token: str = Field(..., description="New JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiry in seconds")
    message: str = Field(..., description="Response message")

class UserResponseSchema(Schema):
    id: str = Field(..., description="User UUID")
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="User active status")
    is_verified: bool = Field(..., description="User verification status")
    phone_number: Optional[str] = Field(None, description="Phone number")
    bio: Optional[str] = Field(None, description="User biography")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    last_login: Optional[str] = Field(None, description="Last login timestamp")

class UserListResponseSchema(Schema):
    id: str = Field(..., description="User UUID")
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="User active status")
    created_at: str = Field(..., description="Creation timestamp")
    last_login: Optional[str] = Field(None, description="Last login timestamp")
    phone_number: Optional[str] = Field(None, description="Phone number (superadmin only)")
    bio: Optional[str] = Field(None, description="User biography (superadmin only)")

class UserActivityResponseSchema(Schema):
    id: str = Field(..., description="Activity UUID")
    activity_type: str = Field(..., description="Type of activity")
    description: str = Field(..., description="Activity description")
    ip_address: Optional[str] = Field(None, description="IP address")
    created_at: str = Field(..., description="Activity timestamp")
    metadata: dict = Field(..., description="Additional metadata")

class UserSessionResponseSchema(Schema):
    id: str = Field(..., description="Session UUID")
    created_at: str = Field(..., description="Session creation timestamp")
    expires_at: str = Field(..., description="Session expiration timestamp")
    is_active: bool = Field(..., description="Session active status")
    ip_address: Optional[str] = Field(None, description="IP address")

class MessageResponseSchema(Schema):
    message: str = Field(..., description="Response message")
    success: Optional[bool] = Field(True, description="Operation success status")

# Create the API instance
api = NinjaAPI(
    title="User Management API",
    version="1.0.0",
    description="Comprehensive user management system with authentication, authorization, and activity tracking",
    docs_url="/docs",
    openapi_url="/openapi.json",
    urls_namespace="users_system"
)

# Authentication router
auth_router = Router(tags=["Authentication"])

@auth_router.post("/login/", response=TokenResponseSchema, summary="User Login")
def login(request, data: LoginSchema):
    """
    Authenticate user and return JWT tokens (access and refresh)
    
    **Features:**
    - Email-based authentication
    - JWT access and refresh token generation
    - Session tracking
    - Activity logging
    
    **Returns:**
    - JWT access token (1 day expiry)
    - JWT refresh token (30 days expiry)
    - Token expiration information
    - User information
    - Success message
    """
    user = authenticate(username=data.email, password=data.password)
    if not user:
        raise HttpError(400, "Invalid credentials")
    if not user.is_active:
        raise HttpError(400, "User account is disabled")
    
    # Update last login
    user.last_login = timezone.now()
    user.save()
    
    # Generate JWT tokens
    tokens = generate_jwt_tokens(user, request)
    
    # Get access token lifetime from settings
    from django.conf import settings
    access_lifetime_seconds = int(settings.CUSTOM_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds())
    
    return {
        "access_token": tokens['access_token'],
        "refresh_token": tokens['refresh_token'],
        "token_type": "Bearer",
        "expires_in": access_lifetime_seconds,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
        },
        "message": "Login successful"
    }

@auth_router.post("/refresh/", response=RefreshTokenResponseSchema, summary="Refresh Access Token")
def refresh_token(request, data: RefreshTokenSchema):
    """
    Generate new access token using refresh token
    
    **Features:**
    - Refresh token validation
    - New access token generation
    - Session management
    - Activity logging
    
    **Returns:**
    - New JWT access token (1 day expiry)
    - Same refresh token
    - Token expiration information
    - Success message
    """
    try:
        tokens = refresh_jwt_token(data.refresh_token, request)
        
        # Get access token lifetime from settings
        from django.conf import settings
        access_lifetime_seconds = int(settings.CUSTOM_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds())
        
        return {
            "access_token": tokens['access_token'],
            "refresh_token": tokens['refresh_token'],
            "token_type": "Bearer",
            "expires_in": access_lifetime_seconds,
            "message": "Token refreshed successfully"
        }
    except Exception as e:
        raise HttpError(401, str(e))

@auth_router.post("/logout/", response=MessageResponseSchema, summary="User Logout")
def logout(request):
    """
    Logout user and revoke JWT token
    
    **Features:**
    - Token revocation
    - Session cleanup
    - Activity logging
    """
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        revoke_jwt_token(token, request)
    
    return {"message": "Logout successful"}

@auth_router.post("/change-password/", response=MessageResponseSchema, summary="Change Password")
def change_password(request, data: ChangePasswordSchema):
    """
    Change user password
    
    **Features:**
    - Current password verification
    - Password strength validation
    - Activity logging
    """
    user = request.auth
    if not user.check_password(data.old_password):
        raise HttpError(400, "Invalid old password")
    
    if data.new_password != data.new_password_confirm:
        raise HttpError(400, "New passwords don't match")
    
    user.set_password(data.new_password)
    user.save()
    
    # Log activity
    UserActivity.objects.create(
        user=user,
        activity_type='update',
        description='Password changed successfully',
        ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
        user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown')
    )
    
    return {"message": "Password changed successfully"}

class PasswordResetRequestSchema(Schema):
    email: str = Field(..., description="User email address", example="user@example.com")

class PasswordResetVerifySchema(Schema):
    email: str = Field(..., description="User email address", example="user@example.com")
    otp: str = Field(..., description="OTP code", example="123456")
    new_password: str = Field(..., description="New password", example="NewPass123!")
    new_password_confirm: str = Field(..., description="New password confirmation", example="NewPass123!")

@auth_router.post("/request-password-reset/", response=MessageResponseSchema, summary="Request Password Reset")
def request_password_reset(request, data: PasswordResetRequestSchema):
    """
    Request password reset using OTP verification
    
    **Features:**
    - Rate limiting
    - Email validation
    - OTP generation and sending
    - Activity logging
    
    **Process:**
    1. Validate email exists in system
    2. Generate and send OTP to email
    3. User receives OTP in email
    4. Use verify-password-reset to complete reset
    """
    try:
        # Check if user exists
        user = User.objects.get(email=data.email, is_active=True)
        
        # Import mailer service
        from apps.mailer.views import PasswordResetService
        
        # Request password reset through mailer service
        result = PasswordResetService.request_password_reset(data.email)
        
        # Log activity
        UserActivity.objects.create(
            user=user,
            activity_type='update',
            description=f'Password reset requested for: {data.email}',
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown'),
            metadata={
                'email_status': result.get('status', 'unknown'),
                'email_message': result.get('message', '')
            }
        )
        
        if result.get('status') == 'success':
            return {
                "message": "Password reset instructions sent to your email",
                "success": True
            }
        else:
            raise HttpError(500, result.get('message', 'Failed to send password reset email'))
            
    except User.DoesNotExist:
        # For security, don't reveal if email exists or not
        return {
            "message": "If the email exists in our system, password reset instructions have been sent",
            "success": True
        }
    except Exception as e:
        raise HttpError(500, f"Failed to process password reset request: {str(e)}")

@auth_router.post("/verify-password-reset/", response=MessageResponseSchema, summary="Verify Password Reset with OTP")
def verify_password_reset(request, data: PasswordResetVerifySchema):
    """
    Verify OTP and reset password
    
    **Features:**
    - OTP verification
    - Password validation
    - Password update
    - Session revocation
    - Activity logging
    
    **Process:**
    1. Verify OTP for the email
    2. Validate new password
    3. Update user password
    4. Revoke all existing sessions
    5. Log activity
    """
    try:
        # Check if user exists
        user = User.objects.get(email=data.email, is_active=True)
        
        # Validate password confirmation
        if data.new_password != data.new_password_confirm:
            raise HttpError(400, "New passwords don't match")
        
        # Import mailer service for OTP verification
        from apps.mailer.views import OTPService
        
        # Verify OTP
        otp_result = OTPService.verify_otp(data.email, data.otp)
        
        if otp_result.get('status') != 'success':
            raise HttpError(400, otp_result.get('message', 'Invalid or expired OTP'))
        
        # Update password
        user.set_password(data.new_password)
        user.save()
        
        # Revoke all existing sessions for security
        UserSession.objects.filter(user=user, is_active=True).update(is_active=False)
        
        # Log activity
        UserActivity.objects.create(
            user=user,
            activity_type='update',
            description=f'Password reset completed successfully for: {data.email}',
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown'),
            metadata={
                'otp_verified': True,
                'sessions_revoked': True
            }
        )
        
        return {
            "message": "Password reset successful. Please login with your new password.",
            "success": True
        }
        
    except User.DoesNotExist:
        raise HttpError(404, "User not found")
    except Exception as e:
        raise HttpError(500, f"Failed to reset password: {str(e)}")

# User management router
users_router = Router(tags=["User Management"])

@users_router.get("/", response=List[UserListResponseSchema], summary="List All Users", auth=jwt_auth)
@paginate
def list_users(request):
    """
    Get list of all users with access control based on user permissions
    
    **Permissions Required:**
    - Admin or Superadmin role for full access
    - Regular users can only see limited public information
    
    **Features:**
    - Pagination support
    - Role-based filtering
    - Activity tracking
    - Access control based on user permissions
    """
    current_user = request.auth
    if not current_user:
        raise HttpError(401, "Authentication required")
    
    # Check user permissions
    if not (current_user.is_admin or current_user.is_superadmin):
        raise HttpError(403, "Admin access required")
    
    users = User.objects.all().order_by('-created_at')
    
    # Return different data based on user access level
    if current_user.is_superadmin:
        # Superadmin gets full access to all user data
        return [
            {
                "id": str(u.id),
                "email": u.email,
                "username": u.username,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
                "last_login": u.last_login.isoformat() if u.last_login else None,
                "phone_number": u.phone_number,
                "bio": u.bio
            }
            for u in users
        ]
    elif current_user.is_admin:
        # Admin gets limited access (no sensitive data like phone numbers)
        return [
            {
                "id": str(u.id),
                "email": u.email,
                "username": u.username,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
                "last_login": u.last_login.isoformat() if u.last_login else None,
            }
            for u in users
        ]
    else:
        # This shouldn't happen due to the permission check above, but just in case
        raise HttpError(403, "Insufficient permissions")

@users_router.post("/", response=UserResponseSchema, summary="Create New User", auth=jwt_auth)
def create_user(request, data: UserRegistrationSchema):
    """
    Create new user with hierarchical permissions
    
    **Permissions Required (as per README.md):**
    - Super Admin: can create anyone (superadmin, admin, dev, visitor)
    - Admin: can create dev and visitor (cannot create other admins or superadmins)
    - Developer: can create visitor only
    - Visitor: cannot create anyone
    
    **Features:**
    - Hierarchical role assignment
    - Password validation
    - Activity logging
    """
    current_user = request.auth
    if not current_user:
        raise HttpError(401, "Authentication required")
    
    # Check if current user can create users at all
    if not current_user.can_create_user_with_role('visitor'):  # Basic check
        raise HttpError(403, "You don't have permission to create users")
    
    # Check if current user can create user with the requested role
    target_role = data.role or 'visitor'
    if not current_user.can_create_user_with_role(target_role):
        allowed_roles = {
            'superadmin': ['superadmin', 'admin', 'dev', 'visitor'],
            'admin': ['dev', 'visitor'],  # Admin CANNOT create other admins or superadmins
            'dev': ['visitor'],
            'visitor': []
        }.get(current_user.role, [])
        
        raise HttpError(403, f"You can only create users with roles: {', '.join(allowed_roles)}")
    
    if data.password != data.password_confirm:
        raise HttpError(400, "Passwords don't match")
    
    if User.objects.filter(email=data.email).exists():
        raise HttpError(400, "Email already exists")
    
    # Store plain password before hashing for email
    plain_password = data.password
    
    new_user = User.objects.create_user(
        email=data.email,
        username=data.username or data.email.split('@')[0],
        password=data.password,
        first_name=data.first_name or "",
        last_name=data.last_name or "",
        role=data.role or "visitor",
        phone_number=data.phone_number,
        bio=data.bio or "",
        is_active=True,
        is_verified=True
    )
    
    # Log activity
    UserActivity.objects.create(
        user=current_user,
        activity_type='create',
        description=f'Created new user: {new_user.email} with role {new_user.role}',
        ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
        user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown')
    )
    
    # Send credentials email to the new user
    try:
        from apps.mailer.views import UserCredentialsEmailService
        
        user_data = {
            'id': new_user.id,
            'email': new_user.email,
            'username': new_user.username,
            'first_name': new_user.first_name,
            'last_name': new_user.last_name,
            'role': new_user.role
        }
        
        email_result = UserCredentialsEmailService.send_user_credentials_email(
            user_data=user_data,
            created_by_user=current_user,
            plain_password=plain_password
        )
        
        # Log email activity
        UserActivity.objects.create(
            user=current_user,
            activity_type='create',
            description=f'Sent credentials email to new user: {new_user.email} - Status: {email_result.get("status")}',
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown'),
            metadata={
                'email_status': email_result.get('status'),
                'email_message': email_result.get('message'),
                'recipient_email': new_user.email,
                'recipient_role': new_user.role
            }
        )
        
    except Exception as email_error:
        # Log the error but don't fail user creation
        UserActivity.objects.create(
            user=current_user,
            activity_type='create',
            description=f'Failed to send credentials email to new user: {new_user.email} - Error: {str(email_error)}',
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown'),
            metadata={
                'email_error': str(email_error),
                'recipient_email': new_user.email,
                'recipient_role': new_user.role
            }
        )
        print(f"Failed to send credentials email: {str(email_error)}")
    
    return {
        "id": str(new_user.id),
        "email": new_user.email,
        "username": new_user.username,
        "first_name": new_user.first_name,
        "last_name": new_user.last_name,
        "role": new_user.role,
        "is_active": new_user.is_active,
        "is_verified": new_user.is_verified,
        "phone_number": new_user.phone_number,
        "bio": new_user.bio,
        "created_at": new_user.created_at.isoformat(),
        "updated_at": new_user.updated_at.isoformat(),
        "last_login": new_user.last_login.isoformat() if new_user.last_login else None,
    }

@users_router.get("/{user_id}/", response=UserResponseSchema, summary="Get User Details", auth=jwt_auth)
def get_user(request, user_id: str):
    """
    Get detailed user information
    
    **Permissions:**
    - Own profile: Any authenticated user
    - Other profiles: Admin/Superadmin only
    """
    current_user = request.auth
    target_user = get_object_or_404(User, id=user_id)
    
    # Check permissions
    if str(current_user.id) != user_id and not (current_user.is_admin or current_user.is_superadmin):
        raise HttpError(403, "Access denied")
    
    return {
        "id": str(target_user.id),
        "email": target_user.email,
        "username": target_user.username,
        "first_name": target_user.first_name,
        "last_name": target_user.last_name,
        "role": target_user.role,
        "is_active": target_user.is_active,
        "is_verified": target_user.is_verified,
        "phone_number": target_user.phone_number,
        "bio": target_user.bio,
        "created_at": target_user.created_at.isoformat(),
        "updated_at": target_user.updated_at.isoformat(),
        "last_login": target_user.last_login.isoformat() if target_user.last_login else None,
    }

@users_router.put("/{user_id}/", response=UserResponseSchema, summary="Update User", auth=jwt_auth)
def update_user(request, user_id: str, data: UserUpdateSchema):
    """
    Update user information including activation status
    
    **Permissions:**
    - Own profile: Any authenticated user (except is_active)
    - Other profiles: Admin/Superadmin only
    - Activation status: Only admin/superadmin can change for other users
    
    **Features:**
    - Update basic profile information (username, first_name, last_name, phone_number, bio)
    - Change user activation status (is_active) with hierarchical permissions
    - Prevent self-deactivation for security
    - Comprehensive activity logging
    
    **Hierarchical Permissions for is_active:**
    - Superadmin: can activate/deactivate anyone
    - Admin: can activate/deactivate dev and visitor users
    - Dev: can activate/deactivate visitor users only
    - Visitor: cannot change activation status of others
    """
    current_user = request.auth
    target_user = get_object_or_404(User, id=user_id)
    
    # Check permissions
    if str(current_user.id) != user_id and not (current_user.is_admin or current_user.is_superadmin):
        raise HttpError(403, "Access denied")
    
    # Check if user is trying to change activation status
    if data.is_active is not None:
        # Only admin/superadmin can change activation status of other users
        if str(current_user.id) != user_id and not (current_user.is_admin or current_user.is_superadmin):
            raise HttpError(403, "Only admin users can change activation status of other users")
        
        # Check if current user can manage this target user (hierarchical permissions)
        if str(current_user.id) != user_id and not current_user.can_manage_user(target_user):
            raise HttpError(403, f"You cannot manage users with role '{target_user.role}'")
        
        # Prevent users from deactivating themselves
        if str(current_user.id) == user_id and not data.is_active:
            raise HttpError(400, "You cannot deactivate your own account")
    
    # Update fields
    if data.username:
        target_user.username = data.username
    if data.first_name is not None:
        target_user.first_name = data.first_name
    if data.last_name is not None:
        target_user.last_name = data.last_name
    if data.phone_number is not None:
        target_user.phone_number = data.phone_number
    if data.bio is not None:
        target_user.bio = data.bio
    if data.is_active is not None:
        target_user.is_active = data.is_active
    
    target_user.save()
    
    # Prepare activity description
    activity_description = f'Updated user profile: {target_user.email}'
    activity_metadata = {}
    
    # Add specific information about what was updated
    updated_fields = []
    if data.username:
        updated_fields.append('username')
    if data.first_name is not None:
        updated_fields.append('first_name')
    if data.last_name is not None:
        updated_fields.append('last_name')
    if data.phone_number is not None:
        updated_fields.append('phone_number')
    if data.bio is not None:
        updated_fields.append('bio')
    if data.is_active is not None:
        updated_fields.append('is_active')
        activity_description = f'Updated user profile: {target_user.email} - Status changed to {"active" if data.is_active else "inactive"}'
        activity_metadata['activation_status_changed'] = True
        activity_metadata['new_status'] = 'active' if data.is_active else 'inactive'
    
    if updated_fields:
        activity_metadata['updated_fields'] = updated_fields
    
    # Log activity
    UserActivity.objects.create(
        user=current_user,
        activity_type='update',
        description=activity_description,
        ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
        user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown'),
        metadata=activity_metadata
    )
    
    return {
        "id": str(target_user.id),
        "email": target_user.email,
        "username": target_user.username,
        "first_name": target_user.first_name,
        "last_name": target_user.last_name,
        "role": target_user.role,
        "is_active": target_user.is_active,
        "is_verified": target_user.is_verified,
        "phone_number": target_user.phone_number,
        "bio": target_user.bio,
        "created_at": target_user.created_at.isoformat(),
        "updated_at": target_user.updated_at.isoformat(),
        "last_login": target_user.last_login.isoformat() if target_user.last_login else None,
    }

@users_router.post("/{user_id}/activate/", response=MessageResponseSchema, summary="Toggle User Activation", auth=jwt_auth)
def toggle_user_activation(request, user_id: str):
    """
    Activate or deactivate user account with hierarchical permissions
    
    **Permissions Required:**
    - Superadmin: can activate/deactivate anyone
    - Admin: can activate/deactivate dev and visitor users
    - Dev: can activate/deactivate visitor users
    - Visitor: cannot activate/deactivate anyone
    """
    current_user = request.auth
    if not current_user:
        raise HttpError(401, "Authentication required")
    
    # Check if current user can manage users at all
    if not current_user.can_create_user_with_role('visitor'):  # Basic check
        raise HttpError(403, "You don't have permission to manage user accounts")
    
    target_user = get_object_or_404(User, id=user_id)
    
    # Check if current user can manage this target user
    if not current_user.can_manage_user(target_user):
        raise HttpError(403, f"You cannot manage users with role '{target_user.role}'")
    
    target_user.is_active = not target_user.is_active
    target_user.save()
    
    action = 'activated' if target_user.is_active else 'deactivated'
    
    # Log activity
    UserActivity.objects.create(
        user=current_user,
        activity_type='update',
        description=f'User {action}: {target_user.email}',
        ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
        user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown')
    )
    
    return {
        "message": f"User {action} successfully",
        "success": True
    }

@users_router.post("/{user_id}/change-role/", response=MessageResponseSchema, summary="Change User Role", auth=jwt_auth)
def change_user_role(request, user_id: str, data: RoleUpdateSchema):
    """
    Change user role with hierarchical permissions
    
    **Permissions Required:**
    - Superadmin: can assign any role (superadmin, admin, dev, visitor)
    - Admin: can assign dev and visitor roles
    - Dev: can assign visitor role
    - Visitor: cannot change roles
    
    **Available Roles:**
    - superadmin: Full system access
    - admin: User management and admin features
    - dev: Development features access
    - visitor: Basic read-only access
    """
    current_user = request.auth
    if not current_user:
        raise HttpError(401, "Authentication required")
    
    # Check if current user can assign roles at all
    if not current_user.can_create_user_with_role('visitor'):  # Basic check
        raise HttpError(403, "You don't have permission to change user roles")
    
    target_user = get_object_or_404(User, id=user_id)
    
    # Check if current user can manage this target user (prevents admin from managing other admin/superadmin)
    if not current_user.can_manage_user(target_user):
        raise HttpError(403, f"You cannot manage users with role '{target_user.role}'")
    
    # Check if current user can assign the requested role
    if not current_user.can_create_user_with_role(data.role):
        allowed_roles = {
            'superadmin': ['superadmin', 'admin', 'dev', 'visitor'],
            'admin': ['admin', 'dev', 'visitor'],  # Admin can now assign admin role
            'dev': ['visitor'],
            'visitor': []
        }.get(current_user.role, [])
        
        raise HttpError(403, f"You can only assign roles: {', '.join(allowed_roles)}")
    
    valid_roles = ['superadmin', 'admin', 'dev', 'visitor']
    if data.role not in valid_roles:
        raise HttpError(400, f"Invalid role. Must be one of: {', '.join(valid_roles)}")
    
    # Prevent users from changing their own role to a lower level (security measure)
    if str(current_user.id) == user_id and data.role != current_user.role:
        current_role_level = {'superadmin': 4, 'admin': 3, 'dev': 2, 'visitor': 1}
        if current_role_level.get(data.role, 0) < current_role_level.get(current_user.role, 0):
            raise HttpError(403, "You cannot downgrade your own role")
    
    old_role = target_user.role
    target_user.role = data.role
    target_user.save()
    
    # Log activity
    UserActivity.objects.create(
        user=current_user,
        activity_type='update',
        description=f'Role changed from {old_role} to {data.role} for user {target_user.email}',
        ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
        user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown')
    )
    
    return {
        "message": f"User role changed to {data.role}",
        "success": True
    }

@users_router.delete("/{user_id}/", response=MessageResponseSchema, summary="Delete User", auth=jwt_auth)
def delete_user(request, user_id: str):
    """
    Delete user account with hierarchical permissions
    
    **Permissions Required:**
    - Superadmin: can delete anyone (except themselves)
    - Admin: can delete dev and visitor users
    - Dev: can delete visitor users
    - Visitor: cannot delete anyone
    
    **Warning:**
    - This action is irreversible
    - All user data will be permanently deleted
    """
    current_user = request.auth
    if not current_user:
        raise HttpError(401, "Authentication required")
    
    # Check if current user can delete users at all
    if not current_user.can_create_user_with_role('visitor'):  # Basic check
        raise HttpError(403, "You don't have permission to delete users")
    
    target_user = get_object_or_404(User, id=user_id)
    
    # Check if current user can manage this target user
    if not current_user.can_manage_user(target_user):
        raise HttpError(403, f"You cannot delete users with role '{target_user.role}'")
    
    if target_user.id == current_user.id:
        raise HttpError(400, "Cannot delete your own account")
    
    user_email = target_user.email
    target_user.delete()
    
    # Log activity
    UserActivity.objects.create(
        user=current_user,
        activity_type='delete',
        description=f'Deleted user account: {user_email}',
        ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
        user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown')
    )
    
    return {
        "message": f"User {user_email} deleted successfully",
        "success": True
    }

# Profile router
profile_router = Router(tags=["User Profile"])

@profile_router.get("/", response=UserResponseSchema, summary="Get Current User Profile", auth=jwt_auth)
def get_profile(request):
    """
    Get current authenticated user's profile
    
    **Authentication Required**
    """
    user = request.auth
    
    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "phone_number": user.phone_number,
        "bio": user.bio,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }

@profile_router.put("/", response=UserResponseSchema, summary="Update Current User Profile", auth=jwt_auth)
def update_profile(request, data: UserUpdateSchema):
    """
    Update current authenticated user's profile
    
    **Authentication Required**
    """
    user = request.auth
    
    # Update fields
    if data.username:
        user.username = data.username
    if data.first_name is not None:
        user.first_name = data.first_name
    if data.last_name is not None:
        user.last_name = data.last_name
    if data.phone_number is not None:
        user.phone_number = data.phone_number
    if data.bio is not None:
        user.bio = data.bio
    
    user.save()
    
    # Log activity
    UserActivity.objects.create(
        user=user,
        activity_type='update',
        description='Profile updated successfully',
        ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
        user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown')
    )
    
    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "phone_number": user.phone_number,
        "bio": user.bio,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }

# Activity router
activity_router = Router(tags=["User Activity"])

@activity_router.get("/", response=List[UserActivityResponseSchema], summary="Get User Activities", auth=jwt_auth)
@paginate
def get_activities(request, user_id: str = None):
    """
    Get user activity logs (Admin/Superadmin only)
    
    **Permissions Required:**
    - Admin or Superadmin role
    
    **Query Parameters:**
    - user_id: Filter activities for specific user
    """
    current_user = request.auth
    if not (current_user.is_admin or current_user.is_superadmin):
        raise HttpError(403, "Admin access required")
    
    activities = UserActivity.objects.all().order_by('-created_at')
    
    if user_id:
        activities = activities.filter(user_id=user_id)
    
    return [
        {
            "id": str(activity.id),
            "activity_type": activity.activity_type,
            "description": activity.description,
            "ip_address": activity.ip_address,
            "created_at": activity.created_at.isoformat(),
            "metadata": activity.metadata,
        }
        for activity in activities
    ]

# Session router
session_router = Router(tags=["User Sessions"])

@session_router.get("/", response=List[UserSessionResponseSchema], summary="Get User Sessions", auth=jwt_auth)
@paginate
def get_sessions(request, user_id: str = None):
    """
    Get user session information (Admin/Superadmin only)
    
    **Permissions Required:**
    - Admin or Superadmin role
    
    **Query Parameters:**
    - user_id: Filter sessions for specific user
    """
    current_user = request.auth
    if not (current_user.is_admin or current_user.is_superadmin):
        raise HttpError(403, "Admin access required")
    
    sessions = UserSession.objects.all().order_by('-created_at')
    
    if user_id:
        sessions = sessions.filter(user_id=user_id)
    
    return [
        {
            "id": str(session.id),
            "created_at": session.created_at.isoformat(),
            "expires_at": session.expires_at.isoformat(),
            "is_active": session.is_active,
            "ip_address": session.ip_address,
        }
        for session in sessions
    ]

@session_router.post("/revoke-all/", response=MessageResponseSchema, summary="Revoke All User Sessions", auth=jwt_auth)
def revoke_all_sessions(request, user_id: str):
    """
    Revoke all active sessions for a user (Admin/Superadmin only)
    
    **Permissions Required:**
    - Admin or Superadmin role
    
    **Use Cases:**
    - Security breach response
    - Force user logout
    - Account maintenance
    """
    current_user = request.auth
    if not (current_user.is_admin or current_user.is_superadmin):
        raise HttpError(403, "Admin access required")
    
    target_user = get_object_or_404(User, id=user_id)
    sessions = UserSession.objects.filter(user=target_user, is_active=True)
    session_count = sessions.count()
    sessions.update(is_active=False)
    
    # Log activity
    UserActivity.objects.create(
        user=current_user,
        activity_type='update',
        description=f'Revoked all sessions for user {target_user.email}',
        ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
        user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown')
    )
    
    return {
        "message": f"Revoked {session_count} sessions for user {target_user.email}",
        "success": True
    }

# Add routers to main API
api.add_router("/auth", auth_router)
api.add_router("/users", users_router)
api.add_router("/profile", profile_router)
api.add_router("/activities", activity_router)
api.add_router("/sessions", session_router)

# Update routers with authentication (except auth router)
for router_path, router in [
    ("/users", users_router),
    ("/profile", profile_router), 
    ("/activities", activity_router),
    ("/sessions", session_router)
]:
    router.auth = jwt_auth
