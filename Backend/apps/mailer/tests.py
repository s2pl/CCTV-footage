from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core import mail

class EmailTestCase(TestCase):
    def setUp(self):
        # Create a test user
        User = get_user_model()
        self.user = User.objects.create_user(
            username='rishikesh',
            password='@Rishi21'
        )
        self.client = APIClient()

    def test_send_email(self):
        # 1. Get the token
        login_response = self.client.post('/api/token/', {
            'username': 'rishikesh',
            'password': '@Rishi21'
        }, format='json')
        
        self.assertEqual(login_response.status_code, 200)
        token = login_response.json()['access']

        # 2. Send email with token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        print(token)
        email_data = {
            'subject': 'Test Email',
            'message': 'This is a test email',
            'to_email': 'rishikesh21.job@gmail.com'
        }
        
        response = self.client.post('/mail/send/', email_data, format='json')
        self.assertEqual(response.status_code, 200)
        print(response.json())

class OTPTestCase(TestCase):
    def setUp(self):
        # Create a test user
        User = get_user_model()
        self.user = User.objects.create_user(
            username='rishikesh',
            password='@Rishi21'
        )
        self.client = APIClient()
        self.test_email = 'test@example.com'
        
        # Get authentication token
        login_response = self.client.post('/api/token/', {
            'username': 'rishikesh',
            'password': '@Rishi21'
        }, format='json')
        
        self.token = login_response.json()['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def tearDown(self):
        # Clear cache after each test
        cache.clear()

    def test_generate_otp(self):
        # Test OTP generation
        response = self.client.post('/mail/generate-otp/', {
            'to_email': self.test_email
        }, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['to_email'], self.test_email)
        
        # Check if email was sent
        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[0]
        self.assertEqual(sent_mail.to[0], self.test_email)
        self.assertEqual(sent_mail.subject, "Your Verification Code")

        # Extract OTP from email body (for testing verification)
        otp = ''.join(filter(str.isdigit, sent_mail.body))[:6]
        
        # Test OTP verification with correct OTP
        verify_response = self.client.post('/mail/verify-otp/', {
            'email': self.test_email,
            'otp': otp
        }, format='json')
        
        self.assertEqual(verify_response.status_code, 200)
        self.assertEqual(verify_response.json()['status'], 'success')

    def test_invalid_otp(self):
        # Generate OTP first
        self.client.post('/mail/generate-otp/', {
            'to_email': self.test_email
        }, format='json')

        # Test with wrong OTP
        response = self.client.post('/mail/verify-otp/', {
            'email': self.test_email,
            'otp': '000000'
        }, format='json')
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'Invalid OTP')

    def test_expired_otp(self):
        # Generate OTP
        self.client.post('/mail/generate-otp/', {
            'to_email': self.test_email
        }, format='json')

        # Clear cache to simulate expired OTP
        cache.clear()

        # Try to verify
        response = self.client.post('/mail/verify-otp/', {
            'email': self.test_email,
            'otp': '123456'
        }, format='json')
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'OTP has expired')

    def test_missing_data(self):
        # Test missing email in generate OTP
        response = self.client.post('/mail/generate-otp/', {}, format='json')
        self.assertEqual(response.status_code, 400)
        
        # Test missing data in verify OTP
        response = self.client.post('/mail/verify-otp/', {}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'Email and OTP are required')