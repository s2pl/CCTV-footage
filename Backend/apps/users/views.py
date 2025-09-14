from rest_framework import status, viewsets, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from .models import User, UserSession, UserActivity
from .serializers import (
    UserSerializer, UserListSerializer, LoginSerializer, ChangePasswordSerializer,
    ResetPasswordSerializer, ResetPasswordConfirmSerializer, UserProfileSerializer,
    UserSessionSerializer, UserActivitySerializer
)
from .permissions import (
    IsSuperAdmin, IsAdmin, CanManageUsers, IsOwnerOrAdmin, IsOwnerOrReadOnly
)
from .auth import generate_jwt_token, revoke_jwt_token

User = get_user_model()


class AuthViewSet(viewsets.ViewSet):
    """
    Authentication endpoints
    """
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """User login endpoint"""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Update last login
            user.last_login = timezone.now()
            user.save()
            
            # Generate JWT token
            token = generate_jwt_token(user, request)
            
            return Response({
                'token': token,
                'user': UserSerializer(user).data,
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """User logout endpoint"""
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header:
            token = auth_header.split(' ')[1]
            if revoke_jwt_token(token, request):
                return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
        
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change user password"""
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.validated_data['old_password']):
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                
                # Log activity
                UserActivity.objects.create(
                    user=user,
                    activity_type='update',
                    description='Password changed successfully',
                    ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
                    user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown')
                )
                
                return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid old password'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def reset_password(self, request):
        """Request password reset"""
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email, is_active=True)
                # Here you would typically send an email with reset link
                # For now, just return success message
                return Response({
                    'message': 'Password reset email sent if account exists'
                }, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                # Don't reveal if user exists or not
                return Response({
                    'message': 'Password reset email sent if account exists'
                }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def reset_password_confirm(self, request):
        """Confirm password reset with token"""
        serializer = ResetPasswordConfirmSerializer(data=request.data)
        if serializer.is_valid():
            # Here you would validate the token and reset password
            # For now, just return success message
            return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """
    User management endpoints
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, CanManageUsers]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return UserProfileSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsSuperAdmin]
        elif self.action in ['update', 'partial_update']:
            self.permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
        return super().get_permissions()
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Get current user profile"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Update current user profile"""
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate/deactivate user"""
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        
        action = 'activated' if user.is_active else 'deactivated'
        
        # Log activity
        UserActivity.objects.create(
            user=request.user,
            activity_type='update',
            description=f'User {action}: {user.email}',
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown')
        )
        
        return Response({
            'message': f'User {action} successfully',
            'is_active': user.is_active
        })
    
    @action(detail=True, methods=['post'])
    def change_role(self, request, pk=None):
        """Change user role (superadmin only)"""
        if not request.user.is_superadmin:
            return Response({'error': 'Only superadmin can change roles'}, status=status.HTTP_403_FORBIDDEN)
        
        user = self.get_object()
        new_role = request.data.get('role')
        
        if new_role not in dict(User.ROLE_CHOICES):
            return Response({'error': 'Invalid role'}, status=status.HTTP_400_BAD_REQUEST)
        
        old_role = user.role
        user.role = new_role
        user.save()
        
        # Log activity
        UserActivity.objects.create(
            user=request.user,
            activity_type='update',
            description=f'Role changed from {old_role} to {new_role} for user {user.email}',
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown')
        )
        
        return Response({
            'message': f'User role changed to {new_role}',
            'new_role': new_role
        })


class UserSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    User session management (read-only for admins)
    """
    queryset = UserSession.objects.all()
    serializer_class = UserSessionSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    
    @action(detail=False, methods=['post'])
    def revoke_all(self, request):
        """Revoke all active sessions for a user"""
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
            sessions = UserSession.objects.filter(user=user, is_active=True)
            sessions.update(is_active=False)
            
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                activity_type='update',
                description=f'Revoked all sessions for user {user.email}',
                ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
                user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown')
            )
            
            return Response({
                'message': f'Revoked {sessions.count()} sessions for user {user.email}'
            })
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class UserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    User activity logging (read-only for admins)
    """
    queryset = UserActivity.objects.all()
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.query_params.get('user_id')
        activity_type = self.request.query_params.get('activity_type')
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
        
        return queryset


class CreateUserView(generics.CreateAPIView):
    """
    Create new user (superadmin only)
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def perform_create(self, serializer):
        user = serializer.save()
        
        # Log activity
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='create',
            description=f'Created new user: {user.email} with role {user.role}',
            ip_address=self.request.META.get('REMOTE_ADDR', '127.0.0.1'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', 'Unknown')
        )
        
        return user
