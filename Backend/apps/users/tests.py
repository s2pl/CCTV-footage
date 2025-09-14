from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.test import APIClient
from .models import UserSession, UserActivity
from .auth import generate_jwt_token, verify_jwt_token, revoke_jwt_token

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'visitor'
        }

    def test_create_user(self):
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, self.user_data['email'])
        self.assertEqual(user.role, self.user_data['role'])
        self.assertTrue(user.check_password(self.user_data['password']))

    def test_user_str_representation(self):
        user = User.objects.create_user(**self.user_data)
        expected = f"{user.email} ({user.get_role_display()})"
        self.assertEqual(str(user), expected)

    def test_user_role_properties(self):
        user = User.objects.create_user(**self.user_data)
        self.assertFalse(user.is_superadmin)
        self.assertFalse(user.is_admin)
        self.assertFalse(user.is_developer)

        # Test admin user
        admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )
        self.assertFalse(admin_user.is_superadmin)
        self.assertTrue(admin_user.is_admin)
        self.assertTrue(admin_user.is_developer)

        # Test superadmin user
        superadmin_user = User.objects.create_user(
            email='superadmin@example.com',
            password='superpass123',
            role='superadmin'
        )
        self.assertTrue(superadmin_user.is_superadmin)
        self.assertTrue(superadmin_user.is_admin)
        self.assertTrue(superadmin_user.is_developer)

    def test_user_permissions(self):
        user = User.objects.create_user(**self.user_data)
        self.assertFalse(user.can_manage_users())
        self.assertFalse(user.can_access_admin_panel())

        admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )
        self.assertTrue(admin_user.can_manage_users())
        self.assertTrue(admin_user.can_access_admin_panel())


class UserSessionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_create_session(self):
        session = UserSession.objects.create(
            user=self.user,
            token='test_token_123',
            expires_at='2024-12-31T23:59:59Z'
        )
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.token, 'test_token_123')
        self.assertTrue(session.is_active)

    def test_session_expiration(self):
        from django.utils import timezone
        from datetime import timedelta
        
        # Create expired session
        expired_time = timezone.now() - timedelta(hours=1)
        expired_session = UserSession.objects.create(
            user=self.user,
            token='expired_token',
            expires_at=expired_time
        )
        self.assertTrue(expired_session.is_expired())

        # Create valid session
        valid_time = timezone.now() + timedelta(hours=1)
        valid_session = UserSession.objects.create(
            user=self.user,
            token='valid_token',
            expires_at=valid_time
        )
        self.assertFalse(valid_session.is_expired())


class UserActivityTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_create_activity(self):
        activity = UserActivity.objects.create(
            user=self.user,
            activity_type='login',
            description='User logged in successfully',
            ip_address='127.0.0.1'
        )
        self.assertEqual(activity.user, self.user)
        self.assertEqual(activity.activity_type, 'login')
        self.assertEqual(activity.description, 'User logged in successfully')


class JWTAuthenticationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_generate_token(self):
        token = generate_jwt_token(self.user)
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 0)

    def test_verify_token(self):
        token = generate_jwt_token(self.user)
        verified_user = verify_jwt_token(token)
        self.assertEqual(verified_user, self.user)

    def test_revoke_token(self):
        token = generate_jwt_token(self.user)
        self.assertTrue(revoke_jwt_token(token))
        
        # Token should no longer be valid
        with self.assertRaises(Exception):
            verify_jwt_token(token)


class UserAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'visitor'
        }
        self.user = User.objects.create_user(**self.user_data)
        self.superadmin = User.objects.create_user(
            email='superadmin@example.com',
            password='superpass123',
            role='superadmin'
        )

    def test_user_login(self):
        url = reverse('auth-login')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)

    def test_user_login_invalid_credentials(self):
        url = reverse('auth-login')
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_profile_authenticated(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('users-profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

    def test_user_profile_unauthenticated(self):
        url = reverse('users-profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_user_superadmin_only(self):
        # Test as regular user (should fail)
        self.client.force_authenticate(user=self.user)
        url = reverse('create-user')
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'role': 'visitor'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test as superadmin (should succeed)
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_users_permission(self):
        # Regular user cannot list users
        self.client.force_authenticate(user=self.user)
        url = reverse('users-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin can list users
        admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )
        self.client.force_authenticate(user=admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PermissionTest(TestCase):
    def setUp(self):
        self.visitor = User.objects.create_user(
            email='visitor@example.com',
            password='visitorpass123',
            role='visitor'
        )
        self.dev = User.objects.create_user(
            email='dev@example.com',
            password='devpass123',
            role='dev'
        )
        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )
        self.superadmin = User.objects.create_user(
            email='superadmin@example.com',
            password='superpass123',
            role='superadmin'
        )

    def test_role_based_permissions(self):
        # Test visitor permissions
        self.assertFalse(self.visitor.can_manage_users())
        self.assertFalse(self.visitor.can_access_admin_panel())

        # Test developer permissions
        self.assertFalse(self.dev.can_manage_users())
        self.assertFalse(self.dev.can_access_admin_panel())

        # Test admin permissions
        self.assertTrue(self.admin.can_manage_users())
        self.assertTrue(self.admin.can_access_admin_panel())

        # Test superadmin permissions
        self.assertTrue(self.superadmin.can_manage_users())
        self.assertTrue(self.superadmin.can_access_admin_panel())
