import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from .models import UserSession, UserActivity
from django.utils import timezone

User = get_user_model()


def generate_jwt_tokens(user, request=None):
    """
    Generate JWT access and refresh tokens for user authentication
    """
    import uuid
    
    # Get token lifetimes from settings
    access_lifetime = settings.CUSTOM_JWT['ACCESS_TOKEN_LIFETIME']
    refresh_lifetime = settings.CUSTOM_JWT['REFRESH_TOKEN_LIFETIME']
    algorithm = settings.CUSTOM_JWT['ALGORITHM']
    signing_key = settings.CUSTOM_JWT['SIGNING_KEY']
    
    # Generate access token
    access_payload = {
        'user_id': str(user.id),
        'email': user.email,
        'role': user.role,
        'exp': datetime.utcnow() + access_lifetime,
        'iat': datetime.utcnow(),
        'jti': str(uuid.uuid4()),  # Add unique token ID
        'type': 'access'
    }
    
    # Generate refresh token
    refresh_payload = {
        'user_id': str(user.id),
        'exp': datetime.utcnow() + refresh_lifetime,
        'iat': datetime.utcnow(),
        'jti': str(uuid.uuid4()),  # Add unique token ID
        'type': 'refresh'
    }
    
    access_token = jwt.encode(access_payload, signing_key, algorithm=algorithm)
    refresh_token = jwt.encode(refresh_payload, signing_key, algorithm=algorithm)
    
    # Create user session with both tokens
    access_expires_at = timezone.now() + access_lifetime
    refresh_expires_at = timezone.now() + refresh_lifetime
    
    session = UserSession.objects.create(
        user=user,
        token=access_token,
        refresh_token=refresh_token,
        expires_at=access_expires_at,
        refresh_expires_at=refresh_expires_at,
        ip_address=request.META.get('REMOTE_ADDR') if request else '127.0.0.1',
        user_agent=request.META.get('HTTP_USER_AGENT') if request else 'Unknown'
    )
    
    # Log login activity
    UserActivity.objects.create(
        user=user,
        activity_type='login',
        description=f'User logged in successfully',
        ip_address=request.META.get('REMOTE_ADDR') if request else '127.0.0.1',
        user_agent=request.META.get('HTTP_USER_AGENT') if request else 'Unknown'
    )
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'access_expires_at': access_expires_at,
        'refresh_expires_at': refresh_expires_at
    }


def generate_jwt_token(user, request=None):
    """
    Backward compatibility wrapper - generates both tokens but returns only access token
    """
    tokens = generate_jwt_tokens(user, request)
    return tokens['access_token']


def verify_jwt_token(token, token_type='access'):
    """
    Verify JWT token and return user
    """
    try:
        # Get settings
        algorithm = settings.CUSTOM_JWT['ALGORITHM']
        signing_key = settings.CUSTOM_JWT['SIGNING_KEY']
        
        payload = jwt.decode(token, signing_key, algorithms=[algorithm])
        user_id = payload.get('user_id')
        token_type_from_payload = payload.get('type', 'access')
        
        if not user_id:
            raise AuthenticationFailed('Invalid token')
        
        if token_type_from_payload != token_type:
            raise AuthenticationFailed(f'Invalid token type. Expected {token_type}, got {token_type_from_payload}')
        
        user = User.objects.get(id=user_id, is_active=True)
        
        # Check if session is still active
        try:
            if token_type == 'access':
                # Try to find session with token as string or bytes
                try:
                    session = UserSession.objects.get(token=token, is_active=True)
                except UserSession.DoesNotExist:
                    # Try with token as bytes (for compatibility)
                    session = UserSession.objects.get(token=token.encode('utf-8'), is_active=True)
                
                if session.is_expired():
                    raise AuthenticationFailed('Access token expired')
            else:  # refresh token
                # Try to find session with refresh_token as string or bytes
                try:
                    session = UserSession.objects.get(refresh_token=token, is_active=True)
                except UserSession.DoesNotExist:
                    # Try with token as bytes (for compatibility)
                    session = UserSession.objects.get(refresh_token=token.encode('utf-8'), is_active=True)
                
                if session.is_refresh_expired():
                    session.is_active = False
                    session.save()
                    raise AuthenticationFailed('Refresh token expired')
        except UserSession.DoesNotExist:
            raise AuthenticationFailed('Invalid session')
        
        return user
        
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed('Token expired')
    except jwt.InvalidTokenError:
        raise AuthenticationFailed('Invalid token')
    except User.DoesNotExist:
        raise AuthenticationFailed('User not found')


def refresh_jwt_token(refresh_token, request=None):
    """
    Generate new access token using refresh token
    """
    try:
        # Verify refresh token
        user = verify_jwt_token(refresh_token, token_type='refresh')
        
        # Find the session with this refresh token
        session = UserSession.objects.get(refresh_token=refresh_token, is_active=True)
        
        # Get settings
        access_lifetime = settings.CUSTOM_JWT['ACCESS_TOKEN_LIFETIME']
        algorithm = settings.CUSTOM_JWT['ALGORITHM']
        signing_key = settings.CUSTOM_JWT['SIGNING_KEY']
        
        # Generate new access token
        import uuid
        access_payload = {
            'user_id': str(user.id),
            'email': user.email,
            'role': user.role,
            'exp': datetime.utcnow() + access_lifetime,
            'iat': datetime.utcnow(),
            'jti': str(uuid.uuid4()),  # Add unique token ID
            'type': 'access'
        }
        
        new_access_token = jwt.encode(access_payload, signing_key, algorithm=algorithm)
        new_access_expires_at = timezone.now() + access_lifetime
        
        # Update session with new access token
        session.token = new_access_token
        session.expires_at = new_access_expires_at
        session.save()
        
        # Log token refresh activity
        UserActivity.objects.create(
            user=user,
            activity_type='update',
            description='Access token refreshed successfully',
            ip_address=request.META.get('REMOTE_ADDR') if request else '127.0.0.1',
            user_agent=request.META.get('HTTP_USER_AGENT') if request else 'Unknown'
        )
        
        return {
            'access_token': new_access_token,
            'refresh_token': refresh_token,  # Keep the same refresh token
            'access_expires_at': new_access_expires_at,
            'refresh_expires_at': session.refresh_expires_at
        }
        
    except (AuthenticationFailed, UserSession.DoesNotExist) as e:
        raise AuthenticationFailed('Invalid or expired refresh token')


def revoke_jwt_token(token, request=None):
    """
    Revoke JWT token by deactivating the session
    """
    try:
        session = UserSession.objects.get(token=token, is_active=True)
        session.is_active = False
        session.save()
        
        # Log logout activity
        if session.user:
            UserActivity.objects.create(
                user=session.user,
                activity_type='logout',
                description=f'User logged out successfully',
                ip_address=request.META.get('REMOTE_ADDR') if request else '127.0.0.1',
                user_agent=request.META.get('HTTP_USER_AGENT') if request else 'Unknown'
            )
        
        return True
    except UserSession.DoesNotExist:
        return False


class JWTAuthentication(authentication.BaseAuthentication):
    """
    Custom JWT authentication class
    """
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header:
            return None
        
        try:
            # Extract token from "Bearer <token>"
            token = auth_header.split(' ')[1]
            user = verify_jwt_token(token)
            return (user, token)
        except (IndexError, AuthenticationFailed):
            return None
    
    def authenticate_header(self, request):
        return 'Bearer realm="api"'
