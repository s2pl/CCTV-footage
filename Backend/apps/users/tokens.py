import uuid
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from .models import User


class TokenGenerator:
    """
    Base class for token generation
    """
    
    def __init__(self, expiry_hours=24):
        self.expiry_hours = expiry_hours
    
    def make_token(self, user):
        """
        Generate a token for the user
        """
        timestamp = timezone.now().timestamp()
        user_id = str(user.id)
        
        # Create a unique token based on user data and timestamp
        token_data = f"{user_id}:{timestamp}:{user.email}"
        token = uuid.uuid5(uuid.NAMESPACE_DNS, token_data).hex
        
        return token
    
    def check_token(self, user, token):
        """
        Check if a token is valid for a user
        """
        expected_token = self.make_token(user)
        return token == expected_token


class PasswordResetTokenGenerator(TokenGenerator):
    """
    Token generator for password reset
    """
    
    def __init__(self):
        super().__init__(expiry_hours=24)
    
    def make_token(self, user):
        """
        Generate password reset token
        """
        timestamp = timezone.now().timestamp()
        user_id = str(user.id)
        
        # Include password hash to invalidate token when password changes
        token_data = f"{user_id}:{timestamp}:{user.password}"
        token = uuid.uuid5(uuid.NAMESPACE_DNS, token_data).hex
        
        return token


class EmailVerificationTokenGenerator(TokenGenerator):
    """
    Token generator for email verification
    """
    
    def __init__(self):
        super().__init__(expiry_hours=48)
    
    def make_token(self, user):
        """
        Generate email verification token
        """
        timestamp = timezone.now().timestamp()
        user_id = str(user.id)
        
        # Include email to invalidate token when email changes
        token_data = f"{user_id}:{timestamp}:{user.email}"
        token = uuid.uuid5(uuid.NAMESPACE_DNS, token_data).hex
        
        return token


# Default token generators
password_reset_token_generator = PasswordResetTokenGenerator()
email_verification_token_generator = EmailVerificationTokenGenerator()
