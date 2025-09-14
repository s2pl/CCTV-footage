from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import EmailSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import random
from datetime import datetime, timedelta
from django.core.cache import cache
from django.conf import settings
from .models import OTP, EmailLog, CreatorBulkMail
from django.db.models import Q
from django.utils import timezone
import threading

def get_email_sender(account_type='invitation'):
    """
    Get the from_email address for a specific account type.
    
    Args:
        account_type (str): The type of email account to use ('invitation', 'no-reply', 'team')
        
    Returns:
        str: The email address to use as sender
    """
    if hasattr(settings, 'EMAIL_ACCOUNTS') and account_type in settings.EMAIL_ACCOUNTS:
        email_account = settings.EMAIL_ACCOUNTS[account_type]
        if 'display_name' in email_account:
            return f"{email_account['display_name']} <{email_account['email']}>"
        return email_account['email']
    
    # Fallback to default values
    if account_type == 'no-reply':
        return settings.OTP_EMAIL_FROM
    elif account_type == 'team':
        return 'team@createathon.co'
    
    # Default to the system default
    return settings.DEFAULT_FROM_EMAIL

class EmailService:
    @staticmethod
    def send_email(email_data):
        try:
            html_message = render_to_string('email/base_email.html', {
                'subject': email_data.subject,
                'message': email_data.message,
                'logo_url': settings.LOGO_URL
            })
            plain_message = strip_tags(email_data.message)

            # Determine email type from subject for appropriate sender
            email_type = 'team'  # Default to team
            subject_lower = email_data.subject.lower()
            
            # Use no-reply for verification and OTP emails
            if 'verification' in subject_lower or 'otp' in subject_lower or 'code' in subject_lower:
                email_type = 'no-reply'
                
            send_mail(
                subject=email_data.subject,
                message=plain_message,
                from_email=get_email_sender(email_type),
                recipient_list=[email_data.to_email],
                html_message=html_message,
            )
            
            # Log the email
            EmailLog.objects.create(
                subject=email_data.subject,
                message=plain_message,
                html_message=html_message,
                from_email=get_email_sender(email_type),
                to_email=email_data.to_email,
                priority='medium',
                status='sent'
            )
            
            return {"status": "success", "message": "Email sent successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def send_bulk_email(email_data_list):
        try:
            for email_data in email_data_list:
                EmailService.send_email(email_data)
            return {"status": "success", "message": "Bulk emails sent successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def send_email_with_attachment(email_data):
        try:
            html_message = render_to_string('email/base_email.html', {
                'subject': email_data.subject,
                'message': email_data.message,
            })
            plain_message = strip_tags(email_data.message)

            send_mail(
                subject=email_data.subject,
                message=plain_message,
                from_email='team@createathon.co',
                recipient_list=[email_data.to_email],
                html_message=html_message,
                attachments=email_data.attachments
            )
            return {"status": "success", "message": "Email with attachment sent successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class OTPService:
    @staticmethod
    def generate_otp(email):
        try:
            # Rate limiting check moved to the start
            cache_key = f"otp_limit_{email}"
            if cache.get(cache_key):
                return {
                    "status": "error",
                    "message": "Too many OTP requests. Please try again later."
                }
            
            # Set rate limit
            cache.set(cache_key, True, 60)  # 1 minute
            
            # Check if there's a recent OTP request
            last_otp = OTP.objects.filter(email=email).order_by('-created_at').first()
            if last_otp and (timezone.now() - last_otp.created_at).total_seconds() < 60:
                return {
                    "status": "error", 
                    "message": "Please wait 1 minute before requesting a new OTP",
                    "can_resend_at": (last_otp.created_at + timedelta(minutes=1)).strftime("%I:%M %p")
                }

            otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            expiry_time = timezone.now() + timedelta(minutes=5)  # Changed to 5 minutes
            cache.set(f"otp_{email}", otp, 300)  # 5 minutes

            # Store in database
            OTP.objects.create(
                email=email,
                otp_code=otp,
                created_at=timezone.now(),
                expires_at=expiry_time
            )

            html_message = render_to_string('email/otp_template.html', {
                'otp_code': otp,
                'expiry_time': expiry_time.strftime("%I:%M %p"),
                'logo_url': settings.LOGO_URL
            })

            send_mail(
                subject="Your Verification Code",
                message=f"Your OTP is: {otp}",
                from_email=get_email_sender('no-reply'),
                recipient_list=[email],
                html_message=html_message,
            )
            return {"status": "success", "message": "OTP sent successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def verify_otp(email, otp):
        try:
            # First check cache
            stored_otp = cache.get(f"otp_{email}")
            if not stored_otp:
                # If not in cache, check database
                otp_obj = OTP.objects.filter(
                    email=email,
                    otp_code=otp,
                    is_used=False,
                    expires_at__gt=timezone.now()
                ).first()
                
                if not otp_obj:
                    return {"status": "error", "message": "Invalid or expired OTP"}
                
                # Mark OTP as used
                otp_obj.is_used = True
                otp_obj.save()
                
                # Delete from cache if exists
                cache.delete(f"otp_{email}")
                
                # Send welcome email
                try:
                    WelcomeEmailService.send_welcome_email(email, email.split('@')[0])
                except Exception as e:
                    print(f"Failed to send welcome email: {str(e)}")
                
                return {"status": "success", "message": "OTP verified successfully"}
            
            # If in cache, verify against it
            if stored_otp != otp:
                return {"status": "error", "message": "Invalid OTP"}
            
            # Delete OTP from both cache and database after successful verification
            cache.delete(f"otp_{email}")
            OTP.objects.filter(email=email, otp_code=otp).update(is_used=True)
            
            # Send welcome email
            try:
                WelcomeEmailService.send_welcome_email(email, email.split('@')[0])
            except Exception as e:
                print(f"Failed to send welcome email: {str(e)}")
            
            return {"status": "success", "message": "OTP verified successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def resend_otp(email):
        try:
            # Check if there's a recent OTP request
            last_otp = OTP.objects.filter(email=email).order_by('-created_at').first()
            
            if not last_otp:
                return OTPService.generate_otp(email)
            
            # Check if 1 minute has passed since the last OTP
            time_diff = (timezone.now() - last_otp.created_at).total_seconds()
            if time_diff < 60:
                return {
                    "status": "error",
                    "message": "Please wait 1 minute before requesting a new OTP",
                    "can_resend_at": (last_otp.created_at + timedelta(minutes=1)).strftime("%I:%M %p")
                }
            
            # Delete old OTP
            cache.delete(f"otp_{email}")
            last_otp.delete()
            
            # Generate new OTP
            return OTPService.generate_otp(email)
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def cleanup_expired_otps():
        """Clean up expired OTPs from the database"""
        try:
            # Delete OTPs that are older than 5 minutes
            expired_time = timezone.now() - timedelta(minutes=5)
            OTP.objects.filter(
                Q(created_at__lt=expired_time) |  # OTPs older than 5 minutes
                Q(verified=True)  # Already verified OTPs
            ).delete()
        except Exception as e:
            print(f"Error cleaning up OTPs: {str(e)}")

class WelcomeEmailService:
    @staticmethod
    def send_welcome_email(email, fullname):
        try:
            html_message = render_to_string('email/welcome.html', {
                'fullname': fullname or "User",
                'logo_url': settings.LOGO_URL
            })
            
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject="Welcome to Our Platform!",
                message=plain_message,
                from_email=get_email_sender('team'),
                recipient_list=[email],
                html_message=html_message,
            )
            return {"status": "success", "message": "Welcome email sent successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class UserCredentialsEmailService:
    @staticmethod
    def send_user_credentials_email(user_data, created_by_user, plain_password):
        """
        Send email with user credentials when a new user is created
        
        Args:
            user_data: Dictionary containing user information (email, username, role, etc.)
            created_by_user: User object of the person who created this user
            plain_password: The plain text password before hashing
        """
        try:
            # Prepare template context
            context = {
                'user_name': user_data.get('first_name', '') + ' ' + user_data.get('last_name', '') or user_data.get('username', 'User'),
                'email': user_data.get('email'),
                'password': plain_password,
                'user_id': str(user_data.get('id', '')),
                'role': user_data.get('role', 'visitor'),
                'created_by_name': f"{created_by_user.first_name} {created_by_user.last_name}".strip() or created_by_user.username,
                'created_by_role': created_by_user.role,
                'logo_url': getattr(settings, 'LOGO_URL', ''),
                'login_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:3000') + '/login'
            }
            
            # Render HTML template
            html_message = render_to_string('email/user_credentials.html', context)
            
            # Create plain text version
            plain_message = f"""
Welcome to Our Platform!

Hello {context['user_name']},

Your account has been created by {context['created_by_name']} ({context['created_by_role']}).

Your Login Credentials:
- Email: {context['email']}
- Password: {context['password']}
- Role: {context['role']}
- Account ID: {context['user_id']}

SECURITY NOTICE: Please change your password after your first login for security purposes.

Next Steps:
1. Login to your account using the credentials above
2. Change your password in account settings
3. Complete your profile information
4. Explore the features available for your role

If you have any questions, please contact our support team.

Best regards,
Your Team
            """.strip()
            
            # Send email
            send_mail(
                subject=f"Your Account Credentials - {context['role'].title()} Access",
                message=plain_message,
                from_email=get_email_sender('team'),
                recipient_list=[user_data.get('email')],
                html_message=html_message,
                fail_silently=False
            )
            
            # Log the email
            try:
                from .models import EmailLog
                EmailLog.objects.create(
                    subject=f"Your Account Credentials - {context['role'].title()} Access",
                    message=plain_message,
                    html_message=html_message,
                    from_email=get_email_sender('team'),
                    to_email=user_data.get('email'),
                    priority='high',
                    status='sent'
                )
            except Exception as log_error:
                print(f"Failed to log email: {str(log_error)}")
            
            return {"status": "success", "message": "User credentials email sent successfully"}
            
        except Exception as e:
            print(f"Failed to send user credentials email: {str(e)}")
            return {"status": "error", "message": str(e)}

class SendEmailView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        # Add role-based check
        if not request.user.is_staff:
            return Response({
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
            
        try:
            emails_data = request.data

            if not isinstance(emails_data, list):
                emails_data = [emails_data]

            results = []
            for email_data in emails_data:
                serializer = EmailSerializer(data=email_data)
                if serializer.is_valid():
                    subject = serializer.validated_data['subject']
                    message = serializer.validated_data['message']
                    to_email = serializer.validated_data['to_email']

                    # Render HTML template
                    html_message = render_to_string('email/base_email.html', {
                        'subject': subject,
                        'message': message,
                    })
                    # Create plain text version
                    plain_message = strip_tags(message)

                    # Determine email type from subject
                    email_type = 'team'  # Default to team
                    subject_lower = subject.lower()
                    
                    # Use no-reply for verification and OTP emails
                    if 'verification' in subject_lower or 'otp' in subject_lower or 'code' in subject_lower:
                        email_type = 'no-reply'

                    try:
                        send_mail(
                            subject=subject,
                            message=plain_message,
                            from_email=get_email_sender(email_type),
                            recipient_list=[to_email],
                            html_message=html_message,
                            fail_silently=False
                        )
                        results.append({
                            'to_email': to_email,
                            'status': 'success',
                            'message': 'Email sent successfully'
                        })
                    except Exception as e:
                        results.append({
                            'to_email': to_email,
                            'status': 'error',
                            'message': str(e)
                        })

                    # Log the email
                    EmailLog.objects.create(
                        subject=subject,
                        message=plain_message,
                        html_message=html_message,
                        from_email=get_email_sender(email_type),
                        to_email=to_email,
                        priority='medium',
                        status='pending'
                    )

            return Response({'results': results}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Invalid JSON format or unexpected error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class GenerateOTPView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def generate_otp(self):
        """Generate a 6 digit random OTP"""
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])

    def store_otp(self, email, otp):
        """Store OTP in both cache and database"""
        # Store in cache for quick lookups
        expiry_time = 10 * 60  # 10 minutes in seconds
        cache_key = f"otp_{email}"
        cache.set(cache_key, otp, expiry_time)
        
        # Store in database for record keeping
        OTP.objects.create(
            email=email,
            otp_code=otp
        )

    def post(self, request):
        # Verify the email belongs to the requesting user
        email_data = request.data
        to_email = email_data.get('to_email')
        
        if not request.user.is_staff and request.user.email != to_email:
            return Response({
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
            
        try:
            if not to_email:
                return Response({
                    'error': 'Email address is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Generate OTP
            otp_code = self.generate_otp()
            
            # Store OTP in cache
            self.store_otp(to_email, otp_code)
            
            # Calculate expiry time for display
            expiry_time = timezone.now() + timedelta(minutes=10)
            expiry_time_str = expiry_time.strftime("%I:%M %p")

            # Render HTML template with OTP
            html_message = render_to_string('email/otp_template.html', {
                'otp_code': otp_code,
                'expiry_time': f'{expiry_time_str}',
                'logo_url': settings.LOGO_URL
            })
            
            # Create plain text version
            plain_message = f"Your verification code is: {otp_code}\nThis code will expire at {expiry_time_str}."

            try:
                send_mail(
                    subject="Your Verification Code",
                    message=plain_message,
                    from_email=get_email_sender('no-reply'),
                    recipient_list=[to_email],
                    html_message=html_message,
                    fail_silently=False
                )
                
                return Response({
                    'status': 'success',
                    'message': 'OTP sent successfully',
                    'to_email': to_email,
                    'expires_at': expiry_time_str
                }, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({
                    'status': 'error',
                    'message': str(e),
                    'to_email': to_email
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({
                'error': 'Invalid request format or unexpected error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        # Verify the email belongs to the requesting user
        email = request.data.get('email')
        otp = request.data.get('otp')
        
        if not request.user.is_staff and request.user.email != email:
            return Response({
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
            
        """Verify the OTP for a given email"""
        try:
            if not email or not otp:
                return Response({
                    'error': 'Email and OTP are required'
                }, status=status.HTTP_400_BAD_REQUEST)

            cache_key = f"otp_{email}"
            stored_otp = cache.get(cache_key)

            if not stored_otp:
                return Response({
                    'error': 'OTP has expired'
                }, status=status.HTTP_400_BAD_REQUEST)

            if stored_otp != otp:
                return Response({
                    'error': 'Invalid OTP'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Clear the OTP from cache after successful verification
            cache.delete(cache_key)

            return Response({
                'status': 'success',
                'message': 'OTP verified successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Verification failed',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class WelcomeEmailView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, *args, **kwargs):  # Add *args, **kwargs
        # Only staff can send welcome emails
        if not request.user.is_staff:
            return Response({
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
            
        try:
            email = request.data.get('email')
            user_name = request.data.get('user_name', '')  # Changed from fullname

            if not email:
                return Response({
                    'error': 'Email is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Render HTML template
            html_message = render_to_string('email/welcome_email.html', {
                'user_name': user_name,
                'logo_url': settings.LOGO_URL
            })
            
            # Create plain text version
            plain_message = f"Welcome to Our Platform!\n\nDear {user_name},\n\nThank you for joining our platform. We're excited to have you on board!\n\nIf you have any questions, feel free to reach out to our support team.\n\nBest regards,\nYour Team"

            send_mail(
                subject="Welcome to Our Platform!",
                message=plain_message,
                from_email=get_email_sender('team'),
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False
            )

            return Response({
                'status': 'success',
                'message': 'Welcome email sent successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Failed to send welcome email',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PasswordResetRequestView(APIView):
    # Allow unauthenticated users to request password reset
    permission_classes = [AllowAny]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        try:
            # Add rate limiting check
            email = request.data.get('email')
            cache_key = f"pwd_reset_{email}"
            
            # Check if there's a recent request
            if cache.get(cache_key):
                return Response({
                    'error': 'Please wait before requesting another reset'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
                
            # Set rate limit
            cache.set(cache_key, True, 300)  # 5 minutes
            
            if not email:
                return Response({
                    'error': 'Email is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Generate and store OTP
            otp_view = GenerateOTPView()
            otp_code = otp_view.generate_otp()
            otp_view.store_otp(email, otp_code)
            
            # Calculate expiry time
            expiry_time = timezone.now() + timedelta(minutes=10)
            expiry_time_str = expiry_time.strftime("%I:%M %p")

            # Render HTML template
            html_message = render_to_string('email/password_reset_email.html', {
                'otp_code': otp_code,
                'expiry_time': expiry_time_str,
                'logo_url': settings.LOGO_URL
            })
            
            # Create plain text version
            plain_message = f"Password Reset Request\n\nUse the following verification code to reset your password: {otp_code}\n\nThis code will expire at {expiry_time_str}."

            send_mail(
                subject="Password Reset Request",
                message=plain_message,
                from_email=get_email_sender('no-reply'),
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False
            )

            return Response({
                'status': 'success',
                'message': 'Password reset instructions sent successfully',
                'expires_at': expiry_time_str
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Failed to process password reset request',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PasswordResetService:
    permission_classes = [AllowAny]  # Allow unauthenticated for password reset
    authentication_classes = [JWTAuthentication]

    @staticmethod
    def request_password_reset(email):
        try:
            # Add rate limiting check
            cache_key = f"pwd_reset_service_{email}"
            
            if cache.get(cache_key):
                return {
                    "status": "error",
                    "message": "Please wait before requesting another reset"
                }
                
            # Set rate limit
            cache.set(cache_key, True, 300)  # 5 minutes
            
            # Use the existing OTPService to generate and send OTP
            otp_response = OTPService.generate_otp(email)
            if otp_response["status"] == "error":
                return otp_response

            # Customize the email template for password reset
            stored_otp = cache.get(f"otp_{email}")
            expiry_time = timezone.now() + timedelta(minutes=5)
            expiry_time_str = expiry_time.strftime("%I:%M %p")

            html_message = render_to_string('email/reset_password.html', {
                'otp_code': stored_otp,
                'expiry_time': expiry_time_str,
                'logo_url': settings.LOGO_URL
            })

            plain_message = strip_tags(html_message)

            send_mail(
                subject="Password Reset Request",
                message=plain_message,
                from_email=get_email_sender('no-reply'),
                recipient_list=[email],
                html_message=html_message,
            )

            # Log the email
            EmailLog.objects.create(
                subject="Password Reset Request",
                message=plain_message,
                html_message=html_message,
                from_email=get_email_sender('no-reply'),
                to_email=email,
                priority='high',
                status='sent'
            )

            return {
                "status": "success", 
                "message": "Password reset instructions sent successfully",
                "expires_at": expiry_time_str
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

class CreatorBulkMailService:
    @staticmethod
    def send_bulk_mail(mail_data):
        try:
            # Create bulk mail record
            bulk_mail = CreatorBulkMail.objects.create(
                campaign_name=mail_data.campaign_name,
                subject=mail_data.subject,
                message=mail_data.message,
                from_email=mail_data.from_email or 'invitation@createathon.co',
                template_name=mail_data.template_name,
                recipient_list=mail_data.recipient_list,
                template_context=mail_data.template_context,
                total_recipients=len(mail_data.recipient_list)
            )
            
            # Start a background thread to send emails
            thread = threading.Thread(
                target=CreatorBulkMailService._process_bulk_mail,
                args=(bulk_mail.id,)
            )
            thread.daemon = True
            thread.start()
            
            return {
                "status": "success", 
                "message": "Bulk mail job created",
                "campaign_id": bulk_mail.id,
                "total_recipients": bulk_mail.total_recipients
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def _process_bulk_mail(bulk_mail_id):
        try:
            bulk_mail = CreatorBulkMail.objects.get(id=bulk_mail_id)
            bulk_mail.mark_as_in_progress()
            
            successful_count = 0
            failed_count = 0
            
            for email in bulk_mail.recipient_list:
                try:
                    # Prepare context for template
                    context = bulk_mail.template_context.copy()
                    
                    # Check if we have recipient details in the template_context
                    recipient_name = None
                    if 'recipients' in context and isinstance(context['recipients'], list):
                        # Find the recipient info for the current email
                        for recipient in context['recipients']:
                            if isinstance(recipient, dict) and recipient.get('email') == email:
                                recipient_name = recipient.get('name')
                                break
                    
                    # If no name was found, extract from email
                    if not recipient_name and '@' in email:
                        recipient_name = email.split('@')[0].title()
                    
                    # Set the name in context
                    context['name'] = recipient_name
                        
                    # Add other default context
                    if 'subject' not in context:
                        context['subject'] = bulk_mail.subject
                    
                    # Render email template
                    html_message = render_to_string(bulk_mail.template_name, context)
                    plain_message = strip_tags(html_message)
                    
                    # Send email
                    send_mail(
                        subject=bulk_mail.subject,
                        message=plain_message,
                        from_email=bulk_mail.from_email,
                        recipient_list=[email],
                        html_message=html_message,
                    )
                    
                    # Log the email
                    EmailLog.objects.create(
                        subject=bulk_mail.subject,
                        message=plain_message,
                        html_message=html_message,
                        from_email=bulk_mail.from_email,
                        to_email=email,
                        priority='medium',
                        status='sent'
                    )
                    
                    successful_count += 1
                except Exception as e:
                    failed_count += 1
                    print(f"Failed to send email to {email}: {str(e)}")
                
                # Update counts periodically (every 10 emails)
                if (successful_count + failed_count) % 10 == 0:
                    bulk_mail.update_counts(successful_count, failed_count)
                    successful_count = 0
                    failed_count = 0
            
            # Update final counts
            bulk_mail.update_counts(successful_count, failed_count)
            bulk_mail.mark_as_completed()
            
        except Exception as e:
            try:
                bulk_mail = CreatorBulkMail.objects.get(id=bulk_mail_id)
                bulk_mail.mark_as_failed(str(e))
            except:
                print(f"Failed to process bulk mail {bulk_mail_id}: {str(e)}")
    
    @staticmethod
    def get_campaign_status(campaign_id):
        try:
            bulk_mail = CreatorBulkMail.objects.get(id=campaign_id)
            return {
                "status": "success",
                "campaign": {
                    "id": bulk_mail.id,
                    "campaign_name": bulk_mail.campaign_name,
                    "status": bulk_mail.status,
                    "total_recipients": bulk_mail.total_recipients,
                    "successful_count": bulk_mail.successful_count,
                    "failed_count": bulk_mail.failed_count,
                    "created_at": bulk_mail.created_at.isoformat(),
                    "started_at": bulk_mail.started_at.isoformat() if bulk_mail.started_at else None,
                    "completed_at": bulk_mail.completed_at.isoformat() if bulk_mail.completed_at else None,
                    "error_message": bulk_mail.error_message
                }
            }
        except CreatorBulkMail.DoesNotExist:
            return {"status": "error", "message": "Campaign not found"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class GeneralBulkMailService:
    @staticmethod
    def send_general_bulk_mail(mail_data):
        try:
            # Create bulk mail record
            bulk_mail = CreatorBulkMail.objects.create(
                campaign_name=mail_data.campaign_name,
                subject=mail_data.subject,
                message=mail_data.message,
                from_email=mail_data.from_email or 'team@createathon.co',
                template_name='email/general_message.html',
                recipient_list=mail_data.recipient_list,
                template_context={
                    'subject': mail_data.subject,
                    'message': mail_data.message,
                    'cta_url': mail_data.cta_url,
                    'cta_text': mail_data.cta_text,
                    **mail_data.template_context
                },
                total_recipients=len(mail_data.recipient_list)
            )
            
            # Start a background thread to send emails
            thread = threading.Thread(
                target=GeneralBulkMailService._process_bulk_mail,
                args=(bulk_mail.id,)
            )
            thread.daemon = True
            thread.start()
            
            return {
                "status": "success", 
                "message": "General bulk mail job created",
                "campaign_id": bulk_mail.id,
                "total_recipients": bulk_mail.total_recipients
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def _process_bulk_mail(bulk_mail_id):
        try:
            bulk_mail = CreatorBulkMail.objects.get(id=bulk_mail_id)
            bulk_mail.mark_as_in_progress()
            
            successful_count = 0
            failed_count = 0
            
            for email in bulk_mail.recipient_list:
                try:
                    # Prepare context for template
                    context = bulk_mail.template_context.copy()
                    
                    # Check if we have recipient details in the template_context
                    recipient_name = None
                    if 'recipients' in context and isinstance(context['recipients'], list):
                        # Find the recipient info for the current email
                        for recipient in context['recipients']:
                            if isinstance(recipient, dict) and recipient.get('email') == email:
                                recipient_name = recipient.get('name')
                                break
                    
                    # If no name was found, extract from email
                    if not recipient_name and '@' in email:
                        recipient_name = email.split('@')[0].title()
                    
                    # Set the name in context
                    context['name'] = recipient_name
                    
                    # Render email template
                    html_message = render_to_string(bulk_mail.template_name, context)
                    plain_message = strip_tags(html_message)
                    
                    # Send email
                    send_mail(
                        subject=bulk_mail.subject,
                        message=plain_message,
                        from_email=bulk_mail.from_email,
                        recipient_list=[email],
                        html_message=html_message,
                    )
                    
                    # Log the email
                    EmailLog.objects.create(
                        subject=bulk_mail.subject,
                        message=plain_message,
                        html_message=html_message,
                        from_email=bulk_mail.from_email,
                        to_email=email,
                        priority='medium',
                        status='sent'
                    )
                    
                    successful_count += 1
                except Exception as e:
                    failed_count += 1
                    print(f"Failed to send email to {email}: {str(e)}")
                
                # Update counts periodically (every 10 emails)
                if (successful_count + failed_count) % 10 == 0:
                    bulk_mail.update_counts(successful_count, failed_count)
                    successful_count = 0
                    failed_count = 0
            
            # Update final counts
            bulk_mail.update_counts(successful_count, failed_count)
            bulk_mail.mark_as_completed()
            
        except Exception as e:
            try:
                bulk_mail = CreatorBulkMail.objects.get(id=bulk_mail_id)
                bulk_mail.mark_as_failed(str(e))
            except:
                print(f"Failed to process bulk mail {bulk_mail_id}: {str(e)}")
    
    @staticmethod
    def get_campaign_status(campaign_id):
        # Reuse the same method from CreatorBulkMailService
        return CreatorBulkMailService.get_campaign_status(campaign_id)

class CampaignService:
    @staticmethod
    def get_recent_campaigns(limit=5):
        """
        Get the most recent campaigns (both creator and general)
        """
        try:
            # Get the 5 most recent campaigns
            campaigns = CreatorBulkMail.objects.all().order_by('-created_at')[:limit]
            
            result = []
            for campaign in campaigns:
                result.append({
                    "id": campaign.id,
                    "campaign_name": campaign.campaign_name,
                    "subject": campaign.subject,
                    "status": campaign.status,
                    "total_recipients": campaign.total_recipients,
                    "successful_count": campaign.successful_count,
                    "failed_count": campaign.failed_count,
                    "created_at": campaign.created_at.isoformat(),
                })
            
            return {
                "status": "success",
                "campaigns": result
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def get_campaign_details(campaign_id):
        """
        Get detailed information about a specific campaign including recipient list
        """
        try:
            campaign = CreatorBulkMail.objects.get(id=campaign_id)
            
            # Get all email logs for this campaign
            email_logs = EmailLog.objects.filter(
                subject=campaign.subject,
                from_email=campaign.from_email
            ).values('to_email', 'status', 'sent_at', 'error_message')
            
            # Prepare participant list with status
            participants = []
            for email in campaign.recipient_list:
                # Find corresponding log entry
                log_entry = next((log for log in email_logs if log['to_email'] == email), None)
                
                participant = {
                    "email": email,
                    "status": log_entry['status'] if log_entry else 'unknown',
                    "sent_at": log_entry['sent_at'].isoformat() if log_entry and log_entry['sent_at'] else None,
                    "error_message": log_entry['error_message'] if log_entry else None
                }
                participants.append(participant)
            
            return {
                "status": "success",
                "campaign": {
                    "id": campaign.id,
                    "campaign_name": campaign.campaign_name,
                    "subject": campaign.subject,
                    "message": campaign.message,
                    "status": campaign.status,
                    "total_recipients": campaign.total_recipients,
                    "successful_count": campaign.successful_count,
                    "failed_count": campaign.failed_count,
                    "created_at": campaign.created_at.isoformat(),
                    "started_at": campaign.started_at.isoformat() if campaign.started_at else None,
                    "completed_at": campaign.completed_at.isoformat() if campaign.completed_at else None,
                    "participants": participants
                }
            }
        except CreatorBulkMail.DoesNotExist:
            return {"status": "error", "message": "Campaign not found"}
        except Exception as e:
            return {"status": "error", "message": str(e)}